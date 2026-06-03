/* PMAS — Effort Tab Chart Builders
 * Depends on globals defined in app.js:
 *   _cssVar, _t, _toolbox, _getPalette
 * Must be loaded AFTER app.js in index.html.
 */

// ---------------------------------------------------------------------------
// calcHeight — dynamic chart height based on item count
// ---------------------------------------------------------------------------
function calcHeight(count) { return Math.max(360, Math.min(count, 40) * 40 + 100); }

// ---------------------------------------------------------------------------
// _buildEffortTitle — title string for the effort chart
// ---------------------------------------------------------------------------
function _buildEffortTitle(selectedCycleIds, selectedPepCodes) {
  if (!selectedCycleIds.length) return _t('chart.all_cycles');
  const first = (_allCycles || []).find(c => String(c.id) === String(selectedCycleIds[0]));
  const name = first ? first.name : `Ciclo #${selectedCycleIds[0]}`;
  let t = selectedCycleIds.length > 1
    ? `${name} (${_t('lbl.plus_cycles').replace('{n}', selectedCycleIds.length - 1)})`
    : name;
  if (selectedPepCodes?.length) t += `  |  PEP: ${selectedPepCodes.join(', ')}`;
  return t;
}

// ============================================================
// _buildHoursBarOption — Unified hours bar builder
// ============================================================
function _buildHoursBarOption({
  data          = [],
  categoryKey   = 'collaborator',
  orientation   = 'horizontal',   // 'horizontal' | 'vertical'
  stacked       = true,
  maxItems      = 40,
  toolboxName   = 'PMAS-Horas',
} = {}) {

  // ── 1. Data preparation ─────────────────────────────────────────────
  const slice      = data.length > maxItems ? data.slice(0, maxItems) : data;
  const truncated  = data.length > maxItems;
  const stack      = stacked ? 'total' : undefined;
  const isHoriz    = orientation === 'horizontal';

  const categories = slice.map(r => r[categoryKey]);
  const normals    = slice.map(r => +(r.normal_hours  ?? 0).toFixed(2));
  const extras     = slice.map(r => +(r.extra_hours   ?? 0).toFixed(2));
  const standbys   = slice.map(r => +(r.standby_hours ?? 0).toFixed(2));

  // ── 2. Category axis ────────────────────────────────────────────────
  const categoryAxis = {
    type: 'category',
    data: categories,
    axisTick: { show: false },
    axisLabel: {
      color:    _cssVar('--text-3'),
      fontSize: 10,
      rotate:   (!isHoriz && categories.length > 6) ? 30 : 0,
    },
  };

  // ── 3. Value axis ────────────────────────────────────────────────────
  const valueAxis = {
    type: 'value',
    name: 'h',
    nameTextStyle: { color: _cssVar('--text-3'), fontSize: 10 },
    axisLabel: {
      color:     _cssVar('--text-3'),
      fontSize:  10,
      formatter: v => `${v}h`,
    },
    splitLine: { lineStyle: { color: _cssVar('--border') } },
  };

  // ── 4. Unified tooltip ───────────────────────────────────────────────
  const tooltip = {
    trigger:     'axis',
    axisPointer: { type: 'shadow' },
    ..._chartDefaults().tooltip,
    formatter: params => {
      let html  = `<b>${params[0].axisValue}</b><br/>`;
      let total = 0;
      params.forEach(p => {
        if (p.value > 0) {
          html  += `${p.marker}${p.seriesName}: <b>${p.value.toFixed(1)}h</b><br/>`;
          total += p.value;
        }
      });
      html += `<hr style="border-color:${_cssVar('--border')};margin:4px 0"/>`;
      html += `Total: <b>${total.toFixed(1)}h</b>`;
      return html;
    },
  };

  // ── 5. Bar series ────────────────────────────────────────────────────
  const bgStyle = { showBackground: true, backgroundStyle: { color: 'rgba(255,255,255,0.05)' } };
  const barMaxWidth = isHoriz ? 32 : 48;

  const _barSerie = (name, data, color) => ({
    name,
    type: 'bar',
    ...bgStyle,
    stack,
    data,
    itemStyle:   { color },
    barMaxWidth,
    label: {
      show:      !!stack,
      position:  'inside',
      fontSize:  10,
      color:     _cssVar('--text'),
      formatter: p => p.value >= 10 ? `${p.value.toFixed(1)}h` : '',
    },
  });

  const _pal = _getPalette();
  const barSeries = [
    _barSerie(_t('ch.normal_h'),  normals,   _pal[0] || _cssVar('--primary')),
    _barSerie(_t('ch.extra_h'),   extras,    _pal[1] || _cssVar('--amber')),
    _barSerie(_t('ch.standby_h'), standbys,  _pal[2] || '#8b5cf6'),
  ];

  // ── 6. Legend ────────────────────────────────────────────────────────
  const legendData = [
    _t('ch.normal_h'),
    _t('ch.extra_h'),
    _t('ch.standby_h'),
  ];

  // ── 7. Grid ──────────────────────────────────────────────────────────
  const grid = {
    top:          44,
    right:        '3%',
    bottom:       isHoriz ? 28 : 56,
    left:         '2%',
    containLabel: true,
  };

  // ── 8. Final assembly ────────────────────────────────────────────────
  return {
    ..._chartDefaults(),

    title: truncated ? {
      subtext:      _t('chart.truncated').replace('{n}', maxItems),
      left:         'center',
      top:          4,
      subtextStyle: { color: _cssVar('--text-3'), fontSize: 10 },
    } : undefined,

    legend: {
      data:       legendData,
      top:        8,
      left:       'center',
      textStyle:  { color: _cssVar('--text'), fontSize: 11 },
      itemGap:    24,
      itemWidth:  14,
      itemHeight: 10,
    },

    toolbox: _toolbox({
      magicType: {
        type:  ['stack', 'tiled'],
        title: {
          stack: _t('toolbox.stack'),
          tiled: _t('toolbox.tiled'),
        },
      },
    }, toolboxName),

    grid,
    tooltip,

    xAxis: isHoriz ? valueAxis    : categoryAxis,
    yAxis: isHoriz ? categoryAxis : valueAxis,

    series: barSeries,
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
