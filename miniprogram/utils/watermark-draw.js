const { getEnabledWatermarkLines } = require('./watermark')

function truncateText(text, maxLength) {
  if (!text) {
    return ''
  }

  return text.length > maxLength ? text.slice(0, maxLength - 1) + '...' : text
}

function drawTextLines(ctx, lines, x, y, options = {}) {
  const fontSize = options.fontSize || 28
  const lineHeight = options.lineHeight || Math.round(fontSize * 1.5)
  const maxLength = options.maxLength || 32

  ctx.setFontSize(fontSize)
  ctx.setFillStyle(options.color || '#ffffff')

  lines.forEach((line, index) => {
    const text = line.label + '：' + line.value
    ctx.fillText(truncateText(text, maxLength), x, y + index * lineHeight)
  })
}

function drawPanelStyle(ctx, width, height, lines) {
  const padding = Math.max(24, Math.round(width * 0.024))
  const fontSize = Math.max(22, Math.round(width * 0.026))
  const lineHeight = Math.round(fontSize * 1.55)
  const panelHeight = padding * 2 + lines.length * lineHeight
  const panelWidth = Math.min(width - padding * 2, Math.round(width * 0.72))
  const x = padding
  const y = height - panelHeight - padding

  ctx.setGlobalAlpha(0.78)
  ctx.setFillStyle('#17212c')
  ctx.fillRect(x, y, panelWidth, panelHeight)
  ctx.setGlobalAlpha(1)

  ctx.setFillStyle('#2f8cc8')
  ctx.fillRect(x, y, 8, panelHeight)

  drawTextLines(ctx, lines, x + padding, y + padding + fontSize, {
    fontSize,
    lineHeight,
    maxLength: 24
  })
}

function drawBarStyle(ctx, width, height, lines) {
  const fontSize = Math.max(20, Math.round(width * 0.024))
  const titleSize = Math.max(26, Math.round(width * 0.032))
  const lineHeight = Math.round(fontSize * 1.35)
  const padding = Math.max(22, Math.round(width * 0.022))
  const visibleLines = lines.slice(0, 5)
  const barHeight = padding * 2 + titleSize + 10 + Math.min(visibleLines.length, 3) * lineHeight
  const y = height - barHeight

  ctx.setGlobalAlpha(0.84)
  ctx.setFillStyle('#17212c')
  ctx.fillRect(0, y, width, barHeight)
  ctx.setGlobalAlpha(1)

  ctx.setFillStyle('#2f8cc8')
  ctx.fillRect(0, y, width, 8)

  ctx.setFillStyle('#ffffff')
  ctx.setFontSize(titleSize)
  ctx.fillText('现场水印记录', padding, y + padding + titleSize)

  drawTextLines(ctx, visibleLines.slice(0, 3), padding, y + padding + titleSize + 12 + fontSize, {
    fontSize,
    lineHeight,
    maxLength: 36
  })
}

function drawSimpleStyle(ctx, width, height, lines) {
  const fontSize = Math.max(22, Math.round(width * 0.026))
  const lineHeight = Math.round(fontSize * 1.5)
  const padding = Math.max(22, Math.round(width * 0.022))
  const visibleLines = lines.slice(0, 5)
  const startY = padding + fontSize

  ctx.setGlobalAlpha(0.6)
  ctx.setFillStyle('#000000')
  drawTextLines(ctx, visibleLines, padding + 3, startY + 3, {
    fontSize,
    lineHeight,
    maxLength: 34,
    color: '#000000'
  })
  ctx.setGlobalAlpha(1)

  drawTextLines(ctx, visibleLines, padding, startY, {
    fontSize,
    lineHeight,
    maxLength: 34
  })
}

function drawStampStyle(ctx, width, height, lines) {
  const padding = Math.max(22, Math.round(width * 0.022))
  const fontSize = Math.max(20, Math.round(width * 0.023))
  const titleSize = Math.max(26, Math.round(width * 0.032))
  const lineHeight = Math.round(fontSize * 1.38)
  const visibleLines = lines.slice(0, 5)
  const panelWidth = Math.min(width - padding * 2, Math.round(width * 0.58))
  const panelHeight = padding * 2 + titleSize + 10 + visibleLines.length * lineHeight
  const x = width - panelWidth - padding
  const y = padding

  ctx.setGlobalAlpha(0.76)
  ctx.setFillStyle('#f6f8fa')
  ctx.fillRect(x, y, panelWidth, panelHeight)
  ctx.setGlobalAlpha(1)

  ctx.setFillStyle('#2f5f8f')
  ctx.fillRect(x, y, panelWidth, 8)

  ctx.setFillStyle('#202832')
  ctx.setFontSize(titleSize)
  ctx.fillText('巡检留痕', x + padding, y + padding + titleSize)

  drawTextLines(ctx, visibleLines, x + padding, y + padding + titleSize + 14 + fontSize, {
    fontSize,
    lineHeight,
    maxLength: 22,
    color: '#202832'
  })
}

function drawWatermark(ctx, options) {
  const lines = getEnabledWatermarkLines(options.fields)

  if (!lines.length) {
    return
  }

  const style = options.style || 'panel'

  if (style === 'simple') {
    drawSimpleStyle(ctx, options.width, options.height, lines)
    return
  }

  if (style === 'bar') {
    drawBarStyle(ctx, options.width, options.height, lines)
    return
  }

  if (style === 'stamp') {
    drawStampStyle(ctx, options.width, options.height, lines)
    return
  }

  drawPanelStyle(ctx, options.width, options.height, lines)
}

module.exports = {
  drawWatermark
}
