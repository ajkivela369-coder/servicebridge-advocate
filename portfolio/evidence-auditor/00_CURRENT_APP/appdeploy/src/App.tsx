import { useEffect, useMemo, useRef, useState } from 'react';
import { api, auth, image } from '@appdeploy/client';
import { GlobalWorkerOptions, getDocument } from 'pdfjs-dist';
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import { Archive, Bot, Brain, CircleAlert, CircleCheck, Cloud, Download, ExternalLink, FileImage, FileSearch, FileText, FolderOpen, Gauge, Globe2, Headphones, ImagePlus, LoaderCircle, LogIn, LogOut, Mail, MemoryStick, MessageSquarePlus, Mic2, Paperclip, PanelLeft, Play, PlugZap, Printer, Scale, Search, Send, ShieldCheck, Sparkles, Square, Trash2, Video, WandSparkles, X } from 'lucide-react';
import { buildSubmissionPdf, type SubmissionBrief } from './submissionPdf';
import SimpleMode from './SimpleMode';
import './simpleMode.css';

GlobalWorkerOptions.workerSrc = pdfWorker;

type User = { userId: string; email?: string; name?: string };
type Memory = { enabled: boolean; caseLabel: string; goal: string; notes: string };
type Doc = { id: string; name: string; contentType: string; charCount: number; pageCount: number; sourceMode?: 'pdf' | 'text' | 'ocr' | 'email' | 'web' | 'search' | 'media'; sourceUrl?: string; createdAt: string; excerpt: string };
type IntegrationStatus = { webSearch: boolean; neuralVoice: boolean; gmailDirect: boolean; gmailNote: string; cloudVault: boolean; googleDriveDirect: boolean; driveNote: string };
type VaultStatus = { root: string; fileCount: number; folders: Array<{ name: string; count: number }>; googleDriveDirect: boolean; driveNote: string };
type EvidenceInventoryItem = { id: string; name: string; category: EvidenceCategory; documentType: string; locator: string; candidateDates: string[]; fingerprint: string; versionGroup: string; storageStatus: 'Stored original' | 'Derived reference' | 'Indexed only'; classificationBasis: 'heuristic' };
type EvidenceDuplicateGroup = { fingerprint: string; documentIds: string[]; names: string[]; note: string };
type EvidenceVersionGroup = { versionGroup: string; documentIds: string[]; names: string[]; note: string };
type EvidenceInventory = { items: EvidenceInventoryItem[]; duplicateGroups: EvidenceDuplicateGroup[]; versionGroups: EvidenceVersionGroup[]; generatedAt: string; warning: string };
type NeuralVoice = { voiceId: string; name: string; labels?: Record<string, string> };
type LiveSearchResult = { answer: string; results: Array<{ title: string; url: string; content: string; publishedDate?: string }>; savedDocument?: Doc | null };
type Chat = { id?: string; threadId: string; question: string; answer: string; tool: string; speed?: WorkMode; sources: string[]; createdAt: string };
type EvidenceFinding = { title: string; finding: string; source: string; whyItMatters: string; kind: string };
type EvidenceGap = { priority: string; gap: string; whyItMatters: string; nextStep: string };
type EvidenceTension = { adverse: string; supporting: string; source: string; reconcile: string };
type TimelineItem = { date: string; event: string; source: string; significance: string };
type ReviewIssue = { issue: string; status: string; note: string };
type Review = { summary: string; recordSignal: string; strongestEvidence: EvidenceFinding[]; gaps: EvidenceGap[]; tensions: EvidenceTension[]; issues: ReviewIssue[]; timeline: TimelineItem[] };
type Packet = { title: string; subtitle: string; executiveSummary: string; chronology: TimelineItem[]; strongestEvidence: EvidenceFinding[]; functionalImpact: string[]; adverseEvidence: EvidenceTension[]; missingEvidencePlan: EvidenceGap[]; reviewerChecklist: string[]; sourceAppendix: string[] };
type LawLens = { program?: string; jurisdiction?: string; issue: string; summary: string; framework?: string[]; whatRaterLooksFor: string[]; evidenceMatches: string[]; gaps: string[]; conflicts: string[]; nextBestEvidence: string[]; officialSources: Array<{ label: string; url: string; kind: string; title: string }> };
type WebResult = { title: string; url: string; answer: string; savedDocument?: Doc | null };
type View = 'chat' | 'cloud' | 'review' | 'packet';
type CopilotRole = 'Elias' | 'Evidence Auditor' | 'NeuroEval' | 'HealthQA' | 'Packet Builder' | 'Citation Auditor' | 'Document Copilot';
type EvidenceCategory = 'Medical Records' | 'Imaging / Tests' | 'Military / Service' | 'VA / Benefits' | 'Disability / SSA / State' | 'Functional Capacity' | 'Correspondence' | 'Legal / Administrative' | 'Other';
type AppMode = 'simple' | 'pro';
type WorkMode = 'Quick' | 'Standard' | 'Deep';
type UploadItem = { id: string; name: string; size: number; kind: 'pdf' | 'image' | 'file'; stage: 'Queued' | 'Uploading' | 'Reading' | 'Indexing' | 'OCR' | 'Ready' | 'Error'; progress: number; detail: string; error?: string };
type BenefitsProgram = 'VA / VBA' | 'Social Security (SSDI / SSI)' | 'New Hampshire' | 'Medical & Functional Evidence';
type PluginName = 'Record Search' | 'Gap Finder' | 'Quote Check' | 'Packet Assurance' | 'Timeline Builder' | 'Rebuttal Lab' | 'Web Research' | 'Web Search' | 'YouTube & Video' | 'Vision & Media' | 'Benefits Law & Medical Lens' | 'OCR Intake' | 'Email Evidence';

const pluginCatalog: Array<{ name: PluginName; blurb: string; chatTool: boolean }> = [
    { name: 'Record Search', blurb: 'Find source-backed evidence fast.', chatTool: true },
    { name: 'Gap Finder', blurb: 'Spot missing records and weak links.', chatTool: true },
    { name: 'Quote Check', blurb: 'Separate exact quotes from paraphrase.', chatTool: true },
    { name: 'Packet Assurance', blurb: 'Check provenance and reviewer-readiness.', chatTool: true },
    { name: 'Timeline Builder', blurb: 'Build and audit chronology.', chatTool: true },
    { name: 'Rebuttal Lab', blurb: 'Reconcile adverse and supporting evidence.', chatTool: true },
    { name: 'Web Research', blurb: 'Read and analyze a supplied public URL.', chatTool: true },
    { name: 'Web Search', blurb: 'Search the live web when the search connector is configured.', chatTool: true },
    { name: 'YouTube & Video', blurb: 'Read YouTube page/transcript text when exposed; uploaded videos use sampled visual frames.', chatTool: true },
    { name: 'Vision & Media', blurb: 'Understand attached images, audio, and representative video frames.', chatTool: false },
    { name: 'Benefits Law & Medical Lens', blurb: 'Compare official VA/VBA, SSA, New Hampshire, and medical-function frameworks with the loaded record.', chatTool: false },
    { name: 'OCR Intake', blurb: 'Read screenshots and scanned document images.', chatTool: false },
    { name: 'Email Evidence', blurb: 'Import .eml or .mbox evidence. Direct mailbox OAuth is not connected yet.', chatTool: false },
];
const emptyMemory: Memory = { enabled: true, caseLabel: '', goal: '', notes: '' };
const defaultPlugins = Object.fromEntries(pluginCatalog.map((plugin) => [plugin.name, true])) as Record<PluginName, boolean>;
const copilotPhases = ['Reading the loaded record…', 'Checking source support…', 'Reconciling chronology and conflicts…', 'Writing the clearest grounded answer…'];
const quickEliasActions: Array<{ label: string; prompt: string; tool: PluginName }> = [
    { label: 'Strongest Evidence', prompt: 'Identify the strongest evidence in the loaded record. Rank it by probative value, explain exactly what each source establishes, and separate record proof from inference.', tool: 'Record Search' },
    { label: 'Missing Evidence', prompt: 'Audit the loaded record for the highest-value missing evidence or records. Prioritize gaps that materially affect chronology, service connection, severity, functional impact, or reliability.', tool: 'Gap Finder' },
    { label: 'Contradiction Check', prompt: 'Find the most important tensions or contradictions in the record. Pair each adverse statement with supporting evidence that should be reconciled and explain the safest record-grounded response.', tool: 'Rebuttal Lab' },
    { label: 'Build Timeline', prompt: 'Build a concise chronological timeline from the loaded evidence with dates, source identities, material events, and any chronology gaps that still need verification.', tool: 'Timeline Builder' },
    { label: 'C&P Rebuttal', prompt: 'Audit the record for examiner findings or adverse conclusions that conflict with objective evidence, longitudinal records, duty history, or documented functional limits. Draft a source-grounded rebuttal outline without overstating causation.', tool: 'Rebuttal Lab' },
    { label: 'Packet QA', prompt: 'Run a reviewer-readiness preflight on the loaded record. Check provenance, quote integrity, missing links, adverse evidence, chronology, functional-impact support, and what should be fixed before a final packet.', tool: 'Packet Assurance' },
];

const copilotSpecialists: Array<{ name: CopilotRole; blurb: string; defaultTool: PluginName }> = [
    { name: 'Elias', blurb: 'Master orchestrator across the full case.', defaultTool: 'Record Search' },
    { name: 'Evidence Auditor', blurb: 'Support, contradictions, gaps, provenance, chronology, and reviewer-readiness.', defaultTool: 'Packet Assurance' },
    { name: 'NeuroEval', blurb: 'Neurologic and functional evidence review without inventing diagnosis or causation.', defaultTool: 'Rebuttal Lab' },
    { name: 'HealthQA', blurb: 'Patient-friendly explanation of supplied health records with clear evidence boundaries.', defaultTool: 'Record Search' },
    { name: 'Packet Builder', blurb: 'Builds structured drafts from verified evidence.', defaultTool: 'Packet Assurance' },
    { name: 'Citation Auditor', blurb: 'Checks whether important statements actually trace to the record.', defaultTool: 'Quote Check' },
    { name: 'Document Copilot', blurb: 'Organizes and formats evidence-backed pages and sections.', defaultTool: 'Timeline Builder' },
];

const copilotOperations: Array<{ label: string; prompt: string; tool: PluginName; view?: View }> = [
    { label: 'Find', prompt: 'Find the most relevant source-backed evidence for the issue I am currently working on and give me precise source identities and locators.', tool: 'Record Search', view: 'cloud' },
    { label: 'Compare', prompt: 'Compare the most relevant records. Show agreements, conflicts, date differences, and what evidence would reconcile them.', tool: 'Rebuttal Lab', view: 'review' },
    { label: 'Explain', prompt: 'Explain the relevant evidence in clear patient-friendly language while keeping source fact, reported history, opinion, agency finding, and inference separate.', tool: 'Record Search' },
    { label: 'Organize', prompt: 'Organize the loaded evidence by evidence type, chronology, issue, and likely submission use. Flag uncertain classifications rather than guessing.', tool: 'Gap Finder', view: 'cloud' },
    { label: 'Link', prompt: 'Create an evidence trace for the key propositions: source -> page or locator -> extracted evidence -> evidence type -> interpretation -> generated statement.', tool: 'Quote Check', view: 'review' },
    { label: 'Draft', prompt: 'Draft a concise source-grounded section using only propositions supported by the loaded record. Preserve uncertainty and pinpoint citations.', tool: 'Record Search' },
    { label: 'Build', prompt: 'Build a structured packet outline from verified evidence, chronology, functional impact, governing framework, and cited source appendix.', tool: 'Packet Assurance', view: 'packet' },
    { label: 'Verify', prompt: 'Verify quote integrity, provenance, chronology, conflicts, uncited propositions, and remaining review blockers.', tool: 'Packet Assurance', view: 'review' },
    { label: 'Export', prompt: 'Prepare this case for export. Check completeness, citation integrity, source visuals, and explicitly flag any remaining visual-QA or under-5-MB compression work.', tool: 'Packet Assurance', view: 'packet' },
];

const evidenceCategories: EvidenceCategory[] = ['Medical Records', 'Imaging / Tests', 'Military / Service', 'VA / Benefits', 'Disability / SSA / State', 'Functional Capacity', 'Correspondence', 'Legal / Administrative', 'Other'];

function categorizeDocument(document: Doc): EvidenceCategory {
    const sample = `${document.name} ${document.excerpt}`.toLowerCase();
    if (/mri|x-ray|xray|ct |ultrasound|emg|eeg|imaging|radiology|diagnostic test/.test(sample)) return 'Imaging / Tests';
    if (/army|guard|military|service|orders|ngb|dd214|duty|lod|line of duty|acdutra|inacdutra|title 32/.test(sample)) return 'Military / Service';
    if (/va |vba|veteran|dbq|c&p|compensation|tdiu|rating decision/.test(sample)) return 'VA / Benefits';
    if (/ssdi|ssi|social security|aptd|dhhs|disability determination|state disability/.test(sample)) return 'Disability / SSA / State';
    if (/fce|functional capacity|work capacity|attendance|pace|persistence|reliability|lifting|sitting|standing/.test(sample)) return 'Functional Capacity';
    if (/email|letter|message|correspondence|memo/.test(sample) || document.sourceMode === 'email') return 'Correspondence';
    if (/court|legal|attorney|hearing|appeal|administrative|decision|denial|notice/.test(sample)) return 'Legal / Administrative';
    if (/medical|clinical|provider|hospital|clinic|patient|treatment|diagnosis|therapy|physician|nurse/.test(sample)) return 'Medical Records';
    return 'Other';
}
const benefitsIssueOptions: Record<BenefitsProgram, string[]> = {
    'VA / VBA': ['Service connection', 'Secondary / aggravation', 'Increased rating', 'TDIU', 'Mental health rating', 'Neurologic / migraines', 'Musculoskeletal rating'],
    'Social Security (SSDI / SSI)': ['Adult disability framework', 'RFC / sustained work capacity', 'Medical opinions / evidence', 'Neurologic listings', 'Mental health listings'],
    'New Hampshire': ['APTD disability standard', 'MEAD / disability Medicaid', 'State assistance evidence'],
    'Medical & Functional Evidence': ['Cross-program functional capacity', 'Objective findings / symptoms', 'Neurologic functional evidence', 'Mental functional evidence'],
};

const quickCreateActions: Array<{ label: string; prompt: string; tool: PluginName }> = [
    { label: 'Evidence Brief', prompt: 'Create a concise reviewer-ready evidence brief from the loaded record with an executive summary, strongest evidence, chronology, functional impact when documented, adverse evidence that must be reconciled, and a short missing-evidence plan. Cite filenames for material facts.', tool: 'Packet Assurance' },
    { label: 'C&P Rebuttal Draft', prompt: 'Create a restrained source-grounded C&P rebuttal draft that identifies the examiner finding, the contrary record evidence, why the conflict matters, and what should be corrected or reconciled. Do not invent examiner motives or unsupported medical causation.', tool: 'Rebuttal Lab' },
    { label: 'Hearing Timeline', prompt: 'Create a hearing-ready chronology from the loaded record with dates, events, source filenames, objective findings, reported symptoms, functional effects, and unresolved date gaps.', tool: 'Timeline Builder' },
];

function App() {
    const [user, setUser] = useState<User | null>(null);
    const [appMode, setAppMode] = useState<AppMode>(() => window.localStorage.getItem('elias-app-mode') === 'pro' ? 'pro' : 'simple');
    const [view, setView] = useState<View>('chat');
    const [memory, setMemory] = useState<Memory>(emptyMemory);
    const [documents, setDocuments] = useState<Doc[]>([]);
    const [chats, setChats] = useState<Chat[]>([]);
    const [threadId, setThreadId] = useState(() => crypto.randomUUID());
    const [question, setQuestion] = useState('');
    const [tool, setTool] = useState<PluginName>('Record Search');
    const [plugins, setPlugins] = useState<Record<PluginName, boolean>>(defaultPlugins);
    const [workMode, setWorkMode] = useState<WorkMode>('Standard');
    const [busy, setBusy] = useState('');
    const [notice, setNotice] = useState('');
    const [uploadSuccessNotice, setUploadSuccessNotice] = useState('');
    const [review, setReview] = useState<Review | null>(null);
    const [packet, setPacket] = useState<Packet | null>(null);
    const [packetStyle, setPacketStyle] = useState('Visual evidence review');
    const [playbook, setPlaybook] = useState('Elias Evidence Playbook v7');
    const [benefitsProgram, setBenefitsProgram] = useState<BenefitsProgram>('VA / VBA');
    const [lawIssue, setLawIssue] = useState('Service connection');
    const [lawLens, setLawLens] = useState<LawLens | null>(null);
    const [webUrl, setWebUrl] = useState('');
    const [webQuestion, setWebQuestion] = useState('What matters here for this case?');
    const [saveWebToCase, setSaveWebToCase] = useState(false);
    const [webResult, setWebResult] = useState<WebResult | null>(null);
    const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
    const [voiceName, setVoiceName] = useState('Auto');
    const [voicePreset, setVoicePreset] = useState('Younger Distinguished');
    const [autoSpeak, setAutoSpeak] = useState(false);
    const [voiceEngine, setVoiceEngine] = useState<'Browser' | 'Neural'>('Browser');
    const [integrations, setIntegrations] = useState<IntegrationStatus>({ webSearch: false, neuralVoice: false, gmailDirect: false, gmailNote: 'Direct Gmail OAuth is not connected.', cloudVault: true, googleDriveDirect: false, driveNote: 'Private Case Vault is available; direct Google Drive sync requires secure per-user OAuth.' });
    const [submissionBrief, setSubmissionBrief] = useState<SubmissionBrief | null>(null);
    const [submissionPreviewBlob, setSubmissionPreviewBlob] = useState<Blob | null>(null);
    const [submissionPreviewUrl, setSubmissionPreviewUrl] = useState('');
    const [submissionPreviewName, setSubmissionPreviewName] = useState('');
    const [vaultStatus, setVaultStatus] = useState<VaultStatus | null>(null);
    const [evidenceInventory, setEvidenceInventory] = useState<EvidenceInventory | null>(null);
    const [neuralVoices, setNeuralVoices] = useState<NeuralVoice[]>([]);
    const [neuralVoiceId, setNeuralVoiceId] = useState('');
    const [mediaFiles, setMediaFiles] = useState<File[]>([]);
    const [uploadItems, setUploadItems] = useState<UploadItem[]>([]);
    const [searchQuery, setSearchQuery] = useState('');
    const [saveSearchToCase, setSaveSearchToCase] = useState(false);
    const [liveSearchResult, setLiveSearchResult] = useState<LiveSearchResult | null>(null);
    const [copilotOpen, setCopilotOpen] = useState(false);
    const [copilotInput, setCopilotInput] = useState('');
    const [copilotBusy, setCopilotBusy] = useState(false);
    const [copilotPhase, setCopilotPhase] = useState(0);
    const [copilotAnswer, setCopilotAnswer] = useState('');
    const [copilotRole, setCopilotRole] = useState<CopilotRole>('Elias');
    const [vaultQuery, setVaultQuery] = useState('');
    const [videoPreviewUrl, setVideoPreviewUrl] = useState('');
    const [videoRate, setVideoRate] = useState(1);
    const fileRef = useRef<HTMLInputElement>(null);
    const mediaRef = useRef<HTMLInputElement>(null);
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const copilotResultRef = useRef<HTMLDivElement | null>(null);
    const speechRunRef = useRef(0);
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const selectedVideo = useMemo(() => mediaFiles.find((file) => file.type.startsWith('video/')) ?? null, [mediaFiles]);

    const errorMessage = (err: unknown, fallback: string) => {
        const value = err as { message?: string; response?: { data?: { error?: string; message?: string } } };
        const raw = value.response?.data?.error || value.response?.data?.message || value.message || fallback;
        if (/internal server error|status code 500|failed with status 500/i.test(raw)) return 'Elias hit a processing limit before the result finished. Your indexed evidence is still intact. Try Standard mode, narrow the request, or run the task again; Elias will automatically use a lighter fallback pass when possible.';
        return raw;
    };

    const updateUploadItem = (id: string, patch: Partial<UploadItem>) => {
        setUploadItems((current) => current.map((item) => item.id === id ? { ...item, ...patch } : item));
    };

    const formatFileSize = (bytes: number) => bytes >= 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(bytes >= 100 * 1024 * 1024 ? 0 : 1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`; 

    const loadEvidenceInventory = async () => {
        try {
            const { data } = await api.get('/api/evidence/inventory');
            setEvidenceInventory(data);
        } catch {
            setEvidenceInventory(null);
        }
    };

    const load = async () => {
        const { data } = await api.get('/api/bootstrap');
        setMemory(data.memory ? { ...emptyMemory, ...data.memory } : emptyMemory);
        setDocuments(data.documents ?? []);
        setChats(data.chats ?? []);
        if (data.playbook) setPlaybook(data.playbook);
        await loadEvidenceInventory();
    };

    const loadIntegrations = async () => {
        try {
            const { data } = await api.get('/api/integrations/status');
            setIntegrations(data);
            if (data.neuralVoice) {
                const voiceResponse = await api.get('/api/voice/voices');
                const available: NeuralVoice[] = voiceResponse.data.voices ?? [];
                setNeuralVoices(available);
                if (available.length && !neuralVoiceId) setNeuralVoiceId(available[0].voiceId);
            }
        } catch {
            setIntegrations((current) => ({ ...current, webSearch: false, neuralVoice: false }));
        }
    };

    useEffect(() => {
        const boot = async () => {
            if (!auth.isSignedIn()) return;
            const current = await auth.getUser();
            if (current) {
                setUser(current);
                await load();
                await loadIntegrations();
            }
        };
        void boot();
    }, []);

    useEffect(() => {
        window.localStorage.setItem('elias-app-mode', appMode);
    }, [appMode]);

    useEffect(() => {
        if (!submissionBrief) {
            setSubmissionPreviewBlob(null);
            setSubmissionPreviewUrl('');
            setSubmissionPreviewName('');
            return undefined;
        }
        const built = buildSubmissionPdf(submissionBrief, memory.caseLabel || 'Evidence_Case');
        const url = URL.createObjectURL(built.blob);
        setSubmissionPreviewBlob(built.blob);
        setSubmissionPreviewUrl(url);
        setSubmissionPreviewName(built.filename);
        return () => URL.revokeObjectURL(url);
    }, [submissionBrief, memory.caseLabel]);

    useEffect(() => {
        const refreshVoices = () => setVoices(window.speechSynthesis?.getVoices?.() ?? []);
        refreshVoices();
        if ('speechSynthesis' in window) window.speechSynthesis.onvoiceschanged = refreshVoices;
        return () => { if ('speechSynthesis' in window) window.speechSynthesis.onvoiceschanged = null; };
    }, []);

    useEffect(() => {
        if (!copilotBusy) {
            setCopilotPhase(0);
            return undefined;
        }
        const timer = window.setInterval(() => setCopilotPhase((value) => (value + 1) % copilotPhases.length), 1350);
        return () => window.clearInterval(timer);
    }, [copilotBusy]);

    useEffect(() => {
        if (!selectedVideo) {
            setVideoPreviewUrl('');
            return undefined;
        }
        const url = URL.createObjectURL(selectedVideo);
        setVideoPreviewUrl(url);
        return () => URL.revokeObjectURL(url);
    }, [selectedVideo]);

    useEffect(() => {
        if (videoRef.current) videoRef.current.playbackRate = videoRate;
    }, [videoRate, videoPreviewUrl]);

    useEffect(() => {
        if (!copilotOpen) return;
        const frame = window.requestAnimationFrame(() => copilotResultRef.current?.scrollTo({ top: copilotResultRef.current.scrollHeight, behavior: 'smooth' }));
        return () => window.cancelAnimationFrame(frame);
    }, [copilotOpen, copilotBusy, copilotAnswer, copilotPhase]);

    const signIn = async () => {
        try {
            const result = await auth.signIn();
            setUser(result.user);
            await load();
            await loadIntegrations();
        } catch (err) {
            const code = (err as { code?: string }).code;
            setNotice(code === 'popup_blocked' ? 'Allow popups, then try signing in again.' : 'Sign-in was not completed.');
        }
    };

    const signOut = async () => {
        window.speechSynthesis?.cancel();
        await auth.signOut();
        setUser(null);
        setDocuments([]);
        setChats([]);
        setMemory(emptyMemory);
    };

    const saveMemory = async () => {
        setBusy('Saving memory…');
        try {
            const { data } = await api.put('/api/memory', memory);
            setMemory(data.memory);
            setNotice('Case memory saved.');
        } catch (err) {
            setNotice(errorMessage(err, 'Memory could not be saved.'));
        } finally { setBusy(''); }
    };

    const encodeBlob = (blob: Blob) => new Promise<string>((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result).split(',')[1] ?? '');
        reader.onerror = () => reject(reader.error);
        reader.readAsDataURL(blob);
    });

    const uploadDocument = async (file: File, uploadItemId: string) => {
        if (file.size > 24 * 1024 * 1024) throw new Error(`${file.name} is still too large after splitting.`);
        const chunkSize = 320 * 1024;
        const total = Math.ceil(file.size / chunkSize);
        const uploadId = crypto.randomUUID();
        updateUploadItem(uploadItemId, { stage: 'Uploading', progress: 2, detail: 'Starting upload…' });
        for (let index = 0; index < total; index += 1) {
            setBusy(`Uploading ${file.name} · chunk ${index + 1} of ${total}…`);
            const slice = file.slice(index * chunkSize, Math.min(file.size, (index + 1) * chunkSize));
            const base64 = await encodeBlob(slice);
            await api.post('/api/uploads/chunk', { uploadId, index, total, base64 });
            const progress = Math.max(3, Math.min(88, Math.round(((index + 1) / total) * 88)));
            updateUploadItem(uploadItemId, { stage: 'Uploading', progress, detail: `Uploading · ${index + 1} of ${total} chunks` });
        }
        setBusy(`Indexing ${file.name}…`);
        updateUploadItem(uploadItemId, { stage: 'Indexing', progress: 94, detail: 'Extracting and indexing text…' });
        const lowerName = file.name.toLowerCase();
        const normalizedType = /\.(eml|mbox)$/.test(lowerName) ? 'text/plain' : file.type || (lowerName.endsWith('.md') ? 'text/markdown' : 'text/plain');
        await api.post('/api/uploads/finalize', {
            uploadId,
            total,
            name: file.name,
            contentType: normalizedType,
        });
        updateUploadItem(uploadItemId, { stage: 'Ready', progress: 100, detail: 'Indexed and ready for Elias' });
    };

    const splitAndUploadPdf = async (file: File, uploadItemId: string) => {
        const directLimit = 24 * 1024 * 1024;
        const largePdfLimit = 250 * 1024 * 1024;
        if (file.size <= directLimit) {
            await uploadDocument(file, uploadItemId);
            return 1;
        }
        if (file.size > largePdfLimit) throw new Error(`${file.name} is over the 250 MB large-PDF limit.`);

        updateUploadItem(uploadItemId, { stage: 'Reading', progress: 2, detail: 'Opening large PDF locally…' });
        setBusy(`Opening ${file.name} locally in large-PDF mode…`);
        let loadingTask: ReturnType<typeof getDocument> | null = null;
        try {
            const bytes = new Uint8Array(await file.arrayBuffer());
            loadingTask = getDocument({ data: bytes, isEvalSupported: false });
            const pdf = await loadingTask.promise;
            const totalPages = pdf.numPages;
            if (!totalPages) throw new Error('No PDF pages were found.');

            let batchStart = 1;
            let batchText = '';
            let partNumber = 0;
            let extractedCharacters = 0;

            const flush = async (endPage: number) => {
                const text = batchText.trim();
                if (!text) {
                    batchStart = endPage + 1;
                    batchText = '';
                    return;
                }
                partNumber += 1;
                setBusy(`Indexing ${file.name} · pages ${batchStart}-${endPage} of ${totalPages}…`);
                updateUploadItem(uploadItemId, { stage: 'Indexing', progress: Math.max(10, Math.min(96, Math.round((endPage / totalPages) * 94))), detail: `Indexing pages ${batchStart}-${endPage} of ${totalPages}` });
                await api.post('/api/uploads/extracted-part', {
                    originalName: file.name,
                    startPage: batchStart,
                    endPage,
                    totalPages,
                    text,
                    partNumber,
                });
                batchStart = endPage + 1;
                batchText = '';
            };

            for (let pageNumber = 1; pageNumber <= totalPages; pageNumber += 1) {
                setBusy(`Reading ${file.name} · page ${pageNumber} of ${totalPages}…`);
                updateUploadItem(uploadItemId, { stage: 'Reading', progress: Math.max(4, Math.min(90, Math.round((pageNumber / totalPages) * 90))), detail: `Reading page ${pageNumber} of ${totalPages}` });
                const page = await pdf.getPage(pageNumber);
                const content = await page.getTextContent();
                const pageText = content.items
                    .map((item) => ('str' in item ? item.str : ''))
                    .join(' ')
                    .replace(/\s+/g, ' ')
                    .trim();
                page.cleanup();
                extractedCharacters += pageText.length;
                const tagged = pageText ? `\n\n--- PAGE ${pageNumber} ---\n${pageText}` : '';
                if (batchText && (batchText.length + tagged.length > 40000 || pageNumber - batchStart >= 19)) {
                    await flush(pageNumber - 1);
                    batchStart = pageNumber;
                }
                batchText += tagged;
            }
            if (batchText.trim()) await flush(totalPages);
            await pdf.cleanup();

            if (extractedCharacters < 100) {
                throw new Error(`${file.name} looks like an image-only scanned PDF. Large searchable PDFs can be indexed automatically; scanned-only PDFs still need OCR page images for now.`);
            }
            updateUploadItem(uploadItemId, { stage: 'Ready', progress: 100, detail: `${totalPages} pages indexed and ready for Elias` });
            return Math.max(1, partNumber);
        } catch (err) {
            const message = err instanceof Error ? err.message : '';
            if (message.includes('image-only scanned PDF')) throw err;
            throw new Error(`${file.name} could not be indexed in large-PDF mode. ${message || 'It may be encrypted, damaged, or use an unsupported PDF structure.'}`);
        } finally {
            if (loadingTask) {
                try { await loadingTask.destroy(); } catch { /* ignore cleanup failure */ }
            }
        }
    };

    const uploadImage = async (file: File, uploadItemId: string) => {
        if (!plugins['OCR Intake']) throw new Error('OCR Intake is disabled in Plugins.');
        setBusy(`Preparing ${file.name} for OCR…`);
        updateUploadItem(uploadItemId, { stage: 'OCR', progress: 18, detail: 'Preparing image for OCR…' });
        const prepared = await image.resizeIfNeeded(file, { maxDimension: 1400, maxPixels: 1500000, quality: 0.76, mimeType: 'image/jpeg' });
        setBusy(`OCR reading ${file.name}…`);
        updateUploadItem(uploadItemId, { stage: 'OCR', progress: 58, detail: 'Reading visible text…' });
        await api.post('/api/uploads/image', { name: file.name, mimeType: prepared.mimeType, base64: prepared.data });
        updateUploadItem(uploadItemId, { stage: 'Ready', progress: 100, detail: 'OCR complete and ready for Elias' });
    };

    const upload = async (files: FileList | null) => {
        const selected = Array.from(files ?? []);
        if (!selected.length) return;
        setNotice('');
        setUploadSuccessNotice('');
        const staged = selected.map((file) => {
            const isImage = file.type.startsWith('image/') || /\.(png|jpe?g|webp)$/i.test(file.name);
            const isPdf = file.type === 'application/pdf' || /\.pdf$/i.test(file.name);
            const kind: UploadItem['kind'] = isPdf ? 'pdf' : isImage ? 'image' : 'file';
            return { file, id: crypto.randomUUID(), kind };
        });
        setUploadItems((current) => [...current, ...staged.map(({ file, id, kind }) => ({ id, name: file.name, size: file.size, kind, stage: 'Queued' as const, progress: 0, detail: 'Waiting to upload' }))]);
        let splitParts = 0;
        let successful = 0;
        const failures: string[] = [];
        for (const entry of staged) {
            try {
                updateUploadItem(entry.id, { stage: 'Uploading', progress: 1, detail: 'Starting…', error: undefined });
                if (entry.kind === 'image') await uploadImage(entry.file, entry.id);
                else if (entry.kind === 'pdf') splitParts += await splitAndUploadPdf(entry.file, entry.id);
                else await uploadDocument(entry.file, entry.id);
                successful += 1;
            } catch (err) {
                const message = errorMessage(err, 'Upload failed.');
                failures.push(`${entry.file.name}: ${message}`);
                updateUploadItem(entry.id, { stage: 'Error', progress: 100, detail: 'Upload failed', error: message });
            }
        }
        if (successful) {
            setSubmissionBrief(null);
            setPacket(null);
            await load();
            try {
                await api.post('/api/vault/organize');
                const vault = await api.get('/api/vault/status');
                setVaultStatus(vault.data);
            } catch {
                // Evidence indexing succeeds independently if cloud organization is temporarily unavailable.
            }
        }
        const pdfCount = staged.filter((entry) => entry.kind === 'pdf').length;
        const splitNote = splitParts > pdfCount ? ` Large PDFs were indexed into ${splitParts} searchable page-range parts.` : '';
        if (successful) setUploadSuccessNotice(`${successful} file${successful === 1 ? '' : 's'} uploaded, indexed, and ready for Elias.${splitNote}`);
        setNotice(failures.length ? `${failures.length} file${failures.length === 1 ? '' : 's'} could not be indexed. Open the upload card for the specific error.` : '');
        setBusy('');
        if (fileRef.current) fileRef.current.value = '';
    };

    const voiceSettings = () => {
        if (voicePreset === 'Command Briefing') return { rate: 0.89, pitch: 0.93 };
        if (voicePreset === 'Calm Clinical') return { rate: 0.90, pitch: 0.98 };
        if (voicePreset === 'Natural') return { rate: 0.98, pitch: 1.0 };
        return { rate: 0.92, pitch: 0.99 };
    };

    const bestAvailableVoice = () => {
        const candidates = voices.filter((voice) => /^en/i.test(voice.lang));
        const score = (voice: SpeechSynthesisVoice) => {
            const name = voice.name.toLowerCase();
            let value = voice.lang.toLowerCase().startsWith('en-us') ? 5 : 0;
            if (/natural|neural|premium|enhanced|online/.test(name)) value += 30;
            if (/microsoft|google|apple|samantha|daniel|ava|jenny|guy/.test(name)) value += 8;
            if (!voice.localService) value += 2;
            return value;
        };
        return [...candidates].sort((a, b) => score(b) - score(a))[0] ?? voices[0];
    };

    const stopSpeaking = () => {
        speechRunRef.current += 1;
        window.speechSynthesis?.cancel();
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.src = '';
            audioRef.current = null;
        }
    };

    const base64AudioUrl = (base64: string, mimeType: string) => {
        const binary = atob(base64);
        const bytes = new Uint8Array(binary.length);
        for (let index = 0; index < binary.length; index += 1) bytes[index] = binary.charCodeAt(index);
        return URL.createObjectURL(new Blob([bytes], { type: mimeType }));
    };

    const speakNeural = async (text: string) => {
        if (!integrations.neuralVoice || !neuralVoiceId) {
            setNotice('Neural voice is not connected yet. Browser voice is still available.');
            return;
        }
        stopSpeaking();
        const runId = speechRunRef.current;
        const clean = text.replace(/\[[^\]]+\]/g, '').replace(/\s+/g, ' ').trim();
        const chunks = clean.match(/.{1,1700}(?:\s|$)/g) ?? [clean];
        for (const chunk of chunks) {
            if (speechRunRef.current !== runId) return;
            const { data } = await api.post('/api/voice/speak', { text: chunk.trim(), voiceId: neuralVoiceId, preset: voicePreset });
            const url = base64AudioUrl(data.audioBase64, data.mimeType || 'audio/mpeg');
            await new Promise<void>((resolve, reject) => {
                const audio = new Audio(url);
                audioRef.current = audio;
                audio.onended = () => { URL.revokeObjectURL(url); resolve(); };
                audio.onerror = () => { URL.revokeObjectURL(url); reject(new Error('Neural voice playback failed.')); };
                void audio.play().catch(reject);
            });
        }
        audioRef.current = null;
    };

    const speak = (text: string) => {
        if (voiceEngine === 'Neural') {
            void speakNeural(text).catch((err) => setNotice(errorMessage(err, 'Neural voice playback failed.')));
            return;
        }
        if (!('speechSynthesis' in window)) {
            setNotice('Voice playback is not available in this browser.');
            return;
        }
        stopSpeaking();
        const runId = speechRunRef.current;
        const clean = text.replace(/\[[^\]]+\]/g, '').replace(/\s+/g, ' ').trim();
        const sentences = clean.match(/[^.!?]+[.!?]+|[^.!?]+$/g) ?? [clean];
        const chunks: string[] = [];
        let current = '';
        for (const sentence of sentences) {
            const candidate = `${current} ${sentence}`.trim();
            if (current && candidate.length > 260) {
                chunks.push(current);
                current = sentence.trim();
            } else current = candidate;
        }
        if (current) chunks.push(current);
        const chosen = voiceName === 'Auto' ? bestAvailableVoice() : voices.find((voice) => voice.name === voiceName) ?? bestAvailableVoice();
        const { rate, pitch } = voiceSettings();
        const speakChunk = (index: number) => {
            if (speechRunRef.current !== runId || index >= chunks.length) return;
            const utterance = new SpeechSynthesisUtterance(chunks[index]);
            utterance.rate = rate;
            utterance.pitch = pitch;
            if (chosen) utterance.voice = chosen;
            utterance.onend = () => speakChunk(index + 1);
            utterance.onerror = () => { if (speechRunRef.current === runId) setNotice('Voice playback stopped unexpectedly. Try another browser voice.'); };
            window.speechSynthesis.speak(utterance);
        };
        speakChunk(0);
    };

    const sampleVideoFrames = async (file: File) => {
        if (file.size > 200 * 1024 * 1024) throw new Error(`${file.name} is over the 200 MB local video-analysis limit.`);
        const url = URL.createObjectURL(file);
        const video = document.createElement('video');
        video.muted = true;
        video.preload = 'metadata';
        video.src = url;
        await new Promise<void>((resolve, reject) => {
            video.onloadedmetadata = () => resolve();
            video.onerror = () => reject(new Error(`Could not open ${file.name} in this browser.`));
        });
        const duration = Number.isFinite(video.duration) && video.duration > 0 ? video.duration : 1;
        const times = [0.05, 0.27, 0.5, 0.73, 0.95].map((fraction) => Math.min(Math.max(0, duration * fraction), Math.max(0, duration - 0.05)));
        const frames: Array<{ data: string; mimeType: string; label: string }> = [];
        try {
            for (let index = 0; index < times.length; index += 1) {
                setBusy(`Sampling ${file.name} · frame ${index + 1} of ${times.length}…`);
                video.currentTime = times[index];
                await new Promise<void>((resolve, reject) => {
                    const timeout = window.setTimeout(() => reject(new Error('Video seek timed out.')), 8000);
                    video.onseeked = () => { window.clearTimeout(timeout); resolve(); };
                });
                const scale = Math.min(1, 1200 / Math.max(video.videoWidth || 1200, video.videoHeight || 675));
                const canvas = document.createElement('canvas');
                canvas.width = Math.max(1, Math.round((video.videoWidth || 1200) * scale));
                canvas.height = Math.max(1, Math.round((video.videoHeight || 675) * scale));
                const context = canvas.getContext('2d');
                if (!context) throw new Error('Video frame capture is unavailable in this browser.');
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
                const blob = await new Promise<Blob>((resolve, reject) => canvas.toBlob((value) => value ? resolve(value) : reject(new Error('Could not capture video frame.')), 'image/jpeg', 0.72));
                const prepared = await image.resizeIfNeeded(blob, { maxDimension: 1200, maxPixels: 1000000, quality: 0.72, mimeType: 'image/jpeg' });
                frames.push({ data: prepared.data, mimeType: prepared.mimeType, label: `${file.name} frame ${index + 1}/${times.length} at ${times[index].toFixed(1)}s` });
            }
            return frames;
        } finally {
            URL.revokeObjectURL(url);
        }
    };

    const prepareMedia = async (files: File[]) => {
        const images: Array<{ data: string; mimeType: string; label: string }> = [];
        const audios: Array<{ data: string; mimeType: string; label: string }> = [];
        const notes: string[] = [];
        let audioBytes = 0;
        for (const file of files.slice(0, 5)) {
            if (file.type.startsWith('video/')) {
                images.push(...await sampleVideoFrames(file));
                notes.push(`${file.name}: analyzed from five representative visual frames; its audio track was not transcribed.`);
            } else if (file.type.startsWith('audio/')) {
                audioBytes += file.size;
                if (file.size > 2 * 1024 * 1024 || audioBytes > 4 * 1024 * 1024) throw new Error('Audio attachments must stay under 2 MB each and 4 MB total.');
                audios.push({ data: await encodeBlob(file), mimeType: file.type || 'audio/mpeg', label: file.name });
            } else if (file.type.startsWith('image/')) {
                const prepared = await image.resizeIfNeeded(file, { maxDimension: 1400, maxPixels: 1500000, quality: 0.78, mimeType: 'image/jpeg' });
                images.push({ data: prepared.data, mimeType: prepared.mimeType, label: file.name });
            }
        }
        return { images: images.slice(0, 5), audios: audios.slice(0, 3), mediaNotes: notes.join('\n') };
    };

    const send = async () => {
        const q = question.trim() || (mediaFiles.length ? 'Analyze the attached media and explain what is relevant.' : '');
        if (!q || busy) return;
        setQuestion('');
        setBusy(workMode === 'Deep' ? 'Elias is doing a deep review…' : workMode === 'Quick' ? 'Elias is answering quickly…' : 'Elias is reviewing…');
        try {
            const { data } = mediaFiles.length
                ? await api.post('/api/multimodal', { question: q, threadId, speed: workMode, ...await prepareMedia(mediaFiles) })
                : await api.post('/api/chat', { question: q, threadId, tool, speed: workMode });
            setChats((prev) => [...prev, data.message]);
            setMediaFiles([]);
            if (autoSpeak) speak(data.message.answer);
        } catch (err) {
            setNotice(errorMessage(err, 'Elias could not answer that request.'));
        } finally { setBusy(''); }
    };

    const runCopilot = async (rawPrompt: string, requestedTool?: PluginName) => {
        const prompt = rawPrompt.trim();
        if (!prompt || copilotBusy || busy) return;
        setCopilotOpen(true);
        setCopilotBusy(true);
        setCopilotAnswer('');
        setNotice('');
        try {
            const specialist = copilotSpecialists.find((item) => item.name === copilotRole) ?? copilotSpecialists[0];
            const preferredTool = requestedTool ?? specialist.defaultTool;
            const selectedTool = plugins[preferredTool] ? preferredTool : 'Record Search';
            const rolePrompt = copilotRole === 'Elias' ? prompt : `[${copilotRole} specialist mode] ${prompt}`;
            const { data } = await api.post('/api/chat', { question: rolePrompt, threadId, tool: selectedTool, speed: workMode });
            setChats((prev) => [...prev, data.message]);
            setCopilotAnswer(data.message.answer);
            if (autoSpeak) speak(data.message.answer);
        } catch (err) {
            setCopilotAnswer(errorMessage(err, 'Elias could not complete that Copilot request.'));
        } finally {
            setCopilotBusy(false);
        }
    };

    const stepVideo = (frames: number) => {
        const video = videoRef.current;
        if (!video) return;
        video.pause();
        video.currentTime = Math.max(0, Math.min(video.duration || Number.MAX_SAFE_INTEGER, video.currentTime + frames / 30));
    };

    const runMotionStudy = async () => {
        if (!mediaFiles.length || !selectedVideo || busy || copilotBusy) return;
        const prompt = 'Analyze this video as a motion-imaging study using representative sampled frames. Describe the observed motion sequence, direction and planes of movement when visually supportable, asymmetry or displacement, key sampled moments, and uncertainty. Clearly distinguish direct observation from inference. Do not call this calibrated medical 3D reconstruction and do not diagnose from the video.';
        setCopilotOpen(true);
        setCopilotBusy(true);
        setCopilotAnswer('');
        setNotice('');
        setBusy('Elias is building a motion-imaging study…');
        try {
            const { data } = await api.post('/api/multimodal', { question: prompt, threadId, speed: workMode, ...await prepareMedia(mediaFiles) });
            setChats((prev) => [...prev, data.message]);
            setCopilotAnswer(data.message.answer);
            if (autoSpeak) speak(data.message.answer);
        } catch (err) {
            setCopilotAnswer(errorMessage(err, 'Elias could not complete the motion study.'));
        } finally {
            setBusy('');
            setCopilotBusy(false);
        }
    };

    const oneClickPacket = async () => {
        if (busy || copilotBusy) return;
        if (!documents.length) {
            setView('chat');
            setNotice('Add at least one medical, administrative, service, or benefits record before building a full case package.');
            return;
        }
        setView('packet');
        setPacketStyle('Visual evidence review');
        setNotice('');
        let lawNote = '';
        try {
            setBusy('Step 1 of 3 · Auditing strengths, weaknesses, chronology, and evidence gaps…');
            const reviewResponse = await api.post('/api/review', { speed: workMode });
            setReview(reviewResponse.data.review);
            setBusy(`Step 2 of 3 · Checking ${benefitsProgram} rules against live official web sources…`);
            try {
                const lensResponse = await api.post('/api/benefits-lens', { program: benefitsProgram, issue: lawIssue, speed: workMode });
                setLawLens(lensResponse.data.lens);
            } catch (lawError) {
                setLawLens(null);
                lawNote = ` The core package is complete, but the live benefits-law crosswalk could not finish: ${errorMessage(lawError, 'official web references were temporarily unavailable')}`;
            }
            setBusy('Step 3 of 3 · Building the visual reviewer package and PDF-ready report…');
            const packetResponse = await api.post('/api/packet', { style: 'Visual evidence review', speed: workMode });
            setPacket(packetResponse.data.packet);
            setNotice(`Full case package ready: evidence strengths, weaknesses, missing information, recommended next steps, chronology, source appendix, and PDF-ready visuals.${lawNote}`);
        } catch (err) {
            setNotice(errorMessage(err, 'Full case package creation failed. Your indexed sources remain intact.'));
        } finally { setBusy(''); }
    }; 

    const createSubmissionBrief = async () => {
        if (!documents.length || busy || copilotBusy) return;
        setBusy(`Building a filing-focused ${benefitsProgram} advocacy brief with verified authorities…`);
        setNotice('');
        try {
            const { data } = await api.post('/api/submission-brief', { program: benefitsProgram, issue: lawIssue, speed: workMode === 'Quick' ? 'Standard' : workMode });
            setSubmissionBrief(data.brief);
            const preflightStatus = data.preflight?.status || data.brief?.preflight?.status || 'Draft';
            const blockerCount = data.preflight?.blockers?.length || data.brief?.preflight?.blockers?.length || 0;
            setNotice(`Submission draft created · ${preflightStatus}${blockerCount ? ` · ${blockerCount} blocker${blockerCount === 1 ? '' : 's'} to review` : ''}. Elias keeps the internal neutral audit separate from this advocacy filing and includes only verified literature returned for the selected public issue.`);
        } catch (err) {
            setNotice(errorMessage(err, 'Submission advocacy brief could not be created.'));
        } finally { setBusy(''); }
    };

    const downloadSubmissionBrief = () => {
        if (!submissionBrief) return;
        const built = buildSubmissionPdf(submissionBrief, memory.caseLabel || 'Evidence_Case');
        const url = URL.createObjectURL(built.blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = built.filename;
        link.click();
        window.setTimeout(() => URL.revokeObjectURL(url), 1200);
    };

    const saveSubmissionToVault = async () => {
        if (!submissionBrief) return;
        setBusy('Saving the submission PDF to your private Case Vault…');
        setNotice('');
        try {
            const built = buildSubmissionPdf(submissionBrief, memory.caseLabel || 'Evidence_Case');
            const base64 = await encodeBlob(built.blob);
            await api.post('/api/vault/generated-file', { name: built.filename, base64, contentType: 'application/pdf' });
            const vault = await api.get('/api/vault/status');
            setVaultStatus(vault.data);
            setNotice('Submission PDF saved under 06_Submission_Packets in your private Case Vault.');
        } catch (err) {
            setNotice(errorMessage(err, 'The PDF could not be saved to Case Vault.'));
        } finally { setBusy(''); }
    };

    const organizeVault = async () => {
        setBusy('Organizing private cloud evidence into Case Vault folders…');
        setNotice('');
        try {
            const { data } = await api.post('/api/vault/organize');
            const vault = await api.get('/api/vault/status');
            setVaultStatus(vault.data);
            setNotice(`Case Vault organized: ${data.organized} stored source${data.organized === 1 ? '' : 's'}; ${data.indexedOnly} indexed-only source${data.indexedOnly === 1 ? '' : 's'}. Indexed-only usually means a large PDF was text-indexed without retaining the original binary.`);
        } catch (err) {
            setNotice(errorMessage(err, 'Case Vault organization failed.'));
        } finally { setBusy(''); }
    };

    const exportVault = async () => {
        setBusy('Building a Google-Drive-ready Case Vault ZIP…');
        setNotice('');
        try {
            const { data } = await api.post('/api/vault/export');
            const link = document.createElement('a');
            link.href = data.url;
            link.download = 'Elias_Case_Vault_Drive_Ready.zip';
            link.target = '_blank';
            link.rel = 'noreferrer';
            link.click();
            setNotice(`Drive-ready Case Vault ZIP created with ${data.fileCount} organized file${data.fileCount === 1 ? '' : 's'}. Upload or extract it in Google Drive to preserve the folder structure.`);
        } catch (err) {
            setNotice(errorMessage(err, 'Case Vault ZIP export failed.'));
        } finally { setBusy(''); }
    };

    const runLawLens = async () => {
        if (!plugins['Benefits Law & Medical Lens']) {
            setNotice('Benefits Law & Medical Lens is disabled in Plugins.');
            return;
        }
        setBusy(`Comparing ${benefitsProgram} · ${lawIssue} with the loaded evidence…`);
        setNotice('');
        try {
            const { data } = await api.post('/api/benefits-lens', { program: benefitsProgram, issue: lawIssue, speed: workMode });
            setLawLens(data.lens);
        } catch (err) {
            setNotice(errorMessage(err, 'Benefits Law & Medical Lens could not run.'));
        } finally { setBusy(''); }
    };

    const runWebSearch = async () => {
        if (!integrations.webSearch) {
            setNotice('Live Web Search is not connected yet. URL Research still works without it.');
            return;
        }
        if (!searchQuery.trim()) {
            setNotice('Enter a web search question first.');
            return;
        }
        setBusy('Searching the live web and comparing results with the case…');
        setNotice('');
        try {
            const { data } = await api.post('/api/web-search', { query: searchQuery.trim(), saveToCase: saveSearchToCase, speed: workMode });
            setLiveSearchResult(data);
            if (data.savedDocument) await load();
        } catch (err) {
            setNotice(errorMessage(err, 'Live Web Search failed.'));
        } finally { setBusy(''); }
    };

    const runWebResearch = async () => {
        if (!plugins['Web Research']) {
            setNotice('Web Research is disabled in Plugins.');
            return;
        }
        if (!webUrl.trim()) {
            setNotice('Paste a public web URL first.');
            return;
        }
        setBusy('Reading the web source and comparing it with the case…');
        setNotice('');
        try {
            const { data } = await api.post('/api/web-research', { url: webUrl.trim(), question: webQuestion.trim(), saveToCase: saveWebToCase, speed: workMode });
            setWebResult(data);
            if (data.savedDocument) await load();
        } catch (err) {
            setNotice(errorMessage(err, 'Web Research could not read that page.'));
        } finally { setBusy(''); }
    };

    const analyze = async () => {
        setBusy(`Running ${workMode.toLowerCase()} case review…`);
        setNotice('');
        try {
            const { data } = await api.post('/api/review', { speed: workMode });
            setReview(data.review);
        } catch (err) {
            setNotice(errorMessage(err, 'Case Review failed.'));
        } finally { setBusy(''); }
    };

    const generatePacket = async () => {
        setBusy(`Drafting packet in ${workMode.toLowerCase()} mode…`);
        setNotice('');
        try {
            const { data } = await api.post('/api/packet', { style: packetStyle, speed: workMode });
            setPacket(data.packet);
        } catch (err) {
            setNotice(errorMessage(err, 'Packet generation failed.'));
        } finally { setBusy(''); }
    };

    const removeDoc = async (id: string) => {
        if (!confirm('Delete this document from your Elias workspace?')) return;
        try {
            await api.delete(`/api/documents/${id}`);
            setSubmissionBrief(null);
            setPacket(null);
            await load();
        } catch (err) {
            setNotice(errorMessage(err, 'Document could not be deleted.'));
        }
    };

    const togglePlugin = (name: PluginName) => {
        setPlugins((current) => ({ ...current, [name]: !current[name] }));
        if (name === tool && plugins[name]) setTool('Record Search');
    };

    const enabledChatTools = pluginCatalog.filter((plugin) => plugin.chatTool && plugins[plugin.name]);
    const activeMessages = useMemo(() => chats.filter((message) => message.threadId === threadId), [chats, threadId]);
    const oldThreads = useMemo(() => Array.from(new Set(chats.map((message) => message.threadId))).slice(-8).reverse(), [chats]);
    const filteredDocuments = useMemo(() => {
        const query = vaultQuery.trim().toLowerCase();
        if (!query) return documents;
        return documents.filter((document) => `${document.name} ${document.excerpt} ${categorizeDocument(document)}`.toLowerCase().includes(query));
    }, [documents, vaultQuery]);
    const categoryCounts = useMemo(() => evidenceCategories.map((category) => ({
        category,
        count: documents.filter((document) => categorizeDocument(document) === category).length,
    })), [documents]);
    const inventoryById = useMemo(() => new Map((evidenceInventory?.items ?? []).map((item) => [item.id, item])), [evidenceInventory]);

    if (!user) {
        return <main className='login-wrap'><section className='login-card'><div className='brand-mark'><Bot size={32} /></div><p className='eyebrow'>Elias + Evidence Auditor</p><h1>One evidence intelligence workspace.</h1><p>Elias orchestrates the case. Evidence Auditor is the flagship audit workspace. NeuroEval, HealthQA, Packet Builder, Citation Auditor, and Document Copilot share the same private evidence cloud instead of creating separate silos.</p><button className='primary large' onClick={signIn}><LogIn size={18} /> Sign in to Elias</button><p className='fine'>Human verification remains required. Record facts, reported history, opinion, agency findings, and AI synthesis remain distinct.</p>{notice && <div className='notice'>{notice}</div>}</section></main>;
    }

    if (appMode === 'simple') {
        return <SimpleMode
            userLabel={user.name || user.email || 'Account'}
            documents={documents}
            uploadItems={uploadItems}
            busy={busy}
            notice={notice}
            benefitsProgram={benefitsProgram}
            lawIssue={lawIssue}
            issueOptions={benefitsIssueOptions[benefitsProgram]}
            submissionReady={!!submissionBrief}
            submissionPreviewBlob={submissionPreviewBlob}
            submissionPreviewUrl={submissionPreviewUrl}
            submissionPreviewName={submissionPreviewName}
            uploadSuccessNotice={uploadSuccessNotice}
            vaultFileCount={vaultStatus?.fileCount ?? 0}
            driveNote={integrations.driveNote}
            onUpload={(files) => void upload(files)}
            onDismissUpload={(id) => setUploadItems((current) => current.filter((item) => item.id !== id))}
            onDismissUploadSuccess={() => setUploadSuccessNotice('')}
            onDeleteDocument={(id) => void removeDoc(id)}
            onSetProgram={(program) => {
                setBenefitsProgram(program);
                setLawIssue(benefitsIssueOptions[program][0]);
                setLawLens(null);
                setSubmissionBrief(null);
            }}
            onSetIssue={(issue) => {
                setLawIssue(issue);
                setLawLens(null);
                setSubmissionBrief(null);
            }}
            onGenerate={() => void createSubmissionBrief()}
            onDownload={downloadSubmissionBrief}
            onSaveVault={() => void saveSubmissionToVault()}
            onOpenPro={() => setAppMode('pro')}
            onSignOut={() => void signOut()}
        />;
    }

    return <div className='shell'>
        <aside className='sidebar nonprint'>
            <div className='brand'><div className='brand-mark small'><Bot size={22} /></div><div><strong>Elias</strong><span>Evidence Intelligence</span></div></div>
            <div className='playbook-badge'><Brain size={14} /><span>{playbook}</span></div>
            <button className='new-chat' onClick={() => { setThreadId(crypto.randomUUID()); setView('chat'); }}><MessageSquarePlus size={17} /> New chat</button>
            <nav>
                <button className={view === 'chat' ? 'active' : ''} onClick={() => setView('chat')}><Bot size={17} /> Elias</button>
                <button className={view === 'cloud' ? 'active' : ''} onClick={() => setView('cloud')}><Cloud size={17} /> Evidence Cloud</button>
                <button className={view === 'review' ? 'active' : ''} onClick={() => setView('review')}><FileSearch size={17} /> Evidence Auditor</button>
                <button className={view === 'packet' ? 'active' : ''} onClick={() => setView('packet')}><WandSparkles size={17} /> Packet Studio</button>
            </nav>

            <details className='control-card' open>
                <summary><Gauge size={15} /> Work speed</summary>
                <div className='speed-grid'>{(['Quick', 'Standard', 'Deep'] as WorkMode[]).map((mode) => <button key={mode} className={workMode === mode ? 'selected' : ''} onClick={() => setWorkMode(mode)}>{mode}</button>)}</div>
                <p>{workMode === 'Quick' ? 'Fastest. Best for simple record lookups.' : workMode === 'Deep' ? 'More reasoning for contradictions, chronology, and packet work.' : 'Balanced speed and depth for most case questions.'}</p>
            </details>

            <details className='control-card'>
                <summary><PlugZap size={15} /> Plugins</summary>
                <div className='plugin-list'>{pluginCatalog.map((plugin) => <label key={plugin.name}><input type='checkbox' checked={plugins[plugin.name]} onChange={() => togglePlugin(plugin.name)} /><span><strong>{plugin.name}</strong><small>{plugin.blurb}</small></span></label>)}</div>
            </details>

            <details className='control-card voice-studio'>
                <summary><Mic2 size={15} /> Voice Studio</summary>
                <div className='voice-status'><span className={voiceEngine === 'Neural' && integrations.neuralVoice ? 'voice-dot connected' : 'voice-dot'} /><div><strong>{voiceEngine === 'Neural' ? 'Neural voice' : 'Device voice'}</strong><small>{voiceEngine === 'Neural' ? (integrations.neuralVoice ? 'Connected · higher fidelity' : 'Not connected') : 'Local browser / OS fallback'}</small></div></div>
                <div className='voice-engine-tabs'><button className={voiceEngine === 'Browser' ? 'selected' : ''} onClick={() => setVoiceEngine('Browser')}>Device</button><button className={voiceEngine === 'Neural' ? 'selected' : ''} disabled={!integrations.neuralVoice} onClick={() => setVoiceEngine('Neural')}>Neural</button></div>
                <span className='mini-label'>Delivery style</span><div className='voice-preset-grid'>{['Natural', 'Younger Distinguished', 'Command Briefing', 'Calm Clinical'].map((preset) => <button key={preset} className={voicePreset === preset ? 'selected' : ''} onClick={() => setVoicePreset(preset)}>{preset}</button>)}</div>
                {voiceEngine === 'Neural' ? <label className='field-label'>Voice<select value={neuralVoiceId} onChange={(e) => setNeuralVoiceId(e.target.value)}>{neuralVoices.map((voice) => <option key={voice.voiceId} value={voice.voiceId}>{voice.name}</option>)}</select></label> : <label className='field-label'>Voice<select value={voiceName} onChange={(e) => setVoiceName(e.target.value)}><option value='Auto'>Best available</option>{voices.filter((voice) => /^en/i.test(voice.lang)).map((voice) => <option key={`${voice.name}-${voice.lang}`}>{voice.name} · {voice.lang}</option>)}</select></label>}
                <label className='auto-speak voice-auto'><input type='checkbox' checked={autoSpeak} onChange={(e) => setAutoSpeak(e.target.checked)} /><span><strong>Auto-read replies</strong><small>Speak new Elias answers automatically</small></span></label>
                <div className='voice-actions'><button className='secondary tiny' onClick={() => speak('Elias voice preview. Source grounded, measured, and clear.')}><Play size={14} /> Preview voice</button><button className='secondary tiny' onClick={stopSpeaking}><Square size={12} /> Stop</button></div>
            </details>

            <div className='thread-list'><span>Recent chats</span>{oldThreads.map((id, index) => <button key={id} onClick={() => { setThreadId(id); setView('chat'); }}>Chat {oldThreads.length - index}</button>)}</div>
            <div className='memory-card'>
                <div className='memory-title'><MemoryStick size={16} /><strong>Case memory</strong><label><input type='checkbox' checked={memory.enabled} onChange={(e) => setMemory({ ...memory, enabled: e.target.checked })} /> On</label></div>
                <input placeholder='Case label' value={memory.caseLabel} onChange={(e) => setMemory({ ...memory, caseLabel: e.target.value })} />
                <textarea placeholder='Main goal' value={memory.goal} onChange={(e) => setMemory({ ...memory, goal: e.target.value })} />
                <textarea placeholder='Important notes / instructions' value={memory.notes} onChange={(e) => setMemory({ ...memory, notes: e.target.value })} />
                <button className='secondary' onClick={saveMemory}>Save memory</button>
            </div>
            <button className='account' onClick={signOut}><LogOut size={16} /> {user.name || user.email || 'Sign out'}</button>
        </aside>

        <main className='main'>
            <header className='topbar nonprint'><div><PanelLeft size={17} /><span>{view === 'chat' ? 'Elias' : view === 'cloud' ? 'Evidence Cloud' : view === 'review' ? 'Evidence Auditor' : 'Packet Studio'}</span></div><div className='top-controls'><span className={`speed-pill ${workMode.toLowerCase()}`}><Gauge size={14} /> {workMode}</span><div className='privacy'><ShieldCheck size={16} /> Private workspace</div><div className='elias-mode-switch pro-top-mode-switch'><button onClick={() => setAppMode('simple')}>Simple</button><button className='active'>Pro</button></div></div></header>
            {uploadSuccessNotice && <div className='upload-success-toast nonprint' role='status' aria-live='polite'><CircleCheck size={21} /><div><strong>Upload complete</strong><span>{uploadSuccessNotice}</span></div><button aria-label='Dismiss upload complete message' onClick={() => setUploadSuccessNotice('')}><X size={16} /></button></div>}
            {notice && <div className='notice nonprint'>{notice}</div>}
            {busy && <><div className='busy nonprint'><Sparkles size={15} /> {busy}</div><div className='working-overlay nonprint' role='status' aria-live='polite'><div className='working-card'><div className='working-orbit'><Sparkles size={22} /></div><div><span>ELIAS IS WORKING</span><strong>{busy}</strong><p>Source controls are temporarily locked so repeated clicks do not start duplicate analysis jobs.</p><div className='working-track'><i /></div></div></div></div></>}

            {view === 'chat' && <section className='chat-page'>
                <div className='chat-column'>
                    {activeMessages.length === 0 && <div className='welcome'><div className='brand-mark'><Bot size={30} /></div><h1>Upload the record once. Elias and Evidence Auditor share it.</h1><p>Add medical records, administrative decisions, forms, emails, service records, screenshots, or other evidence. Elias organizes the case, Evidence Auditor checks support and provenance, and every specialist works from the same private Evidence Cloud.</p><button className='upload-hero' onClick={() => fileRef.current?.click()}><Paperclip size={18} /> Add case files</button><span className='upload-hint'>Multiple files · searchable PDFs up to 250 MB indexed by page range · TXT/MD/EML/MBOX up to 24 MB · JPG/PNG/WebP with OCR</span><div className='case-flow'><div><b>1</b><span><strong>Upload evidence</strong><small>Medical, administrative, service, benefits, email, and image records.</small></span></div><div><b>2</b><span><strong>Elias audits the record</strong><small>Strengths, weaknesses, contradictions, chronology, function, and missing information.</small></span></div><div><b>3</b><span><strong>Get the full package</strong><small>Visual report, recommended next steps, official-rule crosswalk, sources, and PDF output.</small></span></div><button className='primary one-click-create' disabled={!documents.length || !!busy || copilotBusy} onClick={() => void oneClickPacket()}><WandSparkles size={16} /> Build Full Case Package</button><small className='web-ready'><Globe2 size={12} /> Official web references are checked during the benefits crosswalk. Broader live search: {integrations.webSearch ? 'connected' : 'optional / not connected'}.</small></div><div className='quick-evidence-grid'>{quickEliasActions.map((action) => <button key={action.label} disabled={copilotBusy || !!busy} onClick={() => void runCopilot(action.prompt, action.tool)}><Sparkles size={14} /><span><strong>{action.label}</strong><small>One-click source-grounded pass</small></span></button>)}</div></div>}
                    <div className='messages'>{activeMessages.map((message, index) => <div key={`${message.createdAt}-${index}`} className='turn'><div className='user-msg'>{message.question}</div><div className='assistant-msg'><div className='avatar'><Bot size={18} /></div><div><FormattedText text={message.answer} /><div className='chips'><span>{message.tool}</span><span>{message.speed || 'Standard'}</span>{message.sources.map((source) => <span key={source}>{source}</span>)}<button onClick={() => speak(message.answer)} title='Read Elias response aloud'><Play size={12} /> Speak</button></div></div></div></div>)}</div>
                    <div className='composer nonprint'>
                        {uploadItems.length > 0 && <div className='upload-tray' aria-live='polite'>{uploadItems.map((item) => <div className={`upload-card ${item.stage.toLowerCase()}`} key={item.id}><div className={`upload-file-icon ${item.kind}`}>{item.kind === 'pdf' ? <FileText size={20} /> : item.kind === 'image' ? <FileImage size={20} /> : <Paperclip size={19} />}</div><div className='upload-file-meta'><strong title={item.name}>{item.name}</strong><span>{formatFileSize(item.size)} · {item.error || item.detail}</span>{item.stage !== 'Ready' && item.stage !== 'Error' && <div className='upload-progress' role='progressbar' aria-label={`${item.name} upload progress`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={item.progress}><i style={{ width: `${item.progress}%` }} /></div>}</div><div className={`upload-state ${item.stage.toLowerCase()}`}>{item.stage === 'Ready' ? <CircleCheck size={15} /> : item.stage === 'Error' ? <CircleAlert size={15} /> : <LoaderCircle className='spin' size={15} />}<span>{item.stage === 'Ready' || item.stage === 'Error' ? item.stage : `${item.progress}%`}</span></div>{(item.stage === 'Ready' || item.stage === 'Error') && <button className='upload-dismiss' aria-label={`Hide ${item.name} upload card`} title='Hide upload card' onClick={() => setUploadItems((current) => current.filter((upload) => upload.id !== item.id))}><X size={14} /></button>}</div>)}</div>}
                        <div className='tool-row'>{enabledChatTools.map((plugin) => <button key={plugin.name} className={tool === plugin.name ? 'selected' : ''} onClick={() => setTool(plugin.name)}>{plugin.name}</button>)}</div>
                        {mediaFiles.length > 0 && <div className='chips'>{mediaFiles.map((file) => <button key={`${file.name}-${file.size}`} onClick={() => setMediaFiles((current) => current.filter((item) => item !== file))}>{file.type.startsWith('video/') ? <Video size={12} /> : file.type.startsWith('audio/') ? <Headphones size={12} /> : <ImagePlus size={12} />} {file.name} ×</button>)}</div>}
                        {selectedVideo && videoPreviewUrl && <section className='motion-lab'><div className='motion-lab-head'><div><span className='mini-label'>Video + Motion Imaging</span><strong>{selectedVideo.name}</strong><small>Local review player · sampled-frame AI analysis</small></div><span className='motion-safe'>2D source · spatial interpretation, not calibrated 3D</span></div><video ref={videoRef} src={videoPreviewUrl} controls playsInline preload='metadata' /><div className='video-controls'><button onClick={() => stepVideo(-1)}>−1 frame</button><button onClick={() => stepVideo(1)}>+1 frame</button><div className='rate-buttons'>{[0.25, 0.5, 1, 1.5, 2].map((rate) => <button key={rate} className={videoRate === rate ? 'selected' : ''} onClick={() => setVideoRate(rate)}>{rate}×</button>)}</div><button className='motion-study-btn' disabled={!!busy || copilotBusy} onClick={() => void runMotionStudy()}><Sparkles size={13} /> Motion study</button></div><div className='motion-grid'><div><strong>Frame review</strong><span>Step one frame at a time around a key movement.</span></div><div><strong>Spatial planes</strong><span>Elias can discuss visible sagittal/coronal/axial direction when supportable.</span></div><div><strong>Uncertainty guard</strong><span>Single-camera depth and off-frame motion stay labeled as uncertain.</span></div></div></section>}
                        <textarea value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void send(); } }} placeholder={mediaFiles.length ? 'Ask Elias about the attached media…' : 'Message Elias…'} />
                        <div className='composer-actions'><input ref={fileRef} className='hidden' multiple type='file' accept='.pdf,.txt,.md,.eml,.mbox,.png,.jpg,.jpeg,.webp,application/pdf,text/plain,text/markdown,message/rfc822,application/mbox,image/png,image/jpeg,image/webp' onChange={(e) => void upload(e.target.files)} /><input ref={mediaRef} className='hidden' multiple type='file' accept='image/*,video/*,audio/*' onChange={(e) => { setMediaFiles(Array.from(e.target.files ?? []).slice(0, 5)); e.target.value = ''; }} /><button className='attach-btn' onClick={() => fileRef.current?.click()} title='Upload case files'><Paperclip size={17} /> Add files</button><button className='attach-btn' onClick={() => mediaRef.current?.click()} title='Attach image, audio, or video for direct analysis'><ImagePlus size={17} /> Media</button><span>{documents.length} source{documents.length === 1 ? '' : 's'} loaded</span><button className='send-btn' onClick={() => void send()} disabled={(!question.trim() && !mediaFiles.length) || !!busy}><Send size={18} /></button></div>
                    </div>
                </div>
            </section>}

            {view === 'cloud' && <section className='workspace'>
                <input ref={fileRef} className='hidden' multiple type='file' accept='.pdf,.txt,.md,.eml,.mbox,.png,.jpg,.jpeg,.webp,application/pdf,text/plain,text/markdown,message/rfc822,application/mbox,image/png,image/jpeg,image/webp' onChange={(e) => void upload(e.target.files)} />
                <div className='page-head'><div><p className='eyebrow'>Patient evidence cloud</p><h1>Evidence Cloud</h1><p>The shared source layer for Elias, Evidence Auditor, NeuroEval, HealthQA, and Packet Studio. Upload once, organize privately, then reuse the same case evidence across every workflow.</p></div><div className='packet-head-actions'><button className='primary' onClick={() => fileRef.current?.click()}><Paperclip size={17} /> Add evidence</button><button className='secondary' disabled={!!busy} onClick={() => void organizeVault()}><FolderOpen size={16} /> Organize / Refresh</button><button className='secondary' disabled={!!busy} onClick={() => void exportVault()}><Archive size={16} /> Export ZIP</button></div></div>
                <div className='metrics'><div><span>Indexed sources</span><strong>{documents.length}</strong></div><div><span>Private vault files</span><strong>{vaultStatus?.fileCount ?? 0}</strong></div><div><span>Likely duplicates</span><strong>{evidenceInventory?.duplicateGroups.length ?? 0}</strong></div></div>
                <section className='vault-panel'><div className='vault-head'><div><span className='result-kicker'>SHARED CASE STORAGE</span><h2>Private Evidence Cloud</h2><p>The existing Case Vault is now the shared evidence layer. Stored originals are organized into case folders when available; large locally indexed PDFs can remain indexed-only and are labeled that way rather than being represented as preserved originals.</p></div><Cloud size={26} /></div>{vaultStatus && <div className='vault-folders'>{vaultStatus.folders.map((folder) => <div key={folder.name}><FolderOpen size={14} /><span><strong>{folder.name}</strong><small>{folder.count} file{folder.count === 1 ? '' : 's'}</small></span></div>)}</div>}<small className='vault-note'>{integrations.driveNote}</small></section>
                <div className='connector-note'><ShieldCheck size={17} /><div><strong>Original-source control</strong><span>Generated summaries, labels, interpretations, diagrams, and filing prose must stay distinguishable from the underlying record. Human verification remains required.</span></div></div>
                <article className='research-panel'><div className='research-title'><Search size={18} /><div><strong>Search the Evidence Cloud</strong><span>Filename, excerpt, or automatic evidence category</span></div></div><input value={vaultQuery} onChange={(e) => setVaultQuery(e.target.value)} placeholder='Try: FCE, MRI, Guard orders, VA decision, correspondence…' /></article>
                <div className='research-grid'>{categoryCounts.map((item) => <article key={item.category} className='research-panel'><div className='research-title'><FolderOpen size={17} /><div><strong>{item.category}</strong><span>{item.count} source{item.count === 1 ? '' : 's'}</span></div></div><button className='secondary tiny' onClick={() => setVaultQuery(item.category)} disabled={!item.count}>Filter</button></article>)}</div>
                <div className='connector-note'><Brain size={17} /><div><strong>Evidence trace standard</strong><span>Source → page / locator → extracted evidence → evidence classification → interpretation → generated statement. Evidence Auditor and Citation Auditor should flag broken or ambiguous links.</span></div></div>
                {evidenceInventory && <div className='review-grid'>
                    <article><h3>Possible duplicates</h3>{evidenceInventory.duplicateGroups.length ? <ul>{evidenceInventory.duplicateGroups.map((group) => <li key={group.fingerprint}><strong>{group.names.join(' · ')}</strong><br /><small>{group.note}</small></li>)}</ul> : <p>No likely duplicate groups detected by the current fingerprint check.</p>}</article>
                    <article><h3>Possible versions</h3>{evidenceInventory.versionGroups.length ? <ul>{evidenceInventory.versionGroups.map((group) => <li key={group.versionGroup}><strong>{group.names.join(' · ')}</strong><br /><small>{group.note}</small></li>)}</ul> : <p>No filename-based version groups detected.</p>}</article>
                </div>}
                {evidenceInventory && <div className='connector-note'><CircleAlert size={17} /><div><strong>Smart metadata is advisory</strong><span>{evidenceInventory.warning}</span></div></div>}
                <h2 className='section-title'>Cloud source inventory</h2><div className='doc-list'>{filteredDocuments.map((document) => { const meta = inventoryById.get(document.id); return <article key={document.id} className='doc-card'><div>{document.sourceMode === 'ocr' ? <FileImage size={19} /> : document.sourceMode === 'email' ? <Mail size={19} /> : ['web', 'search'].includes(document.sourceMode || '') ? <Globe2 size={19} /> : document.sourceMode === 'media' ? <ImagePlus size={19} /> : <FolderOpen size={19} />}<div><strong>{document.name}</strong><span>{meta?.documentType || categorizeDocument(document)} · {meta?.locator || `${document.pageCount} indexed page${document.pageCount === 1 ? '' : 's'}`} · {Math.round(document.charCount / 1000)}k characters</span>{document.sourceUrl && <a className='source-link' href={document.sourceUrl} target='_blank' rel='noreferrer'>{document.sourceUrl}</a>}</div></div><p>{document.excerpt}</p><div className='chips'><span>{meta?.category || categorizeDocument(document)}</span><span>{meta?.storageStatus || document.sourceMode || 'indexed'}</span>{meta?.candidateDates?.slice(0, 2).map((date) => <span key={`${document.id}-${date}`}>{date}</span>)}{meta && <span>HEURISTIC METADATA</span>}</div><button onClick={() => void removeDoc(document.id)}><Trash2 size={15} /> Delete</button></article>; })}</div>
                {!filteredDocuments.length && <div className='empty-panel'>No loaded source matches this filter.</div>}
            </section>}

            {view === 'review' && <section className='workspace'>
                <div className='page-head'><div><p className='eyebrow'>Flagship audit workspace</p><h1>Evidence Auditor</h1><p>Prove it, source it, package it. Audit support, contradictions, gaps, chronology, provenance, functional reliability, and reviewer-readiness against the same Evidence Cloud Elias uses.</p></div><button className='primary' onClick={() => void analyze()}><FileSearch size={17} /> Run evidence audit · {workMode}</button></div>
                <div className='metrics'><div><span>Documents</span><strong>{documents.length}</strong></div><div><span>Indexed pages</span><strong>{documents.reduce((sum, document) => sum + (document.pageCount || 1), 0)}</strong></div><div><span>OCR / email / web</span><strong>{documents.filter((document) => ['ocr', 'email', 'web'].includes(document.sourceMode || '')).length}</strong></div></div>
                <div className='command-deck nonprint'><div><span className='command-kicker'>EVIDENCE AUDITOR</span><strong>Fast source-grounded audit passes without leaving the flagship workspace</strong></div><div>{quickEliasActions.slice(0, 6).map((action) => <button key={action.label} disabled={copilotBusy || !!busy} onClick={() => void runCopilot(action.prompt, action.tool)}>{action.label}</button>)}</div></div>
                <div className='research-grid nonprint'>
                    <article className='research-panel'>
                        <div className='research-title'><Scale size={18} /><div><strong>Benefits Law & Medical Lens</strong><span>VA/VBA · SSA SSDI/SSI · New Hampshire · medical-function evidence</span></div></div>
                        <small>Program / jurisdiction</small>
                        <select aria-label='Benefits program' value={benefitsProgram} onChange={(e) => { const next = e.target.value as BenefitsProgram; setBenefitsProgram(next); setLawIssue(benefitsIssueOptions[next][0]); setLawLens(null); }}><option>VA / VBA</option><option>Social Security (SSDI / SSI)</option><option>New Hampshire</option><option>Medical & Functional Evidence</option></select>
                        <small>Issue / framework</small>
                        <select aria-label='Benefits issue' value={lawIssue} onChange={(e) => { setLawIssue(e.target.value); setLawLens(null); }}>{benefitsIssueOptions[benefitsProgram].map((issue) => <option key={issue}>{issue}</option>)}</select>
                        <button className='primary' onClick={() => void runLawLens()}>Compare rules to evidence</button>
                        <small>Elias keeps 38 CFR and 20 CFR regulations separate from VBA manuals, SSA POMS/Blue Book material, and state guidance. The crosswalk is evidence analysis—not an eligibility, rating, allowance, or denial prediction.</small>
                    </article>
                    <article className='research-panel'>
                        <div className='research-title'><Globe2 size={18} /><div><strong>YouTube / URL Research</strong><span>Read a public page; YouTube uses public page/transcript text when exposed</span></div></div>
                        <input value={webUrl} onChange={(e) => setWebUrl(e.target.value)} placeholder='https://www.ecfr.gov/…' />
                        <textarea value={webQuestion} onChange={(e) => setWebQuestion(e.target.value)} placeholder='What should Elias look for on this page?' />
                        <label className='save-check'><input type='checkbox' checked={saveWebToCase} onChange={(e) => setSaveWebToCase(e.target.checked)} /> Save this web page as a case source</label>
                        <button className='secondary' onClick={() => void runWebResearch()}>Research URL</button>
                    </article>
                    <article className='research-panel'>
                        <div className='research-title'><Search size={18} /><div><strong>Live Web Search</strong><span>{integrations.webSearch ? 'Connected' : 'Needs Tavily API connection'}</span></div></div>
                        <input value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder='Search current web evidence, VBA guidance, medical literature…' />
                        <label className='save-check'><input type='checkbox' checked={saveSearchToCase} onChange={(e) => setSaveSearchToCase(e.target.checked)} /> Save search findings as a case reference</label>
                        <button className='secondary' onClick={() => void runWebSearch()} disabled={!integrations.webSearch}>Search web</button>
                    </article>
                </div>
                {lawLens && <div className='lens-suite'><article className='lens-hero'><div><span className='result-kicker'>BENEFITS LAW + MEDICAL EVIDENCE CROSSWALK</span><h2>{lawLens.program ? `${lawLens.program} · ` : ''}{lawLens.issue}</h2>{lawLens.jurisdiction && <span className='kind-pill'>{lawLens.jurisdiction}</span>}<FormattedText text={lawLens.summary} /></div><div className='authority-stack'>{lawLens.officialSources.map((source) => <a key={source.url} href={source.url} target='_blank' rel='noreferrer'><Scale size={13} /><span>{source.label}</span><small>{source.kind}</small><ExternalLink size={11} /></a>)}</div></article><div className='lens-grid'>{lawLens.framework && <VisualListCard title='Governing framework' items={lawLens.framework} tone='focus' />}<VisualListCard title='Reviewer focus' items={lawLens.whatRaterLooksFor} tone='focus' /><VisualListCard title='Record matches' items={lawLens.evidenceMatches} tone='positive' /><VisualListCard title='Missing / weak support' items={lawLens.gaps} tone='warning' /><VisualListCard title='Conflicts to reconcile' items={lawLens.conflicts} tone='conflict' /><VisualListCard title='Highest-value next evidence' items={lawLens.nextBestEvidence} tone='action' /></div></div>}
                {webResult && <article className='web-result'><div className='research-title'><Globe2 size={18} /><div><strong>{webResult.title}</strong><a href={webResult.url} target='_blank' rel='noreferrer'>{webResult.url}</a></div></div><p>{webResult.answer}</p></article>}
                {liveSearchResult && <article className='web-result'><div className='research-title'><Search size={18} /><div><strong>Live Web Search</strong><span>{liveSearchResult.results.length} source{liveSearchResult.results.length === 1 ? '' : 's'} returned</span></div></div><p>{liveSearchResult.answer}</p><div className='official-links'>{liveSearchResult.results.map((result) => <a key={result.url} href={result.url} target='_blank' rel='noreferrer'><ExternalLink size={12} /> {result.title}</a>)}</div></article>}
                <div className='connector-note nonprint'><PlugZap size={17} /><div><strong>Connected capabilities</strong><span>Live web search: {integrations.webSearch ? 'connected' : 'not connected'} · Neural voice: {integrations.neuralVoice ? 'connected' : 'not connected'} · Gmail direct OAuth: {integrations.gmailDirect ? 'connected' : 'not connected'}. {integrations.gmailNote}</span></div></div>
                <div className='connector-note nonprint'><Mail size={17} /><div><strong>Email Evidence</strong><span>Upload .eml or .mbox files with Add files and Elias will index them as email evidence. Direct Gmail/Outlook mailbox OAuth is not represented as connected unless a secure per-user connector exists.</span></div></div>
                {review ? <CaseReviewResult review={review} /> : <div className='empty-panel'>Run Analyze record after uploading case documents. Elias will separate supporting evidence, gaps, chronology, and tensions without making a merits decision.</div>}
                <h2 className='section-title'>Source inventory</h2><div className='doc-list'>{documents.map((document) => <article key={document.id} className='doc-card'><div>{document.sourceMode === 'ocr' ? <FileImage size={19} /> : document.sourceMode === 'email' ? <Mail size={19} /> : ['web', 'search'].includes(document.sourceMode || '') ? <Globe2 size={19} /> : document.sourceMode === 'media' ? <ImagePlus size={19} /> : <FolderOpen size={19} />}<div><strong>{document.name}</strong><span>{document.pageCount} page{document.pageCount === 1 ? '' : 's'} · {Math.round(document.charCount / 1000)}k characters · {document.sourceMode === 'ocr' ? 'OCR' : document.sourceMode === 'email' ? 'email' : document.sourceMode === 'web' ? 'web reference' : document.sourceMode === 'search' ? 'web search reference' : document.sourceMode === 'media' ? 'media analysis' : document.sourceMode || 'indexed'}</span>{document.sourceUrl && <a className='source-link' href={document.sourceUrl} target='_blank' rel='noreferrer'>{document.sourceUrl}</a>}</div></div><p>{document.excerpt}</p><button onClick={() => void removeDoc(document.id)}><Trash2 size={15} /> Delete</button></article>)}</div>
            </section>}

            {view === 'packet' && <section className='workspace'>
                <div className='page-head nonprint'><div><p className='eyebrow'>Upload → audit → package</p><h1>Packet Studio</h1><p>One click can audit the loaded evidence, compare the selected benefits framework with live official sources, and build a visual PDF-ready case package.</p></div><div className='packet-head-actions'><button className='secondary' disabled={copilotBusy || !!busy} onClick={() => void runCopilot(quickEliasActions[5].prompt, 'Packet Assurance')}><ShieldCheck size={17} /> Preflight</button><button className='primary one-click-create' disabled={!!busy || copilotBusy || !documents.length} onClick={() => void oneClickPacket()}><Sparkles size={17} /> Build Full Case Package</button><button className='primary' onClick={() => void generatePacket()}><WandSparkles size={17} /> Packet only · {workMode}</button></div></div>
                <div className='package-focus nonprint'><div><strong>Package focus</strong><small>Choose the program Elias should cross-check against the record.</small></div><label>Program<select value={benefitsProgram} onChange={(e) => { const next = e.target.value as BenefitsProgram; setBenefitsProgram(next); setLawIssue(benefitsIssueOptions[next][0]); setLawLens(null); }}><option>VA / VBA</option><option>Social Security (SSDI / SSI)</option><option>New Hampshire</option><option>Medical & Functional Evidence</option></select></label><label>Issue<select value={lawIssue} onChange={(e) => { setLawIssue(e.target.value); setLawLens(null); }}>{benefitsIssueOptions[benefitsProgram].map((issue) => <option key={issue}>{issue}</option>)}</select></label><span className='web-ready'><Globe2 size={12} /> Official-source web crosswalk included · broader live search {integrations.webSearch ? 'connected' : 'optional'}</span></div>
                <section className='submission-panel nonprint'><div><span className='result-kicker'>AGENCY FILING OUTPUT</span><h2>Submission Advocacy PDF</h2><p>A separate claimant-side filing brief modeled on an evidence-convergence/rebuttal packet. It includes only supportable favorable evidence and advocacy arguments—no standalone weaknesses section—while preserving source accuracy and necessary limiting context.</p></div><div className='submission-actions'><button className='primary' disabled={!documents.length || !!busy} onClick={() => void createSubmissionBrief()}><FileText size={16} /> Create Submission Brief</button><button className='secondary' disabled={!submissionBrief || !!busy} onClick={downloadSubmissionBrief}><Download size={16} /> Download PDF</button><button className='secondary' disabled={!submissionBrief || !!busy} onClick={() => void saveSubmissionToVault()}><Cloud size={16} /> Save PDF to Vault</button></div></section>
                <section className='vault-panel nonprint'><div className='vault-head'><div><span className='result-kicker'>PRIVATE EVIDENCE CLOUD</span><h2>Evidence Cloud / Case Vault</h2><p>The same private foldered source library is shared across Elias, Evidence Auditor, and packet workflows. Export a Drive-ready ZIP when you want an external copy.</p></div><Cloud size={26} /></div><div className='vault-actions'><button className='secondary' disabled={!!busy} onClick={() => void organizeVault()}><FolderOpen size={16} /> Organize / Refresh Vault</button><button className='secondary' disabled={!!busy} onClick={() => void exportVault()}><Archive size={16} /> Export Drive-ready ZIP</button><a className='secondary vault-link' href='https://drive.google.com/drive/my-drive' target='_blank' rel='noreferrer'><ExternalLink size={15} /> Open Google Drive</a></div>{vaultStatus && <div className='vault-folders'>{vaultStatus.folders.map((folder) => <div key={folder.name}><FolderOpen size={14} /><span><strong>{folder.name}</strong><small>{folder.count} file{folder.count === 1 ? '' : 's'}</small></span></div>)}</div>}<small className='vault-note'>{integrations.driveNote}</small></section>
                <div className='packet-controls nonprint'><label><input type='radio' checked={packetStyle === 'Visual evidence review'} onChange={() => setPacketStyle('Visual evidence review')} /> Internal visual audit</label><label><input type='radio' checked={packetStyle === 'Formal evidence review'} onChange={() => setPacketStyle('Formal evidence review')} /> Internal formal audit</label>{packet && <button className='secondary' onClick={() => window.print()}><Printer size={16} /> Print Internal Audit</button>}</div><div className='connector-note nonprint'><Gauge size={17} /><div><strong>Under-5-MB export target</strong><span>PDF generation exists now. Automated source-page selection, screenshot cropping/stamping, visual QA, and reliable final compression below 5 MB remain validation work and are not represented as guaranteed.</span></div></div>
                {submissionBrief && <SubmissionBriefPreview brief={submissionBrief} />}
                {packet ? <PacketPreview packet={packet} review={review} lawLens={lawLens} /> : <div className='empty-panel'>Add case records, choose a program focus, then click Build Full Case Package for the internal evidence audit or Create Submission Brief for the filing-facing advocacy document.</div>}
            </section>}
        </main>

        <button className={copilotOpen ? 'elias-fab open nonprint' : 'elias-fab nonprint'} onClick={() => setCopilotOpen(!copilotOpen)}><span><Bot size={19} /></span><div><strong>Elias Copilot</strong><small>{copilotOpen ? 'Close' : `${copilotRole} · app-aware`}</small></div></button>
        {copilotOpen && <aside className='elias-copilot nonprint'>
            <div className='copilot-head'><div><p className='eyebrow'>Unified floating copilot</p><h3>{copilotRole}</h3><span>{documents.length} indexed source{documents.length === 1 ? '' : 's'} · {workMode} mode · {copilotSpecialists.find((item) => item.name === copilotRole)?.blurb}</span></div><button onClick={() => setCopilotOpen(false)}><X size={18} /></button></div>
            <label className='field-label'>Specialist mode<select value={copilotRole} onChange={(e) => setCopilotRole(e.target.value as CopilotRole)}>{copilotSpecialists.map((specialist) => <option key={specialist.name} value={specialist.name}>{specialist.name}</option>)}</select></label>
            <div className='tool-row'>{copilotOperations.map((action) => <button key={action.label} disabled={copilotBusy || !!busy} onClick={() => { if (action.view) setView(action.view); void runCopilot(action.prompt, action.tool); }}>{action.label}</button>)}</div>
            <div className='copilot-actions'>{quickEliasActions.map((action) => <button key={action.label} disabled={copilotBusy || !!busy} onClick={() => void runCopilot(action.prompt, action.tool)}>{action.label}</button>)}</div>
            <div className='copilot-create'><span>Create in one click</span><div>{quickCreateActions.map((action) => <button key={action.label} disabled={copilotBusy || !!busy} onClick={() => void runCopilot(action.prompt, action.tool)}><WandSparkles size={12} /> {action.label}</button>)}<button disabled={copilotBusy || !!busy || !documents.length} onClick={() => void oneClickPacket()}><Sparkles size={12} /> Full Case Package</button></div></div>
            <div ref={copilotResultRef} className='copilot-result' aria-live='polite'>{copilotBusy ? <div className='copilot-thinking'><div className='thinking-dots'><i /><i /><i /></div><div><strong>Elias is thinking</strong><p>{copilotPhases[copilotPhase]}</p></div></div> : copilotAnswer ? <><div className='answer-head'><Bot size={16} /><strong>Latest Copilot answer</strong><span className='latest-pill'>LATEST</span></div><FormattedText text={copilotAnswer} /><button className='secondary tiny' onClick={() => speak(copilotAnswer)}><Play size={13} /> Speak</button><button className='secondary tiny' onClick={() => setView('chat')}><MessageSquarePlus size={13} /> Open in Elias</button></> : <div className='copilot-empty'><Brain size={22} /><p>Choose a specialist, run an app action, or ask a custom question. Every specialist uses the same Evidence Cloud and source-control rules instead of operating as a separate bot silo.</p></div>}</div>
            <div className='copilot-compose'><textarea value={copilotInput} onChange={(e) => setCopilotInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void runCopilot(copilotInput); setCopilotInput(''); } }} placeholder='Ask Elias about the loaded record…' /><button disabled={!copilotInput.trim() || copilotBusy || !!busy} onClick={() => { void runCopilot(copilotInput); setCopilotInput(''); }}><Send size={17} /></button></div>
        </aside>}
    </div>;
}

function InlineEvidenceText({ text }: { text: string }) {
    const parts = text.split(/(\[[^\]]+\])/g);
    return <>{parts.map((part, index) => /^\[[^\]]+\]$/.test(part) ? <span className='inline-source' key={`${part}-${index}`}>{part.slice(1, -1)}</span> : <span key={`text-${index}`}>{part.replace(/\*\*/g, '')}</span>)}</>;
}

function FormattedText({ text }: { text: string }) {
    const lines = text.split('\n');
    return <div className='formatted-output'>{lines.map((raw, index) => {
        const line = raw.trim();
        if (!line) return <div className='text-gap' key={`gap-${index}`} />;
        const heading = line.match(/^#{1,4}\s+(.*)$/);
        if (heading) return <h4 key={`heading-${index}`}><InlineEvidenceText text={heading[1]} /></h4>;
        const numbered = line.match(/^(\d+)[.)]\s+(.*)$/);
        if (numbered) return <div className='number-line' key={`number-${index}`}><span>{numbered[1]}</span><p><InlineEvidenceText text={numbered[2]} /></p></div>;
        const bullet = line.match(/^[-*•]\s+(.*)$/);
        if (bullet) return <div className='bullet-line' key={`bullet-${index}`}><i /><p><InlineEvidenceText text={bullet[1]} /></p></div>;
        return <p key={`line-${index}`}><InlineEvidenceText text={line} /></p>;
    })}</div>;
}

function VisualListCard({ title, items, tone }: { title: string; items: string[]; tone: string }) {
    return <article className={`visual-list-card ${tone}`}><div className='visual-list-title'><span>{String(items.length).padStart(2, '0')}</span><h3>{title}</h3></div>{items.length ? <div className='visual-list-items'>{items.map((item, index) => <div key={`${title}-${index}`}><b>{index + 1}</b><p><InlineEvidenceText text={item} /></p></div>)}</div> : <p className='empty-copy'>No source-grounded item was identified.</p>}</article>;
}

function EvidenceTimeline({ items, compact = false }: { items: TimelineItem[]; compact?: boolean }) {
    return <div className={compact ? 'evidence-timeline compact' : 'evidence-timeline'}>{items.map((item, index) => <div className='timeline-row' key={`${item.date}-${index}`}><div className='timeline-rail'><span>{index + 1}</span><i /></div><div className='timeline-card'><div className='timeline-date'>{item.date || 'Date not isolated'}</div><h4>{item.event}</h4><p>{item.significance}</p><div className='source-band'><FileText size={12} /><InlineEvidenceText text={item.source || 'Source not isolated'} /></div></div></div>)}</div>;
}

function CaseReviewResult({ review }: { review: Review }) {
    return <div className='result-suite'><article className='executive-card'><div><span className='result-kicker'>ELIAS EVIDENCE MAP</span><h2>{review.recordSignal || 'Record synthesis'}</h2><FormattedText text={review.summary} /></div><div className='result-stats'><div><strong>{review.strongestEvidence?.length || 0}</strong><span>high-value findings</span></div><div><strong>{review.tensions?.length || 0}</strong><span>reconciliation targets</span></div><div><strong>{review.gaps?.length || 0}</strong><span>evidence gaps</span></div></div></article>{review.timeline?.length > 0 && <section className='result-section'><div className='result-section-head'><span>01</span><div><p>Chronology</p><h3>What the record shows over time</h3></div></div><EvidenceTimeline items={review.timeline} /></section>}<section className='result-section'><div className='result-section-head'><span>02</span><div><p>Probative evidence</p><h3>Strongest documented support</h3></div></div><div className='finding-grid'>{(review.strongestEvidence || []).map((item, index) => <article className='finding-card' key={`${item.title}-${index}`}><div className='finding-top'><span className='kind-pill'>{item.kind || 'Evidence'}</span><b>#{index + 1}</b></div><h4>{item.title}</h4><p>{item.finding}</p><div className='why-box'><strong>Why it matters</strong><span>{item.whyItMatters}</span></div><div className='source-band'><FileText size={12} /><InlineEvidenceText text={item.source || 'Source not isolated'} /></div></article>)}</div></section><section className='result-section'><div className='result-section-head'><span>03</span><div><p>Reconciliation matrix</p><h3>Adverse evidence versus contrary record support</h3></div></div><div className='tension-stack'>{(review.tensions || []).map((item, index) => <article className='tension-card' key={`tension-${index}`}><div className='tension-side adverse'><span>ADVERSE / CONFLICT</span><p>{item.adverse}</p></div><div className='tension-arrow'>↔</div><div className='tension-side support'><span>RECORD SUPPORT</span><p>{item.supporting}</p><div className='source-band'><InlineEvidenceText text={item.source || 'Source not isolated'} /></div></div><div className='reconcile-band'><strong>Reconcile:</strong> {item.reconcile}</div></article>)}</div></section><section className='result-section two-column-results'><div><div className='result-section-head small'><span>04</span><div><p>Evidence development</p><h3>Priority gaps</h3></div></div><div className='gap-stack'>{(review.gaps || []).map((item, index) => <article className='gap-card' key={`gap-${index}`}><span className={`priority-pill ${item.priority.toLowerCase()}`}>{item.priority || 'Priority'}</span><h4>{item.gap}</h4><p>{item.whyItMatters}</p><div className='next-step'><strong>Next:</strong> {item.nextStep}</div></article>)}</div></div><div><div className='result-section-head small'><span>05</span><div><p>Reviewer map</p><h3>Issues requiring attention</h3></div></div><div className='issue-stack'>{(review.issues || []).map((item, index) => <article className='issue-card' key={`issue-${index}`}><div><h4>{item.issue}</h4><span className='status-pill'>{item.status}</span></div><p>{item.note}</p></article>)}</div></div></section></div>;
}

function SubmissionBriefPreview({ brief }: { brief: SubmissionBrief }) {
    return <article className='submission-preview'><header className='submission-cover'><div><span className='result-kicker'>ADVOCACY SUBMISSION BRIEF · {brief.preflight?.status || 'Draft'}</span><h1>{brief.title}</h1><p>{brief.subtitle}</p></div><ShieldCheck size={26} /></header>{brief.preflight && <section className='submission-request'><strong>Submission Preflight · {brief.preflight.status}</strong>{brief.preflight.blockers.map((item, index) => <p key={`blocker-${index}`}>Blocker: {item}</p>)}{brief.preflight.warnings.map((item, index) => <p key={`warning-${index}`}>Warning: {item}</p>)}{!brief.preflight.blockers.length && !brief.preflight.warnings.length && <p>No blocking preflight findings. Recheck source locators and current authorities before filing.</p>}</section>}<section className='submission-request'><strong>Requested Agency Action</strong><p>{brief.requestedAction}</p></section><section className='submission-block'><h2>Executive Argument</h2><FormattedText text={brief.executiveArgument} /></section><section className='submission-block'><h2>Evidence Convergence</h2><div className='convergence-table'><div className='convergence-head'><span>Evidence</span><span>What it establishes</span><span>Why it matters</span><span>Source</span></div>{(brief.evidenceConvergence || []).map((row, index) => <div className='convergence-row' key={`conv-${index}`}><strong>{row.evidence}</strong><span>{row.establishes}</span><span>{row.whyItMatters}</span><span className='inline-source'>{row.source}</span></div>)}</div></section>{(brief.chronology || []).length > 0 && <section className='submission-block'><h2>Chronology</h2>{brief.chronology?.map((item, index) => <p key={`chron-${index}`}><strong>{item.date}</strong> · {item.event} <span className='inline-source'>{item.source}</span> — {item.significance}</p>)}</section>}{(brief.objectiveFindings || []).length > 0 && <section className='submission-block'><h2>Objective Findings</h2>{brief.objectiveFindings?.map((item, index) => <p key={`objective-${index}`}>{index + 1}. {item}</p>)}</section>}<section className='submission-block'><h2>Record-Grounded Medical & Legal Arguments</h2><div className='submission-arguments'>{(brief.arguments || []).map((argument, index) => <article key={`arg-${index}`}><span className='argument-number'>{String(index + 1).padStart(2, '0')}</span><h3>{argument.heading}</h3><p className='argument-proposition'>{argument.proposition}</p><div className='argument-support'><strong>PRIMARY RECORD SUPPORT</strong><p>{argument.recordSupport}</p><small>{(argument.sourceCitations || []).join(' · ')}</small></div>{argument.medicalReasoning && <div className='argument-support'><strong>MEDICAL REASONING</strong><p>{argument.medicalReasoning}</p></div>}{argument.legalReasoning && <div className='argument-support'><strong>LEGAL / REGULATORY REASONING</strong><p>{argument.legalReasoning}</p><small>{(argument.authorityCitations || []).join(' · ')}</small></div>}</article>)}</div></section>{(brief.medicalLiterature || []).length > 0 && <section className='submission-block'><h2>Peer-Reviewed Medical Literature</h2><p className='submission-caution'>Contextual medical literature only; it does not replace claimant-specific evidence or a medical opinion.</p><div className='authority-list'>{brief.medicalLiterature.map((source, index) => <a href={source.url} target='_blank' rel='noreferrer' key={source.id || index}><span>{index + 1}</span><div><strong>{source.citation || source.title}</strong><small>{source.relevance}</small></div><ExternalLink size={13} /></a>)}</div></section>}<section className='submission-block'><h2>Legal & Program Authorities</h2><div className='authority-list'>{(brief.legalAuthorities || []).map((source, index) => <a href={source.url} target='_blank' rel='noreferrer' key={source.url}><span>{index + 1}</span><div><strong>{source.label}</strong><small>{source.kind}</small></div><ExternalLink size={13} /></a>)}</div></section>{(brief.focusedQuestions || []).length > 0 && <section className='submission-block'><h2>Focused Questions / Next Development</h2>{brief.focusedQuestions?.map((item, index) => <p key={`question-${index}`}>{index + 1}. {item}</p>)}</section>}<section className='submission-block'><h2>Cited Source Library / Appendix</h2><div className='source-index'>{(brief.sourceAppendix || []).map((source, index) => <div key={`${source.name}-${index}`}><b>{String(index + 1).padStart(2, '0')}</b><strong>{source.name}</strong><span>{source.locator}</span><small>{source.use}</small></div>)}</div></section><section className='submission-request final'><strong>Requested Disposition</strong><p>{brief.requestedDisposition}</p><small>{brief.verificationNote}</small></section></article>;
}

function PacketPreview({ packet, review, lawLens }: { packet: Packet; review: Review | null; lawLens: LawLens | null }) {
    const nextStepCount = (review?.gaps?.length || 0) + (lawLens?.nextBestEvidence?.length || 0);
    return <article className='packet-paper packet-visual'><header className='packet-cover'><div><span className='result-kicker'>ELIAS FULL CASE PACKAGE</span><h1>{packet.title}</h1><p>{packet.subtitle}</p></div><div className='packet-seal'><ShieldCheck size={24} /><span>Source-grounded draft</span></div></header>{review && <section className='package-overview'><div className='package-overview-head'><span className='result-kicker'>CASE AT A GLANCE</span><h2>Strengths, weaknesses, missing information & next steps</h2></div><div className='package-overview-grid'><div className='package-overview-card positive'><strong>{review.strongestEvidence?.length || 0}</strong><span>Strengths</span><small>High-value documented findings</small></div><div className='package-overview-card conflict'><strong>{review.tensions?.length || 0}</strong><span>Weaknesses / conflicts</span><small>Items that need reconciliation</small></div><div className='package-overview-card warning'><strong>{review.gaps?.length || 0}</strong><span>Missing information</span><small>Evidence-development gaps</small></div><div className='package-overview-card action'><strong>{nextStepCount}</strong><span>Recommended next steps</span><small>Record and framework-driven actions</small></div></div></section>}<section className='packet-executive'><span className='packet-section-number'>01</span><div><h2>Executive Summary</h2><FormattedText text={packet.executiveSummary} /></div></section>{lawLens && <section className='packet-section packet-law-crosswalk'><div className='packet-section-heading'><span>WEB</span><div><small>Official-source research</small><h2>{lawLens.program ? `${lawLens.program} · ` : ''}{lawLens.issue}</h2></div></div><FormattedText text={lawLens.summary} /><div className='packet-law-grid'><VisualListCard title='Governing framework' items={lawLens.framework || lawLens.whatRaterLooksFor} tone='focus' /><VisualListCard title='Record matches' items={lawLens.evidenceMatches} tone='positive' /><VisualListCard title='Missing / weak support' items={lawLens.gaps} tone='warning' /><VisualListCard title='Recommended next evidence' items={lawLens.nextBestEvidence} tone='action' /></div><div className='official-links'>{lawLens.officialSources.map((source) => <a key={source.url} href={source.url} target='_blank' rel='noreferrer'><ExternalLink size={12} /> {source.label} <small>{source.kind}</small></a>)}</div></section>}{packet.chronology?.length > 0 && <section className='packet-section'><div className='packet-section-heading'><span>02</span><div><small>Chronology</small><h2>Record Timeline</h2></div></div><EvidenceTimeline items={packet.chronology} compact /></section>}<section className='packet-section'><div className='packet-section-heading'><span>03</span><div><small>Evidence</small><h2>Strongest Documented Support</h2></div></div><div className='packet-evidence-grid'>{(packet.strongestEvidence || []).map((item, index) => <div className='packet-evidence-card' key={`${item.title}-${index}`}><span>{item.kind}</span><h3>{item.title}</h3><p>{item.finding}</p><strong>{item.whyItMatters}</strong><div className='source-band'><InlineEvidenceText text={item.source} /></div></div>)}</div></section><section className='packet-section packet-split'><div><div className='packet-section-heading mini'><span>04</span><div><small>Function</small><h2>Reliability & Functional Impact</h2></div></div><div className='check-stack'>{(packet.functionalImpact || []).map((item, index) => <div key={`function-${index}`}><CircleCheck size={15} /><InlineEvidenceText text={item} /></div>)}</div></div><div><div className='packet-section-heading mini'><span>05</span><div><small>Development</small><h2>Missing Evidence & Next Steps</h2></div></div><div className='gap-stack'>{(packet.missingEvidencePlan || []).map((item, index) => <article className='gap-card compact' key={`packet-gap-${index}`}><span className={`priority-pill ${item.priority.toLowerCase()}`}>{item.priority}</span><h4>{item.gap}</h4><div className='next-step'><strong>Next:</strong> {item.nextStep}</div></article>)}</div></div></section><section className='packet-section'><div className='packet-section-heading'><span>06</span><div><small>Weaknesses & reconciliation</small><h2>Adverse Evidence & Record Response</h2></div></div><div className='tension-stack'>{(packet.adverseEvidence || []).map((item, index) => <article className='tension-card' key={`packet-tension-${index}`}><div className='tension-side adverse'><span>ADVERSE / CONFLICT</span><p>{item.adverse}</p></div><div className='tension-arrow'>↔</div><div className='tension-side support'><span>RECORD RESPONSE</span><p>{item.supporting}</p><div className='source-band'><InlineEvidenceText text={item.source} /></div></div><div className='reconcile-band'>{item.reconcile}</div></article>)}</div></section><section className='packet-section packet-split'><div><div className='packet-section-heading mini'><span>07</span><div><small>Preflight</small><h2>Reviewer Checklist</h2></div></div><div className='check-stack'>{(packet.reviewerChecklist || []).map((item, index) => <div key={`check-${index}`}><CircleCheck size={15} />{item}</div>)}</div></div><div><div className='packet-section-heading mini'><span>08</span><div><small>Sources</small><h2>Source Appendix</h2></div></div><div className='appendix-stack'>{(packet.sourceAppendix || []).map((item, index) => <div key={`source-${index}`}><span>{String(index + 1).padStart(2, '0')}</span><InlineEvidenceText text={item} /></div>)}</div></div></section></article>;
}

export default App;