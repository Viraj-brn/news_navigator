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
import os

if not os.getenv("GROQ_API_KEY"):
    raise RuntimeError("GROQ_API_KEY not found in environment variables")

load_dotenv()
app = FastAPI()


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


# ── Routes ──────────────────────────────────────────────

@app.post("/api/navigator")
async def generate_briefing(req: NavigatorRequest):
    articles = await fetch_articles_for_topic(req.topic)
    
    if not articles:
        raise HTTPException(status_code=404, detail="No articles found for this topic")

    # --- NEW RAG LOGIC ---
    # Process and embed the articles into ChromaDB in the background
    chunks = process_articles_into_chunks(articles)
    create_knowledge_base(req.topic, chunks)
    # ---------------------

    briefing = synthesize_briefing(articles, req.topic, req.depth)
    return {"briefing": briefing, "articles": articles, "topic": req.topic}


@app.post("/api/ask")
def ask_question(req: AskRequest):
    """Answer a follow-up question using RAG context."""
    
    answer = ask_briefing(
        briefing=req.briefing,
        topic=req.topic,       # 👈 Pass the topic to the retriever
        conversation_history=req.conversation_history,
        new_question=req.question,
    )
    
    return {"answer": answer}


# ── Serve the frontend ───────────────────────────────────

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")


# ── Run ─────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
