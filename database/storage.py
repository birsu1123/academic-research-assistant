
import hashlib

from database.supabase import get_supabase_client
from processing.pdf_parser import extract_pdf_pages
from processing.chunking import create_chunks
from processing.metadata_extractor import extract_paper_metadata
from rag.embeddings import embed_chunks


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


def save_research_paper(uploaded_file, metadata=None):
    supabase = get_supabase_client()

    file_bytes = uploaded_file.getvalue()
    file_hash = get_file_hash(file_bytes)

    collection_id = get_or_create_collection()

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

    # Use reviewed metadata if provided.
    # Otherwise, extract candidate metadata automatically.
    if metadata is None:
        metadata = extract_paper_metadata(pages)

    title = metadata.get("title") or uploaded_file.name
    authors = metadata.get("authors") or []
    year = metadata.get("publication_year")

    if not isinstance(authors, list):
        raise ValueError("Authors must be a list of names.")

    if year is not None:
        if isinstance(year, bool) or not isinstance(year, int):
            raise ValueError(
                "Publication year must be an integer or None."
            )

    # Split text into chunks
    chunks = create_chunks(pages)

    if not chunks:
        raise ValueError("No extractable text found in PDF.")

    # Generate embeddings
    embedded_chunks = embed_chunks(chunks)

    # Create document record with bibliographic metadata
    document_response = (
        supabase.table("documents")
        .insert({
            "collection_id": collection_id,
            "document_type": "research_paper",
            "title": title,
            "authors": authors,
            "publication_year": year,
            "filename": uploaded_file.name,
            "file_hash": file_hash,
        })
        .execute()
    )

    document_id = document_response.data[0]["id"]

    records = []

    for chunk in embedded_chunks:
        records.append({
            "document_id": document_id,
            "content": chunk["content"].replace("\x00", ""),
            "page_number": chunk["page_number"],
            "chunk_index": chunk["chunk_index"],
            "embedding": chunk["embedding"],
        })

    try:
        batch_size = 20

        for start in range(0, len(records), batch_size):
            batch = records[start:start + batch_size]

            supabase.table("document_chunks").insert(
                batch
            ).execute()

    except Exception:
        supabase.table("documents").delete().eq(
            "id", document_id
        ).execute()
        raise

    return {
        "status": "saved",
        "document_id": document_id,
        "pages": len(pages),
        "chunks": len(records),
        "metadata": {
            "title": title,
            "authors": authors,
            "publication_year": year,
        }
    }


def list_research_papers():
    supabase = get_supabase_client()

    response = (
        supabase.table("documents")
        .select(
            "id, title, filename, authors, publication_year"
        )
        .eq("document_type", "research_paper")
        .order("created_at", desc=True)
        .execute()
    )

    return response.data


def update_paper_metadata(document_id, metadata):
    supabase = get_supabase_client()

    updates = {
        "title": metadata["title"],
        "authors": metadata["authors"],
        "publication_year": metadata["publication_year"],
    }

    response = (
        supabase.table("documents")
        .update(updates)
        .eq("id", document_id)
        .eq("document_type", "research_paper")
        .execute()
    )

    if not response.data:
        raise ValueError("Research paper not found.")

    return response.data[0]
