import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv

from app.core.fetch_articles import fetch_articles_for_topic
from app.llm.synthesize import synthesize_briefing
from app.llm.ask_briefing import ask_briefing
from app.llm.token_tracker import tracker
from app.rag.document_processor import process_articles_into_chunks
from app.rag.vector_store import create_knowledge_base
from app.core.scheduler import _run_sentinel_check
from app.db.supabase_client import supabase
import os

load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("GROQ_API_KEY not found in environment variables")

_start_time = time.time()

app = FastAPI(
    title="F.A.I.T — Finance, AI & Tech Intelligence",
    description="AI-powered intelligence briefing engine for Finance, AI, and Technology news.",
    version="2.0.0",
)

# ── CORS (Cross-Origin Resource Sharing) Middleware ─────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow requests from any website
    allow_credentials=True, # Allow cookies and authentication headers
    allow_methods=["*"], # Allow all HTTP methods (GET, POST, DELETE, etc)
    allow_headers=["*"], # Allow all custom HTTP headers
)


# ── Request Timing Middleware ───────────────────────────
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    process_time = round(time.time() - start, 3)
    response.headers["X-Process-Time"] = str(process_time)
    return response


# ── Request models ──────────────────────────────────────

class NavigatorRequest(BaseModel):
    topic: str
    depth: str = "standard"

    # Add a Pydantic validator to automatically strip spaces
    @field_validator('topic')
    @classmethod
    def validate_topic(cls, v):
        return v.strip() if isinstance(v, str) else v

class AskRequest(BaseModel):
    briefing: dict
    topic: str
    conversation_history: list[dict] = []
    question: str

    @field_validator('topic', 'question')
    @classmethod
    def validate_topic_and_q(cls, v):
        return v.strip() if isinstance(v, str) else v

class AlertRequest(BaseModel):
    keyword: str
    trigger_condition: str


# ── Core Routes ─────────────────────────────────────────

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


# ── Alerts (F.A.I.T Sentinel) ───────────────────────────

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


@app.post("/api/sentinel/run")
def trigger_sentinel():
    """Endpoint for cron-job.org to trigger the daily news alert check."""
    try:
        results = _run_sentinel_check()
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sentinel run failed: {str(e)}")


# ── System Endpoints ────────────────────────────────────

@app.get("/api/health")
def health_check():
    """System health endpoint with metadata — useful for monitoring and interviews."""
    uptime_seconds = round(time.time() - _start_time)
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    from app.core.feeds import FEED_REGISTRY
    return {
        "status": "healthy",
        "app": "F.A.I.T — Finance, AI & Tech Intelligence",
        "version": "2.0.0",
        "uptime": f"{hours}h {minutes}m {seconds}s",
        "feeds_registered": len(FEED_REGISTRY),
        "models": {
            "primary": "llama-3.3-70b-versatile",
            "fast": "llama-3.1-8b-instant",
            "embeddings": "all-MiniLM-L6-v2",
        },
    }


@app.get("/api/stats")
def token_stats():
    """Token usage statistics — demonstrates cost-consciousness in architecture."""
    return tracker.get_stats()


@app.get("/api/keepalive")
def keepalive():
    """Endpoint to keep free hosting tiers awake so scheduled jobs run."""
    return {"status": "awake"}


# ── Serve the frontend ───────────────────────────────────

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")


# ── Run ─────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
