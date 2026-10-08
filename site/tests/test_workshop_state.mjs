import test from 'node:test';
import assert from 'node:assert/strict';
import state from '../lib/workshop-state.js';
const { DEFAULT_STATE, HEARTS, MODES, createDefaultState, normalizeState, encodeState, decodeStateHash, graphemeLength, truncateGraphemes } = state;

test('defaults are a fresh, exact state', () => {
  assert.deepEqual(createDefaultState(), DEFAULT_STATE);
  assert.deepEqual(DEFAULT_STATE, { version: 1, mode: 'signal', signal: [], note: '', noteHeart: '01-heart', rhythm: [] });
});

test('valid state round-trips through a versioned URL hash', () => {
  const source = {
    version: 1,
    mode: 'rhythm',
    signal: ['01-heart', '27-ira-heart'],
    note: 'Привет 👩‍🚀',
    noteHeart: '03-heart-open',
    rhythm: [1, 4, 2, 4],
  };
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
  const state = normalizeState({ version: 1, mode: 'nope', signal: ['01-heart', 'bogus', 4], note: 42, noteHeart: 'nope', rhythm: [1, 9, '2', 0], pointer: { x: 4, y: 2 }, extra: true });
  assert.deepEqual(state, { version: 1, mode: 'signal', signal: ['01-heart'], note: '', noteHeart: '01-heart', rhythm: [1] });
  assert.equal('pointer' in state, false);
  assert.deepEqual(normalizeState({ mode: 'letter', signal: ['01-heart', 'bogus'], noteHeart: '27-ira-heart', rhythm: [1, 2] }), {
    version: 1, mode: 'letter', signal: ['01-heart'], note: '', noteHeart: '27-ira-heart', rhythm: [1, 2],
  });
});

test('notes are limited by Unicode grapheme clusters', () => {
  const note = 'a'.repeat(119) + '👩‍🚀';
  assert.equal(graphemeLength(note), 120);
  assert.equal(graphemeLength(note + 'x'), 121);
  assert.equal(graphemeLength(truncateGraphemes(note + 'x', 120)), 120);
  assert.equal(normalizeState({ note: note + 'x' }).note, note);
});

test('signal and rhythm are capped and state never stores pointer coordinates', () => {
  const state = normalizeState({ mode: 'signal', signal: [...HEARTS, '01-heart', '02-heart-double'], rhythm: Array.from({ length: 40 }, (_, i) => (i % 4) + 1), pointerX: 12, pointerY: 40 });
  assert.equal(state.signal.length, 4);
  assert.equal(state.rhythm.length, 32);
  assert.equal('pointerX' in state, false);
  assert.equal('pointerY' in state, false);
  assert.ok(MODES.includes(state.mode));
});
