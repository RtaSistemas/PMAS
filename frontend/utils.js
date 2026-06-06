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
 * Format an ISO timestamp for display. Respects the current locale (_locale global)
 * and an optional window._timezone override (default: America/Sao_Paulo).
 */
export function fmtDate(isoStr) {
  if (!isoStr) return '—';
  const tz = (typeof window !== 'undefined' && window._timezone) || 'America/Sao_Paulo';
  const loc = (typeof _locale !== 'undefined' ? _locale : (typeof window !== 'undefined' ? window._locale : 'pt')) || 'pt';
  return new Date(isoStr).toLocaleString(loc === 'pt' ? 'pt-BR' : 'en-US', { timeZone: tz, dateStyle: 'short', timeStyle: 'short' });
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
  window.fmtDate = fmtDate;
  window._fmtDate = fmtDate;
  window.clamp = clamp;
  window.parseISODate = parseISODate;
}
