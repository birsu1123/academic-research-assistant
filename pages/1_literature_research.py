
import pandas as pd
import streamlit as st

from processing.pdf_parser import extract_pdf_pages
from processing.chunking import create_chunks
from rag.embeddings import embed_chunks
from database.storage import (
    save_research_paper,
    list_research_papers,
)
from rag.qa import answer_question
from rag.evidence_verifier import verify_answer



st.title("Literature Review Assistant")

st.write(
    "Upload research papers, ask evidence-based questions, "
    "and compare findings across multiple studies."
)


# ==================================================
# 1. UPLOAD RESEARCH PAPER
# ==================================================

uploaded_file = st.file_uploader(
    "Upload a research paper",
    type=["pdf"]
)

if uploaded_file is not None:

    pages = extract_pdf_pages(uploaded_file)
    chunks = create_chunks(pages)
    embedded_chunks = embed_chunks(chunks)

    st.success(
        f"PDF processed successfully — {len(pages)} pages found."
    )

    # Temporary debugging: extracted text
    with st.expander("Preview extracted text"):
        for page in pages[:3]:
            st.subheader(f"Page {page['page_number']}")
            st.text(page["text"][:1500])

    # Temporary debugging: text chunks
    with st.expander("Preview text chunks"):
        for chunk in chunks[:5]:
            st.write(
                f"Chunk {chunk['chunk_index']} | "
                f"Page {chunk['page_number']}"
            )
            st.write(chunk["content"])
            st.divider()

    # Temporary debugging: embeddings
    if embedded_chunks:
        with st.expander("Embedding test"):

            vector = embedded_chunks[0]["embedding"]

            st.write(
                f"Embedding dimensions: {len(vector)}"
            )

            first_10 = [
                float(value)
                for value in vector[:10]
            ]

            df = pd.DataFrame({
                "Dimension": list(range(1, 11)),
                "Value": first_10
            })

            st.table(df)

    # Save uploaded paper
    if st.button("Save paper to research library"):

        with st.spinner(
            "Saving paper and embeddings to Supabase..."
        ):
            try:
                result = save_research_paper(
                    uploaded_file
                )

                if result["status"] == "already_exists":
                    st.info(
                        "This paper is already saved "
                        "in your library."
                    )
                else:
                    st.success(
                        f"Paper saved successfully! "
                        f"{result['pages']} pages and "
                        f"{result['chunks']} chunks stored."
                    )

            except Exception as error:
                st.error(
                    f"Upload failed: {error}"
                )


# ==================================================
# 2. RESEARCH LIBRARY
# ==================================================

st.divider()

st.subheader(
    "Ask questions about your research papers"
)

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

    selected_ids = [
        paper_options[name]
        for name in selected_papers
    ]

    selected_id_set = set(selected_ids)


    # ==================================================
    # 3. QUESTION ANSWERING
    # ==================================================

    question = st.text_input(
        "Your question:",
        placeholder=(
            "What methodology did the authors use?"
        )
    )

    if st.button(
        "Generate answer",
        type="primary"
    ):

        if not selected_papers:
            st.warning(
                "Please select at least one paper."
            )

        elif not question.strip():
            st.warning(
                "Please enter a question."
            )

        else:
            try:
                with st.spinner(
                    "Analysing selected papers..."
                ):
                    result = answer_question(
                        question=question,
                        document_ids=selected_ids
                    )

                st.session_state["rag_answer"] = result
                st.session_state["rag_question"] = question
                st.session_state["rag_paper_ids"] = (
                    selected_id_set.copy()
                )

                # Clear verification for the new answer
                st.session_state.pop(
                    "rag_verification",
                    None
                )

            except Exception as error:
                st.exception(error)


    # ==================================================
    # 4. DISPLAY ANSWER
    # ==================================================

    show_answer = (
        "rag_answer" in st.session_state
        and st.session_state.get(
            "rag_paper_ids"
        ) == selected_id_set
    )

    if show_answer:

        result = st.session_state["rag_answer"]

        st.subheader("Answer")
        st.markdown(result["answer"])

        citation_check = result.get(
            "citation_check", {}
        )

        citation_count = citation_check.get(
            "citations_found", 0
        )

        if not citation_check.get("valid", True):

            st.warning(
                "The answer contains invalid source "
                f"references: "
                f"{citation_check.get('invalid_citations', [])}"
            )

        elif (
            citation_count == 0
            and result.get("sources")
        ):
            st.warning(
                "No source citations were found "
                "in the answer."
            )


        # ==============================================
        # 5. OPTIONAL EVIDENCE VERIFICATION
        # ==============================================

        if st.button("Verify evidence"):

            with st.spinner(
                "Checking citations and evidence..."
            ):
                try:
                    verification = verify_answer(
                        answer=result["answer"],
                        documents=result["sources"]
                    )

                    st.session_state[
                        "rag_verification"
                    ] = verification

                except Exception as error:
                    st.exception(error)


        verification = st.session_state.get(
            "rag_verification", []
        )

        if verification:

            st.subheader(
                "Evidence Verification"
            )

            counts = {
                "supported": 0,
                "partially_supported": 0,
                "unsupported": 0,
                "unclear": 0
            }

            for item in verification:
                status = item.get(
                    "status", "unclear"
                )

                if status not in counts:
                    status = "unclear"

                counts[status] += 1

            col1, col2, col3, col4 = st.columns(4)

            col1.metric(
                "Supported",
                counts["supported"]
            )

            col2.metric(
                "Partial",
                counts["partially_supported"]
            )

            col3.metric(
                "Unsupported",
                counts["unsupported"]
            )

            col4.metric(
                "Unclear",
                counts["unclear"]
            )

            with st.expander(
                "View claim-level verification",
                expanded=True
            ):

                for index, item in enumerate(
                    verification,
                    start=1
                ):

                    status = item.get(
                        "status", "unclear"
                    )

                    st.markdown(
                        f"**Claim {index} — "
                        f"{status.replace('_', ' ').title()}**"
                    )

                    st.write(
                        item.get("claim", "")
                    )

                    st.caption(
                        item.get("explanation", "")
                    )

                    original_status = item.get(
                        "original_status"
                    )

                    if (
                        original_status
                        and original_status != status
                    ):
                        st.write(
                            "Initial assessment: "
                            f"{original_status.replace('_', ' ').title()} "
                            "→ After retrieval: "
                            f"{status.replace('_', ' ').title()}"
                        )

                    # Compatible with recovered evidence,
                    # if recovery is enabled in the future.
                    recovered_sources = item.get(
                        "recovered_sources", []
                    )

                    if recovered_sources:

                        with st.expander(
                            "View additional retrieved evidence"
                        ):

                            for doc in recovered_sources:

                                title = doc.metadata.get(
                                    "title",
                                    "Unknown paper"
                                )

                                page = doc.metadata.get(
                                    "page_number",
                                    "Unknown"
                                )

                                st.markdown(
                                    f"**{title} — Page {page}**"
                                )

                                st.write(
                                    doc.page_content
                                )

                    st.divider()


        # ==============================================
        # 6. SUPPORTING PASSAGES
        # ==============================================

        with st.expander(
            "View supporting passages"
        ):

            for i, doc in enumerate(
                result.get("sources", []),
                start=1
            ):

                title = doc.metadata.get(
                    "title",
                    "Unknown paper"
                )

                page = doc.metadata.get(
                    "page_number",
                    "Unknown"
                )

                st.markdown(
                    f"**[Source {i}] {title} "
                    f"— Page {page}**"
                )

                st.write(
                    doc.page_content
                )

                st.divider()

else:

    st.info(
        "No saved papers found. "
        "Upload a PDF first."
    )
