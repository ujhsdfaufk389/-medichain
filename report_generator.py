import io
import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer,
    Table, TableStyle, HRFlowable
)
from reportlab.lib.colors import HexColor


def generate_report(case_data: dict, decision: dict,
                    band_messages: list) -> bytes:
    """
    PDF report generate karo aur bytes return karo.
    Streamlit download button ke liye.
    """
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize     = A4,
        leftMargin   = 20*mm,
        rightMargin  = 20*mm,
        topMargin    = 20*mm,
        bottomMargin = 20*mm,
    )

    # Styles
    NAVY  = HexColor("#0F172A")
    BLUE  = HexColor("#1D4ED8")
    GREEN = HexColor("#059669")
    RED   = HexColor("#DC2626")
    AMBER = HexColor("#D97706")
    LGRAY = HexColor("#F1F5F9")

    title_style = ParagraphStyle("title",
        fontName="Helvetica-Bold", fontSize=18,
        textColor=NAVY, spaceAfter=6)
    h2_style = ParagraphStyle("h2",
        fontName="Helvetica-Bold", fontSize=12,
        textColor=BLUE, spaceBefore=12, spaceAfter=4)
    body_style = ParagraphStyle("body",
        fontName="Helvetica", fontSize=9.5,
        textColor=NAVY, leading=14, spaceAfter=3)
    small_style = ParagraphStyle("small",
        fontName="Helvetica-Oblique", fontSize=8,
        textColor=HexColor("#64748B"), leading=12)

    story = []

    # Header
    story.append(Paragraph("MediChain AI", title_style))
    story.append(Paragraph(
        "Prior Authorization Review Report — AI-Assisted | Human Review Required",
        small_style))
    story.append(HRFlowable(width="100%", thickness=2,
                             color=BLUE, spaceAfter=8))

    # Case Info Table
    story.append(Paragraph("Case Information", h2_style))
    case_info = [
        ["Case ID",    case_data.get("case_id", "N/A")],
        ["Date",       case_data.get("submission_date", "N/A")],
        ["Patient ID", case_data["patient"].get("id", "N/A")],
        ["Age",        str(case_data["patient"].get("age", "N/A"))],
        ["Insurance",  case_data["patient"].get("insurance_plan", "N/A")],
        ["Diagnosis",  f"{case_data['diagnosis'].get('icd10_code')} — "
                       f"{case_data['diagnosis'].get('description')}"],
        ["Procedure",  f"{case_data['requested_procedure'].get('cpt_code')} — "
                       f"{case_data['requested_procedure'].get('description')}"],
    ]
    t = Table(case_info, colWidths=[45*mm, 120*mm])
    t.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTSIZE",  (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,0), (-1,-1),
         [colors.white, HexColor("#F8FAFC")]),
        ("GRID",      (0,0), (-1,-1), 0.3, HexColor("#E2E8F0")),
        ("LEFTPADDING",  (0,0), (-1,-1), 8),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("BOTTOMPADDING",(0,0), (-1,-1), 5),
    ]))
    story.append(t)

    # Final Decision
    story.append(Paragraph("Final Recommendation", h2_style))
    status     = decision.get("final_status", "UNKNOWN")
    status_color_map = {
        "APPROVED":             GREEN,
        "DENIED":               RED,
        "NEEDS_MORE_INFORMATION": AMBER,
        "ESCALATE_TO_HUMAN":    RED,
    }
    status_color = status_color_map.get(status, HexColor("#64748B"))

    status_table = Table([[
        Paragraph(f"STATUS: {status}",
                  ParagraphStyle("st", fontName="Helvetica-Bold",
                                 fontSize=14, textColor=colors.white))
    ]], colWidths=[165*mm])
    status_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), status_color),
        ("LEFTPADDING",   (0,0), (-1,-1), 12),
        ("TOPPADDING",    (0,0), (-1,-1), 10),
        ("BOTTOMPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(status_table)
    story.append(Spacer(1, 4*mm))

    story.append(Paragraph(
        decision.get("justification", "No justification provided."),
        body_style))

    # Missing Documents
    missing = decision.get("missing_documents", [])
    if missing:
        story.append(Paragraph("Missing Documents Required", h2_style))
        for doc in missing:
            story.append(Paragraph(f"• {doc}", body_style))

    # Policy Reason
    story.append(Paragraph("Policy Reason", h2_style))
    story.append(Paragraph(
        decision.get("policy_reason", "N/A"), body_style))

    # Next Steps
    next_steps = decision.get("next_steps", [])
    if next_steps:
        story.append(Paragraph("Next Steps", h2_style))
        for step in next_steps:
            story.append(Paragraph(f"• {step}", body_style))

    # Human Reviewer Note
    story.append(Paragraph("Human Reviewer Instructions", h2_style))
    note_table = Table([[
        Paragraph(
            decision.get("human_reviewer_note",
                         "Human review required before any action."),
            ParagraphStyle("hn", fontName="Helvetica-Bold",
                           fontSize=9.5, textColor=NAVY))
    ]], colWidths=[165*mm])
    note_table.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,-1), HexColor("#FEF3C7")),
        ("LEFTPADDING",   (0,0), (-1,-1), 10),
        ("TOPPADDING",    (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LINEBEFORE",    (0,0), (0,-1), 3, AMBER),
    ]))
    story.append(note_table)

    # Audit Trail
    story.append(Paragraph("Agent Audit Trail (Band Room)", h2_style))
    for msg in band_messages:
        story.append(Paragraph(
            f"<b>{msg.get('sender', 'Unknown')}</b> "
            f"[{msg.get('timestamp', '')}]",
            ParagraphStyle("at", fontName="Helvetica-Bold",
                           fontSize=9, textColor=BLUE,
                           spaceBefore=6, spaceAfter=2)))
        content = msg.get("content", "")
        if len(content) > 500:
            content = content[:500] + "..."
        story.append(Paragraph(content,
            ParagraphStyle("atb", fontName="Courier",
                           fontSize=7.5, textColor=NAVY,
                           leading=11, leftIndent=10,
                           backColor=LGRAY)))

    # Disclaimer
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=0.5,
                             color=HexColor("#E2E8F0")))
    story.append(Paragraph(
        "DISCLAIMER: This report is generated by MediChain AI for "
        "informational and administrative assistance purposes only. "
        "It does NOT constitute medical advice, a diagnosis, or a "
        "final insurance authorization decision. All recommendations "
        "require review and approval by licensed medical and insurance "
        "professionals. All data used is synthetic/fake.",
        small_style))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
        f"MediChain AI | Band of Agents Hackathon 2026",
        small_style))

    doc.build(story)
    return buffer.getvalue()