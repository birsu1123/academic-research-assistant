from typing import Any

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from pydantic import Field

from rag.retrieval import retrieve_documents


class SupabasePaperRetriever(BaseRetriever):
    document_ids: list[str] = Field(default_factory=list)
    top_k: int = 5

    def _get_relevant_documents(
        self,
        query: str,
        *,
        run_manager: Any = None,
    ) -> list[Document]:

        results = retrieve_documents(
            question=query,
            document_ids=self.document_ids,
            top_k=self.top_k,
        )

        return [
            Document(
                page_content=result["content"],
                metadata={
                    "document_id": result["document_id"],
                    "title": result["title"],
                    "page_number": result["page_number"],
                    "similarity": result["similarity"],
                },
            )
            for result in results
        ]