from __future__ import annotations
import json, shutil, uuid
from pathlib import Path
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from PIL import Image
from .render import OUTPUTS
from .medforge import inspect_image, make_lesson
from . import media_engine, blender_engine


def _safe_image(path: Path, max_w=500, max_h=350):
    try:
        im=Image.open(path);w,h=im.size;scale=min(max_w/w,max_h/h,1);return RLImage(str(path),width=w*scale,height=h*scale)
    except Exception:return None


def _analysis_text(result):
    if isinstance(result,dict):
        for key in ('text','analysis','description'):
            if result.get(key):return str(result[key])
        if isinstance(result.get('result'),dict):return _analysis_text(result['result'])
        return json.dumps(result,indent=2)
    return str(result)


def _make_pdf(title, original:Path, analysis, lesson, visual:Path|None, three_d:dict|None, out:Path):
    styles=getSampleStyleSheet();styles['Title'].textColor=colors.HexColor('#A91F34');styles['Heading1'].textColor=colors.HexColor('#A91F34')
    note=ParagraphStyle('note',parent=styles['BodyText'],backColor=colors.HexColor('#FFF0F1'),borderColor=colors.HexColor('#D8354D'),borderWidth=.6,borderPadding=8)
    story=[Paragraph(title,styles['Title']),Paragraph('MedForge visual teaching package',styles['Heading1']),Paragraph('Educational synthesis only. Generated illustrations and 3D geometry are demonstrative and are not diagnostic scans or validated patient-specific anatomy.',note),Spacer(1,10)]
    src=_safe_image(original)
    if src:story += [Paragraph('Source image',styles['Heading1']),src,Spacer(1,8)]
    story += [Paragraph('Image analysis',styles['Heading1']),Paragraph(_analysis_text(analysis).replace('\n','<br/>'),styles['BodyText']),PageBreak(),Paragraph('Mechanism / teaching structure',styles['Heading1'])]
    scenes=lesson.get('scenes') if isinstance(lesson,dict) else None
    if scenes:
        for i,s in enumerate(scenes,1):
            story.append(Paragraph(f'{i}. {s.get("title") or "Teaching step"}',styles['Heading2']))
            for b in s.get('bullets') or []:story.append(Paragraph('• '+str(b),styles['BodyText']))
            if s.get('narration'):story.append(Paragraph(str(s['narration']),styles['BodyText']))
            story.append(Spacer(1,6))
    else:story.append(Paragraph(json.dumps(lesson,indent=2).replace('\n','<br/>'),styles['BodyText']))
    if visual and visual.exists():
        story += [PageBreak(),Paragraph('Generated teaching visual',styles['Heading1'])]
        pic=_safe_image(visual)
        if pic:story.append(pic)
        story.append(Paragraph('Generated visual for teaching/explanation. Verify anatomy and source consistency before external use.',note))
    if three_d:
        story += [Paragraph('3D mechanism output',styles['Heading1']),Paragraph(str(three_d.get('boundary') or 'Educational 3D teaching geometry.'),note)]
        still=Path(three_d.get('image',''))
        if still.exists():
            pic=_safe_image(still)
            if pic:story.append(pic)
        story.append(Paragraph('Editable Blender scene: '+str(three_d.get('blend') or 'not generated'),styles['BodyText']))
        story.append(Paragraph('Teaching MP4: '+str(three_d.get('video') or 'not generated'),styles['BodyText']))
    SimpleDocTemplate(str(out),pagesize=(612,792),rightMargin=42,leftMargin=42,topMargin=42,bottomMargin=42,title=title).build(story)


def build(image_path:str,title='MedForge Teaching Package',question='Teach me what is visibly present and what should be verified next.',visual_mode='auto',seconds=7.0,progress=lambda x:None):
    source=Path(image_path)
    if not source.exists():raise RuntimeError('Source image is no longer available.')
    run_id=uuid.uuid4().hex[:10]
    progress('1/5 Inspecting the source image locally')
    analysis=inspect_image(source,question)
    analysis_text=_analysis_text(analysis)
    progress('2/5 Building the mechanism / teaching structure')
    lesson=make_lesson(title,analysis_text+'\n\nTeaching focus: '+question)
    visual=None;visual_engine=None;visual_note=None
    media=media_engine.status()
    # Prefer ComfyUI when it is genuinely ready. Otherwise use a Blender still so one-click does not dead-end.
    if visual_mode in ('auto','illustration','2.5d') and media.get('online'):
        try:
            if not media.get('image_configured'):
                cps=media_engine.checkpoints()
                if cps:media_engine.save_workflow('image',media_engine.image_workflow(cps[0]))
            if (media_engine.workflow_dir()/'image.json').exists():
                progress('3/5 Generating a teaching illustration in ComfyUI')
                r=media_engine.generate('image','Medical educational illustration. Clearly diagram rather than diagnostic imaging. Preserve only source-supported concepts. '+analysis_text[:5000]+'\nTeaching goal: '+question,progress)
                visual=Path(r['files'][0]);visual_engine=r.get('engine')
        except Exception as e:visual_note='ComfyUI illustration unavailable: '+str(e)
    three_d=None
    if blender_engine.find_blender():
        progress('4/5 Rendering a genuine Blender 3D teaching scene')
        three_d=blender_engine.render('medforge',question+'\nSource analysis: '+analysis_text[:6000],seconds,f'medforge-teaching-{run_id}',progress)
        if visual is None:
            visual=Path(three_d['image']);visual_engine='Blender still fallback';visual_note=(visual_note+'; ' if visual_note else '')+'Used the Blender teaching still because no validated image-generation workflow was available.'
    elif visual is None:
        visual_note=(visual_note+'; ' if visual_note else '')+'Blender is not installed, so no generated visual/3D scene was produced.'
    progress('5/5 Building the teaching PDF')
    pdf=OUTPUTS/f'medforge-teaching-package-{run_id}.pdf'
    _make_pdf(title,source,analysis,lesson,visual,three_d,pdf)
    return {
        'title':title,'analysis':analysis,'lesson':lesson,'visual':str(visual) if visual else None,'visual_engine':visual_engine,'visual_note':visual_note,
        'three_d':three_d,'pdf':str(pdf),'source_image':str(source),'boundary':'Educational synthesis only; generated visuals are not diagnostic scans or patient-specific geometry.'
    }
