import json
from dotenv import load_dotenv
from app.llm.llm_serve import get_langchain_client
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()


def evaluate_headlines(trigger_condition: str, headlines: list[dict]) -> dict:
    """
    Uses the LLM to evaluate whether any of the scraped headlines
    match the user's trigger condition.

    Returns a dict: {"triggered": bool, "article_title": str, "summary": str}
    """
    if not headlines:
        return {"triggered": False, "article_title": "", "summary": "No headlines to evaluate."}

    client = get_langchain_client(temperature=0.0)

    headline_block = "\n".join(
        [f"- {h['title']}" for h in headlines[:20]]  # Cap at 20 headlines
    )

    system_prompt = (
        "You are a news alert evaluator. Your job is to determine whether any of the "
        "given news headlines match a user's alert trigger condition.\n"
        "You MUST respond with STRICTLY valid JSON. No markdown, no explanations.\n"
        "Format: {\"triggered\": true/false, \"article_title\": \"...\", \"summary\": \"...\"}\n"
        "If triggered is false, set article_title to \"\" and summary to \"No matching headlines found.\""
    )

    user_prompt = f"""Alert Trigger Condition: "{trigger_condition}"

Recent Headlines:
{headline_block}

Evaluate: Does any headline match or closely relate to the trigger condition?
Respond with strictly valid JSON."""

    response = client.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ])

    raw = response.content.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Strip accidental markdown fences
        cleaned = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            return {"triggered": False, "article_title": "", "summary": "Failed to parse evaluator response."}
