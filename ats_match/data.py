from __future__ import annotations

import json
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from ats_match.domain import Job, Requirement, Resume

ROOT = Path(__file__).resolve().parent.parent
MAX_UPLOAD_BYTES = 2 * 1024 * 1024


@dataclass(frozen=True)
class Opening:
    id: str
    department: str
    location: str
    employment_type: str
    job: Job


def load_openings() -> list[Opening]:
    raw = json.loads((ROOT / "data" / "job_openings.json").read_text())
    return [Opening(**{**item, "job": Job.model_validate(item["job"])}) for item in raw]


def load_application_samples() -> tuple[Job, list[Resume], dict]:
    raw = json.loads((ROOT / "data" / "application_profiles.json").read_text())
    job = next(o.job for o in load_openings() if o.id == raw["opening_id"])
    resumes = []
    labels = {}
    for index, profile in enumerate(raw["profiles"], 1):
        content = (ROOT / "output" / "pdf" / "resumes" / profile["filename"]).read_bytes()
        resume = read_resume(profile["filename"], content, index)
        resumes.append(resume)
        labels[resume.id] = profile["labels"]
    return job, resumes, labels


def application_reference(job: Job, resumes: list[Resume]):
    """Return reference labels only for unchanged bundled PDF text and job criteria."""
    reference_job, reference_resumes, labels = load_application_samples()
    if job.model_dump(mode="json") != reference_job.model_dump(mode="json"):
        return None
    by_text = {r.text: labels[r.id] for r in reference_resumes}
    if not resumes or any(r.text not in by_text for r in resumes):
        return None
    return reference_job, resumes, {r.id: by_text[r.text] for r in resumes}


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
