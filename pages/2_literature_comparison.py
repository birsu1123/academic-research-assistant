
import pandas as pd
import streamlit as st

from database.storage import list_research_papers
from rag.literature_matrix import build_literature_matrix


# ==========================================
# PAGE HEADER
# ==========================================

st.title("Literature Comparison")

st.write(
    "Compare research designs, datasets, methods, "
    "findings and limitations across multiple papers."
)


# ==========================================
# 1. LOAD SAVED PAPERS
# ==========================================

papers = list_research_papers()

if not papers:
    st.info(
        "Your research library is empty. "
        "Upload papers on the Literature Research page."
    )
    st.stop()


# ==========================================
# 2. SELECT PAPERS
# ==========================================

paper_options = {
    f"{paper['title']} ({paper['id'][:8]})": paper["id"]
    for paper in papers
}

selected_papers = st.multiselect(
    "Select at least 2 research papers",
    options=list(paper_options.keys())
)

selected_ids = {
    paper_options[name]
    for name in selected_papers
}


# ==========================================
# 3. GENERATE COMPARISON MATRIX
# ==========================================

if len(selected_ids) >= 2:

    if st.button(
        "Generate comparison matrix",
        type="primary"
    ):

        selected_records = [
            paper
            for paper in papers
            if paper["id"] in selected_ids
        ]

        try:
            with st.spinner(
                "Analysing and comparing selected papers..."
            ):

                rows, evidence = build_literature_matrix(
                    selected_records
                )

            # Store generated results
            st.session_state["comparison_rows"] = rows

            st.session_state["comparison_evidence"] = evidence

            st.session_state["comparison_ids"] = (
                selected_ids.copy()
            )

        except Exception as error:
            st.exception(error)

else:
    st.caption(
        "Select at least 2 papers to enable comparison."
    )


# ==========================================
# 4. DISPLAY COMPARISON MATRIX
# ==========================================

show_matrix = (
    len(selected_ids) >= 2
    and "comparison_rows" in st.session_state
    and st.session_state.get("comparison_ids") == selected_ids
)

if show_matrix:

    st.divider()

    st.subheader("Literature Comparison Matrix")

    # Convert comparison results to DataFrame
    matrix_df = pd.DataFrame(
        st.session_state["comparison_rows"]
    )

    # Display papers as columns and categories as rows
    matrix_df = matrix_df.set_index("Paper").T

    matrix_df.index.name = "Comparison Category"

    # Configure paper columns
    column_config = {
        paper: st.column_config.TextColumn(
            paper,
            width="large"
        )
        for paper in matrix_df.columns
    }

    # Display comparison matrix
    st.dataframe(
        matrix_df,
        use_container_width=True,
        height=500,
        column_config=column_config
    )


    # ======================================
    # 5. DOWNLOAD COMPARISON MATRIX
    # ======================================

    st.download_button(
        label="Download matrix as CSV",
        data=matrix_df.to_csv().encode("utf-8-sig"),
        file_name="literature_comparison_matrix.csv",
        mime="text/csv"
    )


    # ======================================
    # 6. VIEW SUPPORTING EVIDENCE
    # ======================================

    with st.expander("View supporting evidence"):

        evidence = st.session_state.get(
            "comparison_evidence", {}
        )

        for paper_id, documents in evidence.items():

            for index, doc in enumerate(
                documents,
                start=1
            ):

                title = doc.metadata.get(
                    "title",
                    str(paper_id)
                )

                page = doc.metadata.get(
                    "page_number",
                    "Unknown"
                )

                st.markdown(
                    f"**{title} — "
                    f"Source {index}, Page {page}**"
                )

                st.write(doc.page_content)

                st.divider()
