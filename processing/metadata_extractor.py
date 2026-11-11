
import json
import re

from langchain_core.prompts import ChatPromptTemplate
from llm.model import get_model


METADATA_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """
You extract bibliographic metadata from academic papers.


Return only a valid JSON object with these fields:

{{
    "title": null,
    "authors": [],
    "publication_year": null
}}


Rules:
1. Extract the actual article title, not the PDF filename.
2. Extract author names exactly as shown in the document.
3. Return authors as a list of strings.
4. Extract the publication year only when explicitly supported.
5. Do not confuse cited references with the article's authors.
6. Do not confuse a year in the references with the publication year.
7. Never invent missing information.
8. Use null for an unknown title or publication year.
9. Use an empty list for unknown authors.
10. Do not include explanations or Markdown.
"""
    ),
    (
        "human",
        "Extract bibliographic metadata from this article:\n\n{text}"
    )
])


def extract_paper_metadata(pages):
    first_pages = "\n\n".join(
        page["text"]
        for page in pages[:2]
    )

    if not first_pages.strip():
        return {
            "title": None,
            "authors": [],
            "publication_year": None
        }

    model = get_model()
    chain = METADATA_PROMPT | model

    response = chain.invoke({
        "text": first_pages[:12000]
    })

    content = str(response.content).strip()

    # Remove possible Markdown code fences
    content = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        content
    ).strip()

    try:
        data = json.loads(content)
    except (json.JSONDecodeError, TypeError):
        return {
            "title": None,
            "authors": [],
            "publication_year": None
        }

    if not isinstance(data, dict):
        return {
            "title": None,
            "authors": [],
            "publication_year": None
        }

    title = data.get("title")
    authors = data.get("authors", [])
    year = data.get("publication_year")

    if not isinstance(title, str) or not title.strip():
        title = None
    else:
        title = title.replace("\x00", "").strip()

    if not isinstance(authors, list):
        authors = []

    authors = [
        author.replace("\x00", "").strip()
        for author in authors
        if isinstance(author, str)
        and author.replace("\x00", "").strip()
    ]

    if isinstance(year, bool):
        year = None
    elif isinstance(year, str):
        year = int(year) if re.fullmatch(r"\d{4}", year.strip()) else None
    elif not isinstance(year, int):
        year = None

    if year is not None and not (1800 <= year <= 2100):
        year = None

    return {
        "title": title,
        "authors": authors,
        "publication_year": year
    }
