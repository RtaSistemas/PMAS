import { describe, it, expect } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';

// Proof that every translation key that the code uses exists in both locales.

const FRONT = path.resolve(__dirname, '../../../frontend');

function loadLang(file, name) {
  const sandbox = { window: {} };
  vm.runInNewContext(fs.readFileSync(path.join(FRONT, 'lang', file), 'utf8'), sandbox);
  return sandbox.window[name];
}

const PT = loadLang('pt.js', '_LANG_PT');
const EN = loadLang('en.js', '_LANG_EN');

function sourceFiles(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap(e => {
    const p = path.join(dir, e.name);
    if (e.isDirectory()) return e.name === 'lang' ? [] : sourceFiles(p);
    return /\.(js|html)$/.test(e.name) && !/\.min\.js$/.test(e.name) ? [p] : [];
  });
}

function usedKeys() {
  const used = new Map();
  const add = (key, file) => { if (!used.has(key)) used.set(key, file); };
  for (const file of sourceFiles(FRONT)) {
    const text = fs.readFileSync(file, 'utf8');
    const rel = path.relative(FRONT, file);
    for (const m of text.matchAll(/data-i18n(?:-ph|-title|-aria)?="([^"$]+)"/g)) add(m[1], rel);
    for (const m of text.matchAll(/\b(?:emptyKey|entity)\s*:\s*'([^'$]+)'/g)) add(m[1], rel);
    for (const m of text.matchAll(/\b_t\(\s*'([^'$]+)'\s*[,)]/g)) add(m[1], rel);
  }
  return used;
}

describe('i18n keys', () => {
  it('both locales have the same keys', () => {
    const missingEn = Object.keys(PT).filter(k => !(k in EN));
    const missingPt = Object.keys(EN).filter(k => !(k in PT));
    expect({ missingEn, missingPt }).toEqual({ missingEn: [], missingPt: [] });
  });

  it('every key that the code uses exists in both locales', () => {
    const missing = [];
    for (const [key, file] of usedKeys()) {
      if (!(key in PT) || !(key in EN)) missing.push(`${key} (${file})`);
    }
    expect(missing).toEqual([]);
  });
});
