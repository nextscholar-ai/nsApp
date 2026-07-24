from datetime import date
from pathlib import Path
from typing import Any


def render_student_id_pdf(card: dict[str, Any], output_pdf_path: str) -> str:
    """Render a front-side student ID card as a PDF.

    Uses reportlab if available; otherwise generates a very simple placeholder PDF-like text file.
    """
    Path(output_pdf_path).parent.mkdir(parents=True, exist_ok=True)

    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import mm
        from reportlab.lib.utils import ImageReader
        from reportlab.pdfgen import canvas

        c = canvas.Canvas(output_pdf_path, pagesize=A4)
        width, height = A4

        # Border
        c.rect(10, 10, width - 20, height - 20)

        y = height - 30

        # Logo
        logo_path = card.get("institute_logo_path")
        if logo_path and Path(logo_path).exists():
            img = ImageReader(logo_path)
            c.drawImage(
                img,
                20,
                y - 35,
                width=35 * mm / 1.0,
                height=35 * mm / 1.0,
                mask="auto",
            )
        c.setFont("Helvetica-Bold", 14)
        c.drawString(70, y - 10, str(card.get("institute_name", "")))

        y -= 55
        c.setFont("Helvetica", 10)
        c.drawString(20, y, f"Contact: {card.get('institute_contact_number', '')}")
        y -= 16
        c.drawString(
            20,
            y,
            f"Academic Session: {card.get('academic_session_label', '')}",
        )

        # Student photo
        photo_path = card.get("student_photo_path")
        if photo_path and Path(photo_path).exists():
            c.drawImage(
                ImageReader(photo_path),
                width - 90,
                y - 120,
                60,
                80,
                mask="auto",
            )

        y -= 30
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20, y, "Student Details")
        y -= 18

        c.setFont("Helvetica", 10)
        c.drawString(20, y, f"Name: {card.get('student_name', '')}")
        y -= 14
        c.drawString(20, y, f"Parent Name: {card.get('parent_name', '')}")
        y -= 14
        c.drawString(20, y, f"Class: {card.get('class_display_name', '')}")
        y -= 14

        doj: date = card.get("date_of_joining")
        valid_till: date = card.get("valid_till")
        c.drawString(20, y, f"DOJ: {doj.isoformat() if isinstance(doj, date) else ''}")
        y -= 14
        c.drawString(
            20,
            y,
            f"Valid Till: {valid_till.isoformat() if isinstance(valid_till, date) else ''}",
        )
        y -= 14

        # Student ID
        c.setFont("Helvetica-Bold", 12)
        c.drawString(20, y, f"Student ID: {card.get('student_id_business', '')}")

        # QR
        qr_path = card.get("qr_code_path")
        if qr_path and Path(qr_path).exists():
            c.drawImage(ImageReader(qr_path), width - 110, 55, 80, 80, mask="auto")

        c.setFont("Helvetica", 9)
        c.drawString(width - 110, 40, "Scan to verify")

        c.showPage()
        c.save()
        return output_pdf_path

    except Exception:
        # Fallback: write a text file with .pdf extension (best-effort)
        with Path(output_pdf_path).open("wb") as f:
            f.write(("Student ID Card placeholder\n" + str(card)).encode("utf-8"))
        return output_pdf_path
