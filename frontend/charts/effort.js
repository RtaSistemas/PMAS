/* PMAS — Effort Tab Chart Builders
 * Depends on globals defined in app.js:
 *   _cssVar, _t, _toolbox, _getPalette
 * Must be loaded AFTER app.js in index.html.
 */

// ---------------------------------------------------------------------------
// calcHeight — dynamic chart height based on item count
// ---------------------------------------------------------------------------
function calcHeight(count) { return Math.max(420, Math.min(count, 40) * 52 + 120); }

// ---------------------------------------------------------------------------
// _buildEffortTitle — title string for the effort chart
// ---------------------------------------------------------------------------
function _buildEffortTitle(selectedCycleIds, selectedPepCodes) {
  if (!selectedCycleIds.length) return 'Todos os ciclos';
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
// Replaces: _buildEffortOption, _buildTrendsOption bar block,
// and the inline tc.setOption({…}) in the timeline modal.
// ============================================================
function _buildHoursBarOption({
  data          = [],
  categoryKey   = 'collaborator',
  orientation   = 'horizontal',   // 'horizontal' | 'vertical'
  stacked       = true,
  showTotal     = true,
  richLabel     = false,
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

  // Quick lookup for richLabel (horizontal only)
  const byCategory = Object.fromEntries(slice.map(r => [r[categoryKey], r]));

  // ── 2. Category axis ────────────────────────────────────────────────
  const categoryAxis = {
    type: 'category',
    data: categories,
    axisTick: { show: false },
    axisLabel: richLabel && isHoriz
      ? {
          color:      _cssVar('--text'),
          fontSize:   10,
          lineHeight: 16,
          formatter: name => {
            const d  = byCategory[name];
            if (!d) return name;
            const t  = (d.normal_hours + d.extra_hours + d.standby_hours).toFixed(1);
            const nm = name.length > 30 ? name.slice(0, 29) + '…' : name;
            return (
              `{nm|${nm}}\n` +
              `{hr|N:${d.normal_hours.toFixed(1)}h  ` +
              `E:${d.extra_hours.toFixed(1)}h  ` +
              `S:${d.standby_hours.toFixed(1)}h  ∑${t}h}`
            );
          },
          rich: {
            nm: { color: _cssVar('--text'), fontSize: 11, lineHeight: 18 },
            hr: { color: _cssVar('--text-3'), fontSize: 9,  lineHeight: 14 },
          },
        }
      : {
          color:    _cssVar('--text-3'),
          fontSize: isHoriz ? 10 : 11,
          rotate:   (!isHoriz && categories.length > 6) ? 30 : 0,
        },
  };

  // ── 3. Value axis ────────────────────────────────────────────────────
  const valueAxis = {
    type: 'value',
    name: 'h',
    nameTextStyle: { color: _cssVar('--text-3'), fontSize: 11 },
    axisLabel: {
      color:     _cssVar('--text-3'),
      fontSize:  11,
      formatter: v => `${v}h`,
    },
    splitLine: { lineStyle: { color: _cssVar('--surface') } },
  };

  // ── 4. Unified tooltip ───────────────────────────────────────────────
  const tooltip = {
    trigger:     'axis',
    axisPointer: { type: 'shadow' },
    backgroundColor: _cssVar('--card'),
    borderColor:     _cssVar('--border'),
    textStyle:       { color: _cssVar('--text') },
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
      fontSize:  9,
      color:     '#fff',
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
  // position: 'right' in horizontal (G1), 'top' in vertical (G2/G3)
  const totalLineSeries = showTotal ? [{
    name:       _t('stat.total'),
    type:       'line',
    color:      '#10b981',
    legendIcon: 'circle',
    data:       totals,
    symbolSize: val => val === maxTotal ? 10 : 6,
    lineStyle:  { width: 1, type: 'dashed' },
    itemStyle:  { color: p => p.value === maxTotal ? _cssVar('--red') : _cssVar('--green') },
    label: {
      show:       true,
      position:   isHoriz ? 'right' : 'top',
      fontSize:   10,
      fontWeight: 600,
      color:      _cssVar('--green'),
      formatter:  p => p.value === maxTotal
        ? `{peak|${p.value.toFixed(1)}h}`
        : `${p.value.toFixed(1)}h`,
      rich: { peak: { color: _cssVar('--red'), fontWeight: 700 } },
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

  // ── 8. Grid — margins adjusted by orientation and total presence ─────
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
    backgroundColor: _cssVar('--card'),

    title: truncated ? {
      subtext:      `Exibindo os primeiros ${maxItems} itens`,
      left:         'center',
      top:          4,
      subtextStyle: { color: _cssVar('--text-3'), fontSize: 11 },
    } : undefined,

    legend: {
      data:       legendData,
      top:        8,
      left:       'center',
      textStyle:  { color: _cssVar('--text'), fontSize: 12 },
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

    // Axes: inverted position by orientation
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
