from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from ats_match.domain import Job, Requirement, Resume

ROOT = Path(__file__).resolve().parent.parent
MAX_UPLOAD_BYTES = 2 * 1024 * 1024


def load_samples() -> tuple[Job, list[Resume], dict]:
    raw = json.loads((ROOT / "data" / "sample_workspace.json").read_text())
    return (
        Job.model_validate(raw["job"]),
        [Resume.model_validate(r) for r in raw["resumes"]],
        raw["labels"],
    )


def make_job(title: str, description: str, requirements: str) -> Job:
    lines = [
        line.strip().removeprefix("- ").strip()
        for line in requirements.splitlines()
        if line.strip()
    ]
    return Job(
        title=title.strip(),
        description=description.strip(),
        requirements=[Requirement(id=f"R{i:02d}", text=text) for i, text in enumerate(lines, 1)],
    )


def read_resume(name: str, content: bytes, index: int) -> Resume:
    if len(content) > MAX_UPLOAD_BYTES:
        raise ValueError("Each resume must be smaller than 2 MB.")
    suffix = Path(name).suffix.lower()
    if suffix == ".txt":
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError("Save this text file as UTF-8 and upload it again.") from exc
    elif suffix == ".pdf":
        if not content.startswith(b"%PDF-"):
            raise ValueError("This file does not contain a valid PDF header.")
        try:
            reader = PdfReader(BytesIO(content))
            if reader.is_encrypted:
                raise ValueError("Upload an unencrypted PDF or paste its text.")
            if len(reader.pages) > 12:
                raise ValueError("Use a resume with at most 12 pages.")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("This PDF could not be read. Upload a text version instead.") from exc
        if len(text.strip()) < 20:
            raise ValueError("No readable resume text was found. Scanned PDFs need OCR first.")
    else:
        raise ValueError("Upload a text-based PDF or a UTF-8 .txt file.")
    if len(text) > 25_000:
        raise ValueError("Keep each resume below 25,000 characters.")
    return Resume(id=f"U{index:02d}", label=Path(name).stem[:160], text=text.strip())
