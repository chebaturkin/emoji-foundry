import test from 'node:test';
import assert from 'node:assert/strict';
import state from '../lib/workshop-state.js';
const { DEFAULT_STATE, TOKENS, MODES, TOKEN_LIMIT, createDefaultState, normalizeState, encodeState, decodeStateHash, graphemeLength, truncateGraphemes } = state;

test('defaults are a fresh Signal state', () => {
  assert.deepEqual(createDefaultState(), DEFAULT_STATE);
  assert.deepEqual(DEFAULT_STATE, { version: 1, mode: 'signal', signal: [], note: '', noteToken: 'pulse', rhythm: [] });
  assert.deepEqual(TOKENS, ['pulse', 'spark', 'wave', 'anchor']);
  assert.equal(TOKEN_LIMIT, 4);
});

test('valid state round-trips through a versioned URL hash', () => {
  const source = { version: 1, mode: 'rhythm', signal: ['pulse', 'anchor'], note: 'Привет 👩‍🚀', noteToken: 'wave', rhythm: [1, 4, 2, 4] };
  const hash = encodeState(source);
  assert.match(hash, /^#v1=/);
  assert.deepEqual(decodeStateHash(hash), normalizeState(source));
});

test('malformed and stale hashes safely fall back to defaults', () => {
  assert.deepEqual(decodeStateHash('#v1=not-base64'), DEFAULT_STATE);
  assert.deepEqual(decodeStateHash('#v2=eyJ2ZXJzaW9uIjoxfQ'), DEFAULT_STATE);
  assert.deepEqual(decodeStateHash('#v1=' + 'A'.repeat(20000)), DEFAULT_STATE);
  assert.deepEqual(decodeStateHash(''), DEFAULT_STATE);
});

test('unknown fields and invalid values are stripped', () => {
  const value = normalizeState({ version: 1, mode: 'nope', signal: ['pulse', 'bogus', 4], note: 42, noteToken: 'nope', rhythm: [1, 9, '2', 0], pointer: { x: 4, y: 2 }, extra: true });
  assert.deepEqual(value, { version: 1, mode: 'signal', signal: ['pulse'], note: '', noteToken: 'pulse', rhythm: [1] });
  assert.equal('pointer' in value, false);
  assert.deepEqual(normalizeState({ mode: 'letter', signal: ['pulse', 'bogus'], noteToken: 'anchor', rhythm: [1, 2] }), { version: 1, mode: 'letter', signal: ['pulse'], note: '', noteToken: 'anchor', rhythm: [1, 2] });
});

test('notes are limited by Unicode grapheme clusters', () => {
  const note = 'a'.repeat(119) + '👩‍🚀';
  assert.equal(graphemeLength(note), 120);
  assert.equal(graphemeLength(note + 'x'), 121);
  assert.equal(graphemeLength(truncateGraphemes(note + 'x', 120)), 120);
  assert.equal(normalizeState({ note: note + 'x' }).note, note);
});

test('signal and rhythm are capped and state never stores pointer coordinates', () => {
  const value = normalizeState({ mode: 'signal', signal: [...TOKENS, 'pulse', 'spark'], rhythm: Array.from({ length: 40 }, (_, i) => (i % 4) + 1), pointerX: 12, pointerY: 40 });
  assert.equal(value.signal.length, TOKEN_LIMIT);
  assert.equal(value.rhythm.length, 32);
  assert.equal('pointerX' in value, false);
  assert.equal('pointerY' in value, false);
  assert.ok(MODES.includes(value.mode));
});
