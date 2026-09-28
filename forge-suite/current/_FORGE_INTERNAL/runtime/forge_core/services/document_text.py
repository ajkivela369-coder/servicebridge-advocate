from __future__ import annotations
from pathlib import Path
import json, re, zipfile
from html import unescape

_TEXT_EXTS={'.txt','.md','.csv','.json','.yaml','.yml','.xml','.html','.htm','.log','.rtf'}

def _decode(data:bytes)->str:
    for enc in ('utf-8','utf-8-sig','cp1252','latin-1'):
        try:return data.decode(enc)
        except Exception:pass
    return data.decode('utf-8',errors='replace')

def _clean_xmlish(text:str)->str:
    text=re.sub(r'<w:tab[^>]*/>','\t',text)
    text=re.sub(r'</w:p>','\n\n',text)
    text=re.sub(r'<[^>]+>','',text)
    return unescape(text).replace('\xa0',' ').strip()

def extract_text(path:Path)->dict:
    path=Path(path); ext=path.suffix.lower(); result={'text':'','method':'none','warning':None}
    try:
        if ext in _TEXT_EXTS:
            result.update(text=_decode(path.read_bytes()),method='plain-text')
        elif ext=='.docx':
            with zipfile.ZipFile(path) as z:
                raw=z.read('word/document.xml').decode('utf-8',errors='replace')
            result.update(text=_clean_xmlish(raw),method='docx-xml')
        elif ext=='.pdf':
            try:
                from pypdf import PdfReader
                reader=PdfReader(str(path)); pages=[]
                for i,p in enumerate(reader.pages):
                    try:pages.append((p.extract_text() or '').strip())
                    except Exception:pages.append('')
                text='\n\n'.join(x for x in pages if x).strip()
                result.update(text=text,method='pypdf')
                if not text:result['warning']='PDF preserved, but no embedded text was extractable (it may be scanned/image-only).'
            except Exception as e:
                result['warning']=f'PDF preserved; text extraction unavailable: {e}'
        else:
            result['warning']='Original preserved. This file type does not have automatic text extraction in this build.'
    except Exception as e:
        result['warning']=f'Original preserved; automatic text extraction failed: {e}'
    # Avoid pathological single chunks while preserving content.
    result['text']=result.get('text','').replace('\x00','').strip()
    return result
