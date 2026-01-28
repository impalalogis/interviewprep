import json

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]


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
def get_spreadsheet(
    sheet_id: str | None = None,
    sheet_url: str | None = None,
    secret_id_key: str | None = None,
    secret_url_key: str | None = None,
):
    client = get_gspread_client()
    if not sheet_id and secret_id_key:
        sheet_id = st.secrets.get(secret_id_key)
    if not sheet_url and secret_url_key:
        sheet_url = st.secrets.get(secret_url_key)
    if not sheet_id:
        sheet_id = st.secrets.get("spreadsheet_id")
    if not sheet_url:
        sheet_url = st.secrets.get("spreadsheet_url")
    if sheet_id:
        return client.open_by_key(sheet_id)
    if sheet_url:
        return client.open_by_url(sheet_url)
    st.error("Set spreadsheet_id/spreadsheet_url or resume/interview sheet IDs in st.secrets.")
    st.stop()


@st.cache_data(ttl=60)
def read_worksheet_df(_spreadsheet, title):
    try:
        worksheet = _spreadsheet.worksheet(title)
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
