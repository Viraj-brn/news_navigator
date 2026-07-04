import json
from dotenv import load_dotenv
from app.llm.llm_serve import get_langchain_client_fast
from app.llm.token_tracker import tracker
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


def evaluate_headlines(trigger_condition: str, headlines: list[dict]) -> dict:
    """
    Uses the fast LLM to evaluate whether any scraped headlines
    match the user's trigger condition.

    Returns a dict: {"triggered": bool, "article_title": str, "summary": str}
    """
    if not headlines:
        return {"triggered": False, "article_title": "", "summary": "No headlines to evaluate."}

    # Use the fast 8b model — this is a simple classification task
    client = get_langchain_client_fast()

    headline_block = "\n".join(
        [f"- {h['title']}" for h in headlines[:15]]  # Cap at 15 headlines
    )

    system_prompt = (
        "You are a news alert evaluator. Determine if any headlines match the trigger condition.\n"
        "Respond with STRICTLY valid JSON: {\"triggered\": true/false, \"article_title\": \"...\", \"summary\": \"...\"}\n"
        "If not triggered: article_title=\"\", summary=\"No matching headlines found.\""
    )

    user_prompt = f"""Trigger: "{trigger_condition}"

Headlines:
{headline_block}

Does any headline match? Respond with strictly valid JSON."""

    response = client.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    raw = response.content.strip()

    # Track token usage
    tracker.log_usage("evaluator", system_prompt + user_prompt, raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Strip accidental markdown fences
        cleaned = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"triggered": False, "article_title": "", "summary": "Failed to parse evaluator response."}
