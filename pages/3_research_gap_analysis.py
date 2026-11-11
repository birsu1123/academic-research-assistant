
import streamlit as st

from database.storage import list_research_papers
from rag.literature_matrix import build_literature_matrix
from rag.research_gaps import generate_research_gaps


# ==========================================
# PAGE HEADER
# ==========================================

st.title("Research Gap Analysis")

st.write(
    "Identify potential research gaps, unresolved "
    "questions and limitations within selected "
    "academic literature."
)


# ==========================================
# 1. LOAD RESEARCH PAPERS
# ==========================================

papers = list_research_papers()

if not papers:
    st.info(
        "Your research library is empty. "
        "Upload research papers first."
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
    key="gap_selected_papers"
)

selected_ids = {
    paper_options[name]
    for name in selected_papers
}


# ==========================================
# 3. RESEARCH TOPIC
# ==========================================

topic = st.text_area(
    "Research topic or question",
    placeholder=(
        "e.g. How does managerial turnover "
        "affect football team performance?"
    ),
    height=100,
    key="gap_research_topic"
)


# ==========================================
# 4. GENERATE RESEARCH GAPS
# ==========================================

can_generate = (
    len(selected_ids) >= 2
    and bool(topic.strip())
)

if st.button(
    "Identify research gaps",
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
            "Retrieving evidence and analysing "
            "potential research gaps..."
        ):

            rows, evidence = build_literature_matrix(
                selected_records
            )

            paper_ids = [
                paper["id"]
                for paper in selected_records
            ]

            gaps = generate_research_gaps(
                rows=rows,
                evidence_by_paper=evidence,
                paper_ids=paper_ids,
                topic=topic
            )

        st.session_state["gap_analysis_result"] = gaps

        st.session_state["gap_analysis_inputs"] = {
            "paper_ids": selected_ids.copy(),
            "topic": topic.strip()
        }

    except Exception as error:
        st.exception(error)


# ==========================================
# 5. DISPLAY RESEARCH GAPS
# ==========================================

saved_inputs = st.session_state.get(
    "gap_analysis_inputs", {}
)

show_results = (
    "gap_analysis_result" in st.session_state
    and saved_inputs.get("paper_ids") == selected_ids
    and saved_inputs.get("topic") == topic.strip()
)

if show_results:

    st.divider()
    st.subheader("Potential Research Gaps")

    gaps = st.session_state["gap_analysis_result"]

    st.markdown(gaps)

    st.download_button(
        "Download research gap analysis",
        data=gaps,
        file_name="research_gap_analysis.md",
        mime="text/markdown"
    )

    st.caption(
        "The identified gaps are based on the "
        "selected papers. Additional literature "
        "searches are required before establishing "
        "whether a gap exists across the research field."
    )

elif not can_generate:

    st.caption(
        "Select at least 2 papers and enter a "
        "research topic to begin."
    )
