
import streamlit as st
from sentence_transformers import CrossEncoder


@st.cache_resource(show_spinner="Loading reranking model...")
def get_reranker():
    return CrossEncoder(
        "cross-encoder/ms-marco-MiniLM-L-6-v2",
        device="cpu"
    )


def rerank_documents(question, documents, top_k=5):
    if not documents:
        return []

    model = get_reranker()

    pairs = [
        (question, document.page_content)
        for document in documents
    ]

    scores = model.predict(pairs)

    ranked = sorted(
        zip(documents, scores),
        key=lambda item: float(item[1]),
        reverse=True
    )

    return [
        document
        for document, score in ranked[:top_k]
    ]
