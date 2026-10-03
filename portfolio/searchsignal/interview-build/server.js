import express from 'express';
import * as cheerio from 'cheerio';
import dns from 'node:dns/promises';
import net from 'node:net';
import path from 'node:path';
import fs from 'node:fs';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer-core';
import chromium from '@sparticuz/chromium';

const app = express();
const PORT = process.env.PORT || 3000;

const ROOT = path.dirname(fileURLToPath(import.meta.url));

app.disable('x-powered-by');
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('Referrer-Policy', 'no-referrer');
  res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
  res.setHeader('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'");
  if (req.path.startsWith('/api/')) res.setHeader('Cache-Control', 'no-store');
  next();
});
app.use(express.json({ limit: '200kb' }));
app.use(express.static(path.join(ROOT, 'public')));

function isPrivateIp(ip) {
  if (net.isIPv4(ip)) {
    const p = ip.split('.').map(Number);
    return p[0] === 10 || p[0] === 127 || p[0] === 0 ||
      (p[0] === 169 && p[1] === 254) ||
      (p[0] === 172 && p[1] >= 16 && p[1] <= 31) ||
      (p[0] === 192 && p[1] === 168);
  }
  const s = ip.toLowerCase();
  return s === '::1' || s === '::' || s.startsWith('fc') ||
    s.startsWith('fd') || s.startsWith('fe80:') || s.startsWith('::ffff:127.');
}

async function validateUrl(raw) {
  let url;
  try { url = new URL(raw); } catch { throw new Error('Enter a valid http(s) URL.'); }
  if (!['http:', 'https:'].includes(url.protocol)) throw new Error('Only http and https URLs are allowed.');
  if (['localhost', '0.0.0.0'].includes(url.hostname.toLowerCase())) throw new Error('Local/private targets are blocked.');
  const records = await dns.lookup(url.hostname, { all: true });
  if (!records.length || records.some((r) => isPrivateIp(r.address))) throw new Error('Private or unroutable targets are blocked.');
  return url;
}

async function fetchHtml(raw) {
  let current = await validateUrl(raw);
  for (let i = 0; i < 5; i++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 9000);
    let response;
    try {
      response = await fetch(current, {
        redirect: 'manual',
        signal: controller.signal,
        headers: { 'user-agent': 'SearchSignalPortfolioAudit/1.0 (+independent demo)' }
      });
    } finally {
      clearTimeout(timer);
    }
    if (response.status >= 300 && response.status < 400 && response.headers.get('location')) {
      current = await validateUrl(new URL(response.headers.get('location'), current).toString());
      continue;
    }
    const contentType = (response.headers.get('content-type') || '').toLowerCase();
    if (!contentType.includes('text/html') && !contentType.includes('application/xhtml')) {
      throw new Error('Target did not return HTML.');
    }
    const buffer = Buffer.from(await response.arrayBuffer());
    if (buffer.length > 2_000_000) throw new Error('Page exceeds the 2 MB audit limit.');
    return { html: buffer.toString('utf8'), status: response.status, finalUrl: current.toString() };
  }
  throw new Error('Too many redirects.');
}

function meta($, selector) { return $(selector).first().attr('content') || ''; }
function weightedScore(checks) {
  const applicable = checks.filter((c) => c.applicable !== false);
  const total = applicable.reduce((s, c) => s + c.weight, 0);
  const earned = applicable.reduce((s, c) => s + (c.ok ? c.weight : 0), 0);
  return total ? Math.round((earned / total) * 100) : null;
}
function issue(severity, label, evidence, fix) { return { severity, label, evidence, fix }; }

app.get('/api/health', (_req, res) => res.json({ ok: true, service: 'SearchSignal' }));
function clampFactor(value) {
  const n = Number(value);
  return Number.isFinite(n) ? Math.max(1, Math.min(5, n)) : 1;
}

function priorityScore(item) {
  const impact = clampFactor(item.impact);
  const gap = clampFactor(item.gap);
  const competition = clampFactor(item.competition);
  const demand = clampFactor(item.demand);
  const staff = clampFactor(item.staff);
  const effort = clampFactor(item.effort);
  const supportNeed = 6 - staff;
  return (impact * 2) + (gap * 1.5) + competition + (demand * 1.5) + supportNeed - (effort * 1.25);
}

function priorityPhase(score) {
  return score >= 24 ? 'Now' : score >= 18 ? 'Next' : 'Later';
}

function recommendationDraft(text) {
  const clean = String(text || '').replace(/\s+/g, ' ').trim().slice(0, 12000);
  const first = clean.split(/[.!?]/)[0].slice(0, 155);
  return {
    opening: first ? first + '.' : '',
    outline: ['What this page covers', 'Key facts', 'Process or requirements', 'FAQs', 'Sources or contact'],
    geo: ['Explicit entity naming', 'Updated date', 'Responsible author/editor', 'Source links', 'Concise Q&A blocks', 'Truthful structured data'],
    seo: ['Unique title', 'Descriptive meta description', 'One H1', 'Descriptive internal links', 'Meaningful alt text', 'Canonical review'],
    boundary: 'Draft guidance only. A human editor should verify facts, claims, accessibility, and institutional policy before publication.'
  };
}

app.post('/api/prioritize', (req, res) => {
  const items = Array.isArray(req.body?.items) ? req.body.items.slice(0, 50) : [];
  const ranked = items.map((item, index) => {
    const score = priorityScore(item);
    return { index, score: Number(score.toFixed(1)), phase: priorityPhase(score) };
  }).sort((a, b) => b.score - a.score);
  res.json({ ranked });
});

app.post('/api/recommendations', (req, res) => {
  res.json(recommendationDraft(req.body?.text));
});


function cleanText(value) {
  return String(value || '').replace(/\s+/g, ' ').trim();
}

function uniqueText(values) {
  return [...new Set(values.map(cleanText).filter(Boolean))];
}

function elementValue($, selector) {
  const el = $(selector).first();
  if (!el.length) return '';
  return cleanText(el.attr('content') || el.attr('href') || el.text());
}

function itemValue($, prop) {
  return elementValue($, '[itemprop="'+prop+'"]');
}

function parseIsoDurationSeconds(raw) {
  const match = String(raw || '').match(/^P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?)?$/i);
  if (!match) return null;
  return Math.round((Number(match[1] || 0) * 86400) + (Number(match[2] || 0) * 3600) + (Number(match[3] || 0) * 60) + Number(match[4] || 0));
}

function chapterLabel(text) {
  const parts = String(text || '').split(/\n+/).map(cleanText).filter(Boolean)
    .filter((x) => !/^(?:\d{1,2}:)?\d{1,2}:\d{2}$/.test(x))
    .filter((x) => !/^(view all|chapters?)$/i.test(x));
  if (!parts.length) return '';
  return parts.sort((a, b) => b.length - a.length)[0].slice(0, 180);
}

function transcriptLabel(text) {
  return cleanText(String(text || '').replace(/^(?:\d{1,2}:)?\d{1,2}:\d{2}\s*/, '')).slice(0, 600);
}

function extractVideoEvidence($, base, bodyText) {
  const ogType = meta($, 'meta[property="og:type"]');
  const title = cleanText(
    meta($, 'meta[name="title"]') ||
    meta($, 'meta[property="og:title"]') ||
    elementValue($, '[itemtype*="VideoObject"] [itemprop="name"]') ||
    ''
  );
  const description = cleanText(
    meta($, 'meta[name="description"]') ||
    meta($, 'meta[property="og:description"]') ||
    elementValue($, '[itemtype*="VideoObject"] [itemprop="description"]') ||
    itemValue($, 'description')
  );
  const authorRoot = $('[itemprop="author"]').first();
  const creator = cleanText(
    authorRoot.find('[itemprop="name"]').first().attr('content') ||
    authorRoot.find('[itemprop="name"]').first().text() ||
    meta($, 'meta[name="author"]') ||
    ''
  );
  const duration = itemValue($, 'duration');
  const datePublished = itemValue($, 'datePublished') || meta($, 'meta[property="article:published_time"]');
  const uploadDate = itemValue($, 'uploadDate') || datePublished;
  const thumbnailUrl = itemValue($, 'thumbnailUrl') || meta($, 'meta[property="og:image"]');
  const embedUrl = itemValue($, 'embedUrl') || meta($, 'meta[property="og:video:url"]') || meta($, 'meta[name="twitter:player"]');
  const tags = uniqueText($('meta[property="og:video:tag"]').map((_, e) => $(e).attr('content')).get()).slice(0, 40);
  const interactions = uniqueText($('[itemprop="userInteractionCount"]').map((_, e) => $(e).attr('content') || $(e).text()).get()).slice(0, 10);

  const chapters = uniqueText($('ytd-macro-markers-list-item-renderer, [data-searchsignal-chapter]').map((_, e) => {
    return $(e).attr('data-searchsignal-chapter') || chapterLabel($(e).text());
  }).get()).filter((x) => x.length >= 2).slice(0, 80);

  const transcriptSegments = uniqueText($('ytd-transcript-segment-renderer, [data-searchsignal-transcript]').map((_, e) => {
    return $(e).attr('data-searchsignal-transcript') || transcriptLabel($(e).text());
  }).get()).filter((x) => x.length >= 2).slice(0, 500);

  const transcriptUi = $('ytd-video-description-transcript-section-renderer, ytd-transcript-renderer').length > 0 ||
    /(?:show|view|open)\s+transcript/i.test(bodyText) ||
    /\btranscript\b/i.test($('h2,h3,button').map((_,e)=>$(e).text()).get().join(' '));

  const microdataVideo = $('[itemtype*="VideoObject"], [itemprop="duration"], [itemprop="thumbnailUrl"], [itemprop="embedUrl"]').length > 0;
  const openGraphVideo = /^video(?:\.|$)/i.test(ogType) || Boolean(meta($, 'meta[property="og:video:url"]'));
  const playerMetadata = Boolean(embedUrl || meta($, 'meta[name="twitter:player"]'));
  const primaryText = uniqueText([title, description, creator, ...chapters, ...transcriptSegments]).join(' ');
  const primaryWordCount = primaryText ? primaryText.split(/\s+/).filter(Boolean).length : 0;
  const machineSignals = [
    openGraphVideo ? 'Open Graph video' : '',
    microdataVideo ? 'Video microdata' : '',
    playerMetadata ? 'Player/embed metadata' : '',
    thumbnailUrl ? 'Thumbnail reference' : '',
    duration ? 'Duration' : '',
    uploadDate ? 'Publication date' : ''
  ].filter(Boolean);

  return {
    title,
    description,
    creator,
    duration,
    durationSeconds: parseIsoDurationSeconds(duration),
    datePublished,
    uploadDate,
    thumbnailUrl,
    embedUrl,
    tags,
    interactions,
    chapters,
    transcript: {
      available: transcriptSegments.length > 0 || transcriptUi,
      loaded: transcriptSegments.length > 0,
      segments: transcriptSegments.length,
      wordCount: transcriptSegments.join(' ').split(/\s+/).filter(Boolean).length,
      sample: transcriptSegments.slice(0, 3)
    },
    metadata: {
      ogType,
      openGraphVideo,
      microdataVideo,
      playerMetadata,
      signals: machineSignals
    },
    primaryWordCount,
    platform: /(^|\.)youtube\.com$/i.test(base.hostname) ? 'YouTube' : (base.hostname || 'Unknown')
  };
}

function classifyContent($, base, raw, bodyText, wordCount, video) {
  const ogType = meta($, 'meta[property="og:type"]');
  const scriptCount = $('script').length;
  const videoMarkers = [
    /^video(?:\.|$)/i.test(ogType),
    Boolean(video.duration),
    Boolean(video.thumbnailUrl),
    Boolean(video.embedUrl),
    video.metadata.microdataVideo,
    /(^|\.)youtube\.com$/i.test(base.hostname) && base.pathname === '/watch'
  ].filter(Boolean).length;

  if (videoMarkers >= 2) {
    return { type: 'video', confidence: videoMarkers >= 4 ? 'high' : 'medium', evidence: videoMarkers+' video-specific signal(s)' };
  }
  if (/article/i.test(ogType) || $('article').length > 0) {
    return { type: 'article', confidence: 'medium', evidence: 'Article semantic/Open Graph signal' };
  }
  if (new URL(raw).hash || (wordCount < 120 && scriptCount >= 8) || ($('#app,#root,[data-reactroot]').length > 0 && scriptCount >= 5)) {
    return { type: 'application', confidence: 'medium', evidence: 'Client-rendered application shell signal' };
  }
  return { type: 'webpage', confidence: 'medium', evidence: 'General HTML document' };
}

function videoRubrics(video, noindex, canonicalOk) {
  const titleOk = video.title.length >= 20 && video.title.length <= 120;
  const descriptionOk = video.description.length >= 80;
  const machineReadable = video.metadata.signals.length >= 3;
  const primaryExtractable = video.primaryWordCount >= 80;
  return {
    seo: [
      { name: 'Indexable', ok: !noindex, weight: 12 },
      { name: 'Descriptive video title', ok: titleOk, weight: 14 },
      { name: 'Video description', ok: descriptionOk, weight: 12 },
      { name: 'Canonical', ok: canonicalOk, weight: 10 },
      { name: 'Creator / channel', ok: Boolean(video.creator), weight: 10 },
      { name: 'Published date', ok: Boolean(video.uploadDate || video.datePublished), weight: 8 },
      { name: 'Duration metadata', ok: Boolean(video.duration), weight: 8 },
      { name: 'Thumbnail metadata', ok: Boolean(video.thumbnailUrl), weight: 8 },
      { name: 'Player / embed metadata', ok: Boolean(video.embedUrl), weight: 7 },
      { name: 'Machine-readable video metadata', ok: machineReadable, weight: 7 },
      { name: 'Chapter structure', ok: video.chapters.length >= 3, weight: 4 }
    ],
    geo: [
      { name: 'Description context', ok: descriptionOk, weight: 14 },
      { name: 'Transcript discoverable', ok: video.transcript.available, weight: 10 },
      { name: 'Transcript text extractable', ok: video.transcript.loaded && video.transcript.wordCount >= 80, weight: 14 },
      { name: 'Chapter structure', ok: video.chapters.length >= 3, weight: 12 },
      { name: 'Creator identity', ok: Boolean(video.creator), weight: 10 },
      { name: 'Freshness date', ok: Boolean(video.uploadDate || video.datePublished), weight: 10 },
      { name: 'Machine-readable video metadata', ok: machineReadable, weight: 12 },
      { name: 'Topic / entity tags', ok: video.tags.length >= 3, weight: 8 },
      { name: 'Primary content extractability', ok: primaryExtractable, weight: 10 }
    ]
  };
}

function analyzeHtml(raw, html, status, finalUrl, retrieval = { mode: 'server-fetch', label: 'Server fetch', rendered: false }) {
  const $ = cheerio.load(html);
  const base = new URL(finalUrl);

  const title = $('title').first().text().trim();
  const description = meta($, 'meta[name="description"]');
  const canonical = $('link[rel="canonical"]').first().attr('href') || '';
  const robots = meta($, 'meta[name="robots"]');
  const lang = $('html').attr('lang') || '';
  const viewport = $('meta[name="viewport"]').attr('content') || '';
  const h1 = $('h1').map((_, e) => $(e).text().trim()).get();
  const h2 = $('h2').map((_, e) => $(e).text().trim()).get();
  const h3 = $('h3').map((_, e) => $(e).text().trim()).get();
  const bodyText = $('body').text().replace(/\s+/g, ' ').trim();
  const wordCount = bodyText ? bodyText.split(/\s+/).filter(Boolean).length : 0;

  const imageCount = $('img').length;
  const imagesWithAlt = $('img[alt]').filter((_, e) => String($(e).attr('alt') || '').trim().length > 0).length;
  const altCoverage = imageCount ? imagesWithAlt / imageCount : null;

  const hrefs = $('a[href]').map((_, e) => $(e).attr('href')).get();
  let internal = 0, external = 0, placeholders = 0;
  for (const href of hrefs) {
    if (!href || href === '#' || href.startsWith('javascript:')) { placeholders++; continue; }
    try {
      const u = new URL(href, base);
      if (['http:', 'https:'].includes(u.protocol)) {
        if (u.hostname === base.hostname) internal++; else external++;
      }
    } catch {}
  }

  const schemas = [];
  let invalidSchemaBlocks = 0;
  $('script[type="application/ld+json"]').each((_, e) => {
    try {
      const parsed = JSON.parse($(e).text());
      const arr = Array.isArray(parsed) ? parsed : [parsed];
      for (const item of arr) {
        if (item && item['@type']) {
          schemas.push(Array.isArray(item['@type']) ? item['@type'].join(', ') : item['@type']);
        }
      }
    } catch { invalidSchemaBlocks++; }
  });

  const generator = meta($, 'meta[name="generator"]');
  const wordpress = /wordpress/i.test(generator) || html.includes('/wp-content/') ||
    html.includes('/wp-includes/') || $('link[rel="https://api.w.org/"]').length > 0;

  const author = meta($, 'meta[name="author"]') || meta($, 'meta[property="article:author"]');
  const published = meta($, 'meta[property="article:published_time"]') || $('time[datetime]').first().attr('datetime') || '';
  const modified = meta($, 'meta[property="article:modified_time"]');
  const openGraph = Boolean(meta($, 'meta[property="og:title"]'));
  const twitter = Boolean(meta($, 'meta[name="twitter:card"]'));
  const questions = h2.concat(h3).filter((x) => x.endsWith('?')).length;
  const hasCitations = external >= 2 || /references|sources|citations/i.test(bodyText);
  const firstParagraph = $('main p, article p, body p').first().text().trim();
  const answerFirst = firstParagraph.length >= 60 && firstParagraph.length <= 500;
  const genericLinkPattern = /^(click here|here|read more|learn more|more|link)$/i;
  const genericLinkText = $('a[href]').filter((_, e) => genericLinkPattern.test($(e).text().replace(/\s+/g, ' ').trim())).length;
  const formControls = $('input:not([type="hidden"]), select, textarea').length;
  const unlabeledControls = $('input:not([type="hidden"]), select, textarea').filter((_, e) => {
    const el = $(e);
    const id = el.attr('id');
    return !(el.attr('aria-label') || el.attr('aria-labelledby') || (id && $('label[for="'+id+'"]').length) || el.closest('label').length);
  }).length;

  const video = extractVideoEvidence($, base, bodyText);
  const pageType = classifyContent($, base, raw, bodyText, wordCount, video);

  const normalizedTitle = title.toLowerCase();
  const normalizedBody = bodyText.toLowerCase();
  const errorTitlePattern = /(website temporarily unavailable|temporarily unavailable|service unavailable|access denied|request blocked|forbidden|too many requests|verify you are human|captcha|robot check|page not found|404 not found|internal server error)/i;
  const errorBodyPattern = /(website temporarily unavailable|service unavailable|access denied|request blocked|verify you are human|unusual traffic|captcha|cloudflare ray id|error 403|error 429|error 500|error 502|error 503|error 504)/i;
  const auditabilityReasons = [];
  if (status >= 400) auditabilityReasons.push('HTTP '+status+' response');
  if (errorTitlePattern.test(normalizedTitle)) auditabilityReasons.push('Error/challenge title detected: '+title);
  if (wordCount < 120 && errorBodyPattern.test(normalizedBody)) auditabilityReasons.push('Error/challenge response text detected');
  if (wordCount === 0 && pageType.type !== 'video') auditabilityReasons.push('No readable body text was returned');
  const scorable = auditabilityReasons.length === 0;
  const noindex = /noindex/i.test(robots);
  const canonicalOk = Boolean(canonical) && (() => {
    try { return new URL(canonical, base).hostname === base.hostname; } catch { return false; }
  })();
  const singleH1 = h1.length === 1;

  const webSeoRubric = [
    { name: 'Indexable', ok: !noindex, weight: 15 },
    { name: 'Title length', ok: title.length >= 20 && title.length <= 65, weight: 12 },
    { name: 'Meta description', ok: description.length >= 70 && description.length <= 170, weight: 10 },
    { name: 'Canonical', ok: canonicalOk, weight: 10 },
    { name: 'Single H1', ok: singleH1, weight: 10 },
    { name: 'Heading structure', ok: h2.length > 0, weight: 8 },
    { name: 'Image alt coverage', ok: imageCount ? altCoverage >= 0.8 : false, applicable: imageCount > 0, weight: 8 },
    { name: 'Internal links', ok: internal >= 3, weight: 7 },
    { name: 'Structured data', ok: schemas.length > 0 && invalidSchemaBlocks === 0, weight: 10 },
    { name: 'Mobile viewport', ok: Boolean(viewport), weight: 5 },
    { name: 'Language attribute', ok: Boolean(lang), weight: 5 }
  ];

  const webGeoRubric = [
    { name: 'Answer-first opening', ok: answerFirst, weight: 14 },
    { name: 'Extractable headings', ok: h2.length >= 2, weight: 12 },
    { name: 'Question-answer structure', ok: questions > 0, weight: 10 },
    { name: 'Structured data', ok: schemas.length > 0, weight: 12 },
    { name: 'Source/citation signals', ok: hasCitations, weight: 12 },
    { name: 'Author context', ok: Boolean(author), weight: 10 },
    { name: 'Freshness date', ok: Boolean(published || modified), weight: 10 },
    { name: 'Factual specificity', ok: wordCount >= 300, weight: 8 },
    { name: 'Accessible HTML text', ok: wordCount >= 150 && singleH1, weight: 7 },
    { name: 'Entity metadata', ok: Boolean(title && description), weight: 5 }
  ];

  const selectedRubrics = pageType.type === 'video' ? videoRubrics(video, noindex, canonicalOk) : { seo: webSeoRubric, geo: webGeoRubric };
  const findings = [];

  if (!scorable) {
    findings.push(issue('Critical', 'Page could not be audited reliably', auditabilityReasons.join(' · '), 'Retry later, use a different public page, or audit a page that allows server-side retrieval. SEO/GEO scores are intentionally suppressed for this response.'));
  } else if (pageType.type === 'video') {
    if (noindex) findings.push(issue('Critical', 'Video page is marked noindex', robots || 'robots=noindex', 'Confirm whether search indexing is intended before changing the directive.'));
    if (!video.title) findings.push(issue('Critical', 'Video title not detected', 'No video-specific title signal was found', 'Expose a descriptive video title in visible content and machine-readable metadata.'));
    else if (video.title.length < 20 || video.title.length > 120) findings.push(issue('High', 'Video title needs review', video.title, 'Use a specific human-readable title without applying ordinary webpage-title limits mechanically.'));
    if (!video.description) findings.push(issue('High', 'Video description not detected', 'No video-specific description signal was found', 'Provide a useful description that explains the subject and context.'));
    else if (video.description.length < 80) findings.push(issue('Medium', 'Video description is thin', video.description, 'Add enough context for users and machines to understand what the video covers.'));
    if (!canonical) findings.push(issue('High', 'Missing canonical', 'No canonical link detected', 'Expose the intended canonical watch URL.'));
    if (!video.creator) findings.push(issue('High', 'Creator / channel not detected', 'No creator identity was extracted', 'Expose the responsible creator or channel in visible and/or machine-readable metadata.'));
    if (!video.uploadDate && !video.datePublished) findings.push(issue('Medium', 'Publication date not detected', 'No upload/publication date signal was extracted', 'Expose a machine-readable publication date when appropriate.'));
    if (!video.duration) findings.push(issue('Medium', 'Duration metadata not detected', 'No duration signal was extracted', 'Expose machine-readable duration metadata for the video.'));
    if (!video.thumbnailUrl) findings.push(issue('Medium', 'Thumbnail metadata not detected', 'No primary thumbnail reference was extracted', 'Expose a representative thumbnail in video metadata.'));
    if (!video.embedUrl) findings.push(issue('Opportunity', 'Embed/player URL not detected', 'No player/embed URL signal was extracted', 'Expose a player/embed reference where appropriate.'));
    if (video.chapters.length < 3) findings.push(issue('Opportunity', 'Limited chapter structure', video.chapters.length+' chapter(s) detected', 'Add meaningful chapters when the video is long enough to benefit from navigation.'));
    if (!video.transcript.available) findings.push(issue('High', 'Transcript / caption signal not detected', 'No public transcript signal was found in the rendered content', 'Provide captions/transcript access where appropriate and verify it is discoverable.'));
    else if (!video.transcript.loaded) findings.push(issue('Opportunity', 'Transcript is discoverable but not loaded', 'A transcript interface was detected, but transcript text was not present in the captured DOM', 'Load the public transcript during a rendered audit when the platform permits it.'));
    if (video.tags.length < 3) findings.push(issue('Opportunity', 'Limited topic metadata', video.tags.length+' video topic tag(s) detected', 'Use specific topic/entity metadata where the platform supports it.'));
  } else {
    if (noindex) findings.push(issue('Critical', 'Page is marked noindex', robots || 'robots=noindex', 'Confirm whether indexing is intended; remove noindex only after owner approval.'));
    if (!title) findings.push(issue('Critical', 'Missing title', 'No <title> detected', 'Add a unique, descriptive title.'));
    else if (title.length < 20 || title.length > 65) findings.push(issue('High', 'Title length needs review', title, 'Use a concise, specific title that reflects page intent.'));
    if (!description) findings.push(issue('High', 'Missing meta description', 'No description detected', 'Write a plain-language summary useful in search snippets.'));
    if (!canonical) findings.push(issue('High', 'Missing canonical', 'No canonical link detected', 'Add a self-referential or intentionally selected canonical URL.'));
    if (!singleH1) findings.push(issue('High', 'H1 structure issue', h1.length + ' H1 elements detected', 'Use one clear page-level H1.'));
    if (schemas.length === 0) findings.push(issue('Medium', 'No JSON-LD structured data', 'No schema types detected', 'Add only schema.org markup that truthfully reflects visible content.'));
    if (invalidSchemaBlocks) findings.push(issue('High', 'Invalid JSON-LD', invalidSchemaBlocks + ' block(s) failed JSON parsing', 'Repair JSON syntax before publishing.'));
    if (imageCount && altCoverage < 0.8) findings.push(issue('Medium', 'Image alt coverage below 80%', imagesWithAlt + '/' + imageCount + ' images have meaningful alt text', 'Add concise alt text where images convey information.'));
    if (placeholders) findings.push(issue('Medium', 'Empty or placeholder links', placeholders + ' link(s)', 'Replace placeholder hrefs with valid destinations or buttons.'));
    if (!answerFirst) findings.push(issue('Opportunity', 'Opening may be hard for answer engines to extract', firstParagraph.slice(0, 220) || 'No opening paragraph found', 'Lead with a concise answer or definition before deeper detail.'));
    if (!hasCitations) findings.push(issue('Opportunity', 'Weak source/citation signals', external + ' external source links detected', 'Add authoritative source links or a references section when appropriate.'));
    if (!author) findings.push(issue('Opportunity', 'No clear author signal', 'No author metadata detected', 'Expose responsible author/editor when appropriate.'));
    if (genericLinkText) findings.push(issue('Medium', 'Non-descriptive link text', genericLinkText + ' link(s) use generic text', 'Replace generic link text with wording that describes the destination or action.'));
    if (unlabeledControls) findings.push(issue('High', 'Form controls need label review', unlabeledControls + '/' + formControls + ' visible control(s) lack an obvious label signal', 'Add programmatic labels and verify the form with accessibility testing.'));
  }

  const effectiveTitle = pageType.type === 'video' && video.title ? video.title : title;
  const effectiveDescription = pageType.type === 'video' && video.description ? video.description : description;
  const primaryContent = pageType.type === 'video'
    ? {
        source: 'video-specific evidence',
        wordCount: video.primaryWordCount,
        shellWordCount: wordCount,
        excludedShellWords: Math.max(0, wordCount - video.primaryWordCount),
        provenance: ['video title','video description','creator/channel','chapters','loaded transcript'].filter((x, i) => i < 5)
      }
    : { source: 'document body', wordCount, shellWordCount: wordCount, excludedShellWords: 0, provenance: ['HTML body'] };

  return {
    url: raw, finalUrl, status,
    title: effectiveTitle, description: effectiveDescription, canonical, robots, lang, viewport,
    retrieval,
    pageType,
    scoringModel: pageType.type === 'video' ? 'video-seo-geo-v1' : 'webpage-seo-geo-v1',
    primaryContent,
    wordCount: primaryContent.wordCount,
    shellWordCount: wordCount,
    headings: { h1, h2, h3 },
    links: { total: hrefs.length, internal, external, placeholders },
    images: { total: imageCount, withAlt: imagesWithAlt, coverage: altCoverage === null ? null : Math.round(altCoverage * 100) },
    schema: {
      types: [...new Set(schemas)],
      invalidBlocks: invalidSchemaBlocks,
      videoSignals: video.metadata.signals
    },
    video: pageType.type === 'video' ? video : null,
    signals: {
      wordpress,
      generator,
      author: pageType.type === 'video' ? video.creator : author,
      published: pageType.type === 'video' ? (video.uploadDate || video.datePublished) : published,
      modified,
      openGraph,
      twitter,
      questions,
      answerFirst,
      hasCitations
    },
    accessibilitySignals: { genericLinkText, formControls, unlabeledControls, note: 'Heuristic signals only; not an accessibility conformance determination.' },
    scores: {
      seo: scorable ? weightedScore(selectedRubrics.seo) : null,
      geo: scorable ? weightedScore(selectedRubrics.geo) : null
    },
    auditability: {
      scorable,
      classification: scorable ? 'content' : 'blocked_or_error',
      reasons: auditabilityReasons,
      note: scorable ? 'Response appears suitable for '+pageType.type+' scoring.' : 'SEO/GEO scores are suppressed because the retrieved response does not appear to be the intended content page.'
    },
    rubrics: {
      seo: selectedRubrics.seo.map(({ name, ok, applicable = true }) => ({ name, ok, applicable: scorable && applicable })),
      geo: selectedRubrics.geo.map(({ name, ok, applicable = true }) => ({ name, ok, applicable: scorable && applicable }))
    },
    findings
  };
}


app.post('/api/audit', async (req, res) => {
  try {
    const raw = String(req.body?.url || '').trim();
    const { html, status, finalUrl } = await fetchHtml(raw);
    res.json(analyzeHtml(raw, html, status, finalUrl, {
      mode: 'server-fetch',
      label: 'Server fetch',
      rendered: false
    }));
  } catch (err) {
    res.status(400).json({ error: err?.name === 'AbortError' ? 'Audit timed out.' : (err?.message || 'Audit failed.') });
  }
});


function localChromiumPath() {
  const candidates = process.platform === 'win32'
    ? [
        process.env.RENDER_CHROME_PATH,
        'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe',
        'C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe',
        'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
      ]
    : [process.env.RENDER_CHROME_PATH, '/usr/bin/google-chrome', '/usr/bin/chromium', '/usr/bin/chromium-browser'];
  return candidates.filter(Boolean).find((candidate) => fs.existsSync(candidate)) || null;
}

async function browserExecutablePath() {
  const local = localChromiumPath();
  if (local) return local;
  return chromium.executablePath();
}

async function publicRequestAllowed(raw, cache) {
  let u;
  try { u = new URL(raw); } catch { return false; }
  if (['data:', 'blob:'].includes(u.protocol)) return true;
  if (!['http:', 'https:'].includes(u.protocol)) return false;
  const host = u.hostname.toLowerCase();
  if (cache.has(host)) return cache.get(host);
  if (cache.size >= 80) return false;
  const promise = (async () => {
    if (['localhost', '0.0.0.0'].includes(host)) return false;
    if (net.isIP(host)) return !isPrivateIp(host);
    try {
      const records = await dns.lookup(host, { all: true });
      return records.length > 0 && !records.some((r) => isPrivateIp(r.address));
    } catch {
      return false;
    }
  })();
  cache.set(host, promise);
  return promise;
}

async function renderHtml(raw) {
  const validated = await validateUrl(raw);
  const executablePath = await browserExecutablePath();
  if (!executablePath) throw new Error('No compatible Chromium executable is available for rendered auditing.');

  const browser = await puppeteer.launch({
    executablePath,
    args: process.platform === 'win32'
      ? ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--disable-background-networking']
      : [...chromium.args, '--disable-background-networking'],
    headless: true,
    defaultViewport: { width: 1440, height: 1000 }
  });

  const started = Date.now();
  let page;
  try {
    page = await browser.newPage();
    await page.setUserAgent('SearchSignalRenderedAudit/1.0 (+independent portfolio demo)');
    await page.setRequestInterception(true);
    const hostCache = new Map();

    page.on('request', async (request) => {
      try {
        const allowed = await publicRequestAllowed(request.url(), hostCache);
        if (!allowed) return request.abort('blockedbyclient');
        const type = request.resourceType();
        if (type === 'media' || type === 'font') return request.abort('blockedbyclient');
        return request.continue();
      } catch {
        try { return request.abort('blockedbyclient'); } catch {}
      }
    });

    const response = await page.goto(validated.toString(), {
      waitUntil: 'domcontentloaded',
      timeout: 12000
    });

    try {
      await page.waitForFunction(() => {
        const text = document.body?.innerText?.replace(/\s+/g, ' ').trim() || '';
        return text.length >= 80 || document.querySelectorAll('a,button,[role="button"],main,article').length >= 8;
      }, { timeout: 5000 });
    } catch {}

    try { await page.waitForNetworkIdle({ idleTime: 700, timeout: 5000 }); } catch {}
    await new Promise((resolve) => setTimeout(resolve, 500));

    let transcriptAttempted = false;
    let transcriptLoaded = false;
    const target = new URL(validated);
    if (/(^|\.)youtube\.com$/i.test(target.hostname) && target.pathname === '/watch') {
      try {
        transcriptAttempted = await page.evaluate(() => {
          const buttons = [...document.querySelectorAll('button')];
          const button = buttons.find((el) => /show transcript/i.test((el.getAttribute('aria-label') || '')+' '+(el.innerText || el.textContent || '')));
          if (!button) return false;
          button.click();
          return true;
        });
        if (transcriptAttempted) {
          try {
            await page.waitForSelector('ytd-transcript-segment-renderer', { timeout: 3500 });
            transcriptLoaded = true;
          } catch {}
        }
      } catch {}
    }

    const html = await page.content();
    if (Buffer.byteLength(html, 'utf8') > 4_000_000) throw new Error('Rendered page exceeds the 4 MB audit limit.');

    const finalUrl = page.url();
    await validateUrl(finalUrl);
    const resourceCount = await page.evaluate(() => performance.getEntriesByType('resource').length);
    const textChars = await page.evaluate(() => (document.body?.innerText || '').trim().length);

    return {
      html,
      status: response?.status?.() || 200,
      finalUrl,
      renderMeta: {
        mode: 'browser-rendered',
        label: 'Browser-rendered audit',
        rendered: true,
        renderMs: Date.now() - started,
        resourceCount,
        textChars,
        hashRoute: Boolean(new URL(raw).hash),
        requestedHash: new URL(raw).hash || '',
        finalHash: new URL(finalUrl).hash || '',
        routeChanged: new URL(raw).origin === new URL(finalUrl).origin && (new URL(raw).pathname + new URL(raw).hash) !== (new URL(finalUrl).pathname + new URL(finalUrl).hash),
        authWall: /(login|signin|sign-in|auth|loginwall|access-denied|forbidden)/i.test(new URL(finalUrl).pathname + new URL(finalUrl).hash),
        transcriptAttempted,
        transcriptLoaded,
        note: 'Rendered in a sandboxed headless Chromium session. Private-network requests are blocked; media and fonts are skipped.'
      }
    };
  } finally {
    try { if (page) await page.close(); } catch {}
    await browser.close();
  }
}


const renderedAuditCache = new Map();
let activeRenderedAudits = 0;
const MAX_RENDERED_AUDITS = 2;
const RENDER_CACHE_TTL_MS = 5 * 60 * 1000;

async function cachedRenderedHtml(raw) {
  const key = String(raw || '').trim();
  const cached = renderedAuditCache.get(key);
  if (cached && Date.now() - cached.at < RENDER_CACHE_TTL_MS) {
    return {
      ...cached.value,
      renderMeta: {
        ...cached.value.renderMeta,
        cached: true,
        note: cached.value.renderMeta.note+' Result reused from the short-lived rendered-audit cache.'
      }
    };
  }
  if (activeRenderedAudits >= MAX_RENDERED_AUDITS) {
    const error = new Error('Rendered-audit capacity is busy. Retry shortly or use Server only.');
    error.statusCode = 429;
    throw error;
  }
  activeRenderedAudits += 1;
  try {
    const value = await renderHtml(key);
    renderedAuditCache.set(key, { at: Date.now(), value });
    if (renderedAuditCache.size > 12) {
      const oldest = [...renderedAuditCache.entries()].sort((a,b)=>a[1].at-b[1].at)[0]?.[0];
      if (oldest) renderedAuditCache.delete(oldest);
    }
    return value;
  } finally {
    activeRenderedAudits -= 1;
  }
}

function renderedResult(raw, rendered, fallbackReason = '') {
  const retrieval = {
    ...rendered.renderMeta,
    mode: fallbackReason ? 'auto-rendered' : 'browser-rendered',
    label: fallbackReason ? 'Automatic browser-rendered audit' : 'Browser-rendered audit',
    autoFallback: Boolean(fallbackReason),
    fallbackReason: fallbackReason || ''
  };
  const result = analyzeHtml(raw, rendered.html, rendered.status, rendered.finalUrl, retrieval);
  if (rendered.renderMeta.authWall && rendered.renderMeta.routeChanged) {
    result.scores = { seo: null, geo: null };
    result.auditability = {
      scorable: false,
      classification: 'rendered_auth_wall',
      reasons: ['Client-side navigation changed the requested route to an authentication/login wall: '+rendered.finalUrl],
      note: 'The rendered DOM belongs to an authentication wall rather than the requested content route, so SEO/GEO scores are suppressed.'
    };
    result.rubrics = {
      seo: result.rubrics.seo.map((item) => ({ ...item, applicable: false })),
      geo: result.rubrics.geo.map((item) => ({ ...item, applicable: false }))
    };
    result.findings = [issue('Critical', 'Requested rendered route was not accessible', 'Requested '+raw+' but the browser ended at '+rendered.finalUrl, 'Sign in or use a publicly accessible route. SearchSignal will not score the login wall as if it were the requested content page.')];
  }
  return result;
}

function renderedFallbackReason(result, raw, html) {
  let url;
  try { url = new URL(raw); } catch { return ''; }
  if (url.hash) return 'Hash-routed URL requires client-side rendering.';
  if (!result.auditability?.scorable) return 'Server response was not reliably scorable.';
  if (result.pageType?.type === 'video') return 'Video page benefits from rendered primary-content, chapter, and transcript inspection.';
  if (result.pageType?.type === 'application') return 'Client-rendered application shell detected.';
  const scriptCount = (String(html || '').match(/<script\b/gi) || []).length;
  if ((result.shellWordCount || 0) < 120 && scriptCount >= 8) return 'Thin HTML shell with substantial JavaScript detected.';
  return '';
}

app.post('/api/rendered-audit', async (req, res) => {
  try {
    const raw = String(req.body?.url || '').trim();
    const rendered = await cachedRenderedHtml(raw);
    res.json(renderedResult(raw, rendered));
  } catch (err) {
    res.status(err?.statusCode || 400).json({ error: err?.name === 'TimeoutError' ? 'Browser-rendered audit timed out.' : (err?.message || 'Browser-rendered audit failed.') });
  }
});

app.post('/api/smart-audit', async (req, res) => {
  try {
    const raw = String(req.body?.url || '').trim();
    const fetched = await fetchHtml(raw);
    const serverResult = analyzeHtml(raw, fetched.html, fetched.status, fetched.finalUrl, {
      mode: 'smart-server',
      label: 'Smart audit · server fetch',
      rendered: false,
      autoFallback: false
    });
    const reason = renderedFallbackReason(serverResult, raw, fetched.html);
    if (!reason) {
      serverResult.retrieval.fallbackReason = '';
      return res.json(serverResult);
    }
    const rendered = await cachedRenderedHtml(raw);
    return res.json(renderedResult(raw, rendered, reason));
  } catch (err) {
    res.status(err?.statusCode || 400).json({ error: err?.name === 'TimeoutError' ? 'Smart audit render timed out.' : (err?.message || 'Smart audit failed.') });
  }
});


function cleanCrawlUrl(raw) {
  const u = new URL(raw);
  u.hash = '';
  u.search = '';
  return u.toString();
}

function isDocumentUrl(url) {
  try { return /\.(pdf|docx?|xlsx?|pptx?)$/i.test(new URL(url).pathname); }
  catch { return false; }
}

async function inspectDocument(raw) {
  let current = await validateUrl(raw);
  for (let i = 0; i < 5; i++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 7000);
    let response;
    try {
      response = await fetch(current, {
        method: 'HEAD',
        redirect: 'manual',
        signal: controller.signal,
        headers: { 'user-agent': 'SearchSignalPortfolioAudit/1.0 (+independent demo)' }
      });
    } finally { clearTimeout(timer); }
    const location = response.headers.get('location');
    if (response.status >= 300 && response.status < 400 && location) {
      current = await validateUrl(new URL(location, current).toString());
      continue;
    }
    return {
      finalUrl: current.toString(),
      status: response.status,
      contentType: response.headers.get('content-type') || '',
      bytes: Number(response.headers.get('content-length') || 0) || null,
      lastModified: response.headers.get('last-modified') || '',
      etag: response.headers.get('etag') || '',
      contentDisposition: response.headers.get('content-disposition') || ''
    };
  }
  throw new Error('Too many document redirects.');
}

async function getRedirectChain(raw) {
  let current = await validateUrl(raw);
  const chain = [];
  const visited = new Set();
  for (let i = 0; i < 8; i++) {
    const key = current.toString();
    if (visited.has(key)) throw new Error('Redirect loop detected.');
    visited.add(key);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 7000);
    let response;
    try {
      response = await fetch(current, {
        redirect: 'manual',
        signal: controller.signal,
        headers: { 'user-agent': 'SearchSignalPortfolioAudit/1.0 (+independent demo)' }
      });
    } finally { clearTimeout(timer); }
    const location = response.headers.get('location');
    chain.push({ url: current.toString(), status: response.status, location: location || null });
    if (response.body) { try { await response.body.cancel(); } catch {} }
    if (response.status >= 300 && response.status < 400 && location) {
      current = await validateUrl(new URL(location, current).toString());
      continue;
    }
    return chain;
  }
  throw new Error('Redirect chain exceeded 8 hops.');
}

app.post('/api/site-scan', async (req, res) => {
  try {
    const raw = String(req.body?.url || '').trim();
    const requested = Number(req.body?.limit || 8);
    const limit = Math.max(1, Math.min(12, Number.isFinite(requested) ? Math.round(requested) : 8));
    const requestedDelay = Number(req.body?.delayMs || 0);
    const delayMs = Math.max(0, Math.min(1000, Number.isFinite(requestedDelay) ? Math.round(requestedDelay) : 0));
    const start = await validateUrl(raw);
    const origin = start.origin;
    const queue = [cleanCrawlUrl(start.toString())];
    const seen = new Set();
    const pages = [];
    const documents = new Map();

    while (queue.length && pages.length < limit) {
      const current = queue.shift();
      if (!current || seen.has(current)) continue;
      seen.add(current);
      if (delayMs > 0 && pages.length > 0) await new Promise((resolve) => setTimeout(resolve, delayMs));
      try {
        const fetched = await fetchHtml(current);
        const $ = cheerio.load(fetched.html);
        const title = $('title').first().text().replace(/\s+/g, ' ').trim();
        const description = meta($, 'meta[name="description"]');
        const canonical = $('link[rel="canonical"]').first().attr('href') || '';
        const robots = meta($, 'meta[name="robots"]');
        const h1Count = $('h1').length;
        const bodyText = $('body').text().replace(/\s+/g, ' ').trim();
        const wordCount = bodyText ? bodyText.split(/\s+/).length : 0;
        let internalLinks = 0;

        $('a[href]').each((_, el) => {
          const href = String($(el).attr('href') || '').trim();
          if (!href || href.startsWith('#') || href.startsWith('mailto:') || href.startsWith('tel:') || href.startsWith('javascript:')) return;
          try {
            const u = new URL(href, fetched.finalUrl);
            if (!['http:', 'https:'].includes(u.protocol) || u.origin !== origin) return;
            const normalized = cleanCrawlUrl(u.toString());
            internalLinks++;
            if (isDocumentUrl(normalized)) {
              if (!documents.has(normalized)) documents.set(normalized, {
                url: normalized,
                source: fetched.finalUrl,
                sources: [fetched.finalUrl],
                linkText: $(el).text().replace(/\s+/g, ' ').trim() || '(no link text)'
              });
              else {
                const existing = documents.get(normalized);
                if (!existing.sources.includes(fetched.finalUrl)) existing.sources.push(fetched.finalUrl);
              }
              return;
            }
            if (!seen.has(normalized) && !queue.includes(normalized) && !/\/(wp-admin|wp-login|search)(\/|$)/i.test(u.pathname)) {
              queue.push(normalized);
            }
          } catch {}
        });

        pages.push({
          url: fetched.finalUrl,
          status: fetched.status,
          title,
          description,
          canonical,
          noindex: /noindex/i.test(robots),
          h1Count,
          wordCount,
          internalLinks
        });
      } catch (error) {
        pages.push({ url: current, error: error?.message || 'Scan failed.' });
      }
    }

    const documentRows = await Promise.all([...documents.values()].slice(0, 10).map(async (doc) => {
      try { return { ...doc, ...(await inspectDocument(doc.url)) }; }
      catch (error) { return { ...doc, error: error?.message || 'Document check failed.' }; }
    }));

    const okPages = pages.filter((p) => !p.error);
    const summary = {
      pagesCrawled: pages.length,
      pageErrors: pages.filter((p) => p.error).length,
      missingTitles: okPages.filter((p) => !p.title).length,
      missingDescriptions: okPages.filter((p) => !p.description).length,
      missingCanonicals: okPages.filter((p) => !p.canonical).length,
      h1Issues: okPages.filter((p) => p.h1Count !== 1).length,
      noindexPages: okPages.filter((p) => p.noindex).length,
      documentsFound: documents.size,
      documentsChecked: documentRows.length,
      averageWords: okPages.length ? Math.round(okPages.reduce((n, p) => n + p.wordCount, 0) / okPages.length) : 0
    };
    res.json({ startUrl: start.toString(), origin, limit, delayMs, summary, pages, documents: documentRows });
  } catch (err) {
    res.status(400).json({ error: err?.name === 'AbortError' ? 'Site scan timed out.' : (err?.message || 'Site scan failed.') });
  }
});

app.post('/api/redirect-check', async (req, res) => {
  try {
    const raw = String(req.body?.url || '').trim();
    const chain = await getRedirectChain(raw);
    res.json({
      url: raw,
      chain,
      hops: Math.max(0, chain.length - 1),
      finalUrl: chain.at(-1)?.url || raw,
      finalStatus: chain.at(-1)?.status || null
    });
  } catch (err) {
    res.status(400).json({ error: err?.name === 'AbortError' ? 'Redirect check timed out.' : (err?.message || 'Redirect check failed.') });
  }
});


function changeLabPayload(action = 'analyze') {
  const beforeHtml = '<title>Health Sciences Program | Example University</title>\n<meta name="description" content="Learn more.">\n<main><h1>Health Sciences</h1><h1>Program Overview</h1><p>Prepare for a career in health sciences.</p><p><a href="/admissions">Click here</a> for admissions.</p></main>';
  const afterHtml = '<title>Health Sciences Program | Example University</title>\n<meta name="description" content="Explore the Health Sciences program, curriculum, admissions requirements, student support, and career pathways at Example University.">\n<script type="application/ld+json">{"@context":"https://schema.org","@type":"WebPage","name":"Health Sciences Program","url":"https://example.edu/health-sciences"}</script>\n<main><h1>Health Sciences Program</h1><h2>Program overview</h2><p>Prepare for a career in health sciences through applied coursework and guided academic support.</p><p><a href="/admissions">Review admissions requirements</a> for next steps.</p><p><a href="/curriculum">Explore the curriculum</a>.</p><p><a href="/support">Student support resources</a>.</p></main>';
  const issues = [
    {id:'meta',severity:'High',label:'Weak meta description',evidence:'“Learn more.” is too vague to explain page intent.'},
    {id:'heading',severity:'High',label:'Heading hierarchy',evidence:'Two H1 elements compete for the page-level heading.'},
    {id:'schema',severity:'Medium',label:'Missing structured data',evidence:'No JSON-LD is present in the sandbox copy.'},
    {id:'links',severity:'Medium',label:'Weak internal linking',evidence:'One generic “Click here” link provides little destination context.'}
  ];
  const changes = [
    {field:'Meta description',before:'Learn more.',after:'Explore the Health Sciences program, curriculum, admissions requirements, student support, and career pathways at Example University.'},
    {field:'Heading structure',before:'H1: Health Sciences + H1: Program Overview',after:'H1: Health Sciences Program + H2: Program overview'},
    {field:'JSON-LD',before:'None',after:'Truthful WebPage schema matching visible content'},
    {field:'Internal links',before:'Click here → /admissions',after:'Descriptive admissions, curriculum, and student-support links'}
  ];
  const applied = action === 'apply' || action === 'verify';
  return {
    sandboxOnly:true,
    productionModified:false,
    action,
    page:{name:'Synthetic Health Sciences Program page',url:'https://example.edu/health-sciences'},
    beforeHtml,
    afterHtml,
    issues,
    changes,
    appliedHtml: applied ? afterHtml : beforeHtml,
    validation: applied ? {metaLength:148,h1Count:1,schemaTypes:['WebPage'],descriptiveInternalLinks:3,placeholderLinks:0,htmlStatus:'Valid demo fragment'} : null,
    reAudit: action === 'verify' ? {before:{seo:54,geo:36},after:{seo:94,geo:83},remaining:['Human editorial review','Accessibility conformance testing','Production change approval']} : null,
    boundary:'No production site modified. All changes are applied only to a synthetic sandbox copy.'
  };
}

app.post('/api/change-lab', (req, res) => {
  const action = String(req.body?.action || 'analyze').toLowerCase();
  if (!['analyze','prepare','apply','verify','reset'].includes(action)) return res.status(400).json({error:'Unsupported Change Lab action.'});
  res.json(changeLabPayload(action === 'reset' ? 'analyze' : action));
});

app.post('/api/scale-sim', (req, res) => {
  const pages = Math.max(100, Math.min(100000, Math.round(Number(req.body?.pages || 20000))));
  const documents = Math.max(0, Math.min(100000, Math.round(Number(req.body?.documents || 15000))));
  const batchSize = Math.max(10, Math.min(1000, Math.round(Number(req.body?.batchSize || 250))));
  const ratePerSecond = Math.max(0.5, Math.min(20, Number(req.body?.ratePerSecond || 4)));
  const resumeFrom = Math.max(0, Math.min(pages + documents, Math.round(Number(req.body?.resumeFrom || 0))));
  const totalItems = pages + documents;
  const remaining = Math.max(0, totalItems - resumeFrom);
  const batches = Math.ceil(remaining / batchSize);
  const estimatedSeconds = Math.ceil(remaining / ratePerSecond);
  const seed = (pages * 31 + documents * 17 + batchSize) % 997;
  const issueCounts = {
    duplicateTitles: Math.round(pages * (0.008 + (seed % 4) / 1000)),
    brokenLinks: Math.round(pages * (0.004 + (seed % 3) / 1000)),
    redirectChains: Math.round(pages * 0.0025),
    missingCanonicals: Math.round(pages * 0.006),
    orphanedDocuments: Math.round(documents * 0.012),
    oversizedDocuments: Math.round(documents * 0.007)
  };
  res.json({
    synthetic:true,
    productionCrawl:false,
    inventory:{pages,documents,totalItems},
    execution:{batchSize,ratePerSecond,resumeFrom,remaining,batches,estimatedSeconds,cacheStrategy:'URL + ETag/Last-Modified fingerprint',checkpointEveryBatches:10},
    issueCounts,
    queuePreview:[
      {priority:'Now',work:'Broken-link clusters on high-traffic program pages'},
      {priority:'Now',work:'Canonical gaps affecting duplicate page families'},
      {priority:'Next',work:'Orphaned/oversized document review'},
      {priority:'Later',work:'Long redirect-chain cleanup after owner validation'}
    ],
    boundary:'Synthetic scale model only. This endpoint does not crawl Geisel or any external site.'
  });
});

async function fetchPublicResource(raw) {
  const current = await validateUrl(raw);
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 7000);
  try {
    const response = await fetch(current, {redirect:'follow', signal:controller.signal, headers:{'user-agent':'SearchSignalPortfolioAudit/1.0 (+independent demo)'}});
    const buffer = Buffer.from(await response.arrayBuffer());
    return {url:current.toString(),status:response.status,contentType:response.headers.get('content-type')||'',bytes:buffer.length,preview:buffer.toString('utf8',0,Math.min(buffer.length,900))};
  } finally { clearTimeout(timer); }
}

app.post('/api/site-meta', async (req, res) => {
  try {
    const start = await validateUrl(String(req.body?.url || '').trim());
    const robotsUrl = new URL('/robots.txt', start.origin).toString();
    const sitemapUrl = new URL('/sitemap.xml', start.origin).toString();
    const [robots, sitemap] = await Promise.all([
      fetchPublicResource(robotsUrl).catch((error)=>({url:robotsUrl,error:error?.message||'Check failed'})),
      fetchPublicResource(sitemapUrl).catch((error)=>({url:sitemapUrl,error:error?.message||'Check failed'}))
    ]);
    res.json({origin:start.origin,robots,sitemap});
  } catch (err) {
    res.status(400).json({error:err?.name==='AbortError'?'Site metadata check timed out.':(err?.message||'Site metadata check failed.')});
  }
});

if (process.env.VERCEL !== '1') {
  app.listen(PORT, () => console.log('SearchSignal listening on ' + PORT));
}

export default app;
