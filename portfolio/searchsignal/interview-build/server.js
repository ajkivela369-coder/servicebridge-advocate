import express from 'express';
import * as cheerio from 'cheerio';
import dns from 'node:dns/promises';
import net from 'node:net';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const app = express();
const PORT = process.env.PORT || 3000;

const ROOT = path.dirname(fileURLToPath(import.meta.url));

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

    res.json({
      url: raw, finalUrl, status, title, description, canonical, robots, lang, viewport,
      wordCount, headings: { h1, h2, h3 },
      links: { total: hrefs.length, internal, external, placeholders },
      images: { total: imageCount, withAlt: imagesWithAlt, coverage: Math.round(altCoverage * 100) },
      schema: { types: [...new Set(schemas)], invalidBlocks: invalidSchemaBlocks },
      signals: { wordpress, generator, author, published, modified, openGraph, twitter, questions, answerFirst, hasCitations },
      scores: { seo: weightedScore(seoRubric), geo: weightedScore(geoRubric) },
      rubrics: { seo: seoRubric, geo: geoRubric },
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
      bytes: Number(response.headers.get('content-length') || 0) || null
    };
  }
  throw new Error('Too many document redirects.');
}

async function getRedirectChain(raw) {
  let current = await validateUrl(raw);
  const chain = [];
  for (let i = 0; i < 8; i++) {
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
                linkText: $(el).text().replace(/\s+/g, ' ').trim() || '(no link text)'
              });
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
    res.json({ startUrl: start.toString(), origin, limit, summary, pages, documents: documentRows });
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

if (process.env.VERCEL !== '1') {
  app.listen(PORT, () => console.log('SearchSignal listening on ' + PORT));
}

export default app;