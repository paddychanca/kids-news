import re
import urllib.request
import trafilatura

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
TIMEOUT_SECONDS = 30
MAX_CHARS = 6000
MIN_CHARS = 300


def clean_blurb(html):
    return re.sub(r"<[^>]+>", " ", html or "").strip()


def get_article_text(story):
    try:
        req = urllib.request.Request(story["link"], headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        text = trafilatura.extract(html)
        if text and len(text) >= MIN_CHARS:
            return text[:MAX_CHARS], "full"
    except Exception as err:
        print(f"  note: could not read article ({err})")
    return clean_blurb(story["blurb"]), "blurb"


if __name__ == "__main__":
    from collect import collect_all

    sections = collect_all()
    for name, stories in sections.items():
        story = stories[0]
        text, kind = get_article_text(story)
        print(f"\n=== {name}: {story['title']}")
        print(f"[{kind}, {len(text)} characters]")
        print(text[:300])