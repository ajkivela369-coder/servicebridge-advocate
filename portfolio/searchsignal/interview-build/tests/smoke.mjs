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

test('interview workflow and priority engine ship in the client', async () => {
  const r = await fetch(`${base}/app.js`);
  const js = await r.text();
  assert.equal(r.status, 200);
  assert.match(js, /Geisel Interview Mode/);
  assert.match(js, /Site Intelligence/);
  assert.match(js, /Demand \/ capacity pressure/);
  assert.match(js, /Run live public-page audit/);
  assert.match(js, /Run bounded site scan/);
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
