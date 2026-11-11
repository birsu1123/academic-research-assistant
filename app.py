import streamlit as st


st.set_page_config(
    page_title="Academic Research Assistant",
    page_icon="🎓",
    layout="wide"
)


# Home page
home = st.Page(
    "pages/home.py",
    title="Academic Research Assistant",
    icon="🎓",
    default=True
)


# Literature research
literature_assistant = st.Page(
    "pages/1_literature_research.py",
    title="Literature Research Assistant",
    icon="📚"
)




# Navigation
navigation = st.navigation(
    {
        "Home": [
            home
        ],
        "Research Tools": [
            literature_assistant
        ],
        "Publication Tools": [
            journal_submission
        ]
    }
)


navigation.run()