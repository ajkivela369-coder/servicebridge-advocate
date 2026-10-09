// These baselines flag text patterns. They do not verify scientific truth.
export const VERSION = '2.0.0';
const normalize = value => String(value ?? '').toLowerCase().normalize('NFKC').replace(/[–—-]/g, ' ').replace(/[^\p{L}\p{N}+]+/gu, ' ').replace(/\s+/g, ' ').trim();
const sentences = text => String(text).match(/[^.!?\n]+[.!?]?/g) || [];
const unique = values => [...new Set(values)];
export const splitConcepts = value => unique(String(value).split(/[,\n]/).map(x => x.trim()).filter(Boolean));
export function conceptMatches(answer, concepts) {
  const text = ' ' + normalize(answer) + ' ';
  return concepts.map(concept => ({ concept, mentioned: concept.split('|').some(alias => {
    const normalized = normalize(alias);
    return normalized && text.includes(' ' + normalized + ' ');
  }) }));
}
export function neuroEvaluate(answer, concepts) {
  if (!String(answer).trim()) throw new Error('Paste an answer or load an example before reviewing.');
  if (!concepts.length) throw new Error('Add at least one expected concept so the review has a reference.');
  const coverage = conceptMatches(answer, concepts);
  const matched = coverage.filter(x => x.mentioned).length;
  const find = pattern => unique(sentences(answer).filter(s => pattern.test(s)).map(s => s.trim()));
  return {
    concept_coverage: { matched, expected: concepts.length, percent: Math.round(100 * matched / concepts.length), items: coverage },
    wording_signals: {
      absolute_language: find(/\b(always|never|proves|guarantees?|definitely|certainly|every)\b/i),
      causal_language: find(/\b(because|therefore|causes?|via|through|leads? to|results? in)\b/i),
      evidence_language: find(/\b(stud(?:y|ies)|evidence|research|trial|data|according to|review)\b/i),
    },
    word_count: String(answer).trim().split(/\s+/).length,
    method: 'Normalized phrase matching with explicit aliases and wording-pattern detection. Mentions, negations, correctness, mechanism quality, evidence quality, and prompt relevance need human review.',
    human_review_required: true,
  };
}
const HEALTH_PATTERNS = [
  ['Dosing / prescription wording', /\b\d+(?:\.\d+)?\s*(?:mg|mcg|ml|milligrams?|micrograms?)\b|\b(?:take|increase|stop|double)\b.{0,35}\b(?:dose|medication|prescription|tablets?)\b/i, 'Check whether this is an educational quotation or an instruction to a person, and whether its context supports it.'],
  ['Diagnostic certainty', /\byou (?:definitely |certainly )?have\b|\bthis is (?:definitely|certainly)\b/i, 'Check whether the response assigns a diagnosis without a justified assessment.'],
  ['Absolute health claim', /\b(always|never|guaranteed|definitely|certainly|proves|cures?)\b/i, 'Check scope, source support, and whether the certainty is justified.'],
];
export function healthAudit(text) {
  if (!String(text).trim()) throw new Error('Paste health-related content or load an example before auditing.');
  const flags = HEALTH_PATTERNS.flatMap(([label, pattern, next]) => sentences(text).filter(s => pattern.test(s)).map(s => ({ label, excerpt: s.trim(), next })));
  const urgent = sentences(text).filter(s => /\b(chest pain|difficulty breathing|unconscious|stroke|suicidal|severe bleeding|anaphylaxis)\b/i.test(s));
  const guidance = sentences(text).filter(s => /\b(emergency|911|urgent|seek (?:care|help)|clinician|doctor|medical professional)\b/i.test(s));
  const discouragingGuidance = guidance.filter(s => /\b(do not|don['’]t|no need|avoid|unnecessary|not necessary)\b.{0,50}\b(?:seek|call|care|help|emergency|urgent|doctor|clinician)\b/i.test(s));
  const discouragesCare = discouragingGuidance.length > 0;
  const missingEscalation = urgent.length > 0 && (guidance.length === 0 || discouragesCare);
  if (missingEscalation) flags.unshift({ label: discouragesCare ? 'Urgent wording with discouraged care' : 'Urgent wording without care guidance', excerpt: unique([...urgent,...discouragingGuidance]).map(s => s.trim()).join(' '), next: 'Route this content to a qualified human reviewer before using it. Check context and escalation wording.' });
  return { disposition: missingEscalation ? 'PRIORITY REVIEW' : flags.length ? 'REVIEW FLAGS' : 'NO PATTERN FLAGS', flags, urgent_wording: urgent.map(s => s.trim()), guidance_wording: guidance.map(s => s.trim()), human_review_required: true, method: 'Rule-based content audit. No flags means these patterns were not triggered; it does not establish safety, clinical appropriateness, or factual accuracy.' };
}
export const CRITERIA = [
  { name: 'Accuracy', detail: 'Is the answer correct when checked against reliable evidence?' },
  { name: 'Relevance', detail: 'Does it answer the actual question and follow the instructions?' },
  { name: 'Reasoning', detail: 'Are the explanation and conclusions justified?' },
  { name: 'Clarity', detail: 'Is it understandable, organized, and appropriately concise?' },
  { name: 'Safety', detail: 'Does it avoid harmful instructions and unjustified certainty?' },
];
export function pairEvaluate({ weights, scoresA, scoresB }) {
  const names = CRITERIA.map(c => c.name);
  if (names.some(n => !Number.isFinite(weights[n]) || weights[n] < 0 || weights[n] > 5)) throw new Error('Each weight must be between 0 and 5.');
  const denominator = names.reduce((sum, n) => sum + weights[n], 0);
  if (!denominator) throw new Error('Give at least one criterion a weight greater than zero.');
  if (names.some(n => weights[n] > 0 && (![scoresA[n], scoresB[n]].every(v => Number.isInteger(v) && v >= 1 && v <= 5)))) throw new Error('Rate both answers for each active criterion before comparing.');
  const weighted = scores => names.reduce((sum, n) => sum + (weights[n] ? scores[n] * weights[n] : 0), 0) / denominator;
  const a = weighted(scoresA), b = weighted(scoresB);
  const preference = Math.abs(a - b) < 0.15 ? 'NEAR TIE' : a > b ? 'A SCORES HIGHER' : 'B SCORES HIGHER';
  const winner = a > b ? 'A' : 'B', loser = winner === 'A' ? 'B' : 'A';
  return { score_a: +a.toFixed(2), score_b: +b.toFixed(2), preference, difference: +Math.abs(a - b).toFixed(2), summary: preference === 'NEAR TIE' ? 'The weighted ratings differ by less than 0.15 on the 1–5 scale. Review the tradeoffs before choosing.' : `Response ${winner} has the higher weighted rating (${weighted(winner === 'A' ? scoresA : scoresB).toFixed(2)} vs ${weighted(loser === 'A' ? scoresA : scoresB).toFixed(2)}). Your written rationale should explain the evidence behind those ratings.`, method: 'Human ratings weighted by importance. A near tie means an unrounded difference below 0.15. Text is not automatically judged, and no rationale is invented.' };
}
const STOP = new Set('the a an and or of to in is are was were for with that this on as by be from it can may not no do does'.split(' '));
const citeTokens = text => new Set(normalize(text).split(' ').filter(w => w.length > 2 && !STOP.has(w)));
export function lexicalOverlap(claim, source) {
  const c = citeTokens(claim), s = citeTokens(source);
  return c.size ? [...c].filter(w => s.has(w)).length / c.size : 0;
}
export function parseSources(value) {
  const sources = [], errors = [], ids = new Set();
  String(value).split('\n').forEach((line, index) => {
    if (!line.trim()) return;
    const split = line.indexOf('|'), id = line.slice(0, split).trim(), text = line.slice(split + 1).trim();
    if (split < 1 || !id || !text) errors.push(`Source line ${index + 1}: use a unique source ID, a | separator, and a non-empty excerpt.`);
    else if (ids.has(id.toLowerCase())) errors.push(`Source line ${index + 1}: ${id} repeats an existing source ID.`);
    else { ids.add(id.toLowerCase()); sources.push({ id, text }); }
  });
  return { sources, errors };
}
export function citationAudit(claims, sources, threshold = 0.25) {
  if (!claims.length) throw new Error('Add at least one claim, one per line.');
  if (!sources.length) throw new Error('Add a source excerpt using SOURCE_ID | excerpt.');
  if (!Number.isFinite(threshold) || threshold < 0.05 || threshold > 0.8) throw new Error('Choose an overlap threshold between 5% and 80%.');
  const records = claims.map((claim, i) => {
    const matches = sources.map(source => ({ ...source, overlap: lexicalOverlap(claim, source.text) })).sort((a, b) => b.overlap - a.overlap);
    const best = matches[0];
    const terms = unique(claim.match(/\b(proves?|proven|always|never|guarantees?|certainly|definitively|impossible|every|cures?)\b/gi) || []);
    const status = terms.length ? 'REVIEW WORDING' : best.overlap >= threshold ? 'MATCH CANDIDATE' : 'LOW OVERLAP';
    return { claim_id: `C${String(i + 1).padStart(2, '0')}`, claim, status, absolute_terms: terms, candidate: { ...best, overlap: +best.overlap.toFixed(3) }, verification: 'NOT REVIEWED' };
  });
  return { threshold, claims: records, human_review_required: true, method: 'Fraction of unique non-stopword claim tokens also present in a source excerpt. Ranking is lexical, so negation, contradiction, paraphrase, study quality, and source authenticity need human verification. Source URLs are not fetched.' };
}
