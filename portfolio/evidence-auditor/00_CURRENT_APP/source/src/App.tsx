import { useEffect, useMemo, useRef, useState } from 'react';
import { api, auth, image } from '@appdeploy/client';
import { GlobalWorkerOptions, getDocument } from 'pdfjs-dist';
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import { Bot, Brain, CircleAlert, CircleCheck, ExternalLink, FileImage, FileSearch, FileText, FolderOpen, Gauge, Globe2, Headphones, ImagePlus, LoaderCircle, LogIn, LogOut, Mail, MemoryStick, MessageSquarePlus, Mic2, Paperclip, PanelLeft, Play, PlugZap, Printer, Scale, Search, Send, ShieldCheck, Sparkles, Square, Trash2, Video, WandSparkles, X } from 'lucide-react';

GlobalWorkerOptions.workerSrc = pdfWorker;

type User = { userId: string; email?: string; name?: string };
type Memory = { enabled: boolean; caseLabel: string; goal: string; notes: string };
type Doc = { id: string; name: string; contentType: string; charCount: number; pageCount: number; sourceMode?: 'pdf' | 'text' | 'ocr' | 'email' | 'web' | 'search' | 'media'; sourceUrl?: string; createdAt: string; excerpt: string };
type IntegrationStatus = { webSearch: boolean; neuralVoice: boolean; gmailDirect: boolean; gmailNote: string };
type NeuralVoice = { voiceId: string; name: string; labels?: Record<string, string> };
type LiveSearchResult = { answer: string; results: Array<{ title: string; url: string; content: string; publishedDate?: string }>; savedDocument?: Doc | null };
type Chat = { id?: string; threadId: string; question: string; answer: string; tool: string; speed?: WorkMode; sources: string[]; createdAt: string };
type Review = { summary: string; strongestEvidence: string[]; gaps: string[]; tensions: string[]; issues: string[] };
type LawLens = { issue: string; summary: string; whatRaterLooksFor: string[]; evidenceMatches: string[]; gaps: string[]; conflicts: string[]; nextBestEvidence: string[]; officialSources: Array<{ label: string; url: string; kind: string; title: string }> };
type WebResult = { title: string; url: string; answer: string; savedDocument?: Doc | null };
type View = 'chat' | 'review' | 'packet';
type WorkMode = 'Quick' | 'Standard' | 'Deep';
type UploadItem = { id: string; name: string; size: number; kind: 'pdf' | 'image' | 'file'; stage: 'Queued' | 'Uploading' | 'Reading' | 'Indexing' | 'OCR' | 'Ready' | 'Error'; progress: number; detail: string; error?: string };
type PluginName = 'Record Search' | 'Gap Finder' | 'Quote Check' | 'Packet Assurance' | 'Timeline Builder' | 'Rebuttal Lab' | 'Web Research' | 'Web Search' | 'YouTube & Video' | 'Vision & Media' | 'VA Law & Rater Lens' | 'OCR Intake' | 'Email Evidence';

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
    { name: 'VA Law & Rater Lens', blurb: 'Compare official CFR/VA reference criteria with the loaded record.', chatTool: false },
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

function App() {
    const [user, setUser] = useState<User | null>(null);
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
    const [review, setReview] = useState<Review | null>(null);
    const [packet, setPacket] = useState('');
    const [packetStyle, setPacketStyle] = useState('Visual evidence review');
    const [playbook, setPlaybook] = useState('Elias Evidence Playbook v5');
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
    const [integrations, setIntegrations] = useState<IntegrationStatus>({ webSearch: false, neuralVoice: false, gmailDirect: false, gmailNote: 'Direct Gmail OAuth is not connected.' });
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
    const fileRef = useRef<HTMLInputElement>(null);
    const mediaRef = useRef<HTMLInputElement>(null);
    const speechRunRef = useRef(0);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    const errorMessage = (err: unknown, fallback: string) => {
        const value = err as { message?: string; response?: { data?: { error?: string; message?: string } } };
        return value.response?.data?.error || value.response?.data?.message || value.message || fallback;
    };

    const updateUploadItem = (id: string, patch: Partial<UploadItem>) => {
        setUploadItems((current) => current.map((item) => item.id === id ? { ...item, ...patch } : item));
    };

    const formatFileSize = (bytes: number) => bytes >= 1024 * 1024 ? `${(bytes / (1024 * 1024)).toFixed(bytes >= 100 * 1024 * 1024 ? 0 : 1)} MB` : `${Math.max(1, Math.round(bytes / 1024))} KB`;

    const load = async () => {
        const { data } = await api.get('/api/bootstrap');
        setMemory(data.memory ? { ...emptyMemory, ...data.memory } : emptyMemory);
        setDocuments(data.documents ?? []);
        setChats(data.chats ?? []);
        if (data.playbook) setPlaybook(data.playbook);
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
        await api.post('/api/uploads/finalize', { uploadId, total, name: file.name, contentType: normalizedType });
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
                await api.post('/api/uploads/extracted-part', { originalName: file.name, startPage: batchStart, endPage, totalPages, text, partNumber });
                batchStart = endPage + 1;
                batchText = '';
            };
            for (let pageNumber = 1; pageNumber <= totalPages; pageNumber += 1) {
                setBusy(`Reading ${file.name} · page ${pageNumber} of ${totalPages}…`);
                updateUploadItem(uploadItemId, { stage: 'Reading', progress: Math.max(4, Math.min(90, Math.round((pageNumber / totalPages) * 90))), detail: `Reading page ${pageNumber} of ${totalPages}` });
                const page = await pdf.getPage(pageNumber);
                const content = await page.getTextContent();
                const pageText = content.items.map((item) => ('str' in item ? item.str : '')).join(' ').replace(/\s+/g, ' ').trim();
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
            if (extractedCharacters < 100) throw new Error(`${file.name} looks like an image-only scanned PDF. Large searchable PDFs can be indexed automatically; scanned-only PDFs still need OCR page images for now.`);
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
        if (successful) await load();
        const pdfCount = staged.filter((entry) => entry.kind === 'pdf').length;
        const splitNote = splitParts > pdfCount ? ` Large PDFs were indexed into ${splitParts} searchable page-range parts.` : '';
        setNotice(failures.length ? `${successful} file${successful === 1 ? '' : 's'} ready; ${failures.length} failed. Open the upload card for the error.${splitNote}` : `${successful} file${successful === 1 ? '' : 's'} indexed and ready for Elias.${splitNote}`);
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

    const runCopilot = async (rawPrompt: string, requestedTool: PluginName = tool) => {
        const prompt = rawPrompt.trim();
        if (!prompt || copilotBusy || busy) return;
        setCopilotOpen(true);
        setCopilotBusy(true);
        setCopilotAnswer('');
        setNotice('');
        try {
            const selectedTool = plugins[requestedTool] ? requestedTool : 'Record Search';
            const { data } = await api.post('/api/chat', { question: prompt, threadId, tool: selectedTool, speed: workMode });
            setChats((prev) => [...prev, data.message]);
            setCopilotAnswer(data.message.answer);
            if (autoSpeak) speak(data.message.answer);
        } catch (err) {
            setCopilotAnswer(errorMessage(err, 'Elias could not complete that Copilot request.'));
        } finally {
            setCopilotBusy(false);
        }
    };

    const runLawLens = async () => {
        if (!plugins['VA Law & Rater Lens']) {
            setNotice('VA Law & Rater Lens is disabled in Plugins.');
            return;
        }
        setBusy(`Comparing ${lawIssue} criteria with the loaded evidence…`);
        setNotice('');
        try {
            const { data } = await api.post('/api/va-lens', { issue: lawIssue, speed: workMode });
            setLawLens(data.lens);
        } catch (err) {
            setNotice(errorMessage(err, 'VA Law & Rater Lens could not run.'));
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

    if (!user) {
        return <main className='login-wrap'><section className='login-card'><div className='brand-mark'><Bot size={32} /></div><p className='eyebrow'>Evidence Auditor Pro</p><h1>Meet Elias.</h1><p>A private, source-grounded evidence workspace with persistent case memory, OCR intake, adjustable reasoning depth, voice playback, case review, and packet drafting.</p><button className='primary large' onClick={signIn}><LogIn size={18} /> Sign in to Elias</button><p className='fine'>Your workspace is private to your signed-in account. Elias organizes evidence; he does not make legal or medical determinations.</p>{notice && <div className='notice'>{notice}</div>}</section></main>;
    }

    return <div className='shell'>
        <aside className='sidebar nonprint'>
            <div className='brand'><div className='brand-mark small'><Bot size={22} /></div><div><strong>Elias</strong><span>Evidence Assistant</span></div></div>
            <div className='playbook-badge'><Brain size={14} /><span>{playbook}</span></div>
            <button className='new-chat' onClick={() => { setThreadId(crypto.randomUUID()); setView('chat'); }}><MessageSquarePlus size={17} /> New chat</button>
            <nav>
                <button className={view === 'chat' ? 'active' : ''} onClick={() => setView('chat')}><Bot size={17} /> Elias</button>
                <button className={view === 'review' ? 'active' : ''} onClick={() => setView('review')}><FileSearch size={17} /> Case Review</button>
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

            <details className='control-card'>
                <summary><Mic2 size={15} /> Voice</summary>
                <label className='field-label'>Voice engine<select value={voiceEngine} onChange={(e) => setVoiceEngine(e.target.value as 'Browser' | 'Neural')}><option value='Browser'>Browser / device</option><option value='Neural' disabled={!integrations.neuralVoice}>Neural (ElevenLabs)</option></select></label>
                <label className='field-label'>Voice style<select value={voicePreset} onChange={(e) => setVoicePreset(e.target.value)}><option>Natural</option><option>Younger Distinguished</option><option>Command Briefing</option><option>Calm Clinical</option></select></label>
                {voiceEngine === 'Neural' ? <label className='field-label'>Neural voice<select value={neuralVoiceId} onChange={(e) => setNeuralVoiceId(e.target.value)}>{neuralVoices.map((voice) => <option key={voice.voiceId} value={voice.voiceId}>{voice.name}</option>)}</select></label> : <label className='field-label'>Browser voice<select value={voiceName} onChange={(e) => setVoiceName(e.target.value)}><option value='Auto'>Best available</option>{voices.filter((voice) => /^en/i.test(voice.lang)).map((voice) => <option key={`${voice.name}-${voice.lang}`}>{voice.name}</option>)}</select></label>}
                <p>{integrations.neuralVoice ? 'Neural voice is connected. Browser/device voice remains available as a fallback.' : 'Neural voice is not connected yet. Best available uses the highest-quality voice installed by your browser/OS.'}</p>
                <label className='auto-speak'><input type='checkbox' checked={autoSpeak} onChange={(e) => setAutoSpeak(e.target.checked)} /> Auto-speak new Elias replies</label>
                <button className='secondary tiny' onClick={() => speak('Elias voice preview. Source grounded, measured, and clear.')}><Play size={14} /> Preview</button>
                <button className='secondary tiny' onClick={stopSpeaking}><Square size={12} /> Stop</button>
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
            <header className='topbar nonprint'><div><PanelLeft size={17} /><span>{view === 'chat' ? 'Elias' : view === 'review' ? 'Case Review' : 'Packet Studio'}</span></div><div className='top-controls'><span className={`speed-pill ${workMode.toLowerCase()}`}><Gauge size={14} /> {workMode}</span><div className='privacy'><ShieldCheck size={16} /> Private workspace</div></div></header>
            {notice && <div className='notice nonprint'>{notice}</div>}
            {busy && <><div className='busy nonprint'><Sparkles size={15} /> {busy}</div><div className='working-overlay nonprint' role='status' aria-live='polite'><div className='working-card'><div className='working-orbit'><Sparkles size={22} /></div><div><span>ELIAS IS WORKING</span><strong>{busy}</strong><p>Source controls are temporarily locked so repeated clicks do not start duplicate analysis jobs.</p><div className='working-track'><i /></div></div></div></div></>}

            {view === 'chat' && <section className='chat-page'>
                <div className='chat-column'>
                    {activeMessages.length === 0 && <div className='welcome'><div className='brand-mark'><Bot size={30} /></div><h1>How can I help with this case?</h1><p>Upload PDFs, text files, screenshots, or scanned document images. Elias can OCR images, find evidence, build timelines, compare contradictions, check quotes, and draft reviewer-ready packets.</p><button className='upload-hero' onClick={() => fileRef.current?.click()}><Paperclip size={18} /> Add case files</button><span className='upload-hint'>Multiple files · searchable PDFs up to 250 MB indexed by page range · TXT/MD/EML/MBOX up to 24 MB · JPG/PNG/WebP with OCR</span><div className='quick-evidence-grid'>{quickEliasActions.map((action) => <button key={action.label} disabled={copilotBusy || !!busy} onClick={() => void runCopilot(action.prompt, action.tool)}><Sparkles size={14} /><span><strong>{action.label}</strong><small>One-click source-grounded pass</small></span></button>)}</div></div>}
                    <div className='messages'>{activeMessages.map((message, index) => <div key={`${message.createdAt}-${index}`} className='turn'><div className='user-msg'>{message.question}</div><div className='assistant-msg'><div className='avatar'><Bot size={18} /></div><div><p>{message.answer}</p><div className='chips'><span>{message.tool}</span><span>{message.speed || 'Standard'}</span>{message.sources.map((source) => <span key={source}>{source}</span>)}<button onClick={() => speak(message.answer)} title='Read Elias response aloud'><Play size={12} /> Speak</button></div></div></div></div>)}</div>
                    <div className='composer nonprint'>
                        {uploadItems.length > 0 && <div className='upload-tray' aria-live='polite'>{uploadItems.map((item) => <div className={`upload-card ${item.stage.toLowerCase()}`} key={item.id}><div className={`upload-file-icon ${item.kind}`}>{item.kind === 'pdf' ? <FileText size={20} /> : item.kind === 'image' ? <FileImage size={20} /> : <Paperclip size={19} />}</div><div className='upload-file-meta'><strong title={item.name}>{item.name}</strong><span>{formatFileSize(item.size)} · {item.error || item.detail}</span>{item.stage !== 'Ready' && item.stage !== 'Error' && <div className='upload-progress' role='progressbar' aria-label={`${item.name} upload progress`} aria-valuemin={0} aria-valuemax={100} aria-valuenow={item.progress}><i style={{ width: `${item.progress}%` }} /></div>}</div><div className={`upload-state ${item.stage.toLowerCase()}`}>{item.stage === 'Ready' ? <CircleCheck size={15} /> : item.stage === 'Error' ? <CircleAlert size={15} /> : <LoaderCircle className='spin' size={15} />}<span>{item.stage === 'Ready' || item.stage === 'Error' ? item.stage : `${item.progress}%`}</span></div>{(item.stage === 'Ready' || item.stage === 'Error') && <button className='upload-dismiss' aria-label={`Hide ${item.name} upload card`} title='Hide upload card' onClick={() => setUploadItems((current) => current.filter((upload) => upload.id !== item.id))}><X size={14} /></button>}</div>)}</div>}
                        <div className='tool-row'>{enabledChatTools.map((plugin) => <button key={plugin.name} className={tool === plugin.name ? 'selected' : ''} onClick={() => setTool(plugin.name)}>{plugin.name}</button>)}</div>
                        {mediaFiles.length > 0 && <div className='chips'>{mediaFiles.map((file) => <button key={`${file.name}-${file.size}`} onClick={() => setMediaFiles((current) => current.filter((item) => item !== file))}>{file.type.startsWith('video/') ? <Video size={12} /> : file.type.startsWith('audio/') ? <Headphones size={12} /> : <ImagePlus size={12} />} {file.name} ×</button>)}</div>}
                        <textarea value={question} onChange={(e) => setQuestion(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void send(); } }} placeholder={mediaFiles.length ? 'Ask Elias about the attached media…' : 'Message Elias…'} />
                        <div className='composer-actions'><input ref={fileRef} className='hidden' multiple type='file' accept='.pdf,.txt,.md,.eml,.mbox,.png,.jpg,.jpeg,.webp,application/pdf,text/plain,text/markdown,message/rfc822,application/mbox,image/png,image/jpeg,image/webp' onChange={(e) => void upload(e.target.files)} /><input ref={mediaRef} className='hidden' multiple type='file' accept='image/*,video/*,audio/*' onChange={(e) => { setMediaFiles(Array.from(e.target.files ?? []).slice(0, 5)); e.target.value = ''; }} /><button className='attach-btn' onClick={() => fileRef.current?.click()} title='Upload case files'><Paperclip size={17} /> Add files</button><button className='attach-btn' onClick={() => mediaRef.current?.click()} title='Attach image, audio, or video for direct analysis'><ImagePlus size={17} /> Media</button><span>{documents.length} source{documents.length === 1 ? '' : 's'} loaded</span><button className='send-btn' onClick={() => void send()} disabled={(!question.trim() && !mediaFiles.length) || !!busy}><Send size={18} /></button></div>
                    </div>
                </div>
            </section>}

            {view === 'review' && <section className='workspace'>
                <div className='page-head'><div><p className='eyebrow'>Evidence workspace</p><h1>Case Review</h1><p>One place for sources, contradictions, gaps, chronology, functional impact, and the strongest record-backed evidence.</p></div><button className='primary' onClick={() => void analyze()}><FileSearch size={17} /> Analyze record · {workMode}</button></div>
                <div className='metrics'><div><span>Documents</span><strong>{documents.length}</strong></div><div><span>Indexed pages</span><strong>{documents.reduce((sum, document) => sum + (document.pageCount || 1), 0)}</strong></div><div><span>OCR / email / web</span><strong>{documents.filter((document) => ['ocr', 'email', 'web'].includes(document.sourceMode || '')).length}</strong></div></div>
                <div className='command-deck nonprint'><div><span className='command-kicker'>ELIAS COMMAND DECK</span><strong>Fast case passes without leaving Case Review</strong></div><div>{quickEliasActions.slice(0, 6).map((action) => <button key={action.label} disabled={copilotBusy || !!busy} onClick={() => void runCopilot(action.prompt, action.tool)}>{action.label}</button>)}</div></div>
                <div className='research-grid nonprint'>
                    <article className='research-panel'>
                        <div className='research-title'><Scale size={18} /><div><strong>VA Law & Rater Lens</strong><span>Live official references + your uploaded evidence</span></div></div>
                        <select value={lawIssue} onChange={(e) => setLawIssue(e.target.value)}><option>Service connection</option><option>Secondary / aggravation</option><option>Increased rating</option><option>TDIU</option><option>Mental health rating</option><option>Neurologic / migraines</option><option>Musculoskeletal rating</option></select>
                        <button className='primary' onClick={() => void runLawLens()}>Compare law to evidence</button>
                        <small>Elias separates 38 CFR regulations from VA procedural references and does not treat the checklist as a grant/denial prediction.</small>
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
                {lawLens && <div className='review-grid lens-output'><article className='wide'><h3>{lawLens.issue}: rater lens</h3><p>{lawLens.summary}</p><div className='official-links'>{lawLens.officialSources.map((source) => <a key={source.url} href={source.url} target='_blank' rel='noreferrer'><ExternalLink size={12} /> {source.label} <small>{source.kind}</small></a>)}</div></article><ReviewCard title='What the reviewer is looking for' items={lawLens.whatRaterLooksFor} /><ReviewCard title='Evidence already in the record' items={lawLens.evidenceMatches} /><ReviewCard title='Missing / weak support' items={lawLens.gaps} /><ReviewCard title='Conflicts to reconcile' items={lawLens.conflicts} /><ReviewCard title='Highest-value next evidence' items={lawLens.nextBestEvidence} /></div>}
                {webResult && <article className='web-result'><div className='research-title'><Globe2 size={18} /><div><strong>{webResult.title}</strong><a href={webResult.url} target='_blank' rel='noreferrer'>{webResult.url}</a></div></div><p>{webResult.answer}</p></article>}
                {liveSearchResult && <article className='web-result'><div className='research-title'><Search size={18} /><div><strong>Live Web Search</strong><span>{liveSearchResult.results.length} source{liveSearchResult.results.length === 1 ? '' : 's'} returned</span></div></div><p>{liveSearchResult.answer}</p><div className='official-links'>{liveSearchResult.results.map((result) => <a key={result.url} href={result.url} target='_blank' rel='noreferrer'><ExternalLink size={12} /> {result.title}</a>)}</div></article>}
                <div className='connector-note nonprint'><PlugZap size={17} /><div><strong>Connected capabilities</strong><span>Live web search: {integrations.webSearch ? 'connected' : 'not connected'} · Neural voice: {integrations.neuralVoice ? 'connected' : 'not connected'} · Gmail direct OAuth: {integrations.gmailDirect ? 'connected' : 'not connected'}. {integrations.gmailNote}</span></div></div>
                <div className='connector-note nonprint'><Mail size={17} /><div><strong>Email Evidence</strong><span>Upload .eml or .mbox files with Add files and Elias will index them as email evidence. Direct Gmail/Outlook mailbox OAuth is not represented as connected unless a secure per-user connector exists.</span></div></div>
                {review ? <div className='review-grid'><article className='wide'><h3>Reviewer summary</h3><p>{review.summary}</p></article><ReviewCard title='Strongest evidence' items={review.strongestEvidence} /><ReviewCard title='Evidence gaps' items={review.gaps} /><ReviewCard title='Tensions to reconcile' items={review.tensions} /><ReviewCard title='Major issues' items={review.issues} /></div> : <div className='empty-panel'>Run Analyze record after uploading case documents. Elias will separate supporting evidence, gaps, and tensions without making a merits decision.</div>}
                <h2 className='section-title'>Source inventory</h2><div className='doc-list'>{documents.map((document) => <article key={document.id} className='doc-card'><div>{document.sourceMode === 'ocr' ? <FileImage size={19} /> : document.sourceMode === 'email' ? <Mail size={19} /> : ['web', 'search'].includes(document.sourceMode || '') ? <Globe2 size={19} /> : document.sourceMode === 'media' ? <ImagePlus size={19} /> : <FolderOpen size={19} />}<div><strong>{document.name}</strong><span>{document.pageCount} page{document.pageCount === 1 ? '' : 's'} · {Math.round(document.charCount / 1000)}k characters · {document.sourceMode === 'ocr' ? 'OCR' : document.sourceMode === 'email' ? 'email' : document.sourceMode === 'web' ? 'web reference' : document.sourceMode === 'search' ? 'web search reference' : document.sourceMode === 'media' ? 'media analysis' : document.sourceMode || 'indexed'}</span>{document.sourceUrl && <a className='source-link' href={document.sourceUrl} target='_blank' rel='noreferrer'>{document.sourceUrl}</a>}</div></div><p>{document.excerpt}</p><button onClick={() => void removeDoc(document.id)}><Trash2 size={15} /> Delete</button></article>)}</div>
            </section>}

            {view === 'packet' && <section className='workspace'>
                <div className='page-head nonprint'><div><p className='eyebrow'>Submission builder</p><h1>Packet Studio</h1><p>Turn the loaded record into a structured reviewer draft. Deep mode is recommended for final packet assembly.</p></div><div className='packet-head-actions'><button className='secondary' disabled={copilotBusy || !!busy} onClick={() => void runCopilot(quickEliasActions[5].prompt, 'Packet Assurance')}><ShieldCheck size={17} /> One-click preflight</button><button className='primary' onClick={() => void generatePacket()}><WandSparkles size={17} /> Generate draft · {workMode}</button></div></div>
                <div className='packet-controls nonprint'><label><input type='radio' checked={packetStyle === 'Visual evidence review'} onChange={() => setPacketStyle('Visual evidence review')} /> Visual evidence review</label><label><input type='radio' checked={packetStyle === 'Formal evidence review'} onChange={() => setPacketStyle('Formal evidence review')} /> Formal evidence review</label>{packet && <button className='secondary' onClick={() => window.print()}><Printer size={16} /> Print / Save PDF</button>}</div>
                {packet ? <article className='packet-paper'><pre>{packet}</pre></article> : <div className='empty-panel'>Generate a packet after loading documents. Elias will create an executive summary, source inventory, chronology, evidence analysis, functional-impact section when supported, adverse-evidence review, missing-record plan, reviewer checklist, and source appendix.</div>}
            </section>}
        </main>

        <button className={copilotOpen ? 'elias-fab open nonprint' : 'elias-fab nonprint'} onClick={() => setCopilotOpen(!copilotOpen)}><span><Bot size={19} /></span><div><strong>Elias Copilot</strong><small>{copilotOpen ? 'Close' : 'One-click evidence help'}</small></div></button>
        {copilotOpen && <aside className='elias-copilot nonprint'>
            <div className='copilot-head'><div><p className='eyebrow'>Floating evidence copilot</p><h3>Elias</h3><span>{documents.length} indexed source{documents.length === 1 ? '' : 's'} · {workMode} mode</span></div><button onClick={() => setCopilotOpen(false)}><X size={18} /></button></div>
            <div className='copilot-actions'>{quickEliasActions.map((action) => <button key={action.label} disabled={copilotBusy || !!busy} onClick={() => void runCopilot(action.prompt, action.tool)}>{action.label}</button>)}</div>
            <div className='copilot-result' aria-live='polite'>{copilotBusy ? <div className='copilot-thinking'><div className='thinking-dots'><i /><i /><i /></div><div><strong>Elias is thinking</strong><p>{copilotPhases[copilotPhase]}</p></div></div> : copilotAnswer ? <><div className='answer-head'><Bot size={16} /><strong>Latest Copilot answer</strong></div><p>{copilotAnswer}</p><button className='secondary tiny' onClick={() => speak(copilotAnswer)}><Play size={13} /> Speak</button><button className='secondary tiny' onClick={() => setView('chat')}><MessageSquarePlus size={13} /> Open in Elias</button></> : <div className='copilot-empty'><Brain size={22} /><p>Choose a one-click pass or ask a custom question. Elias uses the same loaded evidence and source controls as the full workspace.</p></div>}</div>
            <div className='copilot-compose'><textarea value={copilotInput} onChange={(e) => setCopilotInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void runCopilot(copilotInput); setCopilotInput(''); } }} placeholder='Ask Elias about the loaded record…' /><button disabled={!copilotInput.trim() || copilotBusy || !!busy} onClick={() => { void runCopilot(copilotInput); setCopilotInput(''); }}><Send size={17} /></button></div>
        </aside>}
    </div>;
}

function ReviewCard({ title, items }: { title: string; items: string[] }) {
    return <article><h3>{title}</h3>{items.length ? <ul>{items.map((item, index) => <li key={`${title}-${index}`}>{item}</li>)}</ul> : <p>No source-grounded item was identified.</p>}</article>;
}

export default App;
