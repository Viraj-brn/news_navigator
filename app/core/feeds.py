
FEED_REGISTRY = {
    "topStories":    "https://economictimes.indiatimes.com/rssfeedstopstories.cms",
    "markets":       "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
    "economy":       "https://economictimes.indiatimes.com/economy/rssfeeds/1373380680.cms",
    "startups":      "https://economictimes.indiatimes.com/small-biz/startups/rssfeeds/13357270.cms",
    "tech":          "https://economictimes.indiatimes.com/tech/rssfeeds/13357270.cms",
    "sports":        "https://economictimes.indiatimes.com/news/sports/rssfeeds/2635564.cms",
    "politics":      "https://economictimes.indiatimes.com/news/politics-and-nation/rssfeeds/1052732854.cms",
    "defense":       "https://economictimes.indiatimes.com/news/defence/rssfeeds/46687796.cms",
    "international": "https://economictimes.indiatimes.com/news/international/rssfeeds/28508097.cms",
    "science":       "https://economictimes.indiatimes.com/news/science/rssfeeds/39872847.cms",
}

TOPIC_TO_FEEDS = {
    "budget": ["economy", "policy"],
    "market": ["markets"],
    "stock": ["markets"],
    "startup": ["startups", "tech"],
    "tech": ["tech", "startups"],
    "sport": ["sports"],
    "cricket": ["sports"],
    "olympic": ["sports"],
    "election": ["policy"],
    "global": ["international"],
    "business": ["markets", "economy", "startups"], 
    "finance": ["markets", "banking"]               
}