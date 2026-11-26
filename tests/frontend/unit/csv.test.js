import { describe, it, expect } from 'vitest';
import fs from 'node:fs';
import path from 'node:path';
import { csvSafe, csvCell } from '../../../frontend/utils.js';

const TRIGGERS = ['=', '+', '-', '@', '\t', '\r'];

describe('csvSafe', () => {
  it.each(TRIGGERS)('prefixes a quote before text that starts with %j', (t) => {
    expect(csvSafe(`${t}cmd`)).toBe(`'${t}cmd`);
  });
  it('keeps normal text, empty text, null and undefined', () => {
    expect(csvSafe('Ana Souza')).toBe('Ana Souza');
    expect(csvSafe('A=B')).toBe('A=B');
    expect(csvSafe('')).toBe('');
    expect(csvSafe(null)).toBeNull();
    expect(csvSafe(undefined)).toBeUndefined();
  });
  it('keeps a negative number as a number', () => {
    expect(csvSafe(-5)).toBe(-5);
    expect(csvSafe(-5.5)).toBe(-5.5);
  });
});

describe('csvCell', () => {
  it('writes null and empty as an empty cell', () => {
    expect(csvCell(null)).toBe('');
    expect(csvCell(undefined)).toBe('');
    expect(csvCell('')).toBe('');
  });
  it('writes numbers without quotes, including a negative one', () => {
    expect(csvCell(8)).toBe('8');
    expect(csvCell(-3.25)).toBe('-3.25');
  });
  it('quotes text and doubles inner quotes', () => {
    expect(csvCell('Ana "A" Souza')).toBe('"Ana ""A"" Souza"');
  });
  it('makes a formula safe and keeps it quoted', () => {
    expect(csvCell('=HYPERLINK("x")')).toBe('"\'=HYPERLINK(""x"")"');
    expect(csvCell('-Senior')).toBe('"\'-Senior"');
  });
});

describe('every client CSV builder uses the helper', () => {
  const root = path.resolve(__dirname, '../../../frontend');
  const files = [];
  (function walk(dir) {
    for (const e of fs.readdirSync(dir, { withFileTypes: true })) {
      const p = path.join(dir, e.name);
      if (e.isDirectory()) { if (e.name !== 'lang') walk(p); }
      else if (e.name.endsWith('.js') && !e.name.endsWith('.min.js')) files.push(p);
    }
  })(root);

  it('finds the builders (the check is not empty)', () => {
    expect(files.filter(f => fs.readFileSync(f, 'utf8').includes("type: 'text/csv")).length).toBeGreaterThanOrEqual(6);   // 6 files hold the 10 builders (equipe.js has 3)
  });

  it('calls csvCell or csvSafe in each file that builds a CSV Blob', () => {
    const missing = files.filter(f => {
      const src = fs.readFileSync(f, 'utf8');
      return src.includes("type: 'text/csv") && !/csvCell|csvSafe/.test(src);
    }).map(f => path.relative(root, f));
    expect(missing).toEqual([]);
  });
});
