
from langchain_core.prompts import ChatPromptTemplate

from llm.model import get_model


# ==========================================
# BUILD SHARED PAPER CONTEXT
# ==========================================


def build_paper_context(
    rows,
    evidence_by_paper,
    paper_ids,
    paper_metadata=None,
    max_sources=6,
    max_chars_per_source=1200
):
    if len(rows) != len(paper_ids):
        raise ValueError(
            "Paper rows and IDs must have matching lengths."
        )

    paper_metadata = paper_metadata or {}
    sections = []

    for index, (row, paper_id) in enumerate(
        zip(rows, paper_ids),
        start=1
    ):
        metadata = paper_metadata.get(paper_id, {})

        title = metadata.get("title") or row["Paper"]
        authors = metadata.get("authors") or []
        year = metadata.get("publication_year")

        authors_text = (
            ", ".join(authors)
            if isinstance(authors, list) and authors
            else "Unknown"
        )

        year_text = (
            str(year) if year is not None else "Unknown"
        )

        section = [
            f"Study identifier: {index}",
            f"Article title: {title}",
            f"Authors: {authors_text}",
            f"Publication year: {year_text}",
            "EXTRACTED COMPARISON MATRIX:"
        ]

        for field, value in row.items():
            if field != "Paper":
                section.append(f"{field}: {value}")

        documents = evidence_by_paper.get(
            paper_id, []
        )

        section.append("SUPPORTING PASSAGES:")

        for number, doc in enumerate(
            documents[:max_sources],
            start=1
        ):
            page = doc.metadata.get(
                "page_number", "Unknown"
            )

            section.append(
                f"[Study {index}, Source {number}]\n"
                f"Page: {page}\n"
                f"Text: {doc.page_content[:max_chars_per_source]}"
            )

        sections.append("\n\n".join(section))

    return "\n\n---\n\n".join(sections)


# ==========================================
# CROSS-PAPER SYNTHESIS PROMPT
# ==========================================

SYNTHESIS_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an academic literature review assistant.

Generate a comparative synthesis of selected papers.

Rules:
1. Use only the supplied evidence.
2. Compare studies where meaningful.
3. Distinguish research aims from findings.
4. Do not invent information or citations.
5. Cite passages as [Paper 1, Source 2].
6. Preserve uncertainty.
7. Do not claim unrelated studies have conflicting results.
8. Use clear academic English.

Structure:

### Research designs and approaches
### Datasets and samples
### Analytical methods
### Findings across studies
### Limitations and comparability

Study attribution rules:

1. Never refer to studies as "Paper 1",
   "Paper 2", "the first paper", or
   "the second paper" in the written synthesis.

2. Use verified author surnames and publication
   years when these are provided in the context.

3. If verified author and year metadata are
   unavailable, refer to the study by its
   article title.

4. Never invent author names, publication
   years or bibliographic citations.

5. Do not infer author names or publication
   years from filenames.

6. Do not use example names or years from
   these instructions as actual citations.

7. Keep source evidence references separate
   from bibliographic citations.

8. If only a filename is available, use the
   filename or a neutral description of
   the study instead of inventing a citation.


Write connected paragraphs."""
    ),
    (
        "human",
        """Research topic:
{topic}

Selected papers and evidence:
{context}

Generate the synthesis."""
    )
])


# ==========================================
# GENERATE CROSS-PAPER SYNTHESIS
# ==========================================

def generate_literature_synthesis(
    rows,
    evidence_by_paper,
    paper_ids,
    topic="",
    paper_metadata=None
):
    context = build_paper_context(
        rows=rows,
        evidence_by_paper=evidence_by_paper,
        paper_ids=paper_ids,
        paper_metadata=paper_metadata
    )

    model = get_model()

    chain = SYNTHESIS_PROMPT | model

    response = chain.invoke({
        "topic": topic or "Not specified",
        "context": context
    })

    return str(response.content)
