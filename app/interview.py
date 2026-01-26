import pandas as pd
import streamlit as st

from app.ui import find_column


def interview_prep_page(spreadsheet, config):
    st.title("Interview Preparation")

    questions_sheet = config["interview"]["questions_sheet"]
    worksheet_name = st.text_input("Questions worksheet name", value=questions_sheet)
    try:
        worksheet = spreadsheet.worksheet(worksheet_name)
    except Exception:
        st.error(f"Worksheet '{worksheet_name}' not found.")
        st.stop()

    records = worksheet.get_all_records()
    for i, rec in enumerate(records, start=2):
        rec["_row"] = i
    df = pd.DataFrame(records)
    if df.empty:
        st.warning("No questions found. Add rows in Google Sheets to populate.")
        return

    category_col = find_column(df, ["category", "topic", "section"]) or "category"
    question_col = find_column(df, ["question", "prompt"]) or "question"
    answer_col = find_column(df, ["answer", "response"]) or "answer"
    difficulty_col = find_column(df, ["difficulty", "level"])
    tags_col = find_column(df, ["tags", "tag"])

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

    for category, group in (
        filtered.groupby(category_col) if category_col in filtered else [("Questions", filtered)]
    ):
        st.subheader(category)
        for _, row in group.iterrows():
            question = str(row.get(question_col, "")).strip()
            if not question:
                continue
            meta = []
            if difficulty_col and row.get(difficulty_col):
                meta.append(f"Difficulty: {row[difficulty_col]}")
            if tags_col and row.get(tags_col):
                meta.append(f"Tags: {row[tags_col]}")
            with st.expander(question):
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
