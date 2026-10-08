/* Pure, dependency-free Fondy workshop state and URL hash codec.
 * The file is both a browser namespace and a CommonJS module for tests. */
(function workshopStateFactory(global, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (global) global.FondyState = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function createWorkshopStateApi() {
  'use strict';

  const VERSION = 1;
  const MODES = Object.freeze(['signal', 'pause', 'letter', 'rhythm']);
  const HEARTS = Object.freeze(['01-heart', '02-heart-double', '03-heart-open', '27-ira-heart']);
  const DEFAULT_STATE = Object.freeze({
    version: VERSION,
    mode: 'signal',
    signal: Object.freeze([]),
    note: '',
    noteHeart: '01-heart',
    rhythm: Object.freeze([]),
  });
  const MAX_NOTE = 120;
  const MAX_SIGNAL = 4;
  const MAX_RHYTHM = 32;
  const MAX_HASH_LENGTH = 16384;
  const HEART_SET = new Set(HEARTS);
  const MODE_SET = new Set(MODES);

  function createDefaultState() {
    return {
      version: VERSION,
      mode: DEFAULT_STATE.mode,
      signal: [],
      note: '',
      noteHeart: DEFAULT_STATE.noteHeart,
      rhythm: [],
    };
  }

  function segments(value) {
    const text = value == null ? '' : String(value);
    // Intl.Segmenter handles combining marks, ZWJ emoji and regional flags.
    if (typeof Intl !== 'undefined' && typeof Intl.Segmenter === 'function') {
      try { return Array.from(new Intl.Segmenter(undefined, { granularity: 'grapheme' }).segment(text), part => part.segment); } catch (_) { /* use fallback */ }
    }
    // The fallback keeps surrogate pairs together. Combining sequences are joined
    // where possible; it remains safe even in older embedded browsers.
    const codepoints = Array.from(text);
    const result = [];
    for (const point of codepoints) {
      if (result.length && (/\p{Mark}/u.test(point) || point === '\u200d' || /[\ufe00-\ufe0f]/u.test(point))) result[result.length - 1] += point;
      else result.push(point);
    }
    return result;
  }

  function graphemeLength(value) { return segments(value).length; }
  function truncateGraphemes(value, max = MAX_NOTE) { return segments(value).slice(0, Math.max(0, max | 0)).join(''); }

  function normalizeState(input) {
    const source = input && typeof input === 'object' ? input : {};
    const state = createDefaultState();
    state.mode = MODE_SET.has(source.mode) ? source.mode : DEFAULT_STATE.mode;
    const sourceSignal = Array.isArray(source.signal) ? source.signal : [];
    state.signal = sourceSignal.filter(value => HEART_SET.has(value)).slice(0, MAX_SIGNAL);
    state.note = typeof source.note === 'string' ? truncateGraphemes(source.note, MAX_NOTE) : '';
    state.noteHeart = HEART_SET.has(source.noteHeart) ? source.noteHeart : DEFAULT_STATE.noteHeart;
    const sourceRhythm = Array.isArray(source.rhythm) ? source.rhythm : [];
    state.rhythm = sourceRhythm
      .filter(value => Number.isInteger(value) && value >= 1 && value <= 4)
      .slice(0, MAX_RHYTHM);
    // The public shape is deliberately reconstructed from the whitelist above.
    return state;
  }

  function bytesToBase64(bytes) {
    if (typeof Buffer !== 'undefined') return Buffer.from(bytes).toString('base64');
    let binary = '';
    for (let index = 0; index < bytes.length; index += 0x8000) binary += String.fromCharCode(...bytes.subarray(index, index + 0x8000));
    return btoa(binary);
  }

  function textToBase64(text) {
    if (typeof TextEncoder !== 'undefined') return bytesToBase64(new TextEncoder().encode(text));
    if (typeof Buffer !== 'undefined') return Buffer.from(text, 'utf8').toString('base64');
    return btoa(unescape(encodeURIComponent(text)));
  }

  function base64ToText(value) {
    const padded = value.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - value.length % 4) % 4);
    if (!/^[A-Za-z0-9+/]*={0,2}$/.test(padded)) throw new Error('invalid base64');
    if (typeof Buffer !== 'undefined') return Buffer.from(padded, 'base64').toString('utf8');
    const binary = atob(padded);
    if (typeof TextDecoder !== 'undefined') return new TextDecoder().decode(Uint8Array.from(binary, char => char.charCodeAt(0)));
    return decodeURIComponent(escape(binary));
  }

  function encodeState(input) {
    const state = normalizeState(input);
    const json = JSON.stringify(state);
    return '#v1=' + textToBase64(json).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
  }

  function parseStateHash(hash) {
    const value = typeof hash === 'string' ? hash : '';
    if (!value || value.length > MAX_HASH_LENGTH || !/^#v1=/.test(value)) return { state: createDefaultState(), valid: false };
    const payload = value.slice(4);
    if (!payload || payload.length > MAX_HASH_LENGTH || !/^[A-Za-z0-9_-]+$/.test(payload)) return { state: createDefaultState(), valid: false };
    try {
      const parsed = JSON.parse(base64ToText(payload));
      if (!parsed || typeof parsed !== 'object' || parsed.version !== VERSION) return { state: createDefaultState(), valid: false };
      return { state: normalizeState(parsed), valid: true };
    } catch (_) { return { state: createDefaultState(), valid: false }; }
  }

  function decodeStateHash(hash) { return parseStateHash(hash).state; }
  function decodeStateHashResult(hash) { return parseStateHash(hash); }

  return Object.freeze({
    VERSION, MODES, HEARTS, MAX_NOTE, MAX_SIGNAL, MAX_RHYTHM, DEFAULT_STATE,
    createDefaultState, graphemeLength, truncateGraphemes, normalizeState,
    encodeState, decodeStateHash, decodeStateHashResult,
    // Friendly aliases used by small integrations and manual tests.
    encodeHash: encodeState,
    decodeHash: decodeStateHash,
    stateToHash: encodeState,
    stateFromHash: decodeStateHash,
  });
});
