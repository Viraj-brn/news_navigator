
# ── F.A.I.T — Feed Registry ──────────────────────────────
# Global RSS sources covering Finance, AI, and Technology.
# Each feed is tagged with a category for smart routing.

FEED_REGISTRY = {
    # ── Markets & Finance ─────────────────────────────────
    "reuters_business":   "https://feeds.reuters.com/reuters/businessNews",
    "reuters_markets":    "https://feeds.reuters.com/reuters/marketsNews",
    "cnbc_finance":       "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=10000664",
    "cnbc_economy":       "https://search.cnbc.com/rs/search/combinedcms/view.xml?partnerId=wrss01&id=20910258",
    "marketwatch":        "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "yahoo_finance":      "https://finance.yahoo.com/news/rssindex",
    "et_markets":         "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "et_economy":         "https://economictimes.indiatimes.com/economy/rssfeeds/1373380680.cms",
    "moneycontrol":       "https://www.moneycontrol.com/rss/latestnews.xml",

    # ── Technology ────────────────────────────────────────
    "techcrunch":         "https://techcrunch.com/feed/",
    "ars_technica":       "https://feeds.arstechnica.com/arstechnica/technology-lab",
    "the_verge":          "https://www.theverge.com/rss/index.xml",
    "wired":              "https://www.wired.com/feed/rss",
    "mit_tech_review":    "https://www.technologyreview.com/feed/",
    "hacker_news":        "https://hnrss.org/frontpage",
    "et_tech":            "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",

    # ── AI & Data Science ─────────────────────────────────
    "ai_news":            "https://www.artificialintelligence-news.com/feed/",
    "openai_blog":        "https://openai.com/blog/rss.xml",
    "deepmind_blog":      "https://deepmind.google/blog/rss.xml",
    "towards_ds":         "https://towardsdatascience.com/feed",
    "ml_mastery":         "https://machinelearningmastery.com/feed/",

    # ── Crypto & Web3 ─────────────────────────────────────
    "coindesk":           "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph":      "https://cointelegraph.com/rss",

    # ── Global Macro & Geopolitics ────────────────────────
    "reuters_world":      "https://feeds.reuters.com/reuters/worldNews",
    "bbc_business":       "https://feeds.bbci.co.uk/news/business/rss.xml",
    "bbc_tech":           "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "et_international":   "https://economictimes.indiatimes.com/news/international/rssfeeds/28508097.cms",

    # ── Startups & VC ─────────────────────────────────────
    "et_startups":        "https://economictimes.indiatimes.com/small-biz/startups/rssfeeds/13357270.cms",
    "crunchbase":         "https://news.crunchbase.com/feed/",
}


# ── Topic → Feed Routing ─────────────────────────────────
# Maps user query keywords to relevant feed keys.

TOPIC_TO_FEEDS = {
    # Finance & Markets
    "market":       ["reuters_markets", "cnbc_finance", "et_markets", "yahoo_finance", "marketwatch"],
    "stock":        ["reuters_markets", "cnbc_finance", "et_markets", "yahoo_finance"],
    "finance":      ["reuters_business", "cnbc_finance", "et_markets", "et_economy", "moneycontrol"],
    "banking":      ["reuters_business", "cnbc_finance", "et_economy", "moneycontrol"],
    "investment":   ["reuters_markets", "cnbc_finance", "yahoo_finance", "marketwatch"],
    "earnings":     ["reuters_business", "cnbc_finance", "yahoo_finance", "marketwatch"],
    "fed":          ["reuters_markets", "cnbc_economy", "cnbc_finance"],
    "rbi":          ["et_economy", "et_markets", "moneycontrol"],
    "interest rate": ["reuters_markets", "cnbc_economy", "et_economy"],
    "inflation":    ["reuters_markets", "cnbc_economy", "et_economy", "bbc_business"],
    "ipo":          ["reuters_markets", "cnbc_finance", "et_markets", "moneycontrol"],
    "budget":       ["et_economy", "cnbc_economy", "moneycontrol"],
    "quant":        ["reuters_markets", "cnbc_finance", "towards_ds", "ml_mastery"],
    "trading":      ["reuters_markets", "cnbc_finance", "et_markets", "yahoo_finance"],
    "economy":      ["cnbc_economy", "et_economy", "reuters_business", "bbc_business"],
    "forex":        ["reuters_markets", "cnbc_finance", "yahoo_finance"],
    "commodity":    ["reuters_markets", "cnbc_finance", "marketwatch"],

    # Technology
    "tech":         ["techcrunch", "ars_technica", "the_verge", "wired", "et_tech", "bbc_tech"],
    "startup":      ["techcrunch", "et_startups", "crunchbase"],
    "software":     ["techcrunch", "ars_technica", "hacker_news"],
    "semiconductor": ["techcrunch", "ars_technica", "reuters_business", "the_verge"],
    "gpu":          ["techcrunch", "ars_technica", "the_verge", "wired"],
    "chip":         ["techcrunch", "ars_technica", "reuters_business"],
    "cloud":        ["techcrunch", "ars_technica", "cnbc_finance"],
    "cybersecurity": ["techcrunch", "ars_technica", "wired", "bbc_tech"],
    "apple":        ["techcrunch", "the_verge", "cnbc_finance", "reuters_business"],
    "google":       ["techcrunch", "the_verge", "ars_technica", "cnbc_finance"],
    "microsoft":    ["techcrunch", "the_verge", "cnbc_finance", "reuters_business"],

    # AI & Data Science
    "ai":           ["ai_news", "techcrunch", "mit_tech_review", "openai_blog", "deepmind_blog"],
    "artificial intelligence": ["ai_news", "mit_tech_review", "openai_blog", "deepmind_blog", "techcrunch"],
    "machine learning": ["ai_news", "towards_ds", "ml_mastery", "mit_tech_review"],
    "deep learning": ["ai_news", "towards_ds", "ml_mastery", "mit_tech_review"],
    "llm":          ["ai_news", "techcrunch", "openai_blog", "mit_tech_review"],
    "gpt":          ["ai_news", "techcrunch", "openai_blog", "the_verge"],
    "openai":       ["openai_blog", "techcrunch", "ai_news", "the_verge"],
    "data science": ["towards_ds", "ml_mastery", "ai_news"],
    "nlp":          ["ai_news", "towards_ds", "mit_tech_review"],
    "robotics":     ["mit_tech_review", "techcrunch", "ai_news", "wired"],
    "automation":   ["techcrunch", "ai_news", "mit_tech_review", "wired"],

    # Crypto & Web3
    "crypto":       ["coindesk", "cointelegraph", "cnbc_finance"],
    "bitcoin":      ["coindesk", "cointelegraph", "cnbc_finance", "reuters_business"],
    "ethereum":     ["coindesk", "cointelegraph"],
    "blockchain":   ["coindesk", "cointelegraph", "techcrunch"],
    "defi":         ["coindesk", "cointelegraph"],
    "web3":         ["coindesk", "cointelegraph", "techcrunch"],

    # Global & Macro
    "global":       ["reuters_world", "bbc_business", "et_international"],
    "geopolitics":  ["reuters_world", "bbc_business", "et_international"],
    "trade war":    ["reuters_world", "reuters_business", "cnbc_economy"],
    "tesla":        ["techcrunch", "the_verge", "cnbc_finance", "reuters_business"],
    "nvidia":       ["techcrunch", "ars_technica", "cnbc_finance", "reuters_business"],
}