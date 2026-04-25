/* PMAS — MultiSelect component */
class MultiSelect {
  constructor(el, placeholder, onChange) {
    this.el = el;
    this.placeholder = placeholder;
    this.onChange = onChange;
    this.items = [];
    this.selected = new Set();
    this._build();
  }

  _build() {
    this.el.classList.add('ms-root');
    this.btn = document.createElement('button');
    this.btn.type = 'button';
    this.btn.className = 'ms-toggle';
    this.btn.innerHTML = `<span class="ms-label"></span><span class="ms-arrow">▾</span>`;
    this.panel = document.createElement('div');
    this.panel.className = 'ms-dropdown';
    this.panel.hidden = true;
    this.el.appendChild(this.btn);
    this.el.appendChild(this.panel);
    this.btn.addEventListener('click', e => { e.stopPropagation(); this.panel.hidden = !this.panel.hidden; });
    document.addEventListener('click', e => { if (!this.el.contains(e.target)) this.panel.hidden = true; });
    this._updateBtn();
  }

  setItems(items, preserve = false) {
    this.items = items;
    if (!preserve) {
      this.selected.clear();
    } else {
      const valid = new Set(items.map(i => String(i.value)));
      for (const v of [...this.selected]) { if (!valid.has(v)) this.selected.delete(v); }
    }
    this._renderPanel();
    this._updateBtn();
  }

  getValues() { return [...this.selected]; }

  clear() { this.selected.clear(); this._renderPanel(); this._updateBtn(); }

  _updateBtn() {
    const lbl = this.btn.querySelector('.ms-label');
    if (this.selected.size === 0) {
      lbl.textContent = this.placeholder; this.btn.classList.remove('has-value');
    } else if (this.selected.size === 1) {
      const v = [...this.selected][0];
      const item = this.items.find(i => String(i.value) === v);
      lbl.textContent = item ? item.label : v; this.btn.classList.add('has-value');
    } else {
      lbl.textContent = `${this.selected.size} selecionados`; this.btn.classList.add('has-value');
    }
  }

  _renderPanel() {
    this.panel.innerHTML = '';
    if (this.items.length === 0) {
      const e = document.createElement('div'); e.className = 'ms-empty'; e.textContent = 'Sem opções'; this.panel.appendChild(e); return;
    }
    const allLbl = this._makeRow('__all__', 'Selecionar todos', true);
    const allChk = allLbl.querySelector('input');
    allChk.checked = this.selected.size === this.items.length && this.items.length > 0;
    allChk.indeterminate = this.selected.size > 0 && this.selected.size < this.items.length;
    allChk.addEventListener('change', e => {
      e.stopPropagation();
      if (allChk.checked) this.items.forEach(i => this.selected.add(String(i.value))); else this.selected.clear();
      this._renderPanel(); this._updateBtn(); this.onChange?.();
    });
    this.panel.appendChild(allLbl);
    this.items.forEach(item => {
      const lbl = this._makeRow(item.value, item.label, false);
      const chk = lbl.querySelector('input');
      chk.checked = this.selected.has(String(item.value));
      chk.addEventListener('change', e => {
        e.stopPropagation();
        if (chk.checked) this.selected.add(String(item.value)); else this.selected.delete(String(item.value));
        this._renderPanel(); this._updateBtn(); this.onChange?.();
      });
      this.panel.appendChild(lbl);
    });
  }

  _makeRow(value, label, isAll) {
    const lbl = document.createElement('label');
    lbl.className = 'ms-option' + (isAll ? ' ms-all' : '');
    lbl.addEventListener('click', e => e.stopPropagation());
    const chk = document.createElement('input'); chk.type = 'checkbox'; chk.value = value;
    const span = document.createElement('span'); span.textContent = label;
    lbl.appendChild(chk); lbl.appendChild(span); return lbl;
  }
}
