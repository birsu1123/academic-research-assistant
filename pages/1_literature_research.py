import streamlit as st

from processing.pdf_parser import extract_pdf_pages
from processing.chunking import create_chunks
from rag.embeddings import embed_chunks
import pandas as pd
from database.storage import save_research_paper
from database.storage import list_research_papers
from rag.retrieval import retrieve_documents
from rag.langchain_retriever import SupabasePaperRetriever
from rag.qa import answer_question


st.title("Literature Review Assistant")

st.write(
    "Upload a research paper and ask questions based on its content."
)

uploaded_file = st.file_uploader(
    "Upload a research paper",
    type=["pdf"]
)

if uploaded_file is not None:

    pages = extract_pdf_pages(uploaded_file)
    chunks = create_chunks(pages)
    embedded_chunks = embed_chunks(chunks)

    st.success(f"PDF processed successfully — {len(pages)} pages found.")

    # Temporary debugging section
    with st.expander("Preview extracted text"):
        for page in pages[:3]:

            st.subheader(f"Page {page['page_number']}")

            st.text(
                page["text"][:1500]
            )

    with st.expander("Preview text chunks"):

        for chunk in chunks[:5]:

            st.write(
                f"Chunk {chunk['chunk_index']} | "
                f"Page {chunk['page_number']}"
            )

            st.write(chunk["content"])

            st.divider()


    if uploaded_file is not None and embedded_chunks:

        with st.expander("Embedding test"):

            vector = embedded_chunks[0]["embedding"]

            st.write(f"Embedding dimensions: {len(vector)}")

            first_10 = [float(value) for value in vector[:10]]

            df = pd.DataFrame({
                "Dimension": list(range(1, 11)),
                "Value": first_10
            })

            st.table(df)
    
    if st.button("Save paper to research library"):

        with st.spinner("Saving paper and embeddings to Supabase..."):

            try:
                result = save_research_paper(uploaded_file)

                if result["status"] == "already_exists":
                    st.info(
                        "This paper is already saved in your library."
                )

                else:
                    st.success(
                        f"Paper saved successfully! "
                        f"{result['pages']} pages and "
                        f"{result['chunks']} chunks stored."
                )

            except Exception as error:
                st.error(f"Upload failed: {error}")

st.divider()
st.subheader("Ask questions about your research papers")

# Get saved papers from Supabase
papers = list_research_papers()

if papers:
    paper_options = {
        f"{paper['title']} ({paper['id'][:8]})": paper["id"]
        for paper in papers
    }

    selected_papers = st.multiselect(
        "Select research papers",
        options=list(paper_options.keys())
    )

    question = st.text_input(
        "Your question:",
        placeholder="What methodology did the authors use?"
    )


    # ----------------------------------
    # BUTTON 1: GENERATE ANSWER WITH QWEN
    # ----------------------------------

    if st.button("Generate answer", type="primary"):

        if not selected_papers:
            st.warning("Please select at least one paper.")

        elif not question.strip():
            st.warning("Please enter a question.")

        else:
            selected_ids = [
                paper_options[name]
                for name in selected_papers
            ]

            try:
                with st.spinner("Analysing selected papers..."):
                    result = answer_question(
                        question=question,
                        document_ids=selected_ids
                    )

                st.session_state["rag_answer"] = result
                st.session_state["rag_question"] = question

            except Exception as error:
                st.exception(error)

    # Display the generated answer
    if "rag_answer" in st.session_state:
        result = st.session_state["rag_answer"]

        st.subheader("Answer")
        st.markdown(result["answer"])

        citation_check = result.get("citation_check", {})
        citation_count = citation_check.get("citations_found", 0)

        if not citation_check.get("valid", True):
            st.warning(
                "The answer contains invalid source references: "
            f"{citation_check.get('invalid_citations', [])}"
            )
        elif citation_count == 0 and result.get("sources"):
            st.info(
              "No source citations were found in the answer. "
               "The answer may indicate insufficient evidence."
            )

        with st.expander("View supporting passages"):
            for i, doc in enumerate(result.get("sources", []), start=1):
                title = doc.metadata.get("title", "Unknown paper")
                page = doc.metadata.get("page_number", "Unknown")

                st.markdown(
                    f"**[Source {i}] {title} — Page {page}**"
                )
                st.write(doc.page_content)
                st.divider()


else:
    st.info("No saved papers found. Upload a PDF first.")