import json
import time
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)

MODEL = "gemini-3.1-flash-lite"
client = genai.Client()

PROMPT = """You help write a daily news page for a 11-year-old child.
Read the news story below and reply with JSON only.

Rules:
- "suitable": false if the story is mainly about death, murder, shootings, violence, war details, abuse, crime details, sexual content, self-harm, or anything that would upset a child. Also false if it is an opinion piece or commentary, or too complicated to explain simply. Otherwise true.
- "reason": one short sentence explaining your suitable decision.
- If suitable is false, you may leave all the other fields empty.
- "headline": friendly and accurate, under 12 words, no scary or clickbait wording.
- "summary": 3 to 4 short sentences in plain words that a 11-year-old can read alone. Use only facts stated in the story. Copy numbers, scores, rankings and dates exactly as the story gives them. Never turn a fact into a bigger claim (for example, "third title in 4 years" must not become "third in a row"). If you are unsure about a detail, leave it out.
- "simple": 2 sentences, even simpler, for a 7-year-old.
- "why_it_matters": one sentence.
- "hard_words": 2 or 3 items, each with "word" and "meaning". The words must appear in your summary. Explain them in kid-friendly words.
- "quiz": one question about the summary, with "question", "options" (exactly 3), "answer_index" (0, 1 or 2) and "explanation" (one sentence).

- "fr": the same content translated into natural Canadian French for a 11-year-old, as an object with exactly these keys: "headline", "summary", "simple", "why_it_matters", "hard_words" (the same words as the English ones, but in French, each with "word" and "meaning"; every French word must appear in the French summary), and "quiz" (with "question", "options" (exactly 3, in the same order as the English), "answer_index" (the same as the English) and "explanation"). Keep every fact, number and name exactly the same as in the English. Do not add anything new. If suitable is false, leave "fr" as an empty object.

Return exactly these keys: suitable, reason, headline, summary, simple, why_it_matters, hard_words, quiz, fr.

STORY TITLE: __TITLE__

STORY TEXT:
__TEXT__
"""


def summarize_story(story, text):
    prompt = PROMPT.replace("__TITLE__", story["title"]).replace("__TEXT__", text)
    for attempt in range(1, 4):
        try:
            r = client.models.generate_content(
                model=MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                ),
            )
            return json.loads(r.text)
        except Exception as err:
            print(f"  attempt {attempt} failed: {err}")
            time.sleep(10 * attempt)
    return None


if __name__ == "__main__":
    from collect import collect_all
    from extract import get_article_text

    sections = collect_all()
    for name, stories in sections.items():
        story = stories[0]
        text, kind = get_article_text(story)
        result = summarize_story(story, text)
        print(f"\n=== {name}: {story['title']}")
        if not result:
            print("FAILED")
            continue
        print("Suitable:", result.get("suitable"), "-", result.get("reason"))
        if result.get("suitable"):
            print("Headline:", result.get("headline"))
            print("Summary:", result.get("summary"))
        time.sleep(5)