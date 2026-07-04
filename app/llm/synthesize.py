import json
from typing import TypedDict, Optional
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.llm.llm_serve import get_langchain_client, get_langchain_client_fast
from app.llm.token_tracker import tracker

load_dotenv()

# Model selection per depth — saves tokens on quick briefings
DEPTH_CONFIG = {
    "quick": {
        "instruction": "Write 2–3 sentences per section. Be concise and punchy.",
        "model": "fast",
    },
    "standard": {
        "instruction": "Write 1–2 paragraphs per section. Be analytical and clear.",
        "model": "full",
    },
    "expert": {
        "instruction": "Write detailed paragraphs with data, policy references, and expert framing. Assume the reader is a finance/tech professional.",
        "model": "full",
    },
}


def build_article_block(articles: list[dict]) -> str:
    """Build a compact article block for the LLM prompt. Truncates descriptions for token efficiency."""
    lines = []
    for i, a in enumerate(articles, start=1):
        # Truncate description to 200 chars — diminishing returns beyond that
        desc = a['description'][:200].strip()
        lines.append(f"[{i}] {a['title']}\n{desc}")
    return "\n\n".join(lines)


# 1. Define the Graph State
class BriefingState(TypedDict):
    topic: str
    depth: str
    depth_instruction: str
    article_block: str
    article_count: int
    draft: Optional[str]
    error: Optional[str]
    final_briefing: Optional[dict]
    retry_count: int


# 2. Node: Draft Briefing
def draft_node(state: BriefingState):
    depth = state.get("depth", "standard")
    config = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["standard"])

    if config["model"] == "fast":
        client = get_langchain_client_fast()
    else:
        client = get_langchain_client()

    system_prompt = (
        "You are F.A.I.T — an intelligence briefing engine for Finance, AI & Tech news. "
        "Synthesize articles into a structured analytical briefing. "
        "Output STRICTLY valid JSON. No markdown, no backticks, no text outside the JSON."
    )

    user_prompt = f"""Topic: {state['topic']}
Depth: {state['depth_instruction']}

{state['article_count']} recent articles:

{state['article_block']}

Output JSON:
{{
  "headline": "Sharp analytical headline",
  "kicker": "3–5 word topic label",
  "synthesis": "1 paragraph overview",
  "metadata": [{{ "label": "Key Stat", "value": "Data" }}],
  "sections": [{{ "title": "DYNAMIC TITLE", "icon": "📊", "body": "Analysis..." }}],
  "keyTerms": [{{ "term": "Term", "definition": "Def" }}],
  "articleCount": {state['article_count']}
}}

Rules: 4-5 sections with DYNAMIC titles relevant to the topic. Strictly valid JSON."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    # If there was an error in a previous attempt, pass it along
    if state.get("error") and state.get("draft"):
        messages.append(AIMessage(content=state["draft"]))
        messages.append(HumanMessage(
            content=f"Invalid JSON. Error: {state['error']}. Fix and return strictly valid JSON."))

    response = client.invoke(messages)

    # Track token usage
    input_text = system_prompt + user_prompt
    tracker.log_usage("synthesize", input_text, response.content)

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
    config = DEPTH_CONFIG.get(depth, DEPTH_CONFIG["standard"])

    initial_state = {
        "topic": topic,
        "depth": depth,
        "depth_instruction": config["instruction"],
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
