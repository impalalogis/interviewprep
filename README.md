# Streamlit Resume & Interview Prep App

Recruiter‑friendly Streamlit app that renders a resume and a dynamic interview prep library from Google Sheets. The app is modular, configurable, and ready for production deployment.

## Features
- **Resume page** sourced from Google Sheets with profile photo, structured sections, and a PDF download button.
- **Interview prep page** with per‑worksheet sections, search, add/update flows, and live Google Sheets sync.
- **Modular architecture** for reuse and easy extension.
- **Config + secrets** separated for industry‑standard deployment.

---

## Project Structure
```
.
├── app.py
├── app/
│   ├── __init__.py
│   ├── config.py
│   ├── gsheets.py
│   ├── interview.py
│   ├── resume.py
│   └── ui.py
├── config/
│   └── app_config.yaml
├── .streamlit/
│   ├── config.toml
│   └── secrets.toml.template
└── README.md
```

---

## Setup

### 1) Install dependencies
```
pip install -r requirements.txt
```

### 2) Configure Streamlit secrets
Create `.streamlit/secrets.toml` based on the template:
```
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
```
Update values with your Google service account and the two spreadsheet IDs (resume + interview).

### 3) Configure app behavior
Edit `config/app_config.yaml` to set worksheet names and field keys.

### 4) Run the app
```
streamlit run app.py
```

---

## Google Sheets Schema

### Profile (worksheet: `profile`) — Resume Sheet
| key | value |
|-----|-------|
| name | Your name |
| title | Role title |
| email | email@example.com |
| phone | +1‑555‑555‑5555 |
| location | City, Country |
| linkedin | https://linkedin.com/in/... |
| github | https://github.com/... |
| website | https://... |
| photo_url | https://... (optional) |
| photo_path | local/path (optional) |
| resume_pdf_url | https://... (optional) |
| resume_pdf_path | local/path (optional) |

### Resume sections
Each worksheet should contain rows with these common columns:
- `title` / `role` / `project`
- `subtitle` / `company`
- `location`
- `duration` / `start` / `end`
- `details` (bullet text separated by line breaks or `;`)
- `link` (optional)

Recommended worksheets:
- `education`
- `experience`
- `projects`
- `skills` (columns: `category`, `skills`)

### Interview questions — Interview Sheet
Each worksheet is treated as a separate interview section/page.

Recommended columns per worksheet:
| category | question | answer | difficulty | tags |
|----------|----------|--------|-----------|------|

The app automatically reflects updates from Google Sheets without code changes.

---

## Notes
- Keep credentials **out of Git**. Only use `.streamlit/secrets.toml`.
- Use **service accounts** and share the sheet with the service account email.
- Update `config/app_config.yaml` if your worksheet names differ.

---

## Extensibility
You can add new pages by placing logic in `app/` and wiring it in `app.py`. Shared UI utilities live in `app/ui.py`.
