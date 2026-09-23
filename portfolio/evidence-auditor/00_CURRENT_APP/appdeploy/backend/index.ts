import { ai, db, error, json, requireAuth, router, secrets, storage } from '@appdeploy/sdk';
import pdfParse from 'pdf-parse';
import JSZip from 'jszip';

type WorkMode = 'Quick' | 'Standard' | 'Deep';
type MemoryRecord = { enabled: boolean; caseLabel: string; goal: string; notes: string; updatedAt: string };
type DocumentRecord = {
    name: string;
    contentType: string;
    text: string;
    charCount: number;
    pageCount: number;
    storagePath?: string;
    storagePaths?: string[];
    sourceMode?: 'pdf' | 'text' | 'ocr' | 'email' | 'web' | 'search' | 'media';
    sourceUrl?: string;
    createdAt: string;
};
type ChatRecord = { threadId: string; question: string; answer: string; tool: string; speed?: WorkMode; sources: string[]; createdAt: string };
type EvidenceCategory = 'Medical Records' | 'Imaging / Tests' | 'Military / Service' | 'VA / Benefits' | 'Disability / SSA / State' | 'Functional Capacity' | 'Correspondence' | 'Legal / Administrative' | 'Research' | 'Other';
type EvidenceInventoryItem = {
    id: string;
    name: string;
    category: EvidenceCategory;
    documentType: string;
    locator: string;
    candidateDates: string[];
    fingerprint: string;
    versionGroup: string;
    storageStatus: 'Stored original' | 'Derived reference' | 'Indexed only';
    classificationBasis: 'heuristic';
};

const tables = (userId: string) => ({ memory: `memory_${userId}`, documents: `documents_${userId}`, chats: `chats_${userId}` });
const safeName = (name: string) => name.replace(/[^a-zA-Z0-9._-]/g, '_').slice(0, 120) || 'document';
const safeUploadId = (value: string) => value.replace(/[^a-zA-Z0-9_-]/g, '').slice(0, 80);
const textContext = (docs: Array<DocumentRecord & { id: string }>, query = '') => {
    const terms = Array.from(new Set((query.toLowerCase().match(/[a-z0-9]{3,}/g) ?? []).slice(0, 22)));
    const ranked = terms.length ? [...docs].sort((a, b) => {
        const score = (doc: DocumentRecord) => {
            const haystack = `${doc.name} ${doc.text}`.toLowerCase();
            return terms.reduce((sum, term) => sum + (haystack.includes(term) ? 1 : 0), 0);
        };
        return score(b) - score(a);
    }) : docs;
    return ranked.slice(0, 16).map((doc) => `SOURCE: ${doc.name}\n${doc.text.slice(0, 2600)}`).join('\n\n---\n\n').slice(0, 42000);
};
const thinkingMode = (speed: WorkMode) => speed === 'Quick' ? 'NONE' : speed === 'Deep' ? 'DEEP' : 'FAST';
const outputTokens = (speed: WorkMode, base: number) => speed === 'Quick' ? Math.max(700, Math.round(base * 0.58)) : speed === 'Deep' ? Math.min(5200, Math.round(base * 1.35)) : base;

type ResilientGenerateInput = { system: string; prompt: string; schema?: Record<string, unknown>; speed: WorkMode; maxTokens: number; temperature: number; label: string };
async function resilientGenerate(input: ResilientGenerateInput) {
    try {
        return await ai.generate({ system: input.system, prompt: input.prompt, schema: input.schema, thinkingMode: thinkingMode(input.speed), maxTokens: input.maxTokens, temperature: input.temperature });
    } catch (primaryError) {
        console.warn(`${input.label} primary generation failed; retrying with a lighter pass`, primaryError);
        try {
            return await ai.generate({ system: input.system, prompt: input.prompt.slice(0, 50000), schema: input.schema, thinkingMode: 'FAST', maxTokens: Math.min(input.maxTokens, 2600), temperature: input.temperature });
        } catch (retryError) {
            console.error(`${input.label} fallback generation failed`, retryError);
            throw new Error(`${input.label} could not finish this record in one pass. Your indexed sources are still intact. Try Standard mode, narrow the request, or run the task again.`);
        }
    }
}

const VA_GUIDANCE_HUB = { label: 'VA Compensation regulations and Live Manual hub', url: 'https://www.benefits.va.gov/COMPENSATION/resources-regulations.asp', kind: 'VA procedural reference hub' };
const VA_LENS_LIBRARY: Record<string, Array<{ label: string; url: string; kind: string }>> = {
    'Service connection': [
        { label: '38 CFR § 3.303 — Principles relating to service connection', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-3/section-3.303', kind: 'Regulation' },
        { label: '38 CFR § 3.159 — VA assistance in developing claims', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-3/section-3.159', kind: 'Regulation' },
        { label: '38 CFR § 3.102 — Reasonable doubt', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-3/section-3.102', kind: 'Regulation' },
        VA_GUIDANCE_HUB,
    ],
    'Secondary / aggravation': [
        { label: '38 CFR § 3.310 — Disabilities proximately due to or aggravated by service-connected disease or injury', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-3/section-3.310', kind: 'Regulation' },
        { label: '38 CFR § 3.303 — Principles relating to service connection', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-3/section-3.303', kind: 'Regulation' },
        { label: '38 CFR § 3.102 — Reasonable doubt', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-3/section-3.102', kind: 'Regulation' },
        VA_GUIDANCE_HUB,
    ],
    'Increased rating': [
        { label: '38 CFR § 4.1 — Essentials of evaluative rating', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.1', kind: 'Regulation' },
        { label: '38 CFR § 4.7 — Higher of two evaluations', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.7', kind: 'Regulation' },
        { label: '38 CFR § 4.10 — Functional impairment', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.10', kind: 'Regulation' },
        VA_GUIDANCE_HUB,
    ],
    'TDIU': [
        { label: '38 CFR § 4.16 — Total disability ratings based on unemployability', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.16', kind: 'Regulation' },
        { label: '38 CFR § 4.10 — Functional impairment', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.10', kind: 'Regulation' },
        { label: '38 CFR § 4.1 — Essentials of evaluative rating', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.1', kind: 'Regulation' },
        VA_GUIDANCE_HUB,
    ],
    'Mental health rating': [
        { label: '38 CFR § 4.126 — Evaluation of disability from mental disorders', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.126', kind: 'Regulation' },
        { label: '38 CFR § 4.130 — Schedule of ratings—mental disorders', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.130', kind: 'Regulation' },
        { label: '38 CFR § 4.10 — Functional impairment', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.10', kind: 'Regulation' },
        VA_GUIDANCE_HUB,
    ],
    'Neurologic / migraines': [
        { label: '38 CFR § 4.120 — Evaluations by comparison', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.120', kind: 'Regulation' },
        { label: '38 CFR § 4.124a — Schedule of ratings—neurological conditions and convulsive disorders', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.124a', kind: 'Regulation' },
        { label: '38 CFR § 4.10 — Functional impairment', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.10', kind: 'Regulation' },
        VA_GUIDANCE_HUB,
    ],
    'Musculoskeletal rating': [
        { label: '38 CFR § 4.40 — Functional loss', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.40', kind: 'Regulation' },
        { label: '38 CFR § 4.45 — The joints', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.45', kind: 'Regulation' },
        { label: '38 CFR § 4.59 — Painful motion', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.59', kind: 'Regulation' },
        VA_GUIDANCE_HUB,
    ],
};

type BenefitsProgram = 'VA / VBA' | 'Social Security (SSDI / SSI)' | 'New Hampshire' | 'Medical & Functional Evidence';
type OfficialReference = { label: string; url: string; kind: string };

const SSA_BLUE_BOOK: OfficialReference = { label: 'SSA Disability Evaluation Under Social Security — Blue Book', url: 'https://www.ssa.gov/disability/professionals/bluebook/', kind: 'SSA medical-evidence reference' };
const SSA_EVIDENCE_POMS: OfficialReference = { label: 'SSA POMS DI 24501.016 — Evidence Evaluation', url: 'https://secure.ssa.gov/poms.nsf/lnx/0424501016', kind: 'SSA procedural guidance (POMS)' };
const SSA_RFC_POMS: OfficialReference = { label: 'SSA POMS DI 24510.006 — Assessing Residual Functional Capacity', url: 'https://secure.ssa.gov/poms.nsf/lnx/0424510006', kind: 'SSA procedural guidance (POMS)' };
const NH_RSA_167: OfficialReference = { label: 'NH RSA Chapter 167 — Public assistance to aged, blind, or disabled persons', url: 'https://gc.nh.gov/rsa/html/XII/167/167-mrg.htm', kind: 'New Hampshire statute' };
const NH_DHHS_FINANCIAL: OfficialReference = { label: 'NH DHHS — Financial Assistance', url: 'https://www.dhhs.nh.gov/financial-assistance-0', kind: 'New Hampshire program guidance' };

const SSA_LENS_LIBRARY: Record<string, OfficialReference[]> = {
    'Adult disability framework': [
        { label: '20 CFR § 404.1520 — Sequential evaluation of disability', url: 'https://www.ssa.gov/OP_Home/cfr20/404/404-1520.htm', kind: 'Federal regulation' },
        SSA_BLUE_BOOK,
        SSA_EVIDENCE_POMS,
    ],
    'RFC / sustained work capacity': [
        { label: '20 CFR § 404.1545 — Residual functional capacity', url: 'https://www.ssa.gov/OP_Home/cfr20/404/404-1545.htm', kind: 'Federal regulation' },
        SSA_RFC_POMS,
        { label: '20 CFR § 404.1520 — Sequential evaluation of disability', url: 'https://www.ssa.gov/OP_Home/cfr20/404/404-1520.htm', kind: 'Federal regulation' },
    ],
    'Medical opinions / evidence': [
        { label: '20 CFR § 404.1520c — Medical opinions and prior administrative findings', url: 'https://www.ssa.gov/OP_Home/cfr20/404/404-1520c.htm', kind: 'Federal regulation' },
        SSA_EVIDENCE_POMS,
        SSA_BLUE_BOOK,
    ],
    'Neurologic listings': [
        { label: 'SSA Blue Book 11.00 — Neurological disorders, adult', url: 'https://www.ssa.gov/disability/professionals/bluebook/11.00-Neurological-Adult.htm', kind: 'SSA listing criteria' },
        { label: '20 CFR § 404.1545 — Residual functional capacity', url: 'https://www.ssa.gov/OP_Home/cfr20/404/404-1545.htm', kind: 'Federal regulation' },
        SSA_EVIDENCE_POMS,
    ],
    'Mental health listings': [
        { label: 'SSA Blue Book 12.00 — Mental disorders, adult', url: 'https://www.ssa.gov/disability/professionals/bluebook/12.00-MentalDisorders-Adult.htm', kind: 'SSA listing criteria' },
        { label: '20 CFR § 404.1545 — Residual functional capacity', url: 'https://www.ssa.gov/OP_Home/cfr20/404/404-1545.htm', kind: 'Federal regulation' },
        SSA_EVIDENCE_POMS,
    ],
};

const NH_LENS_LIBRARY: Record<string, OfficialReference[]> = {
    'APTD disability standard': [
        NH_RSA_167,
        NH_DHHS_FINANCIAL,
        { label: '20 CFR § 404.1520 — Federal disability sequential evaluation', url: 'https://www.ssa.gov/OP_Home/cfr20/404/404-1520.htm', kind: 'Federal regulation referenced by the state disability framework' },
    ],
    'MEAD / disability Medicaid': [
        NH_RSA_167,
        NH_DHHS_FINANCIAL,
        SSA_EVIDENCE_POMS,
    ],
    'State assistance evidence': [
        NH_RSA_167,
        NH_DHHS_FINANCIAL,
    ],
};

const MEDICAL_LENS_LIBRARY: Record<string, OfficialReference[]> = {
    'Cross-program functional capacity': [
        { label: '38 CFR § 4.10 — Functional impairment', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.10', kind: 'VA regulation' },
        { label: '20 CFR § 404.1545 — Residual functional capacity', url: 'https://www.ssa.gov/OP_Home/cfr20/404/404-1545.htm', kind: 'SSA regulation' },
        SSA_RFC_POMS,
    ],
    'Objective findings / symptoms': [
        { label: '38 CFR § 3.159 — Evidence and VA assistance', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-3/section-3.159', kind: 'VA regulation' },
        { label: '20 CFR § 404.1529 — Evaluation of symptoms, including pain', url: 'https://www.ssa.gov/OP_Home/cfr20/404/404-1529.htm', kind: 'SSA regulation' },
        SSA_EVIDENCE_POMS,
    ],
    'Neurologic functional evidence': [
        { label: '38 CFR § 4.124a — Neurological conditions and convulsive disorders', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.124a', kind: 'VA regulation' },
        { label: 'SSA Blue Book 11.00 — Neurological disorders, adult', url: 'https://www.ssa.gov/disability/professionals/bluebook/11.00-Neurological-Adult.htm', kind: 'SSA listing criteria' },
        { label: '20 CFR § 404.1545 — Residual functional capacity', url: 'https://www.ssa.gov/OP_Home/cfr20/404/404-1545.htm', kind: 'SSA regulation' },
    ],
    'Mental functional evidence': [
        { label: '38 CFR § 4.130 — Schedule of ratings—mental disorders', url: 'https://www.ecfr.gov/current/title-38/chapter-I/part-4/section-4.130', kind: 'VA regulation' },
        { label: 'SSA Blue Book 12.00 — Mental disorders, adult', url: 'https://www.ssa.gov/disability/professionals/bluebook/12.00-MentalDisorders-Adult.htm', kind: 'SSA listing criteria' },
        { label: '20 CFR § 404.1545 — Residual functional capacity', url: 'https://www.ssa.gov/OP_Home/cfr20/404/404-1545.htm', kind: 'SSA regulation' },
    ],
};

const BENEFITS_LENS_LIBRARY: Record<BenefitsProgram, Record<string, OfficialReference[]>> = {
    'VA / VBA': VA_LENS_LIBRARY,
    'Social Security (SSDI / SSI)': SSA_LENS_LIBRARY,
    'New Hampshire': NH_LENS_LIBRARY,
    'Medical & Functional Evidence': MEDICAL_LENS_LIBRARY,
};
const BENEFITS_DEFAULT_ISSUE: Record<BenefitsProgram, string> = {
    'VA / VBA': 'Service connection',
    'Social Security (SSDI / SSI)': 'Adult disability framework',
    'New Hampshire': 'APTD disability standard',
    'Medical & Functional Evidence': 'Cross-program functional capacity',
};
const BENEFITS_JURISDICTION: Record<BenefitsProgram, string> = {
    'VA / VBA': 'Federal · Department of Veterans Affairs / Veterans Benefits Administration',
    'Social Security (SSDI / SSI)': 'Federal · Social Security Administration',
    'New Hampshire': 'State · New Hampshire',
    'Medical & Functional Evidence': 'Cross-program medical and functional evidence framework',
};

function publicHttpUrl(value: string) {
    let url: URL;
    try { url = new URL(value); } catch { throw new Error('Enter a valid http or https URL.'); }
    if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Only public http or https URLs are supported.');
    const host = url.hostname.toLowerCase();
    const private172 = host.match(/^172\.(\d+)\./);
    if (host === 'localhost' || host === '::1' || host.endsWith('.local') || /^127\./.test(host) || /^10\./.test(host) || /^192\.168\./.test(host) || /^169\.254\./.test(host) || (private172 && Number(private172[1]) >= 16 && Number(private172[1]) <= 31)) throw new Error('Private or local network URLs are not supported.');
    return url.toString();
}

async function scrapePage(url: string) {
    const safeUrl = publicHttpUrl(url);
    const page = await ai.scrape({ url: safeUrl });
    if (page.status >= 400 || !page.text.trim()) throw new Error(`Could not read ${safeUrl}`);
    return { url: safeUrl, title: page.title || new URL(safeUrl).hostname, text: page.text.trim() };
}

async function requiredSecret(name: string, label: string) {
    try {
        return await secrets.readSecret(name);
    } catch {
        throw new Error(`${label} is not connected yet.`);
    }
}

type SearchHit = { title: string; url: string; content: string; publishedDate?: string };

async function searchWeb(query: string, officialOnly = false) {
    const key = await requiredSecret('TAVILY_API_KEY', 'Live web search');
    const response = await fetch('https://api.tavily.com/search', {
        method: 'POST',
        headers: { Authorization: `Bearer ${key}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
            query,
            search_depth: 'advanced',
            max_results: 6,
            topic: 'general',
            include_answer: false,
            include_raw_content: false,
            include_published_date: true,
            language: 'en',
            include_domains: officialOnly ? ['va.gov', 'ecfr.gov', 'uscourts.gov', 'congress.gov'] : [],
        }),
    });
    if (!response.ok) throw new Error(`Live web search returned ${response.status}.`);
    const payload = await response.json() as { results?: Array<{ title?: string; url?: string; content?: string; published_date?: string }> };
    const results: SearchHit[] = (payload.results ?? [])
        .filter((item) => item.title && item.url)
        .map((item) => ({ title: String(item.title), url: String(item.url), content: String(item.content ?? ''), publishedDate: item.published_date ? String(item.published_date) : undefined }));
    if (!results.length) throw new Error('Live web search returned no usable results.');
    return results;
}

type LiteratureHit = { id: string; title: string; journal: string; pubDate: string; authors: string; url: string; citation: string };

function literatureTopic(program: BenefitsProgram, issue: string) {
    const normalized = issue.toLowerCase();
    if (normalized.includes('migraine')) return 'migraine work disability functional impairment review';
    if (normalized.includes('neurolog')) return 'neurologic disorders work disability functional capacity review';
    if (normalized.includes('mental')) return 'mental disorders work disability functional capacity systematic review';
    if (normalized.includes('musculoskeletal')) return 'musculoskeletal functional capacity evaluation work disability review';
    if (normalized.includes('rfc') || normalized.includes('tdiu') || normalized.includes('aptd') || normalized.includes('functional')) return 'functional capacity evaluation work disability reliability review';
    return program === 'VA / VBA' ? 'longitudinal medical evidence disability functional impairment review' : 'disability functional capacity sustained work medical evidence review';
}

async function searchPubMed(program: BenefitsProgram, issue: string): Promise<LiteratureHit[]> {
    try {
        const term = literatureTopic(program, issue);
        const search = await fetch(`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=json&retmax=4&sort=relevance&term=${encodeURIComponent(term)}`);
        if (!search.ok) return [];
        const searchPayload = await search.json() as { esearchresult?: { idlist?: string[] } };
        const ids = (searchPayload.esearchresult?.idlist ?? []).slice(0, 4);
        if (!ids.length) return [];
        const summary = await fetch(`https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&retmode=json&id=${ids.join(',')}`);
        if (!summary.ok) return [];
        const payload = await summary.json() as { result?: Record<string, unknown> & { uids?: string[] } };
        return ids.map((id) => {
            const item = (payload.result?.[id] ?? {}) as { title?: string; fulljournalname?: string; pubdate?: string; authors?: Array<{ name?: string }> };
            const authors = (item.authors ?? []).slice(0, 3).map((author) => author.name).filter(Boolean).join(', ');
            const title = String(item.title ?? '').trim();
            const journal = String(item.fulljournalname ?? '').trim();
            const pubDate = String(item.pubdate ?? '').trim();
            return { id: `J${ids.indexOf(id) + 1}`, title, journal, pubDate, authors, url: `https://pubmed.ncbi.nlm.nih.gov/${id}/`, citation: [authors, title, journal, pubDate].filter(Boolean).join('. ') };
        }).filter((item) => item.title);
    } catch (err) {
        console.warn('PubMed literature lookup unavailable', err);
        return [];
    }
}

function vaultCategory(doc: DocumentRecord) {
    if (doc.sourceMode === 'web' || doc.sourceMode === 'search') return '05_Legal_and_Medical_Research';
    const sample = `${doc.name} ${doc.text.slice(0, 1400)}`.toLowerCase();
    if (/hospital|clinic|medical|physician|doctor|psychi|psycholog|rehab|therapy|fce|dbq|emg|mri|ct scan|treatment|diagnos|medication/.test(sample)) return '02_Medical';
    if (/military|army|guard|service record|orders|dd214|ngb|duty|line of duty/.test(sample)) return '04_Service_and_Employment';
    if (/decision|denial|appeal|hearing|exhibit|determination|administrative|agency|notice|application|form|rfc/.test(sample)) return '03_Administrative_and_Agency';
    return '01_Original_Evidence';
}

function vaultLocator(doc: DocumentRecord) {
    const match = doc.name.match(/__pages_(\d+)-(\d+)/i);
    if (match) return `Indexed source pages ${match[1]}-${match[2]}`;
    return `${Math.max(1, doc.pageCount)} indexed page${doc.pageCount === 1 ? '' : 's'}`;
}

function evidenceCategory(doc: DocumentRecord): EvidenceCategory {
    if (doc.sourceMode === 'web' || doc.sourceMode === 'search') return 'Research';
    const sample = `${doc.name} ${doc.text.slice(0, 2200)}`.toLowerCase();
    if (/mri|x-ray|xray|ct scan|ultrasound|emg|eeg|radiology|imaging|diagnostic test/.test(sample)) return 'Imaging / Tests';
    if (/army|guard|military|service record|orders|dd214|ngb|duty|line of duty|acdutra|inacdutra|title 32/.test(sample)) return 'Military / Service';
    if (/va |vba|veteran|dbq|c&p|compensation|tdiu|rating decision/.test(sample)) return 'VA / Benefits';
    if (/ssdi|ssi|social security|aptd|dhhs|disability determination|state disability/.test(sample)) return 'Disability / SSA / State';
    if (/fce|functional capacity|work capacity|attendance|pace|persistence|reliability|lifting|sitting|standing/.test(sample)) return 'Functional Capacity';
    if (/email|letter|message|correspondence|memo/.test(sample) || doc.sourceMode === 'email') return 'Correspondence';
    if (/court|legal|attorney|hearing|appeal|administrative|decision|denial|notice/.test(sample)) return 'Legal / Administrative';
    if (/hospital|clinic|medical|physician|doctor|psychi|psycholog|rehab|therapy|treatment|diagnos|medication|patient/.test(sample)) return 'Medical Records';
    return 'Other';
}

function evidenceDocumentType(doc: DocumentRecord) {
    const sample = `${doc.name} ${doc.text.slice(0, 1200)}`.toLowerCase();
    if (/functional capacity|\bfce\b/.test(sample)) return 'Functional capacity evaluation';
    if (/\bdbq\b/.test(sample)) return 'Disability benefits questionnaire';
    if (/rating decision|decision letter|determination/.test(sample)) return 'Agency decision';
    if (/orders|dd214|ngb|line of duty|\blod\b/.test(sample)) return 'Service record';
    if (/mri|x-ray|xray|ct scan|ultrasound|emg|eeg|radiology/.test(sample)) return 'Diagnostic / imaging record';
    if (/email|message|correspondence/.test(sample) || doc.sourceMode === 'email') return 'Correspondence';
    if (doc.sourceMode === 'web' || doc.sourceMode === 'search') return 'External reference';
    if (doc.sourceMode === 'ocr') return 'Scanned / OCR record';
    if (doc.contentType === 'application/pdf') return 'PDF record';
    return 'Case record';
}

function evidenceCandidateDates(doc: DocumentRecord) {
    const sample = `${doc.name} ${doc.text.slice(0, 5000)}`;
    const matches = sample.match(/\b(?:19|20)\d{2}[-/.](?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])\b|\b(?:0?[1-9]|1[0-2])[-/.](?:0?[1-9]|[12]\d|3[01])[-/.](?:19|20)?\d{2}\b/g) ?? [];
    return Array.from(new Set(matches)).slice(0, 6);
}

function evidenceFingerprint(doc: DocumentRecord) {
    const normalized = `${doc.contentType}|${doc.charCount}|${doc.pageCount}|${doc.text.slice(0, 50000).replace(/\s+/g, ' ').trim().toLowerCase()}`;
    let hash = 2166136261;
    for (let index = 0; index < normalized.length; index += 1) {
        hash ^= normalized.charCodeAt(index);
        hash = Math.imul(hash, 16777619);
    }
    return `fnv1a-${(hash >>> 0).toString(16).padStart(8, '0')}`;
}

function evidenceVersionGroup(name: string) {
    return name.toLowerCase()
        .replace(/__pages_\d+-\d+/g, '')
        .replace(/\.(pdf|txt|md|eml|mbox|png|jpe?g|webp)$/g, '')
        .replace(/\b(copy|final|revised|revision|rev|version|ver|v)\s*[-_.]?\s*\d+\b/g, '')
        .replace(/[()\[\]{}_-]+/g, ' ')
        .replace(/\s+/g, ' ')
        .trim()
        .slice(0, 100) || 'ungrouped';
}

function evidenceStorageStatus(doc: DocumentRecord): EvidenceInventoryItem['storageStatus'] {
    if (doc.storagePaths?.length || doc.storagePath) return 'Stored original';
    if (doc.sourceMode === 'web' || doc.sourceMode === 'search' || doc.sourceMode === 'media') return 'Derived reference';
    return 'Indexed only';
}

function evidenceInventoryItem(doc: DocumentRecord & { id: string }): EvidenceInventoryItem {
    return {
        id: doc.id,
        name: doc.name,
        category: evidenceCategory(doc),
        documentType: evidenceDocumentType(doc),
        locator: vaultLocator(doc),
        candidateDates: evidenceCandidateDates(doc),
        fingerprint: evidenceFingerprint(doc),
        versionGroup: evidenceVersionGroup(doc.name),
        storageStatus: evidenceStorageStatus(doc),
        classificationBasis: 'heuristic',
    };
}

const safeVaultFolder = (value: string) => safeName(value || 'Evidence_Case').replace(/\.[^.]+$/, '').slice(0, 72) || 'Evidence_Case';
async function vaultRootFor(userId: string) {
    const memory = await getMemory(userId);
    return `${userId}/vault/${safeVaultFolder(memory?.caseLabel || 'Evidence_Case')}`;
}

async function integrationFlags() {
    const names = await secrets.listSecretNames();
    return {
        webSearch: names.includes('TAVILY_API_KEY'),
        neuralVoice: names.includes('ELEVENLABS_API_KEY'),
        gmailDirect: false,
        gmailNote: 'Direct Gmail OAuth is not enabled because this build does not yet have secure per-user Google token storage. EML/MBOX import remains available.',
        cloudVault: true,
        googleDriveDirect: false,
        driveNote: 'Private Case Vault is available now. Direct Google Drive sync requires secure per-user Google OAuth; use the Drive-ready ZIP export until that connector is available.',
    };
}

async function getMemory(userId: string) {
    const { items } = await db.list<MemoryRecord>(tables(userId).memory, { limit: 1 });
    return items[0] ?? null;
}

async function getDocuments(userId: string) {
    const { items } = await db.list<DocumentRecord>(tables(userId).documents, { limit: 100 });
    return items;
}

async function saveDocument(userId: string, input: Omit<DocumentRecord, 'createdAt'>) {
    const record: DocumentRecord = { ...input, text: input.text.slice(0, 90000), createdAt: new Date().toISOString() };
    const [id] = await db.add(tables(userId).documents, [record]);
    if (!id) throw new Error('Could not index the uploaded file.');
    return { id, ...record, excerpt: record.text.slice(0, 520) };
}

const ELIAS_PLAYBOOK = `You are Elias, a source-grounded evidence assistant for medical, military/service, disability-benefit, VA, functional-capacity, and administrative records. This is Elias Evidence Playbook v8.
Your operating rules are strict:
1. Source before assertion. Never invent evidence, dates, diagnoses, examinations, duty status, quotations, ratings, legal standards, or medical causation.
2. Separate source fact, user-reported history, and inference. Label uncertainty instead of smoothing it over.
3. Original-source control is mandatory. Primary records control over summaries, captions, diagrams, prior AI prose, and secondary descriptions. Distinguish exact quotation, paraphrase, claimant-reported history, clinician observation, objective testing, medical opinion, agency finding, and AI synthesis. Never promote one evidence type into another. If asked for a quote, use exact language only when it appears in the supplied record; otherwise label it a paraphrase.
4. Cite filenames in square brackets like [source.pdf] for material factual claims whenever a source supports them.
5. For VA-style review, organize evidence around documented event/service evidence, current condition or functional impairment, chronology, nexus/aggravation evidence, functional impact, DBQ/exam consistency, and missing records. Do not decide entitlement, service connection, diagnostic validity, or rating percentage.
6. Treat favorable and adverse evidence symmetrically. Surface adverse evidence that actually exists in the record, but do not invent speculative counterarguments.
7. When records conflict, state exactly what conflicts and what source could reconcile it.
8. Functional reliability matters: attendance, pace, persistence, unscheduled breaks, safety, recovery time, concentration, and repeatability should be highlighted when documented.
9. Prefer page/source-locatable evidence and explain when provenance is weak.
10. When discussing VA law or rating criteria, distinguish statutes/regulations from VA procedural guidance. Never call M21-1 or a VA web page a regulation. Do not predict grant/denial from a checklist alone.
11. When a live web source is supplied, keep web-source statements separate from the claimant record and identify the URL/title. Treat web material as reference unless it is explicitly added to the case record.
12. For multimodal inputs, describe only what is actually visible or audible. Distinguish direct observation, OCR/transcription, and inference. Video-frame analysis is sampled evidence, not proof of what happened between frames.
13. For live web search, cite the returned page titles/URLs in the answer and distinguish current web research from uploaded case evidence.
14. Never imply that an unavailable connector is connected. Email imports, URL reading, search APIs, voice APIs, and media analysis must be described according to their actual configured state.
15. Write like a skilled evidence analyst: clear, concise, conversational, and useful to a human reviewer. Human verification remains required.
16. For federal or state disability-benefit questions, identify the program and jurisdiction first. Keep statutes, regulations, agency manuals, policy guidance, listing criteria, and program webpages in their correct authority category; do not blur them together.
17. For SSA disability review, distinguish the sequential evaluation, listing criteria, residual functional capacity, symptom evaluation, and medical-opinion/evidence rules as applicable. Never predict an allowance or denial from a checklist.
18. For state programs, never assume a federal disability standard controls unless the official state authority incorporates it. State exactly what the state source adopts or changes, and flag date-sensitive standards for human verification.
19. For medical-evidence review, distinguish objective signs/testing, longitudinal observations, medical opinions, reported symptoms, treatment response/side effects, and functional reliability. Do not diagnose, invent causation, or convert a functional comparison into a medical conclusion.
20. An advocacy-focused submission may prioritize favorable supported evidence and omit a standalone weakness section, but it must never fabricate evidence, alter a quotation, conceal context necessary to make a statement accurate, or present an advocacy brief as a complete neutral record review.
21. Peer-reviewed literature is contextual authority, not claimant-specific evidence. Cite only literature metadata or URLs actually supplied to you and never invent an article, author, DOI, holding, or quotation.
22. Never place claimant names, source text, diagnoses, dates of birth, claim numbers, or other identifying case details into a general web or literature-search query. External research queries must be de-identified and derived only from the selected public program/issue.\n23. VA/VBA filing analysis must build the relevant date-specific duty-status chronology before nexus/aggravation analysis when duty status matters; distinguish direct service connection, qualifying-duty injury/aggravation, secondary causation, and secondary aggravation. A missing LOD or incomplete diagnostic workup is a development gap, not affirmative negative evidence, unless an actual adverse finding in the record says otherwise. Reconcile favorable medical opinions explicitly. Analyze frequency, duration, unpredictability, recovery, attendance, pace, persistence, safety, and reliability when documented.\n24. SSA filing analysis must use the five-step sequential framework, medically determinable impairment/severity/duration, Listings when raised, symptom evaluation, medical opinions/prior administrative findings, RFC by function, past relevant work, other-work analysis, and sustained-work reliability. Never recycle VA service-connection framing into SSA analysis.\n25. New Hampshire filing analysis must use the actual state authority and incorporate a federal standard only to the extent the state authority adopts or references it.\n26. Keep the internal neutral audit separate from the claimant-facing advocacy filing. The internal audit may surface strengths, weaknesses, gaps, contradictions, and recommended development; the filing may prioritize favorable supportable evidence but may not fabricate, misquote, or omit context needed for accuracy.\n27. Submission preflight is mandatory. Do not call a filing Ready to Submit when governing authorities are empty, a requested issue/disposition lacks an issue-specific argument, a key proposition lacks claimant-record support, provenance is too ambiguous to verify, locators are overly broad, the source appendix is materially duplicated/mostly uncited, or literature is weakly matched. Return visible blockers/warnings and Draft or Needs Review instead.\n28. Source appendices should be deduplicated and normally contain only sources actually cited in the filing, with stable source identity where available, a meaningful locator, and a useful role/use label.\n29. Literature searches must use the actual public issue/mechanism only, never private claimant data. Exclude weakly matched papers instead of padding the brief.`;

export const handler = router({
    'GET /api/_healthcheck': [async () => json({ message: 'Success', playbook: 'Elias Evidence Playbook v8' })],
    'GET /api/bootstrap': [requireAuth(), async (ctx) => {
        const t = tables(ctx.user!.userId);
        const memory = await getMemory(ctx.user!.userId);
        const documents = await getDocuments(ctx.user!.userId);
        const { items: chats } = await db.list<ChatRecord>(t.chats, { limit: 80 });
        return json({
            memory,
            documents: documents.map(({ text, ...doc }) => ({ ...doc, excerpt: text.slice(0, 520) })),
            chats,
            playbook: 'Elias Evidence Playbook v8',
        });
    }],
    'PUT /api/memory': [requireAuth(), async (ctx) => {
        const body = ctx.body as Partial<MemoryRecord>;
        const record: MemoryRecord = {
            enabled: body.enabled !== false,
            caseLabel: String(body.caseLabel ?? '').slice(0, 120),
            goal: String(body.goal ?? '').slice(0, 1200),
            notes: String(body.notes ?? '').slice(0, 8000),
            updatedAt: new Date().toISOString(),
        };
        const table = tables(ctx.user!.userId).memory;
        const { items } = await db.list<MemoryRecord>(table, { limit: 1 });
        if (items[0]) {
            const [ok] = await db.update(table, [{ id: items[0].id, record }]);
            if (!ok) return error('Could not update memory.', 500);
        } else {
            const [id] = await db.add(table, [record]);
            if (!id) return error('Could not create memory.', 500);
        }
        return json({ memory: record });
    }],
    'POST /api/uploads/chunk': [requireAuth(), async (ctx) => {
        const body = ctx.body as { uploadId?: string; index?: number; total?: number; base64?: string };
        const uploadId = safeUploadId(String(body.uploadId ?? ''));
        const index = Number(body.index ?? -1);
        const total = Number(body.total ?? 0);
        const base64 = String(body.base64 ?? '');
        if (!uploadId || !Number.isInteger(index) || index < 0 || !Number.isInteger(total) || total < 1 || total > 96) return error('Invalid upload chunk.', 400);
        if (!base64 || base64.length > 700000) return error('Upload chunk is empty or too large.', 400);
        const path = `${ctx.user!.userId}/uploads/${uploadId}/${String(index).padStart(4, '0')}.part`;
        const [ok] = await storage.write([{ path, content: base64, contentType: 'application/octet-stream' }]);
        if (!ok) return error('Could not store upload chunk.', 500);
        return json({ received: index, total });
    }],
    'POST /api/uploads/finalize': [requireAuth(), async (ctx) => {
        const body = ctx.body as { uploadId?: string; total?: number; name?: string; contentType?: string };
        const uploadId = safeUploadId(String(body.uploadId ?? ''));
        const total = Number(body.total ?? 0);
        const name = safeName(String(body.name ?? 'document'));
        const contentType = String(body.contentType ?? '');
        if (!uploadId || !Number.isInteger(total) || total < 1 || total > 96) return error('Invalid upload finalization request.', 400);
        if (!['application/pdf', 'text/plain', 'text/markdown'].includes(contentType)) return error('Use PDF, TXT, or Markdown files for document upload.', 400);
        const paths = Array.from({ length: total }, (_, index) => `${ctx.user!.userId}/uploads/${uploadId}/${String(index).padStart(4, '0')}.part`);
        const parts = await storage.read(paths);
        if (parts.some((part) => !part.content)) return error('One or more upload chunks are missing. Please retry the file.', 422);
        const buffer = Buffer.concat(parts.map((part) => Buffer.from(part.content ?? '', 'base64')));
        if (buffer.byteLength > 24 * 1024 * 1024) return error('Files must be 24 MB or smaller.', 400);
        let text = '';
        let pageCount = 1;
        try {
            if (contentType === 'application/pdf') {
                const parsed = await pdfParse(buffer);
                text = parsed.text ?? '';
                pageCount = parsed.numpages ?? 1;
            } else {
                text = buffer.toString('utf8');
            }
        } catch {
            return error('Elias could not extract readable text from that file.', 422);
        }
        text = text.replace(/\u0000/g, ' ').trim();
        if (!text) return error('No readable text was found. For scanned pages, upload page images so OCR can read them.', 422);
        try {
            const document = await saveDocument(ctx.user!.userId, {
                name,
                contentType,
                text,
                charCount: text.length,
                pageCount,
                storagePaths: paths,
                sourceMode: /\.(eml|mbox)$/i.test(name) ? 'email' : contentType === 'application/pdf' ? 'pdf' : 'text',
            });
            return json({ document });
        } catch (err) {
            return error(err instanceof Error ? err.message : 'Could not index the uploaded file.', 500);
        }
    }],
    'POST /api/uploads/extracted-part': [requireAuth(), async (ctx) => {
        const body = ctx.body as { originalName?: string; startPage?: number; endPage?: number; totalPages?: number; text?: string; partNumber?: number };
        const originalName = safeName(String(body.originalName ?? 'large-document.pdf'));
        const startPage = Number(body.startPage ?? 0);
        const endPage = Number(body.endPage ?? 0);
        const totalPages = Number(body.totalPages ?? 0);
        const partNumber = Number(body.partNumber ?? 0);
        const text = String(body.text ?? '').replace(/\u0000/g, ' ').trim();
        if (!Number.isInteger(startPage) || !Number.isInteger(endPage) || startPage < 1 || endPage < startPage || !Number.isInteger(totalPages) || totalPages < endPage) return error('Invalid page range for large PDF intake.', 400);
        if (!Number.isInteger(partNumber) || partNumber < 1) return error('Invalid large PDF part number.', 400);
        if (!text || text.length > 45000) return error('Large PDF text part is empty or too large.', 400);
        const baseName = originalName.replace(/\.pdf$/i, '');
        const name = `${baseName}__pages_${startPage}-${endPage}.pdf`;
        try {
            const document = await saveDocument(ctx.user!.userId, {
                name,
                contentType: 'application/pdf',
                text,
                charCount: text.length,
                pageCount: endPage - startPage + 1,
                sourceMode: 'pdf',
            });
            return json({ document, originalName, startPage, endPage, totalPages, partNumber });
        } catch (err) {
            return error(err instanceof Error ? err.message : 'Could not index the large PDF page range.', 500);
        }
    }],
    'POST /api/uploads/image': [requireAuth(), async (ctx) => {
        const body = ctx.body as { name?: string; mimeType?: string; base64?: string };
        const name = safeName(String(body.name ?? 'image'));
        const mimeType = String(body.mimeType ?? 'image/jpeg');
        const base64 = String(body.base64 ?? '');
        if (!['image/jpeg', 'image/png', 'image/webp'].includes(mimeType)) return error('OCR supports JPG, PNG, and WebP images.', 400);
        if (!base64 || base64.length > 7000000) return error('OCR image is empty or too large.', 400);
        const path = `${ctx.user!.userId}/ocr/${Date.now()}-${name}`;
        const [stored] = await storage.write([{ path, content: base64, contentType: mimeType }]);
        if (!stored) return error('Could not store the OCR image.', 500);
        try {
            const ocr = await ai.ocr({
                images: [{ data: base64, mimeType }],
                prompt: 'Transcribe all visible document text faithfully. Preserve headings, dates, names, labels, checkboxes, tables, and clinically or legally meaningful wording. Do not summarize or infer missing text.',
                thinkingMode: 'FAST',
                maxRetries: 2,
                maxTokens: 5000,
                temperature: 0.05,
            });
            const text = ocr.text.trim();
            if (!text) return error('OCR did not find readable text in that image.', 422);
            const document = await saveDocument(ctx.user!.userId, {
                name,
                contentType: mimeType,
                text,
                charCount: text.length,
                pageCount: 1,
                storagePaths: [path],
                sourceMode: 'ocr',
            });
            return json({ document, ocrAttempts: ocr.attempts });
        } catch (err) {
            console.error('OCR upload failed', err);
            return error('OCR could not read that image. Try a clearer crop or higher-contrast scan.', 422);
        }
    }],
    'GET /api/integrations/status': [requireAuth(), async () => json(await integrationFlags())],
    'GET /api/voice/voices': [requireAuth(), async () => {
        const key = await requiredSecret('ELEVENLABS_API_KEY', 'Neural voice');
        const response = await fetch('https://api.elevenlabs.io/v1/voices', { headers: { 'xi-api-key': key } });
        if (!response.ok) return error(`Neural voice service returned ${response.status}.`, 502);
        const payload = await response.json() as { voices?: Array<{ voice_id?: string; name?: string; labels?: Record<string, string> }> };
        return json({ configured: true, voices: (payload.voices ?? []).filter((voice) => voice.voice_id && voice.name).map((voice) => ({ voiceId: voice.voice_id, name: voice.name, labels: voice.labels ?? {} })).slice(0, 60) });
    }],
    'POST /api/voice/speak': [requireAuth(), async (ctx) => {
        const body = ctx.body as { text?: string; voiceId?: string; preset?: string };
        const text = String(body.text ?? '').replace(/\s+/g, ' ').trim().slice(0, 2200);
        const voiceId = String(body.voiceId ?? '').trim();
        if (!text || !voiceId) return error('Text and a neural voice are required.', 400);
        const key = await requiredSecret('ELEVENLABS_API_KEY', 'Neural voice');
        const preset = String(body.preset ?? 'Younger Distinguished');
        const settings = preset === 'Command Briefing'
            ? { stability: 0.72, similarity_boost: 0.82, style: 0.12, use_speaker_boost: true, speed: 0.92 }
            : preset === 'Calm Clinical'
                ? { stability: 0.82, similarity_boost: 0.78, style: 0.04, use_speaker_boost: true, speed: 0.94 }
                : preset === 'Natural'
                    ? { stability: 0.58, similarity_boost: 0.76, style: 0.08, use_speaker_boost: true, speed: 1.0 }
                    : { stability: 0.66, similarity_boost: 0.82, style: 0.10, use_speaker_boost: true, speed: 0.96 };
        const response = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${encodeURIComponent(voiceId)}?output_format=mp3_44100_128`, {
            method: 'POST',
            headers: { 'xi-api-key': key, 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, model_id: 'eleven_multilingual_v2', voice_settings: settings }),
        });
        if (!response.ok) return error(`Neural voice service returned ${response.status}.`, 502);
        const audio = Buffer.from(await response.arrayBuffer()).toString('base64');
        return json({ audioBase64: audio, mimeType: 'audio/mpeg' });
    }],
    'POST /api/web-search': [requireAuth(), async (ctx) => {
        const body = ctx.body as { query?: string; officialOnly?: boolean; saveToCase?: boolean; speed?: WorkMode };
        const query = String(body.query ?? '').trim().slice(0, 1200);
        if (!query) return error('Enter a web search question.', 400);
        const speed: WorkMode = body.speed === 'Quick' || body.speed === 'Deep' ? body.speed : 'Standard';
        try {
            const results = await searchWeb(query, body.officialOnly === true);
            const docs = await getDocuments(ctx.user!.userId);
            const searchContext = results.map((item, index) => `RESULT ${index + 1}: ${item.title}\nURL: ${item.url}\n${item.publishedDate ? `PUBLISHED: ${item.publishedDate}\n` : ''}${item.content}`).join('\n\n---\n\n').slice(0, 36000);
            const generated = await ai.generate({
                system: `${ELIAS_PLAYBOOK}\nSynthesize current web research without treating it as claimant evidence.`,
                prompt: `WEB SEARCH QUERY\n${query}\n\nSEARCH RESULTS\n${searchContext}\n\nUPLOADED CASE EVIDENCE\n${textContext(docs, query)}\n\nAnswer with Current web findings, Comparison with uploaded evidence, and Sources. Cite source titles and URLs.`,
                thinkingMode: thinkingMode(speed),
                maxTokens: outputTokens(speed, 2200),
                temperature: 0.1,
            });
            let savedDocument: unknown = null;
            if (body.saveToCase === true) {
                const savedText = `SEARCH QUERY: ${query}\n\n${results.map((item) => `TITLE: ${item.title}\nURL: ${item.url}\n${item.content}`).join('\n\n---\n\n')}`;
                savedDocument = await saveDocument(ctx.user!.userId, { name: `WebSearch_${safeName(query).slice(0, 70)}.txt`, contentType: 'text/plain', text: savedText, charCount: savedText.length, pageCount: 1, sourceMode: 'search' });
            }
            return json({ answer: generated.text, results, savedDocument });
        } catch (err) {
            return error(err instanceof Error ? err.message : 'Live web search failed.', 422);
        }
    }],
    'POST /api/multimodal': [requireAuth(), async (ctx) => {
        const body = ctx.body as { question?: string; threadId?: string; speed?: WorkMode; images?: Array<{ data?: string; mimeType?: string; label?: string }>; audios?: Array<{ data?: string; mimeType?: string; label?: string }>; mediaNotes?: string; saveToCase?: boolean };
        const question = String(body.question ?? '').trim().slice(0, 5000) || 'Analyze the attached media and explain what is relevant.';
        const speed: WorkMode = body.speed === 'Quick' || body.speed === 'Deep' ? body.speed : 'Standard';
        const threadId = String(body.threadId ?? 'default').slice(0, 120);
        const images = (body.images ?? []).slice(0, 5).map((item) => ({ data: String(item.data ?? ''), mimeType: String(item.mimeType ?? 'image/jpeg'), label: String(item.label ?? 'image') })).filter((item) => item.data);
        const audios = (body.audios ?? []).slice(0, 3).map((item) => ({ data: String(item.data ?? ''), mimeType: String(item.mimeType ?? 'audio/mpeg'), label: String(item.label ?? 'audio') })).filter((item) => item.data);
        const decodedBytes = [...images, ...audios].reduce((sum, item) => sum + Math.ceil(item.data.length * 0.75), 0);
        if (!images.length && !audios.length) return error('Attach an image, audio file, or video frame set first.', 400);
        if (decodedBytes > 5.5 * 1024 * 1024) return error('Media is too large for one analysis. Use fewer/smaller files.', 400);
        const docs = await getDocuments(ctx.user!.userId);
        const labels = [...images.map((item) => item.label), ...audios.map((item) => item.label)];
        const generated = await ai.generate({
            system: `${ELIAS_PLAYBOOK}\nAnalyze the supplied visual/audio media directly. Be explicit about what is observed versus inferred.`,
            prompt: `MEDIA LABELS\n${labels.join('\n')}\n\nMEDIA NOTES\n${String(body.mediaNotes ?? '').slice(0, 2000)}\n\nUPLOADED CASE RECORD\n${textContext(docs, question)}\n\nUSER QUESTION\n${question}`,
            images: images.map(({ data, mimeType }) => ({ data, mimeType })),
            audios: audios.map(({ data, mimeType }) => ({ data, mimeType })),
            thinkingMode: thinkingMode(speed),
            maxTokens: outputTokens(speed, 2000),
            temperature: 0.12,
        });
        const answer = generated.text.trim();
        const record: ChatRecord = { threadId, question, answer, tool: 'Vision & Media', speed, sources: labels.map((label) => `Media: ${label}`), createdAt: new Date().toISOString() };
        await db.add(tables(ctx.user!.userId).chats, [record]);
        if (body.saveToCase === true) {
            await saveDocument(ctx.user!.userId, { name: `Media_Analysis_${Date.now()}.txt`, contentType: 'text/plain', text: `MEDIA: ${labels.join(', ')}\n\nQUESTION: ${question}\n\nANALYSIS:\n${answer}`, charCount: answer.length, pageCount: 1, sourceMode: 'media' });
        }
        return json({ message: record });
    }],
    'POST /api/web-research': [requireAuth(), async (ctx) => {
        const body = ctx.body as { url?: string; question?: string; saveToCase?: boolean; speed?: WorkMode };
        const question = String(body.question ?? 'Summarize the material that is relevant to this case.').trim().slice(0, 3000);
        const speed: WorkMode = body.speed === 'Quick' || body.speed === 'Deep' ? body.speed : 'Standard';
        try {
            const page = await scrapePage(String(body.url ?? ''));
            const docs = await getDocuments(ctx.user!.userId);
            const generated = await ai.generate({
                system: `${ELIAS_PLAYBOOK}\nYou are using one live web page. Do not treat the web page as claimant evidence unless explicitly saved to the case.`,
                prompt: `WEB PAGE\nTITLE: ${page.title}\nURL: ${page.url}\n${page.text.slice(0, 30000)}\n\nCURRENT CASE RECORD\n${textContext(docs, question)}\n\nQUESTION\n${question}\n\nAnswer with a short Web findings section, a Case-record comparison section, and a Source note with the exact URL.`,
                thinkingMode: thinkingMode(speed),
                maxTokens: outputTokens(speed, 1800),
                temperature: 0.1,
            });
            let savedDocument: unknown = null;
            if (body.saveToCase === true) {
                savedDocument = await saveDocument(ctx.user!.userId, {
                    name: `Web_${safeName(page.title)}.txt`,
                    contentType: 'text/plain',
                    text: `SOURCE URL: ${page.url}\nTITLE: ${page.title}\n\n${page.text}`,
                    charCount: page.text.length,
                    pageCount: 1,
                    sourceMode: 'web',
                    sourceUrl: page.url,
                });
            }
            return json({ title: page.title, url: page.url, answer: generated.text, savedDocument });
        } catch (err) {
            return error(err instanceof Error ? err.message : 'Web research failed.', 422);
        }
    }],
    'POST /api/benefits-lens': [requireAuth(), async (ctx) => {
        const body = ctx.body as { program?: string; issue?: string; speed?: WorkMode };
        const requestedProgram = String(body.program ?? 'VA / VBA');
        const program: BenefitsProgram = requestedProgram in BENEFITS_LENS_LIBRARY ? requestedProgram as BenefitsProgram : 'VA / VBA';
        const programLibrary = BENEFITS_LENS_LIBRARY[program];
        const requestedIssue = String(body.issue ?? BENEFITS_DEFAULT_ISSUE[program]);
        const issue = programLibrary[requestedIssue] ? requestedIssue : BENEFITS_DEFAULT_ISSUE[program];
        const speed: WorkMode = body.speed === 'Quick' || body.speed === 'Deep' ? body.speed : 'Standard';
        const references = programLibrary[issue];
        const scraped: Array<{ label: string; url: string; kind: string; title: string; text: string }> = [];
        for (const source of references) {
            try {
                const page = await scrapePage(source.url);
                scraped.push({ ...source, title: page.title, text: page.text.slice(0, 14000) });
            } catch (err) {
                console.warn('Benefits lens source unavailable', source.url, err);
            }
        }
        if (!scraped.length) return error('Official disability-benefits sources are temporarily unavailable. Try again later.', 502);
        const docs = await getDocuments(ctx.user!.userId);
        const authority = scraped.map((source) => `REFERENCE: ${source.label}\nKIND: ${source.kind}\nURL: ${source.url}\n${source.text.slice(0, 8000)}`).join('\n\n---\n\n').slice(0, 32000);
        const jurisdiction = BENEFITS_JURISDICTION[program];
        try {
            const generated = await resilientGenerate({
                system: `${ELIAS_PLAYBOOK}\nAct as a disability-benefits evidence-comparison assistant for the selected program. Explain the live official authorities, preserve their hierarchy, and compare them with the uploaded record. Distinguish statute/regulation from agency manuals, POMS/M21-style procedural guidance, listing criteria, and informational program guidance. For VA/VBA, distinguish 38 CFR from VBA procedural guidance. For SSA, distinguish 20 CFR, the Blue Book, and POMS. For New Hampshire, do not import a federal rule unless the state authority actually incorporates it. For medical evidence, describe evidentiary and functional relevance without diagnosing or inventing causation. Do not decide entitlement, disability status, service connection, rating percentage, allowance/denial, or legal sufficiency.`,
                prompt: `PROGRAM: ${program}\nJURISDICTION: ${jurisdiction}\nISSUE: ${issue}\n\nLIVE OFFICIAL REFERENCE MATERIAL\n${authority}\n\nUPLOADED CASE EVIDENCE\n${textContext(docs, issue)}\n\nBuild a concise reviewer-facing crosswalk. State the governing framework in plain language, then identify record matches, gaps, conflicts, and the highest-value next evidence. Every case-evidence match must cite an uploaded filename in square brackets. Never present a manual, POMS section, listing page, or agency webpage as if it were a statute or regulation.`,
                schema: {
                    type: 'object',
                    properties: {
                        summary: { type: 'string' },
                        framework: { type: 'array', items: { type: 'string' } },
                        whatRaterLooksFor: { type: 'array', items: { type: 'string' } },
                        evidenceMatches: { type: 'array', items: { type: 'string' } },
                        gaps: { type: 'array', items: { type: 'string' } },
                        conflicts: { type: 'array', items: { type: 'string' } },
                        nextBestEvidence: { type: 'array', items: { type: 'string' } },
                    },
                    required: ['summary', 'framework', 'whatRaterLooksFor', 'evidenceMatches', 'gaps', 'conflicts', 'nextBestEvidence'],
                },
                speed,
                maxTokens: outputTokens(speed, 2600),
                temperature: 0.05,
                label: 'Benefits Law & Medical Lens',
            });
            let lens: Record<string, unknown>;
            try { lens = JSON.parse(generated.text) as Record<string, unknown>; } catch { lens = { summary: generated.text, framework: [], whatRaterLooksFor: [], evidenceMatches: [], gaps: [], conflicts: [], nextBestEvidence: [] }; }
            return json({ lens: { ...lens, program, jurisdiction, issue, officialSources: scraped.map(({ label, url, kind, title }) => ({ label, url, kind, title })) } });
        } catch (err) {
            return error(err instanceof Error ? err.message : 'Benefits Law & Medical Lens could not finish this record.', 422);
        }
    }],
    'POST /api/va-lens': [requireAuth(), async (ctx) => {
        const body = ctx.body as { issue?: string; speed?: WorkMode };
        const issue = String(body.issue ?? 'Service connection');
        const speed: WorkMode = body.speed === 'Quick' || body.speed === 'Deep' ? body.speed : 'Standard';
        const sources = VA_LENS_LIBRARY[issue] ?? VA_LENS_LIBRARY['Service connection'];
        const scraped: Array<{ label: string; url: string; kind: string; title: string; text: string }> = [];
        for (const source of sources) {
            try {
                const page = await scrapePage(source.url);
                scraped.push({ ...source, title: page.title, text: page.text.slice(0, 14000) });
            } catch (err) {
                console.warn('VA lens source unavailable', source.url, err);
            }
        }
        if (!scraped.length) return error('Official VA/eCFR sources are temporarily unavailable. Try again later.', 502);
        const docs = await getDocuments(ctx.user!.userId);
        const authority = scraped.map((source) => `REFERENCE: ${source.label}\nKIND: ${source.kind}\nURL: ${source.url}\n${source.text.slice(0, 8000)}`).join('\n\n---\n\n').slice(0, 28000);
        try {
            const generated = await resilientGenerate({
                system: `${ELIAS_PLAYBOOK}\nAct as a VA evidence-comparison assistant. Explain what the cited regulation or official VA reference generally asks a reviewer to evaluate, then compare that framework with the uploaded evidence. Do not issue a legal conclusion or predict a rating.`,
                prompt: `ISSUE: ${issue}\n\nOFFICIAL REFERENCE MATERIAL\n${authority}\n\nUPLOADED CASE EVIDENCE\n${textContext(docs, issue)}\n\nBuild a concise rater-facing comparison for a visual dashboard. Every evidence match must cite an uploaded filename in square brackets. Keep regulation and VA procedural references separate.`,
                schema: {
                    type: 'object',
                    properties: {
                        summary: { type: 'string' },
                        whatRaterLooksFor: { type: 'array', items: { type: 'string' } },
                        evidenceMatches: { type: 'array', items: { type: 'string' } },
                        gaps: { type: 'array', items: { type: 'string' } },
                        conflicts: { type: 'array', items: { type: 'string' } },
                        nextBestEvidence: { type: 'array', items: { type: 'string' } },
                    },
                    required: ['summary', 'whatRaterLooksFor', 'evidenceMatches', 'gaps', 'conflicts', 'nextBestEvidence'],
                },
                speed,
                maxTokens: outputTokens(speed, 2400),
                temperature: 0.05,
                label: 'VA Law & Rater Lens',
            });
            let lens: Record<string, unknown>;
            try { lens = JSON.parse(generated.text) as Record<string, unknown>; } catch { lens = { summary: generated.text, whatRaterLooksFor: [], evidenceMatches: [], gaps: [], conflicts: [], nextBestEvidence: [] }; }
            return json({ lens: { ...lens, issue, officialSources: scraped.map(({ label, url, kind, title }) => ({ label, url, kind, title })) } });
        } catch (err) {
            return error(err instanceof Error ? err.message : 'VA Law & Rater Lens could not finish this record.', 422);
        }
    }],
    'POST /api/submission-brief': [requireAuth(), async (ctx) => {
        const body = ctx.body as { program?: string; issue?: string; speed?: WorkMode };
        const requestedProgram = String(body.program ?? 'VA / VBA');
        const program: BenefitsProgram = requestedProgram in BENEFITS_LENS_LIBRARY ? requestedProgram as BenefitsProgram : 'VA / VBA';
        const programLibrary = BENEFITS_LENS_LIBRARY[program];
        const requestedIssue = String(body.issue ?? BENEFITS_DEFAULT_ISSUE[program]);
        const issue = programLibrary[requestedIssue] ? requestedIssue : BENEFITS_DEFAULT_ISSUE[program];
        const speed: WorkMode = body.speed === 'Quick' || body.speed === 'Deep' ? body.speed : 'Deep';
        const docs = await getDocuments(ctx.user!.userId);
        if (!docs.length) return error('Upload at least one source before building a submission brief.', 400);
        const memory = await getMemory(ctx.user!.userId);
        const references = programLibrary[issue];
        const scraped: Array<{ label: string; url: string; kind: string; title: string; text: string }> = [];
        for (const source of references) {
            try {
                const page = await scrapePage(source.url);
                scraped.push({ ...source, title: page.title, text: page.text.slice(0, 9000) });
            } catch (err) {
                console.warn('Submission authority unavailable', source.url, err);
            }
        }
        const literature = await searchPubMed(program, issue);
        const authorityContext = scraped.map((source) => `AUTHORITY: ${source.label}\nKIND: ${source.kind}\nURL: ${source.url}\n${source.text.slice(0, 5000)}`).join('\n\n---\n\n').slice(0, 18000);
        const literatureContext = literature.map((source) => `${source.id}: ${source.citation}\nPUBMED: ${source.url}`).join('\n');
        try {
            const generated = await resilientGenerate({
                system: `${ELIAS_PLAYBOOK}\nDraft an advocacy-focused disability-benefits submission brief, separate from the internal neutral audit. Present only favorable arguments actually supportable from the supplied record and cited authorities. Do not create a standalone weaknesses/adverse-evidence section, but never omit context needed for accuracy. For VA/VBA, build relevant duty-status chronology before nexus/aggravation analysis, distinguish direct/qualifying-duty/secondary/aggravation theories, treat missing LOD or diagnostic workup as a development gap rather than negative evidence unless an actual adverse finding says otherwise, reconcile favorable opinions, and analyze frequency/duration/recovery/attendance/pace/persistence/reliability. For SSA, use the five-step framework, MDI/severity/duration, Listings when raised, symptom evaluation, medical opinions, RFC by function, past work/other work, and sustained-work reliability; do not use service-connection framing. For New Hampshire, use the state standard and federal rules only where state authority incorporates them. Use literature only when tightly relevant to the selected public issue/mechanism.`, 
                prompt: `PROGRAM: ${program}\nJURISDICTION: ${BENEFITS_JURISDICTION[program]}\nISSUE: ${issue}\nCASE LABEL: ${memory?.caseLabel ?? 'Evidence case'}\nADVOCACY GOAL: ${memory?.goal ?? ''}\n\nREQUIRED FILING STRUCTURE\nWhat Matters Now / Requested Action; Issues Presented; issue-specific evidence map; relevant chronology; Objective Findings; Favorable Evidence Map; Record-Grounded Medical & Legal Arguments; Functional Reliability / RFC or Work-Impact Table; Governing Authorities; only tightly relevant verified literature; Focused Questions / Next Development when appropriate; concise cited-source appendix; Requested Disposition. Every key proposition needs claimant-record support. Prefer pinpoint locators when the supplied source identity permits them.\n\nOFFICIAL LEGAL / PROGRAM AUTHORITIES\n${authorityContext || 'Live official text was not available; do not invent authority content.'}\n\nPUBMED LITERATURE METADATA\n${literatureContext || 'No PubMed results were available.'}\n\nCLAIMANT RECORD\n${textContext(docs, `${issue} ${memory?.goal ?? ''} strongest objective evidence functional impact treating opinion chronology`).slice(0, 30000)}\n\nBuild a concise filing-ready advocacy brief modeled on an evidence convergence/rebuttal packet. Use filenames in square brackets for claimant-record support. Legal citation names must match the supplied authority labels. Journal references must use only J1-J4 IDs supplied above. The requested action is advocacy language, not a prediction.`,
                schema: {
                    type: 'object',
                    properties: {
                        title: { type: 'string' },
                        subtitle: { type: 'string' },
                        requestedAction: { type: 'string' },
                        executiveArgument: { type: 'string' },
                        evidenceConvergence: { type: 'array', items: { type: 'object', properties: { evidence: { type: 'string' }, establishes: { type: 'string' }, whyItMatters: { type: 'string' }, source: { type: 'string' } }, required: ['evidence', 'establishes', 'whyItMatters', 'source'] } },
                        arguments: { type: 'array', items: { type: 'object', properties: { heading: { type: 'string' }, proposition: { type: 'string' }, recordSupport: { type: 'string' }, medicalReasoning: { type: 'string' }, legalReasoning: { type: 'string' }, sourceCitations: { type: 'array', items: { type: 'string' } }, authorityCitations: { type: 'array', items: { type: 'string' } } }, required: ['heading', 'proposition', 'recordSupport', 'medicalReasoning', 'legalReasoning', 'sourceCitations', 'authorityCitations'] } },
                        functionalCase: { type: 'array', items: { type: 'string' } },
                        medicalLiterature: { type: 'array', items: { type: 'object', properties: { sourceId: { type: 'string' }, relevance: { type: 'string' } }, required: ['sourceId', 'relevance'] } },
                        chronology: { type: 'array', items: { type: 'object', properties: { date: { type: 'string' }, event: { type: 'string' }, source: { type: 'string' }, significance: { type: 'string' } }, required: ['date', 'event', 'source', 'significance'] } },
                        objectiveFindings: { type: 'array', items: { type: 'string' } },
                        focusedQuestions: { type: 'array', items: { type: 'string' } },
                        requestedDisposition: { type: 'string' },
                    },
                    required: ['title', 'subtitle', 'requestedAction', 'executiveArgument', 'evidenceConvergence', 'arguments', 'functionalCase', 'medicalLiterature', 'requestedDisposition'],
                },
                speed,
                maxTokens: outputTokens(speed, 4300),
                temperature: 0.04,
                label: 'Submission Advocacy Brief',
            });
            let brief: Record<string, unknown>;
            try { brief = JSON.parse(generated.text) as Record<string, unknown>; } catch { brief = { title: memory?.caseLabel || 'Advocacy Submission Brief', subtitle: `${program} · ${issue}`, requestedAction: memory?.goal || 'Requested agency action', executiveArgument: generated.text, evidenceConvergence: [], arguments: [], functionalCase: [], medicalLiterature: [], requestedDisposition: memory?.goal || '' }; }
            const requestedLiterature = Array.isArray(brief.medicalLiterature) ? brief.medicalLiterature as Array<Record<string, unknown>> : [];
            brief.medicalLiterature = requestedLiterature.map((item) => {
                const hit = literature.find((source) => source.id === String(item.sourceId ?? ''));
                return hit ? { ...hit, relevance: String(item.relevance ?? ''), sourceType: 'Peer-reviewed literature indexed by PubMed' } : null;
            }).filter(Boolean);
            brief.legalAuthorities = scraped.map(({ label, url, kind, title }) => ({ label, url, kind, title }));
            const arguments = Array.isArray(brief.arguments) ? brief.arguments as Array<Record<string, unknown>> : [];
            const citedNames = new Set<string>();
            for (const argument of arguments) {
                const citations = Array.isArray(argument.sourceCitations) ? argument.sourceCitations : [];
                for (const citation of citations) {
                    const value = String(citation);
                    for (const doc of docs) if (value.includes(doc.name) || value.includes(`[${doc.name}]`)) citedNames.add(doc.name);
                }
                const support = String(argument.recordSupport ?? '');
                for (const doc of docs) if (support.includes(doc.name) || support.includes(`[${doc.name}]`)) citedNames.add(doc.name);
            }
            const convergence = Array.isArray(brief.evidenceConvergence) ? brief.evidenceConvergence as Array<Record<string, unknown>> : [];
            for (const row of convergence) {
                const source = String(row.source ?? '');
                for (const doc of docs) if (source.includes(doc.name) || source.includes(`[${doc.name}]`)) citedNames.add(doc.name);
            }
            const seen = new Set<string>();
            brief.sourceAppendix = docs.filter((doc) => citedNames.has(doc.name)).filter((doc) => {
                const key = `${doc.name.toLowerCase()}|${vaultLocator(doc).toLowerCase()}`;
                if (seen.has(key)) return false;
                seen.add(key);
                return true;
            }).slice(0, 70).map((doc) => ({ sourceId: doc.id, name: doc.name, locator: vaultLocator(doc), use: doc.sourceMode === 'web' || doc.sourceMode === 'search' ? 'Cited reference/research source' : 'Cited claimant-record evidence' }));
            const blockers: string[] = [];
            const warnings: string[] = [];
            if (!scraped.length) blockers.push('Governing authorities are empty or unavailable.');
            if (!arguments.length) blockers.push('No issue-specific record-grounded argument was generated.');
            if (arguments.some((argument) => !String(argument.recordSupport ?? '').trim() || !(Array.isArray(argument.sourceCitations) && argument.sourceCitations.length))) blockers.push('One or more key propositions lack claimant-record citation support.');
            if (!String(brief.requestedDisposition ?? '').trim()) blockers.push('Requested disposition is empty.');
            if ((brief.sourceAppendix as Array<unknown>).length === 0) blockers.push('No cited claimant-record sources could be resolved into the source appendix.');
            if ((brief.sourceAppendix as Array<{ locator: string }>).some((source) => /indexed source pages? \d+-\d+|indexed pages?/i.test(source.locator) && !/pages? \d+-\d+/i.test(source.locator))) warnings.push('One or more source locators are broad; verify pinpoint page/section locators before filing.');
            if (requestedLiterature.length > 0 && (brief.medicalLiterature as Array<unknown>).length === 0) warnings.push('Requested literature was excluded because it could not be verified against returned PubMed metadata.');
            const status = blockers.length ? 'Needs Review' : warnings.length ? 'Needs Review' : 'Ready to Submit';
            brief.preflight = { status, blockers: Array.from(new Set(blockers)), warnings: Array.from(new Set(warnings)) };
            brief.verificationNote = `Preflight status: ${status}. Advocacy-focused filing draft; internal neutral audit remains separate. Claimant-record facts must trace to cited primary records. Recheck official authorities and literature immediately before filing.`;
            return json({ brief, program, issue, literatureConnected: (brief.medicalLiterature as Array<unknown>).length > 0, preflight: brief.preflight });
        } catch (err) {
            return error(err instanceof Error ? err.message : 'Submission Advocacy Brief could not finish this record.', 422);
        }
    }],
    'GET /api/evidence/inventory': [requireAuth(), async (ctx) => {
        const docs = await getDocuments(ctx.user!.userId) as Array<DocumentRecord & { id: string }>;
        const items = docs.map(evidenceInventoryItem);
        const duplicateMap = new Map<string, EvidenceInventoryItem[]>();
        const versionMap = new Map<string, EvidenceInventoryItem[]>();
        items.forEach((item) => {
            duplicateMap.set(item.fingerprint, [...(duplicateMap.get(item.fingerprint) ?? []), item]);
            versionMap.set(item.versionGroup, [...(versionMap.get(item.versionGroup) ?? []), item]);
        });
        const duplicateGroups = Array.from(duplicateMap.entries())
            .filter(([, group]) => group.length > 1)
            .map(([fingerprint, group]) => ({ fingerprint, documentIds: group.map((item) => item.id), names: group.map((item) => item.name), note: 'Likely duplicate based on a deterministic text/content fingerprint; verify before removing anything.' }));
        const versionGroups = Array.from(versionMap.entries())
            .filter(([key, group]) => key !== 'ungrouped' && group.length > 1)
            .map(([versionGroup, group]) => ({ versionGroup, documentIds: group.map((item) => item.id), names: group.map((item) => item.name), note: 'Possible versions based on filename normalization; this is a review cue, not a conclusion.' }));
        return json({ items, duplicateGroups, versionGroups, generatedAt: new Date().toISOString(), warning: 'Categories, document types, candidate dates, duplicate groups, and version groups are heuristic review aids. Original records control.' });
    }],

    'POST /api/vault/organize': [requireAuth(), async (ctx) => {
        const userId = ctx.user!.userId;
        const docs = await getDocuments(userId);
        const root = await vaultRootFor(userId);
        const existing = await storage.list({ prefix: `${root}/`, limit: 200 });
        const existingPaths = new Set(existing.paths);
        const manifest: Array<Record<string, unknown>> = [];
        let copied = 0;
        let indexedOnly = 0;
        for (const doc of docs.slice(0, 70)) {
            const category = vaultCategory(doc);
            const destination = `${root}/${category}/${safeName(doc.name)}`;
            let stored = existingPaths.has(destination);
            if (!stored) {
                const sourcePaths = doc.storagePaths?.length ? doc.storagePaths : doc.storagePath ? [doc.storagePath] : [];
                if (sourcePaths.length) {
                    const parts = await storage.read(sourcePaths);
                    if (parts.every((part) => part.content)) {
                        const buffer = Buffer.concat(parts.map((part) => Buffer.from(part.content ?? '', 'base64')));
                        const [ok] = await storage.write([{ path: destination, content: buffer.toString('base64'), contentType: doc.contentType || 'application/octet-stream' }]);
                        stored = Boolean(ok);
                    }
                } else if (doc.sourceMode === 'web' || doc.sourceMode === 'search' || doc.sourceMode === 'media') {
                    const [ok] = await storage.write([{ path: destination.replace(/\.[^.]+$/, '') + '.txt', content: Buffer.from(doc.text, 'utf8').toString('base64'), contentType: 'text/plain' }]);
                    stored = Boolean(ok);
                }
            }
            if (stored) copied += 1; else indexedOnly += 1;
            manifest.push({ name: doc.name, category, locator: vaultLocator(doc), storedOriginal: stored, note: stored ? 'Private cloud copy organized in Case Vault' : 'Indexed evidence is available to Elias, but an original binary was not preserved for this source.' });
        }
        const manifestPath = `${root}/Case_Vault_Manifest.json`;
        const readmePath = `${root}/README_Case_Vault.txt`;
        await storage.write([
            { path: manifestPath, content: JSON.stringify({ generatedAt: new Date().toISOString(), folders: ['01_Original_Evidence', '02_Medical', '03_Administrative_and_Agency', '04_Service_and_Employment', '05_Legal_and_Medical_Research', '06_Submission_Packets'], documents: manifest }, null, 2), contentType: 'application/json' },
            { path: readmePath, content: 'Elias Case Vault\n\nPrivate app cloud storage organized for evidence review. The Drive-ready ZIP preserves these folders when extracted or uploaded. Direct Google Drive sync is not connected unless secure per-user Google OAuth is available.', contentType: 'text/plain' },
        ]);
        return json({ root, organized: copied, indexedOnly, manifest });
    }],
    'GET /api/vault/status': [requireAuth(), async (ctx) => {
        const root = await vaultRootFor(ctx.user!.userId);
        const listing = await storage.list({ prefix: `${root}/`, limit: 200 });
        const counts = new Map<string, number>();
        for (const path of listing.paths) {
            const relative = path.slice(root.length + 1);
            const folder = relative.includes('/') ? relative.split('/')[0] : 'Vault files';
            if (folder === 'exports') continue;
            counts.set(folder, (counts.get(folder) ?? 0) + 1);
        }
        return json({ root, fileCount: listing.paths.filter((path) => !path.includes('/exports/')).length, folders: Array.from(counts.entries()).map(([name, count]) => ({ name, count })), googleDriveDirect: false, driveNote: 'Direct Google Drive sync requires secure per-user OAuth. Export a Drive-ready ZIP to preserve the folder structure.' });
    }],
    'POST /api/vault/generated-file': [requireAuth(), async (ctx) => {
        const body = ctx.body as { name?: string; base64?: string; contentType?: string };
        const name = safeName(String(body.name ?? 'Submission_Advocacy_Brief.pdf'));
        const base64 = String(body.base64 ?? '');
        if (!base64 || base64.length > 8_000_000) return error('Generated file is empty or too large for Case Vault.', 400);
        const root = await vaultRootFor(ctx.user!.userId);
        const path = `${root}/06_Submission_Packets/${name}`;
        const [ok] = await storage.write([{ path, content: base64, contentType: String(body.contentType ?? 'application/pdf') }]);
        if (!ok) return error('Could not save the generated filing to Case Vault.', 500);
        const [signed] = await storage.url([path]);
        return json({ saved: true, path, url: signed?.url ?? '' });
    }],
    'POST /api/vault/export': [requireAuth(), async (ctx) => {
        const root = await vaultRootFor(ctx.user!.userId);
        const listing = await storage.list({ prefix: `${root}/`, limit: 200 });
        const paths = listing.paths.filter((path) => !path.includes('/exports/')).slice(0, 120);
        if (!paths.length) return error('Case Vault is empty. Organize the evidence first.', 400);
        const files = await storage.read(paths);
        const payloadChars = files.reduce((sum, file) => sum + (file.content?.length ?? 0), 0);
        if (payloadChars > 80_000_000) return error('This vault is too large for a single ZIP export. Download the largest originals separately.', 413);
        const zip = new JSZip();
        files.forEach((file) => {
            if (!file.content) return;
            const relative = file.path.slice(root.length + 1);
            if (relative === 'Case_Vault_Manifest.json' || relative === 'README_Case_Vault.txt') zip.file(relative, file.content);
            else zip.file(relative, file.content, { base64: true });
        });
        const zipped = await zip.generateAsync({ type: 'base64', compression: 'DEFLATE', compressionOptions: { level: 6 } });
        const exportPath = `${root}/exports/Elias_Case_Vault_Drive_Ready.zip`;
        const [ok] = await storage.write([{ path: exportPath, content: zipped, contentType: 'application/zip' }]);
        if (!ok) return error('Could not create the Case Vault ZIP.', 500);
        const [signed] = await storage.url([exportPath]);
        return json({ url: signed?.url ?? '', path: exportPath, fileCount: paths.length });
    }],
    'DELETE /api/documents/:id': [requireAuth(), async (ctx) => {
        const table = tables(ctx.user!.userId).documents;
        const [doc] = await db.get<DocumentRecord>(table, [ctx.params.id]);
        if (!doc) return error('Document not found.', 404);
        const paths = doc.storagePaths?.length ? doc.storagePaths : doc.storagePath ? [doc.storagePath] : [];
        if (paths.length) await storage.delete(paths);
        const [deleted] = await db.delete(table, [ctx.params.id]);
        if (!deleted) return error('Could not delete document.', 500);
        return json({ deleted: true });
    }],
    'POST /api/chat': [requireAuth(), async (ctx) => {
        const body = ctx.body as { question?: string; threadId?: string; tool?: string; speed?: WorkMode };
        const question = String(body.question ?? '').trim().slice(0, 6000);
        if (!question) return error('Ask Elias a question first.', 400);
        const threadId = String(body.threadId ?? 'default').slice(0, 120);
        const tool = String(body.tool ?? 'Record Search').slice(0, 80);
        const speed: WorkMode = body.speed === 'Quick' || body.speed === 'Deep' ? body.speed : 'Standard';
        const userId = ctx.user!.userId;
        const memory = await getMemory(userId);
        const docs = await getDocuments(userId);
        const { items: prior } = await db.list<ChatRecord>(tables(userId).chats, { limit: 40 });
        const recent = prior.filter((message) => message.threadId === threadId).slice(-8).map((message) => `User: ${message.question}\nElias: ${message.answer}`).join('\n\n');
        const memoryText = memory?.enabled ? `Case label: ${memory.caseLabel}\nGoal: ${memory.goal}\nNotes: ${memory.notes}` : 'Case memory is disabled.';
        let webContext = '';
        let webSourceLabel = '';
        if (tool === 'Web Research' || tool === 'YouTube & Video') {
            const match = question.match(/https?:\/\/[^\s]+/i);
            if (!match) return error(`${tool} needs a full http or https URL in your message.`, 400);
            try {
                const page = await scrapePage(match[0].replace(/[),.;]+$/, ''));
                const isYouTube = /(^|\.)youtube\.com$|(^|\.)youtu\.be$/i.test(new URL(page.url).hostname);
                webContext = `${isYouTube ? 'YOUTUBE PAGE / PUBLIC TEXT' : 'WEB SOURCE'}\nTITLE: ${page.title}\nURL: ${page.url}\n${page.text.slice(0, 28000)}\n${isYouTube ? '\nNOTE: This URL mode can use page text, metadata, and transcript/caption text only when the public page exposes it. It is not direct frame-by-frame video playback.' : ''}`;
                webSourceLabel = `${isYouTube ? 'YouTube' : 'Web'}: ${page.title}`;
            } catch (err) {
                return error(err instanceof Error ? err.message : 'Could not read that web page.', 422);
            }
        } else if (tool === 'Web Search') {
            try {
                const results = await searchWeb(question, false);
                webContext = `LIVE WEB SEARCH\n${results.map((item, index) => `RESULT ${index + 1}: ${item.title}\nURL: ${item.url}\n${item.content}`).join('\n\n---\n\n').slice(0, 32000)}`;
                webSourceLabel = `Web search: ${question.slice(0, 90)}`;
            } catch (err) {
                return error(err instanceof Error ? err.message : 'Live web search failed.', 422);
            }
        }
        const toolInstruction: Record<string, string> = {
            'Record Search': 'Answer the question directly from the record and rank the most relevant supporting sources.',
            'Gap Finder': 'Identify missing records, unsupported links, unanswered questions, and the highest-value evidence to obtain next.',
            'Quote Check': 'Check whether proposed wording is exact source language or a paraphrase. Never convert a paraphrase into a quotation.',
            'Packet Assurance': 'Assess provenance, source coverage, contradictions, unsupported claims, and reviewer-readiness without deciding merits.',
            'Timeline Builder': 'Build a source-backed chronology. Flag date conflicts, long gaps, and events whose timing is only reported rather than independently documented.',
            'Rebuttal Lab': 'Compare adverse evidence with contrary source evidence. Draft restrained reconciliation points without inventing motives, bad faith, or medical causation.',
            'Web Research': 'Read the supplied public URL, answer from that page, and compare it with the uploaded record while keeping web reference material distinct from claimant evidence.',
            'Web Search': 'Search the live public web, synthesize the strongest relevant results, cite page titles and URLs, and compare them with uploaded evidence without treating search results as claimant evidence.',
            'YouTube & Video': 'For a YouTube URL, analyze public page text, metadata, and transcript/caption text when exposed. State clearly when direct audiovisual content is unavailable. For uploaded video, the multimodal route handles representative visual frames.',
        };
        let result;
        try {
            result = await resilientGenerate({
                system: ELIAS_PLAYBOOK,
                prompt: `WORK SPEED: ${speed}\nACTIVE PLUGIN: ${tool}\nTASK: ${toolInstruction[tool] ?? toolInstruction['Record Search']}\n\nCASE MEMORY\n${memoryText}\n\nSOURCE RECORD\n${textContext(docs, question)}\n\n${webContext}\n\nRECENT CHAT\n${recent.slice(-9000)}\n\nUSER QUESTION\n${question}`,
                speed,
                maxTokens: outputTokens(speed, 1700),
                temperature: 0.15,
                label: 'Elias Copilot',
            });
        } catch (err) {
            return error(err instanceof Error ? err.message : 'Elias could not finish that request.', 422);
        }
        const answer = result.text.trim();
        const sources = docs.filter((doc) => answer.includes(`[${doc.name}]`)).map((doc) => doc.name);
        if (webSourceLabel) sources.push(webSourceLabel);
        const record: ChatRecord = { threadId, question, answer, tool, speed, sources, createdAt: new Date().toISOString() };
        await db.add(tables(userId).chats, [record]);
        return json({ message: record, playbook: 'Elias Evidence Playbook v7' });
    }],
    'POST /api/review': [requireAuth(), async (ctx) => {
        const body = ctx.body as { speed?: WorkMode };
        const speed: WorkMode = body.speed === 'Quick' || body.speed === 'Deep' ? body.speed : 'Standard';
        const userId = ctx.user!.userId;
        const docs = await getDocuments(userId);
        if (!docs.length) return error('Upload at least one document before running Case Review.', 400);
        const memory = await getMemory(userId);
        const reviewQuery = `${memory?.goal ?? ''} service connection chronology objective findings functional impact adverse evidence contradictions duty medical examinations`;
        try {
            const generated = await resilientGenerate({
                system: `${ELIAS_PLAYBOOK}\nReturn concise, structured, UI-ready review findings only from supplied sources. The recordSignal must describe evidence coverage and reconciliation needs, never predict entitlement or a rating.`,
                prompt: `WORK SPEED: ${speed}\nCASE GOAL: ${memory?.goal ?? ''}\n\nReview the record for the strongest documented evidence, chronology, gaps, adverse-versus-supporting tensions, functional relevance, and major reviewer issues. Use short card-ready language. Reference filenames in source fields. Do not manufacture page numbers or certainty.\n\n${textContext(docs, reviewQuery)}`,
                schema: {
                    type: 'object',
                    properties: {
                        summary: { type: 'string' },
                        recordSignal: { type: 'string' },
                        strongestEvidence: { type: 'array', items: { type: 'object', properties: { title: { type: 'string' }, finding: { type: 'string' }, source: { type: 'string' }, whyItMatters: { type: 'string' }, kind: { type: 'string' } }, required: ['title', 'finding', 'source', 'whyItMatters', 'kind'] } },
                        gaps: { type: 'array', items: { type: 'object', properties: { priority: { type: 'string' }, gap: { type: 'string' }, whyItMatters: { type: 'string' }, nextStep: { type: 'string' } }, required: ['priority', 'gap', 'whyItMatters', 'nextStep'] } },
                        tensions: { type: 'array', items: { type: 'object', properties: { adverse: { type: 'string' }, supporting: { type: 'string' }, source: { type: 'string' }, reconcile: { type: 'string' } }, required: ['adverse', 'supporting', 'source', 'reconcile'] } },
                        issues: { type: 'array', items: { type: 'object', properties: { issue: { type: 'string' }, status: { type: 'string' }, note: { type: 'string' } }, required: ['issue', 'status', 'note'] } },
                        timeline: { type: 'array', items: { type: 'object', properties: { date: { type: 'string' }, event: { type: 'string' }, source: { type: 'string' }, significance: { type: 'string' } }, required: ['date', 'event', 'source', 'significance'] } },
                    },
                    required: ['summary', 'recordSignal', 'strongestEvidence', 'gaps', 'tensions', 'issues', 'timeline'],
                },
                speed,
                maxTokens: outputTokens(speed, 3000),
                temperature: 0.06,
                label: 'Case Review',
            });
            let review: unknown;
            try { review = JSON.parse(generated.text); } catch { review = { summary: generated.text, recordSignal: 'Structured review partially available', strongestEvidence: [], gaps: [], tensions: [], issues: [], timeline: [] }; }
            return json({ review, speed });
        } catch (err) {
            return error(err instanceof Error ? err.message : 'Case Review could not finish this record.', 422);
        }
    }],
    'POST /api/packet': [requireAuth(), async (ctx) => {
        const body = ctx.body as { style?: string; speed?: WorkMode };
        const speed: WorkMode = body.speed === 'Quick' || body.speed === 'Deep' ? body.speed : 'Standard';
        const userId = ctx.user!.userId;
        const docs = await getDocuments(userId);
        if (!docs.length) return error('Upload at least one document before generating a packet.', 400);
        const memory = await getMemory(userId);
        const style = String(body.style ?? 'Visual evidence review');
        const packetQuery = `${memory?.goal ?? ''} chronology strongest objective evidence functional reliability adverse evidence medical service records examinations nexus aggravation`;
        try {
            const generated = await resilientGenerate({
                system: `${ELIAS_PLAYBOOK}\nDraft a reviewer-ready evidence packet as structured data for a visual evidence product. This is an organizing draft, not legal or medical advice. Clearly mark uncertainty and adverse evidence. Do not predict entitlement or rating percentage.`,
                prompt: `WORK SPEED: ${speed}\nSTYLE: ${style}\nCASE: ${memory?.caseLabel ?? 'Untitled case'}\nGOAL: ${memory?.goal ?? ''}\nNOTES: ${memory?.notes ?? ''}\n\nBuild concise packet sections suitable for a visual reviewer interface: executive summary, chronology, strongest evidence, functional reliability, adverse evidence with record response, missing-evidence plan, reviewer checklist. Cite filenames in source fields and material functional-impact items when possible.\n\nSOURCE RECORD\n${textContext(docs, packetQuery)}`,
                schema: {
                    type: 'object',
                    properties: {
                        title: { type: 'string' },
                        subtitle: { type: 'string' },
                        executiveSummary: { type: 'string' },
                        chronology: { type: 'array', items: { type: 'object', properties: { date: { type: 'string' }, event: { type: 'string' }, source: { type: 'string' }, significance: { type: 'string' } }, required: ['date', 'event', 'source', 'significance'] } },
                        strongestEvidence: { type: 'array', items: { type: 'object', properties: { title: { type: 'string' }, finding: { type: 'string' }, source: { type: 'string' }, whyItMatters: { type: 'string' }, kind: { type: 'string' } }, required: ['title', 'finding', 'source', 'whyItMatters', 'kind'] } },
                        functionalImpact: { type: 'array', items: { type: 'string' } },
                        adverseEvidence: { type: 'array', items: { type: 'object', properties: { adverse: { type: 'string' }, supporting: { type: 'string' }, source: { type: 'string' }, reconcile: { type: 'string' } }, required: ['adverse', 'supporting', 'source', 'reconcile'] } },
                        missingEvidencePlan: { type: 'array', items: { type: 'object', properties: { priority: { type: 'string' }, gap: { type: 'string' }, whyItMatters: { type: 'string' }, nextStep: { type: 'string' } }, required: ['priority', 'gap', 'whyItMatters', 'nextStep'] } },
                        reviewerChecklist: { type: 'array', items: { type: 'string' } },
                    },
                    required: ['title', 'subtitle', 'executiveSummary', 'chronology', 'strongestEvidence', 'functionalImpact', 'adverseEvidence', 'missingEvidencePlan', 'reviewerChecklist'],
                },
                speed,
                maxTokens: outputTokens(speed, 4200),
                temperature: 0.08,
                label: 'Packet Studio',
            });
            let packet: Record<string, unknown>;
            try { packet = JSON.parse(generated.text) as Record<string, unknown>; } catch { packet = { title: memory?.caseLabel || 'Evidence Review Packet', subtitle: style, executiveSummary: generated.text, chronology: [], strongestEvidence: [], functionalImpact: [], adverseEvidence: [], missingEvidencePlan: [], reviewerChecklist: [] }; }
            packet.sourceAppendix = docs.slice(0, 60).map((doc) => doc.name);
            return json({ packet, speed });
        } catch (err) {
            return error(err instanceof Error ? err.message : 'Packet Studio could not finish this record.', 422);
        }
    }],
});