from __future__ import annotations

from io import BytesIO
from textwrap import shorten

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate, Frame, Image, KeepTogether, PageBreak, PageTemplate,
    Paragraph, Spacer, Table, TableStyle,
)


def _styles(visual: bool):
    styles = getSampleStyleSheet()
    accent = colors.HexColor("#2563EB") if visual else colors.HexColor("#1F2937")
    soft = colors.HexColor("#EFF6FF") if visual else colors.HexColor("#F7F7F7")
    styles.add(ParagraphStyle(
        name="EA_Title", parent=styles["Title"], fontName="Helvetica-Bold",
        fontSize=22 if visual else 18, leading=26, textColor=accent,
        alignment=TA_CENTER, spaceAfter=10,
    ))
    styles.add(ParagraphStyle(
        name="EA_H1", parent=styles["Heading1"], fontName="Helvetica-Bold",
        fontSize=15, leading=18, textColor=accent, spaceBefore=10, spaceAfter=7,
    ))
    styles.add(ParagraphStyle(
        name="EA_H2", parent=styles["Heading2"], fontName="Helvetica-Bold",
        fontSize=11.5, leading=14, textColor=colors.HexColor("#111827"),
        spaceBefore=7, spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="EA_Body", parent=styles["BodyText"], fontSize=9.4, leading=13,
        textColor=colors.HexColor("#222222"), spaceAfter=6,
    ))
    styles.add(ParagraphStyle(
        name="EA_Small", parent=styles["BodyText"], fontSize=7.8, leading=10,
        textColor=colors.HexColor("#555555"),
    ))
    styles.add(ParagraphStyle(
        name="EA_Callout", parent=styles["BodyText"], fontSize=9, leading=12,
        leftIndent=10, rightIndent=10, borderWidth=0.6, borderColor=accent,
        borderPadding=8, backColor=soft, spaceAfter=8,
    ))
    return styles, accent, soft


def _locator(item: dict) -> str:
    name = item.get("source_name") or "Unknown source"
    page = item.get("page")
    return f"{name}, p. {page}" if page else name


def _header_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 7.5)
    canvas.setFillColor(colors.HexColor("#666666"))
    canvas.drawString(0.55 * inch, 0.35 * inch, "Evidence Auditor Pro · Human review required")
    canvas.drawRightString(7.95 * inch, 0.35 * inch, f"Page {doc.page}")
    canvas.restoreState()


def _mechanism_table(steps: list[str], styles, accent):
    cells = []
    for idx, step in enumerate(steps):
        cells.append(Paragraph(f"<b>{idx+1}</b><br/>{step}", styles["EA_Body"]))
    if not cells:
        cells = [Paragraph("No reviewer-supplied mechanism sequence provided.", styles["EA_Body"])]
    widths = [6.8 * inch / len(cells)] * len(cells)
    t = Table([cells], colWidths=widths)
    t.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOX", (0,0), (-1,-1), 0.7, accent),
        ("INNERGRID", (0,0), (-1,-1), 0.35, colors.HexColor("#C7D2FE")),
        ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#F8FAFC")),
        ("LEFTPADDING", (0,0), (-1,-1), 7),
        ("RIGHTPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING", (0,0), (-1,-1), 7),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
    ]))
    return t


def build_packet(
    result: dict,
    *,
    packet_style: str = "visual_claim",
    case_title: str = "Evidence Review",
    executive_summary: str = "",
    mechanism_steps: list[str] | None = None,
    rebuttal_note: str = "",
    screenshots: list[dict] | None = None,
) -> bytes:
    visual = packet_style == "visual_claim"
    styles, accent, soft = _styles(visual)
    mechanism_steps = mechanism_steps or []
    screenshots = screenshots or []

    buf = BytesIO()
    doc = BaseDocTemplate(
        buf, pagesize=letter, rightMargin=0.55*inch, leftMargin=0.55*inch,
        topMargin=0.55*inch, bottomMargin=0.55*inch,
        title=case_title,
    )
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="normal")
    doc.addPageTemplates([PageTemplate(id="main", frames=frame, onPage=_header_footer)])

    story = []
    story.append(Spacer(1, 0.35*inch))
    story.append(Paragraph(case_title, styles["EA_Title"]))
    story.append(Paragraph(
        "Source-backed evidence review packet generated from reviewer-selected materials. "
        "Automated classifications are screening aids and require human verification.",
        styles["EA_Callout"],
    ))
    story.append(Spacer(1, 0.18*inch))

    summary = result.get("summary", {})
    summary_data = [
        ["Favorable", summary.get("favorable", 0)],
        ["Unfavorable", summary.get("unfavorable", 0)],
        ["Mixed", summary.get("mixed", 0)],
        ["Neutral", summary.get("neutral", 0)],
        ["Source/page units", result.get("source_count", 0)],
        ["Tension candidates", len(result.get("potential_contradictions", []))],
    ]
    st = Table(summary_data, colWidths=[2.45*inch, 1.25*inch])
    st.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.6, accent),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.HexColor("#D1D5DB")),
        ("BACKGROUND", (0,0), (0,-1), soft),
        ("FONTNAME", (0,0), (0,-1), "Helvetica-Bold"),
        ("ALIGN", (1,0), (1,-1), "CENTER"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(st)

    if executive_summary:
        story.append(Spacer(1, 0.18*inch))
        story.append(Paragraph("Executive Summary", styles["EA_H1"]))
        story.append(Paragraph(executive_summary, styles["EA_Body"]))

    story.append(PageBreak())
    story.append(Paragraph("Issue Map", styles["EA_H1"]))
    issue_rows = [["Issue", "Evidence count"]]
    for issue, count in sorted(result.get("issue_summary", {}).items(), key=lambda x: (-x[1], x[0])):
        issue_rows.append([issue.replace("_", " ").title(), count])
    if len(issue_rows) == 1:
        issue_rows.append(["No issue categories detected", 0])
    issue_table = Table(issue_rows, colWidths=[5.5*inch, 1.2*inch], repeatRows=1)
    issue_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), accent),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#9CA3AF")),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.HexColor("#D1D5DB")),
        ("FONTSIZE", (0,0), (-1,-1), 8.5),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(issue_table)

    story.append(Paragraph("Source-Backed Evidence", styles["EA_H1"]))
    selected = [i for i in result.get("items", []) if i.get("stance") in {"favorable", "mixed", "unfavorable"}]
    if not selected:
        story.append(Paragraph("No classified evidence passages were available.", styles["EA_Body"]))
    for item in selected[:80]:
        label = f"{item.get('evidence_id','')} · {item.get('stance','').upper()} · {_locator(item)}"
        story.append(KeepTogether([
            Paragraph(label, styles["EA_H2"]),
            Paragraph(item.get("text",""), styles["EA_Callout"] if visual else styles["EA_Body"]),
            Paragraph("Issues: " + ", ".join(i.replace("_"," ").title() for i in item.get("issues", [])), styles["EA_Small"]),
            Spacer(1, 4),
        ]))

    story.append(PageBreak())
    story.append(Paragraph("Rebuttal / Tension Desk", styles["EA_H1"]))
    if rebuttal_note:
        story.append(Paragraph("<b>Reviewer note:</b> " + rebuttal_note, styles["EA_Callout"]))
    tensions = result.get("potential_contradictions", [])
    if not tensions:
        story.append(Paragraph("No same-issue cross-stance tension was detected.", styles["EA_Body"]))
    for idx, tension in enumerate(tensions[:20], 1):
        fav = tension.get("favorable", {})
        unf = tension.get("unfavorable", {})
        story.append(Paragraph(
            f"Tension {idx}: " + ", ".join(i.replace("_"," ").title() for i in tension.get("issues", [])),
            styles["EA_H2"],
        ))
        rows = [
            [Paragraph("<b>Supporting / favorable</b>", styles["EA_Small"]), Paragraph("<b>Adverse / opposing</b>", styles["EA_Small"])],
            [Paragraph(fav.get("text",""), styles["EA_Body"]), Paragraph(unf.get("text",""), styles["EA_Body"])],
            [Paragraph(_locator(fav), styles["EA_Small"]), Paragraph(_locator(unf), styles["EA_Small"])],
        ]
        t = Table(rows, colWidths=[3.32*inch, 3.32*inch])
        t.setStyle(TableStyle([
            ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#9CA3AF")),
            ("INNERGRID", (0,0), (-1,-1), 0.25, colors.HexColor("#D1D5DB")),
            ("BACKGROUND", (0,0), (0,0), colors.HexColor("#ECFDF5")),
            ("BACKGROUND", (1,0), (1,0), colors.HexColor("#FEF2F2")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("TOPPADDING", (0,0), (-1,-1), 5),
            ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ]))
        story.append(t)
        story.append(Spacer(1, 7))

    story.append(Paragraph("Mechanism / Sequence Map", styles["EA_H1"]))
    story.append(Paragraph(
        "Reviewer-authored explanatory sequence. This section does not independently establish medical causation.",
        styles["EA_Small"],
    ))
    story.append(Spacer(1, 5))
    story.append(_mechanism_table(mechanism_steps, styles, accent))

    if screenshots:
        story.append(PageBreak())
        story.append(Paragraph("Visual Exhibits", styles["EA_H1"]))
        story.append(Paragraph(
            "Reviewer-supplied screenshots and diagrams. Verify each image against its original source before external use.",
            styles["EA_Small"],
        ))
        for idx, shot in enumerate(screenshots, 1):
            try:
                img_buf = BytesIO(shot["bytes"])
                image = Image(img_buf)
                image._restrictSize(6.7*inch, 7.6*inch)
                caption = shot.get("caption") or shot.get("name") or f"Exhibit {idx}"
                story.append(Paragraph(f"Exhibit V-{idx}: {caption}", styles["EA_H2"]))
                story.append(image)
                story.append(Spacer(1, 8))
            except Exception:
                story.append(Paragraph(f"Exhibit V-{idx}: image could not be rendered.", styles["EA_Small"]))

    story.append(PageBreak())
    story.append(Paragraph("Source Appendix", styles["EA_H1"]))
    seen = set()
    rows = [["Source", "Page", "Evidence IDs"]]
    grouped = {}
    for item in result.get("items", []):
        key = (item.get("source_name") or "Unknown source", item.get("page"))
        grouped.setdefault(key, []).append(item.get("evidence_id",""))
    for (name, page), ids in grouped.items():
        rows.append([shorten(name, width=72, placeholder="…"), page or "—", ", ".join(ids[:12])])
    if len(rows) == 1:
        rows.append(["No sources", "—", "—"])
    table = Table(rows, colWidths=[4.6*inch, 0.7*inch, 1.45*inch], repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), accent),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 7.5),
        ("BOX", (0,0), (-1,-1), 0.5, colors.HexColor("#9CA3AF")),
        ("INNERGRID", (0,0), (-1,-1), 0.25, colors.HexColor("#D1D5DB")),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("TOPPADDING", (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(table)

    doc.build(story)
    return buf.getvalue()
