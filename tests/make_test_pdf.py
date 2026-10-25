"""Build small stand-in Tax Code PDFs for testing (cover edition line + many 'residence homestead' hits)."""
import sys
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def build(path, year):
    c = canvas.Canvas(path, pagesize=letter)
    c.setFont("Helvetica-Bold", 28)
    c.drawString(72, 600, "")
    c.showPage()
    c.setFont("Helvetica-Bold", 28)
    c.drawString(90, 520, "TEXAS PROPERTY TAX CODE")
    c.drawString(90, 480, f"{year} EDITION")
    c.showPage()
    for pg in range(12):
        c.setFont("Helvetica-Bold", 12)
        c.drawString(72, 740, f"Sec. 11.{13 + pg}. Residence Homestead Provisions Part {pg + 1}")
        c.setFont("Helvetica", 11)
        y = 715
        for line in range(26):
            c.drawString(72, y, f"({line + 1}) An individual is entitled to an exemption for the residence homestead as provided here.")
            y -= 26
        c.showPage()
    c.save()


if __name__ == "__main__":
    build(sys.argv[1], 2025)
    build(sys.argv[2], 2024)
