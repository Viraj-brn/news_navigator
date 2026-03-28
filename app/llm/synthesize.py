import json
from dotenv import load_dotenv
from groq import Groq
import os

from app.llm.llm_serve import get_client

client = get_client()

load_dotenv()


DEPTH_INSTRUCTIONS = {
    "quick":    "Write 2–3 sentences per section. Be concise and punchy.",
    "standard": "Write 1–2 paragraphs per section. Be analytical and clear.",
    "expert":   "Write detailed paragraphs with data, policy references, and expert framing. Assume the reader is a finance professional.",
}


def build_article_block(articles: list[dict]) -> str:
    lines = []
    for i, a in enumerate(articles, start=1):
        lines.append(
            f"[{i}] {a['title']}\n{a['description']}\nPublished: {a['pubDate']}")
    return "\n\n".join(lines)


def synthesize_briefing(articles: list[dict], topic: str, depth: str = "standard") -> dict:

    article_block = build_article_block(articles)
    depth_instruction = DEPTH_INSTRUCTIONS.get(
        depth, DEPTH_INSTRUCTIONS["standard"])

    system_prompt = (
        "You are an intelligence briefing engine for Economic Times. "
        "You synthesize multiple news articles into a single structured, analytical briefing. "
        "Your output must be STRICTLY valid JSON. Do not include markdown, backticks, explanations, or any text outside the JSON object."
    )

    user_prompt = f"""Topic: {topic}
Depth: {depth_instruction}

Here are {len(articles)} recent ET articles on this topic:

{article_block}

Produce a structured briefing as a JSON object. 
CRITICAL RULES:
1. Do NOT use a rigid template for the sections. You must invent 4 to 5 highly relevant analytical sections with DYNAMIC titles based entirely on the topic.
2. If it's Finance: use titles like 'Market Impact', 'Regulatory View', etc.
3. If it's Sports: use titles like 'Match Highlights', 'Key Performances', 'Tournament Impact', etc.
4. If it's Entertainment/Tech: use context-appropriate headers.

Structure your output EXACTLY like this JSON format:
{{
  "headline": "A sharp, analytical headline for this briefing",
  "kicker": "3–5 word topic label (e.g., 'IPL 2026 · Cricket')",
  "synthesis": "1 paragraph overview of what is happening",
  "metadata": [
    {{ "label": "Key Stat", "value": "Number/Data (e.g., 'Target: 240' or 'Valuation: $5B')" }},
    {{ "label": "Date/Impact", "value": "Short text" }}
  ],
  "sections": [
    {{
      "title": "DYNAMIC TITLE 1 (e.g., 'The Opening Ceremony')",
      "icon": "🏏", 
      "body": "Detailed paragraph synthesizing the information..."
    }},
    {{
      "title": "DYNAMIC TITLE 2 (e.g., 'Key Players to Watch')",
      "icon": "⭐",
      "body": "Detailed paragraph..."
    }}
    // Add 2-3 more DYNAMIC sections here...
  ],
  "keyTerms": [
    {{ "term": "Term", "definition": "Definition for lay readers" }}
  ],
  "articleCount": {len(articles)}
}}

Output strictly valid JSON. No markdown formatting, no explanations."""

    response = client.chat.completions.create(

        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        max_tokens=3000,
        temperature=0.2  # lower = better JSON reliability
    )

    raw = response.choices[0].message.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Strip accidental markdown fences if Claude added them
        cleaned = raw.removeprefix("```json").removeprefix(
            "```").removesuffix("```").strip()
        return json.loads(cleaned)
