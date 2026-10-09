import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const root = fileURLToPath(new URL('..', import.meta.url));
const port = 32000 + (process.pid % 1000);
const base = `http://127.0.0.1:${port}`;
let child;
let childError = '';

async function waitForServer() {
  for (let i = 0; i < 50; i++) {
    if (child?.exitCode !== null && child?.exitCode !== undefined) {
      throw new Error(`SearchSignal test server exited early (${child.exitCode}): ${childError}`);
    }
    try {
      const r = await fetch(`${base}/api/health`);
      if (r.ok) return;
    } catch {}
    await new Promise(r => setTimeout(r, 200));
  }
  throw new Error(`SearchSignal test server did not start. ${childError}`);
}

test.before(async () => {
  child = spawn(process.execPath, ['server.js'], {
    cwd: root,
    env: { ...process.env, PORT: String(port) },
    stdio: ['ignore', 'ignore', 'pipe']
  });
  child.stderr.on('data', chunk => { childError += chunk.toString(); });
  await waitForServer();
});

test.after(() => child?.kill());

test('health endpoint reports SearchSignal ready', async () => {
  const r = await fetch(`${base}/api/health`);
  assert.equal(r.status, 200);
  const data = await r.json();
  assert.equal(data.ok, true);
  assert.equal(data.service, 'SearchSignal');
});

test('case-study workflow and priority engine ship in the client', async () => {
  const r = await fetch(`${base}/app.js`);
  const js = await r.text();
  assert.equal(r.status, 200);
  assert.match(js, /Case Studies/);
  assert.match(js, /Site Intelligence/);
  assert.match(js, /Demand \/ capacity pressure/);
  assert.match(js, /Run live public-page audit/);
  assert.match(js, /Run bounded site scan/);
  assert.match(js, /Sample remediation pack/);
  assert.match(js, /Download sample pack/);
});

test('private network audit targets are blocked', async () => {
  const r = await fetch(`${base}/api/audit`, {
    method: 'POST', headers: {'content-type':'application/json'},
    body: JSON.stringify({url:'http://127.0.0.1/'})
  });
  assert.equal(r.status, 400);
  const data = await r.json();
  assert.match(data.error, /private|blocked/i);
});

test('public page audit returns explainable SEO and GEO scores', async () => {
  const r = await fetch(`${base}/api/audit`, {
    method: 'POST', headers: {'content-type':'application/json'},
    body: JSON.stringify({url:'https://example.com/'})
  });
  assert.equal(r.status, 200);
  const data = await r.json();
  assert.equal(typeof data.scores.seo, 'number');
  assert.equal(typeof data.scores.geo, 'number');
  assert.ok(Array.isArray(data.findings));
  assert.ok(Array.isArray(data.rubrics.seo));
  assert.ok(Array.isArray(data.rubrics.geo));
});

test('bounded site scan returns a page inventory', async () => {
  const r = await fetch(`${base}/api/site-scan`, {
    method: 'POST', headers: {'content-type':'application/json'},
    body: JSON.stringify({url:'https://example.com/', limit:2})
  });
  assert.equal(r.status, 200);
  const data = await r.json();
  assert.ok(data.summary.pagesCrawled >= 1);
  assert.ok(Array.isArray(data.pages));
  assert.ok(Array.isArray(data.documents));
});

test('redirect validator returns an explicit chain', async () => {
  const r = await fetch(`${base}/api/redirect-check`, {
    method: 'POST', headers: {'content-type':'application/json'},
    body: JSON.stringify({url:'https://example.com/'})
  });
  assert.equal(r.status, 200);
  const data = await r.json();
  assert.ok(Array.isArray(data.chain));
  assert.ok(data.chain.length >= 1);
  assert.equal(typeof data.finalStatus, 'number');
});

test('public audit response hides proprietary scoring weights', async () => {
  const r = await fetch(`${base}/api/audit`, {
    method: 'POST', headers: {'content-type':'application/json'},
    body: JSON.stringify({url:'https://example.com/'})
  });
  assert.equal(r.status, 200);
  const data = await r.json();
  for (const group of [data.rubrics.seo, data.rubrics.geo]) {
    assert.ok(group.every(item => !Object.prototype.hasOwnProperty.call(item, 'weight')));
  }
});

test('prioritization runs server-side', async () => {
  const r = await fetch(`${base}/api/prioritize`, {
    method: 'POST', headers: {'content-type':'application/json'},
    body: JSON.stringify({items:[
      {impact:5,gap:4,competition:5,demand:5,staff:3,effort:2},
      {impact:2,gap:2,competition:2,demand:2,staff:4,effort:4}
    ]})
  });
  assert.equal(r.status, 200);
  const data = await r.json();
  assert.equal(data.ranked.length, 2);
  assert.equal(data.ranked[0].index, 0);
  assert.equal(typeof data.ranked[0].score, 'number');
  assert.ok(['Now','Next','Later'].includes(data.ranked[0].phase));
});

test('recommendation generation runs server-side', async () => {
  const r = await fetch(`${base}/api/recommendations`, {
    method: 'POST', headers: {'content-type':'application/json'},
    body: JSON.stringify({text:'Example organization offers public programs, research, services, and educational resources.'})
  });
  assert.equal(r.status, 200);
  const data = await r.json();
  assert.equal(typeof data.opening, 'string');
  assert.ok(Array.isArray(data.geo));
  assert.ok(Array.isArray(data.seo));
});

test('public client omits proprietary formulas and shows ownership notice', async () => {
  const js = await (await fetch(`${base}/app.js`)).text();
  assert.doesNotMatch(js, /impact\s*\*\s*2/i);
  assert.doesNotMatch(js, /supportNeed\s*=|weight:\s*1[0-9]/i);
  const html = await (await fetch(`${base}/`)).text();
  assert.match(html, /© 2026 Alexander J\. Kivela/);
  assert.match(html, /Proprietary portfolio software/);
});

test('security headers protect the public demo surface', async () => {
  const page = await fetch(`${base}/`);
  assert.equal(page.headers.has('x-powered-by'), false);
  assert.match(page.headers.get('content-security-policy') || '', /default-src 'self'/);
  assert.equal(page.headers.get('x-content-type-options'), 'nosniff');

  const api = await fetch(`${base}/api/health`);
  assert.equal(api.headers.get('cache-control'), 'no-store');
});

test('Change Lab is sandbox-only and supports verify re-audit', async () => {
  const r = await fetch(base + '/api/change-lab', {
    method: 'POST', headers: {'content-type':'application/json'},
    body: JSON.stringify({action:'verify'})
  });
  assert.equal(r.status, 200);
  const data = await r.json();
  assert.equal(data.sandboxOnly, true);
  assert.equal(data.productionModified, false);
  assert.equal(data.validation.h1Count, 1);
  assert.ok(data.reAudit.after.seo > data.reAudit.before.seo);
  assert.match(data.boundary, /No production site modified/i);
});

test('scale simulator models 20K pages and 15K documents without crawling production', async () => {
  const r = await fetch(base + '/api/scale-sim', {
    method: 'POST', headers: {'content-type':'application/json'},
    body: JSON.stringify({pages:20000,documents:15000,batchSize:250,ratePerSecond:4})
  });
  assert.equal(r.status, 200);
  const data = await r.json();
  assert.equal(data.synthetic, true);
  assert.equal(data.productionCrawl, false);
  assert.equal(data.inventory.totalItems, 35000);
  assert.ok(data.execution.batches > 0);
  assert.equal(typeof data.issueCounts.orphanedDocuments, 'number');
});

test('client exposes implementation, pattern, document, reporting, and support workflows', async () => {
  const js = await (await fetch(base + '/app.js')).text();
  const phrases = [
    'Change Lab',
    'No production site modified',
    'Site Patterns',
    'Document Intelligence',
    'Progress & Reporting',
    '20K Scale Simulator',
    'My page disappeared from navigation',
    'Baseline → post-change comparison',
    'Implemented',
    'Automated test',
    'Live verified',
    'Explain to department editor'
  ];
  for (const phrase of phrases) assert.ok(js.includes(phrase), 'Missing client phrase: ' + phrase);
});


test('error responses are not given SEO or GEO scores', async () => {
  const r = await fetch(`${base}/api/audit`, {
    method: 'POST', headers: {'content-type':'application/json'},
    body: JSON.stringify({url:'https://example.com/definitely-not-a-real-page-searchsignal'})
  });
  assert.equal(r.status, 200);
  const data = await r.json();
  assert.equal(data.auditability.scorable, false);
  assert.equal(data.scores.seo, null);
  assert.equal(data.scores.geo, null);
  assert.ok(data.auditability.reasons.length >= 1);
  assert.match(data.auditability.note, /suppressed/i);
});

test('zero-image pages do not receive automatic alt-text credit', async () => {
  const r = await fetch(`${base}/api/audit`, {
    method: 'POST', headers: {'content-type':'application/json'},
    body: JSON.stringify({url:'https://example.com/'})
  });
  assert.equal(r.status, 200);
  const data = await r.json();
  if (data.images.total === 0) {
    assert.equal(data.images.coverage, null);
    const altCheck = data.rubrics.seo.find((x) => x.name === 'Image alt coverage');
    assert.equal(altCheck.applicable, false);
  }
});

test('client labels unscorable audits as N/A instead of a misleading score', async () => {
  const js = await (await fetch(`${base}/app.js`)).text();
  assert.match(js, /Not scorable/);
  assert.match(js, /SEO\/GEO scores are suppressed/);
  assert.match(js, /No images detected/);
});
