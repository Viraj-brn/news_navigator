import json
from typing import TypedDict, Optional
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.llm.llm_serve import get_langchain_client

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


# 1. Define the Graph State
class BriefingState(TypedDict):
    topic: str
    depth_instruction: str
    article_block: str
    article_count: int
    draft: Optional[str]
    error: Optional[str]
    final_briefing: Optional[dict]
    retry_count: int


# 2. Node: Draft Briefing
def draft_node(state: BriefingState):
    client = get_langchain_client()
    
    system_prompt = (
        "You are an intelligence briefing engine for Economic Times. "
        "You synthesize multiple news articles into a single structured, analytical briefing. "
        "Your output must be STRICTLY valid JSON. Do not include markdown, backticks, explanations, or any text outside the JSON object."
    )

    user_prompt = f"""Topic: {state['topic']}
Depth: {state['depth_instruction']}

Here are {state['article_count']} recent ET articles on this topic:

{state['article_block']}

Produce a structured briefing as a JSON object. 
CRITICAL RULES:
1. Do NOT use a rigid template for the sections. You must invent 4 to 5 highly relevant analytical sections with DYNAMIC titles based entirely on the topic.
2. Structure your output EXACTLY like this JSON format:
{{
  "headline": "A sharp, analytical headline for this briefing",
  "kicker": "3–5 word topic label (e.g., 'IPL 2026 · Cricket')",
  "synthesis": "1 paragraph overview of what is happening",
  "metadata": [
    {{ "label": "Key Stat", "value": "Number/Data" }}
  ],
  "sections": [
    {{
      "title": "DYNAMIC TITLE 1",
      "icon": "🏏", 
      "body": "Detailed paragraph..."
    }}
  ],
  "keyTerms": [
    {{ "term": "Term", "definition": "Definition" }}
  ],
  "articleCount": {state['article_count']}
}}

Output strictly valid JSON. No markdown formatting, no explanations."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    # If there was an error in a previous attempt, pass it along
    if state.get("error") and state.get("draft"):
        messages.append(AIMessage(content=state["draft"]))
        messages.append(HumanMessage(content=f"Your previous output was invalid. Error: {state['error']}. Please fix the JSON and try again. Provide strictly valid JSON."))

    response = client.invoke(messages)
    return {"draft": response.content, "retry_count": state.get("retry_count", 0) + 1}


# 3. Node: Validate JSON
def validate_node(state: BriefingState):
    raw = state.get("draft", "").strip()
    
    try:
        # Strip accidental markdown
        cleaned = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        parsed = json.loads(cleaned)
        
        # Check required keys
        required_keys = ["headline", "kicker", "synthesis", "sections"]
        for key in required_keys:
            if key not in parsed:
                raise ValueError(f"Missing required key: {key}")
                
        return {"final_briefing": parsed, "error": None}
        
    except Exception as e:
        return {"error": str(e), "final_briefing": None}


# 4. Conditional Edge: Decide next step
def should_continue(state: BriefingState):
    if state.get("final_briefing") is not None:
        return "end"
    if state.get("retry_count", 0) >= 3:
        # Fallback if we fail 3 times
        return "end"
    return "draft"


# 5. Build the Graph
workflow = StateGraph(BriefingState)
workflow.add_node("draft_briefing", draft_node)
workflow.add_node("validate_json", validate_node)

workflow.set_entry_point("draft_briefing")
workflow.add_edge("draft_briefing", "validate_json")
workflow.add_conditional_edges(
    "validate_json",
    should_continue,
    {
        "end": END,
        "draft": "draft_briefing"
    }
)
briefing_app = workflow.compile()


def synthesize_briefing(articles: list[dict], topic: str, depth: str = "standard") -> dict:
    article_block = build_article_block(articles)
    depth_instruction = DEPTH_INSTRUCTIONS.get(depth, DEPTH_INSTRUCTIONS["standard"])
    
    initial_state = {
        "topic": topic,
        "depth_instruction": depth_instruction,
        "article_block": article_block,
        "article_count": len(articles),
        "draft": None,
        "error": None,
        "final_briefing": None,
        "retry_count": 0
    }
    
    result = briefing_app.invoke(initial_state)
    
    if result.get("final_briefing"):
        return result["final_briefing"]
    
    # Fallback if completely failed
    return {
        "headline": "Failed to generate briefing",
        "kicker": "Error",
        "synthesis": "The AI failed to generate a valid response after multiple attempts.",
        "metadata": [],
        "sections": [],
        "keyTerms": [],
        "articleCount": len(articles)
    }
