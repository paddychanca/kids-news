import json
import os
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader, select_autoescape


def edition_date(iso):
    dt = datetime.fromisoformat(iso)
    try:
        from zoneinfo import ZoneInfo
        dt = dt.astimezone(ZoneInfo("America/Edmonton"))
    except Exception:
        dt = dt.astimezone(timezone.utc)
    return f"{dt:%A, %B} {dt.day}"


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def build():
    with open("data/edition.json", encoding="utf-8") as f:
        edition = json.load(f)

    sections = {k: v for k, v in edition["sections"].items() if v}

    env = Environment(
        loader=FileSystemLoader("templates"),
        autoescape=select_autoescape(["html", "j2"]),
    )
    template = env.get_template("index.html.j2")
    html = template.render(
        sections=sections,
        date=edition_date(edition["generated"]),
        css=read("static/style.css"),
        js=read("static/app.js"),
    )

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    total = sum(len(v) for v in sections.values())
    print(f"Built docs/index.html with {total} stories in {len(sections)} categories")


if __name__ == "__main__":
    build()