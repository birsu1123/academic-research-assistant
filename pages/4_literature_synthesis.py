
import streamlit as st

from database.storage import list_research_papers
from rag.literature_matrix import build_literature_matrix
from rag.literature_synthesis import generate_literature_synthesis


# ==========================================
# PAGE HEADER
# ==========================================

st.title("Literature Synthesis")

st.write(
    "Generate a comparative academic discussion "
    "of selected research papers, including their "
    "methods, findings and limitations."
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
    options=list(paper_options.keys()),
    key="synthesis_selected_papers"
)

selected_ids = {
    paper_options[name]
    for name in selected_papers
}


# ==========================================
# 3. RESEARCH FOCUS
# ==========================================

topic = st.text_area(
    "Research focus (optional)",
    placeholder=(
        "e.g. How does managerial turnover "
        "affect football team performance?"
    ),
    height=100,
    key="synthesis_research_topic"
)


# ==========================================
# 4. GENERATE SYNTHESIS
# ==========================================

can_generate = len(selected_ids) >= 2

if st.button(
    "Generate literature synthesis",
    type="primary",
    disabled=not can_generate
):

    selected_records = [
        paper
        for paper in papers
        if paper["id"] in selected_ids
    ]

    try:
        with st.spinner(
            "Retrieving evidence and synthesising "
            "selected research papers..."
        ):

            rows, evidence = build_literature_matrix(
                selected_records
            )

            paper_ids = [
                paper["id"]
                for paper in selected_records
            ]
            paper_metadata = {
                paper["id"]: {
                    "title": paper.get("title"),
                    "authors": paper.get("authors") or [],
                    "publication_year": paper.get("publication_year")
                }
                for paper in selected_records
            }

            synthesis = generate_literature_synthesis(
                rows=rows,
                evidence_by_paper=evidence,
                paper_ids=paper_ids,
                topic=topic.strip(),
                paper_metadata=paper_metadata
            )

        st.session_state[
            "literature_synthesis_result"
        ] = synthesis

        st.session_state[
            "literature_synthesis_inputs"
        ] = {
            "paper_ids": selected_ids.copy(),
            "topic": topic.strip()
        }

    except Exception as error:
        st.exception(error)


# ==========================================
# 5. DISPLAY SYNTHESIS
# ==========================================

saved_inputs = st.session_state.get(
    "literature_synthesis_inputs", {}
)

show_results = (
    "literature_synthesis_result" in st.session_state
    and saved_inputs.get("paper_ids") == selected_ids
    and saved_inputs.get("topic") == topic.strip()
)

if show_results:

    st.divider()
    st.subheader("Cross-Paper Synthesis")

    synthesis = st.session_state[
        "literature_synthesis_result"
    ]

    st.markdown(synthesis)

    st.download_button(
        "Download synthesis",
        data=synthesis,
        file_name="literature_synthesis.md",
        mime="text/markdown"
    )

    st.caption(
        "Review generated claims and citations "
        "against the original research papers "
        "before using this synthesis in academic work."
    )

elif not can_generate:

    st.caption(
        "Select at least 2 papers to generate a synthesis."
    )
