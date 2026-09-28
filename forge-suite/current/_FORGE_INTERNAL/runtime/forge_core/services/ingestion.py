import json, re, shutil, subprocess, tempfile, zipfile
from pathlib import Path, PurePosixPath
from email import policy
from email.parser import BytesParser
from .vault import import_file, add_text
from .document_text import extract_text

MAX_BYTES=200*1024*1024

def extract(path):
    ext=path.suffix.lower()
    if ext=='.eml':
        msg=BytesParser(policy=policy.default).parsebytes(path.read_bytes());body=msg.get_body(preferencelist=('plain',)) if msg.is_multipart() else msg
        content=body.get_content() if body else ''
        return {'text':'\n'.join(f'{k}: {msg.get(k,"")}' for k in ('Date','From','To','Subject'))+'\n\n'+str(content),'method':'email','warning':None}
    if ext in ('.wav','.mp3','.m4a','.mp4','.mov','.webm','.ogg'):
        try:
            from .transcribe import transcribe
            r=transcribe(path);return {'text':r['text'],'method':r['engine'],'warning':'Automatically transcribed; verify names and timestamps against the original recording.'}
        except Exception as e:return {'text':'','method':'transcription-unavailable','warning':str(e)}
    result=extract_text(path)
    if result['text']:return result
    tesseract=shutil.which('tesseract')
    if tesseract and ext in ('.png','.jpg','.jpeg','.tif','.tiff','.webp'):
        try:
            proc=subprocess.run([tesseract,str(path),'stdout'],capture_output=True,text=True,timeout=180,check=True)
            return {'text':proc.stdout,'method':'tesseract-ocr','warning':'OCR text is derived and may contain errors; retain the source image.'}
        except Exception as e:result['warning']='OCR failed: '+str(e)
    elif ext=='.pdf' and tesseract and shutil.which('pdftoppm'):
        try:
            from pypdf import PdfReader
            pages=len(PdfReader(str(path)).pages)
            if pages>100:return {**result,'warning':'Scanned PDF exceeds automatic 100-page OCR limit; original preserved. Split it for OCR.'}
            with tempfile.TemporaryDirectory() as td:
                prefix=Path(td)/'page'
                subprocess.run(['pdftoppm','-scale-to','1800','-png',str(path),str(prefix)],check=True,capture_output=True,timeout=300)
                texts=[]
                for image in sorted(Path(td).glob('*.png')):
                    out=subprocess.run([tesseract,str(image),'stdout'],check=True,capture_output=True,text=True,timeout=90)
                    texts.append(out.stdout)
                return {'text':'\n\n'.join(texts),'method':'pdf-ocr','warning':'OCR text is derived; verify against the included original PDF pages.'}
        except Exception as e:result['warning']='Scanned PDF preserved; OCR failed: '+str(e)
    return result

def ingest(path,metadata=None,auto_index=True,expand_zip=True):
    meta=dict(metadata or {});rec=import_file(path,meta,'forge-batch')
    extracted=extract(path) if auto_index else {'text':'','method':'disabled','warning':None}
    text=extracted.get('text','')
    # Suggestions are explicitly separate from confirmed source metadata.
    categories={'Military / Service':r'\b(army|military|duty|national guard)\b','Medical':r'\b(patient|diagnosis|radiology|physician)\b','VA':r'\b(veterans affairs|rating decision)\b'}
    suggestions=[name for name,pattern in categories.items() if re.search(pattern,text[:12000],re.I)]
    idx=add_text(rec['id'],text[:500000],meta) if text else {'added':0}
    result=rec|{'text_extraction':{'method':extracted['method'],'characters':len(text),'warning':extracted.get('warning')},'indexing':idx,'suggested_categories':suggestions}
    if len(text)>500000:result['text_extraction']['warning']='Index limited to first 500,000 characters; full original retained.'
    results=[result]
    if path.suffix.lower()=='.zip' and expand_zip:
        with zipfile.ZipFile(path) as archive:
            members=[i for i in archive.infolist() if not i.is_dir()]
            if len(members)>100 or sum(i.file_size for i in members)>MAX_BYTES:raise ValueError('ZIP preserved but not expanded: maximum 100 members / 200 MB uncompressed.')
            with tempfile.TemporaryDirectory() as td:
                for n,info in enumerate(members):
                    name=PurePosixPath(info.filename.replace('\\','/'))
                    if name.is_absolute() or '..' in name.parts or info.file_size>50*1024*1024:
                        results.append({'name':info.filename,'error':'Unsafe archive path or file larger than 50 MB; skipped.'});continue
                    folder=Path(td)/str(n);folder.mkdir();target=folder/name.name
                    try:
                        with archive.open(info) as src,target.open('wb') as dest:
                            size=0
                            while chunk:=src.read(1024*1024):
                                size+=len(chunk)
                                if size>50*1024*1024:raise ValueError('Archive entry exceeds 50 MB')
                                dest.write(chunk)
                        results.extend(ingest(target,{**meta,'archive_source_id':rec['id'],'archive_member':info.filename},auto_index,False))
                    except Exception as e:results.append({'name':info.filename,'error':str(e)})
    return results
