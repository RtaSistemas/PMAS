/* PMAS — Help page: show the block for the saved language and let the user switch. */
(function () {
  let lang = 'pt';
  try { lang = localStorage.getItem('pmas_lang') || 'pt'; } catch (_) {}

  function apply() {
    document.documentElement.lang = lang === 'pt' ? 'pt-BR' : 'en';
    document.querySelectorAll('[data-l]').forEach(el => { el.hidden = el.dataset.l !== lang; });
    document.getElementById('helpLangBtn').textContent = lang === 'pt' ? 'EN' : 'PT';
  }

  document.getElementById('helpLangBtn').addEventListener('click', () => {
    lang = lang === 'pt' ? 'en' : 'pt';
    try { localStorage.setItem('pmas_lang', lang); } catch (_) {}
    apply();
  });
  apply();
})();
