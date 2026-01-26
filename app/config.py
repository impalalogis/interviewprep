from __future__ import annotations

from pathlib import Path

import yaml


DEFAULT_CONFIG = {
    "resume": {
        "profile_sheet": "profile",
        "education_sheet": "education",
        "experience_sheet": "experience",
        "projects_sheet": "projects",
        "skills_sheet": "skills",
        "photo_url_key": "photo_url",
        "photo_path_key": "photo_path",
        "resume_pdf_url_key": "resume_pdf_url",
        "resume_pdf_path_key": "resume_pdf_path",
    },
    "interview": {
        "questions_sheet": "questions",
    },
}


def load_app_config(config_path: str | Path = "/workspace/config/app_config.yaml") -> dict:
    path = Path(config_path)
    if not path.exists():
        return DEFAULT_CONFIG
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    merged = DEFAULT_CONFIG.copy()
    merged["resume"] = {**DEFAULT_CONFIG["resume"], **data.get("resume", {})}
    merged["interview"] = {**DEFAULT_CONFIG["interview"], **data.get("interview", {})}
    return merged
