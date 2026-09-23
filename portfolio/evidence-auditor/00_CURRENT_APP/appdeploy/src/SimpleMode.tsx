import { useEffect, useRef, useState } from 'react';
import { getDocument } from 'pdfjs-dist';
import { Bot, CheckCircle2, CircleAlert, Cloud, Download, FileText, FolderOpen, LoaderCircle, LogOut, Paperclip, ShieldCheck, Sparkles, Trash2, WandSparkles, X } from 'lucide-react';

type BenefitsProgram = 'VA / VBA' | 'Social Security (SSDI / SSI)' | 'New Hampshire' | 'Medical & Functional Evidence';
type Doc = { id: string; name: string; contentType: string; charCount: number; pageCount: number; sourceMode?: 'pdf' | 'text' | 'ocr' | 'email' | 'web' | 'search' | 'media'; sourceUrl?: string; createdAt: string; excerpt: string };
type UploadItem = { id: string; name: string; size: number; kind: 'pdf' | 'image' | 'file'; stage: 'Queued' | 'Uploading' | 'Reading' | 'Indexing' | 'OCR' | 'Ready' | 'Error'; progress: number; detail: string; error?: string };

type Props = {
    userLabel: string;
    documents: Doc[];
    uploadItems: UploadItem[];
    busy: string;
    notice: string;
    benefitsProgram: BenefitsProgram;
    lawIssue: string;
    issueOptions: string[];
    submissionReady: boolean;
    submissionPreviewBlob: Blob | null;
    submissionPreviewUrl: string;
    submissionPreviewName: string;
    uploadSuccessNotice: string;
    vaultFileCount: number;
    driveNote: string;
    onUpload: (files: FileList | null) => void;
    onDismissUpload: (id: string) => void;
    onDismissUploadSuccess: () => void;
    onDeleteDocument: (id: string) => void;
    onSetProgram: (program: BenefitsProgram) => void;
    onSetIssue: (issue: string) => void;
    onGenerate: () => void;
    onDownload: () => void;
    onSaveVault: () => void;
    onOpenPro: () => void;
    onSignOut: () => void;
};

const programOptions: BenefitsProgram[] = ['VA / VBA', 'Social Security (SSDI / SSI)', 'New Hampshire', 'Medical & Functional Evidence'];

function sizeLabel(bytes: number) {
    return bytes >= 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;
}

function PdfCanvasPreview({ blob, onValidation }: { blob: Blob; onValidation?: (result: { renderedPages: number; totalPages: number; complete: boolean; error?: string }) => void }) {
    const [pages, setPages] = useState<string[]>([]);
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let cancelled = false;
        let loadingTask: ReturnType<typeof getDocument> | null = null;

        const render = async () => {
            setPages([]);
            setError('');
            setLoading(true);
            try {
                const bytes = new Uint8Array(await blob.arrayBuffer());
                loadingTask = getDocument({ data: bytes, isEvalSupported: false });
                const pdf = await loadingTask.promise;
                if (!pdf.numPages) throw new Error('The generated PDF contains no pages.');
                onValidation?.({ renderedPages: 0, totalPages: pdf.numPages, complete: false });
                const rendered: string[] = [];

                for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
                    if (cancelled) return;
                    const page = await pdf.getPage(pageNumber);
                    const viewport = page.getViewport({ scale: 1.3 });
                    const canvas = document.createElement('canvas');
                    canvas.width = Math.ceil(viewport.width);
                    canvas.height = Math.ceil(viewport.height);
                    const context = canvas.getContext('2d', { alpha: false });
                    if (!context) throw new Error('This browser cannot render the PDF preview canvas.');
                    await page.render({ canvasContext: context, viewport }).promise;
                    rendered.push(canvas.toDataURL('image/png'));
                    page.cleanup();
                    if (!cancelled) { setPages([...rendered]); onValidation?.({ renderedPages: rendered.length, totalPages: pdf.numPages, complete: false }); }
                }

                await pdf.cleanup();
                if (!cancelled) { setLoading(false); onValidation?.({ renderedPages: rendered.length, totalPages: pdf.numPages, complete: rendered.length === pdf.numPages }); }
            } catch (err) {
                if (!cancelled) {
                    const message = err instanceof Error ? err.message : 'The PDF preview could not be rendered.';
                    setError(message);
                    setLoading(false);
                    onValidation?.({ renderedPages: 0, totalPages: 0, complete: false, error: message });
                }
            }
        };

        void render();
        return () => {
            cancelled = true;
            if (loadingTask) void loadingTask.destroy().catch(() => undefined);
        };
    }, [blob, onValidation]);

    if (error) return <div className='simple-pdf-render-error'><CircleAlert size={24} /><strong>Preview could not render</strong><span>{error}</span><small>The generated PDF can still be downloaded with the Download PDF button above.</small></div>;
    if (!pages.length && loading) return <div className='simple-pdf-render-loading'><LoaderCircle className='spin' size={24} /><strong>Rendering PDF preview…</strong><span>Preparing the exact generated pages for review.</span></div>;

    return <div className='simple-pdf-pages' aria-label='Generated submission PDF preview'>
        {pages.map((page, index) => <figure className='simple-pdf-page' key={`pdf-page-${index + 1}`}><figcaption>Page {index + 1}{loading && index === pages.length - 1 ? ' · rendering remaining pages…' : ''}</figcaption><img src={page} alt={`Generated submission PDF page ${index + 1}`} /></figure>)}
    </div>;
}

export default function SimpleMode(props: Props) {
    const fileInput = useRef<HTMLInputElement>(null);
    const previewRef = useRef<HTMLElement>(null);
    const [dragging, setDragging] = useState(false);
    const [pdfValidation, setPdfValidation] = useState<{ renderedPages: number; totalPages: number; complete: boolean; error?: string }>({ renderedPages: 0, totalPages: 0, complete: false });
    const indexedPages = props.documents.reduce((sum, document) => sum + (document.pageCount || 1), 0);
    const uploadPending = props.uploadItems.some((item) => !['Ready', 'Error'].includes(item.stage));
    const canGenerate = props.documents.length > 0 && !uploadPending && !props.busy;
    const generateHint = !props.documents.length ? 'Upload at least one evidence file to unlock submission generation.' : uploadPending ? 'Wait for all uploads to finish indexing before generating the submission.' : 'Generate the filing from the evidence currently indexed in this case.';

    useEffect(() => {
        setPdfValidation({ renderedPages: 0, totalPages: 0, complete: false });
        if (!props.submissionReady || !props.submissionPreviewBlob) return;
        const frame = window.requestAnimationFrame(() => previewRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' }));
        return () => window.cancelAnimationFrame(frame);
    }, [props.submissionReady, props.submissionPreviewBlob]);

    const chooseFiles = (files: FileList | null) => {
        if (!files?.length) return;
        props.onUpload(files);
        if (fileInput.current) fileInput.current.value = '';
    };

    return <div className='simple-shell'>
        <header className='simple-topbar'>
            <div className='simple-brand'><div className='simple-brand-mark'><Bot size={20} /></div><div><strong>Elias</strong><span>+ Evidence Auditor</span></div></div>
            <div className='simple-top-actions'>
                <button className='simple-account' onClick={props.onSignOut}><LogOut size={15} /> {props.userLabel}</button>
                <div className='elias-mode-switch simple-mode-anchor'><button className='active'>Simple</button><button onClick={props.onOpenPro}>Pro</button></div>
            </div>
        </header>

        {props.uploadSuccessNotice && <div className='upload-success-toast' role='status' aria-live='polite'><CheckCircle2 size={21} /><div><strong>Upload complete</strong><span>{props.uploadSuccessNotice}</span></div><button aria-label='Dismiss upload complete message' onClick={props.onDismissUploadSuccess}><X size={16} /></button></div>}
        {props.busy && <div className='simple-working-overlay' role='status' aria-live='polite'><div className='simple-working-card'><div className='simple-working-icon'><Sparkles size={24} /></div><div><span>ELIAS IS WORKING</span><strong>{props.busy}</strong><p>Your evidence stays loaded while Elias prepares the filing draft.</p><div className='simple-working-track'><i /></div></div></div></div>}

        <main className='simple-main'>
            <section className='simple-hero'>
                <span className='simple-kicker'>SIMPLE MODE</span>
                <h1>Upload once. Audit, verify, and build from the same evidence.</h1>
                <p>Elias stores and indexes the case, Evidence Auditor checks source support and provenance, and the filing builder creates a source-cited PDF from that same Evidence Cloud.</p>
                <div className='simple-progress'><div className={props.documents.length ? 'done' : 'active'}><b>1</b><span><strong>Upload evidence</strong><small>Medical + administrative records</small></span></div><div className={props.documents.length && !props.submissionReady ? 'active' : props.submissionReady ? 'done' : ''}><b>2</b><span><strong>Build filing</strong><small>Evidence + law + medical support</small></span></div><div className={props.submissionReady ? 'active' : ''}><b>3</b><span><strong>Preview & download</strong><small>Review the exact PDF</small></span></div></div>
            </section>

            {props.notice && <div className='simple-notice'>{props.notice}</div>}

            <section className='simple-grid'>
                <article className='simple-card evidence-card'>
                    <div className='simple-card-head'><div><span>STEP 1</span><h2>Add your evidence</h2></div><div className='simple-count'>{props.documents.length}<small>sources</small></div></div>
                    <input ref={fileInput} className='hidden' multiple type='file' accept='.pdf,.txt,.md,.eml,.mbox,.png,.jpg,.jpeg,.webp,application/pdf,text/plain,text/markdown,message/rfc822,application/mbox,image/png,image/jpeg,image/webp' onChange={(event) => chooseFiles(event.target.files)} />
                    <button className={dragging ? 'simple-dropzone dragging' : 'simple-dropzone'} onClick={() => fileInput.current?.click()} onDragEnter={(event) => { event.preventDefault(); setDragging(true); }} onDragOver={(event) => event.preventDefault()} onDragLeave={() => setDragging(false)} onDrop={(event) => { event.preventDefault(); setDragging(false); chooseFiles(event.dataTransfer.files); }}>
                        <Paperclip size={24} />
                        <strong>Drop evidence here or choose files</strong>
                        <span>PDF, TXT, MD, email files, JPG, PNG, WebP</span>
                    </button>
                    <div className='simple-source-summary'><span><strong>{indexedPages}</strong> indexed pages</span><span><strong>{props.vaultFileCount}</strong> Evidence Cloud files</span><span><ShieldCheck size={13} /> Private workspace</span></div>
                    {props.uploadItems.length > 0 && <div className='simple-upload-list' aria-live='polite'>{props.uploadItems.map((item) => <div className={`simple-upload-row ${item.stage.toLowerCase()}`} key={item.id}><FileText size={16} /><div><strong>{item.name}</strong><span>{sizeLabel(item.size)} · {item.error || item.detail}</span>{item.stage !== 'Ready' && item.stage !== 'Error' && <div className='simple-upload-progress'><i style={{ width: `${item.progress}%` }} /></div>}</div><b>{item.stage === 'Ready' ? 'Ready' : item.stage === 'Error' ? 'Error' : `${item.progress}%`}</b>{(item.stage === 'Ready' || item.stage === 'Error') && <button aria-label={`Hide ${item.name}`} onClick={(event) => { event.stopPropagation(); props.onDismissUpload(item.id); }}><X size={13} /></button>}</div>)}</div>}
                    {props.documents.length > 0 && <div className='simple-loaded-sources'>{props.documents.slice(0, 8).map((document) => <div key={document.id}><FileText size={14} /><span><strong>{document.name}</strong><small>{document.pageCount} page{document.pageCount === 1 ? '' : 's'}</small></span><button aria-label={`Delete ${document.name}`} onClick={() => props.onDeleteDocument(document.id)}><Trash2 size={13} /></button></div>)}{props.documents.length > 8 && <small className='more-sources'>+ {props.documents.length - 8} more indexed source{props.documents.length - 8 === 1 ? '' : 's'}</small>}</div>}
                </article>

                <article className='simple-card filing-card'>
                    <div className='simple-card-head'><div><span>STEP 2</span><h2>Tell Elias what you are filing</h2></div><WandSparkles size={22} /></div>
                    <label>Program / agency<select value={props.benefitsProgram} onChange={(event) => props.onSetProgram(event.target.value as BenefitsProgram)}>{programOptions.map((program) => <option key={program}>{program}</option>)}</select></label>
                    <label>Issue<select value={props.lawIssue} onChange={(event) => props.onSetIssue(event.target.value)}>{props.issueOptions.map((issue) => <option key={issue}>{issue}</option>)}</select></label>
                    <div className='simple-explainer'><CheckCircle2 size={17} /><p>Elias uses favorable supportable record evidence, current official authorities, source citations, and relevant verified medical literature when available. The filing draft omits a standalone weaknesses section but will not invent or distort evidence.</p></div>
                    <button className='simple-generate' disabled={!canGenerate} onClick={props.onGenerate} title={generateHint}><Sparkles size={18} /> {props.submissionReady ? 'Regenerate Submission-Ready PDF' : 'Generate Submission-Ready PDF'}</button>
                    <small className={canGenerate ? 'simple-help ready' : 'simple-help'}>{canGenerate ? 'Evidence is indexed and ready for submission generation.' : uploadPending ? 'Finish uploading and indexing all evidence before generating.' : 'Upload at least one record first.'}</small>
                </article>
            </section>

            <section className='simple-preview-section' ref={previewRef}>
                <div className='simple-preview-head'><div><span className='simple-kicker'>STEP 3 · PDF PREVIEW</span><h2>Review exactly what you will download</h2><p>PDF.js renders the same generated PDF bytes used by the download button, so the preview does not depend on the browser PDF plug-in.</p></div>{props.submissionReady && <div className='simple-preview-actions'><button onClick={props.onDownload}><Download size={15} /> Download PDF</button><button onClick={props.onSaveVault}><Cloud size={15} /> Save to Evidence Cloud</button>{props.submissionPreviewUrl && <a href={props.submissionPreviewUrl} target='_blank' rel='noreferrer'><FolderOpen size={15} /> Open PDF in browser</a>}</div>}</div>
                {props.submissionReady && props.submissionPreviewBlob ? <div className='simple-pdf-frame'><div className='simple-pdf-meta'><FileText size={15} /><span>{props.submissionPreviewName || 'Submission_Advocacy_Brief.pdf'} · {sizeLabel(props.submissionPreviewBlob.size)}</span><b>{props.submissionPreviewBlob.size < 5 * 1024 * 1024 ? 'UNDER 5 MB' : 'OVER 5 MB'}</b></div><div className='simple-explainer'><CheckCircle2 size={17} /><p><strong>Submission-file validation:</strong> exact generated file size is {sizeLabel(props.submissionPreviewBlob.size)}. {props.submissionPreviewBlob.size < 5 * 1024 * 1024 ? 'The current PDF meets the 5 MB size target.' : 'The current PDF exceeds 5 MB and needs reduction before a 5 MB-limited submission.'} Visual render check: {pdfValidation.complete ? `all ${pdfValidation.totalPages} page${pdfValidation.totalPages === 1 ? '' : 's'} rendered successfully` : pdfValidation.error ? 'preview render failed' : `${pdfValidation.renderedPages}/${pdfValidation.totalPages || '?'} pages rendered`}.</p></div><PdfCanvasPreview blob={props.submissionPreviewBlob} onValidation={setPdfValidation} /></div> : <div className='simple-preview-empty'><div><FileText size={34} /><h3>Your PDF preview will appear here</h3><p>Upload evidence and click Generate Submission-Ready PDF. You can inspect every page before downloading or saving it to the private Evidence Cloud.</p></div></div>}
                <small className='simple-drive-note'>{props.driveNote}</small>
            </section>
        </main>
    </div>;
}
