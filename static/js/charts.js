'use strict';

(function (global) {

  // Utilities 

  function getCSSVar(name) {
    return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  }

  function resolveColor(index) {
    var palette = [
      '#3b82f6', '#14b8a6', '#8b5cf6', '#f59e0b',
      '#ef4444', '#22c55e', '#ec4899', '#06b6d4',
      '#a3e635', '#f97316', '#64748b', '#0ea5e9'
    ];
    return palette[index % palette.length];
  }

  function complianceColor(pct) {
    if (pct >= 70) return '#22c55e';
    if (pct >= 40) return '#f59e0b';
    return '#ef4444';
  }

  function hexToRgba(hex, alpha) {
    var r = parseInt(hex.slice(1, 3), 16);
    var g = parseInt(hex.slice(3, 5), 16);
    var b = parseInt(hex.slice(5, 7), 16);
    return 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
  }

  function setupCanvas(canvas) {
    var dpr = window.devicePixelRatio || 1;
    var rect = canvas.getBoundingClientRect();
    canvas.width  = rect.width  * dpr;
    canvas.height = rect.height * dpr;
    var ctx = canvas.getContext('2d');
    ctx.scale(dpr, dpr);
    return { ctx: ctx, w: rect.width, h: rect.height };
  }

  // Donut Chart 
  // drawDonut(canvasId, segments, opts)
  // segments: [{label, value, color}]
  // opts: { centerLabel, centerSub }

  function drawDonut(canvasId, segments, opts) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    opts = opts || {};

    var c = setupCanvas(canvas);
    var ctx = c.ctx, W = c.w, H = c.h;
    var cx = W / 2, cy = H / 2;
    var radius = Math.min(W, H) / 2 - 8;
    var innerR  = radius * 0.62;

    var total = segments.reduce(function (s, seg) { return s + (seg.value || 0); }, 0);
    if (total === 0) {
      // Empty state
      ctx.beginPath();
      ctx.arc(cx, cy, radius, 0, Math.PI * 2);
      ctx.strokeStyle = getCSSVar('--border') || '#e5e7eb';
      ctx.lineWidth = radius - innerR;
      ctx.stroke();
      return;
    }

    var startAngle = -Math.PI / 2;

    segments.forEach(function (seg) {
      if (!seg.value) return;
      var slice = (seg.value / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, radius, startAngle, startAngle + slice);
      ctx.closePath();
      ctx.fillStyle = seg.color;
      ctx.fill();
      startAngle += slice;
    });

    // Inner hole
    ctx.beginPath();
    ctx.arc(cx, cy, innerR, 0, Math.PI * 2);
    ctx.fillStyle = getCSSVar('--bg-card') || '#ffffff';
    ctx.fill();

    // Center text
    if (opts.centerLabel) {
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = getCSSVar('--text-primary') || '#111827';
      ctx.font = 'bold 22px Inter, Segoe UI, Arial, sans-serif';
      ctx.fillText(opts.centerLabel, cx, cy - 8);
      if (opts.centerSub) {
        ctx.font = '11px Inter, Segoe UI, Arial, sans-serif';
        ctx.fillStyle = getCSSVar('--text-muted') || '#6b7280';
        ctx.fillText(opts.centerSub, cx, cy + 14);
      }
    }
  }

  // Horizontal Bar Chart 
  // drawHBar(canvasId, items, opts)
  // items: [{label, value, color}]
  // opts: { max, unit }

  function drawHBar(canvasId, items, opts) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    opts = opts || {};

    var c = setupCanvas(canvas);
    var ctx = c.ctx, W = c.w, H = c.h;

    if (!items.length) return;

    var max = opts.max || Math.max.apply(null, items.map(function (i) { return i.value; })) || 1;
    var unit = opts.unit || '';
    var rowH = H / items.length;
    var labelW = 130;
    var barAreaW = W - labelW - 48;
    var barH = Math.min(rowH * 0.45, 18);
    var muted = getCSSVar('--text-muted') || '#6b7280';
    var textPrimary = getCSSVar('--text-primary') || '#111827';

    items.forEach(function (item, i) {
      var y = i * rowH + rowH / 2;

      // Label
      ctx.textAlign = 'right';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = textPrimary;
      ctx.font = '12px Inter, Segoe UI, Arial, sans-serif';
      var label = item.label.length > 18 ? item.label.slice(0, 17) + '…' : item.label;
      ctx.fillText(label, labelW - 8, y);

      // Track
      ctx.beginPath();
      ctx.roundRect(labelW, y - barH / 2, barAreaW, barH, 4);
      ctx.fillStyle = hexToRgba(item.color || '#3b82f6', 0.12);
      ctx.fill();

      // Fill
      var fillW = (item.value / max) * barAreaW;
      if (fillW > 0) {
        ctx.beginPath();
        ctx.roundRect(labelW, y - barH / 2, fillW, barH, 4);
        ctx.fillStyle = item.color || '#3b82f6';
        ctx.fill();
      }

      // Value label
      ctx.textAlign = 'left';
      ctx.fillStyle = item.color || '#3b82f6';
      ctx.font = 'bold 11px Inter, Segoe UI, Arial, sans-serif';
      ctx.fillText(item.value + unit, labelW + fillW + 6, y);
    });
  }

  // Vertical Bar Chart 
  // drawVBar(canvasId, items, opts)
  // items: [{label, value, color}]

  function drawVBar(canvasId, items, opts) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;
    opts = opts || {};

    var c = setupCanvas(canvas);
    var ctx = c.ctx, W = c.w, H = c.h;

    if (!items.length) return;

    var paddingBottom = 28;
    var paddingTop = 16;
    var chartH = H - paddingBottom - paddingTop;
    var max = opts.max || Math.max.apply(null, items.map(function (i) { return i.value; })) || 1;
    var colW = W / items.length;
    var barW = Math.min(colW * 0.55, 48);
    var muted = getCSSVar('--text-muted') || '#6b7280';
    var border = getCSSVar('--border') || '#e5e7eb';
    var textPrimary = getCSSVar('--text-primary') || '#111827';

    // Gridlines
    [0, 0.25, 0.5, 0.75, 1].forEach(function (frac) {
      var y = paddingTop + chartH * (1 - frac);
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(W, y);
      ctx.strokeStyle = border;
      ctx.lineWidth = 1;
      ctx.stroke();
    });

    items.forEach(function (item, i) {
      var cx = i * colW + colW / 2;
      var barH = (item.value / max) * chartH;
      var x = cx - barW / 2;
      var y = paddingTop + chartH - barH;

      // Bar
      if (barH > 0) {
        ctx.beginPath();
        ctx.roundRect(x, y, barW, barH, [6, 6, 0, 0]);
        ctx.fillStyle = item.color || resolveColor(i);
        ctx.fill();
      }

      // Value on top
      if (item.value > 0) {
        ctx.textAlign = 'center';
        ctx.textBaseline = 'bottom';
        ctx.fillStyle = textPrimary;
        ctx.font = 'bold 11px Inter, Segoe UI, Arial, sans-serif';
        ctx.fillText(item.value, cx, y - 2);
      }

      // X label
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.fillStyle = muted;
      ctx.font = '11px Inter, Segoe UI, Arial, sans-serif';
      ctx.fillText(item.label, cx, paddingTop + chartH + 6);
    });
  }

  // Pie Chart 
  // drawPie(canvasId, segments)
  // segments: [{label, value, color}]

  function drawPie(canvasId, segments) {
    var canvas = document.getElementById(canvasId);
    if (!canvas) return;

    var c = setupCanvas(canvas);
    var ctx = c.ctx, W = c.w, H = c.h;
    var cx = W / 2, cy = H / 2;
    var radius = Math.min(W, H) / 2 - 4;

    var total = segments.reduce(function (s, seg) { return s + (seg.value || 0); }, 0);
    if (total === 0) return;

    var startAngle = -Math.PI / 2;

    segments.forEach(function (seg, i) {
      if (!seg.value) return;
      var slice = (seg.value / total) * Math.PI * 2;
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, radius, startAngle, startAngle + slice);
      ctx.closePath();
      ctx.fillStyle = seg.color || resolveColor(i);
      ctx.fill();
      ctx.strokeStyle = getCSSVar('--bg-card') || '#fff';
      ctx.lineWidth = 2;
      ctx.stroke();
      startAngle += slice;
    });
  }

  // Expose globally
  global.SIWESCharts = {
    drawDonut: drawDonut,
    drawHBar: drawHBar,
    drawVBar: drawVBar,
    drawPie: drawPie,
    resolveColor: resolveColor,
    complianceColor: complianceColor,
  };

})(window);