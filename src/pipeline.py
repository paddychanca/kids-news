import json
import os
import re
import time
from datetime import datetime, timezone

from collect import collect_all
from extract import get_article_text
from summarize import summarize_story

KEEP_PER_SECTION = 3
PAUSE_SECONDS = 4


def iso_time(t):
    if not t or t.tm_year < 1990:
        return ""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", t)


def title_key(title):
    return re.sub(r"[^a-z0-9]", "", title.lower())


def run():
    sections = collect_all()
    edition = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "sections": {},
    }
    seen_links = set()
    seen_titles = set()

    for name, candidates in sections.items():
        print(f"\n== {name}")
        kept = []
        for story in candidates:
            if len(kept) >= KEEP_PER_SECTION:
                break
            if story["link"] in seen_links or title_key(story["title"]) in seen_titles:
                print(f"  duplicate: {story['title'][:60]}")
                continue
            text, kind = get_article_text(story)
            result = summarize_story(story, text)
            time.sleep(PAUSE_SECONDS)
            seen_links.add(story["link"])
            seen_titles.add(title_key(story["title"]))
            if not result or not result.get("suitable"):
                print(f"  skipped: {story['title'][:60]}")
                continue
            kept.append({
                "headline": result.get("headline", story["title"]),
                "summary": result.get("summary", ""),
                "simple": result.get("simple", ""),
                "why_it_matters": result.get("why_it_matters", ""),
                "hard_words": result.get("hard_words", []),
                "quiz": result.get("quiz", {}),
                "fr": result.get("fr", {}),
                "original_title": story["title"],
                "source": story["source"],
                "link": story["link"],
                "published": iso_time(story["published"]),
            })
            print(f"  kept: {kept[-1]['headline']}")
        edition["sections"][name] = kept

    os.makedirs("data", exist_ok=True)
    with open("data/edition.json", "w", encoding="utf-8") as f:
        json.dump(edition, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in edition["sections"].values())
    print(f"\nDone. Saved {total} stories to data/edition.json")


if __name__ == "__main__":
    run()