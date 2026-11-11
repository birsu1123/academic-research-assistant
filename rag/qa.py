
import re

from langchain_core.prompts import ChatPromptTemplate
from rag.langchain_retriever import SupabasePaperRetriever
from llm.model import get_model


PROMPT = ChatPromptTemplate.from_messages([
    (
        "system",
        """You are an academic research assistant.

Answer the user's question using only the retrieved passages.

Rules:
1. Discuss each selected paper separately, using its document title.
2. For methodology questions, describe the research design,
   data, sample, and analytical methods only when supported.
3. Do not infer a paper's methodology from references to
   other studies or from general discussion passages.
4. Cite factual statements using [Source 1], [Source 2], etc.
5. Every citation must refer to a supplied source.
6. If evidence is insufficient for a paper, state this clearly.
7. Do not invent findings, methods, citations, or references.
8. Distinguish what the authors did from what they cited.

Selected papers:
{paper_list}

Retrieved passages:
{context}"""
    ),
    ("human", "{question}")
])


def validate_citations(answer, documents):
    numbers = re.findall(
        r"\[Source\s+(\d+)\]",
        answer,
        flags=re.IGNORECASE
    )

    valid_numbers = set(range(1, len(documents) + 1))
    invalid = [
        int(number)
        for number in numbers
        if int(number) not in valid_numbers
    ]

    return {
        "valid": len(invalid) == 0,
        "invalid_citations": invalid,
        "citations_found": len(numbers)
    }


def answer_question(question, document_ids):
    if not document_ids:
        return {
            "answer": "Please select at least one research paper.",
            "sources": [],
            "citation_check": validate_citations("", [])
        }

    documents = []
    paper_names = []

    # Retrieve evidence independently for each paper.
    for document_id in dict.fromkeys(document_ids):
        retriever = SupabasePaperRetriever(
            document_ids=[document_id],
            top_k=5
        )

        paper_documents = retriever.invoke(question)
        documents.extend(paper_documents)

        if paper_documents:
            paper_names.append(
                paper_documents[0].metadata.get(
                    "title", str(document_id)
                )
            )
        else:
            paper_names.append(str(document_id))

    if not documents:
        return {
            "answer": (
                "No relevant passages were retrieved "
                "from the selected papers."
            ),
            "sources": [],
            "citation_check": validate_citations("", [])
        }

    context = "\n\n".join(
        (
            f"[Source {i}]\n"
            f"Document: {doc.metadata.get('title', 'Unknown')}\n"
            f"Page: {doc.metadata.get('page_number', 'Unknown')}\n"
            f"Text: {doc.page_content}"
        )
        for i, doc in enumerate(documents, start=1)
    )

    response = (PROMPT | get_model()).invoke({
        "question": question,
        "paper_list": "\n".join(
            f"- {name}" for name in paper_names
        ),
        "context": context
    })

    answer = response.content
    if not isinstance(answer, str):
        answer = str(answer)

    citation_check = validate_citations(answer, documents)

    return {
        "answer": answer,
        "sources": documents,
        "citation_check": citation_check
    }
