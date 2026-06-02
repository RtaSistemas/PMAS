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

export function formatCost(raw, factor = 1, symbol = 'R$') {
  if (raw == null || isNaN(Number(raw))) return '—';
  const converted = Number(raw) * factor;
  return `${symbol} ${converted.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

export function riskColor(risk) {
  const colors = {
    ok:        'var(--primary, #4f8ef7)',
    warning:   'var(--amber,   #d9b273)',
    critical:  'var(--red,     #c56d76)',
    overrun:   'var(--red,     #c56d76)',
    no_budget: 'var(--text-3,  #818998)',
  };
  return colors[risk] || colors.no_budget;
}

/**
 * Classify budget consumption health.
 * @returns {'ok'|'warning'|'critical'|'no_budget'}
 */
export function classifyBudgetHealth(consumed, budget, warnThreshold = 0.9, critThreshold = 1.0) {
  if (budget == null || budget <= 0) return 'no_budget';
  const ratio = consumed / budget;
  if (ratio >= critThreshold) return 'critical';
  if (ratio >= warnThreshold) return 'warning';
  return 'ok';
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
