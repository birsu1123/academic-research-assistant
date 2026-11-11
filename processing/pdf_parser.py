
import pymupdf


def clean_pdf_text(text):
    """
    Remove null characters that PostgreSQL
    cannot store in text columns.
    """
    if not isinstance(text, str):
        return ""

    return text.replace("\x00", "").strip()


def extract_pdf_pages(pdf_file):
    """
    Extract and clean text from a PDF page by page.

    Returns:
        list[dict]: Page number and cleaned text.
    """

    pdf_bytes = pdf_file.getvalue()

    if not pdf_bytes:
        raise ValueError("The uploaded PDF is empty.")

    pages = []

    with pymupdf.open(
        stream=pdf_bytes,
        filetype="pdf"
    ) as document:

        for page_index, page in enumerate(document):

            text = page.get_text("text")

            cleaned_text = clean_pdf_text(text)

            pages.append({
                "page_number": page_index + 1,
                "text": cleaned_text
            })

    return pages
