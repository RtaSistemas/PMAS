/* PMAS — Forecast Tab Chart Builders
 * Depends on globals defined in app.js:
 *   _cssVar, _t, escHtml, _toolbox, _getPalette, _fmtCost,
 *   _budgetWarning, _budgetCritical
 * Must be loaded AFTER app.js in index.html.
 */

// ---------------------------------------------------------------------------
// _buildForecastOption — S-curve: realized vs projected vs PV vs budget
// ---------------------------------------------------------------------------
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
  const lastHistoryCat = historyCats.at(-1) ?? null;

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

  const _fpal = _getPalette();
  const _fC0  = _fpal[0] || '#0ea5e9';
  const series = [
    {
      name: _t('forecast.realized'),
      type: 'line', yAxisIndex: 0,
      data: realizedData,
      smooth: false, symbol: 'circle', symbolSize: 6,
      lineStyle: { color: _fC0, width: 2.5 },
      itemStyle: { color: _fC0 },
      areaStyle: { color: _fC0 + '1a' },
      emphasis:  { focus: 'series' },
      connectNulls: false,
      ...(lastHistoryCat ? {
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { color: _cssVar('--border'), type: 'solid', width: 1 },
          data: [{ xAxis: lastHistoryCat,
            label: { show: true, formatter: _t('forecast.now_marker'),
              color: _cssVar('--text-3'), fontSize: 9, position: 'insideEndTop' } }],
        },
      } : {}),
    },
    {
      name: _t('forecast.projection'),
      type: 'line', yAxisIndex: 0,
      data: projectionData,
      smooth: false, symbol: 'circle', symbolSize: 5,
      lineStyle: { color: _cssVar('--text-3'), width: 2, type: 'dashed' },
      itemStyle: { color: _cssVar('--text-3') },
      emphasis:  { focus: 'series' },
      connectNulls: false,
    },
  ];
  if (pvData) {
    const _fC3 = _fpal[3] || '#a78bfa';
    series.push({
      name: _t('forecast.pv_line'),
      type: 'line', yAxisIndex: 0,
      data: pvData,
      symbol: 'none',
      lineStyle: { color: _fC3, width: 2, type: 'dotted' },
      itemStyle: { color: _fC3 },
      emphasis:  { focus: 'series' },
      connectNulls: true,
    });
  }
  if (budgetData) {
    series.push({
      name: _t('forecast.budget_line'),
      type: 'line', yAxisIndex: 0,
      data: budgetData,
      symbol: 'none',
      lineStyle: { color: _cssVar('--amber'), width: 1.5, type: 'dashed' },
      itemStyle: { color: _cssVar('--amber') },
      emphasis:  { focus: 'series' },
    });
  }

  const legendData = [_t('forecast.realized'), _t('forecast.projection')];
  if (pvData) legendData.push(_t('forecast.pv_line'));
  if (budgetData) legendData.push(_t('forecast.budget_line'));

  return {
    ..._chartDefaults(),
    legend: {
      data: legendData, top: 8, left: 'center',
      textStyle: { color: _cssVar('--text'), fontSize: 12 },
      itemGap: 24, itemWidth: 18, itemHeight: 10,
    },
    grid: { top: 44, right: '4%', bottom: 56, left: '2%', containLabel: true },
    tooltip: {
      trigger: 'axis',
      ..._chartDefaults().tooltip,
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
      dataZoom: { title: { zoom: _t('toolbox.zoom'), back: _t('toolbox.zoom_back') } },
    }, 'PMAS-IDP'),
    xAxis: {
      type: 'category', data: allCats,
      axisLabel: { color: _cssVar('--text-3'), rotate: allCats.length > 8 ? 30 : 0, fontSize: 11 },
      axisTick: { alignWithLabel: true },
    },
    yAxis: {
      type: 'value', name: _t('ch.hours'),
      nameTextStyle: { color: _cssVar('--text-3'), fontSize: 11 },
      axisLabel: { color: _cssVar('--text-3'), fontSize: 11, formatter: v => `${v}h` },
      splitLine: { lineStyle: { color: _cssVar('--border') } },
    },
    series,
  };
}

// ---------------------------------------------------------------------------
// _buildBurnUpOption — EVM burn-up: PV / EV / AC / EAC lines
// ---------------------------------------------------------------------------
function _buildBurnUpOption(fc) {
  const history = fc.history || [];
  const cats = history.map(h => h.cycle_name);
  const pvData = history.map(h => h.cumulative_planned_cost ?? null);
  const evData = history.map(h => h.cumulative_ev_cost      ?? null);
  const acData = history.map(h => h.cumulative_cost         ?? null);

  const _fmtR = v => v == null ? '' : `R$ ${(+v).toLocaleString('pt-BR', {minimumFractionDigits:2, maximumFractionDigits:2})}`;

  const eacColor = _cssVar('--amber') || '#f59e0b';
  const legendData = [_t('burnup.pv'), _t('burnup.ev'), _t('burnup.ac')];
  if (fc.eac != null) legendData.push(_t('burnup.eac'));

  const series = [
    {
      name: _t('burnup.pv'),
      type: 'line', data: pvData,
      symbol: 'none', connectNulls: true,
      lineStyle: { color: '#94a3b8', width: 2, type: 'dashed' },
      itemStyle: { color: '#94a3b8' },
      emphasis:  { focus: 'series' },
    },
    {
      name: _t('burnup.ev'),
      type: 'line', data: evData,
      symbol: 'circle', symbolSize: 5, connectNulls: false,
      lineStyle: { color: _cssVar('--green') || '#22c55e', width: 2.5 },
      itemStyle: { color: _cssVar('--green') || '#22c55e' },
      areaStyle: { color: (_cssVar('--green') || '#22c55e') + '18' },
      emphasis:  { focus: 'series' },
    },
    {
      name: _t('burnup.ac'),
      type: 'line', data: acData,
      symbol: 'circle', symbolSize: 5, connectNulls: false,
      lineStyle: { color: _cssVar('--red') || '#ef4444', width: 2.5 },
      itemStyle: { color: _cssVar('--red') || '#ef4444' },
      emphasis:  { focus: 'series' },
    },
  ];
  if (fc.eac != null) {
    series.push({
      name: _t('burnup.eac'),
      type: 'line',
      data: cats.map(() => fc.eac),
      symbol: 'none',
      lineStyle: { color: eacColor, width: 1.5, type: 'dotted' },
      itemStyle: { color: eacColor },
      emphasis:  { focus: 'series' },
      tooltip: { formatter: () => `EAC: ${_fmtR(fc.eac)}` },
    });
  }

  return {
    ..._chartDefaults(),
    legend: {
      data: legendData, top: 8, left: 'center',
      textStyle: { color: _cssVar('--text'), fontSize: 12 },
      itemGap: 24, itemWidth: 18, itemHeight: 10,
    },
    grid: { top: 44, right: '4%', bottom: 56, left: '2%', containLabel: true },
    tooltip: {
      trigger: 'axis',
      ..._chartDefaults().tooltip,
      formatter: params => {
        let html = `<b>${escHtml(params[0].axisValue)}</b><br>`;
        params.forEach(p => {
          if (p.value == null) return;
          html += `${p.marker} ${p.seriesName}: <b>${_fmtR(p.value)}</b><br>`;
        });
        return html;
      },
    },
    toolbox: _toolbox({
      dataZoom: { title: { zoom: _t('toolbox.zoom'), back: _t('toolbox.zoom_back') } },
    }, 'PMAS-BurnUp'),
    xAxis: {
      type: 'category', data: cats,
      axisLabel: { color: _cssVar('--text-3'), rotate: cats.length > 8 ? 30 : 0, fontSize: 11 },
      axisTick: { alignWithLabel: true },
    },
    yAxis: {
      type: 'value', name: 'R$',
      nameTextStyle: { color: _cssVar('--text-3'), fontSize: 11 },
      axisLabel: {
        color: _cssVar('--text-3'), fontSize: 11,
        formatter: v => `R$${(v/1000).toFixed(0)}k`,
      },
      splitLine: { lineStyle: { color: _cssVar('--border') } },
    },
    series,
  };
}

// ---------------------------------------------------------------------------
// _buildPepCpiOption — per-PEP CPI/SPI trend lines
// ---------------------------------------------------------------------------
function _buildPepCpiOption(peps, allCycleNames, spiMapByPep = {}) {
  const pal = _getPalette();
  const cpiSeries = peps.map(([wbs, { desc, points }], i) => {
    const dataMap = Object.fromEntries(points.map(p => [p.cycleName, p.cpi]));
    const data    = allCycleNames.map(n => dataMap[n] ?? null);
    const color   = pal[i % pal.length];
    return {
      name: `${wbs} — ${desc} ${_t('pepcpi.cpi_suffix')}`,
      type: 'line',
      data,
      connectNulls: false,
      smooth: false,
      symbol: 'circle', symbolSize: 7,
      lineStyle: { color, width: 2.5 },
      itemStyle: { color },
      emphasis: { focus: 'series' },
    };
  });

  // SPI (IDP) series — dashed lines, same color as their CPI counterpart
  const spiSeries = peps
    .map(([wbs, { desc }], i) => {
      const spiMap = spiMapByPep[wbs];
      if (!spiMap || !Object.keys(spiMap).length) return null;
      const data  = allCycleNames.map(n => spiMap[n] ?? null);
      const color = pal[i % pal.length];
      return {
        name: `${wbs} — ${desc} ${_t('pepcpi.spi_suffix')}`,
        type: 'line',
        data,
        connectNulls: false,
        smooth: false,
        symbol: 'diamond', symbolSize: 6,
        lineStyle: { color, width: 1.8, type: 'dashed' },
        itemStyle: { color },
        emphasis: { focus: 'series' },
      };
    })
    .filter(Boolean);

  const series = [...cpiSeries, ...spiSeries];

  return {
    ..._chartDefaults(),
    toolbox: _toolbox({}, 'PMAS-CPI-PEP'),
    title: {
      text: _t('pepcpi.title'),
      textStyle: { color: _cssVar('--text'), fontSize: 14, fontWeight: 600 },
      left: 'center', top: 8,
    },
    tooltip: {
      trigger: 'axis',
      ..._chartDefaults().tooltip,
      formatter: params => {
        const header = `<b>${escHtml(params[0]?.axisValue)}</b><br/>`;
        const lines  = params
          .filter(p => p.value != null)
          .map(p => {
            const val   = p.value;
            const isSpi = p.seriesName.endsWith(_t('pepcpi.spi_suffix'));
            const color = val >= _budgetCritical ? _cssVar('--primary') : val >= _budgetWarning ? _cssVar('--amber') : _cssVar('--red');
            const shape = isSpi
              ? `<span style="display:inline-block;width:10px;height:10px;background:${p.color};transform:rotate(45deg);margin-right:4px"></span>`
              : `<span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${p.color};margin-right:4px"></span>`;
            return `${shape}${escHtml(p.seriesName)}: <b style="color:${color}">${val.toFixed(2)}</b>`;
          })
          .join('<br/>');
        return header + lines;
      },
    },
    legend: {
      bottom: 0,
      textStyle: { color: _cssVar('--text-3'), fontSize: 10 },
      itemWidth: 14, itemHeight: 3,
    },
    grid: { top: 48, bottom: 64, left: 48, right: 16, containLabel: true },
    xAxis: {
      type: 'category',
      data: allCycleNames,
      axisLabel: { color: _cssVar('--text-3'), fontSize: 10, rotate: allCycleNames.length > 6 ? 30 : 0 },
      axisLine:  { lineStyle: { color: _cssVar('--border') } },
      splitLine: { show: false },
    },
    yAxis: {
      name: _t('pepcpi.yaxis'),
      nameTextStyle: { color: _cssVar('--text-3'), fontSize: 11 },
      axisLabel: { color: _cssVar('--text-3'), formatter: v => v.toFixed(2) },
      axisLine:  { lineStyle: { color: _cssVar('--border') } },
      splitLine: { lineStyle: { color: _cssVar('--surface') } },
      min: v => Math.max(0, +(v.min - 0.15).toFixed(1)),
      max: v => +(v.max + 0.15).toFixed(1),
      markLine: {
        silent: true,
        symbol: 'none',
        lineStyle: { color: _cssVar('--text-3'), type: 'dashed', width: 1.5 },
        data: [{ yAxis: 1.0, label: { formatter: _t('pepcpi.ref_line'), color: _cssVar('--text-3'), fontSize: 10 } }],
      },
    },
    series: series.map((s, i) => i > 0 ? s : {
      ...s,
      markArea: {
        silent: true,
        data: [
          [{ yAxis: 0,   itemStyle: { color: (_cssVar('--red')   || '#ef4444') + '18' },
             label: { show: true, position: 'insideTopLeft', formatter: _t('cpi.zone_critical'),
               color: _cssVar('--red')   || '#ef4444', fontSize: 9 } },
           { yAxis: 0.9 }],
          [{ yAxis: 0.9, itemStyle: { color: (_cssVar('--amber') || '#f59e0b') + '14' },
             label: { show: true, position: 'insideTopLeft', formatter: _t('cpi.zone_warning'),
               color: _cssVar('--amber') || '#f59e0b', fontSize: 9 } },
           { yAxis: 1.0 }],
        ],
      },
    }),
  };
}
