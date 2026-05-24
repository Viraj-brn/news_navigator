import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
from app.db.supabase_client import supabase
from app.core.fetch_articles import fetch_articles_for_topic
from app.llm.evaluator import evaluate_headlines


def _run_sentinel_check():
    """
    The core sentinel job:
    1. Fetch all active alerts from Supabase.
    2. For each alert, scrape headlines using the existing RSS pipeline.
    3. Pass headlines to the LLM evaluator.
    4. Print an alert to the terminal if triggered.
    """
    print("\n[Sentinel] Running scheduled alert check...")

    # 1. Fetch active alerts
    try:
        result = supabase.table("user_alerts").select("*").eq("is_active", True).execute()
        alerts = result.data
    except Exception as e:
        print(f"[Sentinel] Failed to fetch alerts: {e}")
        return

    if not alerts:
        print("[Sentinel] No active alerts found. Skipping.")
        return

    print(f"[Sentinel] Found {len(alerts)} active alert(s). Evaluating...")

    # 2. Process each alert
    for alert in alerts:
        keyword = alert["keyword"]
        trigger_condition = alert["trigger_condition"]

        try:
            # Use asyncio to run the async fetch function from sync context
            articles = asyncio.run(fetch_articles_for_topic(keyword))
        except RuntimeError:
            # If there's already an event loop running (inside FastAPI/uvicorn)
            loop = asyncio.get_event_loop()
            articles = loop.run_until_complete(fetch_articles_for_topic(keyword))

        if not articles:
            print(f"[Sentinel] No articles found for keyword '{keyword}'. Skipping.")
            continue

        # 3. Evaluate with LLM
        verdict = evaluate_headlines(trigger_condition, articles)

        # 4. Print alert if triggered
        if verdict.get("triggered"):
            print(f"\n{'='*60}")
            print(f"  [ALERT TRIGGERED]")
            print(f"  Keyword:   {keyword}")
            print(f"  Condition: {trigger_condition}")
            print(f"  Match:     {verdict.get('article_title', 'N/A')}")
            print(f"  Summary:   {verdict.get('summary', 'N/A')}")
            print(f"{'='*60}\n")
        else:
            print(f"[Sentinel] No match for alert '{keyword}' -> '{trigger_condition}'.")

    print("[Sentinel] Check complete.\n")


# --- Scheduler setup ---
scheduler = BackgroundScheduler()
scheduler.add_job(_run_sentinel_check, "interval", hours=6, id="news_sentinel")


def start_scheduler():
    """Start the APScheduler background scheduler."""
    if not scheduler.running:
        scheduler.start()
        print("[Sentinel] Scheduler started. Checking every 6 hours.")


def stop_scheduler():
    """Gracefully shut down the scheduler."""
    if scheduler.running:
        scheduler.shutdown(wait=False)
        print("[Sentinel] Scheduler stopped.")
