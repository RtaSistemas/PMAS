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
  showTotal     = true,
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
  const totals     = slice.map((_, i) =>
    +(normals[i] + extras[i] + standbys[i]).toFixed(2)
  );
  const maxTotal   = Math.max(...totals, 0);

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
      const bars  = params.filter(p => p.seriesName !== _t('stat.total'));
      let html    = `<b>${params[0].axisValue}</b><br/>`;
      let total   = 0;
      bars.forEach(p => {
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

  // ── 6. Total line series (optional) ─────────────────────────────────
  // Per-item data objects are used instead of callbacks so that each
  // symbol's color and size are resolved once, avoiding ECharts quirks
  // with itemStyle.color functions on line series.
  const totalLineData = totals.map(v => {
    const isPeak = v > 0 && v === maxTotal;
    return {
      value:      v,
      symbol:     v === 0 ? 'none' : 'circle',
      symbolSize: isPeak ? 10 : 6,
      itemStyle:  { color: isPeak ? _cssVar('--red') : _cssVar('--green') },
    };
  });

  const totalLineSeries = showTotal ? [{
    name:       _t('stat.total'),
    type:       'line',
    color:      _cssVar('--green'),
    legendIcon: 'circle',
    data:       totalLineData,
    lineStyle:  { width: 1, type: 'dashed' },
    label: {
      show:      !!stack,
      position:  isHoriz ? 'right' : 'top',
      fontSize:  10,
      color:     _cssVar('--green'),
      formatter: p => {
        const v = p.value ?? 0;
        if (v === 0) return '';
        return v === maxTotal
          ? `{peak|${v.toFixed(1)}h}`
          : `${v.toFixed(1)}h`;
      },
      rich: { peak: { color: _cssVar('--red'), fontSize: 10 } },
    },
    z: 10,
  }] : [];

  // ── 7. Legend ────────────────────────────────────────────────────────
  const legendData = [
    _t('ch.normal_h'),
    _t('ch.extra_h'),
    _t('ch.standby_h'),
    ...(showTotal ? [_t('stat.total')] : []),
  ];

  // ── 8. Grid ──────────────────────────────────────────────────────────
  const grid = {
    top:          44,
    right:        showTotal && isHoriz  ? '8%'  :
                  showTotal && !isHoriz ? '6%'  : '3%',
    bottom:       isHoriz ? 28 : 56,
    left:         '2%',
    containLabel: true,
  };

  // ── 9. Final assembly ────────────────────────────────────────────────
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

    series: [...barSeries, ...totalLineSeries],
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
