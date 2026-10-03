import express from 'express';
import * as cheerio from 'cheerio';
import dns from 'node:dns/promises';
import net from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

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
  const total = checks.reduce((s, c) => s + c.weight, 0);
  const earned = checks.reduce((s, c) => s + (c.ok ? c.weight : 0), 0);
  return Math.round((earned / total) * 100);
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

app.post('/api/audit', async (req, res) => {
  try {
    const raw = String(req.body?.url || '').trim();
    const { html, status, finalUrl } = await fetchHtml(raw);
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
    const wordCount = bodyText ? bodyText.split(' ').length : 0;

    const imageCount = $('img').length;
    const imagesWithAlt = $('img[alt]').filter((_, e) => String($(e).attr('alt') || '').trim().length > 0).length;
    const altCoverage = imageCount ? imagesWithAlt / imageCount : 1;

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
    const noindex = /noindex/i.test(robots);
    const canonicalOk = Boolean(canonical) && (() => {
      try { return new URL(canonical, base).hostname === base.hostname; } catch { return false; }
    })();
    const singleH1 = h1.length === 1;

    const seoRubric = [
      { name: 'Indexable', ok: !noindex, weight: 15 },
      { name: 'Title length', ok: title.length >= 20 && title.length <= 65, weight: 12 },
      { name: 'Meta description', ok: description.length >= 70 && description.length <= 170, weight: 10 },
      { name: 'Canonical', ok: canonicalOk, weight: 10 },
      { name: 'Single H1', ok: singleH1, weight: 10 },
      { name: 'Heading structure', ok: h2.length > 0, weight: 8 },
      { name: 'Image alt coverage', ok: altCoverage >= 0.8, weight: 8 },
      { name: 'Internal links', ok: internal >= 3, weight: 7 },
      { name: 'Structured data', ok: schemas.length > 0 && invalidSchemaBlocks === 0, weight: 10 },
      { name: 'Mobile viewport', ok: Boolean(viewport), weight: 5 },
      { name: 'Language attribute', ok: Boolean(lang), weight: 5 }
    ];

    const geoRubric = [
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

    const findings = [];
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

    res.json({
      url: raw, finalUrl, status, title, description, canonical, robots, lang, viewport,
      wordCount, headings: { h1, h2, h3 },
      links: { total: hrefs.length, internal, external, placeholders },
      images: { total: imageCount, withAlt: imagesWithAlt, coverage: Math.round(altCoverage * 100) },
      schema: { types: [...new Set(schemas)], invalidBlocks: invalidSchemaBlocks },
      signals: { wordpress, generator, author, published, modified, openGraph, twitter, questions, answerFirst, hasCitations },
      accessibilitySignals: { genericLinkText, formControls, unlabeledControls, note: 'Heuristic signals only; not an accessibility conformance determination.' },
      scores: { seo: weightedScore(seoRubric), geo: weightedScore(geoRubric) },
      rubrics: {
        seo: seoRubric.map(({ name, ok }) => ({ name, ok })),
        geo: geoRubric.map(({ name, ok }) => ({ name, ok }))
      },
      findings
    });
  } catch (err) {
    res.status(400).json({ error: err?.name === 'AbortError' ? 'Audit timed out.' : (err?.message || 'Audit failed.') });
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
