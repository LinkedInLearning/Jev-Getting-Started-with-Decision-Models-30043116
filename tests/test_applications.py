from pathlib import Path

from pypdf import PdfReader

from ats_match.data import ROOT, application_reference, load_application_samples, load_openings


def test_sample_pdfs_are_single_page_and_extract_as_resumes():
    job, resumes, labels = load_application_samples()
    assert job.title == "Python Backend Engineer"
    assert len(resumes) == len(labels) == 5
    for resume in resumes:
        path = ROOT / "output/pdf/resumes" / (resume.label + ".pdf")
        reader = PdfReader(path)
        assert len(reader.pages) == 1
        assert "Experience" in resume.text
        assert "Fictional applicant" in resume.text
        assert resume.label.replace("_", " ") in resume.text
        assert "Selected project" in resume.text
    assert Path(ROOT / "output/pdf/applicant-resumes.zip").is_file()


def test_reference_labels_follow_pdf_content_and_do_not_score_edited_jobs():
    job, resumes, _ = load_application_samples()
    # Upload order and filenames can change without changing the actual resume evidence.
    uploaded = [
        r.model_copy(update={"id": f"U{i:02d}", "label": f"renamed_{i}"})
        for i, r in enumerate(reversed(resumes), 1)
    ]
    reference = application_reference(job, uploaded)
    assert reference[2]["U01"]["matches"]["R01"] == "related"
    assert reference[2]["U05"]["matches"]["R01"] == "direct"
    changed = job.model_copy(update={"description": job.description + "\nChanged role."})
    assert application_reference(changed, uploaded) is None
    uploaded[0] = uploaded[0].model_copy(update={"text": uploaded[0].text + "\nNew evidence."})
    assert application_reference(job, uploaded) is None


def test_openings_have_distinct_job_descriptions_and_explicit_criteria():
    openings = load_openings()
    assert len({o.id for o in openings}) == 3
    assert len({o.job.description for o in openings}) == 3
    assert all(len(o.job.requirements) == 4 for o in openings)
