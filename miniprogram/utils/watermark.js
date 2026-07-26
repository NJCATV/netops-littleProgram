const WATERMARK_STYLE_OPTIONS = [
  { key: 'simple', label: '简洁' },
  { key: 'panel', label: '信息块' },
  { key: 'bar', label: '底栏' },
  { key: 'stamp', label: '巡检' }
]

const FIELD_OPTIONS = [
  { key: 'date', label: '日期', editable: true, picker: 'date' },
  { key: 'time', label: '时间', editable: true, picker: 'time' },
  { key: 'location', label: '定位', editable: true },
  { key: 'note', label: '备注', editable: true },
  { key: 'operator', label: '人员/部门', editable: true },
  { key: 'siteType', label: '现场类型', editable: true }
]

function pad(value) {
  return `${value}`.padStart(2, '0')
}

function formatDate(date = new Date()) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

function formatTime(date = new Date()) {
  return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`
}

function createDefaultFields(now = new Date()) {
  return {
    date: { label: '日期', value: formatDate(now), enabled: true },
    time: { label: '时间', value: formatTime(now), enabled: true },
    location: { label: '定位', value: '正在获取定位', enabled: true },
    note: { label: '备注', value: '现场支撑', enabled: true },
    operator: { label: '人员/部门', value: '江苏有线南京分公司', enabled: true },
    siteType: { label: '现场类型', value: '现场巡检', enabled: true }
  }
}

function getEnabledWatermarkLines(fields) {
  return FIELD_OPTIONS
    .filter((item) => fields[item.key] && fields[item.key].enabled)
    .map((item) => ({
      key: item.key,
      label: fields[item.key].label || item.label,
      value: fields[item.key].value || ''
    }))
    .filter((item) => item.value)
}

module.exports = {
  WATERMARK_STYLE_OPTIONS,
  FIELD_OPTIONS,
  createDefaultFields,
  getEnabledWatermarkLines,
  formatDate,
  formatTime
}
