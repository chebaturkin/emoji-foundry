/* Signal workshop runtime. It only talks to native data-* hooks in workshop.html. */
(() => {
  'use strict';

  const root = document.querySelector('[data-workshop-root]');
  if (!root) return;

  const fallbackState = {
    VERSION: 1,
    MODES: ['signal', 'pause', 'letter', 'rhythm'],
    TOKENS: ['pulse', 'spark', 'wave', 'anchor'],
    MAX_NOTE: 120, MAX_SIGNAL: 4, MAX_RHYTHM: 32,
    createDefaultState: () => ({ version: 1, mode: 'signal', signal: [], note: '', noteToken: 'pulse', rhythm: [] }),
    graphemeLength: text => Array.from(String(text || '')).length,
    truncateGraphemes: (text, max) => Array.from(String(text || '')).slice(0, max || 120).join(''),
    normalizeState(input) {
      const state = this.createDefaultState();
      const source = input && typeof input === 'object' ? input : {};
      if (this.MODES.includes(source.mode)) state.mode = source.mode;
      state.signal = Array.isArray(source.signal) ? source.signal.filter(item => this.TOKENS.includes(item)).slice(0, 4) : [];
      state.note = typeof source.note === 'string' ? this.truncateGraphemes(source.note, 120) : '';
      if (this.TOKENS.includes(source.noteToken)) state.noteToken = source.noteToken;
      state.rhythm = Array.isArray(source.rhythm) ? source.rhythm.filter(item => Number.isInteger(item) && item > 0 && item < 5).slice(0, 32) : [];
      return state;
    },
    encodeState(input) {
      const state = this.normalizeState(input);
      let payload;
      try { payload = btoa(unescape(encodeURIComponent(JSON.stringify(state)))); } catch (_) { payload = ''; }
      return '#v1=' + payload.replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '');
    },
    decodeStateHash(hash) {
      const value = typeof hash === 'string' ? hash : '';
      if (!/^#v1=[A-Za-z0-9_-]+$/.test(value)) return this.createDefaultState();
      try {
        const encoded = value.slice(4).replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - value.slice(4).length % 4) % 4);
        const decoded = JSON.parse(decodeURIComponent(escape(atob(encoded))));
        return decoded && decoded.version === 1 ? this.normalizeState(decoded) : this.createDefaultState();
      } catch (_) { return this.createDefaultState(); }
    },
  };
  const State = window.SignalState || fallbackState;
  const DEFAULT_STATE = State.createDefaultState();
  const modes = Array.from(State.MODES || ['signal', 'pause', 'letter', 'rhythm']);
  const tokens = Array.from(State.TOKENS || ['pulse', 'spark', 'wave', 'anchor']);
  const tokenSet = new Set(tokens);
  const tokenNames = { pulse: 'пульс', spark: 'искра', wave: 'волна', anchor: 'якорь' };
  const signalLimit = State.TOKEN_LIMIT || State.MAX_SIGNAL || 4;
  const rhythmLimit = State.MAX_RHYTHM || 32;

  const status = root.querySelector('[data-workshop-status]');
  const modeButtons = Array.from(root.querySelectorAll('[data-workshop-mode]'));
  const scenes = Array.from(root.querySelectorAll('[data-workshop-scene]'));
  const actions = Array.from(root.querySelectorAll('[data-workshop-action]'));
  const mascot = root.querySelector('[data-fondy-mascot]');
  const mascotWrap = root.querySelector('[data-fondy-wrap]');
  const timers = new Set();
  const rafs = new Set();
  let state = State.decodeStateHash ? State.decodeStateHash(location.hash) : { ...DEFAULT_STATE };
  let draftNote = '';
  let draftNoteToken = state.noteToken || 'pulse';
  let rhythmEvents = state.rhythm.map((pad, index) => ({ pad, at: index * 240 }));
  let lastAction = null;
  let activeMode = state.mode;
  let destroyed = false;
  let drag = null;
  let ignoreChoiceClickUntil = 0;
  let pauseStep = 0;
  let pauseHolding = false;
  let pauseHoldStarted = 0;
  let pauseDelayTimer = null;
  let signalAnimationTimer = null;
  let rhythmReplayToken = 0;
  let pointerFrame = null;
  let pointerLast = null;
  let idleObserver = null;

  const later = (callback, delay) => {
    const id = window.setTimeout(() => { timers.delete(id); callback(); }, delay);
    timers.add(id);
    return id;
  };
  const cancelTimer = id => { if (id != null) { window.clearTimeout(id); timers.delete(id); } };
  const cancelAllTimers = () => { timers.forEach(id => window.clearTimeout(id)); timers.clear(); };
  const cancelRaf = id => { if (id != null) { window.cancelAnimationFrame(id); rafs.delete(id); } };
  const cancelAllRafs = () => { rafs.forEach(id => window.cancelAnimationFrame(id)); rafs.clear(); };
  const announce = message => { if (status) status.textContent = message; };
  const sceneFor = mode => scenes.find(scene => scene.dataset.workshopScene === mode);
  const activeScene = () => sceneFor(activeMode);
  const glyphShapes = {
    pulse: '<circle cx="50" cy="50" r="28"/><path d="M14 50h18l7-13 10 27 8-17h29"/>',
    spark: '<path d="M50 8l7 30 30 12-30 7-7 35-8-35-30-7 30-12z"/>',
    wave: '<path d="M8 55c12-26 24-26 36 0s24 26 36 0 24-26 36 0"/>',
    anchor: '<circle cx="50" cy="24" r="10"/><path d="M50 34v45M34 55h32M22 70c7 14 19 21 28 21s21-7 28-21"/>',
  };
  const glyphSvg = token => `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" aria-hidden="true" focusable="false"><g fill="none" stroke="currentColor" stroke-width="7" stroke-linecap="round" stroke-linejoin="round">${glyphShapes[token] || glyphShapes.pulse}</g></svg>`;
  const glyphDataUri = token => utf8DataUri(glyphSvg(token));
  const isReducedMotion = () => Boolean(window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches);

  function commitState(next, message) {
    state = State.normalizeState ? State.normalizeState(next) : next;
    try { history.replaceState(null, '', State.encodeState(state)); } catch (_) { try { location.hash = State.encodeState(state).slice(1); } catch (__) { /* private/file contexts */ } }
    renderState();
    if (message) announce(message);
  }

  function setMode(mode, options = {}) {
    const nextMode = modes.includes(mode) ? mode : modes[0];
    if (nextMode !== activeMode) cancelSceneWork();
    activeMode = nextMode;
    // Rendering the current state must stay pure. Calling commitState here would
    // render again, which would call setMode again and recurse forever.
    if (state.mode !== nextMode) commitState({ ...state, mode: nextMode });
    modeButtons.forEach(button => {
      const selected = button.dataset.workshopMode === nextMode;
      button.classList.toggle('is-active', selected);
      button.setAttribute('aria-selected', String(selected));
      button.tabIndex = selected ? 0 : -1;
      if (!button.getAttribute('role')) button.setAttribute('role', 'tab');
      if (selected && options.focus) button.focus();
    });
    scenes.forEach(scene => {
      const selected = scene.dataset.workshopScene === nextMode;
      scene.hidden = !selected;
      scene.classList.toggle('is-active', selected);
      if (!scene.getAttribute('role')) scene.setAttribute('role', 'tabpanel');
    });
    root.dataset.workshopActiveMode = nextMode;
    root.dataset.workshopMode = nextMode;
    root.classList.remove('is-signal', 'is-pause', 'is-letter', 'is-rhythm');
    root.classList.add(`is-${nextMode}`);
    if (options.announce !== false) {
      const button = modeButtons.find(item => item.dataset.workshopMode === nextMode);
      if (button) announce(`сцена: ${button.textContent.trim().replace(/^\d+/, '').trim()}`);
    }
    if (nextMode === 'pause') renderPause();
    if (nextMode === 'rhythm') renderRhythm();
  }

  function cancelSceneWork() {
    cancelAllTimers();
    cancelAllRafs();
    rhythmReplayToken += 1;
    if (signalAnimationTimer) cancelTimer(signalAnimationTimer);
    signalAnimationTimer = null;
    pauseDelayTimer = null;
    pauseHolding = false;
    cancelDrag();
    if (mascot) mascot.style.transform = '';
    if (mascotWrap) mascotWrap.classList.remove('is-reacting');
    root.querySelectorAll('.is-pulsing, .is-playing, .is-dragging, .is-drop-target').forEach(node => node.classList.remove('is-pulsing', 'is-playing', 'is-dragging', 'is-drop-target'));
  }

  function renderState() {
    state = State.normalizeState ? State.normalizeState(state) : state;
    renderTokenChoices();
    renderSignal();
    renderLetter();
    renderPause();
    renderRhythm();
    setMode(activeMode, { announce: false });
  }

  function renderTokenChoices() {
    root.querySelectorAll('[data-token]').forEach(button => {
      const art = button.querySelector('.token-choice-art');
      if (art) art.innerHTML = glyphSvg(button.dataset.token);
    });
  }

  function createGlyph(token, className = '') {
    const glyph = document.createElement('span');
    glyph.className = className;
    glyph.dataset.token = token;
    glyph.innerHTML = glyphSvg(token);
    glyph.setAttribute('aria-hidden', 'true');
    return glyph;
  }

  function renderSignal() {
    const slots = Array.from(root.querySelectorAll('[data-signal-slot]'));
    const count = root.querySelector('[data-signal-count]');
    if (count) count.textContent = `${state.signal.length} / ${signalLimit}`;
    slots.forEach((slot, index) => {
      slot.replaceChildren();
      slot.dataset.filled = state.signal[index] || '';
      slot.classList.remove('is-filled');
      const number = document.createElement('span');
      number.textContent = String(index + 1).padStart(2, '0');
      number.className = 'signal-slot-number';
      slot.append(number);
      if (!state.signal[index]) return;
      slot.classList.add('is-filled');
      const glyph = createGlyph(state.signal[index], 'signal-slot-glyph');
      glyph.setAttribute('aria-label', `знак ${index + 1}: ${tokenNames[state.signal[index]] || state.signal[index]}`);
      slot.append(glyph);
      const controls = document.createElement('span');
      controls.className = 'signal-slot-controls';
      const remove = slotButton('убрать знак', '×');
      remove.addEventListener('click', event => { event.stopPropagation(); removeSignal(index); });
      controls.append(remove);
      if (index > 0) {
        const left = slotButton('сдвинуть влево', '←');
        left.addEventListener('click', event => { event.stopPropagation(); reorderSignal(index, index - 1); });
        controls.append(left);
      }
      if (index < state.signal.length - 1) {
        const right = slotButton('сдвинуть вправо', '→');
        right.addEventListener('click', event => { event.stopPropagation(); reorderSignal(index, index + 1); });
        controls.append(right);
      }
      slot.append(controls);
    });
    const result = root.querySelector('[data-signal-result]');
    if (result) {
      result.textContent = state.signal.length ? `сигнал собран: ${state.signal.map(name => tokenNames[name] || name).join(' · ')}` : 'здесь появится твой сигнал';
    }
    root.querySelectorAll('[data-signal-undo]').forEach(button => { button.disabled = !state.signal.length; });
  }

  function slotButton(label, text) {
    const button = document.createElement('button');
    button.type = 'button'; button.className = 'signal-slot-button'; button.setAttribute('aria-label', label); button.textContent = text;
    return button;
  }

  function addSignalToken(token, message = 'знак добавлен в сигнал') {
    if (!tokenSet.has(token)) return false;
    if (state.signal.length >= signalLimit) { announce('сигнал уже собран из четырёх знаков'); return false; }
    const signal = state.signal.concat(token);
    lastAction = { type: 'signal', signal: signal.slice() };
    commitState({ ...state, signal }, message);
    react('signal');
    return true;
  }
  function removeSignal(index) {
    if (index < 0 || index >= state.signal.length) return;
    const signal = state.signal.slice(); signal.splice(index, 1);
    lastAction = { type: 'signal', signal: signal.slice() };
    commitState({ ...state, signal }, 'знак убран из сигнала');
  }
  function reorderSignal(from, to) {
    if (from < 0 || to < 0 || from >= state.signal.length || to >= state.signal.length) return;
    const signal = state.signal.slice(); [signal[from], signal[to]] = [signal[to], signal[from]];
    lastAction = { type: 'signal', signal: signal.slice() };
    commitState({ ...state, signal }, 'порядок сигнала изменён');
  }

  function renderLetter() {
    const field = root.querySelector('[data-letter-note]');
    const counter = root.querySelector('[data-letter-count]');
    if (field && document.activeElement !== field && field.value !== draftNote) field.value = draftNote;
    if (counter) counter.textContent = `${State.graphemeLength ? State.graphemeLength(draftNote) : Array.from(draftNote).length} / 120`;
    root.querySelectorAll('[data-note-token]').forEach(button => {
      const selected = button.dataset.noteToken === draftNoteToken;
      button.classList.toggle('is-selected', selected);
      button.setAttribute('aria-pressed', String(selected));
      const glyph = button.querySelector('.token-glyph');
      if (glyph) glyph.innerHTML = glyphSvg(button.dataset.noteToken);
    });
    const token = root.querySelector('[data-envelope-token]');
    if (token) {
      token.className = `envelope-token token-art-${draftNoteToken}`;
      token.innerHTML = glyphSvg(draftNoteToken);
      token.dataset.envelopeToken = draftNoteToken;
    }
    const note = root.querySelector('[data-envelope-note]');
    if (note && !state.note) note.textContent = 'твой текст\nостанется здесь';
    if (note && state.note) note.textContent = state.note;
    const result = root.querySelector('[data-letter-result]');
    if (result) result.textContent = state.note ? 'записка сложена — можно поделиться' : 'конверт ждёт записку';
  }

  function renderPause() {
    const progress = root.querySelector('[data-pause-progress]');
    const label = root.querySelector('[data-pause-progress-label]');
    if (progress) progress.value = pauseStep;
    if (label) label.textContent = `${pauseStep} / 4`;
    root.querySelectorAll('[data-pause-step]').forEach(button => {
      const step = Number(button.dataset.pauseStep);
      button.classList.toggle('is-current', step === pauseStep + 1 && pauseStep < 4);
      button.classList.toggle('is-complete', step <= pauseStep);
      button.setAttribute('aria-pressed', String(step <= pauseStep));
    });
    const message = root.querySelector('[data-pause-message]');
    if (message) message.textContent = pauseStep >= 4 ? 'пауза собрана — Фонди рядом' : ['начни с первого шага', 'удержи момент', 'отпусти, когда будешь готов', 'останься ещё немного'][Math.min(pauseStep, 3)];
  }

  function startPauseStep(event) {
    const button = event.currentTarget;
    const step = Number(button.dataset.pauseStep);
    if (step !== pauseStep + 1 || pauseStep >= 4 || pauseHolding) return;
    pauseHolding = true; pauseHoldStarted = performance.now();
    button.classList.add('is-holding');
    root.querySelector('[data-pause-stage]')?.classList.add('is-holding');
    if (event.pointerId != null && button.setPointerCapture) { try { button.setPointerCapture(event.pointerId); } catch (_) { /* unsupported */ } }
    announce(`шаг ${step}: удерживай и отпусти`);
  }
  function finishPauseStep(event) {
    const button = event.currentTarget;
    if (!pauseHolding) return;
    pauseHolding = false; button.classList.remove('is-holding');
    root.querySelector('[data-pause-stage]')?.classList.remove('is-holding');
    if (event.pointerId != null && button.releasePointerCapture) { try { button.releasePointerCapture(event.pointerId); } catch (_) { /* already released */ } }
    pauseStep = Math.min(4, pauseStep + 1);
    lastAction = { type: 'pause', step: pauseStep };
    renderPause();
    react('pause');
    announce(pauseStep >= 4 ? 'пауза собрана — Фонди рядом' : `шаг ${pauseStep} готов`);
    if (pauseStep < 4 && !isReducedMotion()) pauseDelayTimer = later(() => { pauseDelayTimer = null; renderPause(); }, 5000);
  }
  function skipPause() {
    pauseHolding = false; cancelTimer(pauseDelayTimer); pauseDelayTimer = null;
    pauseStep = Math.min(4, pauseStep + 1); lastAction = { type: 'pause', step: pauseStep }; renderPause();
    announce(pauseStep >= 4 ? 'пауза собрана — шаги пройдены' : `шаг пропущен — следующий: ${pauseStep + 1}`);
  }
  function restartPause(quiet = false) {
    pauseHolding = false; pauseStep = 0; cancelTimer(pauseDelayTimer); pauseDelayTimer = null; renderPause();
    if (!quiet) announce('пауза начнётся заново');
  }

  function renderRhythm() {
    const count = root.querySelector('[data-rhythm-count]');
    if (count) count.textContent = `${state.rhythm.length} / ${rhythmLimit}`;
    const result = root.querySelector('[data-rhythm-result]');
    if (result) result.textContent = state.rhythm.length ? state.rhythm.join(' · ') : 'ритм пока пустой';
  }

  function commitBeat(pad) {
    const value = Number(pad);
    if (!Number.isInteger(value) || value < 1 || value > 4) return false;
    if (state.rhythm.length >= rhythmLimit) { announce('ритм уже собран из 32 ударов'); return false; }
    const now = performance.now();
    const previous = rhythmEvents[rhythmEvents.length - 1];
    rhythmEvents.push({ pad: value, at: previous ? Math.max(previous.at + 16, now) : now });
    const rhythm = state.rhythm.concat(value);
    lastAction = { type: 'rhythm', events: rhythmEvents.map(item => ({ ...item })) };
    commitState({ ...state, rhythm }, 'удар добавлен в ритм');
    pulsePad(value);
    react('rhythm');
    return true;
  }
  function pulsePad(value) {
    const button = root.querySelector(`[data-rhythm-pad="${value}"]`);
    if (!button) return;
    button.classList.remove('is-pulsing'); void button.offsetWidth; button.classList.add('is-pulsing');
    const bars = root.querySelectorAll('.rhythm-bars i');
    const bar = bars[Math.max(0, state.rhythm.length - 1) % Math.max(1, bars.length)];
    if (bar) { bar.classList.remove('is-hit'); void bar.offsetWidth; bar.classList.add('is-hit'); }
    later(() => {
      button.classList.remove('is-pulsing');
      if (bar) bar.classList.remove('is-hit');
    }, isReducedMotion() ? 0 : 160);
  }
  function replayRhythm(events) {
    if (!events || !events.length) { announce('ритм пока пустой'); return; }
    cancelSceneWork();
    const token = ++rhythmReplayToken;
    const origin = events[0].at;
    events.forEach(event => {
      const delay = isReducedMotion() ? 0 : Math.max(0, Math.min(8000, event.at - origin));
      later(() => { if (token === rhythmReplayToken && activeMode === 'rhythm') pulsePad(event.pad); }, delay);
    });
    announce('ритм повторяется в исходном темпе');
  }

  function react(mode) {
    if (!mascotWrap) return;
    mascotWrap.classList.remove('is-reacting', 'react-signal', 'react-letter', 'react-pause', 'react-rhythm');
    mascotWrap.classList.add('is-reacting', `react-${mode}`);
    cancelTimer(signalAnimationTimer);
    signalAnimationTimer = later(() => mascotWrap.classList.remove('is-reacting', `react-${mode}`), isReducedMotion() ? 0 : 620);
  }

  function onLetterInput(event) {
    const value = event.currentTarget.value;
    const max = State.MAX_NOTE || 120;
    draftNote = State.truncateGraphemes ? State.truncateGraphemes(value, max) : Array.from(value).slice(0, max).join('');
    if (event.currentTarget.value !== draftNote) event.currentTarget.value = draftNote;
    renderLetter();
  }
  function submitLetter(event) {
    event.preventDefault();
    state = State.normalizeState({ ...state, note: draftNote, noteToken: draftNoteToken });
    lastAction = { type: 'letter', note: draftNote, noteToken: draftNoteToken };
    commitState(state, draftNote ? 'записка сложена в конверт' : 'пустая записка сложена в конверт');
    const envelope = root.querySelector('[data-envelope]');
    if (envelope) { envelope.classList.remove('is-folded'); void envelope.offsetWidth; envelope.classList.add('is-folded'); }
    react('letter');
  }

  function attachSignalDrag(button) {
    button.addEventListener('pointerdown', event => {
      if (event.pointerType === 'mouse' && event.button !== 0) return;
      const token = button.dataset.token;
      drag = { button, token, pointerId: event.pointerId, startX: event.clientX, startY: event.clientY, moved: false, captured: false };
      button.classList.add('is-pressed');
      later(() => { if (drag && drag.button === button && !drag.moved) drag.longPress = true; }, 120);
      try { button.setPointerCapture(event.pointerId); drag.captured = true; } catch (_) { /* capture optional */ }
    });
    button.addEventListener('pointermove', event => {
      if (!drag || drag.button !== button || event.pointerId !== drag.pointerId) return;
      const distance = Math.hypot(event.clientX - drag.startX, event.clientY - drag.startY);
      if (distance < 8 && !drag.longPress) return;
      drag.moved = true; button.classList.add('is-dragging');
      event.preventDefault();
      const stage = root.querySelector('[data-signal-stage]');
      const bounds = stage && stage.getBoundingClientRect();
      const inside = bounds && event.clientX >= bounds.left && event.clientX <= bounds.right && event.clientY >= bounds.top && event.clientY <= bounds.bottom;
      if (stage) stage.classList.toggle('is-drop-target', Boolean(inside));
    });
    button.addEventListener('pointerup', event => finishSignalDrag(event, button));
    button.addEventListener('pointercancel', () => cancelDrag(button));
    button.addEventListener('lostpointercapture', event => { if (drag && drag.button === button && !drag.moved) cancelDrag(button); });
    button.addEventListener('click', event => {
      if (Date.now() < ignoreChoiceClickUntil) { event.preventDefault(); return; }
      addSignalToken(button.dataset.token);
    });
  }
  function finishSignalDrag(event, button) {
    if (!drag || drag.button !== button) return;
    const current = drag; const stage = root.querySelector('[data-signal-stage]');
    const bounds = stage && stage.getBoundingClientRect();
    const inside = bounds && event.clientX >= bounds.left && event.clientX <= bounds.right && event.clientY >= bounds.top && event.clientY <= bounds.bottom;
    if (current.moved && inside) { event.preventDefault(); addSignalToken(current.token, 'знак добавлен перетаскиванием'); ignoreChoiceClickUntil = Date.now() + 450; }
    else if (current.moved) ignoreChoiceClickUntil = Date.now() + 450;
    cancelDrag(button);
  }
  function cancelDrag(button) {
    if (!drag || (button && drag.button !== button)) return;
    const current = drag; drag = null; current.button.classList.remove('is-dragging', 'is-pressed');
    const stage = root.querySelector('[data-signal-stage]'); if (stage) stage.classList.remove('is-drop-target');
    if (current.captured && current.button.releasePointerCapture) { try { current.button.releasePointerCapture(current.pointerId); } catch (_) { /* already released */ } }
  }

  function copyText(text) {
    if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') return navigator.clipboard.writeText(text);
    return new Promise((resolve, reject) => {
      const field = document.createElement('textarea'); field.value = text; field.setAttribute('readonly', ''); field.style.position = 'fixed'; field.style.opacity = '0';
      document.body.append(field); field.select();
      try { if (!document.execCommand('copy')) throw new Error('copy failed'); resolve(); } catch (error) { reject(error); } finally { field.remove(); }
    });
  }
  async function copyLink() {
    const hash = State.encodeState ? State.encodeState(state) : '';
    const url = `${location.origin === 'null' ? location.href.split('#')[0] : location.href.split('#')[0]}${hash}`;
    try {
      await copyText(url);
      const local = /^(localhost|127\.0\.0\.1|\[::1\])$/.test(location.hostname);
      announce(local ? 'ссылка скопирована — локальный адрес работает только на этом компьютере' : 'ссылка скопирована — состояние живёт в адресе');
    } catch (_) { announce('не удалось скопировать — адрес можно взять из строки браузера'); }
  }

  function xmlEscape(value) {
    return String(value == null ? '' : value).replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;' }[character]));
  }
  function utf8DataUri(text, mime = 'image/svg+xml') {
    try {
      const bytes = new TextEncoder().encode(text); let binary = '';
      for (const byte of bytes) binary += String.fromCharCode(byte);
      return `data:${mime};base64,${btoa(binary)}`;
    } catch (_) { return `data:${mime},${encodeURIComponent(text)}`; }
  }
  async function fileDataUri(url, fallbackMime = 'image/png') {
    try {
      const response = await fetch(url, { credentials: 'same-origin' });
      if (!response.ok) throw new Error('asset unavailable');
      const blob = await response.blob();
      return await new Promise((resolve, reject) => { const reader = new FileReader(); reader.onload = () => resolve(reader.result); reader.onerror = reject; reader.readAsDataURL(blob); });
    } catch (_) { return url ? `${url}` : `data:${fallbackMime},`; }
  }
  async function mascotDataUri() {
    const image = root.querySelector('[data-fondy-mascot]');
    if (!image) return '';
    try {
      const response = await fetch(image.currentSrc || image.src, { credentials: 'same-origin' });
      if (!response.ok) throw new Error('mascot unavailable');
      return utf8DataUri(await response.text());
    } catch (_) { return image.currentSrc || image.src; }
  }

  const exportPalette = {
    paper: '#FFF4DF', ink: '#171717', blue: '#2457FF', orange: '#FF6B35',
    yellow: '#F4D35E', softBlue: '#DFE5FF', softOrange: '#FFE1D6', line: '#D9CFBD',
  };
  const modeTitles = {
    signal: 'собрать сигнал', pause: 'поймать паузу', letter: 'свернуть записку', rhythm: 'сыграть ритм',
  };

  function wrapExportText(value, maxChars = 30, maxLines = 6) {
    const words = String(value || '').trim().split(/\s+/).filter(Boolean);
    if (!words.length) return [];
    const lines = [];
    let line = '';
    words.forEach(word => {
      const pieces = Array.from(word);
      while (pieces.length > maxChars) {
        if (line) { lines.push(line); line = ''; }
        lines.push(pieces.splice(0, maxChars).join(''));
      }
      const candidate = line ? `${line} ${pieces.join('')}` : pieces.join('');
      if (line && Array.from(candidate).length > maxChars) { lines.push(line); line = pieces.join(''); }
      else line = candidate;
    });
    if (line) lines.push(line);
    if (lines.length <= maxLines) return lines;
    const clipped = lines.slice(0, maxLines);
    const last = Array.from(clipped[maxLines - 1]);
    if (last.length >= 2) last.splice(Math.max(0, last.length - 2), 2, '…');
    clipped[maxLines - 1] = last.join('');
    return clipped;
  }

  function svgLines(lines, x, y, lineHeight, attributes = '') {
    return lines.map((line, index) => `<tspan x="${x}" y="${y + index * lineHeight}" ${attributes}>${xmlEscape(line)}</tspan>`).join('');
  }

  function svgImage(uri, x, y, width, height, extra = '') {
    if (!uri) return '';
    return `<image href="${xmlEscape(uri)}" x="${x}" y="${y}" width="${width}" height="${height}" preserveAspectRatio="xMidYMid meet" ${extra}/>`;
  }

  function svgTokenRow(uris, y = 360) {
    const size = 170; const gap = 24; const startX = 90;
    return uris.map((uri, index) => {
      const x = startX + index * (size + gap);
      return `<rect x="${x}" y="${y}" width="${size}" height="${size}" rx="28" fill="${exportPalette.paper}" opacity=".98"/>${svgImage(uri, x + 18, y + 18, size - 36, size - 36)}`;
    }).join('');
  }

  function exportHeader(title, mascotUri) {
    return `<text x="92" y="94" fill="${exportPalette.ink}" font-family="EF Onest, sans-serif" font-size="22" font-weight="700" letter-spacing="1.5">SIGNAL / ФОНДИ</text><circle cx="1090" cy="80" r="10" fill="${exportPalette.orange}"/><circle cx="1120" cy="80" r="6" fill="${exportPalette.blue}"/><text x="92" y="194" fill="${exportPalette.ink}" font-family="EF Dela, sans-serif" font-size="74" letter-spacing="-2">${xmlEscape(title)}</text>${svgImage(mascotUri, 1040, 118, 260, 268)}`;
  }

  async function exportSvg() {
    if (document.fonts && document.fonts.ready) { try { await document.fonts.ready; } catch (_) { /* fonts are optional */ } }
    const title = modeTitles[activeMode] || modeTitles.signal;
    const tokenIds = activeMode === 'signal' && state.signal.length ? state.signal : [state.noteToken || state.signal[state.signal.length - 1] || 'pulse'];
    const [tokenUris, mascotUri] = await Promise.all([Promise.resolve(tokenIds.map(name => glyphDataUri(name))), mascotDataUri()]);
    const noteLines = wrapExportText(state.note || 'собери свой жест', 31, 6);
    const signalLabels = state.signal.map(name => tokenNames[name] || name);
    let body = '';
    if (activeMode === 'signal') {
      body = `<rect x="78" y="288" width="1244" height="425" rx="36" fill="${exportPalette.blue}"/><text x="112" y="336" fill="${exportPalette.paper}" opacity=".7" font-family="EF Onest, sans-serif" font-size="18" font-weight="700" letter-spacing="1">ТВОЙ СИГНАЛ · ${state.signal.length}/4</text>${state.signal.length ? svgTokenRow(tokenUris, 380) : `<text x="112" y="500" fill="${exportPalette.paper}" opacity=".82" font-family="EF Onest, sans-serif" font-size="29">добавь первый знак в мастерской</text>`}<text x="92" y="816" fill="${exportPalette.ink}" font-family="EF Onest, sans-serif" font-size="26" font-weight="700">${xmlEscape(signalLabels.length ? signalLabels.join('  ·  ') : 'сигнал пока пустой')}</text>`;
    } else if (activeMode === 'letter') {
      const tokenUri = tokenUris[0];
      body = `<rect x="78" y="288" width="1244" height="450" rx="36" fill="${exportPalette.orange}"/><rect x="116" y="340" width="622" height="326" rx="22" fill="${exportPalette.paper}" transform="rotate(-2 427 503)"/><text x="160" y="408" fill="${exportPalette.ink}" opacity=".55" font-family="EF Onest, sans-serif" font-size="16" font-weight="700" letter-spacing="1">ТВОЯ ЗАПИСКА</text><text x="160" y="466" fill="${exportPalette.ink}" font-family="EF Dela, sans-serif" font-size="34" letter-spacing="-.6">${svgLines(noteLines, 160, 466, 43)}</text>${svgImage(tokenUri, 630, 560, 72, 72)}<path d="M838 388h340l-170 142-170-142Z" fill="${exportPalette.paper}"/><path d="M838 388v280h340V388" fill="none" stroke="${exportPalette.ink}" stroke-opacity=".18" stroke-width="4"/><path d="M838 668l170-142 170 142" fill="none" stroke="${exportPalette.blue}" stroke-width="8" stroke-linejoin="round"/><text x="860" y="735" fill="${exportPalette.ink}" font-family="EF Onest, sans-serif" font-size="19" font-weight="700">сложено Фонди · можно отправлять</text>`;
    } else if (activeMode === 'pause') {
      const dots = Array.from({ length: 4 }, (_, index) => { const x = 150 + index * 270; const done = index < pauseStep; return `<circle cx="${x}" cy="480" r="76" fill="${done ? exportPalette.orange : exportPalette.paper}"/><text x="${x}" y="492" text-anchor="middle" fill="${exportPalette.ink}" font-family="EF Dela, sans-serif" font-size="38">0${index + 1}</text>`; }).join('');
      body = `<rect x="78" y="288" width="1244" height="430" rx="36" fill="${exportPalette.ink}"/>${dots}<path d="M226 610H1034" stroke="${exportPalette.paper}" stroke-opacity=".28" stroke-width="3" stroke-dasharray="9 14"/><text x="112" y="784" fill="${exportPalette.ink}" font-family="EF Onest, sans-serif" font-size="28" font-weight="700">${pauseStep >= 4 ? 'пауза собрана — Фонди рядом' : `пройдено шагов: ${pauseStep} из 4`}</text>`;
    } else {
      const bars = state.rhythm.length ? state.rhythm.map((pad, index) => { const x = 112 + index * 34; const h = 56 + (pad * 18); const color = [exportPalette.orange, exportPalette.yellow, exportPalette.paper, exportPalette.softBlue][(pad - 1) % 4]; return `<rect x="${x}" y="${632 - h}" width="20" height="${h}" rx="8" fill="${color}"/>`; }).join('') : `<text x="112" y="500" fill="${exportPalette.paper}" opacity=".82" font-family="EF Onest, sans-serif" font-size="29">нажми клавиши 1–4, чтобы оставить ритм</text>`;
      body = `<rect x="78" y="288" width="1244" height="430" rx="36" fill="${exportPalette.blue}"/><text x="112" y="338" fill="${exportPalette.paper}" opacity=".72" font-family="EF Onest, sans-serif" font-size="18" font-weight="700" letter-spacing="1">ТВОЙ РИСУНОК · ${state.rhythm.length}/32</text><line x1="112" y1="632" x2="1220" y2="632" stroke="${exportPalette.paper}" stroke-opacity=".25" stroke-width="3"/>${bars}<text x="92" y="816" fill="${exportPalette.ink}" font-family="EF Onest, sans-serif" font-size="26" font-weight="700">${xmlEscape(state.rhythm.length ? state.rhythm.join('  ·  ') : 'ритм пока пустой')}</text>`;
    }
    return `<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="900" viewBox="0 0 1400 900" role="img" aria-labelledby="export-title export-description"><title id="export-title">${xmlEscape(title)}</title><desc id="export-description">Открытка из мастерской Фонди</desc><rect width="1400" height="900" rx="48" fill="${exportPalette.paper}"/>${exportHeader(title, mascotUri)}${body}<text x="92" y="862" fill="${exportPalette.ink}" opacity=".55" font-family="EF Onest, sans-serif" font-size="17">собрано в браузере · без аккаунта и отправки данных</text></svg>`;
  }
  function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob); const link = document.createElement('a'); link.href = url; link.download = filename; link.rel = 'noopener';
    document.body.append(link); link.click(); link.remove(); window.setTimeout(() => URL.revokeObjectURL(url), 0);
  }
  async function exportPng() {
    const svg = await exportSvg();
    if (!document.createElement('canvas').getContext) { downloadBlob(new Blob([svg], { type: 'image/svg+xml' }), 'signal-postcard.svg'); announce('PNG недоступен — сохранён SVG'); return; }
    const canvas = document.createElement('canvas'); canvas.width = 1400; canvas.height = 900;
    const context = canvas.getContext('2d');
    if (!context) { downloadBlob(new Blob([svg], { type: 'image/svg+xml' }), 'signal-postcard.svg'); announce('PNG недоступен — сохранён SVG'); return; }
    const url = URL.createObjectURL(new Blob([svg], { type: 'image/svg+xml;charset=utf-8' }));
    try {
      const image = new Image(); image.decoding = 'async'; image.src = url;
      if (image.decode) { try { await image.decode(); } catch (_) { await new Promise(resolve => { image.onload = resolve; image.onerror = resolve; }); } }
      context.drawImage(image, 0, 0, 1400, 900);
      const blob = await new Promise(resolve => canvas.toBlob ? canvas.toBlob(resolve, 'image/png') : resolve(null));
      if (!blob) { downloadBlob(new Blob([svg], { type: 'image/svg+xml' }), 'signal-postcard.svg'); announce('PNG недоступен — сохранён SVG'); return; }
      downloadBlob(blob, 'signal-postcard.png'); announce('PNG готов — файл сохранён');
    } finally { URL.revokeObjectURL(url); }
  }

  async function createPortableHtml() {
    const [svg, delaUri, onestUri] = await Promise.all([
      exportSvg(),
      fileDataUri('assets/fonts/dela-gothic-one.woff2', 'font/woff2'),
      fileDataUri('assets/fonts/onest-variable.woff2', 'font/woff2'),
    ]);
    const title = modeTitles[activeMode] || modeTitles.signal;
    const style = `@font-face{font-family:'EF Dela';src:url('${delaUri}') format('woff2');font-display:swap}@font-face{font-family:'EF Onest';src:url('${onestUri}') format('woff2');font-display:swap}html,body{margin:0;min-height:100%;background:#efe5d3}body{display:grid;place-items:center;padding:32px;box-sizing:border-box;font-family:'EF Onest',sans-serif}.postcard{width:min(1400px,100%);margin:auto}.postcard svg{display:block;width:100%;height:auto;box-shadow:0 24px 80px rgba(23,23,23,.16);border-radius:28px}.postcard p{margin:18px 0 0;color:#5c554c;text-align:center;font-size:14px}.postcard strong{color:#171717}`;
    return `<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>${xmlEscape(title)} · Фонди</title><style>${style}</style></head><body><main class="postcard" aria-label="Открытка из мастерской Фонди">${svg}<p><strong>${xmlEscape(title)}</strong> · открытка собрана локально в браузере</p></main></body></html>`;
  }
  async function downloadPortable() {
    try { downloadBlob(new Blob([await createPortableHtml()], { type: 'text/html;charset=utf-8' }), 'signal-postcard.html'); announce('открытка сохранена — её можно открыть отдельно'); } catch (_) { announce('не удалось собрать открытку'); }
  }

  function resetCurrentScene() {
    cancelSceneWork();
    if (activeMode === 'signal') { commitState({ ...state, signal: [] }, 'сигнал сброшен — можно собрать заново'); }
    else if (activeMode === 'letter') { draftNote = ''; draftNoteToken = 'pulse'; commitState({ ...state, note: '', noteToken: 'pulse' }, 'записка сброшена — можно написать заново'); }
    else if (activeMode === 'pause') { restartPause(true); announce('пауза сброшена — можно начать заново'); }
    else if (activeMode === 'rhythm') { rhythmEvents = []; commitState({ ...state, rhythm: [] }, 'ритм сброшен — можно сыграть заново'); }
  }
  function repeatCurrent() {
    if (activeMode === 'signal') { if (!state.signal.length) { announce('сигнал пока пустой'); return; } react('signal'); announce('сигнал повторяется'); }
    else if (activeMode === 'letter') { if (!state.note) { announce('сначала сложи записку'); return; } const envelope = root.querySelector('[data-envelope]'); if (envelope) envelope.classList.toggle('is-folded'); react('letter'); announce('записка повторяется'); }
    else if (activeMode === 'pause') { restartPause(); }
    else if (activeMode === 'rhythm') replayRhythm((lastAction && lastAction.type === 'rhythm' ? lastAction.events : rhythmEvents).slice());
  }

  modeButtons.forEach(button => {
    button.addEventListener('click', () => setMode(button.dataset.workshopMode, { focus: false }));
    button.addEventListener('keydown', event => {
      const index = modeButtons.indexOf(button);
      let next = null;
      if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = modeButtons[(index + 1) % modeButtons.length];
      if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = modeButtons[(index - 1 + modeButtons.length) % modeButtons.length];
      if (event.key === 'Home') next = modeButtons[0];
      if (event.key === 'End') next = modeButtons[modeButtons.length - 1];
      if (!next) return;
      event.preventDefault();
      next.focus();
      setMode(next.dataset.workshopMode, { focus: false });
    });
  });
  root.querySelectorAll('.token-choice[data-token]').forEach(attachSignalDrag);
  root.querySelectorAll('[data-signal-undo]').forEach(button => button.addEventListener('click', () => removeSignal(state.signal.length - 1)));
  root.querySelectorAll('[data-note-token]').forEach(button => button.addEventListener('click', () => { draftNoteToken = tokenSet.has(button.dataset.noteToken) ? button.dataset.noteToken : 'pulse'; renderLetter(); }));
  root.querySelectorAll('[data-letter-note]').forEach(field => field.addEventListener('input', onLetterInput));
  root.querySelectorAll('[data-letter-form]').forEach(form => form.addEventListener('submit', submitLetter));
  root.querySelectorAll('[data-pause-step]').forEach(button => {
    button.addEventListener('pointerdown', startPauseStep); button.addEventListener('pointerup', finishPauseStep); button.addEventListener('pointercancel', () => { pauseHolding = false; button.classList.remove('is-holding'); root.querySelector('[data-pause-stage]')?.classList.remove('is-holding'); });
    button.addEventListener('keydown', event => { if ((event.key === ' ' || event.key === 'Enter') && !event.repeat) { event.preventDefault(); startPauseStep({ currentTarget: button, pointerId: null }); } });
    button.addEventListener('keyup', event => { if (event.key === ' ' || event.key === 'Enter') { event.preventDefault(); finishPauseStep({ currentTarget: button, pointerId: null }); } });
  });
  root.querySelectorAll('[data-pause-skip]').forEach(button => button.addEventListener('click', skipPause));
  root.querySelectorAll('[data-pause-restart]').forEach(button => button.addEventListener('click', () => restartPause()));
  root.querySelectorAll('[data-rhythm-pad]').forEach(button => button.addEventListener('click', () => commitBeat(button.dataset.rhythmPad)));
  actions.forEach(button => {
    const action = button.dataset.workshopAction;
    if (action === 'reset') button.addEventListener('click', resetCurrentScene);
    if (action === 'repeat') button.addEventListener('click', repeatCurrent);
    if (action === 'copy') button.addEventListener('click', copyLink);
    if (action === 'export') button.addEventListener('click', () => exportPng().catch(() => announce('не удалось сохранить PNG')));
    if (action === 'portable') button.addEventListener('click', () => downloadPortable());
  });

  document.addEventListener('keydown', event => {
    if (event.key === 'Escape') { cancelDrag(); if (pauseHolding) { pauseHolding = false; root.querySelectorAll('.is-holding').forEach(node => node.classList.remove('is-holding')); } return; }
    const target = event.target; const editable = target && (target.matches('input, textarea, select, [contenteditable="true"]') || target.isContentEditable);
    if (editable || event.metaKey || event.ctrlKey || event.altKey) return;
    if (/^[1-4]$/.test(event.key)) { event.preventDefault(); setMode('rhythm', { announce: false }); commitBeat(Number(event.key)); }
    else if (event.key === ' ' && target && target.matches('[data-rhythm-pad]')) { event.preventDefault(); commitBeat(target.dataset.rhythmPad); }
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) { cancelAllRafs(); if (pointerFrame) pointerFrame = null; } });
  window.addEventListener('hashchange', () => { const decoded = State.decodeStateHash ? State.decodeStateHash(location.hash) : fallbackState.decodeStateHash(location.hash); state = decoded; activeMode = decoded.mode; draftNote = decoded.note; draftNoteToken = decoded.noteToken; rhythmEvents = decoded.rhythm.map((pad, index) => ({ pad, at: index * 240 })); renderState(); });

  function setupPointerAndIdle() {
    if (!mascotWrap || isReducedMotion() || !window.matchMedia || !window.matchMedia('(hover: hover) and (pointer: fine)').matches) return;
    const target = root.querySelector('[data-fondy-stage]') || mascotWrap;
    target.addEventListener('pointermove', event => {
      pointerLast = { x: event.clientX, y: event.clientY };
      if (pointerFrame == null) pointerFrame = window.requestAnimationFrame(() => {
        pointerFrame = null; if (!pointerLast) return;
        const bounds = mascotWrap.getBoundingClientRect();
        const x = Math.max(-1, Math.min(1, (pointerLast.x - (bounds.left + bounds.width / 2)) / Math.max(1, bounds.width / 2)));
        const y = Math.max(-1, Math.min(1, (pointerLast.y - (bounds.top + bounds.height / 2)) / Math.max(1, bounds.height / 2)));
        if (mascot) mascot.style.transform = `translate(${(x * 6).toFixed(2)}px, ${(y * 6).toFixed(2)}px) rotate(${(x * 5).toFixed(2)}deg)`;
      });
    }, { passive: true });
    target.addEventListener('pointerleave', () => { pointerLast = null; if (mascot) mascot.style.transform = ''; });
    if ('IntersectionObserver' in window) { idleObserver = new IntersectionObserver(entries => mascotWrap.classList.toggle('is-idle-paused', !entries.some(entry => entry.isIntersecting))); idleObserver.observe(mascotWrap); }
  }

  if (location.hash && State.decodeStateHashResult && !State.decodeStateHashResult(location.hash).valid) announce('ссылка устарела или повреждена');
  if (!state.mode || !modes.includes(state.mode)) state = { ...DEFAULT_STATE };
  draftNote = state.note || ''; draftNoteToken = state.noteToken || 'pulse'; activeMode = state.mode || 'signal';
  root.querySelectorAll('[data-workshop-navigation]').forEach(nav => { if (!nav.getAttribute('role')) nav.setAttribute('role', 'tablist'); });
  setupPointerAndIdle();
  renderState();

  window.__signalWorkshop = window.__signalWorkshop || { root, getState: () => ({ ...state, signal: state.signal.slice(), rhythm: state.rhythm.slice() }), setMode, reset: resetCurrentScene, repeat: repeatCurrent, encodeState: () => State.encodeState(state) };
})();
