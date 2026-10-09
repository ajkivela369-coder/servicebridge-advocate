import { VERSION, splitConcepts, neuroEvaluate, healthAudit, pairEvaluate, CRITERIA, parseSources, citationAudit } from './engine.js';
import { NEURO_TOPICS, HEALTH_EXAMPLES, PAIR_EXAMPLES, CITE_EXAMPLES } from './examples.js';

const app = document.getElementById('app');
const $ = id => document.getElementById(id);
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[c]));
const path = location.pathname.replace(/^\/+|\/+$/g, '').toLowerCase();
const TOOLS = {
  neuroeval: { name: 'NeuroEval', short: 'Neuroscience', symbol: 'N', title: 'Review a neuroscience answer.', lead: 'Check whether an AI answer mentions the concepts you expect, spot wording that needs a closer look, and record your own scientific review.', use: 'For students, researchers, and AI evaluators reviewing biology or neuroscience explanations.', steps: ['Choose a topic or write your own question.', 'Paste an answer and set the expected concepts.', 'Run the review, verify the science, and export.'], result: 'You will see concept mentions, missing phrases, wording signals, and a source-review checklist.', action: 'Review answer' },
  healthqa: { name: 'HealthQA Auditor', short: 'Health content', symbol: 'H', title: 'Review health content before using it.', lead: 'Find diagnostic certainty, prescription-style wording, and urgent-symptom language that needs human attention.', use: 'For people evaluating AI health explanations and health-content drafts.', steps: ['Choose a sample or bring your own content.', 'Paste the health-related response.', 'Audit the wording, check context, and record your review.'], result: 'You will see flagged excerpts, why they matter, and what a human reviewer should check.', action: 'Audit content' },
  pairrank: { name: 'PairRank', short: 'Compare answers', symbol: 'P', title: 'Compare two answers with a clear rubric.', lead: 'Read two responses to the same question, rate them against five criteria, and explain which one better meets the task.', use: 'For AI evaluators, researchers, and reviewers making consistent A/B comparisons.', steps: ['Enter the shared question and both responses.', 'Rate each answer from 1 to 5.', 'Compare the weighted ratings and explain your decision.'], result: 'You will see weighted scores, the difference, and the preference produced by your ratings.', action: 'Compare ratings' },
  citeguard: { name: 'CiteGuard', short: 'Check sources', symbol: 'C', title: 'Connect each claim to a source for review.', lead: 'Paste claims and source excerpts to find possible matches, spot absolute language, and record whether each source actually supports the claim.', use: 'For writers, researchers, and AI evaluators reviewing source-grounded drafts.', steps: ['Enter one claim per line.', 'Add labeled source excerpts.', 'Find match candidates, read them, and record support.'], result: 'You will see the closest wording match for each claim and a separate human support decision.', action: 'Find source matches' },
};
const current = TOOLS[path] ? path : 'home';
const key = `aj-eval-${VERSION}-${current}`;
let saved = {};
try { saved = JSON.parse(sessionStorage.getItem(key) || '{}'); } catch { /* restricted storage remains usable */ }
let mode = saved.mode === 'pro' ? 'pro' : 'simple';
let result = null;
let exampleLoaded = false;
let citeDecisions = {};

const field = (id, label, hint, value = '', type = 'textarea', attrs = '') => `<div class="field"><label for="${id}">${label}</label><p class="hint" id="${id}Hint">${hint}</p>${type === 'textarea' ? `<textarea id="${id}" aria-describedby="${id}Hint" ${attrs}>${esc(value)}</textarea>` : `<input id="${id}" aria-describedby="${id}Hint" value="${esc(value)}" ${attrs}>`}</div>`;
const step = (number, title, body) => `<section class="form-step"><div class="step-heading"><span class="step-number">${number}</span><h2>${title}</h2></div>${body}</section>`;
const options = (items, selected) => items.map(x => `<option value="${esc(x.id)}" ${x.id === selected ? 'selected' : ''}>${esc(x.name)}</option>`).join('');
const chooser = (id, label, hint, items, selected) => `<div class="field"><label for="${id}">${label}</label><p class="hint" id="${id}Hint">${hint}</p><div class="example-row"><select id="${id}" aria-describedby="${id}Hint">${options(items, selected)}</select><button type="button" class="button secondary" id="loadExample">Try this example</button></div></div>`;
const checklist = items => `<ul class="review-list">${items.map(x => `<li>${esc(x)}</li>`).join('')}</ul>`;
function stash() {
  const fields = {};
  document.querySelectorAll('#reviewForm [id], #reviewDecision [id]').forEach(el => {
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName)) fields[el.id] = el.type === 'checkbox' ? el.checked : el.value;
  });
  try { sessionStorage.setItem(key, JSON.stringify({mode, fields})); } catch { /* no storage required */ }
}
function setMode(next) {
  mode = next;
  document.body.dataset.mode = next;
  document.querySelectorAll('[data-mode-choice]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.modeChoice === next)));
  $('modeDescription').textContent = next === 'simple' ? 'The main workflow, with guidance at each step.' : 'The main workflow plus detailed review controls and structured output.';
  stash();
}
function restoreFields() {
  for (const [id, value] of Object.entries(saved.fields || {})) {
    const el = $(id);
    if (el && ['INPUT','TEXTAREA','SELECT'].includes(el.tagName)) {
      if (el.type === 'checkbox') el.checked = Boolean(value); else el.value = String(value);
    }
  }
}
function liveStatus(text) { $('notice').textContent = text; }
function emptyResults(changed = false) {
  result = null;
  citeDecisions = {};
  $('humanVerdict').value = 'NOT REVIEWED';
  $('humanNotes').value = '';
  $('resultBody').innerHTML = `<div class="result-empty"><span class="empty-symbol">${TOOLS[current].symbol}</span><h3>${changed ? 'Ready for a fresh review' : 'Your review will appear here'}</h3><p>${changed ? 'The inputs changed. Run the review again so the result matches your current text.' : TOOLS[current].result}</p><p class="hint">Start with “Try this example,” or paste your own text. Then choose “${TOOLS[current].action}.”</p></div>`;
  $('resultState').textContent = changed ? 'Inputs changed' : 'Not run yet';
  $('exports').hidden = true;
  $('reviewDecision').hidden = true;
}
function manualControls() {
  return `<div id="reviewDecision" class="decision" hidden><h3>Your final review</h3><p class="hint">Record your judgment after checking the content. This is separate from the text-pattern results.</p><div class="field"><label for="humanVerdict">Reviewer decision</label><select id="humanVerdict"><option value="NOT REVIEWED">Not reviewed yet</option><option value="NEEDS REVISION">Needs revision</option><option value="ACCEPTABLE FOR TASK">Acceptable for this task</option><option value="DO NOT USE">Do not use</option></select></div>${field('humanNotes','Review notes','Record the evidence, corrections, or limitations behind your decision.','','textarea','rows="3"')}</div>`;
}
function frame(form) {
  const t = TOOLS[current];
  app.innerHTML = `<section class="shell"><div class="breadcrumb"><a href="/">All tools</a><span aria-hidden="true">/</span><span>${t.name}</span></div><header class="hero"><div><div class="eyebrow">${t.name} <span>·</span> ${t.short}</div><h1>${t.title}</h1><p class="lead">${t.lead}</p><p class="audience">${t.use}</p></div><div class="mode-card"><span class="group-label">Choose your workspace</span><div class="mode-switch" role="group" aria-label="Workspace mode"><button type="button" data-mode-choice="simple" aria-pressed="true">Simple</button><button type="button" data-mode-choice="pro" aria-pressed="false">Pro</button></div><p id="modeDescription">The main workflow, with guidance at each step.</p></div></header><ol class="quick-steps" aria-label="How to use ${t.name}">${t.steps.map((text,i) => `<li><span>${i+1}</span>${text}</li>`).join('')}</ol><div class="privacy-strip"><span class="privacy-dot" aria-hidden="true"></span>Runs in your browser · No account or API key needed <details><summary>How your text is handled</summary><p>Your inputs stay in this browser tab. Drafts use session storage so they survive a refresh; closing the tab ends that session. The app does not send your text to an AI service or fetch source URLs. Clear inputs to remove this tool’s draft.</p></details></div><div class="workbench"><form id="reviewForm" class="input-panel" novalidate>${form}<div class="form-actions"><button class="button primary" type="submit">${t.action}<span aria-hidden="true"> →</span></button><button class="button ghost" type="button" id="clearInputs">Clear inputs</button></div><p id="formError" class="form-error" role="alert" hidden></p><p id="notice" class="notice" role="status"></p></form><aside class="results-panel" aria-labelledby="resultHeading"><div class="results-heading"><h2 id="resultHeading">Review results</h2><span id="resultState" class="status">Not run yet</span></div><div id="resultBody"></div>${manualControls()}<div id="exports" class="export-area" hidden><h3>Keep your review</h3><div class="export-buttons"><button type="button" class="button secondary" id="downloadReport">Download readable report</button><button type="button" class="button ghost" id="printReport">Print / Save PDF</button><button type="button" class="button ghost pro-only" id="downloadJson">Download JSON</button></div><p class="hint">Exports include the reviewed inputs, method, and your notes. Nothing is sent anywhere.</p><details class="pro-only"><summary>Inspect structured output</summary><pre id="reportJson"></pre></details></div></aside></div><section class="help-section"><h2>Understand this review</h2>${helpContent(current)}</section></section>`;
  document.querySelectorAll('[data-route]').forEach(a => { if (a.dataset.route === current) a.setAttribute('aria-current','page'); });
  restoreFields();
  setMode(mode);
  emptyResults();
  $('reviewForm').addEventListener('submit', runReview);
  $('reviewForm').addEventListener('input', () => {
    if (result) { emptyResults(true); liveStatus('Inputs changed. Run the review again to update the findings.'); }
    $('formError').hidden = true;
    stash();
  });
  $('reviewForm').addEventListener('change', () => { if (result) { emptyResults(true); liveStatus('Inputs changed. Run the review again to update the findings.'); } stash(); });
  document.querySelectorAll('[data-mode-choice]').forEach(button => button.onclick = () => setMode(button.dataset.modeChoice));
  $('clearInputs').onclick = clearInputs;
  $('loadExample').onclick = loadExample;
  $('reviewDecision').addEventListener('input', () => { stash(); updateExport(); });
  $('downloadReport').onclick = () => saveDownload(`${current}-review.md`, readableReport(), 'text/markdown');
  $('downloadJson').onclick = () => saveDownload(`${current}-review.json`, JSON.stringify(report(), null, 2), 'application/json');
  $('printReport').onclick = () => { $('printContent').textContent = readableReport(); window.print(); };
  mountGuide();
  document.title = `${t.name} · AI Evaluation Lab`;
}
function helpContent(tool) {
  const paragraphs = {
    neuroeval: [['What the coverage number means','The percentage is the share of your expected concept phrases found in the answer. It is not an accuracy grade. An incorrect or negated statement can still mention every concept.'],['How to set concepts','Use comma-separated concepts. Add explicit alternatives with |, such as “acetylcholine | ACh”. The app normalizes case, spacing, and hyphens; it does not understand synonyms unless you supply them.'],['How to finish','Check the actual question, causal explanation, source support, and omissions. Record your final judgment and notes, then download a readable report.']],
    healthqa: [['What the disposition means','Priority review means urgent wording lacked care guidance or included discouraged care. Review flags means other configured patterns triggered. No pattern flags means only that these rules found no matches. Every result still needs human review.'],['Why context matters','A medication dose may be a quoted textbook example rather than a prescription. A word such as “never” may be justified in context. Read the highlighted excerpt before deciding whether it is an error.'],['What to check next','Verify factual claims and references, consider the audience, and review health guidance with the appropriate qualified reviewer. This app audits writing and does not make patient-care decisions.']],
    pairrank: [['How to rate','Use 1 for a serious problem, 2 for major revisions, 3 for mixed quality, 4 for a strong answer with minor issues, and 5 for an excellent answer for the specific task. Check accuracy against sources before assigning it.'],['How the result is calculated','Each rating is multiplied by its criterion weight; the total is divided by the sum of weights. Pro mode lets you change importance from 0 to 5. A weight of 0 excludes that criterion. An unrounded score difference below 0.15 is labeled a near tie.'],['Who makes the judgment','You do. PairRank computes the ratings you supply; it does not read the answers and decide which is correct. The rationale stays blank for your own text until you write it. Example ratings are explicitly illustrative.']],
    citeguard: [['How to format sources','Use one source per line: SOURCE_ID | actual excerpt. Give every source a unique ID. Copy relevant text from the source; a URL by itself is not an excerpt, and this app does not open links.'],['What a match candidate means','Overlap is the fraction of distinct claim words also found in an excerpt after common words are removed. Matching words can hide a contradiction. Low overlap can still occur with a valid paraphrase. Neither label establishes support.'],['How to verify support','Read the source in context. Check whether it supports, contradicts, or fails to resolve the claim, and whether the source and study scope are appropriate. Record that decision for each claim. Pro mode lets you adjust the overlap threshold.']],
  };
  return `<div class="help-grid">${paragraphs[tool].map(([title,text]) => `<details><summary>${title}</summary><p>${text}</p></details>`).join('')}</div>`;
}
function neuroForm() {
  const t = NEURO_TOPICS[0];
  return step(1, 'Choose what you want to review', chooser('topic','Neuroscience topic','Eight educational topics, or “Other / my own topic” for anything else.',NEURO_TOPICS,t.id) + '<p id="topicNote" class="topic-note"></p>') +
    step(2, 'Add the question and answer', field('prompt','Question or task','What was the AI asked to explain?',t.prompt,'textarea','rows="2"') + field('answer','Answer to review','Paste an AI answer, a student explanation, or your own draft. The app reviews existing text; it does not generate an answer.','','textarea','rows="7" placeholder="Paste the response you want to evaluate…"')) +
    step(3, 'Set the concepts you expect',field('concepts','Expected concepts','Comma-separated phrases. Use | between acceptable alternatives, such as “long-term potentiation | LTP”.',t.concepts,'input') + `<div id="topicReference" class="reference-note"></div><div class="pro-only">${field('referenceNotes','Reference / review context','Optional: paste source context for your own review. It is saved with the report but is not automatically checked.','','textarea','rows="3"')}</div>`);
}
function healthForm() {
  return step(1,'Choose a starting point',chooser('healthExample','Example scenario','Examples demonstrate different kinds of wording; your own content can cover any health topic.',HEALTH_EXAMPLES,'education') + '<p id="exampleLesson" class="topic-note"></p>') +
    step(2,'Add the content to audit',field('healthText','Health-related content','Paste an existing answer or draft. Deliberately problematic examples are labeled for review practice.','','textarea','rows="10" placeholder="Paste the health explanation or AI response…"')) +
    step(3,'Add review context',field('audience','Intended audience / task','Optional: for example, “student learning physiology” or “public educational article”.','','input') + `<div class="pro-only">${field('referenceNotes','Source and context notes','Optional context for the human reviewer; saved with the report.','','textarea','rows="3"')}</div><p class="hint">The audit will show excerpt-level flags and review steps. It does not certify medical safety.</p>`);
}
function ratingRow(criterion) {
  const rating = side => `<select id="${side}_${criterion.name}" aria-label="Response ${side.toUpperCase()} ${criterion.name} rating"><option value="">Rate…</option>${[1,2,3,4,5].map(n => `<option value="${n}">${n}</option>`).join('')}</select>`;
  return `<tr><th scope="row">${criterion.name}<small>${criterion.detail}</small></th><td>${rating('a')}</td><td>${rating('b')}</td><td class="pro-only"><input id="w_${criterion.name}" type="number" min="0" max="5" step="1" value="${criterion.name === 'Accuracy' || criterion.name === 'Safety' ? 3 : 2}" aria-label="${criterion.name} importance weight"></td></tr>`;
}
function pairForm() {
  return step(1,'Give both answers the same task',chooser('pairExample','Comparison example','Explore science or writing examples, then bring your own question and answers.',PAIR_EXAMPLES,'source-scope') + field('prPrompt','Shared question or task','Both responses must answer this same task.','','textarea','rows="2" placeholder="What were both models asked?"') + `<div class="answer-pair">${field('prA','Response A','Paste the first answer.','','textarea','rows="6"')}${field('prB','Response B','Paste the second answer.','','textarea','rows="6"')}</div>`) +
    step(2,'Rate both answers',`<p class="hint">1 = serious problem · 3 = mixed quality · 5 = excellent for this task. Scores are your judgments.</p><div class="table-scroll"><table class="rating-table"><thead><tr><th scope="col">Criterion</th><th scope="col">A</th><th scope="col">B</th><th scope="col" class="pro-only">Weight</th></tr></thead><tbody>${CRITERIA.map(ratingRow).join('')}</tbody></table></div><p class="hint pro-only">Weight 0 excludes a criterion; 5 gives it the greatest importance. At least one weight must be greater than 0.</p>`) +
    step(3,'Explain the comparison',field('prRationale','Your comparison rationale','Explain the evidence behind the ratings. For your own text, write your own rationale before finalizing.','','textarea','rows="3" placeholder="Which answer better meets the task, and why?"') + `<div class="pro-only"><div class="answer-pair">${field('prANotes','A review notes','Optional detail about the first response.','','textarea','rows="2"')}${field('prBNotes','B review notes','Optional detail about the second response.','','textarea','rows="2"')}</div><fieldset class="tags"><legend>Review tags</legend>${['factual error','missing nuance','unsupported claim','unsafe content','instruction following','poor reasoning'].map((x,i) => `<label><input id="tag${i}" type="checkbox" value="${x}">${x}</label>`).join('')}</fieldset></div>`);
}
function citeForm() {
  return step(1,'Add the claims',chooser('citeExample','Citation-review example','Try a contradiction, a scope problem, or a claim with no close source match.',CITE_EXAMPLES,'negation') + '<p id="exampleLesson" class="topic-note"></p>' + field('cgClaims','Claims — one per line','Separate each factual statement so you can review its support individually.','','textarea','rows="5" placeholder="Paste the first claim…\nPaste the next claim…"')) +
    step(2,'Provide the actual source text',field('cgSources','Source excerpts','One per line: SOURCE_ID | excerpt. Use unique IDs; paste relevant text rather than only a URL.','','textarea','rows="7" placeholder="PAPER-01 | Paste a relevant excerpt here.\nBOOK-02 | Paste another excerpt here."') + '<p class="hint">Demo source excerpts are synthetic teaching examples, not external studies.</p>') +
    step(3,'Find candidates, then verify',`<p class="hint">Each candidate is a wording match. After running the audit, read the excerpt and record whether it actually supports the claim.</p><div class="pro-only field"><label for="cgThreshold">Minimum word overlap for a candidate</label><div class="range-wrap"><input id="cgThreshold" type="range" min="5" max="80" step="5" value="25"><output id="cgThresholdValue">25%</output></div><p class="hint">Changes how lexical matches are labeled; it does not change whether a claim is true.</p></div>`);
}
function topicNotes() {
  const t = NEURO_TOPICS.find(t => t.id === $('topic').value) || NEURO_TOPICS[0];
  $('topicNote').textContent = t.id === 'custom' ? 'Use any biology or neuroscience topic. Supply your own question and expected concepts.' : t.review;
  $('topicReference').innerHTML = t.source ? `<span class="group-label">Reference for independent review</span><a href="${esc(t.source[1])}" target="_blank" rel="noopener noreferrer">${esc(t.source[0])} ↗</a><p class="hint">The link is a reading reference. The app does not automatically verify your answer against it.</p>` : '';
  $('loadExample').disabled = t.id === 'custom';
}
function loadExample() {
  const put = (id,value) => { $(id).value = value; };
  if (current === 'neuroeval') {
    const t = NEURO_TOPICS.find(t => t.id === $('topic').value);
    if (!t || t.id === 'custom') return;
    put('prompt',t.prompt); put('answer',t.answer); put('concepts',t.concepts); topicNotes();
  } else if (current === 'healthqa') {
    const e = HEALTH_EXAMPLES.find(e => e.id === $('healthExample').value);
    put('healthText', e.text); $('exampleLesson').textContent = e.lesson;
  } else if (current === 'pairrank') {
    const e = PAIR_EXAMPLES.find(e => e.id === $('pairExample').value);
    put('prPrompt',e.prompt); put('prA',e.a); put('prB',e.b); put('prRationale',e.rationale);
    CRITERIA.forEach((c,i) => { put(`a_${c.name}`,e.ratingsA[i]); put(`b_${c.name}`,e.ratingsB[i]); put(`w_${c.name}`,c.name === 'Accuracy' || c.name === 'Safety' ? 3 : 2); });
    put('prANotes',''); put('prBNotes',''); document.querySelectorAll('.tags input').forEach(e => e.checked = false);
  } else {
    const e = CITE_EXAMPLES.find(e => e.id === $('citeExample').value);
    put('cgClaims', e.claims); put('cgSources', e.sources); $('exampleLesson').textContent = e.lesson;
  }
  exampleLoaded = true;
  $('humanVerdict').value = 'NOT REVIEWED'; $('humanNotes').value = '';
  emptyResults(); $('formError').hidden = true;
  liveStatus(current === 'pairrank' ? 'Example loaded. These ratings and the rationale are illustrative. Review them, then choose “Compare ratings.”' : `Example loaded. Read it, then choose “${TOOLS[current].action}.”`);
  stash();
}
function clearInputs() {
  document.querySelectorAll('#reviewForm textarea, #reviewForm input:not([type=number]):not([type=range]), #reviewDecision textarea').forEach(el => { if (el.type === 'checkbox') el.checked = false; else el.value = ''; });
  document.querySelectorAll('.rating-table select').forEach(el => el.value = '');
  CRITERIA.forEach(c => { if ($(`w_${c.name}`)) $(`w_${c.name}`).value = c.name === 'Accuracy' || c.name === 'Safety' ? 3 : 2; });
  if ($('cgThreshold')) { $('cgThreshold').value = '25'; $('cgThresholdValue').value = '25%'; }
  if ($('exampleLesson')) $('exampleLesson').textContent = '';
  $('humanVerdict').value = 'NOT REVIEWED'; exampleLoaded = false;
  emptyResults(); $('formError').hidden = true;
  try { sessionStorage.removeItem(key); } catch { /* no-op */ }
  liveStatus('Inputs cleared. Paste your own text or try another example.');
}
function metric(label,value) { return `<div class="metric"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`; }
function resultSection(title,content) { return `<section class="result-section"><h3>${title}</h3>${content}</section>`; }
function runReview(event) {
  event.preventDefault();
  $('formError').hidden = true;
  try {
    if (current === 'neuroeval') {
      if (!$('prompt').value.trim()) throw new Error('Add the question or task so the review has context.');
      result = neuroEvaluate($('answer').value, splitConcepts($('concepts').value));
      const c = result.concept_coverage;
      $('resultBody').innerHTML = `<div class="summary-box"><span class="group-label">Concept mentions</span><strong class="big-number">${c.matched}<small> / ${c.expected}</small></strong><p>${c.percent}% of your expected phrases appear in the answer.</p><p class="hint">This measures mention coverage. It is not a factual-accuracy grade.</p></div>${resultSection('Which concepts appear?', `<ul class="concept-list">${c.items.map(x => `<li><span class="pill ${x.mentioned ? 'match' : 'review'}">${x.mentioned ? 'Mentioned' : 'Not found'}</span><span>${esc(x.concept)}</span></li>`).join('')}</ul>`)}${resultSection('Wording signals',Object.entries(result.wording_signals).map(([k,items]) => `<details class="signal"><summary>${({absolute_language:'Absolute wording',causal_language:'Causal wording',evidence_language:'Evidence wording'})[k]} <span>${items.length}</span></summary>${items.length ? items.map(s => `<blockquote>${esc(s)}</blockquote>`).join('') : '<p class="hint">No matches for this pattern.</p>'}</details>`).join('') + '<p class="hint">A word such as “because” does not establish a correct mechanism. Evidence wording does not establish evidence quality.</p>')}${resultSection('What to check next',checklist(['Does the answer address the actual question?', 'Are the mentioned concepts used correctly, including negations?', 'Do the sources support the mechanism and the scope?', 'What needs correction or more detail?']))}`;
    } else if (current === 'healthqa') {
      result = healthAudit($('healthText').value);
      $('resultBody').innerHTML = `<div class="summary-box"><span class="group-label">Wording audit disposition</span><strong class="disposition">${result.disposition}</strong><p>${result.flags.length ? `${result.flags.length} pattern flag${result.flags.length === 1 ? '' : 's'} to inspect in context.` : 'These configured patterns found no flags.'}</p><p class="hint">Human review is still required. This result does not establish safety or correctness.</p></div>${resultSection('Excerpts to review', result.flags.length ? result.flags.map(f => `<article class="flag-card"><h4>${esc(f.label)}</h4><blockquote>${esc(f.excerpt)}</blockquote><p>${esc(f.next)}</p></article>`).join('') : '<p>No pattern flags. Check source support, audience, and context before using the content.</p>')}${resultSection('What to check next',checklist(['Read each flagged excerpt in context.', 'Check health claims against reliable sources.', 'Decide whether wording is appropriate for the intended audience.', 'Record corrections and a human reviewer decision.']))}`;
    } else if (current === 'pairrank') {
      if (['prPrompt','prA','prB'].some(id => !$(id).value.trim())) throw new Error('Add the shared task and both responses before comparing.');
      const weights = {}, scoresA = {}, scoresB = {};
      CRITERIA.forEach(c => { weights[c.name] = +$(`w_${c.name}`).value; scoresA[c.name] = $(`a_${c.name}`).value ? +$(`a_${c.name}`).value : null; scoresB[c.name] = $(`b_${c.name}`).value ? +$(`b_${c.name}`).value : null; });
      result = pairEvaluate({weights,scoresA,scoresB});
      $('resultBody').innerHTML = `<div class="summary-box"><span class="group-label">From your ratings</span><strong class="disposition">${esc(result.preference)}</strong><p>${esc(result.summary)}</p></div><div class="metrics">${metric('Response A',`${result.score_a} / 5`)}${metric('Response B',`${result.score_b} / 5`)}${metric('Difference', result.difference)}</div>${resultSection('Your rationale',$('prRationale').value.trim() ? `<blockquote>${esc($('prRationale').value)}</blockquote>` : '<p class="warning">Write a comparison rationale to make this review complete. No explanation has been generated for you.</p>')}${resultSection('What to check next',checklist(['Check your ratings against the text and reliable sources.', 'Explain meaningful tradeoffs, including any safety problem.', 'Use your written reasoning to make the final preference.', 'Export the record for calibration or further review.']))}`;
    } else {
      const parsed = parseSources($('cgSources').value);
      if (parsed.errors.length) throw new Error(parsed.errors.join(' '));
      result = citationAudit($('cgClaims').value.split('\n').map(s => s.trim()).filter(Boolean),parsed.sources,+$('cgThreshold').value / 100);
      $('resultBody').innerHTML = `<div class="summary-box"><span class="group-label">Sources ready for human review</span><strong class="big-number">${result.claims.length}<small> claim${result.claims.length === 1 ? '' : 's'}</small></strong><p>Match candidates show shared words. Read each excerpt to determine support.</p></div>${result.claims.map(c => `<article class="claim-card"><div class="claim-head"><span>${esc(c.claim_id)}</span><span class="pill ${c.status === 'MATCH CANDIDATE' ? 'match' : 'review'}">${esc(c.status)}</span></div><h3>${esc(c.claim)}</h3><p class="hint">Closest wording match: <b>${esc(c.candidate.id)}</b> · ${Math.round(c.candidate.overlap*100)}% overlap</p><blockquote>${esc(c.candidate.text)}</blockquote>${c.absolute_terms.length ? `<p class="warning">Check absolute wording: ${esc(c.absolute_terms.join(', '))}</p>` : ''}<label for="verify_${c.claim_id}">Your source-support decision</label><select id="verify_${c.claim_id}" data-claim-decision="${c.claim_id}"><option value="NOT REVIEWED">Not reviewed yet</option><option value="SUPPORTS">Supports the claim</option><option value="PARTIAL SUPPORT">Partially supports</option><option value="CONTRADICTS">Contradicts the claim</option><option value="INSUFFICIENT">Insufficient evidence</option></select><p class="hint">Read the original source in context. This decision is yours.</p></article>`).join('')}${resultSection('What to check next',checklist(['Watch for opposite meanings despite shared words.', 'Verify the source’s authenticity, context, and study scope.', 'Retrieve more evidence when needed.', 'Record support separately from the overlap label.']))}`;
      document.querySelectorAll('[data-claim-decision]').forEach(el => el.onchange = () => { citeDecisions[el.dataset.claimDecision] = el.value; updateExport(); });
    }
    $('resultState').textContent = 'Awaiting your review';
    $('exports').hidden = false; $('reviewDecision').hidden = false;
    // A changed input always clears the prior result; keep any existing reviewer notes visible.
    liveStatus('Review complete. Read the results, record your judgment, and download your report.');
    updateExport(); stash();
    $('resultHeading').setAttribute('tabindex', '-1');
    $('resultHeading').focus({preventScroll:true});
    if (window.matchMedia('(max-width: 980px)').matches) $('resultHeading').scrollIntoView({behavior:window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',block:'start'});
  } catch (error) {
    emptyResults();
    $('formError').textContent = error.message; $('formError').hidden = false;
    liveStatus('The review needs the input described above.');
  }
}
function inputs() {
  const data = {};
  document.querySelectorAll('#reviewForm input[id],#reviewForm textarea[id],#reviewForm select[id]').forEach(el => { data[el.id] = el.type === 'checkbox' ? el.checked : el.value; });
  return data;
}
function report() {
  const data = { version: VERSION, tool: TOOLS[current].name, exported_at: new Date().toISOString(), inputs: inputs(), automated_result: result, reviewer: { decision: $('humanVerdict').value, notes: $('humanNotes').value }, method_boundary: 'Browser-only review assistance. Automated patterns do not establish scientific truth, clinical safety, or source support.' };
  if (current === 'neuroeval') data.reading_reference = NEURO_TOPICS.find(t => t.id === $('topic').value)?.source || null;
  if (current === 'citeguard' && result) data.claim_verification = result.claims.map(c => ({claim_id:c.claim_id,decision:citeDecisions[c.claim_id] || 'NOT REVIEWED'}));
  if (current === 'pairrank') data.comparison_rationale = $('prRationale').value;
  return data;
}
function updateExport() {
  if (!result) return;
  $('reportJson').textContent = JSON.stringify(report(),null,2);
  $('resultState').textContent = $('humanVerdict').value === 'NOT REVIEWED' ? 'Awaiting your review' : 'Reviewer decision recorded';
}
function readableReport() {
  if (!result) return '';
  const r = report();
  const lines = [`# ${r.tool} review`, `Version: ${VERSION}`, `Exported: ${r.exported_at}`, '', r.method_boundary, '', '## Inputs'];
  for (const [id,value] of Object.entries(r.inputs)) if (value !== '' && value !== false) {
    const el = $(id), label = document.querySelector(`label[for="${id}"]`);
    const title = label?.textContent || el?.getAttribute('aria-label') || id;
    const display = el?.tagName === 'SELECT' ? el.selectedOptions[0]?.textContent || value : value;
    lines.push(`\n### ${title}\n${display}`);
  }
  lines.push('\n## Review results');
  if (current === 'neuroeval') {
    const c = result.concept_coverage;
    lines.push(`Concept mentions: ${c.matched}/${c.expected} (${c.percent}%). Not a factual-accuracy grade.`,...c.items.map(x => `${x.mentioned ? 'Mentioned' : 'Not found'}: ${x.concept}`));
    for (const [signal,excerpts] of Object.entries(result.wording_signals)) lines.push(`\n${signal.replace(/_/g,' ')}: ${excerpts.length}`, ...excerpts.map(s => `> ${s}`));
    if (r.reading_reference) lines.push('\nReading reference (not automatically checked):',...r.reading_reference);
  } else if (current === 'healthqa') lines.push(result.disposition,...result.flags.flatMap(f => [`\n${f.label}`,`> ${f.excerpt}`,f.next]));
  else if (current === 'pairrank') lines.push(result.preference, `Response A: ${result.score_a}/5; Response B: ${result.score_b}/5; difference: ${result.difference}.`, result.summary);
  else for (const c of result.claims) lines.push(`\n${c.claim_id}: ${c.claim}`, `${c.status}: ${c.candidate.id}; overlap ${Math.round(c.candidate.overlap*100)}%.`,`> ${c.candidate.text}`,`Absolute terms: ${c.absolute_terms.join(', ') || 'none detected'}`);
  lines.push('\n## Method and limits',result.method,'\n## Human reviewer decision',r.reviewer.decision,r.reviewer.notes || 'No review notes recorded.');
  if (r.claim_verification) lines.push('\n## Claim verification',...r.claim_verification.map(c => `${c.claim_id}: ${c.decision}`));
  if (current === 'pairrank' && !$('prRationale').value.trim()) lines.push('\nReview incomplete: no comparison rationale recorded.');
  return lines.join('\n');
}
function saveDownload(name,text,type) {
  if (!result) return;
  const url = URL.createObjectURL(new Blob([text],{type}));
  const a = document.createElement('a'); a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url),1000);
  liveStatus('Report downloaded. It includes your current inputs and review notes.');
}
function mountGuide() {
  const host = $('guide');
  host.innerHTML = `<button class="guide-launcher" type="button" id="openGuide" aria-expanded="false" aria-controls="guidePanel"><span aria-hidden="true">✦</span> Elias · Help</button><section class="guide-panel" id="guidePanel" aria-label="Elias app guide" hidden><div class="guide-heading"><div><strong>Elias · App guide</strong><small>Built-in guidance · no AI model connected</small></div><button class="icon-button" id="closeGuide" type="button" aria-label="Close guide">×</button></div><div class="guide-conversation" id="guideConversation" aria-live="polite"><p class="guide-message">I can help you start a review, understand a result, choose another topic, or export your work.</p></div><div class="guide-shortcuts">${['How do I start?','What do results mean?','Can I use my own topic?','How do I export?'].map(q => `<button type="button" data-guide-question="${esc(q)}">${q}</button>`).join('')}</div><form id="guideForm"><label for="guideQuestion" class="sr-only">Ask about using the app</label><input id="guideQuestion" placeholder="Ask how to use ${TOOLS[current].name}…" maxlength="800"><button type="submit" class="button primary">Ask</button></form></section>`;
  const toggle = open => { $('guidePanel').hidden = !open; $('openGuide').setAttribute('aria-expanded',String(open)); if (open) $('guideQuestion').focus(); else $('openGuide').focus(); };
  $('openGuide').onclick = () => toggle($('guidePanel').hidden);
  $('closeGuide').onclick = () => toggle(false);
  $('guidePanel').addEventListener('keydown',event => { if (event.key === 'Escape') toggle(false); });
  const answer = question => {
    const q = question.toLowerCase(); let text;
    if (/export|download|pdf|save/.test(q)) text = 'Run a review first. “Download readable report” creates a text report with your inputs, results, and notes. “Print / Save PDF” opens your browser print dialog; choose Save as PDF. Pro mode also offers JSON. Downloads stay with you and are not sent anywhere.';
    else if (/privacy|data|cloud|upload|store/.test(q)) text = 'The app runs locally in this browser. Inputs are kept in tab session storage to survive refresh, and are not sent to an AI service. Clear inputs removes this tool’s saved draft. Source URLs are not fetched. Use de-identified text when appropriate.';
    else if (/topic|custom|own|action potential/.test(q)) text = current === 'neuroeval' ? 'Choose synaptic transmission, action potentials, plasticity, myelin, autonomic regulation, the neuromuscular junction, EEG/fMRI, or sleep. For another subject choose “Other / my own topic,” enter your question, paste the answer, and set expected concepts. Use | for explicit alternatives.' : 'All four tools accept your own text. Examples are starting points: HealthQA accepts health-content drafts, PairRank accepts any shared task and two responses, and CiteGuard accepts claims plus labeled source excerpts.';
    else if (/result|score|grade|accur|safe|support|flag|mean/.test(q)) text = ({neuroeval:'Coverage means your chosen phrases were mentioned. It does not grade factual accuracy, understand negation, or check a source. Review the concepts and mechanism yourself, then record a decision.',healthqa:'The disposition describes configured wording flags. “No pattern flags” does not certify safety. Inspect each excerpt in context and record a human review.',pairrank:'Scores come from the ratings you assign. The app multiplies each by its weight and divides by the weight total. It does not judge the answer text. Write the rationale; a difference below 0.15 is a near tie.',citeguard:'A match candidate shares words with a claim. It can still contradict it. Read the source, check its scope, and use the source-support decision dropdown for each claim.'})[current];
    else if (/pro|simple|weight|threshold/.test(q)) text = 'Simple shows the main workflow. Pro adds review context, detailed controls, JSON export, and inspectable output. PairRank adds editable criterion weights; CiteGuard adds an overlap threshold. Switching modes keeps your current inputs.';
    else if (/start|how|use|example|help/.test(q)) text = TOOLS[current].steps.join(' ') + ` You can begin with “Try this example,” read the inputs, then choose “${TOOLS[current].action}.”`;
    else text = 'I am a built-in usage guide and cannot evaluate new scientific or medical questions. I can explain how to start, use your own topic, interpret these results, switch modes, or export. The “Understand this review” section provides more detail.';
    const conversation = $('guideConversation');
    conversation.insertAdjacentHTML('beforeend',`<p class="guide-message user-message">${esc(question)}</p><p class="guide-message">${esc(text)}</p>`); conversation.scrollTop = conversation.scrollHeight;
  };
  $('guideForm').onsubmit = event => { event.preventDefault(); const q = $('guideQuestion').value.trim(); if (q) answer(q); $('guideQuestion').value = ''; };
  document.querySelectorAll('[data-guide-question]').forEach(b => b.onclick = () => answer(b.dataset.guideQuestion));
}
function home() {
  document.title = 'AI Evaluation Lab · Choose a review tool';
  app.innerHTML = `<section class="shell home-shell"><div class="eyebrow">AJ · AI Evaluation Lab</div><h1>Better answers start<br>with a careful review.</h1><p class="lead">Four tools for four different questions. Choose a workflow, try a guided example, then bring your own text.</p><div class="home-grid">${Object.entries(TOOLS).map(([id,t]) => `<article class="home-card"><span class="tool-symbol">${t.symbol}</span><span class="eyebrow">${t.short}</span><h2>${t.name}</h2><p>${t.lead}</p><ul>${t.steps.map(s => `<li>${s}</li>`).join('')}</ul><a class="button primary" href="/${id}">Open ${t.name} →</a></article>`).join('')}</div><div class="home-note"><h2>Bring the answer. Keep the judgment.</h2><p>These tools review existing text. NeuroEval, HealthQA, and CiteGuard use visible text patterns; PairRank computes your human ratings. Every review shows its method and leaves the final decision with you.</p><p>Runs in your browser. No account, API key, or paid model call required.</p></div></section>`;
}
if (current === 'home') home();
else {
  frame(({neuroeval:neuroForm,healthqa:healthForm,pairrank:pairForm,citeguard:citeForm})[current]());
  if (current === 'neuroeval') {
    topicNotes();
    $('topic').onchange = () => {
      const t = NEURO_TOPICS.find(t => t.id === $('topic').value);
      $('prompt').value = t.prompt; $('concepts').value = t.concepts;
      // Leave an existing answer available until the user explicitly loads another example.
      $('referenceNotes').value = '';
      $('humanVerdict').value = 'NOT REVIEWED'; $('humanNotes').value = '';
      topicNotes(); emptyResults(); stash();
      liveStatus(t.id === 'custom' ? 'Enter your own question and concepts. You can edit the existing answer or paste a new one.' : 'Topic selected. Update the answer for this question, or choose “Try this example” to replace it.');
    };
  }
  if ($('cgThreshold')) {
    $('cgThresholdValue').value = `${$('cgThreshold').value}%`;
    $('cgThreshold').addEventListener('input', () => $('cgThresholdValue').value = `${$('cgThreshold').value}%`);
  }
}
