from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(override=True)

READER_MODEL = "gemini-3.1-flash-lite"
client = genai.Client()

READ_PROMPT = """Open this news article and write a detailed factual digest of it in your own words: every key fact, name, number, date and place, in the order the article gives them. Do not add anything that is not in the article. If you cannot open the page, reply with exactly: CANNOT_READ

URL: __URL__
"""


def retrieved_ok(response):
    try:
        for m in response.candidates[0].url_context_metadata.url_metadata:
            if "SUCCESS" in str(m.url_retrieval_status):
                return True
    except Exception:
        pass
    return False


def read_with_gemini(url):
    try:
        r = client.models.generate_content(
            model=READER_MODEL,
            contents=READ_PROMPT.replace("__URL__", url),
            config=types.GenerateContentConfig(
                tools=[types.Tool(url_context=types.UrlContext())]
            ),
        )
    except Exception as err:
        print(f"  note: Gemini could not read page ({err})")
        return None
    text = (r.text or "").strip()
    if not retrieved_ok(r) or text.startswith("CANNOT_READ") or len(text) < 200:
        return None
    return text


if __name__ == "__main__":
    from collect import load_feeds, get_stories

    story = get_stories(load_feeds()["Animals"])[0]
    print("Testing:", story["title"])
    print(story["link"])
    text = read_with_gemini(story["link"])
    if text:
        print("SUCCESS,", len(text), "characters")
        print(text[:500])
    else:
        print("FAILED to read")