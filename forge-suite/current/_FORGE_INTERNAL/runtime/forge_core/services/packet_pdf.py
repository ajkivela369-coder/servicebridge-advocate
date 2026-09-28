"""Polished deterministic evidence packets with source-control front matter and intact exhibits.

The packet may organize and quote retained sources and saved user-created source-linked statements.
It does not invent medical nexus, duty status, diagnoses, or legal conclusions.
"""
from pathlib import Path
from io import BytesIO
from html import escape
import json
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from pypdf import PdfReader, PdfWriter
from .ingestion import extract as extract_text

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
font_regular=next((p for p in ('C:/Windows/Fonts/arial.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf') if Path(p).exists()),None)
font_bold=next((p for p in ('C:/Windows/Fonts/arialbd.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf') if Path(p).exists()),None)
if font_regular and font_bold:
    pdfmetrics.registerFont(TTFont('ForgeText',font_regular));pdfmetrics.registerFont(TTFont('ForgeBold',font_bold))

NAVY=colors.HexColor('#0B2338'); BLUE=colors.HexColor('#17658B'); CYAN=colors.HexColor('#2DB4C8')
INK=colors.HexColor('#17232D'); MUTED=colors.HexColor('#5F7280'); PALE=colors.HexColor('#EDF5F8')
AMBER=colors.HexColor('#D99A26'); GREEN=colors.HexColor('#16865C'); RED=colors.HexColor('#B14343')
STYLES=getSampleStyleSheet()
base_font='ForgeText' if font_regular and font_bold else 'Helvetica'
bold_font='ForgeBold' if font_regular and font_bold else 'Helvetica-Bold'
for name in ('Normal','BodyText'): STYLES[name].fontName=base_font
for name in ('Title','Heading1','Heading2'): STYLES[name].fontName=bold_font
STYLES['Normal'].fontSize=9.4; STYLES['Normal'].leading=13.2; STYLES['Normal'].textColor=INK
STYLES['Title'].fontSize=23; STYLES['Title'].leading=27; STYLES['Title'].textColor=NAVY
STYLES['Heading1'].fontSize=15; STYLES['Heading1'].leading=19; STYLES['Heading1'].textColor=BLUE; STYLES['Heading1'].spaceBefore=8; STYLES['Heading1'].spaceAfter=7
STYLES['Heading2'].fontSize=11; STYLES['Heading2'].leading=14; STYLES['Heading2'].textColor=NAVY
SMALL=ParagraphStyle('ForgeSmall',parent=STYLES['Normal'],fontSize=8.1,leading=10.5,textColor=MUTED)
CALLOUT=ParagraphStyle('ForgeCallout',parent=STYLES['Normal'],backColor=PALE,borderColor=CYAN,borderWidth=0.7,borderPadding=9,spaceBefore=6,spaceAfter=8)
CENTER=ParagraphStyle('ForgeCenter',parent=STYLES['Normal'],alignment=TA_CENTER,textColor=MUTED)


def para(text,style='Normal'):
    s=STYLES.get(style,style) if isinstance(style,str) else style
    return Paragraph(escape(str(text or '')).replace('\n','<br/>'),s)


def _meta(item):
    try:return json.loads(item.get('metadata') or '{}')
    except Exception:return {}


def _category(item):
    m=_meta(item); text=' '.join(str(x or '') for x in (m.get('category'),m.get('record_type'),m.get('type'),item.get('name'))).lower()
    if any(x in text for x in ('military','service','order','dfas','ngb','duty','drill','idt','adt','at ')):return 'Duty / service evidence'
    if any(x in text for x in ('email','correspond','message','letter','command')):return 'Contemporaneous correspondence'
    if any(x in text for x in ('emg','mri','ct','medical','clinical','operative','surgery','imaging','provider','hospital','va ')):return 'Medical / objective evidence'
    if any(x in text for x in ('lay','witness','caregiver','statement','testimony')):return 'Lay / witness evidence'
    if any(x in text for x in ('3d','mechanism','diagram','illustration','visual')):return 'Demonstrative / explanatory material'
    return 'Other retained source'


def _role_text(kind):
    k=(kind or 'GENERAL').upper()
    if k=='VBA':
        return ('This packet organizes the selected record for VA disability review. Duty/service records establish status and dates; contemporaneous correspondence establishes notice and reported events; medical records establish documented findings and treatment; lay evidence establishes firsthand observations and functional consequences. Medical nexus and diagnosis remain questions for qualified clinicians/examiners.')
    if k=='SSDI':
        return ('This packet organizes the selected longitudinal record for disability review, with emphasis on medically documented impairments and what functioning can be sustained safely, reliably, repeatedly, and predictably across a normal work schedule. One good examination or isolated task is not treated as proof of sustained capacity.')
    if k=='APTD':
        return ('This packet organizes the selected longitudinal record for disability review, separating objective findings, treatment history, firsthand functional evidence, episodic variability, recovery time, attendance, endurance, cognition, and unresolved conflicts.')
    if k=='ADA':
        return ('This packet organizes functional evidence relevant to accommodation review. It separates documented limitations and firsthand functional effects from diagnoses or causal conclusions that require professional evaluation.')
    if k=='CLINICIAN':
        return ('This packet is a source-controlled clinical briefing. It separates source-recorded diagnoses/findings, patient-reported symptoms, firsthand observations, and open mechanism questions so a clinician can independently assess the record.')
    return ('This packet organizes the selected record while preserving source control. Original records govern whenever any summary differs from the source.')


def _questions(kind):
    k=(kind or 'GENERAL').upper()
    if k=='VBA': return [
        'Are all verified duty/service periods and contemporaneous reports reflected in the review?',
        'For each verified duty period, does the record support a new injury, reinjury, or material aggravation, and what evidence supports that conclusion?',
        'How do objective findings, procedures, and the before/after chronology affect the medical analysis?',
        'If an opinion is negative, does its reasoning address the full longitudinal record rather than an abbreviated service history?',
        'Which claimed secondary or downstream manifestations require separate specialist evaluation?'
    ]
    if k=='SSDI': return [
        'What limitations can be sustained across an 8-hour day and 5-day week, not only during a brief examination?',
        'How do episodic attacks, recovery time, attendance, cognition, communication, endurance, and variability affect reliable work?',
        'Do isolated normal findings conflict with the longitudinal record, and if so how should that conflict be resolved?',
        'Which limitations are supported by objective findings, longitudinal treatment, and consistent firsthand observations?'
    ]
    if k=='APTD': return [
        'What can the claimant sustain safely, reliably, repeatedly, and predictably?',
        'How do episodic symptoms, recovery time, attendance and cognitive effects change functional capacity?',
        'Which objective findings and longitudinal observations support or conflict with the functional assessment?'
    ]
    if k=='ADA': return [
        'Which functional limitations materially affect access to work, education, communication, attendance, concentration or physical tasks?',
        'Which accommodations would address those limitations without relying on assumptions from a single good day?',
        'What documentation is sufficient to support the requested accommodation while minimizing unnecessary disclosure?'
    ]
    if k=='CLINICIAN': return [
        'Which findings are directly documented versus patient-reported or inferred?',
        'What mechanisms are medically plausible, and what additional testing or specialist review would help distinguish them?',
        'How do symptoms and functional limitations vary over time and with activity or position?'
    ]
    return ['What does each source directly establish?', 'What conflicts or gaps require resolution?', 'What should the reviewer verify before relying on any synthesis?']


def _footer(c,doc):
    c.saveState(); c.setFillColor(NAVY); c.rect(0,0,612,30,fill=1,stroke=0)
    c.setFillColor(colors.white); c.setFont(base_font,7.5); c.drawString(42,11,'Evidence Auditor | source-controlled packet | original source exhibits control')
    c.drawRightString(570,11,f'Page {doc.page}'); c.restoreState()


def document(path,story):
    SimpleDocTemplate(str(path),pagesize=(612,792),rightMargin=40,leftMargin=40,topMargin=42,bottomMargin=44).build(story,onFirstPage=_footer,onLaterPages=_footer)


def _table(rows,widths=None,header=True):
    prepared=[]
    for row in rows:
        prepared.append([x if hasattr(x,'wrap') else para(x,SMALL) for x in row])
    t=Table(prepared,colWidths=widths,repeatRows=1 if header else 0,hAlign='LEFT')
    cmds=[('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#BFCED6')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5)]
    if header:
        cmds += [('BACKGROUND',(0,0),(-1,0),NAVY),('TEXTCOLOR',(0,0),(-1,0),colors.white),('FONTNAME',(0,0),(-1,0),bold_font)]
    for r in range(1 if header else 0,len(rows)):
        if r%2==0:cmds.append(('BACKGROUND',(0,r),(-1,r),colors.HexColor('#F7FAFC')))
    t.setStyle(TableStyle(cmds));return t


def make_packet_pdf(items,claims,case_name,kind,out_path):
    if not items:raise ValueError('Select or upload at least one evidence source.')
    kind=(kind or 'GENERAL').upper(); out_path=Path(out_path); derived=out_path.parent/(out_path.stem+'-sources');derived.mkdir(exist_ok=True)
    sources=[];warnings=[]
    for i,item in enumerate(items,1):
        p=Path(item['stored_path']);dest=derived/f'source-{i:03d}.pdf';label=f'S{i:03d}';warning=None;count=0;excerpt=''
        try:
            if p.suffix.lower()=='.pdf':
                reader=PdfReader(str(p))
                if reader.is_encrypted and not reader.decrypt(''):raise ValueError('password-protected PDF')
                if not reader.pages:raise ValueError('empty PDF')
                w=PdfWriter();w.append(reader,import_outline=False);w.write(str(dest));count=len(reader.pages)
                excerpt='\n'.join((pg.extract_text() or '')[:1200] for pg in list(reader.pages)[:2])[:2200]
                if not excerpt.strip():warning='No embedded text extracted; original scanned pages are included for visual review.'
            elif item.get('mime','').startswith('image/'):
                from PIL import Image
                image=Image.open(p);c=canvas.Canvas(str(dest),pagesize=(612,792))
                for frame in range(getattr(image,'n_frames',1)):
                    image.seek(frame);pic=image.convert('RGB');iw,ih=pic.size;scale=min(524/iw,704/ih)
                    c.drawImage(ImageReader(pic),(612-iw*scale)/2,(792-ih*scale)/2,iw*scale,ih*scale);c.showPage()
                c.save();count=len(PdfReader(str(dest)).pages);warning='Image included as a source exhibit; OCR may be separate from the visual exhibit.'
            else:
                extraction=extract_text(p);text=extraction.get('text','')
                if not text:raise ValueError(extraction.get('warning') or 'No PDF conversion for this format')
                blocks=[text[j:j+2500] for j in range(0,len(text),2500)]
                document(dest,[para(item['name'],'Heading1'),para('Text rendering derived from the preserved original.',CALLOUT)]+[para(b) for b in blocks])
                count=len(PdfReader(str(dest)).pages);excerpt=text[:2200]
        except Exception as e:warning='Not included as PDF pages: '+str(e)
        if warning:warnings.append(label+' '+item['name']+': '+warning)
        sources.append({'label':label,'item':item,'pdf':dest,'pages':count,'warning':warning,'excerpt':excerpt,'category':_category(item)})

    labels={s['item']['id']:s['label'] for s in sources}
    valid_claims=[]
    for c in claims:
        try:ids=json.loads(c.get('source_ids') or '[]')
        except Exception:ids=[]
        if ids and set(ids).issubset(labels): valid_claims.append(c)

    # Cover / core record map.
    story=[para(case_name,'Title'),para(kind+' evidence / defense packet','Heading1'),Spacer(1,4),para(_role_text(kind),CALLOUT),
           para('Three source-control rules','Heading1')]
    rules=[
        ('1. SOURCE RECORDS CONTROL','Every summary, timeline entry, question, and saved statement must be checked against the retained source exhibit.'),
        ('2. KEEP EVIDENCE IN ITS LANE','Duty documents, medical records, correspondence, lay observations, and demonstrative material answer different questions and should not be converted into one another.'),
        ('3. FUNCTION IS LONGITUDINAL','When functional capacity is relevant, assess what can be sustained safely, reliably, repeatedly, and predictably - including episodic symptoms, recovery time, cognition, communication, attendance and endurance.')]
    story.append(_table([[para(a,'Heading2'),b] for a,b in rules],[170,350],header=False));story += [Spacer(1,8),para('Record map','Heading1')]
    groups={}
    for s in sources:groups.setdefault(s['category'],[]).append(s)
    rows=[['Evidence lane','Selected sources','What this lane can directly establish']]
    direct={
        'Duty / service evidence':'Status, dates, assignment/training context; not medical causation by itself.',
        'Contemporaneous correspondence':'Notice, timing, reported events/symptoms, command or agency communication; not independent diagnosis by itself.',
        'Medical / objective evidence':'Documented findings, treatment, procedures, clinician observations and recorded symptom reports; duty status requires separate proof.',
        'Lay / witness evidence':'Firsthand sequence and observed functional consequences; medical etiology requires qualified opinion.',
        'Demonstrative / explanatory material':'Illustrates an anatomical or mechanical question; does not independently prove diagnosis or causation.',
        'Other retained source':'Retained source material; its probative role depends on the document itself.'}
    for lane,ss in groups.items():rows.append([lane,str(len(ss)),direct[lane]])
    story.append(_table(rows,[155,65,300]));story += [PageBreak(),para('Selected source inventory','Heading1')]
    inv=[['ID','Source','Date','Category / provider','Pages']]
    for s in sources:
        it=s['item'];m=_meta(it);inv.append([s['label'],it['name'],m.get('date') or m.get('source_date') or 'not entered',f"{m.get('category') or s['category']}\n{m.get('provider') or ''}",str(s['pages'])])
    story.append(_table(inv,[42,205,76,150,42]));story += [Spacer(1,10),para(f'{len(items)} selected source(s); {sum(s["pages"] for s in sources)} exhibit page(s). SHA-256 identifiers and source IDs are retained in the packet manifest.',SMALL)]

    # Chronology from source dates + explicitly saved dated statements.
    story += [PageBreak(),para('Verified / source-linked chronology','Heading1'),para('Dates below come from entered source metadata or saved source-linked statements. Upload dates are not silently substituted for event dates.',CALLOUT)]
    chronology=[]
    for s in sources:
        m=_meta(s['item']);d=m.get('date') or m.get('source_date')
        if d:chronology.append((str(d),s['label'],s['item']['name'],'source'))
    for c in valid_claims:
        try:m=json.loads(c.get('metadata') or '{}')
        except Exception:m={}
        d=m.get('date') or m.get('service_date')
        if d:
            ids=json.loads(c.get('source_ids') or '[]');chronology.append((str(d),', '.join(labels[x] for x in ids if x in labels),c.get('statement') or '','saved statement'))
    if chronology:
        story.append(_table([['Date','Source(s)','Record / statement','Type']]+[[a,b,c,d] for a,b,c,d in sorted(chronology,key=lambda x:x[0])],[72,78,315,55]))
    else:story.append(para('No event/source dates were entered. No chronology has been inferred.',CALLOUT))

    # Source-linked issue synthesis; never manufacture claims.
    story += [PageBreak(),para('Source-linked issue map','Heading1'),para('This section contains only saved source-linked statements. If no statements were saved, the source exhibits remain authoritative and this section stays intentionally sparse.',CALLOUT)]
    if valid_claims:
        by_issue={}
        for c in valid_claims:
            try:m=json.loads(c.get('metadata') or '{}')
            except Exception:m={}
            by_issue.setdefault(m.get('issue') or 'Uncategorized issue',[]).append(c)
        for issue,rows_claim in by_issue.items():
            story.append(para(issue,'Heading2'))
            for c in rows_claim:
                ids=json.loads(c.get('source_ids') or '[]');story += [para(c.get('statement') or ''),para('Sources: '+', '.join(labels[x] for x in ids if x in labels),SMALL),Spacer(1,5)]
    else:story.append(para('No saved source-linked statements are present. Use Evidence Auditor Copilot or Claims to add a statement only after selecting the supporting source(s).'))

    story += [PageBreak(),para('Questions for reviewer / examiner','Heading1'),para('These are organizational questions, not answers. The reviewer should resolve them from the source record and applicable standards.',CALLOUT)]
    for n,q in enumerate(_questions(kind),1):story.append(para(f'{n}. {q}'))
    story += [Spacer(1,8),para('Source-control instruction','Heading1'),para('Use affirmative evidence without overclaiming. A duty record can establish duty/status without proving nexus. A contemporaneous email can establish notice/reporting without becoming a diagnosis. Objective tests and operative records establish documented findings/treatment; qualified clinicians address causation. Demonstrative visuals illustrate a question and never replace the original medical or military record.',CALLOUT)]

    story += [PageBreak(),para('Orientation excerpts','Heading1'),para('Short verbatim source excerpts are included only for navigation. Always review the complete exhibit and surrounding context.',CALLOUT)]
    for s in sources:
        if s['excerpt'].strip():story += [KeepTogether([para(s['label']+' | '+s['item']['name'],'Heading2'),para(s['excerpt']),Spacer(1,8)])]
    story += [para('Extraction / inclusion notes','Heading1')]
    story += [para(w,SMALL) for w in warnings] or [para('All selected sources were converted or retained as PDF exhibit pages.',SMALL)]

    cover=derived/'front-matter.pdf';document(cover,story)
    # Calculate exhibit page ranges iteratively because index pagination changes offsets.
    index_path=derived/'exhibit-index.pdf';cover_pages=len(PdfReader(str(cover)).pages);index_pages=1
    for _ in range(5):
        start=cover_pages+index_pages+1;entries=[para('Clickable-style exhibit index','Heading1'),para('Packet page ranges point to the complete PDF. PDF bookmarks also jump directly to each exhibit.',CALLOUT)]
        idxrows=[['Exhibit','Source','Packet pages','Source pages']]
        for source in sources:
            if source['pages']:
                idxrows.append([source['label'],source['item']['name'],f'{start}-{start+source["pages"]-1}',f'1-{source["pages"]}']);start+=source['pages']
        entries.append(_table(idxrows,[50,292,90,88]));document(index_path,entries);actual=len(PdfReader(str(index_path)).pages)
        if actual==index_pages:break
        index_pages=actual

    w=PdfWriter();w.append(str(cover),import_outline=False);w.append(str(index_path),import_outline=False)
    w.add_outline_item('Defense packet front matter',0);w.add_outline_item('Exhibit index',cover_pages)
    exhibit_index=[]
    for s in sources:
        if not s['pages']:continue
        start=len(w.pages);w.append(str(s['pdf']),import_outline=False);w.add_outline_item(s['label']+' | '+s['item']['name'],start)
        exhibit_index.append({'source_id':s['item']['id'],'label':s['label'],'packet_start_page':start+1,'pages':s['pages']})
    w.add_metadata({'/Title':case_name,'/Author':'Evidence Auditor','/Subject':kind+' source-controlled evidence/defense packet'})
    w.write(str(out_path))

    limit=4_800_000;parts=[]
    if out_path.stat().st_size>limit:
        reader=PdfReader(str(out_path));part=PdfWriter();first=1
        def save_part(writer,start,end):
            name=out_path.with_name(out_path.stem+f'-part-{len(parts)+1:03d}.pdf');writer.write(str(name));parts.append({'file':str(name),'start_page':start,'end_page':end,'bytes':name.stat().st_size,'under_5_mb':name.stat().st_size<5_000_000})
        for n,page in enumerate(reader.pages,1):
            candidate=PdfWriter()
            for old in part.pages:candidate.add_page(old)
            candidate.add_page(page);buf=BytesIO();candidate.write(buf)
            if buf.tell()>limit and len(part.pages):save_part(part,first,n-1);part=PdfWriter();part.add_page(page);first=n
            else:part=candidate
        if len(part.pages):save_part(part,first,len(reader.pages))
        if any(not p['under_5_mb'] for p in parts):warnings.append('At least one source page alone exceeds 5 MB. It was preserved; that part needs manual size reduction before submission.')
    return {'pdf':str(out_path),'pdf_bytes':out_path.stat().st_size,'pdf_pages':len(w.pages),'front_matter_pages':cover_pages+index_pages,'under_5_mb':out_path.stat().st_size<5_000_000,'parts':parts,'warnings':warnings,'exhibit_index':exhibit_index,'packet_style':'source-controlled-defense'}
