# Sample applications

The five one-page PDFs in `resumes/` are fictional applications for the built-in **Python Backend Engineer** role.
Upload them together in RoleMatch.
The same files are bundled in `applicant-resumes.zip`.

The applications include direct backend experience, an adjacent testing framework, data engineering, unclear deployment evidence, and a different backend language.
Names and contact details are not assessment criteria.

Editable source content is in `data/application_profiles.json`.
Rebuild the PDFs and bundle from the repository root:

```bash
uv run --with reportlab python scripts/build_application_pdfs.py
```
