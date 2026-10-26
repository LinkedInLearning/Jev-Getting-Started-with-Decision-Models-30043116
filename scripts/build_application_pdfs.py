"""Build the five fictional application PDFs used in the course recording."""

import json
from pathlib import Path
from xml.sax.saxutils import escape
from zipfile import ZIP_DEFLATED, ZipFile

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "output" / "pdf" / "resumes"


def build():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    profiles = json.loads((ROOT / "data" / "application_profiles.json").read_text())["profiles"]
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            "Applicant",
            fontName="Helvetica-Bold",
            fontSize=27,
            leading=31,
            textColor=colors.HexColor("#172522"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            "Position",
            fontName="Helvetica",
            fontSize=12,
            leading=17,
            textColor=colors.HexColor("#40564d"),
            spaceAfter=5,
        )
    )
    styles.add(
        ParagraphStyle(
            "Contact",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#65736c"),
            spaceAfter=19,
        )
    )
    styles.add(
        ParagraphStyle(
            "SectionName",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#213d32"),
            spaceBefore=15,
            spaceAfter=7,
        )
    )
    styles.add(
        ParagraphStyle(
            "Copy",
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=colors.HexColor("#26352e"),
            alignment=TA_LEFT,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            "RoleName",
            parent=styles["Copy"],
            fontName="Helvetica-Bold",
            spaceBefore=7,
            spaceAfter=3,
        )
    )
    styles.add(
        ParagraphStyle(
            "Employer",
            parent=styles["Copy"],
            textColor=colors.HexColor("#65736c"),
            fontSize=9,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            "Point", parent=styles["Copy"], leftIndent=10, firstLineIndent=-8, spaceAfter=5
        )
    )

    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor("#dce3df"))
        canvas.line(45, 38, doc.pagesize[0] - 45, 38)
        canvas.setFillColor(colors.HexColor("#738078"))
        canvas.setFont("Helvetica", 7)
        canvas.drawString(45, 25, "Fictional application prepared for training.")
        canvas.drawRightString(doc.pagesize[0] - 45, 25, str(doc.page))

    for profile in profiles:
        target = OUTPUT / profile["filename"]
        doc = SimpleDocTemplate(
            str(target),
            pagesize=(8.5 * inch, 11 * inch),
            rightMargin=45,
            leftMargin=45,
            topMargin=43,
            bottomMargin=49,
            title=f"{profile['name']} | Resume",
            author="Fictional course applicant",
        )
        story = []

        def text(value, style="Copy", story=story):
            story.append(Paragraph(escape(value), styles[style]))

        text(profile["name"], "Applicant")
        text(profile["title"], "Position")
        text(profile["email"], "Contact")
        text("Profile", "SectionName")
        text(profile["summary"])
        text("Technical skills", "SectionName")
        text(profile["skills"])
        text("Experience", "SectionName")
        for role in profile["experience"]:
            text(role["role"], "RoleName")
            text(f"{role['company']} | {role['dates']}", "Employer")
            for point in role["bullets"]:
                text(f"- {point}", "Point")
        text("Selected project", "SectionName")
        text(profile["project"]["title"], "RoleName")
        text(profile["project"]["text"])
        story.append(Spacer(1, 2))
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        print(target.relative_to(ROOT))
    archive = OUTPUT.parent / "applicant-resumes.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for profile in profiles:
            bundle.write(OUTPUT / profile["filename"], profile["filename"])
    print(archive.relative_to(ROOT))


if __name__ == "__main__":
    build()
