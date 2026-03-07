from __future__ import annotations

from io import BytesIO

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def build_report_pdf(patient: dict, result: dict) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    y = height - 56
    pdf.setTitle(result["title"])
    pdf.setFont("Helvetica-Bold", 22)
    pdf.drawString(48, y, "MyLab Official Report")

    y -= 36
    pdf.setFont("Helvetica", 12)
    pdf.drawString(48, y, f"Patient: {patient['first_name']} {patient['last_name']}")
    y -= 18
    pdf.drawString(48, y, f"Result: {result['title']}")
    y -= 18
    pdf.drawString(48, y, f"Date: {result['date']}")
    y -= 18
    pdf.drawString(48, y, f"Status: {result['status'].capitalize()}")

    y -= 32
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(48, y, "Summary")
    y -= 20
    pdf.setFont("Helvetica", 11)
    pdf.drawString(48, y, result["summary"])

    y -= 30
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(48, y, "Measured Values")
    y -= 24
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(48, y, "Parameter")
    pdf.drawString(230, y, "Value")
    pdf.drawString(330, y, "Reference")
    pdf.drawString(460, y, "Status")

    y -= 16
    pdf.setFont("Helvetica", 10)
    for value in result["values"]:
        pdf.drawString(48, y, value["name"])
        pdf.drawString(230, y, f"{value['value']} {value['unit']}")
        pdf.drawString(330, y, value["reference_range"])
        pdf.drawString(460, y, value["status"].capitalize())
        y -= 16
        if y < 100:
            pdf.showPage()
            y = height - 56

    y -= 16
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(48, y, "Explanation")
    y -= 20
    pdf.setFont("Helvetica", 11)
    text = pdf.beginText(48, y)
    text.setLeading(14)
    text.textLines(result["explanation"])
    pdf.drawText(text)

    y = text.getY() - 18
    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(48, y, "Suggested Action")
    y -= 20
    pdf.setFont("Helvetica", 11)
    action_text = pdf.beginText(48, y)
    action_text.setLeading(14)
    action_text.textLines(result["recommended_action"])
    pdf.drawText(action_text)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
