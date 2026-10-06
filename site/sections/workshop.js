/* Fondy workshop runtime shell. Scene state and export helpers extend this entry point. */
(() => {
  'use strict';

  const root = document.querySelector('[data-workshop-root]');
  if (!root) return;

  const status = root.querySelector('[data-workshop-status]');
  const modeButtons = [...root.querySelectorAll('[data-workshop-mode]')];
  const scenes = [...root.querySelectorAll('[data-workshop-scene]')];

  const announce = (message) => {
    if (status) status.textContent = message;
  };

  const setMode = (mode, { focus = false } = {}) => {
    const button = modeButtons.find(item => item.dataset.workshopMode === mode) || modeButtons[0];
    if (!button) return;
    const activeMode = button.dataset.workshopMode;
    modeButtons.forEach(item => {
      const active = item === button;
      item.classList.toggle('is-active', active);
      item.setAttribute('aria-pressed', String(active));
    });
    scenes.forEach(scene => {
      const active = scene.dataset.workshopScene === activeMode;
      scene.hidden = !active;
      scene.classList.toggle('is-active', active);
    });
    root.dataset.workshopActiveMode = activeMode;
    if (focus) button.focus();
    announce(`сцена: ${button.textContent.trim().replace(/^\d+/, '').trim()}`);
  };

  modeButtons.forEach(button => {
    button.addEventListener('click', () => setMode(button.dataset.workshopMode));
  });

  root.querySelectorAll('[data-workshop-action="reset"]').forEach(button => {
    button.addEventListener('click', () => {
      root.querySelectorAll('textarea').forEach(field => { field.value = ''; });
      root.querySelectorAll('[data-letter-count]').forEach(counter => { counter.textContent = '0 / 120'; });
      root.querySelectorAll('[data-signal-count]').forEach(counter => { counter.textContent = '0 / 4'; });
      root.querySelectorAll('[data-rhythm-count]').forEach(counter => { counter.textContent = '0 / 32'; });
      announce('сцена сброшена — можно собрать заново');
      button.focus();
    });
  });

  root.querySelectorAll('[data-workshop-action="repeat"]').forEach(button => {
    button.addEventListener('click', () => {
      announce('повторяем последний жест');
      button.focus();
    });
  });

  root.querySelectorAll('[data-letter-note]').forEach(field => {
    const counter = root.querySelector('[data-letter-count]');
    field.addEventListener('input', () => {
      if (counter) counter.textContent = `${[...field.value].length} / 120`;
    });
  });

  root.querySelectorAll('[data-note-heart]').forEach(button => {
    button.addEventListener('click', () => {
      root.querySelectorAll('[data-note-heart]').forEach(item => {
        const selected = item === button;
        item.classList.toggle('is-selected', selected);
        item.setAttribute('aria-pressed', String(selected));
      });
    });
  });

  setMode('signal');

  if ((location.hostname === 'localhost' || location.hostname === '127.0.0.1') && !window.__fondyWorkshop) {
    window.__fondyWorkshop = { announce, setMode, root };
  }
})();
