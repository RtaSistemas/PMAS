/* PMAS — Frontend App */

// ---------------------------------------------------------------------------
// i18n
// ---------------------------------------------------------------------------
const _LANG = {
  pt: {
    'btn.import_ts':'⬆ Importar','btn.logout':'Sair','btn.lang':'EN',
    'tab.cycles':'Ciclos','tab.projects':'Projetos','tab.team':'Equipe',
    'filters.title':'Filtros','filter.cycle':'Ciclo','filter.pep_code':'PEP (Código)',
    'filter.pep_desc':'PEP (Descrição)','filter.collab':'Colaborador',
    'filter.dfrom':'Data início','filter.dto':'Data fim',
    'btn.load':'Carregar','btn.clear':'Limpar',
    'atab.effort':'Esforço da Equipe','atab.portfolio':'Saúde do Portfólio','atab.trends':'Tendências','atab.allocation':'Alocação','atab.forecast':'Previsão',
    'allocation.empty':'Nenhum dado encontrado para os filtros selecionados.',
    'allocation.collaborator':'Colaborador','allocation.total':'Total',
    'allocation.btn_h':'Horas','allocation.btn_r':'R$',
    'forecast.title':'Previsão de Conclusão (EVM)',
    'forecast.select_pep':'— selecione um PEP —',
    'forecast.empty':'Selecione um PEP para visualizar a previsão de conclusão.',
    'forecast.consumed':'Horas Consumidas','forecast.remaining':'Horas Restantes',
    'forecast.utilization':'Utilização','forecast.completion':'Conclusão Estimada',
    'forecast.realized':'Realizado','forecast.projection':'Projeção','forecast.budget_line':'Orçamento',
    'forecast.pv_line':'VP (Valor Planejado)',
    'forecast.spi':'IDP / SPI','forecast.sv':'Variação de Prazo (SV)',
    'forecast.no_budget':'Sem orçamento cadastrado para este PEP.',
    'effort.empty':'Selecione um ciclo ou PEP nos filtros e clique em Carregar.',
    'btn.stacked':'Vista: Empilhada','btn.grouped':'Vista: Agrupada',
    'btn.export_csv':'⬇ Exportar CSV','budget.title':'Orçado vs. Realizado por PEP',
    'radar.title':'Horas e Custo por PEP — Radar',
    'radar.note':'Valores normalizados · passe o mouse para ver totais absolutos',
    'portfolio.treemap_h':'Distribuição de Horas por PEP (Treemap)',
    'portfolio.treemap_r':'Custo Real por PEP (Treemap)',
    'portfolio.empty':'Nenhum dado de horas encontrado para os filtros selecionados.',
    'portfolio.note':'Blocos cinzas = PEP sem projeto cadastrado',
    'btn.view_hours':'Vista: Horas','btn.view_cost':'Vista: R$',
    'bullet.title':'Orçado vs. Realizado — Bullet Chart',
    'trends.title':'Queima de Horas por Ciclo','trends.pep_lbl':'PEP:',
    'trends.all':'Todos',
    'trends.empty':'Nenhum dado encontrado. Importe timesheets e crie ciclos para visualizar tendências.',
    'cycles.title':'Ciclos cadastrados','btn.new_cycle':'+ Novo ciclo',
    'cycles.search_ph':'Buscar por nome de ciclo…',
    'cycles.th.name':'Nome','cycles.th.start':'Início','cycles.th.end':'Fim',
    'cycles.th.type':'Tipo','cycles.th.recs':'Registros',
    'projects.title':'Projetos / PEPs','btn.new_project':'+ Novo projeto',
    'projects.search_ph':'Buscar por PEP, nome ou cliente…',
    'projects.th.pep':'Código PEP','projects.th.name':'Nome do Projeto',
    'projects.th.client':'Cliente','projects.th.mgr':'Gerente',
    'projects.th.budget':'Budget (h)','projects.th.status':'Status',
    'seniority.title':'Níveis de Senioridade','seniority.th.name':'Nome',
    'btn.new_seniority':'+ Novo nível',
    'ratecard.title':'Tabela de Taxas (Rate Card)','btn.new_ratecard':'+ Nova taxa',
    'ratecard.th.level':'Nível','ratecard.th.rate':'Valor/hora (R$)',
    'ratecard.th.from':'Vigência início','ratecard.th.to':'Vigência fim',
    'config.title':'Fatores Globais de Custo',
    'config.extra_lbl':'Multiplicador — Hora Extra',
    'config.standby_lbl':'Multiplicador — Hora Sobreaviso',
    'btn.save_config':'Salvar fatores',
    'team.title':'Colaboradores','btn.assign_all':'Atribuir a todos',
    'team.th.name':'Nome','team.th.seniority':'Senioridade','team.th.rate':'Taxa atual (R$/h)',
    'admin.title':'Gestão de Usuários','btn.new_user':'+ Novo usuário',
    'user.th.user':'Usuário','user.th.role':'Perfil',
    'btn.cancel':'Cancelar','btn.save':'Salvar','btn.edit':'Editar','btn.delete':'Excluir',
    'btn.export_csv2':'⬇ Exportar CSV','btn.import_csv':'⬆ Importar CSV',
    'cm.title_new':'Novo Ciclo','cm.title_edit':'Editar Ciclo',
    'cm.name_lbl':'Nome *','cm.name_ph':'Ex: Janeiro/2026',
    'cm.start_lbl':'Data início *','cm.end_lbl':'Data fim *',
    'pm.title_new':'Novo Projeto','pm.title_edit':'Editar Projeto',
    'pm.pep_lbl':'Código PEP *','pm.pep_ph':'Ex: 60OP-03333','pm.status_lbl':'Status',
    'pm.name_lbl':'Nome do Projeto','pm.name_ph':'Nome descritivo',
    'pm.client_lbl':'Cliente','pm.client_ph':'Nome do cliente',
    'pm.mgr_lbl':'Gerente','pm.mgr_ph':'Nome do gerente',
    'pm.bh_lbl':'Budget de horas','pm.bc_lbl':'Budget (R$)',
    'opt.ativo':'Ativo','opt.suspenso':'Suspenso','opt.encerrado':'Encerrado',
    'sm.title_new':'Novo Nível de Senioridade','sm.name_lbl':'Nome *','sm.name_ph':'Ex: Pleno, Sênior',
    'rm.title_new':'Nova Taxa','rm.level_lbl':'Nível de Senioridade *',
    'rm.rate_lbl':'Valor/hora (R$) *','rm.rate_ph':'Ex: 120.00',
    'rm.from_lbl':'Vigência início *','rm.to_lbl':'Vigência fim (opcional)',
    'as.title':'Atribuir Senioridade','as.level_lbl':'Nível de Senioridade',
    'as.none_opt':'— Sem senioridade —',
    'um.title':'Novo Usuário','um.user_lbl':'Usuário *','um.user_ph':'mínimo 3 caracteres',
    'um.pwd_lbl':'Senha *','um.pwd_ph':'mínimo 6 caracteres','um.role_lbl':'Perfil',
    'opt.user':'Usuário',
    'pwdm.title':'Alterar Senha','pwdm.new_lbl':'Nova senha *','pwdm.new_ph':'mínimo 6 caracteres',
    'ch.normal_h':'Horas Normais','ch.extra_h':'Horas Extras','ch.standby_h':'Sobreaviso',
    'ch.budget':'Budget','ch.actual':'Realizado','ch.hours':'Horas','ch.cost':'Custo (R$)',
    'ch.cycle_axis':'Ciclo','ch.cost_axis':'Custo Real (R$)',
    'badge.quarantine':'Quarentena','badge.regular':'Regular',
    'title.lock':'Bloquear ciclo','title.unlock':'Desbloquear ciclo',
    'title.archive':'Arquivar ciclo','title.restore':'Restaurar ciclo',
    'cycles.show_archived':'Mostrar arquivados',
    'anomaly.title':'⚠ Alertas de Anomalia na Importação',
    'stat.normal_h':'Horas Normais','stat.extra_h':'Horas Extras','stat.standby_h':'Sobreaviso',
    'stat.total':'Total','stat.collabs':'Colaboradores',
    'stat.budgeted':'Orçado (PEPs c/ budget)','stat.vs_budget':'Realizado vs Orçado',
    'budget.exceeded':'Estourado','budget.warning':'Atenção ≥90%',
    'lbl.admin':'Admin','lbl.user':'Usuário',
    'loading':'Carregando…','no_cycles':'Nenhum ciclo encontrado.',
    'no_projects':'Nenhum projeto encontrado.','no_seniority':'Nenhum nível cadastrado.',
    'no_rates':'Nenhuma taxa cadastrada.','no_team':'Nenhum colaborador encontrado.',
    'no_users':'Nenhum usuário encontrado.',
    'btn.assign':'Atribuir','btn.pwd':'Senha',
    'ch.actual_cost':'Custo Real',
    'tt.over_budget':'Acima do orçado','tt.utilization':'Utilização','tt.total_hours':'Total horas',
    'tt.project':'Projeto','tt.consumed':'Consumido','tt.actual_cost_lbl':'Custo real',
    'tt.utilized':'utilizado','tt.pep_not_reg':'⚠ PEP não cadastrado',
    'collab.timeline_title': 'Evolução por Ciclo — ',
    'collab.timeline_empty': 'Nenhum dado encontrado para este colaborador.',
    'auditlog.title':'Log de Auditoria','btn.refresh':'↺ Atualizar',
    'auditlog.filter.all_entity':'Todas entidades','auditlog.filter.all_action':'Todas ações',
    'auditlog.th.when':'Quando','auditlog.th.user':'Usuário','auditlog.th.action':'Ação',
    'auditlog.th.entity':'Entidade','auditlog.th.id':'ID','auditlog.th.detail':'Detalhe',
    'no_audit':'Nenhum evento registrado.',
    'cpi.title':'IDP — Índice de Desempenho de Custo por Ciclo',
    'plan.title':'Baseline de Planejamento (Horas/Ciclo)',
    'plan.btn_add':'+ Adicionar ciclo','plan.btn_export':'↓ Exportar CSV','plan.btn_import':'↑ Importar CSV',
    'plan.hint':'Define as horas planejadas por ciclo para calcular VP, IDP e Variação de Prazo.',
    'plan.th.cycle':'Ciclo','plan.th.hours':'Horas Planejadas',
    'plan.select_cycle':'— selecione um ciclo —','plan.no_plans':'Nenhum baseline definido.',
  },
  en: {
    'btn.import_ts':'⬆ Import','btn.logout':'Sign Out','btn.lang':'PT',
    'tab.cycles':'Cycles','tab.projects':'Projects','tab.team':'Team',
    'filters.title':'Filters','filter.cycle':'Cycle','filter.pep_code':'PEP (Code)',
    'filter.pep_desc':'PEP (Description)','filter.collab':'Collaborator',
    'filter.dfrom':'Start date','filter.dto':'End date',
    'btn.load':'Load','btn.clear':'Clear',
    'atab.effort':'Team Effort','atab.portfolio':'Portfolio Health','atab.trends':'Trends','atab.allocation':'Allocation','atab.forecast':'Forecast',
    'allocation.empty':'No data found for the selected filters.',
    'allocation.collaborator':'Collaborator','allocation.total':'Total',
    'allocation.btn_h':'Hours','allocation.btn_r':'R$',
    'forecast.title':'Completion Forecast (EVM)',
    'forecast.select_pep':'— select a PEP —',
    'forecast.empty':'Select a PEP to view the completion forecast.',
    'forecast.consumed':'Consumed Hours','forecast.remaining':'Remaining Hours',
    'forecast.utilization':'Utilization','forecast.completion':'Est. Completion',
    'forecast.realized':'Realized','forecast.projection':'Projection','forecast.budget_line':'Budget',
    'forecast.pv_line':'PV (Planned Value)',
    'forecast.spi':'SPI','forecast.sv':'Schedule Variance (SV)',
    'forecast.no_budget':'No budget registered for this PEP.',
    'effort.empty':'Select a cycle or PEP in the filters and click Load.',
    'btn.stacked':'View: Stacked','btn.grouped':'View: Grouped',
    'btn.export_csv':'⬇ Export CSV','budget.title':'Budget vs. Actual by PEP',
    'radar.title':'Hours & Cost by PEP — Radar',
    'radar.note':'Normalized values · hover for absolute totals',
    'portfolio.treemap_h':'Hour Distribution by PEP (Treemap)',
    'portfolio.treemap_r':'Actual Cost by PEP (Treemap)',
    'portfolio.empty':'No hour data found for the selected filters.',
    'portfolio.note':'Gray blocks = PEP without registered project',
    'btn.view_hours':'View: Hours','btn.view_cost':'View: R$',
    'bullet.title':'Budget vs. Actual — Bullet Chart',
    'trends.title':'Hours Burn by Cycle','trends.pep_lbl':'PEP:',
    'trends.all':'All',
    'trends.empty':'No data found. Import timesheets and create cycles to view trends.',
    'cycles.title':'Registered Cycles','btn.new_cycle':'+ New cycle',
    'cycles.search_ph':'Search by cycle name…',
    'cycles.th.name':'Name','cycles.th.start':'Start','cycles.th.end':'End',
    'cycles.th.type':'Type','cycles.th.recs':'Records',
    'projects.title':'Projects / PEPs','btn.new_project':'+ New project',
    'projects.search_ph':'Search by PEP, name or client…',
    'projects.th.pep':'PEP Code','projects.th.name':'Project Name',
    'projects.th.client':'Client','projects.th.mgr':'Manager',
    'projects.th.budget':'Budget (h)','projects.th.status':'Status',
    'seniority.title':'Seniority Levels','seniority.th.name':'Name',
    'btn.new_seniority':'+ New level',
    'ratecard.title':'Rate Card Table','btn.new_ratecard':'+ New rate',
    'ratecard.th.level':'Level','ratecard.th.rate':'Rate/hour (R$)',
    'ratecard.th.from':'Valid from','ratecard.th.to':'Valid to',
    'config.title':'Global Cost Factors',
    'config.extra_lbl':'Multiplier — Overtime',
    'config.standby_lbl':'Multiplier — Standby',
    'btn.save_config':'Save factors',
    'team.title':'Collaborators','btn.assign_all':'Assign to all',
    'team.th.name':'Name','team.th.seniority':'Seniority','team.th.rate':'Current rate (R$/h)',
    'admin.title':'User Management','btn.new_user':'+ New user',
    'user.th.user':'Username','user.th.role':'Role',
    'btn.cancel':'Cancel','btn.save':'Save','btn.edit':'Edit','btn.delete':'Delete',
    'btn.export_csv2':'⬇ Export CSV','btn.import_csv':'⬆ Import CSV',
    'cm.title_new':'New Cycle','cm.title_edit':'Edit Cycle',
    'cm.name_lbl':'Name *','cm.name_ph':'E.g.: January/2026',
    'cm.start_lbl':'Start date *','cm.end_lbl':'End date *',
    'pm.title_new':'New Project','pm.title_edit':'Edit Project',
    'pm.pep_lbl':'PEP Code *','pm.pep_ph':'E.g.: 60OP-03333','pm.status_lbl':'Status',
    'pm.name_lbl':'Project Name','pm.name_ph':'Descriptive name',
    'pm.client_lbl':'Client','pm.client_ph':'Client name',
    'pm.mgr_lbl':'Manager','pm.mgr_ph':'Manager name',
    'pm.bh_lbl':'Hours budget','pm.bc_lbl':'Budget (R$)',
    'opt.ativo':'Active','opt.suspenso':'Suspended','opt.encerrado':'Closed',
    'sm.title_new':'New Seniority Level','sm.name_lbl':'Name *','sm.name_ph':'E.g.: Mid, Senior',
    'rm.title_new':'New Rate','rm.level_lbl':'Seniority Level *',
    'rm.rate_lbl':'Rate/hour (R$) *','rm.rate_ph':'E.g.: 120.00',
    'rm.from_lbl':'Valid from *','rm.to_lbl':'Valid to (optional)',
    'as.title':'Assign Seniority','as.level_lbl':'Seniority Level',
    'as.none_opt':'— No seniority —',
    'um.title':'New User','um.user_lbl':'Username *','um.user_ph':'minimum 3 characters',
    'um.pwd_lbl':'Password *','um.pwd_ph':'minimum 6 characters','um.role_lbl':'Role',
    'opt.user':'User',
    'pwdm.title':'Change Password','pwdm.new_lbl':'New password *','pwdm.new_ph':'minimum 6 characters',
    'ch.normal_h':'Normal Hours','ch.extra_h':'Overtime','ch.standby_h':'Standby',
    'ch.budget':'Budget','ch.actual':'Actual','ch.hours':'Hours','ch.cost':'Cost (R$)',
    'ch.cycle_axis':'Cycle','ch.cost_axis':'Actual Cost (R$)',
    'badge.quarantine':'Quarantine','badge.regular':'Regular',
    'title.lock':'Lock cycle','title.unlock':'Unlock cycle',
    'title.archive':'Archive cycle','title.restore':'Restore cycle',
    'cycles.show_archived':'Show archived',
    'anomaly.title':'⚠ Ingestion Anomaly Alerts',
    'stat.normal_h':'Normal Hours','stat.extra_h':'Overtime','stat.standby_h':'Standby',
    'stat.total':'Total','stat.collabs':'Collaborators',
    'stat.budgeted':'Budgeted (PEPs w/ budget)','stat.vs_budget':'Actual vs Budget',
    'budget.exceeded':'Exceeded','budget.warning':'Warning ≥90%',
    'lbl.admin':'Admin','lbl.user':'User',
    'loading':'Loading…','no_cycles':'No cycles found.',
    'no_projects':'No projects found.','no_seniority':'No levels registered.',
    'no_rates':'No rates registered.','no_team':'No collaborators found.',
    'no_users':'No users found.',
    'btn.assign':'Assign','btn.pwd':'Password',
    'ch.actual_cost':'Actual Cost',
    'tt.over_budget':'Above budget','tt.utilization':'Utilization','tt.total_hours':'Total hours',
    'tt.project':'Project','tt.consumed':'Consumed','tt.actual_cost_lbl':'Actual cost',
    'tt.utilized':'utilized','tt.pep_not_reg':'⚠ PEP not registered',
    'collab.timeline_title': 'Cycle Evolution — ',
    'collab.timeline_empty': 'No data found for this collaborator.',
    'auditlog.title':'Audit Log','btn.refresh':'↺ Refresh',
    'auditlog.filter.all_entity':'All entities','auditlog.filter.all_action':'All actions',
    'auditlog.th.when':'When','auditlog.th.user':'User','auditlog.th.action':'Action',
    'auditlog.th.entity':'Entity','auditlog.th.id':'ID','auditlog.th.detail':'Detail',
    'no_audit':'No events recorded.',
    'cpi.title':'CPI — Cost Performance Index per Cycle',
    'plan.title':'Planning Baseline (Hours/Cycle)',
    'plan.btn_add':'+ Add cycle','plan.btn_export':'↓ Export CSV','plan.btn_import':'↑ Import CSV',
    'plan.hint':'Set planned hours per cycle to compute PV, SPI and Schedule Variance.',
    'plan.th.cycle':'Cycle','plan.th.hours':'Planned Hours',
    'plan.select_cycle':'— select a cycle —','plan.no_plans':'No baseline defined.',
  },
};
let _locale = localStorage.getItem('pmas_lang') || 'pt';
function _t(key) { return (_LANG[_locale] || _LANG.pt)[key] || key; }
function _applyI18n() {
  document.querySelectorAll('[data-i18n]').forEach(el => { el.textContent = _t(el.dataset.i18n); });
  document.querySelectorAll('[data-i18n-ph]').forEach(el => { el.placeholder = _t(el.dataset.i18nPh); });
}

// ---------------------------------------------------------------------------
// Multi-currency display (UI-only conversion, no backend calls)
// ---------------------------------------------------------------------------
let _currencyFactor = 1;
let _currencySymbol = 'R$';

function _fmtCost(rawValue) {
  const v = rawValue * _currencyFactor;
  return `${_currencySymbol} ${v.toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function _applyConversion(factor, symbol) {
  _currencyFactor = factor > 0 ? factor : 1;
  _currencySymbol = symbol || 'R$';
}

function _onCurrencyChange() {
  const factor = parseFloat(document.getElementById('currencyFactor').value);
  const symbol = document.getElementById('currencySymbol').value.trim();
  _applyConversion(factor, symbol);
  _renderActiveTab();
}

document.getElementById('currencyFactor').addEventListener('change', _onCurrencyChange);
document.getElementById('currencySymbol').addEventListener('change', _onCurrencyChange);

// ---------------------------------------------------------------------------
// Top-level tab navigation
// ---------------------------------------------------------------------------
const tabBtns     = document.querySelectorAll('.tab-btn');
const tabSections = document.querySelectorAll('.tab-section');

tabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    tabBtns.forEach(b => b.classList.remove('active'));
    tabSections.forEach(s => s.hidden = true);
    btn.classList.add('active');
    document.getElementById(`tab-${btn.dataset.tab}`).hidden = false;

    if (btn.dataset.tab === 'cycles')   loadCyclesTable();
    if (btn.dataset.tab === 'projects') loadProjectsTable();
    if (btn.dataset.tab === 'team')     loadTeamTab();
    if (btn.dataset.tab === 'admin')  { loadUsersTable(); loadAuditLog(); }
  });
});

// ---------------------------------------------------------------------------
// Analytics sub-tab navigation + ECharts instance registry
// ---------------------------------------------------------------------------

// Chart instance registry — keyed by DOM element id
const _charts = {};

// Which chart IDs belong to each sub-tab (to dispose on leave)
const CHARTS_PER_TAB = {
  effort:     ['effortChart', 'budgetChart', 'radarChart'],
  portfolio:  ['treemapChart', 'bulletChart'],
  trends:     ['trendsChart', 'cpiChart'],
  allocation: [],
  forecast:   ['forecastChart'],
};

function _disposeTabCharts(tabId) {
  (CHARTS_PER_TAB[tabId] || []).forEach(id => {
    if (_charts[id] && !_charts[id].isDisposed()) {
      _charts[id].dispose();
    }
    delete _charts[id];
  });
}

function _getOrCreateChart(id) {
  if (!_charts[id] || _charts[id].isDisposed()) {
    _charts[id] = echarts.init(document.getElementById(id), 'dark', { renderer: 'svg' });
  }
  return _charts[id];
}

// ResizeObserver — resize all live charts when container changes
const _ro = new ResizeObserver(() => {
  Object.values(_charts).forEach(c => { try { if (!c.isDisposed()) c.resize(); } catch (_) {} });
});
_ro.observe(document.querySelector('main'));

// Print hooks — hide toolbox icons before printing (SVG renderer embeds them
// as <path> elements inside <svg>, so @media print CSS cannot target them).
// Restore immediately after the print dialog closes.
window.addEventListener('beforeprint', () => {
  Object.values(_charts).forEach(c => { try { if (!c.isDisposed()) c.setOption({ toolbox: { show: false } }); } catch (_) {} });
});
window.addEventListener('afterprint', () => {
  Object.values(_charts).forEach(c => { try { if (!c.isDisposed()) c.setOption({ toolbox: { show: true  } }); } catch (_) {} });
});

// Sub-tab state
let _activeATab = 'effort';
let _stackMode  = true;   // true = stacked, false = grouped
let _evmMode    = false;  // false = hours, true = R$

const atabBtns     = document.querySelectorAll('.atab-btn');
const atabSections = document.querySelectorAll('.atab-section');

atabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    _disposeTabCharts(_activeATab);
    atabBtns.forEach(b => b.classList.remove('active'));
    atabSections.forEach(s => s.hidden = true);
    btn.classList.add('active');
    _activeATab = btn.dataset.atab;
    document.getElementById(`atab-${_activeATab}`).hidden = false;
    if (_activeATab === 'trends')   _populateTrendsPepSelect();
    if (_activeATab === 'forecast') _populateForecastPepSelect();
    _renderActiveTab();
  });
});

document.getElementById('evmToggleBtn').addEventListener('click', () => {
  _evmMode = !_evmMode;
  document.getElementById('evmToggleBtn').textContent = _evmMode ? _t('btn.view_cost') : _t('btn.view_hours');
  _renderPortfolioTab();
});

document.getElementById('exportCsvBtn').addEventListener('click', () => {
  if (!_lastEffortData.length) { notify('Carregue dados antes de exportar.', 'info'); return; }
  const header = 'Colaborador,Horas Normais,Horas Extras,Sobreaviso,Total';
  const rows = _lastEffortData.map(d => {
    const total = (d.normal_hours + d.extra_hours + d.standby_hours).toFixed(1);
    return `"${d.collaborator}",${d.normal_hours.toFixed(1)},${d.extra_hours.toFixed(1)},${d.standby_hours.toFixed(1)},${total}`;
  });
  const csv  = [header, ...rows].join('\n');
  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url; a.download = 'esforco-equipe.csv'; a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('stackToggleBtn').addEventListener('click', () => {
  _stackMode = !_stackMode;
  document.getElementById('stackToggleBtn').textContent =
    _stackMode ? _t('btn.stacked') : _t('btn.grouped');
  const ch = _charts['effortChart'];
  if (ch && !ch.isDisposed()) {
    ch.setOption(_buildEffortSeriesOnly(_stackMode), false);
  }
});

// ---------------------------------------------------------------------------
// Dashboard — DOM refs and multi-selects
// ---------------------------------------------------------------------------
const csvInput = document.getElementById('csvInput');
const loadBtn  = document.getElementById('loadBtn');
const clearBtn   = document.getElementById('clearBtn');

const cycleMs        = new MultiSelect(document.getElementById('cycleMs'),        '— Selecione ciclo(s) —',   onCycleChange);
const pepMs          = new MultiSelect(document.getElementById('pepMs'),           '— Todos os PEPs —',        onPepChange);
const pepDescMs      = new MultiSelect(document.getElementById('pepDescMs'),       '— Todas as descrições —',  onPepDescChange);
const collaboratorMs = new MultiSelect(document.getElementById('collaboratorMs'),  '— Todos —',                onCollabChange);

let pepDataCache = {};

async function onCycleChange()    { await Promise.all([refreshPeps(), refreshCollaborators()]); }
async function onPepChange()      { refreshPepDescriptions(); await refreshCollaborators(); }
async function onPepDescChange()  { await refreshCollaborators(); }
async function onCollabChange()   { await refreshPeps(); }

// ---------------------------------------------------------------------------
// Filter cascade helpers
// ---------------------------------------------------------------------------
async function loadDashboardCycles() {
  try {
    const cycles = await apiFetch('/api/cycles');
    cycleMs.setItems(cycles.map(c => ({ value: c.id, label: c.name })));
  } catch (e) { notify(`Erro ao carregar ciclos: ${e.message}`, 'error'); }
}

async function refreshPeps() {
  const cycleIds  = cycleMs.getValues();
  const collabIds = collaboratorMs.getValues();
  const p = new URLSearchParams();
  cycleIds.forEach(id  => p.append('cycle_id', id));
  collabIds.forEach(id => p.append('collaborator_id', id));
  try {
    const peps = await apiFetch(`/api/peps?${p}`);
    pepDataCache = {};
    peps.forEach(p => { pepDataCache[p.code] = p.descriptions || []; });
    pepMs.setItems(peps.map(p => ({ value: p.code, label: p.code })), true);
    refreshPepDescriptions();
  } catch (_) {}
}

function refreshPepDescriptions() {
  const selected = pepMs.getValues();
  const descs = [...new Set(selected.flatMap(code => pepDataCache[code] || []))];
  pepDescMs.setItems(descs.map(d => ({ value: d, label: d })), true);
}

async function refreshCollaborators() {
  const cycleIds = cycleMs.getValues();
  const pepCodes = pepMs.getValues();
  const pepDescs = pepDescMs.getValues();
  const p = new URLSearchParams();
  cycleIds.forEach(id => p.append('cycle_id', id));
  pepCodes.forEach(c  => p.append('pep_code', c));
  pepDescs.forEach(d  => p.append('pep_description', d));
  try {
    const collabs = await apiFetch(`/api/collaborators?${p}`);
    collaboratorMs.setItems(collabs.map(c => ({ value: c.id, label: c.name })), true);
  } catch (_) {}
}

// ---------------------------------------------------------------------------
// Upload
// ---------------------------------------------------------------------------
csvInput.addEventListener('change', async () => {
  const file = csvInput.files[0]; if (!file) return;
  notify(`Enviando "${file.name}"…`, 'info');
  const form = new FormData(); form.append('file', file);
  try {
    const res  = await fetch('/api/upload-timesheet', { method: 'POST', headers: _authHeaders(), body: form });
    const json = await res.json();
    if (res.status === 401) { _handleUnauthorized(); return; }
    if (!res.ok) { notify(`Erro: ${json.detail ?? res.statusText}`, 'error'); return; }
    let msg = `✔ ${json.records_inserted.toLocaleString('pt-BR')} registro(s) importado(s).`;
    if (json.records_skipped > 0)           msg += ` (${json.records_skipped} duplicata(s) ignorada(s))`;
    if (json.quarantine_cycles_created > 0) msg += ` ⚠ ${json.quarantine_cycles_created} ciclo(s) de Quarentena criado(s).`;
    notify(msg, json.quarantine_cycles_created > 0 ? 'info' : 'success');
    const warnings = json.warnings || [];
    const panel = document.getElementById('anomalyPanel');
    if (warnings.length) {
      document.getElementById('anomalyList').innerHTML = warnings.map(w => `<li>${escHtml(w)}</li>`).join('');
      panel.hidden = false;
    } else {
      panel.hidden = true;
    }
    await loadDashboardCycles();
    _renderActiveTab();
  } catch (err) { notify(`Falha na conexão: ${err.message}`, 'error'); }
});

// Language toggle
document.getElementById('langToggleBtn').addEventListener('click', () => {
  _locale = _locale === 'pt' ? 'en' : 'pt';
  localStorage.setItem('pmas_lang', _locale);
  document.getElementById('langToggleBtn').textContent = _t('btn.lang');
  _applyI18n();
  // Re-render dynamic content for active tab
  const tab = document.querySelector('.tab-btn.active')?.dataset.tab;
  if (tab === 'cycles')   _renderCyclesTable(_allCycles);
  if (tab === 'projects') _renderProjectsTable(_allProjects);
  if (tab === 'team')     loadTeamTab();
  if (tab === 'dashboard') _renderActiveTab();
});

// ---------------------------------------------------------------------------
// Load button
// ---------------------------------------------------------------------------
loadBtn.addEventListener('click', () => _renderActiveTab());

clearBtn.addEventListener('click', () => {
  cycleMs.clear(); pepMs.clear(); pepDescMs.clear(); collaboratorMs.clear();
  document.getElementById('dateFromInput').value = '';
  document.getElementById('dateToInput').value   = '';
  pepDataCache = {};
  _evmMode = false;
  document.getElementById('evmToggleBtn').textContent = _t('btn.view_hours');
  _disposeTabCharts('effort');
  _disposeTabCharts('portfolio');
  _disposeTabCharts('trends');
  _disposeTabCharts('allocation');
  document.getElementById('allocationMatrix').innerHTML = '';
  _showEmpty('allocationEmpty', false);
  _disposeTabCharts('forecast');
  document.getElementById('forecastKpis').hidden = true;
  document.getElementById('forecastKpis').innerHTML = '';
  _showEmpty('forecastEmpty', true);
  document.getElementById('effortStats').innerHTML = '';
  document.getElementById('budgetPanel').hidden  = true;
  document.getElementById('bulletPanel').hidden  = true;
  _showEmpty('effortEmpty',    false);
  _showEmpty('portfolioEmpty', false);
  _showEmpty('trendsEmpty',    false);
});

// ---------------------------------------------------------------------------
// Analytics — render dispatcher
// ---------------------------------------------------------------------------
async function _renderActiveTab() {
  if (_activeATab === 'effort')     await _renderEffortTab();
  if (_activeATab === 'portfolio')  await _renderPortfolioTab();
  if (_activeATab === 'trends')     await _renderTrendsTab();
  if (_activeATab === 'allocation') await _renderAllocationTab();
  if (_activeATab === 'forecast')   await _renderForecastTab();
}

function _showEmpty(id, show) {
  const el = document.getElementById(id);
  if (el) el.hidden = !show;
}

// ---------------------------------------------------------------------------
// Esforço da Equipe
// ---------------------------------------------------------------------------
let _lastEffortData = [];

async function _renderEffortTab() {
  const cycleIds  = cycleMs.getValues();
  const pepCodes  = pepMs.getValues();
  const pepDescs  = pepDescMs.getValues();
  const collabIds = collaboratorMs.getValues();
  const dateFrom  = document.getElementById('dateFromInput').value;
  const dateTo    = document.getElementById('dateToInput').value;

  const p = new URLSearchParams();
  pepCodes.forEach(c  => p.append('pep_code', c));
  pepDescs.forEach(d  => p.append('pep_description', d));
  collabIds.forEach(id => p.append('collaborator_id', id));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  try {
    let payload;
    if (cycleIds.length === 0) {
      payload = await apiFetch(`/api/dashboard?${p}`);
    } else {
      payload = await apiFetch(`/api/dashboard/${cycleIds[0]}?${p}`);
    }

    const data = payload.data || [];
    _lastEffortData = data;
    const bva  = (payload.budget_vs_actual || []).filter(d => d.budget_hours > 0);

    // Stats row
    document.getElementById('effortStats').innerHTML = '';
    document.getElementById('effortStats').appendChild(_buildStatsRow(data, bva));

    // Title
    document.getElementById('effortTitle').textContent = _buildEffortTitle(payload, cycleIds.length);

    if (data.length === 0) {
      _showEmpty('effortEmpty', true);
      _disposeTabCharts('effort');
      document.getElementById('budgetPanel').hidden = true;
      return;
    }
    _showEmpty('effortEmpty', false);

    // Effort chart
    const h = calcHeight(data.length);
    document.getElementById('effortChart').style.height = `${h}px`;
    const ch = _getOrCreateChart('effortChart');
    ch.setOption(_buildEffortOption(data, _stackMode), true);
    ch.resize();
    ch.off('click');
    ch.on('click', async (params) => {
      if (params && params.name) {
        await _openCollabTimelineModal(params.name);
      }
    });

    // Budget chart
    if (bva.length > 0) {
      document.getElementById('budgetPanel').hidden = false;
      document.getElementById('budgetChart').style.height =
        `${Math.max(220, bva.length * 56 + 80)}px`;
      const bch = _getOrCreateChart('budgetChart');
      bch.setOption(_buildBudgetOption(bva), true);
      bch.resize();
    } else {
      document.getElementById('budgetPanel').hidden = true;
    }

    // Radar chart
    const rp = new URLSearchParams(p);
    cycleIds.forEach(id => rp.append('cycle_id', id));
    const radarItems = await apiFetch(`/api/dashboard/pep-radar?${rp}`).catch(() => []);
    if (radarItems.length >= 3) {
      document.getElementById('radarPanel').hidden = false;
      const rc = _getOrCreateChart('radarChart');
      rc.setOption(_buildRadarOption(radarItems), true);
      rc.resize();
    } else {
      document.getElementById('radarPanel').hidden = true;
      if (_charts['radarChart'] && !_charts['radarChart'].isDisposed()) {
        _charts['radarChart'].dispose();
        delete _charts['radarChart'];
      }
    }
  } catch (err) { notify(`Erro: ${err.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// Saúde do Portfólio
// ---------------------------------------------------------------------------
async function _renderPortfolioTab() {
  const cycleIds = cycleMs.getValues();
  const pepCodes = pepMs.getValues();
  const dateFrom = document.getElementById('dateFromInput').value;
  const dateTo   = document.getElementById('dateToInput').value;
  const p = new URLSearchParams();
  cycleIds.forEach(id => p.append('cycle_id', id));
  pepCodes.forEach(c => p.append('pep_wbs', c));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  try {
    const health = await apiFetch(`/api/portfolio-health?${p}`);

    if (!health.length) {
      _showEmpty('portfolioEmpty', true);
      _disposeTabCharts('portfolio');
      document.getElementById('bulletPanel').hidden = true;
      return;
    }
    _showEmpty('portfolioEmpty', false);

    // Update treemap title
    document.getElementById('portfolioTreemapTitle').textContent =
      _evmMode ? _t('portfolio.treemap_r') : _t('portfolio.treemap_h');

    // Treemap
    const tm = _getOrCreateChart('treemapChart');
    tm.setOption(_buildTreemapOption(health, _evmMode), true);
    tm.resize();

    // Bullet chart — in hours mode use budget_hours, in R$ mode use budget_cost
    const withBudget = _evmMode
      ? health.filter(d => d.budget_cost != null)
      : health.filter(d => d.budget_hours != null);
    if (withBudget.length > 0) {
      document.getElementById('bulletPanel').hidden = false;
      document.getElementById('bulletChart').style.height =
        `${Math.max(220, withBudget.length * 60 + 80)}px`;
      const bc = _getOrCreateChart('bulletChart');
      bc.setOption(_buildBulletOption(withBudget, _evmMode), true);
      bc.resize();
    } else {
      document.getElementById('bulletPanel').hidden = true;
    }
  } catch (err) { notify(`Erro: ${err.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// Tendências
// ---------------------------------------------------------------------------
async function _populateTrendsPepSelect() {
  const sel = document.getElementById('trendsPepSelect');
  const current = sel.value;
  try {
    const peps = await apiFetch('/api/peps');
    sel.innerHTML = `<option value="">${_t('trends.all')}</option>` +
      peps.map(p => `<option value="${escHtml(p.code)}">${escHtml(p.code)}${p.descriptions[0] ? ' — ' + escHtml(p.descriptions[0]) : ''}</option>`).join('');
    if (peps.some(p => p.code === current)) sel.value = current;
  } catch (_) { /* non-critical */ }
}

async function _renderTrendsTab() {
  const localPep  = document.getElementById('trendsPepSelect').value;
  const dateFrom  = document.getElementById('dateFromInput').value;
  const dateTo    = document.getElementById('dateToInput').value;
  const p = new URLSearchParams();
  if (localPep) {
    p.append('pep_wbs', localPep);
  } else {
    pepMs.getValues().forEach(c => p.append('pep_wbs', c));
  }
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  try {
    const trends = await apiFetch(`/api/trends?${p}`);

    if (!trends.length) {
      _showEmpty('trendsEmpty', true);
      _disposeTabCharts('trends');
      return;
    }
    _showEmpty('trendsEmpty', false);

    const tc = _getOrCreateChart('trendsChart');
    tc.setOption(_buildTrendsOption(trends), true);
    tc.resize();

    // CPI chart — only if at least one cycle has a cpi value
    const cpiData = trends.filter(t => t.cpi != null);
    const cpiCard = document.getElementById('cpiChartCard');
    if (cpiData.length) {
      cpiCard.hidden = false;
      const cpiChart = _getOrCreateChart('cpiChart');
      cpiChart.setOption(_buildCpiOption(trends), true);
      cpiChart.resize();
    } else {
      cpiCard.hidden = true;
      if (_charts['cpiChart']) { _charts['cpiChart'].dispose(); delete _charts['cpiChart']; }
    }
  } catch (err) { notify(`Erro: ${err.message}`, 'error'); }
}

document.getElementById('trendsPepSelect').addEventListener('change', () => {
  if (_activeATab === 'trends') _renderTrendsTab();
});

// ---------------------------------------------------------------------------
// Alocação — Matriz Colaborador × Projeto
// ---------------------------------------------------------------------------

let _allocEvmMode = false;

document.getElementById('allocToggleBtn').addEventListener('click', () => {
  _allocEvmMode = !_allocEvmMode;
  document.getElementById('allocToggleBtn').textContent = _allocEvmMode ? _t('allocation.btn_r') : _t('allocation.btn_h');
  if (_activeATab === 'allocation') _renderAllocationTab();
});

async function _renderAllocationTab() {
  const cycleIds  = cycleMs.getValues();
  const collabIds = collaboratorMs.getValues();
  const pepCodes  = pepMs.getValues();
  const dateFrom  = document.getElementById('dateFromInput').value;
  const dateTo    = document.getElementById('dateToInput').value;

  const p = new URLSearchParams();
  cycleIds.forEach(id  => p.append('cycle_id', id));
  collabIds.forEach(id => p.append('collaborator_id', id));
  pepCodes.forEach(c   => p.append('pep_wbs', c));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to', dateTo);

  const emptyEl  = document.getElementById('allocationEmpty');
  const matrixEl = document.getElementById('allocationMatrix');

  try {
    const data = await apiFetch(`/api/allocation?${p}`);

    if (!data.length) {
      _showEmpty('allocationEmpty', true);
      matrixEl.innerHTML = '';
      return;
    }
    _showEmpty('allocationEmpty', false);

    // Collect unique PEPs
    const pepLabels = {};
    data.forEach(d => {
      if (d.pep_wbs) pepLabels[d.pep_wbs] = d.pep_description || d.pep_wbs;
    });

    // Build value map: matrix[collaborator][pep_wbs] = value
    const collabTotals = {};
    const pepTotals    = {};
    const matrix       = {};

    data.forEach(d => {
      const pep = d.pep_wbs || '__none__';
      const val = _allocEvmMode ? d.actual_cost : d.total_hours;
      if (!matrix[d.collaborator]) matrix[d.collaborator] = {};
      matrix[d.collaborator][pep] = (matrix[d.collaborator][pep] || 0) + val;
      collabTotals[d.collaborator] = (collabTotals[d.collaborator] || 0) + val;
      pepTotals[pep] = (pepTotals[pep] || 0) + val;
    });

    const sortedCollabs = Object.keys(collabTotals).sort((a, b) => collabTotals[b] - collabTotals[a]);
    const sortedPeps    = Object.keys(pepTotals).sort((a, b) => pepTotals[b] - pepTotals[a]);
    const grandTotal    = Object.values(collabTotals).reduce((a, b) => a + b, 0);
    const maxVal        = Math.max(...Object.values(collabTotals));

    const fmt = v => _allocEvmMode
      ? `R$ ${v.toLocaleString('pt-BR', {minimumFractionDigits: 0, maximumFractionDigits: 0})}`
      : `${v.toFixed(1)}h`;

    const cellBg = v => {
      if (!v) return '';
      const ratio = v / maxVal;
      const a = (0.08 + ratio * 0.72).toFixed(2);
      return `background:rgba(14,165,233,${a})`;
    };

    let html = '<table class="alloc-matrix"><thead><tr>';
    html += `<th>${_t('allocation.collaborator')}</th>`;
    sortedPeps.forEach(pep => {
      const label = pep === '__none__' ? '(sem PEP)' : (pepLabels[pep] || pep);
      const short = label.length > 18 ? label.slice(0, 16) + '…' : label;
      html += `<th title="${escHtml(label)}">${escHtml(short)}</th>`;
    });
    html += `<th>${_t('allocation.total')}</th></tr></thead><tbody>`;

    sortedCollabs.forEach(collab => {
      html += `<tr><td class="alloc-name">${escHtml(collab)}</td>`;
      sortedPeps.forEach(pep => {
        const v = matrix[collab]?.[pep] || 0;
        html += v
          ? `<td style="${cellBg(v)}">${fmt(v)}</td>`
          : `<td class="alloc-zero">—</td>`;
      });
      html += `<td class="alloc-total">${fmt(collabTotals[collab] || 0)}</td></tr>`;
    });

    html += `<tr class="alloc-footer"><td>${_t('allocation.total')}</td>`;
    sortedPeps.forEach(pep => {
      html += `<td>${fmt(pepTotals[pep] || 0)}</td>`;
    });
    html += `<td class="alloc-total">${fmt(grandTotal)}</td></tr>`;
    html += '</tbody></table>';

    matrixEl.innerHTML = html;
  } catch (err) {
    notify(`Erro: ${err.message}`, 'error');
  }
}

// ---------------------------------------------------------------------------
// Previsão de Conclusão (EVM)
// ---------------------------------------------------------------------------

async function _populateForecastPepSelect() {
  const sel = document.getElementById('forecastPepSelect');
  const current = sel.value;
  try {
    const peps = await apiFetch('/api/peps');
    sel.innerHTML = `<option value="">${_t('forecast.select_pep')}</option>` +
      peps.map(p => `<option value="${escHtml(p.code)}">${escHtml(p.code)}${p.descriptions[0] ? ' — ' + escHtml(p.descriptions[0]) : ''}</option>`).join('');
    if (peps.some(p => p.code === current)) sel.value = current;
  } catch (_) { /* non-critical */ }
}

document.getElementById('forecastPepSelect').addEventListener('change', () => {
  if (_activeATab === 'forecast') _renderForecastTab();
});

function _buildForecastKpis(fc) {
  const fmtH = h => `${(+h).toFixed(1)}h`;
  const fmtR = v => _fmtCost(v);

  const pct = fc.budget_hours
    ? `${Math.min(fc.consumed_hours / fc.budget_hours * 100, 999).toFixed(1)}%`
    : '—';
  const over = fc.budget_hours != null && fc.consumed_hours > fc.budget_hours;

  const cpiVal = fc.cpi != null ? (+fc.cpi).toFixed(2) : '—';
  const cpiCls = fc.cpi == null ? 'neutral' : fc.cpi >= 1.0 ? 'green' : fc.cpi >= 0.9 ? 'amber' : 'red';

  const spiVal = fc.spi != null ? (+fc.spi).toFixed(2) : '—';
  const spiCls = fc.spi == null ? 'neutral' : fc.spi >= 1.0 ? 'green' : fc.spi >= 0.9 ? 'amber' : 'red';
  const svFmt  = fc.sv != null ? (fc.sv >= 0 ? '+' : '') + fmtR(fc.sv) : '—';
  const svCls  = fc.sv == null ? 'neutral' : fc.sv >= 0 ? 'green' : 'red';

  const completionVal = fc.estimated_completion_cycle
    || (fc.estimated_cycles_to_complete != null ? `+${fc.estimated_cycles_to_complete} ciclos` : '—');

  const cards = [
    { val: fmtH(fc.consumed_hours),                          lbl: _t('forecast.consumed'),     cls: 'blue'              },
    { val: fc.remaining_hours != null ? fmtH(Math.max(0, fc.remaining_hours)) : '—',
                                                              lbl: _t('forecast.remaining'),    cls: over ? 'red' : 'neutral' },
    { val: pct,                                               lbl: _t('forecast.utilization'),  cls: over ? 'red' : 'green'   },
    { val: cpiVal,                                            lbl: 'CPI',                       cls: cpiCls              },
    { val: fc.eac != null ? fmtR(fc.eac) : '—',              lbl: 'EAC',                       cls: 'neutral'           },
    { val: spiVal,                                            lbl: _t('forecast.spi'),          cls: spiCls              },
    { val: svFmt,                                             lbl: _t('forecast.sv'),           cls: svCls               },
    { val: escHtml(String(completionVal)),                    lbl: _t('forecast.completion'),   cls: 'violet'            },
  ];
  return cards.map(({ val, lbl, cls }) =>
    `<div class="stat-card ${cls}"><div class="val">${val}</div><div class="lbl">${escHtml(lbl)}</div></div>`
  ).join('');
}

function _buildForecastOption(fc) {
  const history  = fc.history || [];
  const avg      = fc.avg_hours_per_cycle || 0;
  const lastCum  = history.length ? history.at(-1).cumulative_hours : 0;
  const budget   = fc.budget_hours;

  const projCount = budget && avg > 0
    ? Math.max(0, Math.min(Math.ceil((budget - lastCum) / avg) + 1, 14))
    : 6;

  const projCats = Array.from({ length: projCount }, (_, i) => `▸${i + 1}`);
  const projVals = [];
  for (let i = 1; i <= projCount; i++) {
    const v = lastCum + avg * i;
    projVals.push(+((budget ? Math.min(v, budget) : v)).toFixed(2));
  }

  const historyCats = history.map(h => h.cycle_name);
  const historyVals = history.map(h => h.cumulative_hours);
  const allCats = [...historyCats, ...projCats];
  const n = historyVals.length;

  // Realized series: historical values, null for projected slots
  const realizedData = [...historyVals, ...Array(projCount).fill(null)];

  // Projection series: null up to last historical, then projected values (bridged from last historical)
  const projectionData = [
    ...Array(n - 1).fill(null),
    historyVals.at(-1) ?? 0,
    ...projVals,
  ];

  // Budget flat line
  const budgetData = budget ? allCats.map(() => budget) : null;

  // Planned Value (PV) curve — only if history contains cumulative_planned_hours
  const hasPV = history.some(h => h.cumulative_planned_hours != null);
  const pvData = hasPV
    ? [...history.map(h => h.cumulative_planned_hours ?? null), ...Array(projCount).fill(null)]
    : null;

  const series = [
    {
      name: _t('forecast.realized'),
      type: 'line', yAxisIndex: 0,
      data: realizedData,
      smooth: false, symbol: 'circle', symbolSize: 6,
      lineStyle: { color: '#0ea5e9', width: 2.5 },
      itemStyle: { color: '#0ea5e9' },
      areaStyle: { color: 'rgba(14,165,233,0.10)' },
      connectNulls: false,
    },
    {
      name: _t('forecast.projection'),
      type: 'line', yAxisIndex: 0,
      data: projectionData,
      smooth: false, symbol: 'circle', symbolSize: 5,
      lineStyle: { color: '#94a3b8', width: 2, type: 'dashed' },
      itemStyle: { color: '#94a3b8' },
      connectNulls: false,
    },
  ];
  if (pvData) {
    series.push({
      name: _t('forecast.pv_line'),
      type: 'line', yAxisIndex: 0,
      data: pvData,
      symbol: 'none',
      lineStyle: { color: '#a78bfa', width: 2, type: 'dotted' },
      itemStyle: { color: '#a78bfa' },
      connectNulls: true,
    });
  }
  if (budgetData) {
    series.push({
      name: _t('forecast.budget_line'),
      type: 'line', yAxisIndex: 0,
      data: budgetData,
      symbol: 'none',
      lineStyle: { color: '#f59e0b', width: 1.5, type: 'dashed' },
      itemStyle: { color: '#f59e0b' },
    });
  }

  const legendData = [_t('forecast.realized'), _t('forecast.projection')];
  if (pvData) legendData.push(_t('forecast.pv_line'));
  if (budgetData) legendData.push(_t('forecast.budget_line'));

  return {
    backgroundColor: 'transparent',
    legend: {
      data: legendData, top: 8, left: 'center',
      textStyle: { color: '#cbd5e1', fontSize: 12 },
      itemGap: 24, itemWidth: 18, itemHeight: 10,
    },
    grid: { top: 44, right: '4%', bottom: 56, left: '2%', containLabel: true },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1e293b', borderColor: '#475569',
      textStyle: { color: '#e2e8f0' },
      formatter: params => {
        let html = `<b>${escHtml(params[0].axisValue)}</b><br>`;
        params.forEach(p => {
          if (p.value == null) return;
          html += `${p.marker} ${p.seriesName}: <b>${(+p.value).toFixed(1)}h</b><br>`;
        });
        return html;
      },
    },
    toolbox: _toolbox({
      dataZoom: { title: { zoom: 'Dar Zoom', back: 'Restaurar Zoom' } },
    }),
    xAxis: {
      type: 'category', data: allCats,
      axisLabel: { color: '#94a3b8', rotate: allCats.length > 8 ? 30 : 0, fontSize: 11 },
      axisTick: { alignWithLabel: true },
    },
    yAxis: {
      type: 'value', name: _t('ch.hours'),
      nameTextStyle: { color: '#94a3b8', fontSize: 11 },
      axisLabel: { color: '#94a3b8', fontSize: 11, formatter: v => `${v}h` },
      splitLine: { lineStyle: { color: '#334155' } },
    },
    series,
  };
}

async function _renderForecastTab() {
  await _populateForecastPepSelect();
  const pep      = document.getElementById('forecastPepSelect').value;
  const dateFrom = document.getElementById('dateFromInput').value;
  const dateTo   = document.getElementById('dateToInput').value;

  const kpisEl  = document.getElementById('forecastKpis');
  const emptyEl = document.getElementById('forecastEmpty');

  if (!pep) {
    _showEmpty('forecastEmpty', true);
    kpisEl.hidden = true;
    _disposeTabCharts('forecast');
    return;
  }

  const p = new URLSearchParams({ pep_wbs: pep });
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  try {
    const fc = await apiFetch(`/api/forecast?${p}`);
    _showEmpty('forecastEmpty', false);
    kpisEl.hidden = false;
    kpisEl.innerHTML = _buildForecastKpis(fc);
    const chart = _getOrCreateChart('forecastChart');
    chart.setOption(_buildForecastOption(fc), true);
    chart.resize();
    _currentForecastPep = pep;
    await _renderPlanTable(pep);
    document.getElementById('planCard').hidden = false;
  } catch (err) {
    _showEmpty('forecastEmpty', true);
    kpisEl.hidden = true;
    document.getElementById('planCard').hidden = true;
    _disposeTabCharts('forecast');
    if (!err.message?.includes('404')) notify(`Erro: ${err.message}`, 'error');
  }
}

// ---------------------------------------------------------------------------
// Plan management (ProjectCyclePlan)
// ---------------------------------------------------------------------------
let _currentForecastPep = null;
let _planProjectId = null;

async function _renderPlanTable(pep_wbs) {
  // Resolve project_id from pep_wbs
  try {
    const projects = await apiFetch('/api/projects');
    const proj = projects.find(p => p.pep_wbs === pep_wbs);
    _planProjectId = proj ? proj.id : null;
  } catch { _planProjectId = null; }

  const tbody = document.getElementById('planBody');
  if (!_planProjectId) {
    tbody.innerHTML = `<tr><td colspan="3" style="color:#64748b;font-size:.85rem;padding:.75rem">${_t('plan.no_plans')} (PEP não cadastrado)</td></tr>`;
    return;
  }
  try {
    const plans = await apiFetch(`/api/projects/${_planProjectId}/plans`);
    if (!plans.length) {
      tbody.innerHTML = `<tr><td colspan="3" style="color:#64748b;font-size:.85rem;padding:.75rem">${_t('plan.no_plans')}</td></tr>`;
      return;
    }
    tbody.innerHTML = plans.map(pl => `
      <tr>
        <td>${escHtml(pl.cycle_name)}</td>
        <td style="text-align:right">${(+pl.planned_hours).toLocaleString('pt-BR', {minimumFractionDigits:1, maximumFractionDigits:1})}</td>
        <td><button class="btn btn-danger btn-sm" onclick="deletePlan(${pl.cycle_id})">${_t('btn.delete')}</button></td>
      </tr>`).join('');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

async function deletePlan(cycle_id) {
  if (!_planProjectId) return;
  if (!confirm('Remover esta linha do baseline?')) return;
  try {
    await apiFetchJSON(`/api/projects/${_planProjectId}/plans/${cycle_id}`, 'DELETE');
    await _renderPlanTable(_currentForecastPep);
    _renderForecastTab();
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

document.getElementById('addPlanRowBtn').addEventListener('click', async () => {
  if (!_planProjectId) return;
  // Build a select of all available active cycles not yet planned
  try {
    const [allCycles, existingPlans] = await Promise.all([
      apiFetch('/api/cycles?include_archived=false'),
      apiFetch(`/api/projects/${_planProjectId}/plans`),
    ]);
    const plannedCycleIds = new Set(existingPlans.map(p => p.cycle_id));
    const available = allCycles.filter(c => !plannedCycleIds.has(c.id) && !c.is_quarantine);
    if (!available.length) { notify('Todos os ciclos já têm baseline definido.', 'info'); return; }
    const cycleId = parseInt(prompt(
      'ID do ciclo:\n' + available.map(c => `${c.id} — ${c.name}`).join('\n')
    ));
    if (!cycleId || isNaN(cycleId)) return;
    const hours = parseFloat(prompt('Horas planejadas para este ciclo:'));
    if (isNaN(hours) || hours < 0) return;
    await apiFetchJSON(`/api/projects/${_planProjectId}/plans/${cycleId}`, 'PUT', { cycle_id: cycleId, planned_hours: hours });
    await _renderPlanTable(_currentForecastPep);
    _renderForecastTab();
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
});

document.getElementById('exportPlanBtn').addEventListener('click', async () => {
  if (!_planProjectId) return;
  try {
    const res = await fetch(`/api/projects/${_planProjectId}/plans/export`, {
      headers: { Authorization: `Bearer ${localStorage.getItem('pmas_token')}` },
    });
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const disp = res.headers.get('Content-Disposition') || '';
    const match = disp.match(/filename="([^"]+)"/);
    const fname = match ? match[1] : 'baseline.csv';
    const url = URL.createObjectURL(blob);
    Object.assign(document.createElement('a'), { href: url, download: fname }).click();
    URL.revokeObjectURL(url);
  } catch (e) { notify(`Erro ao exportar: ${e.message}`, 'error'); }
});

document.getElementById('importPlanFile').addEventListener('change', async function () {
  const file = this.files[0];
  if (!file) return;
  this.value = '';
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/projects/plans/import', {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('pmas_token')}` },
      body: form,
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = `Baseline importado: ${data.created} criados, ${data.updated} atualizados` +
      (data.errors.length ? ` — ${data.errors.length} erro(s)` : '');
    notify(msg, data.errors.length ? 'warning' : 'success');
    if (data.errors.length) console.warn('Erros na importação de baseline:', data.errors);
    await _renderPlanTable(_currentForecastPep);
    _renderForecastTab();
  } catch (e) { notify(`Erro ao importar: ${e.message}`, 'error'); }
});

// ---------------------------------------------------------------------------
// Chart option builders
// ---------------------------------------------------------------------------

function calcHeight(count) { return Math.max(420, Math.min(count, 40) * 52 + 120); }

function _buildEffortTitle(payload, cycleCount) {
  const { cycle, filters } = payload;
  let t = cycleCount > 1 ? `${cycle.name} (+${cycleCount - 1} ciclo(s))` : cycle.name;
  if (filters.pep_codes?.length) t += `  |  PEP: ${filters.pep_codes.join(', ')}`;
  return t;
}

// ---------------------------------------------------------------------------
// Toolbox padrão ECharts — garante consistência visual em todos os gráficos.
// extra: objeto com features adicionais (magicType, dataZoom, etc.)
// ---------------------------------------------------------------------------
function _toolbox(extra = {}) {
  return {
    right: 10,
    top: 10,
    feature: {
      dataView:    { readOnly: true, title: 'Ver Dados',     lang: ['Dados do Gráfico', 'Fechar', 'Atualizar'] },
      restore:     { title: 'Restaurar' },
      saveAsImage: { title: 'Salvar Imagem', pixelRatio: 2 },
      ...extra,
    },
  };
}

function _buildEffortOption(data, stacked) {
  const MAX        = 40;
  const slice      = data.length > MAX ? data.slice(0, MAX) : data;
  const stack      = stacked ? 'total' : undefined;
  const byName     = Object.fromEntries(data.map(d => [d.collaborator, d]));
  const truncNote  = data.length > MAX
    ? `Exibindo ${MAX} de ${data.length} colaboradores`
    : '';

  // ── Totais por colaborador (para a linha de total) ──────────────────────
  const totals = slice.map(r =>
    +(r.normal_hours + r.extra_hours + r.standby_hours).toFixed(2)
  );

  // ── Maior total da série (para destacar o pico) ─────────────────────────
  const maxTotal = Math.max(...totals);

  return {
    backgroundColor: 'transparent',

    title: {
      subtext: truncNote.trim(),
      left: 'center',
      top: 4,
      subtextStyle: { color: '#64748b', fontSize: 11 },
    },

    legend: {
      data: [_t('ch.normal_h'), _t('ch.extra_h'), _t('ch.standby_h'), _t('stat.total')],
      top: 8,
      left: 'center',
      textStyle: { color: '#cbd5e1', fontSize: 12 },
      itemGap: 24,
      itemWidth: 14,
      itemHeight: 10,
    },

    grid: {
      top: 44,
      right: '8%',   // margem extra para os labels de total na linha
      bottom: 28,
      left: '2%',
      containLabel: true,
    },

    toolbox: _toolbox(),

    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#1e293b',
      borderColor: '#475569',
      textStyle: { color: '#e2e8f0' },
      formatter: params => {
        // ignora a série de total no tooltip (ela já aparece no rodapé)
        const bars = params.filter(p => p.seriesName !== _t('stat.total'));
        let html  = `<b>${params[0].axisValue}</b><br/>`;
        let total = 0;
        bars.forEach(p => {
          if (p.value > 0) {
            html  += `${p.marker}${p.seriesName}: <b>${p.value.toFixed(1)}h</b><br/>`;
            total += p.value;
          }
        });
        html += `<hr style="border-color:#334155;margin:4px 0"/>`;
        html += `Total: <b>${total.toFixed(1)}h</b>`;
        return html;
      },
    },

    xAxis: {
      type: 'value',
      name: _t('ch.hours'),
      nameTextStyle: { color: '#94a3b8', fontSize: 11 },
      axisLabel: {
        color: '#94a3b8',
        fontSize: 11,
        formatter: v => `${v}h`,
      },
      splitLine: { lineStyle: { color: '#1e293b' } },
    },

    yAxis: {
      type: 'category',
      data: slice.map(r => r.collaborator),
      axisTick: { show: false },
      axisLabel: {
        fontSize: 10,
        lineHeight: 16,
        formatter: name => {
          const d  = byName[name];
          if (!d) return name;
          const t  = (d.normal_hours + d.extra_hours + d.standby_hours).toFixed(1);
          const nm = name.length > 30 ? name.slice(0, 29) + '…' : name;
          return `{nm|${nm}}\n{hr|N:${d.normal_hours.toFixed(1)}h  E:${d.extra_hours.toFixed(1)}h  S:${d.standby_hours.toFixed(1)}h  ∑${t}h}`;
        },
        rich: {
          nm: { color: '#e2e8f0', fontSize: 11, lineHeight: 18 },
          hr: { color: '#64748b', fontSize: 9,  lineHeight: 14 },
        },
      },
    },

    series: [
      // ── Barra: Horas Normais ─────────────────────────────────────────────
      {
        name: _t('ch.normal_h'),
        type: 'bar',
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(180, 180, 180, 0.01)'
        },
        stack,
        data: slice.map(r => +r.normal_hours.toFixed(2)),
        itemStyle: { color: '#3b82f6' },
        barMaxWidth: 32,
        // Label visível apenas no modo empilhado e quando o segmento é grande o suficiente
        label: {
          show: !!stack,
          position: 'inside',
          fontSize: 9,
          color: '#fff',
          formatter: p => p.value >= 10 ? `${p.value.toFixed(1)}h` : '',
        },
      },

      // ── Barra: Horas Extras ──────────────────────────────────────────────
      {
        name: _t('ch.extra_h'),
        type: 'bar',
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(180, 180, 180, 0.01)'
        },
        stack,
        data: slice.map(r => +r.extra_hours.toFixed(2)),
        itemStyle: { color: '#f59e0b' },
        barMaxWidth: 32,
        label: {
          show: !!stack,
          position: 'inside',
          fontSize: 9,
          color: '#fff',
          formatter: p => p.value >= 10 ? `${p.value.toFixed(1)}h` : '',
        },
      },

      // ── Barra: Sobreaviso ────────────────────────────────────────────────
      {
        name: _t('ch.standby_h'),
        type: 'bar',
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(180, 180, 180, 0.01)'
        },
        stack,
        data: slice.map(r => +r.standby_hours.toFixed(2)),
        itemStyle: { color: '#8b5cf6' },
        barMaxWidth: 32,
        label: {
          show: !!stack,
          position: 'inside',
          fontSize: 9,
          color: '#fff',
          formatter: p => p.value >= 10 ? `${p.value.toFixed(1)}h` : '',
        },
      },

      // ── Linha de Total ───────────────────────────────────────────────────
      {
        name: _t('stat.total'),
        type: 'line',
        color: '#10b981',       // fixed color → legend icon shows green
        legendIcon: 'circle',   // avoids dashed-line artifact in legend
        data: totals,
        symbolSize: val => val === maxTotal ? 10 : 6,
        lineStyle: { width: 1, type: 'dashed' },
        itemStyle: {
          color: p => p.value === maxTotal ? '#f87171' : '#10b981',
        },
        label: {
          show: true,
          position: 'right',
          fontSize: 10,
          fontWeight: 600,
          color: '#10b981',
          formatter: p => p.value === maxTotal
            ? `{peak|${p.value.toFixed(1)}h}`
            : `${p.value.toFixed(1)}h`,
          rich: { peak: { color: '#f87171', fontWeight: 700 } },
        },
        z: 10,
      },
    ],
  };
}

// Only update the stack property — avoids full re-render flicker
function _buildEffortSeriesOnly(stacked) {
  const stack = stacked ? 'total' : undefined;
  return {
    series: [
      { name: _t('ch.normal_h'),  stack },
      { name: _t('ch.extra_h'),   stack },
      { name: _t('ch.standby_h'), stack },
    ],
  };
}

function _buildBudgetOption(budgetData) {
  const labels  = budgetData.map(d => d.pep_wbs + (d.name ? `\n${d.name.slice(0, 30)}` : ''));
  const budgets = budgetData.map(d => +(d.budget_hours.toFixed(2)));
  const actuals = budgetData.map((d, i) => ({
    value: +(d.actual_hours.toFixed(2)),
    itemStyle: { color: d.actual_hours > budgets[i] ? '#f87171' : '#34d399' },
  }));
  return {
    backgroundColor: 'transparent',
    legend: {
      data: [_t('ch.budget'), _t('ch.actual')], top: 8, left: 'center',
      textStyle: { color: '#cbd5e1', fontSize: 12 }, itemGap: 24, itemWidth: 14, itemHeight: 10,
    },
    grid: { top: 44, right: '3%', bottom: 28, left: '2%', containLabel: true },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      backgroundColor: '#1e293b', borderColor: '#475569', textStyle: { color: '#e2e8f0' },
      formatter: params => {
        const bVal = params.find(p => p.seriesName === _t('ch.budget'))?.value ?? 0;
        const aVal = params.find(p => p.seriesName === _t('ch.actual'))?.value ?? 0;
        const pct  = bVal > 0 ? ` (${(aVal / bVal * 100).toFixed(1)}%)` : '';
        let html = `<div style="font-weight:600;margin-bottom:4px">${params[0].axisValue.replace('\n', ' — ')}</div>`;
        params.forEach(p => {
          const extra = p.seriesName === _t('ch.actual') ? pct : '';
          html += `<div>${p.marker} ${p.seriesName}: <b>${p.value.toFixed(1)}h</b>${extra}</div>`;
        });
        if (bVal > 0 && aVal > bVal) html += `<div style="color:#f87171;font-size:11px;margin-top:4px">⚠ ${_t('tt.over_budget')}</div>`;
        return html;
      },
    },
    xAxis: { type: 'value', name: _t('ch.hours'), nameTextStyle: { color: '#94a3b8', fontSize: 11 }, axisLabel: { color: '#94a3b8', fontSize: 11, formatter: v => `${v}h` }, splitLine: { lineStyle: { color: '#1e293b' } } },
    yAxis: { type: 'category', data: labels, axisTick: { show: false }, axisLabel: { color: '#e2e8f0', fontSize: 10, lineHeight: 16 } },
    series: [
      { name: _t('ch.budget'), type: 'bar', data: budgets, itemStyle: { color: '#22d3ee' }, barMaxWidth: 28, barGap: '10%' },
      { name: _t('ch.actual'), type: 'bar', data: actuals,                                  barMaxWidth: 28, barGap: '10%' },
    ],
  };
}

function _buildRadarOption(items) {
  const maxH   = Math.max(...items.map(d => d.total_hours), 1);
  const maxC   = Math.max(...items.map(d => d.actual_cost), 1);
  const totalH = items.reduce((s, d) => s + d.total_hours, 0);
  const totalC = items.reduce((s, d) => s + d.actual_cost, 0);
  const fmtR   = v => _fmtCost(v);
  const abbrev = s => s.length > 20 ? s.slice(0, 19) + '…' : s;
  const LINE_H = 17;
  const TOP    = 44;   // abaixo do título
  return {
    backgroundColor: 'transparent',
    toolbox: _toolbox(),
    title: {
      text: `Total  ·  ${totalH.toFixed(1)}h  |  ${fmtR(totalC)}`,
      top: 6,
      left: 'center',
      textStyle: { color: '#e2e8f0', fontSize: 12, fontWeight: 600 },
    },
    legend: {
      data: [_t('ch.hours'), _t('ch.cost')],
      bottom: 4,
      textStyle: { color: '#cbd5e1', fontSize: 12 },
      itemGap: 24,
    },
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1e293b', borderColor: '#475569', textStyle: { color: '#e2e8f0' },
      formatter: params => {
        const isCost = params.name === _t('ch.cost');
        let html = `<b>${escHtml(params.name)}</b><br>`;
        (params.data.value || []).forEach((_, i) => {
          if (i >= items.length) return;
          const d = items[i];
          const raw = isCost ? fmtR(d.actual_cost) : `${d.total_hours.toFixed(1)}h`;
          html += `<span style="color:#94a3b8">${escHtml(d.pep_description)}</span>: <b>${raw}</b><br>`;
        });
        return html;
      },
    },
    radar: {
      indicator: items.map(d => ({ name: d.pep_description, max: 100 })),
      center: ['50%', '50%'],
      radius: '60%',
      axisName: { color: '#94a3b8', fontSize: 10 },
      splitLine: { lineStyle: { color: '#334155' } },
      splitArea: { areaStyle: { color: ['rgba(15, 23, 42, 0.95)', 'rgba(51, 65, 85, 0.30)'] } },
      axisLine: { lineStyle: { color: '#475569' } },
    },
    series: [{
      type: 'radar',
      data: [
        {
          name: _t('ch.hours'),
          value: items.map(d => +(d.total_hours / maxH * 100).toFixed(1)),
          itemStyle: { color: '#3b82f6' },
          lineStyle: { color: '#3b82f6', width: 1 },
          areaStyle: { color: 'rgba(59,130,246,0.15)' },
        },
        {
          name: _t('ch.cost'),
          value: items.map(d => +(d.actual_cost / maxC * 100).toFixed(1)),
          itemStyle: { color: '#f59e0b' },
          lineStyle: { color: '#f59e0b', width: 1 },
          areaStyle: { color: 'rgba(245,158,11,0.15)' },
        },
      ],
    }],

graphic: [
  // Painel esquerdo — horas por PEP
  {
    type: 'group',
    left: 4,
    top: TOP,
    children: [
      // Caixa única contornando todos os itens
      {
        type: 'rect',
        y: -8,
        shape: {
          x: 0,
          y: 0,
          width: 220,
          height: items.length * LINE_H + 8,
          r: 3,
        },
        style: {
          fill: 'transparent',
          stroke: '#5470c6',
          lineWidth: 0.8,
        },
        z: 0,
      },
      // Textos
      ...items.map((d, i) => ({
        type: 'text',
        x: 6,
        y: i * LINE_H,
        z: 1,
        style: {
          text: `${d.pep_description}: ${d.total_hours.toFixed(1)}h`,
          fill: '#94a3b8',
          fontSize: 10,
          textAlign: 'left',
        },
      })),
    ],
  },

  // Painel direito — custo por PEP
  {
    type: 'group',
    right: 4,
    top: TOP,
    children: [
      // Caixa única contornando todos os itens
      {
        type: 'rect',
        y: -8,
        shape: {
          x: -220,
          y: 0,
          width: 245,
          height: items.length * LINE_H + 8,
          r: 3,
        },
        style: {
          fill: 'transparent',
          stroke: '#f59e0b',
          lineWidth: 0.8,
        },
        z: 0,
      },
      // Textos
      ...items.map((d, i) => ({
        type: 'text',
        x: -214,
        y: i * LINE_H,
        z: 1,
        style: {
          text: `${d.pep_description}: ${fmtR(d.actual_cost)}`,
          fill: '#94a3b8',
          fontSize: 10,
          textAlign: 'left',
        },
      })),
    ],
  },
],
};
}

function _buildTreemapOption(health, evmMode = false) {
  const fmtVal = (v, raw = false) => evmMode
    ? (raw ? _fmtCost(v) : _fmtCost(v * _currencyFactor))
    : v.toFixed(1) + 'h';
  return {
    backgroundColor: 'transparent',
    toolbox: _toolbox(),
    tooltip: {
      trigger: 'item',
      backgroundColor: '#1e293b', borderColor: '#475569', textStyle: { color: '#e2e8f0' },
      formatter: params => {
        const d = health.find(x => x.pep_wbs === params.name);
        if (!d) return escHtml(params.name);
        let html = `<b>${escHtml(d.pep_wbs)}</b>`;
        if (d.pep_description) html += `<br><span style="color:#94a3b8">${escHtml(d.pep_description)}</span>`;
        if (d.name)            html += `<br>${_t('tt.project')}: ${escHtml(d.name)}`;
        const consumed = evmMode ? d.actual_cost : d.consumed_hours;
        const budget   = evmMode ? d.budget_cost : d.budget_hours;
        html += `<br>${evmMode ? _t('tt.actual_cost_lbl') : _t('tt.consumed')}: <b>${fmtVal(consumed, true)}</b>`;
        if (budget != null) {
          const pct = (consumed / budget * 100).toFixed(1);
          html += `<br>${_t('ch.budget')}: ${fmtVal(budget, true)} (${pct}% ${_t('tt.utilized')})`;
        }
        if (!d.is_registered) html += `<br><span style="color:#f59e0b">${_t('tt.pep_not_reg')}</span>`;
        return html;
      },
    },
    series: [{
      type: 'treemap',
      roam: false,
      width: '100%',
      height: '100%',
      breadcrumb: { show: false },
      label: {
        show: true, fontSize: 11, color: '#f1f5f9',
        formatter: params => {
          const d = health.find(x => x.pep_wbs === params.name);
          const val = d ? (evmMode ? d.actual_cost * _currencyFactor : d.consumed_hours) : 0;
          const valStr = evmMode
            ? _currencySymbol + (val / 1000 >= 1 ? (val / 1000).toFixed(0) + 'k' : val.toFixed(0))
            : val.toFixed(0) + 'h';
          const nm = params.name.length > 16 ? params.name.slice(0, 15) + '…' : params.name;
          return `${nm}\n${valStr}${d && !d.is_registered ? '\n⚠' : ''}`;
        },
      },
      itemStyle: { gapWidth: 2, borderRadius: 4 },
      levels: [{
        itemStyle: { borderWidth: 0, gapWidth: 4 },
        upperLabel: { show: false },
      }],
      data: health.map(d => {
        const consumed = evmMode ? d.actual_cost * _currencyFactor : d.consumed_hours;
        const budget   = evmMode ? (d.budget_cost ?? null) && d.budget_cost * _currencyFactor : d.budget_hours;
        return {
          name: d.pep_wbs,
          value: consumed,
          itemStyle: {
            color: !d.is_registered
              ? '#475569'
              : budget != null && consumed / budget >= 1.0
                ? 'rgba(248,113,113,0.75)'
                : budget != null && consumed / budget >= 0.75
                  ? 'rgba(245,158,11,0.75)'
                  : 'rgba(59,130,246,0.75)',
            borderColor: '#0f172a',
          },
        };
      }),
    }],
  };
}

function _buildBulletOption(withBudget, evmMode = false) {
  const labels  = withBudget.map(d => d.pep_wbs + (d.name ? `\n${d.name.slice(0, 28)}` : ''));
  const budgets = withBudget.map(d => (evmMode ? (d.budget_cost || 0) * _currencyFactor : d.budget_hours) || 0);
  const actuals = withBudget.map((d, i) => {
    const consumed = evmMode ? (d.actual_cost || 0) * _currencyFactor : d.consumed_hours;
    const pct = budgets[i] > 0 ? consumed / budgets[i] : 0;
    const color = pct >= 1.0 ? '#f87171' : pct >= 0.75 ? '#f59e0b' : '#3b82f6';
    return { value: +consumed.toFixed(2), itemStyle: { color, borderRadius: [0, 2, 2, 0] } };
  });
  const unit = evmMode ? _currencySymbol : 'h';
  const fmtAx = evmMode
    ? v => v >= 1000 ? `${_currencySymbol}${(v/1000).toFixed(0)}k` : `${_currencySymbol}${v.toFixed(0)}`
    : v => `${v}h`;
  return {
    backgroundColor: 'transparent',
    toolbox: _toolbox(),
    grid: { top: 46, right: '10%', bottom: 16, left: '2%', containLabel: true },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'none' },
      backgroundColor: '#1e293b', borderColor: '#475569', textStyle: { color: '#e2e8f0' },
      formatter: params => {
        const b = budgets[params[0].dataIndex];
        const a = params.find(p => p.seriesName === _t('ch.actual'))?.value ?? 0;
        const pct = b > 0 ? `${(a / b * 100).toFixed(1)}%` : '—';
        const fmtV = v => evmMode ? _fmtCost(v / _currencyFactor) : v.toFixed(1) + 'h';
        let html = `<b>${escHtml(params[0].axisValue.replace('\n', ' '))}</b><br>`;
        html += `${_t('ch.budget')}: <b>${fmtV(b)}</b><br>${_t('ch.actual')}: <b>${fmtV(a)}</b><br>`;
        html += `${_t('tt.utilization')}: <b>${pct}</b>`;
        if (b > 0 && a > b) html += `<br><span style="color:#f87171">⚠ ${_t('tt.over_budget')}</span>`;
        return html;
      },
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: '#94a3b8', fontSize: 10, formatter: fmtAx },
      splitLine: { lineStyle: { color: '#334155' } },
    },
    yAxis: {
      type: 'category', data: labels,
      axisTick: { show: false },
      axisLabel: { color: '#e2e8f0', fontSize: 10, lineHeight: 16 },
    },
    series: [
      {
        name: _t('ch.budget'),
        type: 'bar',
        barMaxWidth: 48,
        barGap: '-100%',
        z: 1,
        data: budgets.map(b => ({
          value: b,
          itemStyle: {
            color: 'rgba(148,163,184,0.18)',
            borderColor: 'rgba(148,163,184,0.35)',
            borderWidth: 1,
            borderRadius: [0, 3, 3, 0],
          },
        })),
      },
      {
        name: _t('ch.actual'),
        type: 'bar',
        barMaxWidth: 28,
        barGap: '-100%',
        z: 2,
        data: actuals,
        label: {
          show: true,
          position: 'right',
          fontSize: 10,
          color: '#e2e8f0',
          formatter: params => {
            const b = budgets[params.dataIndex];
            return b > 0 ? `${(params.value / b * 100).toFixed(0)}%` : '';
          },
        },
      },
    ],
  };
}

function _buildTrendsOption(trends) {
  const cats     = trends.map(d => d.cycle_name);
  const normals  = trends.map(d => +d.normal_hours.toFixed(2));
  const extras   = trends.map(d => +d.extra_hours.toFixed(2));
  const standbys = trends.map(d => +(d.standby_hours ?? 0).toFixed(2));
  const costs    = trends.map(d => +((d.actual_cost ?? 0) * _currencyFactor).toFixed(2));
  return {
    backgroundColor: 'transparent',
    toolbox: _toolbox({
      dataZoom: { title: { zoom: 'Dar Zoom', back: 'Restaurar Zoom' } },
    }),
    legend: {
      data: [_t('ch.normal_h'), _t('ch.extra_h'), _t('ch.standby_h'), _t('ch.actual_cost')],
      top: 8, left: 'center',
      textStyle: { color: '#cbd5e1', fontSize: 12 },
      itemGap: 24, itemWidth: 18, itemHeight: 10,
    },
    grid: { top: 44, right: '8%', bottom: 48, left: '2%', containLabel: true },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1e293b', borderColor: '#475569', textStyle: { color: '#e2e8f0' },
      formatter: params => {
        let html = `<b>${escHtml(params[0].axisValue)}</b><br>`;
        let totalHours = 0;
        params.forEach(p => {
          if (p.seriesName === _t('ch.actual_cost')) {
            html += `${p.marker} ${p.seriesName}: <b>${_fmtCost(p.value / _currencyFactor)}</b><br>`;
          } else {
            html += `${p.marker} ${p.seriesName}: <b>${p.value.toFixed(1)}h</b><br>`;
            totalHours += p.value;
          }
        });
        html += `<div style="border-top:1px solid #475569;padding-top:4px;margin-top:4px">${_t('tt.total_hours')}: <b>${totalHours.toFixed(1)}h</b></div>`;
        return html;
      },
    },
    xAxis: {
      type: 'category',
      data: cats,
      axisLabel: { color: '#94a3b8', rotate: cats.length > 6 ? 30 : 0, fontSize: 11 },
      axisTick: { alignWithLabel: true },
    },
    yAxis: [
      {
        type: 'value', name: _t('ch.hours'),
        nameTextStyle: { color: '#94a3b8', fontSize: 11 },
        axisLabel: { color: '#94a3b8', fontSize: 11, formatter: v => `${v}h` },
        splitLine: { lineStyle: { color: '#334155' } },
      },
      {
        type: 'value', name: _currencySymbol,
        nameTextStyle: { color: '#94a3b8', fontSize: 11 },
        axisLabel: { color: '#94a3b8', fontSize: 11, formatter: v => `${_currencySymbol}${(v/1000).toFixed(0)}k` },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: _t('ch.normal_h'), type: 'line', yAxisIndex: 0,
        data: normals, smooth: true, symbol: 'circle', symbolSize: 7,
        lineStyle: { color: '#3b82f6', width: 2.5 },
        itemStyle: { color: '#3b82f6' },
        areaStyle: { color: 'rgba(59,130,246,0.12)' },
      },
      {
        name: _t('ch.extra_h'), type: 'line', yAxisIndex: 0,
        data: extras, smooth: true, symbol: 'circle', symbolSize: 7,
        lineStyle: { color: '#f59e0b', width: 2.5 },
        itemStyle: { color: '#f59e0b' },
        areaStyle: { color: 'rgba(245,158,11,0.10)' },
      },
      {
        name: _t('ch.standby_h'), type: 'line', yAxisIndex: 0,
        data: standbys, smooth: true, symbol: 'circle', symbolSize: 7,
        lineStyle: { color: '#a855f7', width: 2.5 },
        itemStyle: { color: '#a855f7' },
        areaStyle: { color: 'rgba(168,85,247,0.10)' },
      },
      {
        name: _t('ch.actual_cost'), type: 'line', yAxisIndex: 1,
        data: costs, smooth: true, symbol: 'diamond', symbolSize: 8,
        lineStyle: { color: '#10b981', width: 2, type: 'dashed' },
        itemStyle: { color: '#10b981' },
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// Collaborator Timeline Modal
// ---------------------------------------------------------------------------
async function _openCollabTimelineModal(collaboratorName) {
  // 1. Pega filtros ativos da tela
  const pepCodes  = pepMs.getValues();
  const pepDescs  = pepDescMs.getValues();
  const dateFrom  = document.getElementById('dateFromInput').value;
  const dateTo    = document.getElementById('dateToInput').value;

  // 2. Monta query string
  const p = new URLSearchParams();
  p.set('collaborator_name', collaboratorName);
  pepCodes.forEach(c => p.append('pep_code', c));
  pepDescs.forEach(d => p.append('pep_description', d));
  if (dateFrom) p.set('date_from', dateFrom);
  if (dateTo)   p.set('date_to',   dateTo);

  // 3. Chama o endpoint
  let rows = [];
  try {
    rows = await apiFetch(`/api/dashboard/collaborator-timeline?${p}`);
  } catch (err) {
    notify('Erro ao carregar timeline do colaborador.', 'error');
    return;
  }

  // 4. Função auxiliar de fechar
  function _closeCollabModal() {
    const chartEl = document.getElementById('collabTimelineChart');
    const c = echarts.getInstanceByDom(chartEl);
    if (c && !c.isDisposed()) c.dispose();
    chartEl.style.display = 'none';
    modal.style.display = 'none';
  }

  // 5. Cria modal apenas uma vez
  let modal = document.getElementById('collabTimelineModal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'collabTimelineModal';
    modal.style.cssText = `
      position:fixed;inset:0;z-index:9999;
      display:flex;align-items:center;justify-content:center;
      background:rgba(0,0,0,0.7);
    `;
    modal.innerHTML = `
      <div style="background:#1e293b;border:1px solid #334155;border-radius:10px;
                  padding:1.5rem;width:min(860px,95vw);max-height:90vh;overflow:auto;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
          <span id="collabTimelineTitle"
            style="font-size:1rem;font-weight:600;color:#e2e8f0;"></span>
          <button id="collabTimelineClose"
            style="background:none;border:none;color:#94a3b8;font-size:1.4rem;
                   cursor:pointer;line-height:1;">✕</button>
        </div>
        <div id="collabTimelineEmpty"
          style="color:#64748b;text-align:center;padding:2rem;" hidden></div>
        <div id="collabTimelineChart" style="width:100%;height:360px;"></div>
      </div>
    `;
    document.body.appendChild(modal);

    document.getElementById('collabTimelineClose').addEventListener('click', () => {
      _closeCollabModal();
    });

    modal.addEventListener('click', (e) => {
      if (e.target === modal) _closeCollabModal();
    });
  }

  // 6. Exibe o modal
  modal.style.display = 'flex';

  // 7. Atualiza título
  document.getElementById('collabTimelineTitle').textContent =
    _t('collab.timeline_title') + collaboratorName;

  // 8. Sem dados
  const emptyEl = document.getElementById('collabTimelineEmpty');
  const chartEl = document.getElementById('collabTimelineChart');

  if (!rows.length) {
    emptyEl.textContent = _t('collab.timeline_empty');
    emptyEl.hidden = false;
    chartEl.style.display = 'none';
    return;
  }

  emptyEl.hidden = true;
  chartEl.style.display = '';

  // 9. Destrói instância anterior se existir
  const existing = echarts.getInstanceByDom(chartEl);
  if (existing && !existing.isDisposed()) existing.dispose();

  // 10. Renderiza gráfico
  const tc = echarts.init(chartEl, 'dark', { renderer: 'svg' });
  const cycles = rows.map(r => r.cycle_name);

  tc.setOption({
    backgroundColor: 'transparent',
    legend: {
      data: [_t('ch.normal_h'), _t('ch.extra_h'), _t('ch.standby_h')],
      top: 8,
      left: 'center',
      textStyle: { color: '#cbd5e1', fontSize: 12 },
      itemGap: 24,
      itemWidth: 14,
      itemHeight: 10,
    },
    grid: { top: 44, right: '4%', bottom: 56, left: '4%', containLabel: true },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: '#1e293b',
      borderColor: '#475569',
      textStyle: { color: '#e2e8f0' },
      formatter: params => {
        let html = `<b>${params[0].axisValue}</b><br/>`;
        let total = 0;
        params.forEach(p => {
          if (p.value > 0) {
            html += `${p.marker}${p.seriesName}: <b>${p.value.toFixed(1)}h</b><br/>`;
            total += p.value;
          }
        });
        html += `<hr style="border-color:#334155;margin:4px 0"/>Total: <b>${total.toFixed(1)}h</b>`;
        return html;
      },
    },
    toolbox: _toolbox({
      magicType: { type: ['stack', 'tiled'], title: { stack: 'Empilhado', tiled: 'Lado a Lado' } },
    }),
    xAxis: {
      type: 'category',
      data: cycles,
      axisLabel: {
        color: '#94a3b8',
        fontSize: 10,
        rotate: 30,
      },
      axisLine: { lineStyle: { color: '#334155' } },
    },
    yAxis: {
      type: 'value',
      name: 'h',
      nameTextStyle: { color: '#94a3b8', fontSize: 11 },
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      splitLine: { lineStyle: { color: '#1e293b' } },
    },
    series: [
      {
        name: _t('ch.normal_h'),
        type: 'bar',
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(180, 180, 180, 0.01)'
        },
        label: {
          show: true,
          position: 'inside',
          fontSize: 9,
          color: '#fff',
          formatter: p => p.value >= 10 ? `${p.value.toFixed(1)}h` : '',
        },
        stack: 'total',
        data: rows.map(r => +r.normal_hours.toFixed(2)),
        itemStyle: { color: '#3b82f6' },
        barMaxWidth: 48,
      },
      {
        name: _t('ch.extra_h'),
        type: 'bar',
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(180, 180, 180, 0.01)'
        },
        label: {
          show: true,
          position: 'inside',
          fontSize: 9,
          color: '#fff',
          formatter: p => p.value >= 10 ? `${p.value.toFixed(1)}h` : '',
        },
        stack: 'total',
        data: rows.map(r => +r.extra_hours.toFixed(2)),
        itemStyle: { color: '#f59e0b' },
        barMaxWidth: 48,
      },
      {
        name: _t('ch.standby_h'),
        type: 'bar',
        showBackground: true,
        backgroundStyle: {
          color: 'rgba(180, 180, 180, 0.01)'
        },
        label: {
          show: true,
          position: 'inside',
          fontSize: 9,
          color: '#fff',
          formatter: p => p.value >= 10 ? `${p.value.toFixed(1)}h` : '',
        },
        stack: 'total',
        data: rows.map(r => +r.standby_hours.toFixed(2)),
        itemStyle: { color: '#8b5cf6' },
        barMaxWidth: 48,
      },
    ],
  });
}

// ---------------------------------------------------------------------------
// CPI trend chart
// ---------------------------------------------------------------------------
function _buildCpiOption(trends) {
  const cats = trends.map(d => d.cycle_name);
  // connectNulls: true bridges cycles with no CPI value
  const cpiSeries = trends.map(d => d.cpi != null ? +d.cpi.toFixed(3) : null);
  return {
    backgroundColor: 'transparent',
    toolbox: _toolbox({
      dataZoom: { title: { zoom: 'Dar Zoom', back: 'Restaurar Zoom' } },
    }),
    tooltip: {
      trigger: 'axis',
      formatter: params => {
        const p = params[0];
        if (p.value == null) return `${p.name}<br/>IDP: —`;
        const color = p.value >= 1 ? '#4ade80' : p.value >= 0.9 ? '#fbbf24' : '#f87171';
        return `${p.name}<br/>IDP: <b style="color:${color}">${p.value.toFixed(3)}</b>`;
      },
    },
    grid: { left: 60, right: 20, top: 20, bottom: 50 },
    xAxis: { type: 'category', data: cats, axisLabel: { color: '#94a3b8', fontSize: 10, rotate: 30 } },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#94a3b8', fontSize: 10 },
      splitLine: { lineStyle: { color: '#1e293b' } },
    },
    series: [{
      type: 'line',
      data: cpiSeries,
      connectNulls: true,
      smooth: false,
      lineStyle: { color: '#60a5fa', width: 2 },
      itemStyle: {
        color: params => {
          const v = params.value;
          if (v == null) return '#60a5fa';
          return v >= 1 ? '#4ade80' : v >= 0.9 ? '#fbbf24' : '#f87171';
        },
      },
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: '#94a3b8', type: 'dashed', width: 1 },
        label: { formatter: 'IDP = 1.0', color: '#94a3b8', fontSize: 10 },
        data: [{ yAxis: 1.0 }],
      },
    }],
  };
}

// ---------------------------------------------------------------------------
// Stats row (effort tab)
// ---------------------------------------------------------------------------
function _buildStatsRow(data, budgetData = []) {
  let normal = 0, extra = 0, standby = 0;
  data.forEach(r => { normal += r.normal_hours; extra += r.extra_hours; standby += r.standby_hours; });
  const total = normal + extra + standby;
  const row   = document.createElement('div'); row.className = 'stats-row';
  const cards = [
    { val: fmt(normal),  lbl: _t('stat.normal_h'),  cls: 'blue'    },
    { val: fmt(extra),   lbl: _t('stat.extra_h'),   cls: 'amber'   },
    { val: fmt(standby), lbl: _t('stat.standby_h'), cls: 'violet'  },
    { val: fmt(total),   lbl: _t('stat.total'),     cls: 'green'   },
    { val: data.length,  lbl: _t('stat.collabs'),   cls: 'neutral' },
  ];
  if (budgetData.length > 0) {
    const totalBudget = budgetData.reduce((s, d) => s + d.budget_hours, 0);
    const totalActual = budgetData.reduce((s, d) => s + d.actual_hours, 0);
    const pct  = totalBudget > 0 ? (totalActual / totalBudget * 100).toFixed(1) : '—';
    const over = totalBudget > 0 && totalActual > totalBudget;
    cards.push(
      { val: fmt(totalBudget), lbl: _t('stat.budgeted'),   cls: 'neutral' },
      { val: `${pct}%`,        lbl: _t('stat.vs_budget'),  cls: over ? 'red' : 'green' },
    );
  }
  cards.forEach(({ val, lbl, cls }) => {
    const card = document.createElement('div'); card.className = `stat-card ${cls}`;
    card.innerHTML = `<div class="val">${val}</div><div class="lbl">${lbl}</div>`;
    row.appendChild(card);
  });
  return row;
}

// ---------------------------------------------------------------------------
// Cycles management
// ---------------------------------------------------------------------------
let _cycleEditId = null;
let _allCycles   = [];

async function loadCyclesTable() {
  const showArchived = document.getElementById('showArchivedCycles')?.checked;
  const url = showArchived ? '/api/cycles?include_archived=true' : '/api/cycles';
  try {
    _allCycles = await apiFetch(url);
    _renderCyclesTable(_allCycles);
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _renderCyclesTable(cycles) {
  const tbody = document.getElementById('cyclesBody');
  if (!cycles.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#475569;padding:2rem">${_t('no_cycles')}</td></tr>`;
    return;
  }
  const admin = _isAdmin();
  tbody.innerHTML = cycles.map(c => `
    <tr style="${!c.is_active ? 'opacity:.5' : ''}">
      <td>${escHtml(c.name)}${!c.is_active ? ' <em style="color:#64748b;font-size:.8rem">(arquivado)</em>' : ''}</td>
      <td>${c.start_date}</td>
      <td>${c.end_date}</td>
      <td><span class="badge-status ${c.is_quarantine ? 'quarantine' : 'ativo'}">${c.is_quarantine ? _t('badge.quarantine') : _t('badge.regular')}</span></td>
      <td style="text-align:right">${c.record_count.toLocaleString('pt-BR')}</td>
      <td><div class="actions">
        ${admin ? `<button class="btn btn-sm ${c.is_closed ? 'btn-warning' : 'btn-secondary'}" onclick="toggleCycleLock(${c.id}, ${c.is_closed})" title="${c.is_closed ? _t('title.unlock') : _t('title.lock')}">${c.is_closed ? '🔒' : '🔓'}</button>` : ''}
        ${admin ? `<button class="btn btn-sm btn-secondary" onclick="toggleCycleArchive(${c.id}, ${c.is_active})" title="${c.is_active ? _t('title.archive') : _t('title.restore')}">${c.is_active ? '📦' : '↩'}</button>` : ''}
        <button class="btn btn-secondary btn-sm" onclick="openCycleModal(${c.id})">${_t('btn.edit')}</button>
        <button class="btn btn-danger btn-sm" onclick="deleteCycle(${c.id}, ${escHtml(JSON.stringify(c.name))}, ${c.record_count})">${_t('btn.delete')}</button>
      </div></td>
    </tr>`).join('');
}

async function toggleCycleLock(id, isClosed) {
  const label = isClosed ? 'Desbloquear' : 'Bloquear';
  if (!confirm(`${label} este ciclo?`)) return;
  try {
    await apiFetchJSON(`/api/cycles/${id}/toggle-status`, 'PATCH');
    loadCyclesTable();
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

async function toggleCycleArchive(id, isActive) {
  const label = isActive ? 'Arquivar' : 'Restaurar';
  if (!confirm(`${label} este ciclo?`)) return;
  try {
    await apiFetchJSON(`/api/cycles/${id}/toggle-archive`, 'PATCH');
    loadCyclesTable();
    loadDashboardCycles();
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

document.getElementById('showArchivedCycles').addEventListener('change', loadCyclesTable);

function openCycleModal(id = null) {
  _cycleEditId = id;
  document.getElementById('cycleModalTitle').textContent = id ? _t('cm.title_edit') : _t('cm.title_new');
  document.getElementById('cycleError').textContent = '';
  if (id) {
    const c = _allCycles.find(x => x.id === id);
    if (c) {
      document.getElementById('cycleNameInput').value  = c.name;
      document.getElementById('cycleStartInput').value = c.start_date;
      document.getElementById('cycleEndInput').value   = c.end_date;
    }
  } else {
    document.getElementById('cycleNameInput').value  = '';
    document.getElementById('cycleStartInput').value = '';
    document.getElementById('cycleEndInput').value   = '';
  }
  document.getElementById('cycleModal').hidden = false;
}

function closeCycleModal() { document.getElementById('cycleModal').hidden = true; }

document.getElementById('cycleSaveBtn').addEventListener('click', async () => {
  const body = {
    name:       document.getElementById('cycleNameInput').value.trim(),
    start_date: document.getElementById('cycleStartInput').value,
    end_date:   document.getElementById('cycleEndInput').value,
  };
  if (!body.name || !body.start_date || !body.end_date) {
    document.getElementById('cycleError').textContent = 'Preencha todos os campos obrigatórios.';
    return;
  }
  try {
    if (_cycleEditId) {
      await apiFetchJSON(`/api/cycles/${_cycleEditId}`, 'PUT', body);
    } else {
      await apiFetchJSON('/api/cycles', 'POST', body);
    }
    closeCycleModal();
    loadCyclesTable();
    loadDashboardCycles();
  } catch (e) {
    document.getElementById('cycleError').textContent = e.message;
  }
});

document.getElementById('cycleCancelBtn').addEventListener('click', closeCycleModal);
document.getElementById('cycleModalClose').addEventListener('click', closeCycleModal);
document.getElementById('newCycleBtn').addEventListener('click', () => openCycleModal());

document.getElementById('cycleSearch').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  _renderCyclesTable(q ? _allCycles.filter(c => c.name.toLowerCase().includes(q)) : _allCycles);
});

async function deleteCycle(id, name, count) {
  if (count > 0) { notify(`Ciclo "${name}" possui ${count} registro(s) e não pode ser excluído.`, 'error'); return; }
  if (!confirm(`Excluir o ciclo "${name}"?`)) return;
  try { await apiFetchJSON(`/api/cycles/${id}`, 'DELETE'); loadCyclesTable(); loadDashboardCycles(); }
  catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

document.getElementById('exportCyclesBtn').addEventListener('click', () => {
  if (!_allCycles.length) { notify('Nenhum ciclo para exportar.', 'info'); return; }
  const header = 'name,start_date,end_date,is_quarantine,is_closed,record_count';
  const rows = _allCycles.map(c =>
    `"${c.name}",${c.start_date},${c.end_date},${c.is_quarantine},${c.is_closed},${c.record_count}`
  );
  const blob = new Blob(['﻿' + [header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: 'ciclos.csv' });
  a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('importCyclesInput').addEventListener('change', async e => {
  const file = e.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/cycles/import', { method: 'POST', headers: _authHeaders(), body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = `Importação concluída: ${data.created} criado(s)` +
      (data.errors.length ? `; ${data.errors.length} erro(s): ${data.errors.slice(0,3).join('; ')}` : '');
    notify(msg, data.errors.length ? 'error' : 'success');
    loadCyclesTable();
    loadDashboardCycles();
  } catch (err) { notify(`Erro na importação: ${err.message}`, 'error'); }
  e.target.value = '';
});

// ---------------------------------------------------------------------------
// Projects management
// ---------------------------------------------------------------------------
let _projectEditId  = null;
let _allProjects    = [];
let _consumedByPep  = {};

async function loadProjectsTable() {
  try {
    const [projects, health] = await Promise.all([
      apiFetch('/api/projects'),
      apiFetch('/api/portfolio-health').catch(() => []),
    ]);
    _allProjects   = projects;
    _consumedByPep = Object.fromEntries(health.map(h => [h.pep_wbs, h.consumed_hours]));
    _renderProjectsTable(projects);
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _buildBudgetCell(p) {
  if (p.budget_hours == null) return '—';
  const consumed = _consumedByPep[p.pep_wbs];
  const budgetStr = p.budget_hours.toLocaleString('pt-BR') + 'h';
  if (!consumed) return budgetStr;
  const pct = consumed / p.budget_hours;
  if (pct >= 1.0) return `${budgetStr}<span class="badge-budget critical" title="${consumed.toFixed(1)}h consumidas">${_t('budget.exceeded')}</span>`;
  if (pct >= 0.9) return `${budgetStr}<span class="badge-budget warning" title="${consumed.toFixed(1)}h consumidas">${_t('budget.warning')}</span>`;
  return budgetStr;
}

function _renderProjectsTable(projects) {
  const tbody = document.getElementById('projectsBody');
  if (!projects.length) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:#475569;padding:2rem">${_t('no_projects')}</td></tr>`;
    return;
  }
  tbody.innerHTML = projects.map(p => `
    <tr>
      <td><code>${escHtml(p.pep_wbs)}</code></td>
      <td>${escHtml(p.name || '—')}</td>
      <td>${escHtml(p.client || '—')}</td>
      <td>${escHtml(p.manager || '—')}</td>
      <td style="text-align:right">${_buildBudgetCell(p)}</td>
      <td><span class="badge-status ${p.status}">${p.status}</span></td>
      <td><div class="actions">
        <button class="btn btn-secondary btn-sm" onclick="openProjectModal(${p.id})">${_t('btn.edit')}</button>
        <button class="btn btn-danger btn-sm" onclick="deleteProject(${p.id}, ${escHtml(JSON.stringify(p.pep_wbs))})">${_t('btn.delete')}</button>
      </div></td>
    </tr>`).join('');
}

function openProjectModal(id = null) {
  _projectEditId = id;
  document.getElementById('projectModalTitle').textContent = id ? _t('pm.title_edit') : _t('pm.title_new');
  document.getElementById('projectError').textContent = '';
  if (id) {
    const p = _allProjects.find(x => x.id === id);
    if (p) {
      document.getElementById('projectPepInput').value         = p.pep_wbs;
      document.getElementById('projectNameInput').value        = p.name    || '';
      document.getElementById('projectClientInput').value      = p.client  || '';
      document.getElementById('projectManagerInput').value     = p.manager || '';
      document.getElementById('projectBudgetInput').value      = p.budget_hours ?? '';
      document.getElementById('projectBudgetCostInput').value  = p.budget_cost ?? '';
      document.getElementById('projectStatusInput').value      = p.status;
    }
  } else {
    ['projectPepInput','projectNameInput','projectClientInput','projectManagerInput','projectBudgetInput','projectBudgetCostInput']
      .forEach(fid => { document.getElementById(fid).value = ''; });
    document.getElementById('projectStatusInput').value = 'ativo';
  }
  document.getElementById('projectModal').hidden = false;
}

function closeProjectModal() { document.getElementById('projectModal').hidden = true; }

document.getElementById('projectSaveBtn').addEventListener('click', async () => {
  const pep = document.getElementById('projectPepInput').value.trim();
  if (!pep) { document.getElementById('projectError').textContent = 'Código PEP é obrigatório.'; return; }
  const budget     = document.getElementById('projectBudgetInput').value;
  const budgetCost = document.getElementById('projectBudgetCostInput').value;
  const body = {
    pep_wbs:      pep,
    name:         document.getElementById('projectNameInput').value.trim()    || null,
    client:       document.getElementById('projectClientInput').value.trim()  || null,
    manager:      document.getElementById('projectManagerInput').value.trim() || null,
    budget_hours: budget     !== '' ? parseFloat(budget)     : null,
    budget_cost:  budgetCost !== '' ? parseFloat(budgetCost) : null,
    status:       document.getElementById('projectStatusInput').value,
  };
  try {
    if (_projectEditId) {
      await apiFetchJSON(`/api/projects/${_projectEditId}`, 'PUT', body);
    } else {
      await apiFetchJSON('/api/projects', 'POST', body);
    }
    closeProjectModal();
    loadProjectsTable();
  } catch (e) {
    document.getElementById('projectError').textContent = e.message;
  }
});

document.getElementById('projectCancelBtn').addEventListener('click', closeProjectModal);
document.getElementById('projectModalClose').addEventListener('click', closeProjectModal);
document.getElementById('newProjectBtn').addEventListener('click', () => openProjectModal());

document.getElementById('projectSearch').addEventListener('input', e => {
  const q = e.target.value.toLowerCase();
  _renderProjectsTable(q ? _allProjects.filter(p =>
    (p.pep_wbs || '').toLowerCase().includes(q) ||
    (p.name    || '').toLowerCase().includes(q) ||
    (p.client  || '').toLowerCase().includes(q)
  ) : _allProjects);
});

async function deleteProject(id, pep) {
  if (!confirm(`Excluir o projeto "${pep}"?`)) return;
  try { await apiFetchJSON(`/api/projects/${id}`, 'DELETE'); loadProjectsTable(); }
  catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

document.getElementById('exportProjectsBtn').addEventListener('click', () => {
  if (!_allProjects.length) { notify('Nenhum projeto para exportar.', 'info'); return; }
  const header = 'pep_wbs,name,client,manager,budget_hours,budget_cost,status';
  const esc = v => (v == null ? '' : `"${String(v).replace(/"/g, '""')}"`);
  const rows = _allProjects.map(p =>
    `${esc(p.pep_wbs)},${esc(p.name)},${esc(p.client)},${esc(p.manager)},${p.budget_hours ?? ''},${p.budget_cost ?? ''},${p.status}`
  );
  const blob = new Blob(['﻿' + [header, ...rows].join('\n')], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement('a'), { href: url, download: 'projetos.csv' });
  a.click();
  URL.revokeObjectURL(url);
});

document.getElementById('importProjectsInput').addEventListener('change', async e => {
  const file = e.target.files[0];
  if (!file) return;
  const form = new FormData();
  form.append('file', file);
  try {
    const res = await fetch('/api/projects/import', { method: 'POST', headers: _authHeaders(), body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    const msg = `Importação concluída: ${data.created} criado(s), ${data.updated} atualizado(s)` +
      (data.errors.length ? `; ${data.errors.length} erro(s): ${data.errors.slice(0,3).join('; ')}` : '');
    notify(msg, data.errors.length ? 'error' : 'success');
    loadProjectsTable();
  } catch (err) { notify(`Erro na importação: ${err.message}`, 'error'); }
  e.target.value = '';
});

// ---------------------------------------------------------------------------
// Team / RateCard management
// ---------------------------------------------------------------------------
let _allSeniorityLevels = [];
let _allRateCards       = [];
let _allTeam            = [];
let _seniorityEditId    = null;
let _rateCardEditId     = null;
let _assignCollabId     = null;

async function loadTeamTab() {
  await Promise.all([loadSeniorityLevels(), loadRateCards(), loadGlobalConfig()]);
  await loadTeamTable();
}

async function loadSeniorityLevels() {
  try {
    _allSeniorityLevels = await apiFetch('/api/seniority-levels');
    const tbody = document.getElementById('seniorityBody');
    if (!_allSeniorityLevels.length) {
      tbody.innerHTML = `<tr><td colspan="2" style="text-align:center;color:#475569;padding:1.5rem">${_t('no_seniority')}</td></tr>`;
      return;
    }
    tbody.innerHTML = _allSeniorityLevels.map(l => `
      <tr>
        <td>${escHtml(l.name)}</td>
        <td><div class="actions">
          <button class="btn btn-secondary btn-sm" onclick="openSeniorityModal(${l.id})">${_t('btn.edit')}</button>
          <button class="btn btn-danger btn-sm" onclick="deleteSeniorityLevel(${l.id}, ${escHtml(JSON.stringify(l.name))})">${_t('btn.delete')}</button>
        </div></td>
      </tr>`).join('');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

async function loadRateCards() {
  try {
    _allRateCards = await apiFetch('/api/rate-cards');
    const tbody = document.getElementById('rateCardBody');
    if (!_allRateCards.length) {
      tbody.innerHTML = `<tr><td colspan="5" style="text-align:center;color:#475569;padding:1.5rem">${_t('no_rates')}</td></tr>`;
      return;
    }
    tbody.innerHTML = _allRateCards.map(c => `
      <tr>
        <td>${escHtml(c.seniority_level_name)}</td>
        <td style="text-align:right">R$ ${Number(c.hourly_rate).toLocaleString('pt-BR', {minimumFractionDigits:2})}</td>
        <td>${c.valid_from}</td>
        <td>${c.valid_to ?? '—'}</td>
        <td><div class="actions">
          <button class="btn btn-secondary btn-sm" onclick="openRateCardModal(${c.id})">${_t('btn.edit')}</button>
          <button class="btn btn-danger btn-sm" onclick="deleteRateCard(${c.id})">${_t('btn.delete')}</button>
        </div></td>
      </tr>`).join('');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

async function loadTeamTable() {
  try {
    _allTeam = await apiFetch('/api/team');
    const tbody = document.getElementById('teamBody');
    if (!_allTeam.length) {
      tbody.innerHTML = `<tr><td colspan="4" style="text-align:center;color:#475569;padding:1.5rem">${_t('no_team')}</td></tr>`;
    } else {
      tbody.innerHTML = _allTeam.map(m => `
        <tr>
          <td>${escHtml(m.name)}</td>
          <td>${m.seniority_level_name ? escHtml(m.seniority_level_name) : '<span style="color:#475569">—</span>'}</td>
          <td style="text-align:right">${m.current_hourly_rate != null ? 'R$ ' + Number(m.current_hourly_rate).toLocaleString('pt-BR', {minimumFractionDigits:2}) : '—'}</td>
          <td><button class="btn btn-secondary btn-sm" onclick="openAssignSeniority(${m.id}, ${escHtml(JSON.stringify(m.name))}, ${m.seniority_level_id ?? 'null'})">${_t('btn.assign')}</button></td>
        </tr>`).join('');
    }
    // Populate bulk seniority select
    const bulkSel = document.getElementById('bulkSenioritySelect');
    bulkSel.innerHTML = '<option value="">— Sem senioridade —</option>' +
      _allSeniorityLevels.map(l => `<option value="${l.id}">${escHtml(l.name)}</option>`).join('');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// Seniority level modal
function openSeniorityModal(id = null) {
  _seniorityEditId = id;
  document.getElementById('seniorityModalTitle').textContent = id ? 'Editar Nível' : 'Novo Nível de Senioridade';
  document.getElementById('seniorityError').textContent = '';
  const l = id ? _allSeniorityLevels.find(x => x.id === id) : null;
  document.getElementById('seniorityNameInput').value = l ? l.name : '';
  document.getElementById('seniorityModal').hidden = false;
}
function closeSeniorityModal() { document.getElementById('seniorityModal').hidden = true; }

document.getElementById('senioritySaveBtn').addEventListener('click', async () => {
  const name = document.getElementById('seniorityNameInput').value.trim();
  if (!name) { document.getElementById('seniorityError').textContent = 'Nome é obrigatório.'; return; }
  try {
    if (_seniorityEditId) {
      await apiFetchJSON(`/api/seniority-levels/${_seniorityEditId}`, 'PUT', { name });
    } else {
      await apiFetchJSON('/api/seniority-levels', 'POST', { name });
    }
    closeSeniorityModal();
    await loadSeniorityLevels();
  } catch (e) { document.getElementById('seniorityError').textContent = e.message; }
});
document.getElementById('seniorityCancelBtn').addEventListener('click', closeSeniorityModal);
document.getElementById('seniorityModalClose').addEventListener('click', closeSeniorityModal);
document.getElementById('newSeniorityBtn').addEventListener('click', () => openSeniorityModal());

async function deleteSeniorityLevel(id, name) {
  if (!confirm(`Excluir o nível "${name}"?`)) return;
  try { await apiFetchJSON(`/api/seniority-levels/${id}`, 'DELETE'); await loadSeniorityLevels(); }
  catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// Rate card modal
function _populateLevelSelect(selectId, selectedId = null) {
  const sel = document.getElementById(selectId);
  sel.innerHTML = _allSeniorityLevels.map(l =>
    `<option value="${l.id}" ${l.id === selectedId ? 'selected' : ''}>${escHtml(l.name)}</option>`
  ).join('');
}

function openRateCardModal(id = null) {
  _rateCardEditId = id;
  document.getElementById('rateCardModalTitle').textContent = id ? 'Editar Taxa' : 'Nova Taxa';
  document.getElementById('rateCardError').textContent = '';
  const c = id ? _allRateCards.find(x => x.id === id) : null;
  _populateLevelSelect('rateCardLevelInput', c?.seniority_level_id ?? null);
  document.getElementById('rateCardRateInput').value = c ? c.hourly_rate : '';
  document.getElementById('rateCardFromInput').value = c ? c.valid_from : '';
  document.getElementById('rateCardToInput').value   = c ? (c.valid_to ?? '') : '';
  document.getElementById('rateCardModal').hidden = false;
}
function closeRateCardModal() { document.getElementById('rateCardModal').hidden = true; }

document.getElementById('rateCardSaveBtn').addEventListener('click', async () => {
  const rate = document.getElementById('rateCardRateInput').value;
  const from = document.getElementById('rateCardFromInput').value;
  if (!rate || !from) { document.getElementById('rateCardError').textContent = 'Preencha os campos obrigatórios.'; return; }
  const to = document.getElementById('rateCardToInput').value;
  const body = {
    seniority_level_id: parseInt(document.getElementById('rateCardLevelInput').value),
    hourly_rate: parseFloat(rate),
    valid_from: from,
    valid_to: to || null,
  };
  try {
    if (_rateCardEditId) {
      await apiFetchJSON(`/api/rate-cards/${_rateCardEditId}`, 'PUT', body);
    } else {
      await apiFetchJSON('/api/rate-cards', 'POST', body);
    }
    closeRateCardModal();
    await loadRateCards();
    await loadTeamTable();
  } catch (e) { document.getElementById('rateCardError').textContent = e.message; }
});
document.getElementById('rateCardCancelBtn').addEventListener('click', closeRateCardModal);
document.getElementById('rateCardModalClose').addEventListener('click', closeRateCardModal);
document.getElementById('newRateCardBtn').addEventListener('click', () => openRateCardModal());

async function deleteRateCard(id) {
  if (!confirm('Excluir esta taxa?')) return;
  try { await apiFetchJSON(`/api/rate-cards/${id}`, 'DELETE'); await loadRateCards(); await loadTeamTable(); }
  catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// Assign seniority modal
function openAssignSeniority(collabId, name, currentLevelId) {
  _assignCollabId = collabId;
  document.getElementById('assignSeniorityTitle').textContent = `Senioridade — ${name}`;
  document.getElementById('assignSeniorityError').textContent = '';
  const sel = document.getElementById('assignSenioritySelect');
  sel.innerHTML = '<option value="">— Sem senioridade —</option>' +
    _allSeniorityLevels.map(l =>
      `<option value="${l.id}" ${l.id === currentLevelId ? 'selected' : ''}>${escHtml(l.name)}</option>`
    ).join('');
  document.getElementById('assignSeniorityModal').hidden = false;
}
function closeAssignSeniority() { document.getElementById('assignSeniorityModal').hidden = true; }

document.getElementById('assignSenioritySaveBtn').addEventListener('click', async () => {
  const val = document.getElementById('assignSenioritySelect').value;
  const body = { seniority_level_id: val ? parseInt(val) : null };
  try {
    await apiFetchJSON(`/api/team/${_assignCollabId}/seniority`, 'PUT', body);
    closeAssignSeniority();
    await loadTeamTable();
  } catch (e) { document.getElementById('assignSeniorityError').textContent = e.message; }
});
document.getElementById('assignSeniorityCancelBtn').addEventListener('click', closeAssignSeniority);
document.getElementById('assignSeniorityClose').addEventListener('click', closeAssignSeniority);

// Bulk assign seniority
document.getElementById('bulkSeniorityBtn').addEventListener('click', async () => {
  const val = document.getElementById('bulkSenioritySelect').value;
  const label = val
    ? _allSeniorityLevels.find(l => l.id === parseInt(val))?.name
    : 'Sem senioridade';
  if (!confirm(`Atribuir "${label}" a TODOS os colaboradores?`)) return;
  try {
    const body = { seniority_level_id: val ? parseInt(val) : null };
    await apiFetchJSON('/api/team/bulk-seniority', 'PUT', body);
    await loadTeamTable();
    notify(`Senioridade "${label}" atribuída a todos.`, 'success');
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
});

// Global config (multipliers)
async function loadGlobalConfig() {
  try {
    const cfg = await apiFetch('/api/config');
    document.getElementById('extraMultiplierInput').value   = cfg.extra_hours_multiplier;
    document.getElementById('standbyMultiplierInput').value = cfg.standby_hours_multiplier;
  } catch (e) { /* non-critical, leave placeholders */ }
}

document.getElementById('saveConfigBtn').addEventListener('click', async () => {
  const em  = parseFloat(document.getElementById('extraMultiplierInput').value);
  const sm  = parseFloat(document.getElementById('standbyMultiplierInput').value);
  const msg = document.getElementById('configMsg');
  if (isNaN(em) || isNaN(sm) || em <= 0 || sm <= 0) {
    msg.style.color = '#ef4444';
    msg.textContent = 'Os multiplicadores devem ser números positivos.';
    return;
  }
  try {
    await apiFetchJSON('/api/config', 'PUT', {
      extra_hours_multiplier: em,
      standby_hours_multiplier: sm,
    });
    msg.style.color = '#22c55e';
    msg.textContent = 'Fatores salvos com sucesso.';
    setTimeout(() => { msg.textContent = ''; }, 3000);
  } catch (e) {
    msg.style.color = '#ef4444';
    msg.textContent = e.message;
  }
});

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------
// ---------------------------------------------------------------------------
// Auth helpers
// ---------------------------------------------------------------------------
function _authHeaders(extra = {}) {
  const token = sessionStorage.getItem('access_token');
  return token ? { Authorization: `Bearer ${token}`, ...extra } : extra;
}

function _getTokenPayload() {
  const token = sessionStorage.getItem('access_token');
  if (!token) return null;
  try { return JSON.parse(atob(token.split('.')[1])); } catch (_) { return null; }
}

function _isAdmin() {
  const p = _getTokenPayload();
  return p ? p.role === 'admin' : false;
}

function _handleUnauthorized() {
  sessionStorage.removeItem('access_token');
  document.getElementById('appShell').hidden = true;
  document.getElementById('loginOverlay').removeAttribute('hidden');
}

async function apiFetch(url) {
  const res = await fetch(url, { headers: _authHeaders() });
  if (res.status === 401) { _handleUnauthorized(); return; }
  if (!res.ok) {
    const j = await res.json().catch(() => ({}));
    throw new Error(j.detail ?? res.statusText);
  }
  return res.json();
}

async function apiFetchJSON(url, method, body) {
  const res = await fetch(url, {
    method,
    headers: _authHeaders({ 'Content-Type': 'application/json' }),
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (res.status === 401) { _handleUnauthorized(); return; }
  if (!res.ok) {
    const j = await res.json().catch(() => ({}));
    throw new Error(j.detail ?? res.statusText);
  }
  return res.status === 204 ? null : res.json();
}

function notify(msg, type = 'info') {
  const el = document.getElementById('notification');
  el.textContent = msg; el.className = type; el.style.display = 'block';
  setTimeout(() => { el.style.display = 'none'; }, 6000);
}

function fmt(h) { return h >= 1000 ? (h / 1000).toFixed(1) + 'k' : Number(h).toFixed(1); }

function escHtml(s) {
  return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;').replace(/'/g,'&#39;');
}

// ---------------------------------------------------------------------------
// Login form
// ---------------------------------------------------------------------------
document.getElementById('loginForm').addEventListener('submit', async e => {
  e.preventDefault();
  const username = document.getElementById('loginUsername').value.trim();
  const password = document.getElementById('loginPassword').value;
  const errEl    = document.getElementById('loginError');
  errEl.textContent = '';
  try {
    const res = await fetch('/api/token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username, password }),
    });
    if (!res.ok) {
      const j = await res.json().catch(() => ({}));
      errEl.textContent = j.detail ?? 'Credenciais inválidas.';
      return;
    }
    const { access_token } = await res.json();
    sessionStorage.setItem('access_token', access_token);
    document.getElementById('loginOverlay').setAttribute('hidden', '');
    document.getElementById('appShell').removeAttribute('hidden');
    _bootApp();
  } catch (_) {
    errEl.textContent = 'Erro de conexão. Tente novamente.';
  }
});

document.getElementById('logoutBtn').addEventListener('click', () => {
  sessionStorage.removeItem('access_token');
  document.getElementById('appShell').hidden = true;
  document.getElementById('loginOverlay').removeAttribute('hidden');
});

// ---------------------------------------------------------------------------
// Users management (Admin tab)
// ---------------------------------------------------------------------------
let _allUsers = [];

async function loadUsersTable() {
  try {
    _allUsers = await apiFetch('/api/users');
    _renderUsersTable(_allUsers);
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _renderUsersTable(users) {
  const tbody = document.getElementById('usersBody');
  if (!users.length) {
    tbody.innerHTML = `<tr><td colspan="3" style="text-align:center;color:#475569;padding:2rem">${_t('no_users')}</td></tr>`;
    return;
  }
  const payload = _getTokenPayload();
  const selfId  = payload ? payload.sub : null;
  tbody.innerHTML = users.map(u => `
    <tr>
      <td>${escHtml(u.username)}</td>
      <td><span class="badge-status ${u.role === 'admin' ? 'ativo' : 'quarantine'}">${u.role === 'admin' ? _t('lbl.admin') : _t('lbl.user')}</span></td>
      <td><div class="actions">
        <button class="btn btn-secondary btn-sm" onclick="openPwdModal(${u.id})">${_t('btn.pwd')}</button>
        ${u.username !== selfId ? `<button class="btn btn-danger btn-sm" onclick="deleteUser(${u.id}, ${escHtml(JSON.stringify(u.username))})">${_t('btn.delete')}</button>` : ''}
      </div></td>
    </tr>`).join('');
}

document.getElementById('newUserBtn').addEventListener('click', () => {
  document.getElementById('userUsernameInput').value = '';
  document.getElementById('userPasswordInput').value = '';
  document.getElementById('userRoleSelect').value    = 'user';
  document.getElementById('userError').textContent   = '';
  document.getElementById('userModal').hidden = false;
});

document.getElementById('userModalClose').addEventListener('click',  () => { document.getElementById('userModal').hidden = true; });
document.getElementById('userCancelBtn').addEventListener('click',   () => { document.getElementById('userModal').hidden = true; });

document.getElementById('userSaveBtn').addEventListener('click', async () => {
  const username = document.getElementById('userUsernameInput').value.trim();
  const password = document.getElementById('userPasswordInput').value;
  const role     = document.getElementById('userRoleSelect').value;
  const errEl    = document.getElementById('userError');
  errEl.textContent = '';
  if (!username || !password) { errEl.textContent = 'Preencha todos os campos obrigatórios.'; return; }
  try {
    await apiFetchJSON('/api/users', 'POST', { username, password, role });
    document.getElementById('userModal').hidden = true;
    loadUsersTable();
    notify(`Usuário "${escHtml(username)}" criado com sucesso.`, 'success');
  } catch (e) { errEl.textContent = e.message; }
});

function openPwdModal(userId) {
  document.getElementById('pwdTargetId').value  = userId;
  document.getElementById('pwdNewInput').value  = '';
  document.getElementById('pwdError').textContent = '';
  document.getElementById('pwdModal').hidden = false;
}

document.getElementById('pwdModalClose').addEventListener('click', () => { document.getElementById('pwdModal').hidden = true; });
document.getElementById('pwdCancelBtn').addEventListener('click',  () => { document.getElementById('pwdModal').hidden = true; });

document.getElementById('pwdSaveBtn').addEventListener('click', async () => {
  const userId      = document.getElementById('pwdTargetId').value;
  const new_password = document.getElementById('pwdNewInput').value;
  const errEl       = document.getElementById('pwdError');
  errEl.textContent = '';
  if (!new_password) { errEl.textContent = 'Informe a nova senha.'; return; }
  try {
    await apiFetchJSON(`/api/users/${userId}/password`, 'PATCH', { new_password });
    document.getElementById('pwdModal').hidden = true;
    notify('Senha alterada com sucesso.', 'success');
  } catch (e) { errEl.textContent = e.message; }
});

async function deleteUser(id, username) {
  if (!confirm(`Excluir o usuário "${username}"?`)) return;
  try {
    await apiFetchJSON(`/api/users/${id}`, 'DELETE');
    loadUsersTable();
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

// ---------------------------------------------------------------------------
// Audit Log (Admin tab)
// ---------------------------------------------------------------------------

async function loadAuditLog() {
  const entity = document.getElementById('auditEntityFilter').value;
  const action = document.getElementById('auditActionFilter').value;
  const params = new URLSearchParams({ limit: 200 });
  if (entity) params.set('entity', entity);
  if (action) params.set('action', action);
  try {
    const rows = await apiFetch(`/api/audit-log?${params}`);
    _renderAuditLog(rows);
  } catch (e) { notify(`Erro: ${e.message}`, 'error'); }
}

function _renderAuditLog(rows) {
  const tbody = document.getElementById('auditBody');
  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="6" style="text-align:center;color:#475569;padding:2rem">${_t('no_audit')}</td></tr>`;
    return;
  }
  tbody.innerHTML = rows.map(r => {
    const when = new Date(r.timestamp).toLocaleString(_locale === 'pt' ? 'pt-BR' : 'en-US', { dateStyle: 'short', timeStyle: 'short' });
    let detail = '';
    if (r.detail) {
      try {
        const obj = JSON.parse(r.detail);
        detail = Object.entries(obj).map(([k, v]) => `${k}: ${v}`).join(', ');
      } catch { detail = r.detail; }
    }
    return `<tr>
      <td style="white-space:nowrap">${escHtml(when)}</td>
      <td>${escHtml(r.username || '—')}</td>
      <td><code>${escHtml(r.action)}</code></td>
      <td>${escHtml(r.entity)}</td>
      <td style="text-align:right">${r.entity_id ?? '—'}</td>
      <td style="font-size:.78rem;color:#94a3b8;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escHtml(detail)}">${escHtml(detail)}</td>
    </tr>`;
  }).join('');
}

document.getElementById('auditRefreshBtn').addEventListener('click', loadAuditLog);
document.getElementById('auditEntityFilter').addEventListener('change', loadAuditLog);
document.getElementById('auditActionFilter').addEventListener('change', loadAuditLog);

// ---------------------------------------------------------------------------
// Boot
// ---------------------------------------------------------------------------
function _bootApp() {
  if (_isAdmin()) document.getElementById('adminTabBtn').removeAttribute('hidden');
  document.getElementById('langToggleBtn').textContent = _t('btn.lang');
  _applyI18n();
  loadDashboardCycles();
  _renderActiveTab();
}

if (sessionStorage.getItem('access_token')) {
  document.getElementById('loginOverlay').setAttribute('hidden', '');
  document.getElementById('appShell').removeAttribute('hidden');
  _bootApp();
}
