import streamlit as st

from langchain_huggingface import HuggingFaceEmbeddings


@st.cache_resource(show_spinner="Loading embedding model...")
def get_embeddings():

    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-small-en-v1.5",
        model_kwargs={"device": "mps"},
        encode_kwargs={"normalize_embeddings": True}
    )


def embed_chunks(chunks):

    embeddings = get_embeddings()

    texts = [chunk["content"] for chunk in chunks]

    vectors = embeddings.embed_documents(texts)

    return [
        {**chunk, "embedding": vector}
        for chunk, vector in zip(chunks, vectors)
    ]