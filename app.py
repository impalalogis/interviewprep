import json
from io import BytesIO
from pathlib import Path

import gspread
import pandas as pd
import requests
import streamlit as st
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


st.set_page_config(page_title="Resume and Interview Prep", page_icon=":briefcase:", layout="wide")


def _load_service_account():
    if "gcp_service_account" in st.secrets:
        return st.secrets["gcp_service_account"]
    if "gcp_service_account_json" in st.secrets:
        try:
            return json.loads(st.secrets["gcp_service_account_json"])
        except json.JSONDecodeError:
            st.error("Invalid gcp_service_account_json in st.secrets.")
            st.stop()
    st.error("Missing Google service account credentials in st.secrets.")
    st.stop()


@st.cache_resource
def get_gspread_client():
    sa_info = _load_service_account()
    creds = Credentials.from_service_account_info(sa_info, scopes=SCOPES)
    return gspread.authorize(creds)


@st.cache_resource
def get_spreadsheet():
    client = get_gspread_client()
    sheet_id = st.secrets.get("spreadsheet_id")
    sheet_url = st.secrets.get("spreadsheet_url")
    if sheet_id:
        return client.open_by_key(sheet_id)
    if sheet_url:
        return client.open_by_url(sheet_url)
    st.error("Set spreadsheet_id or spreadsheet_url in st.secrets.")
    st.stop()


@st.cache_data(ttl=60)
def read_worksheet_df(spreadsheet, title):
    try:
        worksheet = spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        return pd.DataFrame()
    records = worksheet.get_all_records()
    return pd.DataFrame(records)


def get_kv_sheet(spreadsheet, title):
    df = read_worksheet_df(spreadsheet, title)
    if df.empty:
        return {}
    if "key" in df.columns and "value" in df.columns:
        return dict(zip(df["key"], df["value"]))
    return {}


def split_bullets(text):
    if not text:
        return []
    if isinstance(text, list):
        return text
    raw = str(text).replace("\r", "\n")
    parts = [p.strip("- ").strip() for p in raw.split("\n") if p.strip()]
    if len(parts) <= 1:
        parts = [p.strip() for p in str(text).split(";") if p.strip()]
    return parts


def render_section(title, df):
    if df.empty:
        return
    st.subheader(title)
    for _, row in df.iterrows():
        header = row.get("title") or row.get("item") or row.get("name") or row.get("role")
        if not header:
            header = row.get("company") or row.get("project") or row.get("degree")
        if header:
            st.markdown(f"**{header}**")
        meta_parts = [
            row.get("subtitle"),
            row.get("company"),
            row.get("location"),
            row.get("duration"),
            row.get("start"),
            row.get("end"),
        ]
        meta = " | ".join([str(m) for m in meta_parts if m])
        if meta:
            st.caption(meta)
        details = row.get("details") or row.get("description") or row.get("summary")
        for bullet in split_bullets(details):
            st.write(f"- {bullet}")
        link = row.get("link")
        if link:
            st.markdown(f"[Link]({link})")
        st.write("")


def resume_page(spreadsheet):
    st.title("Professional Resume")

    profile = get_kv_sheet(spreadsheet, "profile")
    photo = profile.get("photo_url") or profile.get("photo_path")
    if photo:
        if str(photo).startswith("http"):
            st.image(photo, width=150)
        else:
            path = Path(photo)
            if path.exists():
                st.image(str(path), width=150)

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

    pdf_url = profile.get("resume_pdf_url")
    pdf_path = profile.get("resume_pdf_path")
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

    for section in ["education", "experience", "projects"]:
        df = read_worksheet_df(spreadsheet, section)
        if not df.empty:
            render_section(section.title(), df)

    skills_df = read_worksheet_df(spreadsheet, "skills")
    if not skills_df.empty:
        st.subheader("Skills")
        if "category" in skills_df.columns and "skills" in skills_df.columns:
            for _, row in skills_df.iterrows():
                st.markdown(f"**{row['category']}**: {row['skills']}")
        elif "skill" in skills_df.columns:
            st.write(", ".join(skills_df["skill"].dropna().astype(str).tolist()))


def _find_column(df, candidates):
    cols = {c.lower(): c for c in df.columns}
    for name in candidates:
        if name.lower() in cols:
            return cols[name.lower()]
    return None


def interview_prep_page(spreadsheet):
    st.title("Interview Preparation")

    worksheet_name = st.text_input("Questions worksheet name", value="questions")
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except gspread.WorksheetNotFound:
        st.error(f"Worksheet '{worksheet_name}' not found.")
        st.stop()

    records = worksheet.get_all_records()
    for i, rec in enumerate(records, start=2):
        rec["_row"] = i
    df = pd.DataFrame(records)
    if df.empty:
        st.warning("No questions found. Add rows in Google Sheets to populate.")
        return

    category_col = _find_column(df, ["category", "topic", "section"]) or "category"
    question_col = _find_column(df, ["question", "prompt"]) or "question"
    answer_col = _find_column(df, ["answer", "response"]) or "answer"
    difficulty_col = _find_column(df, ["difficulty", "level"])
    tags_col = _find_column(df, ["tags", "tag"])

    categories = sorted([c for c in df[category_col].dropna().unique()]) if category_col in df else []
    selected_category = st.selectbox("Category", ["All"] + categories)
    search = st.text_input("Search questions")

    filtered = df.copy()
    if selected_category != "All" and category_col in filtered:
        filtered = filtered[filtered[category_col] == selected_category]
    if search:
        mask = filtered[question_col].astype(str).str.contains(search, case=False, na=False)
        if answer_col in filtered:
            mask = mask | filtered[answer_col].astype(str).str.contains(search, case=False, na=False)
        filtered = filtered[mask]

    for category, group in filtered.groupby(category_col) if category_col in filtered else [("Questions", filtered)]:
        st.subheader(category)
        for _, row in group.iterrows():
            q = str(row.get(question_col, "")).strip()
            if not q:
                continue
            meta = []
            if difficulty_col and row.get(difficulty_col):
                meta.append(f"Difficulty: {row[difficulty_col]}")
            if tags_col and row.get(tags_col):
                meta.append(f"Tags: {row[tags_col]}")
            with st.expander(q):
                if meta:
                    st.caption(" | ".join(meta))
                st.write(row.get(answer_col, ""))

    st.divider()
    st.subheader("Add a new question")
    with st.form("add_question_form"):
        new_category = st.text_input("Category")
        new_question = st.text_area("Question")
        new_answer = st.text_area("Answer")
        new_difficulty = st.text_input("Difficulty (optional)")
        new_tags = st.text_input("Tags (optional)")
        submitted = st.form_submit_button("Add question")
    if submitted:
        headers = worksheet.row_values(1)
        row = []
        for header in headers:
            h = header.lower()
            if h == category_col.lower():
                row.append(new_category)
            elif h == question_col.lower():
                row.append(new_question)
            elif h == answer_col.lower():
                row.append(new_answer)
            elif difficulty_col and h == difficulty_col.lower():
                row.append(new_difficulty)
            elif tags_col and h == tags_col.lower():
                row.append(new_tags)
            else:
                row.append("")
        worksheet.append_row(row, value_input_option="USER_ENTERED")
        st.success("Question added. Refresh to see updates.")

    st.subheader("Edit an existing question")
    choices = [
        f"{row['_row']}: {str(row.get(question_col, ''))[:80]}"
        for _, row in df.iterrows()
    ]
    selected = st.selectbox("Select question", choices)
    if selected:
        row_num = int(selected.split(":")[0])
        existing = df[df["_row"] == row_num].iloc[0].to_dict()
        with st.form("edit_question_form"):
            edit_category = st.text_input("Category", value=str(existing.get(category_col, "")))
            edit_question = st.text_area("Question", value=str(existing.get(question_col, "")))
            edit_answer = st.text_area("Answer", value=str(existing.get(answer_col, "")))
            edit_difficulty = st.text_input(
                "Difficulty (optional)",
                value=str(existing.get(difficulty_col, "")) if difficulty_col else "",
            )
            edit_tags = st.text_input(
                "Tags (optional)",
                value=str(existing.get(tags_col, "")) if tags_col else "",
            )
            updated = st.form_submit_button("Update question")
        if updated:
            header_map = {h.lower(): i + 1 for i, h in enumerate(worksheet.row_values(1))}
            worksheet.update_cell(row_num, header_map[category_col.lower()], edit_category)
            worksheet.update_cell(row_num, header_map[question_col.lower()], edit_question)
            worksheet.update_cell(row_num, header_map[answer_col.lower()], edit_answer)
            if difficulty_col:
                worksheet.update_cell(row_num, header_map[difficulty_col.lower()], edit_difficulty)
            if tags_col:
                worksheet.update_cell(row_num, header_map[tags_col.lower()], edit_tags)
            st.success("Question updated. Refresh to see changes.")


def sidebar_setup_help():
    with st.sidebar.expander("Setup help"):
        st.write("Add these to .streamlit/secrets.toml:")
        st.code(
            """
spreadsheet_id = "YOUR_SHEET_ID"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "..."
client_id = "..."
token_uri = "https://oauth2.googleapis.com/token"
            """.strip()
        )


def main():
    sidebar_setup_help()
    spreadsheet = get_spreadsheet()

    page = st.sidebar.selectbox("Navigate", ["Resume", "Interview Prep"])
    if page == "Resume":
        resume_page(spreadsheet)
    else:
        interview_prep_page(spreadsheet)


if __name__ == "__main__":
    main()
