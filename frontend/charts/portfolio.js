/* PMAS — Portfolio Tab Chart Builders
 * Depends on globals defined in app.js:
 *   _cssVar, _t, escHtml, _toolbox, _getPalette, _fmtCost,
 *   _currencyFactor, _currencySymbol, _HCSS, _budgetWarning, _budgetCritical
 * Must be loaded AFTER app.js in index.html.
 */

// Resolves the "ok/success" health color from the chart palette so it
// follows the admin-configured palette color 1, not the fixed --green.
function _healthColor(h) {
  if (h === 'success') return _getPalette()[0] || _cssVar('--primary');
  return _cssVar(_HCSS[h] || '--primary');
}

// ---------------------------------------------------------------------------
// _buildEvmQuadrantOption — CPI × SPI scatter/bubble chart
// ---------------------------------------------------------------------------
function _buildEvmQuadrantOption(items, showTrajectory = false) {
  const AXIS_CAP = 2.0;

  const red   = _cssVar('--red')     || '#ef4444';
  const amber = _cssVar('--amber')   || '#f59e0b';
  const green = _cssVar('--green')   || '#22c55e';
  const blue  = _cssVar('--primary') || '#4f8ef7';
  const dim   = _cssVar('--text-3');

  const colorOf = d => {
    const spiOk = d.spi >= 1.0;
    if (d.cpi >= 1.0 && spiOk)  return green;
    if (d.cpi >= 1.0 && !spiOk) return amber;
    if (d.cpi < 1.0  && spiOk)  return blue;
    return red;
  };

  const rawSpis = items.map(d => d.spi);
  const rawCpis = items.map(d => d.cpi);
  const costs   = items.map(d => d.total_cost || 0);
  const maxCost = Math.max(...costs, 1);
  const _bubbleSize = cost => {
    const normalized = Math.sqrt(Math.max(0, cost) / maxCost);
    return Math.round(10 + normalized * 34);
  };

  const xMin = +Math.max(0, Math.min(...rawSpis, 0.8) - 0.1).toFixed(2);
  const xMax = +Math.min(Math.max(...rawSpis, 1.2) + 0.1, AXIS_CAP + 0.08).toFixed(2);
  const yMin = +Math.max(0, Math.min(...rawCpis, 0.8) - 0.1).toFixed(2);
  const yMax = +Math.min(Math.max(...rawCpis, 1.2) + 0.1, AXIS_CAP + 0.08).toFixed(2);

  // Trajectory connector lines — one per PEP that has ≥2 CPI+SPI snapshots.
  // Hidden by default; toggled via #toggleTrajectoryBtn.
  const trajectoryLines = showTrajectory ? items
    .filter(d => Array.isArray(d.trajectory) && d.trajectory.length >= 2)
    .map(d => ({
      type: 'line',
      name: `traj_${d.pep_wbs}`,
      silent: true,
      showSymbol: true,
      symbolSize: 4,
      z: 1,
      lineStyle: { color: colorOf(d), opacity: 0.4, width: 1.5 },
      itemStyle: { color: colorOf(d), opacity: 0.4 },
      emphasis: { disabled: true },
      tooltip: {
        trigger: 'item',
        formatter: p => {
          const t = p.data._t;
          if (!t) return null;
          return `${escHtml(d.pep_wbs)} — ${escHtml(t.cycle_name)}<br/>SPI: ${t.spi.toFixed(2)}, CPI: ${t.cpi.toFixed(2)}`;
        },
      },
      data: d.trajectory.map(t => ({
        value: [Math.min(t.spi, AXIS_CAP), Math.min(t.cpi, AXIS_CAP)],
        _t: t,
      })),
    })) : [];

  return {
    ..._chartDefaults(),
    brush: {
      brushStyle: {
        borderWidth: 1,
        color:       'rgba(148,163,184,0.10)',
        borderColor: _cssVar('--primary'),
      },
      outOfBrush: { colorAlpha: 0.15 },
    },
    toolbox: _toolbox({
      brush: {
        type:  ['rect', 'clear'],
        title: { rect: _t('toolbox.brush_rect'), clear: _t('toolbox.brush_clear') },
      },
    }, 'PMAS-EVM-Quadrant'),
    tooltip: {
      trigger: 'item',
      ..._chartDefaults().tooltip,
      formatter: p => {
        const d = p.data._raw;
        if (!d) return null;
        const _evmQ = { success: green, warning: amber, danger: red };
        const cC = _evmQ[d.cpi_color] || green;
        const sC = _evmQ[d.spi_color] || green;
        const capNote = v => ` <span style="color:${dim};font-size:9px">(real: ${v.toFixed(2)})</span>`;
        return [
          `<b>${escHtml(d.pep_wbs)}</b>`,
          d.name ? `<span style="color:${dim}">${escHtml(d.name)}</span>` : null,
          `CPI: <b style="color:${cC}">${Math.min(d.cpi, AXIS_CAP).toFixed(2)}</b>${d.cpi > AXIS_CAP ? capNote(d.cpi) : ''}`,
          `SPI: <b style="color:${sC}">${Math.min(d.spi, AXIS_CAP).toFixed(2)}</b>${d.spi > AXIS_CAP ? capNote(d.spi) : ''}`,
        ].filter(Boolean).join('<br/>');
      },
    },
    grid: { top: 40, bottom: 52, left: 60, right: 24, containLabel: false },
    xAxis: {
      name: _t('scatter.axis_spi'),
      nameLocation: 'middle', nameGap: 34,
      nameTextStyle: { color: dim, fontSize: 11 },
      axisLabel: { color: dim, formatter: v => v.toFixed(1) },
      axisLine: { lineStyle: { color: _cssVar('--border') } },
      splitLine: { show: false },
      min: xMin, max: xMax,
    },
    yAxis: {
      name: _t('scatter.axis_cpi'),
      nameLocation: 'middle', nameGap: 52,
      nameTextStyle: { color: dim, fontSize: 11 },
      axisLabel: { color: dim, formatter: v => v.toFixed(1) },
      axisLine: { lineStyle: { color: _cssVar('--border') } },
      splitLine: { show: false },
      min: yMin, max: yMax,
    },
    series: [
      ...trajectoryLines,
      {
        type: 'scatter',
        symbolSize: (value, params) => _bubbleSize(params.data._raw?.total_cost || 0),
        data: items.map(d => {
          const spiCapped = d.spi > AXIS_CAP;
          const cpiCapped = d.cpi > AXIS_CAP;
          const symbol       = (spiCapped || cpiCapped) ? 'arrow' : 'circle';
          const symbolRotate = spiCapped && cpiCapped ? 45 : spiCapped ? 90 : 0;
          return {
            value: [Math.min(d.spi, AXIS_CAP), Math.min(d.cpi, AXIS_CAP)],
            symbol,
            symbolRotate: (spiCapped || cpiCapped) ? symbolRotate : undefined,
            itemStyle: {
              color:       colorOf(d),
              opacity:     0.9,
              borderColor: (spiCapped || cpiCapped) ? _cssVar('--text') : _cssVar('--bg'),
              borderWidth: 2,
            },
            label: {
              show: true, formatter: d.pep_wbs,
              position: 'top', distance: 6,
              color: _cssVar('--text'), fontSize: 10, fontWeight: 600,
            },
            _raw: d,
          };
        }),
        emphasis: { focus: 'self', scale: 1.3, itemStyle: { borderWidth: 3, borderColor: _cssVar('--text') } },
        markLine: {
          silent: true, symbol: 'none',
          lineStyle: { color: _cssVar('--border'), type: 'dashed', width: 1.5 },
          data: [
            { xAxis: 1.0,      label: { formatter: 'SPI=1', color: dim, fontSize: 9 } },
            { yAxis: 1.0,      label: { formatter: 'CPI=1', color: dim, fontSize: 9 } },
            { xAxis: AXIS_CAP, lineStyle: { type: 'dotted', width: 1, color: dim },
              label: { formatter: `→ ${AXIS_CAP}`, color: dim, fontSize: 10, position: 'insideEndTop' } },
            { yAxis: AXIS_CAP, lineStyle: { type: 'dotted', width: 1, color: dim },
              label: { formatter: `↑ ${AXIS_CAP}`, color: dim, fontSize: 10, position: 'insideEndTop' } },
          ],
        },
        markArea: {
          silent: true,
          data: [
            [{ coord: [xMin - 1, yMin - 1], itemStyle: { color: red,   opacity: 0.10 },
               label: { show: true, color: red,   fontSize: 9, position: 'insideTopLeft', formatter: _t('q.bl') } },
             { coord: [1.0, 1.0] }],
            [{ coord: [1.0, yMin - 1],       itemStyle: { color: blue,  opacity: 0.10 },
               label: { show: true, color: blue,  fontSize: 9, position: 'insideTopLeft', formatter: _t('q.br') } },
             { coord: [xMax + 1, 1.0] }],
            [{ coord: [xMin - 1, 1.0],       itemStyle: { color: amber, opacity: 0.10 },
               label: { show: true, color: amber, fontSize: 9, position: 'insideTopLeft', formatter: _t('q.tl') } },
             { coord: [1.0, yMax + 1] }],
            [{ coord: [1.0, 1.0],            itemStyle: { color: green, opacity: 0.10 },
               label: { show: true, color: green, fontSize: 9, position: 'insideTopLeft', formatter: _t('q.tr') } },
             { coord: [xMax + 1, yMax + 1] }],
          ],
        },
      },
    ],
  };
}

// ---------------------------------------------------------------------------
// _buildTreemapOption — portfolio treemap
// ---------------------------------------------------------------------------
function _buildTreemapOption(health, evmMode = false) {
  // fmtVal always receives raw R$ values; _fmtCost applies _currencyFactor once internally
  const fmtVal = v => evmMode ? _fmtCost(v) : v.toFixed(1) + 'h';
  return {
    ..._chartDefaults(),
    toolbox: _toolbox({}, 'PMAS-Treemap'),
    tooltip: {
      trigger: 'item',
      ..._chartDefaults().tooltip,
      formatter: params => {
        const d = health.find(x => x.pep_wbs === params.name);
        if (!d) return escHtml(params.name);
        let html = `<b>${escHtml(d.pep_wbs)}</b>`;
        if (d.pep_description) html += `<br><span style="color:${_cssVar('--text-3')}">${escHtml(d.pep_description)}</span>`;
        if (d.name)            html += `<br>${_t('tt.project')}: ${escHtml(d.name)}`;
        const consumed = evmMode ? d.total_cost : d.total_hours;
        const budget   = evmMode ? d.budget_cost : d.budget_hours;
        html += `<br>${evmMode ? _t('tt.actual_cost_lbl') : _t('tt.consumed')}: <b>${fmtVal(consumed)}</b>`;
        if (budget != null) {
          const pct = (consumed / budget * 100).toFixed(1);
          html += `<br>${_t('ch.budget')}: ${fmtVal(budget)} (${pct}% ${_t('tt.utilized')})`;
        }
        if (!d.is_registered) html += `<br><span style="color:${_cssVar('--amber')}">${_t('tt.pep_not_reg')}</span>`;
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
        show: true, fontSize: 11, color: _cssVar('--text'),
        formatter: params => {
          const d = health.find(x => x.pep_wbs === params.name);
          const raw = d ? (evmMode ? d.total_cost : d.total_hours) : 0;
          const disp = evmMode ? raw * _currencyFactor : raw;
          const valStr = evmMode
            ? _currencySymbol + (disp / 1000 >= 1 ? (disp / 1000).toFixed(0) + 'k' : disp.toFixed(0))
            : disp.toFixed(0) + 'h';
          const nm = params.name.length > 16 ? params.name.slice(0, 15) + '…' : params.name;
          return `${nm}\n${valStr}${d && !d.is_registered ? '\n⚠' : ''}`;
        },
      },
      emphasis: { focus: 'self', itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.5)' } },
      itemStyle: { gapWidth: 2, borderRadius: 4 },
      levels: [{
        itemStyle: { borderWidth: 0, gapWidth: 4 },
        upperLabel: { show: false },
      }],
      data: health.map(d => {
        const consumed = evmMode ? d.total_cost : d.total_hours;   // raw — proportions unaffected by _currencyFactor
        const hColor = evmMode ? d.health_cost_color : d.health_hours_color;
        return {
          name: d.pep_wbs,
          value: consumed,
          itemStyle: {
            color: !d.is_registered
              ? _cssVar('--text-3')
              : _healthColor(hColor),
            borderColor: _cssVar('--bg'),
          },
        };
      }),
    }],
  };
}

// ---------------------------------------------------------------------------
// _buildTimelineTreemapOption — treemap with ECharts timeline scrubber
// ---------------------------------------------------------------------------
function _buildTimelineTreemapOption(snapshots, evmMode) {
  const defaults = _chartDefaults();
  const dim = _cssVar('--text-3');

  function _makeData(health) {
    return health.map(d => {
      const consumed = evmMode ? d.total_cost : d.total_hours;
      const hColor   = evmMode ? d.health_cost_color : d.health_hours_color;
      return {
        name:      d.pep_wbs,
        value:     consumed,
        itemStyle: {
          color:       !d.is_registered ? _cssVar('--text-3') : _healthColor(hColor),
          borderColor: _cssVar('--bg'),
        },
        _raw: d,
      };
    });
  }

  return {
    baseOption: {
      ...defaults,
      toolbox: _toolbox({}, 'PMAS-Treemap-Timeline'),
      tooltip: {
        trigger: 'item',
        ...defaults.tooltip,
        formatter: params => {
          const d = params.data?._raw;
          if (!d) return escHtml(params.name);
          const fmtVal = v => evmMode ? _fmtCost(v) : v.toFixed(1) + 'h';
          const consumed = evmMode ? d.total_cost : d.total_hours;
          const budget   = evmMode ? d.budget_cost : d.budget_hours;
          let html = `<b>${escHtml(d.pep_wbs)}</b>`;
          if (d.pep_description) html += `<br><span style="color:${dim}">${escHtml(d.pep_description)}</span>`;
          if (d.name)            html += `<br>${_t('tt.project')}: ${escHtml(d.name)}`;
          html += `<br>${evmMode ? _t('tt.actual_cost_lbl') : _t('tt.consumed')}: <b>${fmtVal(consumed)}</b>`;
          if (budget != null) {
            const pct = (consumed / budget * 100).toFixed(1);
            html += `<br>${_t('ch.budget')}: ${fmtVal(budget)} (${pct}% ${_t('tt.utilized')})`;
          }
          if (!d.is_registered) html += `<br><span style="color:${_cssVar('--amber')}">${_t('tt.pep_not_reg')}</span>`;
          return html;
        },
      },
      timeline: {
        axisType:     'category',
        autoPlay:     false,
        playInterval: 1500,
        data:         snapshots.map(s => s.cycle_name),
        left: 0, right: 0, bottom: 4,
        height: 52,
        padding: [4, 10, 4, 10],
        currentIndex: snapshots.length - 1,
        controlStyle: {
          color:       _cssVar('--primary'),
          borderColor: 'transparent',
        },
        checkpointStyle: {
          color:       _cssVar('--primary'),
          borderColor: _cssVar('--primary'),
          symbol:      'circle',
          symbolSize:  12,
          animation:   false,
        },
        label: {
          color:    dim,
          fontSize: 9,
          formatter: val => val.length > 9 ? val.slice(0, 8) + '…' : val,
        },
        lineStyle:    { color: _cssVar('--border') },
        itemStyle:    { color: _cssVar('--border') },
        emphasis: {
          label:     { color: _cssVar('--text'), fontSize: 10 },
          itemStyle: { color: _cssVar('--primary') },
        },
        tooltip: { show: false },
        symbol:     'circle',
        symbolSize: 7,
      },
      series: [{
        type:  'treemap',
        roam:  false,
        left:  0,
        right: 0,
        top:   0,
        bottom: 64,
        breadcrumb: { show: false },
        label: {
          show: true, fontSize: 11, color: _cssVar('--text'),
          formatter: params => {
            const d = params.data._raw;
            if (!d) return params.name;
            const raw  = evmMode ? d.total_cost : d.total_hours;
            const disp = evmMode ? raw * _currencyFactor : raw;
            const valStr = evmMode
              ? _currencySymbol + (disp / 1000 >= 1 ? (disp / 1000).toFixed(0) + 'k' : disp.toFixed(0))
              : disp.toFixed(0) + 'h';
            const nm = params.name.length > 16 ? params.name.slice(0, 15) + '…' : params.name;
            return `${nm}\n${valStr}${d && !d.is_registered ? '\n⚠' : ''}`;
          },
        },
        emphasis:  { focus: 'self', itemStyle: { shadowBlur: 8, shadowColor: 'rgba(0,0,0,0.5)' } },
        itemStyle: { gapWidth: 2, borderRadius: 4 },
        levels:    [{ itemStyle: { borderWidth: 0, gapWidth: 4 }, upperLabel: { show: false } }],
        data: [],
      }],
    },
    options: snapshots.map(s => ({ series: [{ data: _makeData(s.items) }] })),
  };
}

// ---------------------------------------------------------------------------
// _buildBulletOption — bullet chart: budgeted vs actual
// ---------------------------------------------------------------------------
function _buildBulletOption(withBudget, evmMode = false) {
  const labels  = withBudget.map(d => d.pep_wbs + (d.name ? `\n${d.name.slice(0, 28)}` : ''));
  const budgets = withBudget.map(d => (evmMode ? (d.budget_cost || 0) * _currencyFactor : d.budget_hours) || 0);
  const actuals = withBudget.map(d => {
    const consumed = evmMode ? (d.total_cost || 0) * _currencyFactor : d.total_hours;
    const hColor = evmMode ? d.health_cost_color : d.health_hours_color;
    const color  = _healthColor(hColor);
    return { value: +consumed.toFixed(2), itemStyle: { color, borderRadius: [0, 2, 2, 0] } };
  });
  const unit = evmMode ? _currencySymbol : 'h';
  const fmtAx = evmMode
    ? v => v >= 1000 ? `${_currencySymbol}${(v/1000).toFixed(0)}k` : `${_currencySymbol}${v.toFixed(0)}`
    : v => `${v}h`;
  return {
    ..._chartDefaults(),
    toolbox: _toolbox({}, 'PMAS-Bullet'),
    grid: { top: 46, right: '10%', bottom: 16, left: '2%', containLabel: true },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'none' },
      ..._chartDefaults().tooltip,
      formatter: params => {
        const idx = params[0].dataIndex;
        const b   = budgets[idx];
        const a   = params.find(p => p.seriesName === _t('ch.actual'))?.value ?? 0;
        const pct = b > 0 ? `${(a / b * 100).toFixed(1)}%` : '—';
        const fmtV = v => evmMode ? _fmtCost(v / _currencyFactor) : v.toFixed(1) + 'h';
        const d = withBudget[idx];
        const cpiItem = d?.cpi;
        let html = `<b>${escHtml(params[0].axisValue.replace('\n', ' '))}</b><br>`;
        html += `${_t('ch.budget')}: <b>${fmtV(b)}</b><br>${_t('ch.actual')}: <b>${fmtV(a)}</b><br>`;
        html += `${_t('tt.utilization')}: <b>${pct}</b>`;
        if (cpiItem != null) {
          const _cpiC = { success: _cssVar('--green'), warning: _cssVar('--amber'), danger: _cssVar('--red') };
          const cpiColor = _cpiC[d.cpi_color] || _cssVar('--green');
          html += `<br>IDC (CPI): <b style="color:${cpiColor}">${cpiItem.toFixed(2)}</b>`;
        }
        if (b > 0 && a > b) html += `<br><span style="color:${_cssVar('--red')}">⚠ ${_t('tt.over_budget')}</span>`;
        return html;
      },
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: _cssVar('--text-3'), fontSize: 10, formatter: fmtAx },
      splitLine: { lineStyle: { color: _cssVar('--border') } },
    },
    yAxis: {
      type: 'category', data: labels,
      axisTick: { show: false },
      axisLabel: { color: _cssVar('--text'), fontSize: 10, lineHeight: 16 },
    },
    series: [
      {
        name: _t('ch.budget'),
        type: 'bar',
        barMaxWidth: 48,
        barGap: '-100%',
        emphasis: { focus: 'series' },
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
        emphasis: { focus: 'series' },
        z: 2,
        data: actuals,
        label: {
          show: true,
          position: 'right',
          fontSize: 10,
          color: _cssVar('--text'),
          formatter: params => {
            const b = budgets[params.dataIndex];
            return b > 0 ? `${(params.value / b * 100).toFixed(0)}%` : '';
          },
        },
      },
      {
        // Transparent overlay — inside label only, no visual bar
        type: 'bar',
        barMaxWidth: 28,
        barGap: '-100%',
        z: 3,
        silent: true,
        legendHoverLink: false,
        data: actuals.map(a => ({
          value: a.value,
          itemStyle: { color: 'transparent' },
        })),
        label: {
          show: true,
          position: 'inside',
          fontSize: 10,
          color: _cssVar('--text'),
          overflow: 'truncate',
          formatter: params => {
            if (!params.value) return '';
            if (evmMode) {
              const disp = params.value; // already in display units (raw * _currencyFactor)
              return _currencySymbol + (disp >= 1000 ? (disp / 1000).toFixed(0) + 'k' : disp.toFixed(0));
            }
            return `${(+params.value).toFixed(1)}h`;
          },
        },
      },
    ],
  };
}
