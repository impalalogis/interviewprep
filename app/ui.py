from pathlib import Path

import streamlit as st


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


def find_column(df, candidates):
    cols = {c.lower(): c for c in df.columns}
    for name in candidates:
        if name.lower() in cols:
            return cols[name.lower()]
    return None


def sidebar_setup_help():
    with st.sidebar.expander("Setup help"):
        st.write("Add these to .streamlit/secrets.toml:")
        st.code(
            """
resume_spreadsheet_id = "RESUME_SHEET_ID"
interview_spreadsheet_id = "INTERVIEW_SHEET_ID"

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


def render_profile_image(photo_value):
    if not photo_value:
        return
    if str(photo_value).startswith("http"):
        st.image(photo_value, width=150)
        return
    path = Path(photo_value)
    if path.exists():
        st.image(str(path), width=150)
