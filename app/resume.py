from pathlib import Path

import requests
import streamlit as st

from app.gsheets import get_kv_sheet, read_worksheet_df
from app.ui import render_profile_image, render_section


def resume_page(spreadsheet, config):
    st.title("Professional Resume")

    resume_cfg = config["resume"]
    profile = get_kv_sheet(spreadsheet, resume_cfg["profile_sheet"])
    render_profile_image(profile.get(resume_cfg["photo_url_key"]) or profile.get(resume_cfg["photo_path_key"]))

    name = profile.get("name", "Your Name")
    title = profile.get("title", "Data Engineer")
    st.header(name)
    st.write(title)

    contact_cols = st.columns(3)
    contact_cols[0].write(profile.get("email", ""))
    contact_cols[1].write(profile.get("phone", ""))
    contact_cols[2].write(profile.get("location", ""))

    link_cols = st.columns(3)
    linkedin = profile.get("linkedin")
    github = profile.get("github")
    website = profile.get("website")
    if linkedin:
        link_cols[0].markdown(f"[LinkedIn]({linkedin})")
    if github:
        link_cols[1].markdown(f"[GitHub]({github})")
    if website:
        link_cols[2].markdown(f"[Website]({website})")

    pdf_url = profile.get(resume_cfg["resume_pdf_url_key"])
    pdf_path = profile.get(resume_cfg["resume_pdf_path_key"])
    if pdf_url:
        try:
            response = requests.get(pdf_url, timeout=20)
            response.raise_for_status()
            st.download_button(
                "Download Resume (PDF)",
                data=response.content,
                file_name="resume.pdf",
                mime="application/pdf",
            )
        except requests.RequestException:
            st.warning("Resume PDF URL is not reachable.")
    elif pdf_path and Path(pdf_path).exists():
        with open(pdf_path, "rb") as file:
            st.download_button(
                "Download Resume (PDF)",
                data=file.read(),
                file_name=Path(pdf_path).name,
                mime="application/pdf",
            )

    st.divider()

    for section in [
        resume_cfg["education_sheet"],
        resume_cfg["experience_sheet"],
        resume_cfg["projects_sheet"],
    ]:
        df = read_worksheet_df(spreadsheet, section)
        if not df.empty:
            render_section(section.title(), df)

    skills_df = read_worksheet_df(spreadsheet, resume_cfg["skills_sheet"])
    if not skills_df.empty:
        st.subheader("Skills")
        if "category" in skills_df.columns and "skills" in skills_df.columns:
            for _, row in skills_df.iterrows():
                st.markdown(f"**{row['category']}**: {row['skills']}")
        elif "skill" in skills_df.columns:
            st.write(", ".join(skills_df["skill"].dropna().astype(str).tolist()))
