/* PMAS — First-use checklist (Dashboard tab)
 * Shows to administrators until a cycle, a project and a timesheet import exist.
 */

const _ONBOARD_STEPS = [
  { key: 'step1', go: 'go1', tab: 'cycles' },
  { key: 'step2', go: 'go2', tab: 'projects' },
  { key: 'step3', go: 'go3', tab: 'my', sub: 'upload' },
];

async function _loadOnboardingCounts() {
  const [cycles, projects, uploads] = await Promise.all([
    apiFetch('/api/cycles'),
    apiFetch('/api/projects'),
    apiFetch('/api/upload-history?limit=1'),
  ]);
  return [cycles.length, projects.length, uploads.length];
}

async function _refreshOnboarding() {
  const host = document.getElementById('onboardingCard');
  if (!host) return;
  if (!_isAdmin()) { host.hidden = true; return; }

  let counts;
  try {
    counts = await _loadOnboardingCounts();
  } catch (_) {
    host.hidden = true;   // do not block the Dashboard when the check fails
    return;
  }

  const done = counts.map(n => n > 0);
  const doneCount = done.filter(Boolean).length;
  if (doneCount === _ONBOARD_STEPS.length) { host.hidden = true; return; }

  const items = _ONBOARD_STEPS.map((s, i) => {
    const state = done[i] ? 'done' : 'todo';
    const mark  = done[i] ? '✓' : String(i + 1);
    const label = done[i] ? _t('onboard.done') : _t('onboard.todo');
    const btn   = done[i] ? '' :
      `<button type="button" class="btn btn-secondary btn-sm" data-onboard-step="${i}">${_t('onboard.' + s.go)}</button>`;
    return `<li class="onboarding-step ${state}">
      <span class="onboarding-mark" aria-hidden="true">${mark}</span>
      <span class="sr-only">${label}: </span>
      <span class="onboarding-text">${_t('onboard.' + s.key)}</span>
      ${btn}
    </li>`;
  }).join('');

  const progress = _t('onboard.progress')
    .replace('{done}', doneCount).replace('{total}', _ONBOARD_STEPS.length);

  host.innerHTML = `
    <h2 class="onboarding-title">${_t('onboard.title')}</h2>
    <p class="onboarding-progress">${progress}</p>
    <ol class="onboarding-steps">${items}</ol>`;
  host.hidden = false;
}

document.getElementById('onboardingCard')?.addEventListener('click', e => {
  const btn = e.target.closest('[data-onboard-step]');
  if (!btn) return;
  const step = _ONBOARD_STEPS[Number(btn.dataset.onboardStep)];
  document.querySelector(`.tab-btn[data-tab="${step.tab}"]`)?.click();
  if (step.sub) {
    setTimeout(() => document.querySelector(`[data-my-tab="${step.sub}"]`)?.click(), 150);
  }
});
