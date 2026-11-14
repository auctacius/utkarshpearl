"""Export every nonblank journal line, in order; no summary/truncation."""
from pathlib import Path
from html import escape
from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
P=Path(__file__).resolve().parents[1]
styles=getSampleStyleSheet()
styles['BodyText'].fontSize=9.5
styles['BodyText'].leading=13
styles['BodyText'].spaceAfter=6
styles['BodyText'].splitLongWords=True
story=[]
for line in (P/'docs/ENGINEERING_JOURNAL.md').read_text().splitlines():
    if not line.strip(): continue
    level=len(line)-len(line.lstrip('#'))
    style=styles['Heading1' if level==1 else 'Heading2' if level==2 else 'BodyText']
    story.append(Paragraph(escape(line.lstrip('#').strip()) if level else escape(line),style))
def footer(c,d):
    c.setFillColor(colors.HexColor('#526176'));c.setFont('Helvetica',8)
    c.drawString(42,24,'PIIParity | Engineering journal | Phase 1')
    c.drawRightString(570,24,str(d.page))
SimpleDocTemplate(str(P/'reports/PIIParity_Engineering_Journal.pdf'),pagesize=(612,792),rightMargin=42,leftMargin=42,topMargin=36,bottomMargin=36).build(story,onFirstPage=footer,onLaterPages=footer)
