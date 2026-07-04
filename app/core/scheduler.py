import asyncio
from app.db.supabase_client import supabase
from app.core.fetch_articles import fetch_articles_for_topic
from app.llm.evaluator import evaluate_headlines


def _run_sentinel_check():
    """
    The core F.A.I.T sentinel job:
    1. Fetch all active alerts from Supabase.
    2. For each alert, scrape headlines using the RSS pipeline.
    3. Pass headlines to the LLM evaluator.
    4. Log an alert if triggered.
    """
    print("\n[F.A.I.T Sentinel] Running scheduled alert check...")
    results_summary = []

    # 1. Fetch active alerts
    try:
        result = supabase.table("user_alerts").select("*").eq("is_active", True).execute()
        alerts = result.data
    except Exception as e:
        print(f"[F.A.I.T Sentinel] Failed to fetch alerts: {e}")
        return {"status": "error", "message": str(e)}

    if not alerts:
        print("[F.A.I.T Sentinel] No active alerts found. Skipping.")
        return {"status": "skipped", "message": "No active alerts"}

    print(f"[F.A.I.T Sentinel] Found {len(alerts)} active alert(s). Evaluating...")

    # 2. Process each alert
    for alert in alerts:
        keyword = alert["keyword"]
        trigger_condition = alert["trigger_condition"]

        try:
            # Check if there is an existing event loop
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = None

            if loop and loop.is_running():
                # We are inside an async context (FastAPI endpoint)
                import nest_asyncio
                nest_asyncio.apply()
                articles = asyncio.run(fetch_articles_for_topic(keyword))
            else:
                articles = asyncio.run(fetch_articles_for_topic(keyword))
        except Exception as e:
            print(f"[F.A.I.T Sentinel] Error fetching articles for '{keyword}': {e}")
            continue

        if not articles:
            print(f"[F.A.I.T Sentinel] No articles found for keyword '{keyword}'. Skipping.")
            continue

        # 3. Evaluate with LLM
        verdict = evaluate_headlines(trigger_condition, articles)

        # 4. Record results
        if verdict.get("triggered"):
            summary = {
                "keyword": keyword,
                "triggered": True,
                "match": verdict.get('article_title', 'N/A'),
                "details": verdict.get('summary', 'N/A')
            }
            results_summary.append(summary)
            print(f"\n{'='*60}")
            print(f"  [ALERT TRIGGERED] {keyword}")
            print(f"  Match: {summary['match']}")
            print(f"{'='*60}\n")
        else:
            results_summary.append({
                "keyword": keyword,
                "triggered": False
            })
            print(f"[F.A.I.T Sentinel] No match for alert '{keyword}'.")

    print("[F.A.I.T Sentinel] Check complete.\n")
    return {"status": "success", "results": results_summary}
