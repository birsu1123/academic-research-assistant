
import streamlit as st

st.set_page_config(
    page_title="Academic Research Assistant",
    page_icon="📚",
    layout="wide"
)

st.title("Academic Research Assistant")

st.write(
    """
    An AI-powered academic research assistant using
    Retrieval-Augmented Generation (RAG) and language models
    to support literature research. Users can upload and
    manage academic papers, ask questions about their content,
    and receive evidence-based answers with source citations.

    The application is being developed to compare research
    questions, methodologies, datasets, findings, and
    limitations across multiple studies, organise information
    into structured literature matrices, and synthesise
    research findings to identify agreements, disagreements,
    and research gaps.
    """
)
