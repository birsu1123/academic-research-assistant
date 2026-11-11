
import json
import re

from langchain_core.prompts import ChatPromptTemplate

from llm.model import get_model
from rag.langchain_retriever import SupabasePaperRetriever
from rag.reranker import rerank_documents


FIELDS = {
    "research_design": "Research design",
    "dataset": "Dataset",
    "sample": "Sample",
    "analytical_methods": "Analytical methods",
    "main_findings": "Main findings",
    "limitations": "Limitations",
}

EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You extract information from academic papers.

Use only the passages supplied from the selected paper.

Rules:
1. Describe the authors' own research, not studies they cite.
2. Do not invent methods, datasets, findings or limitations.
3. If a field is not established, write "Not established".
4. Include source numbers for supported information.
5. Return only a JSON object with these exact keys:
   research_design, dataset, sample,
   analytical_methods, main_findings, limitations.
6. Every value must be a string.
7. Use citations such as [Source 1] in the values."""
    ),
    (
        "human",
        "Paper: {title}\n\nEvidence:\n{context}"
    )
])


def parse_json(content):
    if not isinstance(content, str):
        content = str(content)

    content = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        content.strip()
    ).strip()

    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        data = {}

    if not isinstance(data, dict):
        data = {}

    return {
        field: str(data.get(field, "Not established"))
        for field in FIELDS
    }


def build_literature_matrix(papers):
    """
    papers: list of dictionaries containing 'id' and 'title'.
    """
    rows = []
    evidence_by_paper = {}

    for paper in papers:
        document_id = paper["id"]
        title = paper["title"]

        queries = [
            "research design dataset sample data collection methodology",
            "statistical analysis estimation model analytical methods",
            "main findings results conclusions limitations",
        ]

        candidates = []

        for query in queries:
            retriever = SupabasePaperRetriever(
                document_ids=[document_id],
                top_k=12
            )
            candidates.extend(retriever.invoke(query))

        # Remove duplicate retrieved passages.
        unique = {}

        for doc in candidates:
            key = (
                doc.metadata.get("document_id"),
                doc.metadata.get("page_number"),
                doc.page_content
            )
            unique[key] = doc

        ranked = rerank_documents(
            question=(
                "Identify the paper's research design, dataset, "
                "sample, analytical methods, main findings "
                "and limitations."
            ),
            documents=list(unique.values()),
            top_k=10
        )

        context = "\n\n".join(
            f"[Source {i}] Page "
            f"{doc.metadata.get('page_number', 'Unknown')}\n"
            f"{doc.page_content}"
            for i, doc in enumerate(ranked, start=1)
        )

        if not ranked:
            extracted = {
                field: "Not established"
                for field in FIELDS
            }
        else:
            response = (
                EXTRACTION_PROMPT | get_model()
            ).invoke({
                "title": title,
                "context": context
            })
            extracted = parse_json(response.content)

        rows.append({
            "Paper": title,
            **{
                label: extracted[field]
                for field, label in FIELDS.items()
            }
        })

        evidence_by_paper[document_id] = ranked

    return rows, evidence_by_paper
