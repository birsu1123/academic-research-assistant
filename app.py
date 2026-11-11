
import streamlit as st

st.set_page_config(
    page_title="Academic Research Assistant",
    page_icon="📚",
    layout="wide"
)

# Home page
home = st.Page(
    "home_content.py",
    title="Home",
    icon=":material/home:",
    default=True
)

# Literature Research page
literature = st.Page(
    "pages/1_literature_research.py",
    title="Literature Research",
    icon=":material/menu_book:"
)

# Literature Comparison page
comparison = st.Page(
    "pages/2_literature_comparison.py",
    title="Literature Comparison",
    icon=":material/table_chart:"
)

# Navigation
navigation = st.navigation([
    home,
    literature,
    comparison
])

navigation.run()
