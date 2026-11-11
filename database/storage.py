import hashlib

from database.supabase import get_supabase_client
from processing.pdf_parser import extract_pdf_pages
from processing.chunking import create_chunks
from rag.embeddings import embed_chunks
from io import BytesIO


COLLECTION_NAME = "My Research Library"


def get_file_hash(file_bytes):
    return hashlib.sha256(file_bytes).hexdigest()


def get_or_create_collection():
    supabase = get_supabase_client()

    response = (
        supabase.table("collections")
        .select("id")
        .eq("name", COLLECTION_NAME)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]["id"]

    response = (
        supabase.table("collections")
        .insert({"name": COLLECTION_NAME})
        .execute()
    )

    return response.data[0]["id"]


def save_research_paper(uploaded_file):
    supabase = get_supabase_client()

    file_bytes = uploaded_file.getvalue()
    file_hash = get_file_hash(file_bytes)

    collection_id = get_or_create_collection()

    # Check whether the PDF was previously uploaded
    existing = (
        supabase.table("documents")
        .select("id, title")
        .eq("collection_id", collection_id)
        .eq("file_hash", file_hash)
        .limit(1)
        .execute()
    )

    if existing.data:
        return {
            "status": "already_exists",
            "document_id": existing.data[0]["id"],
        }

    # Extract PDF text

    pages = extract_pdf_pages(uploaded_file)

    # Split text into chunks
    chunks = create_chunks(pages)

    if not chunks:
        raise ValueError("No extractable text found in PDF.")

    # Generate embeddings
    embedded_chunks = embed_chunks(chunks)

    # Create document record
    document_response = (
        supabase.table("documents")
        .insert({
            "collection_id": collection_id,
            "document_type": "research_paper",
            "title": uploaded_file.name,
            "filename": uploaded_file.name,
            "file_hash": file_hash,
        })
        .execute()
    )

    document_id = document_response.data[0]["id"]

    # Prepare chunk records
    records = []

    for chunk in embedded_chunks:
        records.append({
            "document_id": document_id,
            "content": chunk["content"],
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"],
            "embedding": chunk["embedding"],
        })

    # Insert in batches
    try:
        batch_size = 20

        for start in range(0, len(records), batch_size):
            batch = records[start:start + batch_size]

            supabase.table("document_chunks").insert(
                batch
            ).execute()

    except Exception:
        # Remove partial document and its chunks
        supabase.table("documents").delete().eq(
            "id", document_id
        ).execute()
        raise

    return {
        "status": "saved",
        "document_id": document_id,
        "pages": len(pages),
        "chunks": len(records),
    }

def list_research_papers():
    supabase = get_supabase_client()

    response = (
        supabase.table("documents")
        .select("id, title, filename")
        .eq("document_type", "research_paper")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data