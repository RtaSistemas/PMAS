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
  ES: {
    pt: {
      name: 'PC — Prazo Conquistado (Earned Schedule)',
      desc: 'Ponto na linha de base onde o VP acumulado iguala o VA atual. Mede progresso real de cronograma em unidades de tempo.',
      formula: 'PC = ciclo onde VP(t) = VA\n  Interpolado na curva S de horas planejadas\n  AT = Tempo Real decorrido (ciclos)',
    },
    en: {
      name: 'ES — Earned Schedule',
      desc: 'Point on the baseline where cumulative PV equals current EV. Measures real schedule progress in time units.',
      formula: 'ES = period where PV(t) = EV\n  Interpolated on the planned hours S-curve\n  AT = Actual Time elapsed (cycles)',
    },
  },
  SPIt: {
    pt: {
      name: 'IDP(t) — Índice de Desempenho de Prazo (tempo)',
      desc: 'Razão entre o prazo conquistado e o tempo real decorrido. > 1,0 = adiantado; < 1,0 = atrasado. Baseado em tempo, não em valor.',
      formula: 'IDP(t) = PC ÷ AT\n  PC = Prazo Conquistado (Earned Schedule)\n  AT = Tempo Real decorrido (ciclos)',
    },
    en: {
      name: 'SPI(t) — Schedule Performance Index (time)',
      desc: 'Ratio of earned schedule to actual time elapsed. > 1.0 = ahead; < 1.0 = behind. Time-based, not value-based.',
      formula: 'SPI(t) = ES ÷ AT\n  ES = Earned Schedule\n  AT = Actual Time elapsed (cycles)',
    },
  },
  SVt: {
    pt: {
      name: 'VS(t) — Variação de Prazo (tempo)',
      desc: 'Diferença entre prazo conquistado e tempo real, em ciclos. Positivo = adiantado; negativo = atrasado.',
      formula: 'VS(t) = PC − AT\n  PC = Prazo Conquistado (ciclos)\n  AT = Tempo Real decorrido (ciclos)',
    },
    en: {
      name: 'SV(t) — Schedule Variance (time)',
      desc: 'Difference between earned schedule and actual time, in cycles. Positive = ahead; negative = behind.',
      formula: 'SV(t) = ES − AT\n  ES = Earned Schedule (cycles)\n  AT = Actual Time elapsed (cycles)',
    },
  },
  IEACt: {
    pt: {
      name: 'EPDT(t) — Estimativa de Prazo no Término (tempo)',
      desc: 'Previsão da duração total do projeto baseada no desempenho de prazo atual (IDP(t)). Em unidades de ciclos.',
      formula: 'EPDT(t) = DP ÷ IDP(t)\n  DP = Duração Planejada (ciclos)\n  IDP(t) = Índice de Desempenho de Prazo (tempo)',
    },
    en: {
      name: 'IEAC(t) — Independent EAC (time)',
      desc: 'Forecast of total project duration based on current time-based schedule performance.',
      formula: 'IEAC(t) = PD ÷ SPI(t)\n  PD = Planned Duration (cycles)\n  SPI(t) = Schedule Performance Index (time)',
    },
  },
  SimAvgVel: {
    pt: {
      name: 'Velocidade Média Histórica — What-If',
      desc: 'Média de horas por ciclo calculada sobre os últimos 6 ciclos (ou todos, se houver menos de 6). Janela mais ampla que a do Forecast (3 ciclos) para dar uma base mais suavizada ao cenário.',
      formula: 'vel_média = Σ horas_ciclo ÷ n\n  n = min(6, total de ciclos)\n  Inclui ciclos com zero horas (períodos ociosos contam)\n  Forecast/Runway: últimos 3 ciclos\n  Monte Carlo: todos os ciclos com h > 0',
    },
    en: {
      name: 'Historical Average Velocity — What-If',
      desc: 'Average hours per cycle over the last 6 cycles (or all cycles if fewer than 6). Wider window than Forecast (3 cycles) to provide a smoother scenario baseline.',
      formula: 'avg_velocity = Σ cycle_hours ÷ n\n  n = min(6, total cycles)\n  Includes zero-hour cycles (idle periods count)\n  Forecast/Runway: last 3 cycles\n  Monte Carlo: all cycles with h > 0',
    },
  },
  SimVelocity: {
    pt: {
      name: 'Velocidade Simulada',
      desc: 'Projeção de horas por ciclo aplicando o multiplicador e as horas extras configurados pelo usuário.',
      formula: 'vel_sim = vel_média × multiplicador + horas_extras\n  multiplicador: fator de aceleração/desaceleração\n  horas_extras: incremento fixo por ciclo',
    },
    en: {
      name: 'Simulated Velocity',
      desc: 'Projected hours per cycle applying the user-configured multiplier and extra hours.',
      formula: 'sim_velocity = avg_velocity × multiplier + extra_hours\n  multiplier: speed-up / slow-down factor\n  extra_hours: fixed increment per cycle',
    },
  },
  SimCycles: {
    pt: {
      name: 'Ciclos para Concluir',
      desc: 'Número estimado de ciclos adicionais para esgotar as horas restantes do projeto à velocidade simulada.',
      formula: 'ciclos = ceil(horas_restantes ÷ vel_sim)\n  null quando vel_sim = 0 ou projeto concluído',
    },
    en: {
      name: 'Cycles to Complete',
      desc: 'Estimated number of additional cycles to exhaust remaining project hours at the simulated velocity.',
      formula: 'cycles = ceil(remaining_hours ÷ sim_velocity)\n  null when sim_velocity = 0 or project is done',
    },
  },
  SimEAC: {
    pt: {
      name: 'EAC Projetado — Estimativa no Término (What-If)',
      desc: 'Custo total estimado ao término do projeto considerando a velocidade simulada e a tarifa média atual da equipe.',
      formula: 'EAC = custo_realizado + ciclos_restantes × custo_médio_ciclo\n  custo_médio_ciclo = vel_sim × tarifa_média',
    },
    en: {
      name: 'Projected EAC — Estimate at Completion (What-If)',
      desc: 'Estimated total project cost at completion using the simulated velocity and current team average rate.',
      formula: 'EAC = actual_cost + remaining_cycles × avg_cycle_cost\n  avg_cycle_cost = sim_velocity × avg_rate',
    },
  },
  MCP10: {
    pt: {
      name: 'P10 — Cenário Otimista (Monte Carlo)',
      desc: '10% das simulações preveem conclusão em até este número de ciclos adicionais. Representa o cenário mais favorável com 90% de probabilidade de ser superado.',
      formula: '1.000 simulações de caminhada aleatória\n  Velocidade: N(vel_média, desvio_padrão)\n  P10 = 10º percentil dos ciclos até conclusão',
    },
    en: {
      name: 'P10 — Optimistic Scenario (Monte Carlo)',
      desc: '10% of simulations forecast completion within this many additional cycles. Best-case scenario, 90% chance of being exceeded.',
      formula: '1,000 random-walk simulations\n  Velocity: N(mean_velocity, stdev_velocity)\n  P10 = 10th percentile of cycles to completion',
    },
  },
  MCP50: {
    pt: {
      name: 'P50 — Cenário Central (Monte Carlo)',
      desc: '50% das simulações preveem conclusão em até este número de ciclos adicionais. Representa a estimativa mediana — tão provável de ser superada quanto de ser alcançada.',
      formula: '1.000 simulações de caminhada aleatória\n  P50 = mediana dos ciclos até conclusão\n  Equivale à previsão "mais provável"',
    },
    en: {
      name: 'P50 — Central Scenario (Monte Carlo)',
      desc: '50% of simulations forecast completion within this many additional cycles. The median estimate — equally likely to be met or missed.',
      formula: '1,000 random-walk simulations\n  P50 = median of cycles to completion\n  Equivalent to the "most likely" forecast',
    },
  },
  MCP90: {
    pt: {
      name: 'P90 — Cenário Pessimista (Monte Carlo)',
      desc: '90% das simulações preveem conclusão em até este número de ciclos adicionais. Represeta o pior cenário plausível; apenas 10% das simulações ultrapassam este valor.',
      formula: '1.000 simulações de caminhada aleatória\n  P90 = 90º percentil dos ciclos até conclusão\n  Recomendado como buffer de planejamento',
    },
    en: {
      name: 'P90 — Pessimistic Scenario (Monte Carlo)',
      desc: '90% of simulations forecast completion within this many additional cycles. Worst plausible case; only 10% of simulations exceed this value.',
      formula: '1,000 random-walk simulations\n  P90 = 90th percentile of cycles to completion\n  Recommended as the planning buffer target',
    },
  },
  MCMeanVel: {
    pt: {
      name: 'Velocidade Média (Monte Carlo)',
      desc: 'Média de todos os ciclos com horas > 0, usada como centro da distribuição gaussiana. Quanto maior o desvio padrão σ, maior o espalhamento entre P10 e P90. Usa toda a história (sem janela) para capturar a variância real do projeto.',
      formula: 'vel_média = Σ horas_ciclo ÷ nº ciclos (h > 0)\n  Distribuição amostrada: N(vel_média, σ)\n  σ = desvio padrão das velocidades históricas\n  Janela: TODOS os ciclos com h > 0 (sem limite)\n  Forecast/Runway: últimos 3 · Simulate: últimos 6',
    },
    en: {
      name: 'Mean Velocity (Monte Carlo)',
      desc: 'Average of all cycles with hours > 0, used as the centre of the Gaussian distribution. Higher σ means wider P10–P90 spread. Uses the full history (no window) to capture the project\'s true variance.',
      formula: 'mean_velocity = Σ cycle_hours ÷ cycle_count (h > 0)\n  Sampled distribution: N(mean_velocity, σ)\n  σ = standard deviation of historical velocities\n  Window: ALL cycles with h > 0 (no cap)\n  Forecast/Runway: last 3 · Simulate: last 6',
    },
  },
  RunwayAvg: {
    pt: {
      name: 'Média/ciclo — Runway',
      desc: 'Média de horas (ou custo) por ciclo dos últimos 3 ciclos do PEP. Usada para calcular os ciclos restantes e a conclusão estimada na tabela de saúde. Ciclos com zero horas são excluídos do denominador mas mantidos na janela.',
      formula: 'média = Σ h_ciclo (h > 0) ÷ nº ciclos não-zero\n  Janela: últimos 3 ciclos\n  Ex: [0, 8, 12] → (8+12) ÷ 2 = 10 h/ciclo\n  Alinhado ao Forecast (3 ciclos)\n  Simulate: últimos 6 · Monte Carlo: todos',
    },
    en: {
      name: 'Avg/cycle — Runway',
      desc: 'Average hours (or cost) per cycle over the last 3 cycles of the PEP. Used to estimate remaining cycles and projected completion in the health table. Zero-hour cycles are excluded from the denominator but kept within the window.',
      formula: 'avg = Σ cycle_h (h > 0) ÷ non-zero cycle count\n  Window: last 3 cycles\n  Ex: [0, 8, 12] → (8+12) ÷ 2 = 10 h/cycle\n  Aligned with Forecast (3 cycles)\n  Simulate: last 6 · Monte Carlo: all',
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
  const tipH = _evmTipEl.offsetHeight || 160;
  let left = rect.left;
  let top  = rect.bottom + 6;
  // clamp horizontally so the tooltip never leaves the viewport
  if (left + tipW > window.innerWidth - 8) left = Math.max(8, window.innerWidth - tipW - 8);
  // flip above the anchor when there is not enough room below
  if (top + tipH > window.innerHeight - 8) top = rect.top - tipH - 6;
  top = Math.max(8, top);
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
