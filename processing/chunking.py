from langchain_text_splitters import RecursiveCharacterTextSplitter


text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    length_function=len
)


def create_chunks(pages):
    """
    Split extracted PDF pages into smaller text chunks
    while preserving the original page number.
    """

    chunks = []
    chunk_index = 0

    for page in pages:

        page_chunks = text_splitter.split_text(page["text"])

        for text in page_chunks:

            chunks.append({
                "content": text,
                "page_number": page["page_number"],
                "chunk_index": chunk_index
            })

            chunk_index += 1

    return chunks