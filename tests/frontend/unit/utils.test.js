import { describe, it, expect } from 'vitest';
import {
  escHtml,
  fmtDateBR,
  formatHours,
  formatCost,
  clamp,
  parseISODate,
} from '../../../frontend/utils.js';

// ── escHtml ───────────────────────────────────────────────────────────────────

describe('escHtml', () => {
  it('passes through plain text unchanged', () => {
    expect(escHtml('hello world')).toBe('hello world');
  });

  it('escapes ampersands', () => {
    expect(escHtml('a & b')).toBe('a &amp; b');
  });

  it('escapes angle brackets', () => {
    expect(escHtml('<script>')).toBe('&lt;script&gt;');
  });

  it('escapes double quotes', () => {
    expect(escHtml('"quoted"')).toBe('&quot;quoted&quot;');
  });

  it('escapes single quotes', () => {
    expect(escHtml("it's")).toBe('it&#39;s');
  });

  it('handles null', () => {
    expect(escHtml(null)).toBe('');
  });

  it('handles undefined', () => {
    expect(escHtml(undefined)).toBe('');
  });

  it('handles numbers', () => {
    expect(escHtml(42)).toBe('42');
  });

  it('escapes all dangerous chars in one string', () => {
    expect(escHtml('<img src="x" onerror=\'alert(1)\'>')).toBe(
      '&lt;img src=&quot;x&quot; onerror=&#39;alert(1)&#39;&gt;'
    );
  });
});

// ── fmtDateBR ─────────────────────────────────────────────────────────────────

describe('fmtDateBR', () => {
  it('converts ISO to DD/MM/YYYY', () => {
    expect(fmtDateBR('2024-01-15')).toBe('15/01/2024');
  });

  it('handles single-digit days and months', () => {
    expect(fmtDateBR('2024-03-07')).toBe('07/03/2024');
  });

  it('returns null for empty string', () => {
    expect(fmtDateBR('')).toBeNull();
  });

  it('returns null for null', () => {
    expect(fmtDateBR(null)).toBeNull();
  });

  it('returns null for undefined', () => {
    expect(fmtDateBR(undefined)).toBeNull();
  });
});

// ── formatHours ───────────────────────────────────────────────────────────────

describe('formatHours', () => {
  it('formats zero as 0.0h', () => {
    expect(formatHours(0)).toBe('0.0h');
  });

  it('formats integer with one decimal', () => {
    expect(formatHours(8)).toBe('8.0h');
  });

  it('rounds to 1 decimal place', () => {
    expect(formatHours(7.567)).toBe('7.6h');
  });

  it('returns dash for null', () => {
    expect(formatHours(null)).toBe('—');
  });

  it('returns dash for undefined', () => {
    expect(formatHours(undefined)).toBe('—');
  });

  it('handles large numbers', () => {
    expect(formatHours(1000)).toBe('1000.0h');
  });
});

// ── formatCost ────────────────────────────────────────────────────────────────

describe('formatCost', () => {
  it('formats with default symbol and factor', () => {
    const result = formatCost(1000);
    expect(result).toContain('R$');
    expect(result).toContain('1.000');  // pt-BR thousands separator
  });

  it('applies factor correctly', () => {
    const result = formatCost(100, 2, '$');
    expect(result).toContain('$');
    expect(result).toContain('200');
  });

  it('returns dash for null', () => {
    expect(formatCost(null)).toBe('—');
  });

  it('returns dash for undefined', () => {
    expect(formatCost(undefined)).toBe('—');
  });
});

// ── clamp ─────────────────────────────────────────────────────────────────────

describe('clamp', () => {
  it('returns value when within range', () => {
    expect(clamp(5, 0, 10)).toBe(5);
  });

  it('clamps to min', () => {
    expect(clamp(-5, 0, 10)).toBe(0);
  });

  it('clamps to max', () => {
    expect(clamp(15, 0, 10)).toBe(10);
  });

  it('returns min when value equals min', () => {
    expect(clamp(0, 0, 10)).toBe(0);
  });

  it('returns max when value equals max', () => {
    expect(clamp(10, 0, 10)).toBe(10);
  });
});

// ── parseISODate ──────────────────────────────────────────────────────────────

describe('parseISODate', () => {
  it('parses a valid ISO date', () => {
    const d = parseISODate('2024-06-15');
    expect(d).toBeInstanceOf(Date);
    expect(d.getUTCFullYear()).toBe(2024);
    expect(d.getUTCMonth()).toBe(5);  // 0-indexed
    expect(d.getUTCDate()).toBe(15);
  });

  it('returns null for empty string', () => {
    expect(parseISODate('')).toBeNull();
  });

  it('returns null for null', () => {
    expect(parseISODate(null)).toBeNull();
  });

  it('returns null for undefined', () => {
    expect(parseISODate(undefined)).toBeNull();
  });
});
