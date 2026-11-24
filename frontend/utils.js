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

export function formatHours(h, decimals = 1) {
  if (h == null || isNaN(Number(h))) return '—';
  return Number(h).toFixed(decimals) + 'h';
}

export function formatCost(raw, factor = 1, symbol = 'R$', locale = 'pt-BR') {
  if (raw == null || isNaN(Number(raw))) return '—';
  const converted = Number(raw) * factor;
  return `${symbol} ${converted.toLocaleString(locale, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

// One date rule for the whole interface: dd/mm/yyyy in both languages (the same as fmtDateBR).
// A time shows as HH:mm, 24 hours, in the time zone of the system (window._timezone).
function _formatDateParts(d, withTime) {
  const tz = (typeof window !== 'undefined' && window._timezone) || 'America/Sao_Paulo';
  const options = { timeZone: tz, day: '2-digit', month: '2-digit', year: 'numeric' };
  if (withTime) Object.assign(options, { hour: '2-digit', minute: '2-digit', hourCycle: 'h23' });
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-GB', options).formatToParts(d).map(x => [x.type, x.value]));
  return `${p.day}/${p.month}/${p.year}` + (withTime ? ` ${p.hour}:${p.minute}` : '');
}

/**
 * Format an ISO timestamp as "dd/mm/yyyy HH:mm". Returns a dash for an empty value.
 */
export function fmtDate(isoStr) {
  if (!isoStr) return '—';
  const d = new Date(isoStr);
  return isNaN(d) ? String(isoStr) : _formatDateParts(d, true);
}

/**
 * Format an ISO date (YYYY-MM-DD) or an ISO timestamp as "dd/mm/yyyy". Returns a dash for an empty value.
 */
export function fmtDateOnly(isoStr) {
  if (!isoStr) return '—';
  if (/^\d{4}-\d{2}-\d{2}$/.test(String(isoStr))) return fmtDateBR(isoStr);
  const d = new Date(isoStr);
  return isNaN(d) ? String(isoStr) : _formatDateParts(d, false);
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
  window.fmtDateOnly = fmtDateOnly;
  window._fmtDate = fmtDate;
  window.clamp = clamp;
  window.parseISODate = parseISODate;
}
