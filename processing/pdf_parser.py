import pymupdf


def extract_pdf_pages(pdf_file):
    """
    Extract text from a PDF page by page.

    Returns:
        list[dict]: Each dictionary contains the page number and text.
    """

    pdf_bytes = pdf_file.getvalue()

    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    pages = []

    with pymupdf.open(stream=pdf_bytes, filetype="pdf") as document:

        for page_index, page in enumerate(document):
            text = page.get_text("text")

            pages.append(
                {
                    "page_number": page_index + 1,
                    "text": text.strip()
                }
            )

    return pages