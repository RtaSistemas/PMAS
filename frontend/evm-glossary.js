/* PMAS — EVM Glossary: terms and tooltip behaviour */

window._EVM_TERMS = {
  CPI: {
    pt: {
      name: 'IDC — Índice de Desempenho de Custo',
      desc: 'Mede a eficiência do custo realizado. > 1,0 = abaixo do orçamento; < 1,0 = acima.',
      formula: 'IDC = VA ÷ CR\n  VA = Valor Agregado\n  CR = Custo Real acumulado',
    },
    en: {
      name: 'CPI — Cost Performance Index',
      desc: 'Measures cost efficiency. > 1.0 = under budget; < 1.0 = over budget.',
      formula: 'CPI = EV ÷ AC\n  EV = Earned Value\n  AC = Actual Cost',
    },
  },
  SPI: {
    pt: {
      name: 'IDP — Índice de Desempenho de Prazo',
      desc: 'Mede a eficiência do cronograma. > 1,0 = adiantado; < 1,0 = atrasado.',
      formula: 'IDP = Horas Realizadas ÷ Horas Planejadas (acum.)\n  Proxy AgileEVM em horas — equivale a VA÷VP quando o custo é uniforme',
    },
    en: {
      name: 'SPI — Schedule Performance Index',
      desc: 'Measures schedule efficiency. > 1.0 = ahead of schedule; < 1.0 = behind.',
      formula: 'SPI = Actual Hours ÷ Planned Hours (cumulative)\n  AgileEVM hours proxy — equivalent to EV÷PV when cost is uniformly distributed',
    },
  },
  EAC: {
    pt: {
      name: 'EPT — Estimativa no Término',
      desc: 'Projeção do custo total do projeto ao término. Usa IDC×IDP quando há baseline de prazo, ou apenas IDC caso contrário.',
      formula: 'EPT (IDC)     = OAT ÷ IDC\nEPT (IDC×IDP) = CR + (OAT − VA) ÷ (IDC × IDP)\n  OAT = Orçamento ao Término (BAC)\n  IDC = Índice de Desempenho de Custo\n  IDP = Índice de Desempenho de Prazo',
    },
    en: {
      name: 'EAC — Estimate at Completion',
      desc: 'Projected total cost at completion. Uses CPI×SPI when a schedule baseline exists, otherwise CPI only.',
      formula: 'EAC (CPI)     = BAC ÷ CPI\nEAC (CPI×SPI) = AC + (BAC − EV) ÷ (CPI × SPI)\n  BAC = Budget at Completion\n  CPI = Cost Performance Index\n  SPI = Schedule Performance Index',
    },
  },
  AC: {
    pt: {
      name: 'AC — Custo Real (Actual Cost)',
      desc: 'Total de custos reais incorridos e registrados para o trabalho realizado até o momento.',
      formula: 'AC = Σ (horas × custo/hora)\n  Calculado com a tarifa congelada no momento da importação',
    },
    en: {
      name: 'AC — Actual Cost',
      desc: 'Total of actual costs incurred for work performed to date.',
      formula: 'AC = Σ (hours × cost/hour)\n  Rate is frozen at ingestion time (EVM freeze pattern)',
    },
  },
  SV: {
    pt: {
      name: 'VS — Variação de Prazo',
      desc: 'Diferença entre o valor do trabalho realizado e o planejado. Negativo = atrasado.',
      formula: 'VS = VA − VP\n  VA = Valor Agregado\n  VP = Valor Planejado',
    },
    en: {
      name: 'SV — Schedule Variance',
      desc: 'Difference between earned and planned value. Negative = behind schedule.',
      formula: 'SV = EV − PV\n  EV = Earned Value\n  PV = Planned Value',
    },
  },
  PV: {
    pt: {
      name: 'VP — Valor Planejado (horas)',
      desc: 'Horas planejadas acumuladas que deveriam ter sido realizadas até o momento (baseline S-curve).',
      formula: 'VP = Σ horas planejadas acumuladas até o ciclo atual\n  O IDP e VS são calculados em horas (proxy AgileEVM)',
    },
    en: {
      name: 'PV — Planned Value (hours)',
      desc: 'Cumulative planned hours that should have been completed by now (baseline S-curve).',
      formula: 'PV = Σ planned hours up to current cycle\n  SPI and SV are computed in hours (AgileEVM proxy)',
    },
  },
  CV: {
    pt: {
      name: 'VC — Variação de Custo',
      desc: 'Diferença entre o valor agregado e o custo real. Positivo = abaixo do orçamento; negativo = acima.',
      formula: 'VC = VA − CR\n  VA = Valor Agregado (EV)\n  CR = Custo Real (AC)',
    },
    en: {
      name: 'CV — Cost Variance',
      desc: 'Difference between earned value and actual cost. Positive = under budget; negative = over budget.',
      formula: 'CV = EV − AC\n  EV = Earned Value\n  AC = Actual Cost',
    },
  },
  TCPI: {
    pt: {
      name: 'IDC-PC — Índice de Desempenho para Conclusão',
      desc: 'Eficiência de custo necessária para terminar o projeto dentro do orçamento original. > 1,0 exige melhora de eficiência.',
      formula: 'IDC-PC = (OAT − VA) ÷ (OAT − CR)\n  OAT = Orçamento ao Término (BAC)',
    },
    en: {
      name: 'TCPI — To-Complete Performance Index',
      desc: 'Required cost efficiency to finish within the original budget. > 1.0 means tighter performance needed.',
      formula: 'TCPI = (BAC − EV) ÷ (BAC − AC)\n  BAC = Budget at Completion',
    },
  },
  VAC: {
    pt: {
      name: 'VNT — Variação no Término',
      desc: 'Diferença projetada entre o orçamento e o custo final estimado. Positivo = economia; negativo = estouro.',
      formula: 'VNT = OAT − EPT\n  OAT = Orçamento ao Término (BAC)\n  EPT = Estimativa no Término (EAC)',
    },
    en: {
      name: 'VAC — Variance at Completion',
      desc: 'Projected difference between budget and estimated final cost. Positive = savings; negative = overrun.',
      formula: 'VAC = BAC − EAC\n  BAC = Budget at Completion\n  EAC = Estimate at Completion',
    },
  },
  ETC: {
    pt: {
      name: 'EPC — Estimativa para Conclusão',
      desc: 'Custo restante projetado para concluir o trabalho, com base no desempenho atual.',
      formula: 'EPC = EPT − CR\n  EPT = Estimativa no Término (EAC)\n  CR = Custo Real acumulado (AC)',
    },
    en: {
      name: 'ETC — Estimate to Complete',
      desc: 'Projected remaining cost to complete the work, based on current performance.',
      formula: 'ETC = EAC − AC\n  EAC = Estimate at Completion\n  AC = Actual Cost',
    },
  },
  EVM: {
    pt: {
      name: 'EVM — Gestão de Valor Agregado',
      desc: 'Metodologia que integra escopo, prazo e custo para medir o desempenho real do projeto e projetar tendências.',
      formula: 'Indicadores: IDC, IDP, EPT, VC, VNT, EPC, IDC-PC, VS, VP',
    },
    en: {
      name: 'EVM — Earned Value Management',
      desc: 'Methodology integrating scope, schedule and cost to measure actual project performance and forecast trends.',
      formula: 'Metrics: CPI, SPI, EAC, CV, VAC, ETC, TCPI, SV, PV',
    },
  },
};

let _evmTipEl    = null;
let _evmTipTimer = null;

function _showEvmTip(anchor) {
  const key  = anchor.dataset.evm;
  const term = window._EVM_TERMS[key];
  if (!term) return;
  // _locale is defined in app.js; falls back to 'pt' if not yet available
  const locale = (typeof _locale !== 'undefined' ? _locale : null) || 'pt';
  const loc  = term[locale] || term.pt;

  if (!_evmTipEl) {
    _evmTipEl = document.createElement('div');
    _evmTipEl.className = 'evm-tooltip';
    document.body.appendChild(_evmTipEl);
  }
  _evmTipEl.innerHTML =
    `<div class="evm-tip-name">${escHtml(loc.name)}</div>` +
    `<div class="evm-tip-desc">${escHtml(loc.desc)}</div>` +
    `<div class="evm-tip-formula">${escHtml(loc.formula)}</div>`;
  _evmTipEl.hidden = false;

  const rect = anchor.getBoundingClientRect();
  const tipW = 270;
  let left = rect.left;
  let top  = rect.bottom + 6;
  if (left + tipW > window.innerWidth - 8) left = Math.max(8, window.innerWidth - tipW - 8);
  if (top + 120 > window.innerHeight)      top  = rect.top - 8 - (_evmTipEl.offsetHeight || 120);
  _evmTipEl.style.left = `${left}px`;
  _evmTipEl.style.top  = `${top}px`;
}

function _hideEvmTip() {
  clearTimeout(_evmTipTimer);
  if (_evmTipEl) _evmTipEl.hidden = true;
}

function _initEvmTips() {
  document.addEventListener('mouseover', e => {
    const el = e.target.closest('[data-evm]');
    if (!el) return;
    clearTimeout(_evmTipTimer);
    _evmTipTimer = setTimeout(() => _showEvmTip(el), 350);
  });
  document.addEventListener('mouseout', e => {
    if (!e.target.closest('[data-evm]')) return;
    clearTimeout(_evmTipTimer);
    _hideEvmTip();
  });
}

_initEvmTips();
