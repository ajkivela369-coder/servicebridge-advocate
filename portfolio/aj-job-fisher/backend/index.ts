import { ai, db, error, json, requireAuth, router } from '@appdeploy/sdk';

type ScoreComponents = {
  hardQualifications: number;
  backgroundMatch: number;
  flexibilityFit: number;
  compensationFit: number;
  domainRelevance: number;
  applicationFriction: number;
  strategicValue: number;
};

type JobRecord = {
  company: string;
  title: string;
  location: string;
  employmentType: string;
  compensation: string;
  source: string;
  sourceUrl: string;
  directUrl: string;
  remoteEligible: boolean;
  requiredCredentialsVerified: boolean;
  travelPercent: number;
  score: number;
  scoreComponents: ScoreComponents;
  stopConditions: string[];
  concerns: string;
  notes: string;
  disposition: string;
  firstSeen: string;
  lastVerified: string;
  appliedAt: string;
  confirmationNumber: string;
  resumeVersion: string;
  followUpDate: string;
  atsKeywords: string[];
  summary: string;
  schedule: string;
  remoteEvidence: string;
  requiredCredentials: string[];
  preferredCredentials: string[];
  applicationRisks: string[];
  payFloorStatus: string;
  applicationPackage: string;
  packageGeneratedAt: string;
};

type ScanRecord = {
  createdAt: string;
  source: string;
  url: string;
  reviewed: number;
  newLive: number;
  strong: number;
  blocked: number;
  duplicates: number;
  label: string;
};

type InboxRecord = {
  sender: string;
  company: string;
  role: string;
  subject: string;
  receivedAt: string;
  type: string;
  actionNeeded: string;
  deadline: string;
  summary: string;
  suggestedReply: string;
  rawPreview: string;
};

type ParsedJob = {
  company?: string;
  title?: string;
  location?: string;
  employmentType?: string;
  compensation?: string;
  remoteEligibleForNewHampshire?: boolean;
  remoteEligibilityEvidence?: string;
  travelKnown?: boolean;
  travelPercent?: number;
  hardCredentialMismatch?: boolean;
  requiredCredentials?: string[];
  preferredCredentials?: string[];
  schedule?: string;
  phoneIntensity?: string;
  physicalDemands?: string;
  applicationRisks?: string[];
  atsKeywords?: string[];
  summary?: string;
  domainTags?: string[];
  yearsExperienceRequired?: number;
  compensationFloorStatus?: string;
};

const limits: ScoreComponents = {
  hardQualifications: 25,
  backgroundMatch: 20,
  flexibilityFit: 15,
  compensationFit: 15,
  domainRelevance: 10,
  applicationFriction: 10,
  strategicValue: 5,
};

const verifiedProfile = [
  'B.S. in Neuroscience & Behavior.',
  'U.S. Army National Guard military medical background.',
  'Scientific and health-data analysis, writing, and evidence-review experience.',
  'NeuroEval project: Biology & Neuroscience AI Response Evaluator.',
  'HealthQA Auditor project: Safety-First Health-Science AI Evaluation.',
  'U.S. citizen; authorized to work in the United States without sponsorship.',
  'Standing preference: fully remote U.S., up to 10% travel, at least $20/hour or $40,000/year.',
  'Do not claim RN, LCSW, PA, MD/DO, PhD, active coding certification, security clearance, or any other credential not explicitly verified.',
].join(' ');

function cleanText(value: unknown, max = 500) {
  return typeof value === 'string' ? value.trim().slice(0, max) : '';
}

function safeNumber(value: unknown, min: number, max: number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? Math.min(max, Math.max(min, parsed)) : min;
}

function cleanList(value: unknown, maxItems = 30, maxText = 160) {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item): item is string => typeof item === 'string')
    .map(item => item.trim().slice(0, maxText))
    .filter(Boolean)
    .slice(0, maxItems);
}

function normalize(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, ' ')
    .trim();
}

function tableFor(prefix: string, userId: string) {
  return `${prefix}:${userId}`;
}

function riskToStop(risk: string) {
  const text = risk.toLowerCase();
  if (text.includes('medical exam') || text.includes('drug test'))
    return 'Drug test or medical exam';
  if (text.includes('disability') || text.includes('medical condition'))
    return 'Medical/disability question';
  if (text.includes('background')) return 'Background-check authorization';
  if (text.includes('driver') || text.includes('vehicle'))
    return 'Driving/vehicle requirement';
  if (text.includes('clearance')) return 'Security-clearance disclosure';
  if (text.includes('arbitration') || text.includes('binding agreement'))
    return 'Binding agreement';
  if (text.includes('reference')) return 'Reference request';
  if (text.includes('start date') || text.includes('availability'))
    return 'Start-date commitment';
  if (text.includes('relocation')) return 'Relocation requirement';
  return null;
}

function scoreParsedJob(parsed: ParsedJob): ScoreComponents {
  const years = safeNumber(parsed.yearsExperienceRequired, 0, 20);
  const hardQualifications = parsed.hardCredentialMismatch
    ? 4
    : years >= 6
      ? 13
      : years >= 4
        ? 18
        : 23;
  const tags = cleanList(parsed.domainTags, 12, 60).map(tag => tag.toLowerCase());
  const domainHits = tags.filter(tag =>
    ['healthcare', 'veteran', 'neuroscience', 'ai', 'research', 'health data', 'behavioral health'].some(target =>
      tag.includes(target)
    )
  ).length;
  const backgroundMatch = Math.min(20, 14 + domainHits * 2);
  let flexibilityFit = parsed.remoteEligibleForNewHampshire ? 15 : 0;
  const schedule = cleanText(parsed.schedule, 300).toLowerCase();
  const phone = cleanText(parsed.phoneIntensity, 120).toLowerCase();
  if (/(fixed|evening|weekend|overnight|on-call)/.test(schedule))
    flexibilityFit = Math.max(0, flexibilityFit - 3);
  if (phone.includes('high')) flexibilityFit = Math.max(0, flexibilityFit - 2);
  const payStatus = cleanText(parsed.compensationFloorStatus, 20).toLowerCase();
  const compensationFit = payStatus === 'yes' ? 15 : payStatus === 'no' ? 0 : 8;
  const domainRelevance = domainHits >= 2 ? 10 : domainHits === 1 ? 8 : 5;
  const risks = cleanList(parsed.applicationRisks, 20, 160);
  const applicationFriction = Math.max(2, 10 - risks.length * 2);
  const strategicValue = domainRelevance >= 8 ? 5 : 3;
  return {
    hardQualifications,
    backgroundMatch,
    flexibilityFit,
    compensationFit,
    domainRelevance,
    applicationFriction,
    strategicValue,
  };
}

function buildRecord(
  body: Record<string, unknown>,
  existing?: JobRecord
): JobRecord {
  const currentComponents = existing?.scoreComponents ?? {
    hardQualifications: 0,
    backgroundMatch: 0,
    flexibilityFit: 0,
    compensationFit: 0,
    domainRelevance: 0,
    applicationFriction: 0,
    strategicValue: 0,
  };
  const incomingComponents =
    body.scoreComponents && typeof body.scoreComponents === 'object'
      ? (body.scoreComponents as Record<string, unknown>)
      : {};
  const scoreComponents: ScoreComponents = {
    hardQualifications: safeNumber(
      incomingComponents.hardQualifications ?? currentComponents.hardQualifications,
      0,
      limits.hardQualifications
    ),
    backgroundMatch: safeNumber(
      incomingComponents.backgroundMatch ?? currentComponents.backgroundMatch,
      0,
      limits.backgroundMatch
    ),
    flexibilityFit: safeNumber(
      incomingComponents.flexibilityFit ?? currentComponents.flexibilityFit,
      0,
      limits.flexibilityFit
    ),
    compensationFit: safeNumber(
      incomingComponents.compensationFit ?? currentComponents.compensationFit,
      0,
      limits.compensationFit
    ),
    domainRelevance: safeNumber(
      incomingComponents.domainRelevance ?? currentComponents.domainRelevance,
      0,
      limits.domainRelevance
    ),
    applicationFriction: safeNumber(
      incomingComponents.applicationFriction ?? currentComponents.applicationFriction,
      0,
      limits.applicationFriction
    ),
    strategicValue: safeNumber(
      incomingComponents.strategicValue ?? currentComponents.strategicValue,
      0,
      limits.strategicValue
    ),
  };
  const score = Object.values(scoreComponents).reduce((sum, value) => sum + value, 0);
  const remoteEligible =
    typeof body.remoteEligible === 'boolean'
      ? body.remoteEligible
      : (existing?.remoteEligible ?? true);
  const requiredCredentialsVerified =
    typeof body.requiredCredentialsVerified === 'boolean'
      ? body.requiredCredentialsVerified
      : (existing?.requiredCredentialsVerified ?? true);
  const travelPercent = safeNumber(body.travelPercent ?? existing?.travelPercent ?? 0, 0, 100);
  const payFloorStatus = cleanText(body.payFloorStatus ?? existing?.payFloorStatus ?? 'unknown', 20) || 'unknown';
  const explicitStops =
    body.stopConditions === undefined
      ? (existing?.stopConditions ?? [])
      : cleanList(body.stopConditions, 20, 120);
  const derivedStops = [
    ...explicitStops,
    ...(remoteEligible ? [] : ['Remote eligibility failed']),
    ...(travelPercent <= 10 ? [] : ['Travel exceeds 10%']),
    ...(requiredCredentialsVerified ? [] : ['Required credentials not verified']),
    ...(payFloorStatus === 'no' ? ['Compensation below standing floor'] : []),
  ];
  const stopConditions = Array.from(new Set(derivedStops));
  let disposition = cleanText(body.disposition ?? existing?.disposition ?? '', 40);
  if (!disposition) {
    disposition =
      score >= 85
        ? stopConditions.length
          ? 'blocked'
          : 'ready'
        : score >= 75
          ? 'package_ready'
          : 'near_match';
  }
  if (stopConditions.length && disposition === 'ready') disposition = 'blocked';
  const now = new Date().toISOString();
  return {
    company: cleanText(body.company ?? existing?.company, 120),
    title: cleanText(body.title ?? existing?.title, 160),
    location: cleanText(body.location ?? existing?.location, 120),
    employmentType: cleanText(body.employmentType ?? existing?.employmentType, 80),
    compensation: cleanText(body.compensation ?? existing?.compensation, 160),
    source: cleanText(body.source ?? existing?.source, 100),
    sourceUrl: cleanText(body.sourceUrl ?? existing?.sourceUrl, 800),
    directUrl: cleanText(body.directUrl ?? existing?.directUrl, 800),
    remoteEligible,
    requiredCredentialsVerified,
    travelPercent,
    score,
    scoreComponents,
    stopConditions,
    concerns: cleanText(body.concerns ?? existing?.concerns, 2200),
    notes: cleanText(body.notes ?? existing?.notes, 4000),
    disposition,
    firstSeen: existing?.firstSeen ?? now,
    lastVerified: now,
    appliedAt: cleanText(body.appliedAt ?? existing?.appliedAt, 60),
    confirmationNumber: cleanText(body.confirmationNumber ?? existing?.confirmationNumber, 120),
    resumeVersion: cleanText(body.resumeVersion ?? existing?.resumeVersion, 200),
    followUpDate: cleanText(body.followUpDate ?? existing?.followUpDate, 60),
    atsKeywords:
      body.atsKeywords === undefined
        ? (existing?.atsKeywords ?? [])
        : cleanList(body.atsKeywords, 40, 80),
    summary: cleanText(body.summary ?? existing?.summary, 2400),
    schedule: cleanText(body.schedule ?? existing?.schedule, 600),
    remoteEvidence: cleanText(body.remoteEvidence ?? existing?.remoteEvidence, 1000),
    requiredCredentials:
      body.requiredCredentials === undefined
        ? (existing?.requiredCredentials ?? [])
        : cleanList(body.requiredCredentials, 30, 140),
    preferredCredentials:
      body.preferredCredentials === undefined
        ? (existing?.preferredCredentials ?? [])
        : cleanList(body.preferredCredentials, 30, 140),
    applicationRisks:
      body.applicationRisks === undefined
        ? (existing?.applicationRisks ?? [])
        : cleanList(body.applicationRisks, 30, 160),
    payFloorStatus,
    applicationPackage: cleanText(
      body.applicationPackage ?? existing?.applicationPackage,
      42000
    ),
    packageGeneratedAt: cleanText(
      body.packageGeneratedAt ?? existing?.packageGeneratedAt,
      60
    ),
  };
}

async function findDuplicate(userId: string, record: JobRecord) {
  const { items } = await db.list<JobRecord>(tableFor('jobs', userId), { limit: 100 });
  const incomingUrl = record.directUrl || record.sourceUrl;
  return items.find(item => {
    const itemUrl = item.directUrl || item.sourceUrl;
    const sameUrl = Boolean(incomingUrl && itemUrl && incomingUrl === itemUrl);
    const sameIdentity =
      normalize(item.company) === normalize(record.company) &&
      normalize(item.title) === normalize(record.title);
    return sameUrl || sameIdentity;
  });
}

function validHttpUrl(value: string) {
  try {
    const parsed = new URL(value);
    return parsed.protocol === 'http:' || parsed.protocol === 'https:';
  } catch {
    return false;
  }
}

function hostFromUrl(value: string) {
  try {
    return new URL(value).hostname.replace(/^www\./, '');
  } catch {
    return 'Direct';
  }
}

const jobSchema = {
  type: 'object',
  properties: {
    company: { type: 'string' },
    title: { type: 'string' },
    location: { type: 'string' },
    employmentType: { type: 'string' },
    compensation: { type: 'string' },
    remoteEligibleForNewHampshire: { type: 'boolean' },
    remoteEligibilityEvidence: { type: 'string' },
    travelKnown: { type: 'boolean' },
    travelPercent: { type: 'number' },
    hardCredentialMismatch: { type: 'boolean' },
    requiredCredentials: { type: 'array', items: { type: 'string' } },
    preferredCredentials: { type: 'array', items: { type: 'string' } },
    schedule: { type: 'string' },
    phoneIntensity: { type: 'string' },
    physicalDemands: { type: 'string' },
    applicationRisks: { type: 'array', items: { type: 'string' } },
    atsKeywords: { type: 'array', items: { type: 'string' } },
    summary: { type: 'string' },
    domainTags: { type: 'array', items: { type: 'string' } },
    yearsExperienceRequired: { type: 'number' },
    compensationFloorStatus: { type: 'string' },
  },
  required: [
    'company',
    'title',
    'location',
    'employmentType',
    'compensation',
    'remoteEligibleForNewHampshire',
    'remoteEligibilityEvidence',
    'travelKnown',
    'travelPercent',
    'hardCredentialMismatch',
    'requiredCredentials',
    'preferredCredentials',
    'schedule',
    'phoneIntensity',
    'physicalDemands',
    'applicationRisks',
    'atsKeywords',
    'summary',
    'domainTags',
    'yearsExperienceRequired',
    'compensationFloorStatus',
  ],
};

const inboxSchema = {
  type: 'object',
  properties: {
    sender: { type: 'string' },
    company: { type: 'string' },
    role: { type: 'string' },
    subject: { type: 'string' },
    type: { type: 'string' },
    actionNeeded: { type: 'string' },
    deadline: { type: 'string' },
    summary: { type: 'string' },
  },
  required: ['sender', 'company', 'role', 'subject', 'type', 'actionNeeded', 'deadline', 'summary'],
};


async function generateApplicationPackage(existing: JobRecord) {
  const result = await ai.generate({
    system:
      'You are an exacting ATS application writer. Never fabricate employment, dates, metrics, degrees, licenses, certifications, clearances, or clinical credentials. When a needed fact is missing, write [ADD VERIFIED DETAIL] instead of guessing.',
    prompt:
      `Create a tailored application package for this role. VERIFIED AJ PROFILE: ${verifiedProfile}\n\n` +
      `ROLE: ${existing.company} — ${existing.title}\nLOCATION: ${existing.location}\nCOMPENSATION: ${existing.compensation || 'Not listed'}\nSUMMARY: ${existing.summary || existing.notes}\nREQUIRED CREDENTIALS: ${(existing.requiredCredentials || []).join(', ') || 'Not extracted'}\nPREFERRED CREDENTIALS: ${(existing.preferredCredentials || []).join(', ') || 'Not extracted'}\nATS KEYWORDS: ${(existing.atsKeywords || []).join(', ') || 'Not extracted'}\nCONCERNS: ${existing.concerns || 'None recorded'}\n\n` +
      'Output clean Markdown with these sections: Targeted Professional Summary; Core Skills; Verified Experience/Project Bullets; ATS Keyword Map; One-Page Resume Draft; Concise Cover Letter; Screening Answer Guidance; Gaps / Do Not Claim. Keep the resume ATS-safe and use only verified facts above. Do not mention disability or medical conditions.',
    maxTokens: 3600,
    temperature: 0.25,
    thinkingMode: 'FAST',
  });
  const now = new Date().toISOString();
  return {
    ...existing,
    applicationPackage: result.text.slice(0, 42000),
    packageGeneratedAt: now,
    resumeVersion: `Job Fisher auto-package ${now.slice(0, 10)}`,
    lastVerified: now,
  };
}

export const handler = router({
  'GET /api/_healthcheck': [async () => json({ message: 'Success' })],
  'GET /api/dashboard': [
    requireAuth(),
    async ctx => {
      const userId = ctx.user!.userId;
      const [jobs, scans, inbox] = await Promise.all([
        db.list<JobRecord>(tableFor('jobs', userId), { limit: 100 }),
        db.list<ScanRecord>(tableFor('scans', userId), { limit: 60 }),
        db.list<InboxRecord>(tableFor('inbox', userId), { limit: 100 }),
      ]);
      return json({ jobs: jobs.items, scans: scans.items, inbox: inbox.items });
    },
  ],
  'POST /api/jobs': [
    requireAuth(),
    async ctx => {
      const body = (ctx.body ?? {}) as Record<string, unknown>;
      const record = buildRecord(body);
      if (!record.company || !record.title)
        return error('Company and role are required.', 400);
      if (await findDuplicate(ctx.user!.userId, record))
        return error('This opportunity is already in the ledger.', 409);
      const [id] = await db.add(tableFor('jobs', ctx.user!.userId), [record]);
      if (!id) return error('Could not create the candidate.', 500);
      return json({ job: { id, ...record } }, 201);
    },
  ],
  'PUT /api/jobs/:id': [
    requireAuth(),
    async ctx => {
      const table = tableFor('jobs', ctx.user!.userId);
      const [existing] = await db.get<JobRecord>(table, [ctx.params.id]);
      if (!existing) return error('Candidate not found.', 404);
      const body = (ctx.body ?? {}) as Record<string, unknown>;
      const record = buildRecord(body, existing);
      const [ok] = await db.update(table, [{ id: ctx.params.id, record }]);
      if (!ok) return error('Could not update the candidate.', 500);
      return json({ job: { id: ctx.params.id, ...record } });
    },
  ],
  'DELETE /api/jobs/:id': [
    requireAuth(),
    async ctx => {
      const [deleted] = await db.delete(tableFor('jobs', ctx.user!.userId), [ctx.params.id]);
      if (!deleted) return error('Candidate not found or could not be deleted.', 404);
      return json({ deleted: true });
    },
  ],
  'POST /api/ingest': [
    requireAuth(),
    async ctx => {
      const body = (ctx.body ?? {}) as { url?: string };
      const url = cleanText(body.url, 1200);
      if (!validHttpUrl(url)) return error('A valid http/https job URL is required.', 400);
      try {
        const scraped = await ai.scrape({ url });
        if (scraped.status >= 400) return error('The job page could not be read.', 502);
        const extracted = await ai.extract({
          content: scraped.text.slice(0, 60000),
          prompt:
            `Analyze this page as a possible job posting for AJ. Verified profile: ${verifiedProfile} ` +
            'Extract factual posting details only. remoteEligibleForNewHampshire must be true only when the posting clearly allows New Hampshire or nationwide U.S. remote work; otherwise false. ' +
            'hardCredentialMismatch should be true only for a required credential AJ is explicitly known not to hold. ' +
            'compensationFloorStatus must be yes, no, or unknown relative to $20/hour or $40,000/year. ' +
            'applicationRisks should list any background-check authorization, drug/medical exam, driving/vehicle, security clearance, relocation, references, arbitration/binding agreement, start-date/availability commitment, or similar application issue stated on the page. ' +
            'If this is not clearly a job posting, still extract the page title as title and hostname/site identity as company when possible, and keep summary clear that the page is not a conventional posting.',
          schema: jobSchema,
          maxRetries: 2,
          maxTokens: 2200,
          thinkingMode: 'FAST',
        });
        const parsed = extracted.data as ParsedJob;
        const risks = cleanList(parsed.applicationRisks, 30, 160);
        const riskStops = risks.map(riskToStop).filter((value): value is string => Boolean(value));
        const scoreComponents = scoreParsedJob(parsed);
        const source = hostFromUrl(url);
        const company = cleanText(parsed.company, 120) || source;
        const title = cleanText(parsed.title, 160) || cleanText(scraped.title, 160) || 'Imported opportunity';
        const concerns = [
          cleanText(parsed.remoteEligibilityEvidence, 500),
          cleanText(parsed.schedule, 300),
          cleanText(parsed.physicalDemands, 300),
          cleanText(parsed.phoneIntensity, 120) ? `Phone intensity: ${cleanText(parsed.phoneIntensity, 120)}` : '',
        ]
          .filter(Boolean)
          .join(' · ');
        const record = buildRecord({
          company,
          title,
          location: cleanText(parsed.location, 120) || 'Not stated',
          employmentType: cleanText(parsed.employmentType, 80) || 'Not stated',
          compensation: cleanText(parsed.compensation, 160),
          source,
          sourceUrl: url,
          directUrl: url,
          remoteEligible: Boolean(parsed.remoteEligibleForNewHampshire),
          requiredCredentialsVerified: !Boolean(parsed.hardCredentialMismatch),
          travelPercent: parsed.travelKnown ? safeNumber(parsed.travelPercent, 0, 100) : 0,
          scoreComponents,
          stopConditions: riskStops,
          concerns,
          notes: cleanText(parsed.summary, 2400),
          atsKeywords: cleanList(parsed.atsKeywords, 40, 80),
          summary: cleanText(parsed.summary, 2400),
          schedule: cleanText(parsed.schedule, 600),
          remoteEvidence: cleanText(parsed.remoteEligibilityEvidence, 1000),
          requiredCredentials: cleanList(parsed.requiredCredentials, 30, 140),
          preferredCredentials: cleanList(parsed.preferredCredentials, 30, 140),
          applicationRisks: risks,
          payFloorStatus: cleanText(parsed.compensationFloorStatus, 20).toLowerCase() || 'unknown',
        });
        if (await findDuplicate(ctx.user!.userId, record))
          return error('This opportunity is already in the ledger.', 409);
        const [id] = await db.add(tableFor('jobs', ctx.user!.userId), [record]);
        if (!id) return error('Could not save the analyzed opportunity.', 500);
        let savedRecord = record;
        // Every qualified lead lands with a tailored resume/application package already prepared.
        // 75–84: one-click package. 85+: package is prepared immediately for the application queue.
        if (record.score >= 75 && record.remoteEligible && record.requiredCredentialsVerified && record.payFloorStatus !== 'no') {
          try {
            savedRecord = await generateApplicationPackage(record);
            await db.update(tableFor('jobs', ctx.user!.userId), [{ id, record: savedRecord }]);
          } catch {
            // Discovery must never fail merely because package generation is temporarily unavailable.
          }
        }
        const scan: ScanRecord = {
          createdAt: new Date().toISOString(),
          source,
          url,
          reviewed: 1,
          newLive: 1,
          strong: record.score >= 85 ? 1 : 0,
          blocked: record.stopConditions.length ? 1 : 0,
          duplicates: 0,
          label: `${company} — ${title}`.slice(0, 220),
        };
        const [scanId] = await db.add(tableFor('scans', ctx.user!.userId), [scan]);
        return json({ job: { id, ...savedRecord }, scan: scanId ? { id: scanId, ...scan } : null });
      } catch (err) {
        const rpcError = err as { statusCode?: number; responseText?: string };
        if (rpcError?.statusCode && rpcError.responseText)
          return error(`Job analysis failed (${rpcError.statusCode}): ${rpcError.responseText.slice(0, 300)}`, 502);
        return error('Job analysis failed. The page may block automated reading or AI extraction.', 502);
      }
    },
  ],
  'POST /api/jobs/:id/package': [
    requireAuth(),
    async ctx => {
      const table = tableFor('jobs', ctx.user!.userId);
      const [existing] = await db.get<JobRecord>(table, [ctx.params.id]);
      if (!existing) return error('Candidate not found.', 404);
      try {
        const updated = await generateApplicationPackage(existing);
        const [ok] = await db.update(table, [{ id: ctx.params.id, record: updated }]);
        if (!ok) return error('Could not save the generated package.', 500);
        return json({ job: { id: ctx.params.id, ...updated } });
      } catch (err) {
        const rpcError = err as { statusCode?: number; responseText?: string };
        if (rpcError?.statusCode && rpcError.responseText)
          return error(`Package generation failed (${rpcError.statusCode}).`, 502);
        return error('Package generation failed.', 502);
      }
    },
  ],
  'POST /api/inbox/parse': [
    requireAuth(),
    async ctx => {
      const body = (ctx.body ?? {}) as { text?: string };
      const text = cleanText(body.text, 16000);
      if (text.length < 20) return error('Paste the recruiter or hiring email first.', 400);
      try {
        const extracted = await ai.extract({
          content: text,
          prompt:
            'Extract the hiring-message details. type should be one of recruiter outreach, assessment, interview, request for information, status update, rejection, or other. actionNeeded should be a short concrete next action. deadline should be exact if stated, otherwise blank. Do not invent missing company or role information.',
          schema: inboxSchema,
          maxRetries: 2,
          maxTokens: 1200,
          thinkingMode: 'FAST',
        });
        const parsed = extracted.data as Record<string, unknown>;
        const reply = await ai.generate({
          system:
            'Draft concise professional hiring replies. Do not accept binding terms, disclose medical/disability information, invent qualifications, or make start-date/salary commitments unless explicitly provided.',
          prompt:
            `Draft a reply to this hiring message using the extracted context. Sender: ${cleanText(parsed.sender, 160)}. Company: ${cleanText(parsed.company, 160)}. Role: ${cleanText(parsed.role, 160)}. Subject: ${cleanText(parsed.subject, 200)}. Action needed: ${cleanText(parsed.actionNeeded, 500)}. Message summary: ${cleanText(parsed.summary, 1200)}. Keep it warm, direct, and under 180 words. If scheduling is requested but no availability is provided, ask for available times rather than inventing availability.`,
          maxTokens: 500,
          temperature: 0.25,
          thinkingMode: 'FAST',
        });
        const record: InboxRecord = {
          sender: cleanText(parsed.sender, 160),
          company: cleanText(parsed.company, 160),
          role: cleanText(parsed.role, 160),
          subject: cleanText(parsed.subject, 220),
          receivedAt: new Date().toISOString(),
          type: cleanText(parsed.type, 80) || 'other',
          actionNeeded: cleanText(parsed.actionNeeded, 700),
          deadline: cleanText(parsed.deadline, 120),
          summary: cleanText(parsed.summary, 1800),
          suggestedReply: reply.text.slice(0, 5000),
          rawPreview: text.slice(0, 1200),
        };
        const [id] = await db.add(tableFor('inbox', ctx.user!.userId), [record]);
        if (!id) return error('Could not save the recruiter message.', 500);
        return json({ message: { id, ...record } }, 201);
      } catch (err) {
        const rpcError = err as { statusCode?: number; responseText?: string };
        if (rpcError?.statusCode && rpcError.responseText)
          return error(`Recruiter message analysis failed (${rpcError.statusCode}).`, 502);
        return error('Recruiter message analysis failed.', 502);
      }
    },
  ],
  'DELETE /api/inbox/:id': [
    requireAuth(),
    async ctx => {
      const [deleted] = await db.delete(tableFor('inbox', ctx.user!.userId), [ctx.params.id]);
      if (!deleted) return error('Message not found or could not be dismissed.', 404);
      return json({ deleted: true });
    },
  ],
});
