
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

navigation = st.navigation([home, literature])
navigation.run()
