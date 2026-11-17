import time
import urllib.request
import feedparser
import yaml

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
STORIES_PER_SECTION = 8
TIMEOUT_SECONDS = 30


def load_feeds(path="feeds.yaml"):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def fetch_feed(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
        return feedparser.parse(resp.read())


def get_stories(feed_urls):
    stories = []
    seen = set()
    for url in feed_urls:
        print(f"  Fetching {url}")
        try:
            feed = fetch_feed(url)
        except Exception as err:
            print(f"  WARNING: could not load {url} ({err})")
            continue
        if not feed.entries:
            print(f"  WARNING: no stories from {url}")
            continue
        for e in feed.entries:
            link = e.get("link", "")
            title = e.get("title", "").strip()
            if not link or not title or link in seen:
                continue
            seen.add(link)
            stories.append({
                "title": title,
                "link": link,
                "blurb": e.get("summary", ""),
                "published": e.get("published_parsed") or time.gmtime(0),
                "source": feed.feed.get("title", url),
            })
    stories.sort(key=lambda s: s["published"], reverse=True)
    return stories[:STORIES_PER_SECTION]


def collect_all():
    sections = load_feeds()
    result = {}
    for name, urls in sections.items():
        print(f"Collecting {name}...")
        result[name] = get_stories(urls)
    return result


if __name__ == "__main__":
    for section, stories in collect_all().items():
        print(f"\n=== {section} ===")
        for s in stories:
            print(f"- {s['title']}  ({s['source']})")