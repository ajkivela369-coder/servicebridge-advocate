import test from 'node:test';
import assert from 'node:assert/strict';
import { splitConcepts, conceptMatches, neuroEvaluate, healthAudit, pairEvaluate, CRITERIA, parseSources, citationAudit } from '../engine.js';
import { NEURO_TOPICS, HEALTH_EXAMPLES, PAIR_EXAMPLES } from '../examples.js';

test('empty reviews cannot produce favorable findings', () => {
  assert.throws(() => neuroEvaluate('', ['calcium']), /Paste an answer/);
  assert.throws(() => neuroEvaluate('Some answer', []), /at least one expected/);
  assert.throws(() => healthAudit(''), /Paste health/);
  assert.throws(() => citationAudit([], [{id:'X',text:'source'}]), /at least one claim/);
  assert.throws(() => citationAudit(['claim'], []), /source excerpt/);
});
test('concept coverage stays a mention check even when the answer is wrong or negated', () => {
  const result = neuroEvaluate('Calcium does not cause vesicles to release neurotransmitter at receptors.', ['calcium','vesicles','neurotransmitter','receptors']);
  assert.equal(result.concept_coverage.percent, 100);
  assert.equal(result.human_review_required, true);
  assert.equal('factuality' in result, false);
  assert.equal('total' in result, false);
  assert.match(result.method, /negations/);
});
test('concept aliases are explicit and whole phrases avoid accidental substring matches', () => {
  assert.equal(conceptMatches('ACh acts at the receptor.', ['acetylcholine | ACh'])[0].mentioned, true);
  assert.equal(conceptMatches('The recovered data describe history.', ['cover'])[0].mentioned, false);
  assert.equal(conceptMatches('Voltage-gated channels', ['voltage gated'])[0].mentioned, true);
});
test('all eight educational neuroscience topics use their own concepts and references', () => {
  const topics = NEURO_TOPICS.filter(t => t.id !== 'custom');
  assert.equal(topics.length, 8);
  assert.equal(new Set(topics.map(t => t.prompt)).size, 8);
  for (const topic of topics) {
    assert.equal(neuroEvaluate(topic.answer, splitConcepts(topic.concepts)).concept_coverage.percent, 100, topic.name);
    assert.match(topic.source[1], /^https:\/\//);
  }
});
test('no-pattern health results still require a human; negated care guidance is not treated as escalation', () => {
  const clean = healthAudit(HEALTH_EXAMPLES.find(e => e.id === 'education').text);
  assert.equal(clean.disposition, 'NO PATTERN FLAGS');
  assert.equal(clean.human_review_required, true);
  const urgent = healthAudit(HEALTH_EXAMPLES.find(e => e.id === 'urgent').text);
  assert.equal(urgent.disposition, 'PRIORITY REVIEW');
  assert.ok(urgent.flags.some(f => f.label === 'Urgent wording with discouraged care'));
  assert.match(urgent.flags[0].excerpt,/Do not seek care/);
  assert.equal(healthAudit('Chest pain can be serious. Seek urgent care.').disposition, 'NO PATTERN FLAGS');
  assert.equal(healthAudit('Chest pain is mentioned here.').disposition, 'PRIORITY REVIEW');
});
test('prescription and diagnostic excerpts remain visible for context review', () => {
  const text = HEALTH_EXAMPLES.find(e => e.id === 'dosing').text;
  const result = healthAudit(text);
  assert.ok(result.flags.some(f => f.label === 'Dosing / prescription wording' && f.excerpt.includes('50 mg')));
  assert.ok(result.flags.some(f => f.label === 'Diagnostic certainty'));
});
const weights = Object.fromEntries(CRITERIA.map(c => [c.name, 1]));
const ratings = value => Object.fromEntries(CRITERIA.map(c => [c.name, value]));
test('PairRank handles A, B, and near-tie outcomes without inventing a rationale', () => {
  const a = pairEvaluate({weights,scoresA:ratings(5),scoresB:ratings(2)});
  const b = pairEvaluate({weights,scoresA:ratings(2),scoresB:ratings(5)});
  const tie = pairEvaluate({weights,scoresA:ratings(4),scoresB:ratings(4)});
  assert.equal(a.preference, 'A SCORES HIGHER');
  assert.equal(b.preference, 'B SCORES HIGHER');
  assert.match(b.summary, /Response B has the higher/);
  assert.equal(tie.preference,'NEAR TIE');
  assert.equal('rationale' in b,false);
});
test('PairRank rejects all-zero weights and missing ratings; excludes inactive criteria', () => {
  assert.throws(() => pairEvaluate({weights:ratings(0),scoresA:ratings(4),scoresB:ratings(3)}), /at least one criterion/);
  assert.throws(() => pairEvaluate({weights,scoresA:{...ratings(4),Safety:null},scoresB:ratings(3)}), /Rate both/);
  const w = {...ratings(0),Accuracy:5};
  const r = pairEvaluate({weights:w,scoresA:{Accuracy:5},scoresB:{Accuracy:1}});
  assert.equal(r.score_a,5); assert.equal(r.score_b,1);
});
test('the writing example produces a B preference, not a stock A preference', () => {
  const e = PAIR_EXAMPLES.find(e => e.id === 'instructions');
  const toScores = a => Object.fromEntries(CRITERIA.map((c,i) => [c.name,a[i]]));
  assert.equal(pairEvaluate({weights,scoresA:toScores(e.ratingsA),scoresB:toScores(e.ratingsB)}).preference,'B SCORES HIGHER');
});
test('source parsing refuses malformed lines, empty excerpts, and duplicate identities', () => {
  assert.equal(parseSources('A | Useful excerpt').errors.length,0);
  assert.equal(parseSources('Useful excerpt without identity').errors.length,1);
  assert.equal(parseSources('A | ').errors.length,1);
  assert.equal(parseSources('A | first\na | second').errors.length,1);
});
test('contradictory high-overlap text is never labeled supported automatically', () => {
  const r = citationAudit(['The treatment improved memory in the study.'],[{id:'S1',text:'The treatment did not improve memory in the study.'}]);
  assert.equal(r.claims[0].status,'MATCH CANDIDATE');
  assert.equal(r.claims[0].verification,'NOT REVIEWED');
  assert.equal(r.human_review_required,true);
  assert.match(r.method,/contradiction/);
});
test('CiteGuard separates absolute wording and low-overlap claims from candidate matches', () => {
  const sources = [{id:'S1',text:'Myelin insulates axons and supports faster conduction.'}];
  assert.equal(citationAudit(['Myelin always improves conduction.'],sources).claims[0].status,'REVIEW WORDING');
  assert.equal(citationAudit(['Circadian clocks regulate sleep timing.'],sources).claims[0].status,'LOW OVERLAP');
});
