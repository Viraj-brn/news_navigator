import feedparser
import asyncio
import httpx
from app.core.feeds import FEED_REGISTRY, TOPIC_TO_FEEDS


async def fetch_single_feed(client: httpx.AsyncClient, url: str, feed_name: str) -> list[dict]:
    """Fetch and parse one RSS feed asynchronously."""
    try:
        response = await client.get(url, timeout=12.0, follow_redirects=True)
        response.raise_for_status()
        feed = feedparser.parse(response.text)

        articles = []
        for item in feed.entries[:8]:  # Cap per-feed to 8 for token efficiency
            articles.append({
                "title":       item.get("title", ""),
                "description": item.get("summary", "")[:300],  # Truncate descriptions early
                "link":        item.get("link", ""),
                "pubDate":     item.get("published", ""),
                "source":      feed.feed.get("title", feed_name),
                "category":    feed_name.split("_")[0],  # e.g., "reuters" from "reuters_business"
            })
        return articles

    except Exception as e:
        print(f"⚠️ Failed to fetch feed '{feed_name}': {e}")
        return []


async def fetch_articles_for_topic(topic: str) -> list[dict]:
    """Fetch articles and smartly filter them based on the topic."""
    topic_lower = topic.lower()
    feed_keys = []

    # 1. Try to find specific feeds mapped to the topic
    for keyword, feeds in TOPIC_TO_FEEDS.items():
        if keyword in topic_lower:
            feed_keys.extend(feeds)

    feed_keys = list(set(feed_keys))  # Deduplicate

    # 2. Fetch the targeted feeds
    async with httpx.AsyncClient() as client:
        if feed_keys:
            tasks = [fetch_single_feed(client, FEED_REGISTRY[key], key)
                     for key in feed_keys if key in FEED_REGISTRY]
            results = await asyncio.gather(*tasks)
            all_articles = [
                article for feed_articles in results for article in feed_articles]
        else:
            all_articles = []

        # 3. FALLBACK: If targeted feeds returned nothing, scan top general feeds
        if not all_articles:
            print(
                f"⚠️ No targeted articles found for '{topic}'. Falling back to general feeds.")
            fallback_keys = [
                "reuters_business", "techcrunch", "ai_news",
                "cnbc_finance", "bbc_business", "coindesk",
            ]
            tasks = [fetch_single_feed(client, FEED_REGISTRY[key], key)
                     for key in fallback_keys if key in FEED_REGISTRY]
            results = await asyncio.gather(*tasks)
            all_articles = [
                article for feed_articles in results for article in feed_articles]

    # 4. Deduplicate by title
    seen = set()
    unique_articles = []
    for article in all_articles:
        if article["title"] not in seen:
            seen.add(article["title"])
            unique_articles.append(article)

    # 5. Smart Filtering with Plural Handling
    topic_words = topic_lower.split()

    # Build a set of search variations to automatically handle plurals
    search_terms = set(topic_words)
    for w in topic_words:
        if w.endswith('s') and len(w) > 3:  # Avoid breaking words like "is", "gas"
            search_terms.add(w[:-1])  # "stocks" -> "stock"
        else:
            search_terms.add(w + 's')  # "startup" -> "startups"
            search_terms.add(w + 'es')  # "tax" -> "taxes"

    # Broad categories that shouldn't be strictly filtered
    BROAD_CATEGORIES = {
        "market", "markets", "tech", "technology", "ai",
        "finance", "economy", "crypto", "startup", "startups",
        "business", "businesses", "trading", "investment",
        "data science", "machine learning", "blockchain",
        "global", "geopolitics",
    }

    # If it's a broad category, trust the RAG to pull the right articles
    if len(topic_words) == 1 and topic_words[0] in BROAD_CATEGORIES:
        return unique_articles[:12]

    # Otherwise, strictly filter by our singular/plural variations
    filtered_articles = []
    for article in unique_articles:
        text = (article["title"] + " " + article["description"]).lower()
        if any(term in text for term in search_terms):
            filtered_articles.append(article)

    final_articles = filtered_articles if filtered_articles else unique_articles
    return final_articles[:12]  # Cap at 12 for token efficiency
