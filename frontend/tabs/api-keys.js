/* PMAS — API keys for automatic import (Admin tab) */

async function loadApiKeys() {
  const body = document.getElementById('apiKeysBody');
  if (!body) return;
  try {
    const keys = await apiFetch('/api/api-keys');
    if (!keys.length) {
      body.innerHTML = `<tr><td colspan="7" class="td-empty">${_t('apikey.empty')}</td></tr>`;
      return;
    }
    body.innerHTML = keys.map(k => {
      const revoked = !!k.revoked_at;
      const status = revoked
        ? `<span class="badge-revoked">${_t('apikey.status.revoked')}</span>`
        : _t('apikey.status.active');
      const action = revoked ? '' :
        `<button type="button" class="btn btn-danger btn-sm" data-revoke-key="${k.id}" data-key-name="${escHtml(k.name)}"
           aria-label="${_t('apikey.revoke')}" title="${_t('apikey.revoke')}">${_t('apikey.revoke')}</button>`;
      return `<tr>
        <td>${escHtml(k.name)}</td>
        <td>${escHtml(k.username)}</td>
        <td><code>${escHtml(k.key_prefix)}…</code></td>
        <td>${_fmtDateShort(k.created_at)}</td>
        <td>${k.last_used_at ? _fmtDateShort(k.last_used_at) : _t('apikey.never')}</td>
        <td>${status}</td>
        <td>${action}</td>
      </tr>`;
    }).join('');
  } catch (e) {
    body.innerHTML = `<tr><td colspan="7" class="td-empty">${escHtml(_friendlyError(e))}</td></tr>`;
  }
}

async function _openApiKeyModal() {
  document.getElementById('apiKeyNameInput').value = '';
  document.getElementById('apiKeyError').textContent = '';
  const select = document.getElementById('apiKeyUserSelect');
  try {
    const users = await apiFetch('/api/users');
    const me = _getTokenPayload()?.sub;
    select.innerHTML = users.map(u =>
      `<option value="${u.id}"${u.username === me ? ' selected' : ''}>${escHtml(u.username)} (${escHtml(u.role)})</option>`
    ).join('');
  } catch (e) {
    notify(_friendlyError(e), 'error');
    return;
  }
  openModal('apiKeyModal', document.getElementById('newApiKeyBtn'), '#apiKeyNameInput');
}

document.getElementById('newApiKeyBtn')?.addEventListener('click', _openApiKeyModal);

document.getElementById('apiKeySaveBtn')?.addEventListener('click', async () => {
  const name = document.getElementById('apiKeyNameInput').value.trim();
  const errEl = document.getElementById('apiKeyError');
  errEl.textContent = '';
  if (name.length < 3) { errEl.textContent = _t('apikey.name_short'); return; }
  try {
    const created = await apiFetchJSON('/api/api-keys', 'POST', {
      name, user_id: Number(document.getElementById('apiKeyUserSelect').value),
    });
    closeModal('apiKeyModal');
    document.getElementById('apiKeyValue').textContent = created.key;
    openModal('apiKeyShownModal', null, '#apiKeyCopyBtn');
    loadApiKeys();
  } catch (e) { errEl.textContent = e.message; }
});

document.getElementById('apiKeyCopyBtn')?.addEventListener('click', async () => {
  const value = document.getElementById('apiKeyValue').textContent;
  try {
    await navigator.clipboard.writeText(value);
    notify(_t('apikey.copied'), 'success');
  } catch (_) {
    // The clipboard can be blocked. The key stays selectable in the modal.
    const range = document.createRange();
    range.selectNodeContents(document.getElementById('apiKeyValue'));
    const sel = window.getSelection();
    sel.removeAllRanges();
    sel.addRange(range);
  }
});

document.getElementById('apiKeysBody')?.addEventListener('click', e => {
  const btn = e.target.closest('[data-revoke-key]');
  if (!btn) return;
  const id = btn.dataset.revokeKey;
  confirmDialog(_t('apikey.confirm_revoke').replace('{name}', btn.dataset.keyName), async () => {
    try {
      await apiFetchJSON(`/api/api-keys/${id}`, 'DELETE');
      notify(_t('apikey.revoked'), 'success');
      loadApiKeys();
    } catch (err) { notify(_friendlyError(err), 'error'); }
  });
});
