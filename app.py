
import streamlit as st

st.set_page_config(
    page_title="Academic Research Assistant",
    page_icon="📚",
    layout="wide"
)

home = st.Page(
    "home_content.py",
    title="Home",
    icon=":material/home:",
    default=True
)

literature = st.Page(
    "pages/1_literature_research.py",
    title="Literature Research",
    icon=":material/menu_book:"
)

comparison = st.Page(
    "pages/2_literature_comparison.py",
    title="Literature Comparison",
    icon=":material/table_chart:"
)

synthesis = st.Page(
    "pages/4_literature_synthesis.py",
    title="Literature Synthesis",
    icon=":material/auto_stories:"
)

research_gaps = st.Page(
    "pages/3_research_gap_analysis.py",
    title="Research Gap Analysis",
    icon=":material/psychology:"
)

navigation = st.navigation([
    home,
    literature,
    comparison,
    synthesis,
    research_gaps
])

navigation.run()
