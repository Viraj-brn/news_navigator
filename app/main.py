from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from app.core.fetch_articles import fetch_articles_for_topic
from app.llm.synthesize import synthesize_briefing
from app.llm.ask_briefing import ask_briefing
from app.rag.document_processor import process_articles_into_chunks
from app.rag.vector_store import create_knowledge_base
from app.core.scheduler import start_scheduler, stop_scheduler
from app.db.supabase_client import supabase
import os

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("GROQ_API_KEY not found in environment variables")


# ── App Lifecycle ────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start the News Sentinel scheduler on startup, stop on shutdown."""
    start_scheduler()
    yield
    stop_scheduler()

app = FastAPI(lifespan=lifespan)


# ── Request models ──────────────────────────────────────

class NavigatorRequest(BaseModel):
    topic: str
    depth: str = "standard"
    
    # Add a Pydantic validator to automatically strip spaces
    @classmethod
    def validate_topic(cls, v):
        return v.strip() if isinstance(v, str) else v

class AskRequest(BaseModel):
    briefing: dict
    topic: str
    conversation_history: list[dict] = []
    question: str
    
    @classmethod
    def validate_topic_and_q(cls, v):
        return v.strip() if isinstance(v, str) else v

class AlertRequest(BaseModel):
    keyword: str
    trigger_condition: str


# ── Routes ──────────────────────────────────────────────

@app.post("/api/navigator")
async def generate_briefing(req: NavigatorRequest):
    articles = await fetch_articles_for_topic(req.topic)
    
    if not articles:
        raise HTTPException(status_code=404, detail="No articles found for this topic")

    # Process and embed the articles into Supabase pgvector
    chunks = process_articles_into_chunks(articles)
    create_knowledge_base(req.topic, chunks)

    briefing = synthesize_briefing(articles, req.topic, req.depth)
    return {"briefing": briefing, "articles": articles, "topic": req.topic}


@app.post("/api/ask")
def ask_question(req: AskRequest):
    """Answer a follow-up question using RAG context."""
    
    answer = ask_briefing(
        briefing=req.briefing,
        topic=req.topic,
        conversation_history=req.conversation_history,
        new_question=req.question,
    )
    
    return {"answer": answer}


# ── Alerts (News Sentinel) ───────────────────────────────

@app.post("/api/alerts/create")
def create_alert(req: AlertRequest):
    """Save a new alert to the Supabase user_alerts table."""
    try:
        result = supabase.table("user_alerts").insert({
            "keyword": req.keyword.strip(),
            "trigger_condition": req.trigger_condition.strip(),
            "is_active": True,
        }).execute()
        
        return {"status": "ok", "alert": result.data[0]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create alert: {str(e)}")


@app.get("/api/alerts")
def get_alerts():
    """Fetch all alerts from the Supabase user_alerts table."""
    try:
        result = supabase.table("user_alerts").select("*").order("created_at", desc=True).execute()
        return {"alerts": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")


@app.delete("/api/alerts/{alert_id}")
def delete_alert(alert_id: str):
    """Delete an alert by ID."""
    try:
        supabase.table("user_alerts").delete().eq("id", alert_id).execute()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete alert: {str(e)}")


# ── Serve the frontend ───────────────────────────────────

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")


# ── Run ─────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
