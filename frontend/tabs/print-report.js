/* PMAS — Printed report header
 * The browser print dialog prints the active tab. This module fills a header block
 * (logo, report name, date, user, active filters) just before printing.
 */

function _printFilterParts() {
  const parts = [];
  const labelsOf = (ms, values) => values.map(v => {
    const item = (ms.items || []).find(i => String(i.value) === String(v));
    return item ? (item.label ?? item.text ?? v) : v;
  });
  [
    ['filter.cycle',    cycleMs],
    ['filter.pep_code', pepMs],
    ['filter.collab',   collaboratorMs],
  ].forEach(([key, ms]) => {
    const values = ms.getValues();
    if (values.length) parts.push([_t(key), labelsOf(ms, values).join(', ')]);
  });
  const from = document.getElementById('dateFromInput')?.value;
  const to   = document.getElementById('dateToInput')?.value;
  if (from) parts.push([_t('filter.dfrom'), fmtDateBR(from)]);
  if (to)   parts.push([_t('filter.dto'),   fmtDateBR(to)]);
  return parts;
}

function _printReportTitle() {
  const tab = document.querySelector('.tab-btn.active');
  const name = tab ? tab.textContent.trim() : '';
  if (tab?.dataset.tab !== 'dashboard') return name;
  const sub = document.querySelector('.atab-btn.active');
  return sub ? `${name} — ${sub.textContent.trim()}` : name;
}

function _buildPrintHeader() {
  const host = document.getElementById('printHeader');
  if (!host) return;

  const appName = document.querySelector('[data-app-name]')?.textContent || 'PMAS';
  const logo = document.querySelector('#headerLogoBox img');
  const logoHtml = logo ? `<img class="print-logo" src="${escHtml(logo.getAttribute('src'))}" alt="" />` : '';

  const user = _getTokenPayload()?.sub || '';
  const when = new Date().toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-GB',
    { dateStyle: 'medium', timeStyle: 'short' });
  const generated = _t('print.generated').replace('{date}', when).replace('{user}', user);

  const parts = _printFilterParts();
  const filters = parts.length
    ? parts.map(([k, v]) => `<span class="print-filter"><b>${escHtml(k)}:</b> ${escHtml(v)}</span>`).join('')
    : `<span class="print-filter">${_t('print.no_filters')}</span>`;

  host.innerHTML = `
    <div class="print-header-top">
      ${logoHtml}
      <div>
        <div class="print-app">${escHtml(appName)}</div>
        <h1 class="print-title">${escHtml(_printReportTitle())}</h1>
      </div>
      <div class="print-generated">${escHtml(generated)}</div>
    </div>
    <div class="print-filters"><b>${_t('print.filters')}</b> ${filters}</div>`;
}

window.addEventListener('beforeprint', _buildPrintHeader);
