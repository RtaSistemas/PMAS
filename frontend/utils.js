/**
 * Pure utility functions — no DOM or global state dependencies.
 * Exported for use in both app.js (via import or global assignment) and
 * Vitest unit tests.
 */

export function escHtml(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

export function fmtDateBR(iso) {
  if (!iso) return null;
  const [y, m, d] = String(iso).split('-');
  return `${d}/${m}/${y}`;
}

export function formatHours(h) {
  if (h == null || isNaN(Number(h))) return '—';
  return Number(h).toFixed(1) + 'h';
}

export function formatCost(raw, factor = 1, symbol = 'R$', locale = 'pt-BR') {
  if (raw == null || isNaN(Number(raw))) return '—';
  const converted = Number(raw) * factor;
  return `${symbol} ${converted.toLocaleString(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * Clamp a number between min and max.
 */
export function clamp(val, min, max) {
  return Math.min(Math.max(val, min), max);
}

/**
 * Parse an ISO date string (YYYY-MM-DD) into a JS Date at midnight UTC.
 * Returns null for falsy inputs.
 */
export function parseISODate(iso) {
  if (!iso) return null;
  const [y, m, d] = String(iso).split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

// Expose as browser globals when running outside a module context (Vitest runs via import)
if (typeof window !== 'undefined') {
  window.escHtml = escHtml;
  window.fmtDateBR = fmtDateBR;
  window.formatHours = formatHours;
  window.formatCost = formatCost;
  window.clamp = clamp;
  window.parseISODate = parseISODate;
}
