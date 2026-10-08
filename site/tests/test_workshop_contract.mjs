import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const read = name => readFile(join(root, name), 'utf8');

test('Signal workshop exposes four scenes and shared action hooks', async () => {
  const html = await read('sections/workshop.html');
  assert.match(html, /id="workshop-signal"/);
  assert.match(html, /id="workshop-letter"/);
  assert.match(html, /id="workshop-pause"/);
  assert.match(html, /id="workshop-rhythm"/);
  assert.equal((html.match(/data-workshop-mode=/g) ?? []).length, 4);
  assert.match(html, /data-token="pulse"/);
  assert.match(html, /data-token="anchor"/);
  assert.doesNotMatch(html, /heart|серд/iu);
  assert.match(html, /role="status"[^>]*aria-live="polite"/);
  assert.match(html, /data-workshop-action="copy"/);
  assert.match(html, /data-workshop-action="export"/);
});

test('workshop assets define motion-safe primitives and inline token runtime', async () => {
  const css = await read('sections/workshop.css');
  const js = await read('sections/workshop.js');
  assert.match(css, /--ease-snap/);
  assert.match(css, /prefers-reduced-motion/);
  assert.match(js, /glyphSvg/);
  assert.doesNotMatch(js, /assets\/hearts|heart|серд/iu);
});

test('workshop controls have tab semantics and useful share/export actions', async () => {
  const html = await read('sections/workshop.html');
  const js = await read('sections/workshop.js');
  const build = await read('build.py');
  assert.match(html, /role="tablist"/);
  assert.equal((html.match(/role="tab"/g) ?? []).length, 4);
  assert.equal((html.match(/role="tabpanel"/g) ?? []).length, 4);
  assert.match(html, /aria-selected="true"/);
  assert.match(js, /navigator\.clipboard/);
  assert.match(js, /download/);
  assert.match(build, /encoding=['"]utf-8['"]/);
  assert.doesNotMatch(build, /href="\/assets\//);
});
