from database.supabase import get_supabase_client
from rag.embeddings import get_embeddings


def retrieve_documents(question, document_ids, top_k=5):
    """
    Search selected research papers using cosine similarity.
    """

    if not document_ids:
        return []

    # Generate an embedding for the question
    embeddings = get_embeddings()
    query_embedding = embeddings.embed_query(question)

    # Search stored embeddings in Supabase
    supabase = get_supabase_client()

    response = supabase.rpc(
        "match_document_chunks",
        {
            "query_embedding": query_embedding,
            "match_count": top_k,
            "filter_document_ids": document_ids,
        }
    ).execute()

    return response.data