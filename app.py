import streamlit as st

from app.config import load_app_config
from app.gsheets import get_spreadsheet
from app.interview import interview_prep_page
from app.resume import resume_page
from app.ui import sidebar_setup_help


st.set_page_config(page_title="Resume and Interview Prep", page_icon=":briefcase:", layout="wide")


def main():
    sidebar_setup_help()
    config = load_app_config()
    spreadsheet = get_spreadsheet()

    page = st.sidebar.selectbox("Navigate", ["Resume", "Interview Prep"])
    if page == "Resume":
        resume_page(spreadsheet, config)
    else:
        interview_prep_page(spreadsheet, config)


if __name__ == "__main__":
    main()
