from dotenv import load_dotenv
from groq import Groq
import os

from app.llm.llm_serve import get_client
from app.rag.vector_store import retrieve_relevant_context

client = get_client()
load_dotenv()

def ask_briefing(
    briefing: dict,
    topic: str,
    conversation_history: list[dict],
    new_question: str,
) -> str:
    
    # 1. Retrieve ONLY the mathematically closest text chunks to the question
    relevant_context = retrieve_relevant_context(topic=topic, query=new_question, top_k=4)

    system = f"""You are an AI intelligence assistant for Economic Times.
Your job is to answer the user's follow-up question based ONLY on the specific article snippets provided below.

RELEVANT SNIPPETS:
{relevant_context}

Rules:
- Answer accurately based ONLY on the snippets.
- If the snippets do not contain the answer, explicitly state: "I don't have enough information in the current briefing sources to answer that."
- Cite your sources by mentioning the publication name or article title provided in the snippet.
- Keep the answer analytical, brief, and to the point."""

    messages = conversation_history + [{"role": "user", "content": new_question}]

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system},
            *messages
        ],
        max_tokens=600,
        temperature=0.2 # Low temperature for accurate retrieval synthesis
    )

    return response.choices[0].message.content