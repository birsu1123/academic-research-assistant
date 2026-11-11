
from rag.langchain_retriever import SupabasePaperRetriever
from rag.reranker import rerank_documents
from rag.evidence_verifier import (
    VERIFICATION_PROMPT,
    parse_verification_response,
)
from llm.model import get_model


def recover_evidence(verification, documents):
    """
    Search the cited papers again for claims that are
    unsupported or partially supported.

    Return updated assessments and additional evidence.
    """
    recovered = []

    chain = VERIFICATION_PROMPT | get_model()

    for item in verification:
        updated = dict(item)
        updated["original_status"] = item["status"]
        updated["recovered_sources"] = []

        if item["status"] not in {
            "unsupported",
            "partially_supported",
        }:
            recovered.append(updated)
            continue

        source_numbers = item.get("source_numbers", [])

        cited_documents = [
            documents[number - 1]
            for number in source_numbers
            if 1 <= number <= len(documents)
        ]

        document_ids = {
            doc.metadata.get("document_id")
            for doc in cited_documents
            if doc.metadata.get("document_id")
        }

        # Do not search unrelated papers.
        if not document_ids:
            recovered.append(updated)
            continue

        candidates = []

        for document_id in document_ids:
            retriever = SupabasePaperRetriever(
                document_ids=[document_id],
                top_k=20,
            )

            candidates.extend(
                retriever.invoke(item["claim"])
            )

        if not candidates:
            recovered.append(updated)
            continue

        ranked = rerank_documents(
            question=item["claim"],
            documents=candidates,
            top_k=5,
        )

        # Recheck using original citations and new evidence.
        combined = cited_documents + ranked

        evidence = "\n\n".join(
            (
                f"Document: {doc.metadata.get('title', 'Unknown')}\n"
                f"Page: {doc.metadata.get('page_number', 'Unknown')}\n"
                f"Text: {doc.page_content}"
            )
            for doc in combined
        )

        try:
            response = chain.invoke({
                "claim": item["claim"],
                "evidence": evidence,
            })

            assessment = parse_verification_response(
                response.content
            )

            updated["status"] = assessment["status"]
            updated["explanation"] = assessment["explanation"]
            updated["recovered_sources"] = ranked

        except Exception as error:
            updated["recovery_error"] = str(error)

        recovered.append(updated)

    return recovered
