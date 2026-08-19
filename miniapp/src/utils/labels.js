const ROLE_LABELS = {
  super_admin: '超级管理员',
  org_admin: '组织管理员',
  normal_user: '普通用户'
}

const USER_TYPE_LABELS = {
  internal: '内部用户',
  external: '外部用户',
  system: '系统账号',
  all: '全部类型'
}

const STATUS_LABELS = {
  active: '启用',
  disabled: '禁用',
  pending: '待处理',
  enabled: '启用',
  maintenance: '维护中',
  offline: '离线'
}

const ENVIRONMENT_LABELS = {
  production: '生产',
  staging: '维护',
  test: '测试',
  backup: '备用'
}

const CREDENTIAL_TYPE_LABELS = {
  ssh: 'SSH',
  mysql: 'MySQL',
  database: '数据库',
  redis: 'Redis',
  kafka: 'Kafka',
  api: 'API',
  web: 'Web',
  switch: '交换机',
  other: '其他'
}

const OSS_STATUS_LABELS = {
  unbound: '未绑定',
  pending: '待确认',
  bound: '已绑定',
  failed: '校验失败'
}

const MESSAGE_LABELS = {
  'permission denied': '没有操作权限',
  'user not found': '用户不存在',
  'org not found': '组织不存在',
  'parent_id is invalid': '上级组织无效',
  'org level cannot exceed 3': '组织层级不能超过三级',
  'menu not found': '功能不存在',
  'server not found': '服务器不存在',
  'credential not found': '资料不存在',
  'credential name is required': '请填写资料名称',
  'credential type is invalid': '资料类型无效',
  'share_user_ids is invalid': '共享用户无效',
  'group_id is invalid': '分组无效',
  'server status is invalid': '服务器状态无效',
  'environment is invalid': '环境类型无效',
  'last_checked_at is invalid': '巡检时间无效',
  'port is invalid': '端口无效',
  'mobile already exists': '手机号已存在',
  'oss_account already exists': 'OSS 账号已存在',
  'oss_account is required': '请填写 OSS 账号',
  'oss_password is required': '请填写 OSS 密码',
  'oss_account is already bound': 'OSS 账号已被其他用户绑定',
  'OSS login failed': 'OSS 登录校验失败',
  'avatar file is required': '请选择头像图片',
  'avatar file is too large': '头像图片不能超过 2MB',
  'avatar file type is invalid': '头像仅支持 JPG、PNG 或 WebP',
  'avatar dimensions are too small': '头像宽高不能小于 128 像素',
  'avatar dimensions are too large': '头像宽高不能超过 4096 像素',
  'cannot disable the last super_admin': '不能禁用最后一个超级管理员',
  'real_name is required': '请填写姓名',
  'mobile is invalid': '手机号格式不正确',
  'org_id is invalid': '组织无效',
  'manage_org_id is invalid': '管理组织无效',
  'name is required': '请填写名称',
  'menu_key already exists': '菜单编码已存在',
  'menu_key is required': '请填写菜单编码',
  'icon is required': '请填写图标',
  'group_name is required': '请填写分组',
  'min_role is invalid': '最小角色无效',
  'user_type is invalid': '用户类型无效',
  'sort_order is invalid': '排序必须是数字',
  'network request:fail': '网络请求失败',
  'request:fail': '网络请求失败'
}

export function roleLabel(value) {
  return ROLE_LABELS[value] || value || '-'
}

export function userTypeLabel(value) {
  return USER_TYPE_LABELS[value] || value || '-'
}

export function statusLabel(value) {
  return STATUS_LABELS[value] || value || '-'
}

export function environmentLabel(value) {
  return ENVIRONMENT_LABELS[value] || value || '-'
}

export function credentialTypeLabel(value) {
  return CREDENTIAL_TYPE_LABELS[value] || value || '-'
}

export function ossStatusLabel(value) {
  return OSS_STATUS_LABELS[value] || value || '-'
}

export function enabledLabel(value) {
  return value ? '启用' : '禁用'
}

export function messageLabel(message) {
  return MESSAGE_LABELS[message] || message || '操作失败'
}

export function option(label, value) {
  return { label, value }
}
