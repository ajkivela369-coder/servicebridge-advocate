import { jsPDF } from 'jspdf';
import autoTable from 'jspdf-autotable';

export type SubmissionAuthority = { label: string; url: string; kind: string; title?: string };
export type SubmissionLiterature = { id: string; title: string; journal: string; pubDate: string; authors: string; url: string; citation: string; relevance: string; sourceType?: string };
export type SubmissionEvidence = { evidence: string; establishes: string; whyItMatters: string; source: string };
export type SubmissionArgument = { heading: string; proposition: string; recordSupport: string; medicalReasoning: string; legalReasoning: string; sourceCitations: string[]; authorityCitations: string[] };
export type SubmissionSource = { sourceId?: string; name: string; locator: string; use: string };
export type SubmissionPreflight = { status: 'Draft' | 'Needs Review' | 'Ready to Submit'; blockers: string[]; warnings: string[] };
export type SubmissionCitationAudit = { total: number; pinpoint: number; broad: number; invalid: string[]; unresolved: string[] };
export type SubmissionReconciliation = { issue: string; favorableEvidence: string; limitingContext: string; sourceCitations: string[] };
export type SubmissionVisual = { data: string; mimeType: string; title: string; label: string; kind?: string; sources?: Array<{ name: string; locator: string }> };
export type SubmissionBrief = { title: string; subtitle: string; requestedAction: string; executiveArgument: string; evidenceConvergence: SubmissionEvidence[]; arguments: SubmissionArgument[]; functionalCase: string[]; chronology?: Array<{ date: string; event: string; source: string; significance: string }>; objectiveFindings?: string[]; focusedQuestions?: string[]; recordReconciliations?: SubmissionReconciliation[]; medicalLiterature: SubmissionLiterature[]; requestedDisposition: string; legalAuthorities: SubmissionAuthority[]; sourceAppendix: SubmissionSource[]; visuals?: SubmissionVisual[]; preflight?: SubmissionPreflight; citationAudit?: SubmissionCitationAudit; verificationNote: string; demo?: boolean };

type PdfWithTable = jsPDF & { lastAutoTable?: { finalY: number } };
const clean = (value: string) => String(value ?? '').replace(/\*\*/g, '').replace(/\s+/g, ' ').trim();
const safeFile = (value: string) => clean(value || 'Evidence_Case').replace(/[^a-zA-Z0-9._-]+/g, '_').slice(0, 70) || 'Evidence_Case';

export function buildSubmissionPdf(brief: SubmissionBrief, caseLabel = 'Evidence Case') {
    const doc = new jsPDF({ unit: 'pt', format: 'letter', orientation: 'portrait', compress: true });
    const pageWidth = doc.internal.pageSize.getWidth();
    const pageHeight = doc.internal.pageSize.getHeight();
    const left = 48;
    const right = 48;
    const contentWidth = pageWidth - left - right;
    const navy: [number, number, number] = [18, 55, 78];
    const teal: [number, number, number] = [25, 111, 124];
    const pale: [number, number, number] = [245, 248, 250];
    let y = 0;

    const newPageIfNeeded = (needed: number) => {
        if (y + needed > pageHeight - 62) {
            doc.addPage();
            y = 58;
        }
    };
    const paragraph = (text: string, size = 10, gap = 8, weight: 'normal' | 'bold' = 'normal') => {
        const lines = doc.splitTextToSize(clean(text), contentWidth);
        newPageIfNeeded(lines.length * (size + 3) + gap);
        doc.setFont('helvetica', weight);
        doc.setFontSize(size);
        doc.setTextColor(35, 48, 61);
        doc.text(lines, left, y);
        y += lines.length * (size + 3) + gap;
    };
    const section = (title: string) => {
        newPageIfNeeded(36);
        doc.setFillColor(...navy);
        doc.rect(left, y, contentWidth, 24, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(10);
        doc.text(title.toUpperCase(), left + 9, y + 16);
        y += 36;
    };
    const callout = (label: string, text: string) => {
        const lines = doc.splitTextToSize(clean(text), contentWidth - 22);
        const height = Math.max(48, lines.length * 12 + 28);
        newPageIfNeeded(height + 10);
        doc.setDrawColor(...teal);
        doc.setFillColor(...pale);
        doc.roundedRect(left, y, contentWidth, height, 3, 3, 'FD');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(8);
        doc.setTextColor(...teal);
        doc.text(label.toUpperCase(), left + 10, y + 14);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
        doc.setTextColor(35, 48, 61);
        doc.text(lines, left + 10, y + 29);
        y += height + 10;
    };

    doc.setFillColor(...navy);
    doc.rect(0, 0, pageWidth, 154, 'F');
    doc.setTextColor(128, 221, 226);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10);
    doc.text('ADVOCACY SUBMISSION BRIEF', left, 42);
    doc.setTextColor(255, 255, 255);
    doc.setFont('times', 'bold');
    doc.setFontSize(24);
    const titleLines = doc.splitTextToSize(clean(brief.title || caseLabel), contentWidth - 20);
    doc.text(titleLines, left, 72);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.setTextColor(207, 220, 230);
    doc.text(clean(brief.subtitle), left, 125);
    y = 182;

    callout('What Matters Now / Requested Action', brief.requestedAction);
    if (brief.preflight) {
        callout(`Submission preflight  |  ${brief.preflight.status}`, [...brief.preflight.blockers.map((item) => `BLOCKER: ${item}`), ...brief.preflight.warnings.map((item) => `WARNING: ${item}`)].join(' ') || 'No blocking preflight findings.');
    }
    if (brief.citationAudit) {
        const audit = brief.citationAudit;
        const problems = [...(audit.invalid || []), ...(audit.unresolved || [])];
        callout('Citation integrity', `${audit.pinpoint} of ${audit.total} claimant-record citation${audit.total === 1 ? '' : 's'} verified with pinpoint pages${audit.broad ? `; ${audit.broad} broad citation${audit.broad === 1 ? '' : 's'} still need page locators` : ''}${problems.length ? `; ${problems.length} unresolved/invalid citation${problems.length === 1 ? '' : 's'} require correction` : ''}.`);
    }
    section('Executive Argument');
    paragraph(brief.executiveArgument, 10.5, 10);

    section('Evidence Convergence');
    autoTable(doc, {
        startY: y,
        margin: { left, right },
        head: [['Evidence', 'What it establishes', 'Why it matters', 'Source']],
        body: (brief.evidenceConvergence || []).map((row) => [clean(row.evidence), clean(row.establishes), clean(row.whyItMatters), clean(row.source)]),
        tableWidth: contentWidth,
        styles: { font: 'helvetica', fontSize: 7.4, cellPadding: 5, overflow: 'linebreak', valign: 'top', minCellWidth: 0 },
        headStyles: { fillColor: navy, textColor: 255, fontStyle: 'bold' },
        alternateRowStyles: { fillColor: pale },
        columnStyles: { 0: { cellWidth: 92 }, 1: { cellWidth: 154 }, 2: { cellWidth: 154 }, 3: { cellWidth: 116 } },
    });
    y = ((doc as PdfWithTable).lastAutoTable?.finalY ?? y) + 22;

    if ((brief.chronology || []).length) {
        section('Chronology');
        (brief.chronology || []).forEach((item) => { const source = clean(item.source); const cited = source.startsWith('[') ? source : `[${source}]`; paragraph(`${item.date} - ${item.event} ${cited} ${item.significance}`, 9, 5); });
    }
    if ((brief.objectiveFindings || []).length) {
        section('Objective Findings');
        (brief.objectiveFindings || []).forEach((item, index) => paragraph(`${index + 1}. ${item}`, 9.5, 5));
    }
    section('Record-Grounded Medical & Legal Arguments');
    (brief.arguments || []).forEach((argument, index) => {
        newPageIfNeeded(90);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(11);
        doc.setTextColor(...teal);
        doc.text(`${index + 1}. ${clean(argument.heading)}`, left, y);
        y += 17;
        paragraph(argument.proposition, 10, 5, 'bold');
        callout('Primary record support', `${argument.recordSupport} ${(argument.sourceCitations || []).join('  |  ')}`);
        if (clean(argument.medicalReasoning)) callout('Medical reasoning', argument.medicalReasoning);
        if (clean(argument.legalReasoning)) callout('Legal / regulatory reasoning', `${argument.legalReasoning} ${(argument.authorityCitations || []).join('  |  ')}`);
        y += 4;
    });

    if ((brief.recordReconciliations || []).length) {
        section('Record Reconciliation Notes');
        paragraph('These notes are limited to conflicts or limiting context that materially affect the favorable arguments above. This is not a general weakness inventory.', 8.5, 9, 'bold');
        (brief.recordReconciliations || []).forEach((item, index) => {
            newPageIfNeeded(72);
            paragraph(`${index + 1}. ${item.issue}`, 9.5, 4, 'bold');
            callout('Favorable evidence', `${item.favorableEvidence} ${(item.sourceCitations || []).join(' | ')}`);
            paragraph(`Context needed for accuracy: ${item.limitingContext}`, 8.8, 7);
        });
    }

    if ((brief.functionalCase || []).length) {
        section('Functional Case');
        (brief.functionalCase || []).forEach((item, index) => paragraph(`${index + 1}. ${item}`, 9.5, 5));
    }

    if ((brief.legalAuthorities || []).length) {
        section('Legal & Program Authorities');
        (brief.legalAuthorities || []).forEach((authority, index) => {
            newPageIfNeeded(34);
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(9);
            doc.setTextColor(35, 48, 61);
            doc.text(`${index + 1}. ${clean(authority.label)}`, left, y);
            y += 12;
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(7.5);
            doc.setTextColor(...teal);
            doc.textWithLink(clean(authority.url), left + 10, y, { url: authority.url });
            y += 16;
        });
    }

    if ((brief.medicalLiterature || []).length) {
        section('Peer-Reviewed Medical Literature');
        paragraph('These sources provide general medical context only. They do not substitute for claimant-specific medical evidence or an expert opinion.', 8.5, 10, 'bold');
        (brief.medicalLiterature || []).forEach((source, index) => {
            newPageIfNeeded(60);
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(8.7);
            doc.setTextColor(35, 48, 61);
            const citationLines = doc.splitTextToSize(`${index + 1}. ${clean(source.citation || source.title)}`, contentWidth);
            doc.text(citationLines, left, y);
            y += citationLines.length * 11 + 3;
            paragraph(`Relevance: ${source.relevance}`, 8.4, 3);
            doc.setFontSize(7.5);
            doc.setTextColor(...teal);
            doc.textWithLink(source.url, left, y, { url: source.url });
            y += 16;
        });
    }

    if ((brief.visuals || []).length) {
        section('Derived Visual Evidence');
        paragraph('The following pages are derived review aids created from identified source records. They are not original medical imaging and do not replace the cited primary evidence.', 8.5, 10, 'bold');
        (brief.visuals || []).slice(0, 6).forEach((visual, index) => {
            doc.addPage();
            y = 50;
            doc.setFillColor(...navy);
            doc.rect(0, 0, pageWidth, 88, 'F');
            doc.setTextColor(128, 221, 226);
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(8);
            doc.text('DERIVED VISUAL  |  ORIGINAL RECORD CONTROLS', left, 28);
            doc.setTextColor(255, 255, 255);
            doc.setFont('times', 'bold');
            doc.setFontSize(18);
            const visualTitle = clean(visual.title || `Visual ${index + 1}`);
            doc.text(doc.splitTextToSize(visualTitle, contentWidth), left, 53);
            y = 112;
            try {
                const dataUrl = `data:${visual.mimeType || 'image/png'};base64,${visual.data}`;
                const props = doc.getImageProperties(dataUrl);
                const maxHeight = 450;
                const scale = Math.min(contentWidth / props.width, maxHeight / props.height, 1);
                const width = props.width * scale;
                const height = props.height * scale;
                const x = left + (contentWidth - width) / 2;
                doc.setDrawColor(203, 213, 225);
                doc.rect(x - 1, y - 1, width + 2, height + 2);
                doc.addImage(dataUrl, visual.mimeType.includes('jpeg') ? 'JPEG' : visual.mimeType.includes('webp') ? 'WEBP' : 'PNG', x, y, width, height, undefined, 'FAST');
                y += height + 18;
            } catch {
                callout('Visual unavailable', 'The selected derived visual could not be embedded in this PDF. Review the source/provenance record before filing.');
            }
            callout('Derived visual status', visual.label || 'Derived explanatory visual. Original record controls.');
            if ((visual.sources || []).length) paragraph(`Supporting sources: ${(visual.sources || []).map((source) => `${source.name} - ${source.locator}`).join('  |  ')}`, 8.2, 6);
        });
    }

    if ((brief.focusedQuestions || []).length) {
        section('Focused Questions / Next Development');
        (brief.focusedQuestions || []).forEach((item, index) => paragraph(`${index + 1}. ${item}`, 9.5, 5));
    }
    section('Cited Source Library / Appendix');
    autoTable(doc, {
        startY: y,
        margin: { left, right },
        head: [['ID', 'Source file', 'Locator', 'Use']],
        body: (brief.sourceAppendix || []).map((source, index) => [clean(source.sourceId || String(index + 1).padStart(2, '0')), clean(source.name), clean(source.locator), clean(source.use)]),
        tableWidth: contentWidth,
        styles: { font: 'helvetica', fontSize: 7.4, cellPadding: 5, overflow: 'linebreak', valign: 'top', minCellWidth: 0 },
        headStyles: { fillColor: navy, textColor: 255, fontStyle: 'bold' },
        alternateRowStyles: { fillColor: pale },
        columnStyles: { 0: { cellWidth: 30 }, 1: { cellWidth: 220 }, 2: { cellWidth: 110 }, 3: { cellWidth: 156 } },
    });
    y = ((doc as PdfWithTable).lastAutoTable?.finalY ?? y) + 22;

    section('Requested Disposition');
    paragraph(brief.requestedDisposition || brief.requestedAction, 10.5, 10, 'bold');
    paragraph(brief.verificationNote, 8, 4);

    const pages = doc.getNumberOfPages();
    for (let page = 1; page <= pages; page += 1) {
        doc.setPage(page);
        doc.setDrawColor(203, 213, 225);
        doc.line(left, pageHeight - 34, pageWidth - right, pageHeight - 34);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7.5);
        doc.setTextColor(100, 116, 139);
        doc.text(`${safeFile(caseLabel)} | Advocacy Submission Brief`, left, pageHeight - 20);
        doc.text(`${page} / ${pages}`, pageWidth - right, pageHeight - 20, { align: 'right' });
    }

    const filename = `${safeFile(caseLabel)}_Advocacy_Submission_Brief.pdf`;
    return { blob: doc.output('blob'), filename };
}
