<template>
  <view class="page keyring-page">
    <view class="keyring-head">
      <view>
        <view class="keyring-title">服务器管理</view>
        <view class="keyring-subtitle">共 {{ total }} 台</view>
      </view>
      <button class="round-add" @tap="openCreate">+</button>
    </view>

    <view class="simple-search">
      <view class="search-mark"></view>
      <input
        v-model.trim="keyword"
        class="simple-search-input"
        placeholder="搜索服务器名称 / 用途 / IP"
        placeholder-class="placeholder"
        confirm-type="search"
        @confirm="loadServers"
      />
    </view>

    <scroll-view class="group-filter" scroll-x>
      <button
        v-for="group in groupFilterOptions"
        :key="group.value"
        class="group-pill"
        :class="{ active: selectedGroup === group.value }"
        @tap="selectGroup(group.value)"
      >
        <text class="pill-icon group-mini"></text>
        <text>{{ group.label }}</text>
      </button>
    </scroll-view>

    <view v-if="loading" class="status-text">加载中...</view>
    <view v-else-if="items.length === 0" class="empty-panel">
      <view class="empty-icon">+</view>
      <view class="empty-title">还没有服务器</view>
      <view class="empty-desc">点击右上角添加第一台，后续可记录 SSH、MySQL、端口、UFW 和交换机资料。</view>
    </view>

    <view v-else class="keyring-list">
      <view
        v-for="item in items"
        :key="item.id"
        class="keyring-card"
        @tap="openDetail(item)"
      >
        <view class="asset-icon" :class="`asset-icon-${item.icon || 'linux'}`">
          <view class="icon-glyph"></view>
        </view>
        <view class="keyring-main">
          <view class="keyring-line">
            <text class="keyring-name">{{ item.name }}</text>
            <text class="env-chip" :class="`env-${item.environment || 'production'}`">{{ environmentLabel(item.environment) }}</text>
          </view>
          <view v-if="coreIp(item)" class="keyring-ip">{{ coreIp(item) }}</view>
          <view v-if="item.role" class="keyring-purpose">{{ item.role }}</view>
        </view>
      </view>
    </view>

    <view v-if="showDetail" class="detail-page">
      <view class="keyring-detail-scroll">
        <view class="keyring-detail-nav">
          <button class="detail-close" @tap="closeDetail">关闭</button>
          <view class="detail-nav-title">{{ selectedServer.name || '服务器详情' }}</view>
          <button v-if="selectedServer.can_manage" class="nav-edit" @tap="openEditFromDetail">编辑</button>
        </view>

        <view class="summary-card">
          <view class="summary-top">
            <view class="asset-icon large" :class="`asset-icon-${selectedServer.icon || 'linux'}`">
              <view class="icon-glyph"></view>
            </view>
            <view class="summary-title-area">
              <view class="summary-name">{{ selectedServer.name }}</view>
              <view v-if="selectedServer.role" class="summary-purpose">{{ selectedServer.role }}</view>
            </view>
            <text class="env-chip" :class="`env-${selectedServer.environment || 'production'}`">{{ environmentLabel(selectedServer.environment) }}</text>
          </view>
          <view class="summary-grid">
            <view v-if="coreIp(selectedServer)" class="summary-field">
              <text>IP</text>
              <strong>{{ coreIp(selectedServer) }}</strong>
            </view>
            <view v-if="selectedServer.location" class="summary-field">
              <text>位置</text>
              <strong>{{ selectedServer.location }}</strong>
            </view>
            <view v-if="selectedServer.hostname" class="summary-field">
              <text>主机名</text>
              <strong>{{ selectedServer.hostname }}</strong>
            </view>
          </view>
          <view class="summary-flags">
            <text v-if="selectedServer.ufw_enabled" class="ufw-chip">UFW 已启用</text>
            <text class="privacy-chip">默认仅本人可见 · 已共享人员可查看</text>
          </view>
          <view v-if="selectedServer.group_name || selectedServer.group_share_count" class="summary-meta">
            <view v-if="selectedServer.group_name" class="summary-meta-item">
              <text class="pill-icon group-mini"></text>
              <text>分组：{{ selectedServer.group_name }}</text>
            </view>
            <view v-if="selectedServer.group_share_count" class="summary-meta-item">
              <text class="pill-icon share-mini"></text>
              <text>共享给 {{ selectedServer.group_share_count }} 人</text>
            </view>
          </view>
        </view>

        <view class="detail-section">
          <view class="section-head compact">
            <view class="section-title">连接信息</view>
            <button v-if="selectedServer.can_manage" class="section-add" @tap="openCredentialForm('ssh')">+ 新增</button>
          </view>
          <view v-if="credentials.length === 0" class="empty-line">暂无连接资料。</view>
          <view v-for="item in credentials" :key="item.id" class="compact-connection-card">
            <view class="record-head">
              <view class="record-title-wrap">
                <view class="record-type-icon" :class="`record-type-${item.credential_type || 'other'}`">
                  <view class="icon-glyph"></view>
                </view>
                <view class="record-title">{{ item.name }}</view>
                <text class="type-chip">{{ credentialTypeLabel(item.credential_type) }}</text>
              </view>
              <button v-if="selectedServer.can_manage" class="record-edit" @tap="editCredential(item)">编辑</button>
            </view>
            <view class="record-lines">
              <view v-if="connectionHost(item)" class="record-line">
                <text>地址</text>
                <strong>{{ connectionHost(item) }}</strong>
              </view>
              <view v-if="item.port" class="record-line">
                <text>端口</text>
                <strong>{{ item.port }}</strong>
              </view>
              <view v-if="item.username" class="record-line">
                <text>账号</text>
                <strong>{{ item.username }}</strong>
              </view>
              <view v-if="item.has_secret" class="record-line secret-line">
                <text>密码（查看会记入审计）</text>
                <view class="secret-tools">
                  <strong>{{ maskedSecret(item) }}</strong>
                  <button class="icon-action eye" @tap="toggleSecret(item)"></button>
                  <button class="icon-action copy" @tap="copySecret(item)"></button>
                </view>
              </view>
              <view v-if="item.database_name" class="record-line">
                <text>库名</text>
                <strong>{{ item.database_name }}</strong>
              </view>
            </view>
            <view v-if="item.command" class="command-box">
              <text>{{ item.command }}</text>
              <button @tap="copyCommand(item)">复制</button>
            </view>
            <view v-if="item.remark" class="record-remark">{{ item.remark }}</view>
          </view>
        </view>

        <view v-if="selectedServer.remark" class="detail-section">
          <view class="section-head compact">
            <view class="section-title">备注</view>
          </view>
          <view class="remark-card">{{ selectedServer.remark }}</view>
        </view>
      </view>

    </view>

    <view v-if="showServerForm" class="form-mask" @tap="closeServerForm">
      <view class="sheet-panel" @tap.stop>
        <view class="sheet-header">
          <view>
            <view class="sheet-title">{{ formMode === 'edit' ? '编辑服务器' : '新增服务器' }}</view>
            <view class="sheet-subtitle">按分组维护基础、网络、备注和可见范围</view>
          </view>
          <button class="close-button" @tap="closeServerForm">×</button>
        </view>

        <view class="form-card">
          <view class="form-section-title">基础信息</view>
          <view class="field">
            <view class="field-label">图标</view>
            <view class="icon-picker">
              <button
                v-for="icon in iconOptions"
                :key="icon.value"
                class="icon-choice"
                :class="{ active: form.icon === icon.value }"
                @tap="form.icon = icon.value"
              >
                <view class="asset-icon form-icon" :class="`asset-icon-${icon.value}`">
                  <view class="icon-glyph"></view>
                </view>
                <text class="icon-label">{{ icon.label }}</text>
              </button>
            </view>
          </view>
          <view class="field">
            <view class="field-label">服务器名称</view>
            <input v-model.trim="form.name" class="input" placeholder="如核心应用服务器" placeholder-class="placeholder" />
          </view>
          <view class="field">
            <view class="field-label">所属分组</view>
            <input v-model.trim="form.group_name" class="input" placeholder="如后端 / 数据库 / 测试环境" placeholder-class="placeholder" />
          </view>
          <view class="field two-col">
            <view>
              <view class="field-label">环境</view>
              <picker :range="environmentOptions" range-key="label" :value="environmentIndex" @change="pickEnvironment">
                <view class="picker-box">{{ environmentLabel(form.environment) }}</view>
              </picker>
            </view>
            <view>
              <view class="field-label">状态</view>
              <picker :range="editStatusOptions" range-key="label" :value="editStatusIndex" @change="pickStatus">
                <view class="picker-box">{{ serverStatusLabel(form.status) }}</view>
              </picker>
            </view>
          </view>
          <view class="field two-col">
            <view>
              <view class="field-label">内网 IP</view>
              <input v-model.trim="form.intranet_ip" class="input" placeholder="10.x.x.x" placeholder-class="placeholder" />
            </view>
            <view>
              <view class="field-label">公网 IP</view>
              <input v-model.trim="form.public_ip" class="input" placeholder="可不填" placeholder-class="placeholder" />
            </view>
          </view>
          <view class="field two-col">
            <view>
              <view class="field-label">用途</view>
              <input v-model.trim="form.role" class="input" placeholder="API / 数据库 / 测试机" placeholder-class="placeholder" />
            </view>
            <view>
              <view class="field-label">负责人</view>
              <input v-model.trim="form.owner_name" class="input" placeholder="姓名" placeholder-class="placeholder" />
            </view>
          </view>
        </view>

        <view class="form-card">
          <view class="form-section-title">系统与网络</view>
          <view class="field two-col">
            <view>
              <view class="field-label">主机名</view>
              <input v-model.trim="form.hostname" class="input" placeholder="hostname" placeholder-class="placeholder" />
            </view>
            <view>
              <view class="field-label">位置</view>
              <input v-model.trim="form.location" class="input" placeholder="机房 / 云厂商 / 区域" placeholder-class="placeholder" />
            </view>
          </view>
          <view class="field two-col">
            <view>
              <view class="field-label">系统</view>
              <input v-model.trim="form.os_name" class="input" placeholder="Ubuntu / CentOS" placeholder-class="placeholder" />
            </view>
            <view>
              <view class="field-label">版本</view>
              <input v-model.trim="form.os_version" class="input" placeholder="22.04 / 7.9" placeholder-class="placeholder" />
            </view>
          </view>
          <view class="field two-col">
            <view>
              <view class="field-label">上联交换机</view>
              <input v-model.trim="form.upstream_device" class="input" placeholder="如 SW-01" placeholder-class="placeholder" />
            </view>
            <view>
              <view class="field-label">上联端口</view>
              <input v-model.trim="form.upstream_port" class="input" placeholder="GE0/0/1" placeholder-class="placeholder" />
            </view>
          </view>
          <view class="field two-col">
            <view>
              <view class="field-label">VLAN</view>
              <input v-model.trim="form.upstream_vlan" class="input" placeholder="VLAN 10" placeholder-class="placeholder" />
            </view>
            <view>
              <view class="field-label">业务网段</view>
              <input v-model.trim="form.upstream_network" class="input" placeholder="10.x.x.0/24" placeholder-class="placeholder" />
            </view>
          </view>
          <view class="field">
            <view class="field-label">UFW 防火墙</view>
            <picker :range="ufwOptions" range-key="label" :value="ufwIndex" @change="pickUfw">
              <view class="picker-box">{{ form.ufw_enabled ? '已启用' : '未启用' }}</view>
            </picker>
          </view>
        </view>

        <view class="form-card">
          <view class="form-section-title">备注与可见范围</view>
          <view class="notice-box">SSH、MySQL、API、交换机命令等连接资料在详情页“连接信息”里单独维护，密码和 Token 会继续走加密存取。</view>
          <view class="field">
            <view class="field-label">备注</view>
            <textarea v-model.trim="form.remark" class="textarea" maxlength="255" placeholder="只记录说明，不在这里填写密码、密钥或 token" placeholder-class="placeholder" />
          </view>
          <view class="field">
            <view class="field-label">可见用户</view>
            <checkbox-group class="share-list" @change="onShareChange">
              <label v-for="user in shareUsers" :key="user.id" class="share-row">
                <checkbox :value="String(user.id)" :checked="form.share_user_ids.includes(user.id)" color="#1f6feb" />
                <view class="share-copy">
                  <view class="share-name">{{ user.real_name || user.mobile }}</view>
                  <view class="share-meta">{{ user.mobile }} · {{ roleLabel(user.role_code) }}</view>
                </view>
              </label>
            </checkbox-group>
          </view>
          <view class="field">
            <view class="field-label">分组共享用户</view>
            <checkbox-group class="share-list" @change="onGroupShareChange">
              <label v-for="user in shareUsers" :key="user.id" class="share-row">
                <checkbox :value="String(user.id)" :checked="form.group_share_user_ids.includes(user.id)" color="#1f6feb" />
                <view class="share-copy">
                  <view class="share-name">{{ user.real_name || user.mobile }}</view>
                  <view class="share-meta">{{ user.mobile }} · {{ roleLabel(user.role_code) }}</view>
                </view>
              </label>
            </checkbox-group>
          </view>
        </view>

        <view class="sheet-actions">
          <button class="ghost-button" @tap="closeServerForm">取消</button>
          <button class="primary-button" :loading="saving" :disabled="saving" @tap="saveServer">保存服务器</button>
        </view>
      </view>
    </view>

    <view v-if="showDataForm" class="form-mask" @tap="closeDataForm">
      <view class="sheet-panel" @tap.stop>
        <view class="sheet-header">
          <view>
            <view class="sheet-title">{{ credentialForm.id ? '编辑资料' : '新增资料' }}</view>
            <view class="sheet-subtitle">密码、Token 和密钥默认加密保存，页面默认脱敏。</view>
          </view>
          <button class="close-button" @tap="closeDataForm">×</button>
        </view>
        <view class="form-card">
          <view class="field two-col">
            <view>
              <view class="field-label">名称</view>
              <input v-model.trim="credentialForm.name" class="input" placeholder="如 SSH / MySQL" placeholder-class="placeholder" />
            </view>
            <view>
              <view class="field-label">类型</view>
              <picker :range="credentialTypeOptions" range-key="label" :value="credentialTypeIndex" @change="pickCredentialType">
                <view class="picker-box">{{ credentialTypeLabel(credentialForm.credential_type) }}</view>
              </picker>
            </view>
          </view>
          <view class="field two-col">
            <view>
              <view class="field-label">Host</view>
              <input v-model.trim="credentialForm.host" class="input" placeholder="默认用服务器 IP" placeholder-class="placeholder" />
            </view>
            <view>
              <view class="field-label">端口</view>
              <input v-model="credentialForm.port" class="input" type="number" :placeholder="portPlaceholder" placeholder-class="placeholder" />
            </view>
          </view>
          <view class="field two-col">
            <view>
              <view class="field-label">用户名</view>
              <input v-model.trim="credentialForm.username" class="input" placeholder="如 admin / operator" placeholder-class="placeholder" />
            </view>
            <view>
              <view class="field-label">库名 / Topic</view>
              <input v-model.trim="credentialForm.database_name" class="input" placeholder="可不填" placeholder-class="placeholder" />
            </view>
          </view>
          <view class="field">
            <view class="field-label">密码 / Token / 密钥</view>
            <input v-model="credentialForm.secret" class="input" password placeholder="留空表示不修改" placeholder-class="placeholder" />
          </view>
          <view class="field">
            <view class="field-label">自定义命令</view>
            <input v-model.trim="credentialForm.command" class="input" placeholder="可不填，系统按模板生成" placeholder-class="placeholder" />
          </view>
          <view class="field">
            <view class="field-label">备注</view>
            <textarea v-model.trim="credentialForm.remark" class="textarea small-textarea" maxlength="255" placeholder="补充用途或注意事项" placeholder-class="placeholder" />
          </view>
        </view>
        <button class="primary-button save-button" :loading="credentialSaving" :disabled="credentialSaving" @tap="saveCredential">保存资料</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import {
  createCredential,
  createServer,
  listCredentials,
  listServers,
  revealCredential,
  serverShareOptions,
  updateCredential,
  updateServer
} from '../../../api/adminServers'
import { requireLogin } from '../../../api/auth'
import { credentialTypeLabel, environmentLabel, messageLabel, roleLabel } from '../../../utils/labels'

const statusOptions = [
  { label: '全部', value: '' },
  { label: '在线', value: 'active' },
  { label: '离线', value: 'offline' },
  { label: '维护', value: 'maintenance' }
]
const editStatusOptions = statusOptions.slice(1)
const environmentOptions = [
  { label: '生产', value: 'production' },
  { label: '测试', value: 'test' },
  { label: '维护', value: 'staging' },
  { label: '备用', value: 'backup' }
]
const ufwOptions = [
  { label: '未启用', value: false },
  { label: '已启用', value: true }
]
const credentialTypeOptions = [
  { label: 'SSH', value: 'ssh' },
  { label: 'MySQL', value: 'mysql' },
  { label: 'API', value: 'api' },
  { label: 'Web', value: 'web' },
  { label: '交换机', value: 'switch' },
  { label: 'Redis', value: 'redis' },
  { label: 'Kafka', value: 'kafka' },
  { label: '数据库', value: 'database' },
  { label: '其他', value: 'other' }
]
const iconOptions = [
  { label: 'Linux 服务器', value: 'linux' },
  { label: '数据库', value: 'database' },
  { label: 'Web 服务', value: 'web' },
  { label: '交换机', value: 'switch' },
  { label: 'NAS', value: 'nas' },
  { label: '云主机', value: 'cloud' },
  { label: '测试机', value: 'test' },
  { label: '其他', value: 'other' }
]
const keyword = ref('')
const status = ref('')
const selectedGroup = ref('')
const items = ref([])
const counts = ref({})
const groups = ref([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)
const showDetail = ref(false)
const showServerForm = ref(false)
const showDataForm = ref(false)
const formMode = ref('create')
const formStep = ref('base')
const detailTab = ref('overview')
const selectedServer = ref({})
const credentials = ref([])
const shareUsers = ref([])
const credentialSaving = ref(false)
const revealedSecrets = reactive({})
const form = reactive(defaultForm())
const credentialForm = reactive(defaultCredentialForm())

const environmentIndex = computed(() => Math.max(0, environmentOptions.findIndex((item) => item.value === form.environment)))
const editStatusIndex = computed(() => Math.max(0, editStatusOptions.findIndex((item) => item.value === form.status)))
const ufwIndex = computed(() => (form.ufw_enabled ? 1 : 0))
const credentialTypeIndex = computed(() => Math.max(0, credentialTypeOptions.findIndex((item) => item.value === credentialForm.credential_type)))
const groupFilterOptions = computed(() => [
  { label: '全部', value: '' },
  ...groups.value.map((item) => ({ label: item.name, value: String(item.id) })),
  { label: '未分组', value: 'ungrouped' }
])
const portPlaceholder = computed(() => {
  const map = { ssh: '5333', mysql: '6603', redis: '6379', kafka: '9092', api: '443', web: '80', switch: '22' }
  return map[credentialForm.credential_type] || '端口'
})
const hasOverviewInfo = computed(() => {
  const item = selectedServer.value
  return Boolean(
    fieldValue(item.os_name, item.os_version) ||
      item.hostname ||
      item.location ||
      upstreamLine(item) ||
      item.upstream_network ||
      item.ufw_enabled !== null && item.ufw_enabled !== undefined
  )
})
onLoad(() => {
  requireLogin()
    .then(loadServers)
    .catch((error) => {
      if (error.message !== '未登录') {
        toast(error.message)
      }
    })
})

function defaultForm() {
  return {
    id: null,
    name: '',
    group_name: '',
    icon: 'linux',
    hostname: '',
    intranet_ip: '',
    public_ip: '',
    role: '',
    location: '',
    owner_name: '',
    os_name: '',
    os_version: '',
    upstream_device: '',
    upstream_port: '',
    upstream_vlan: '',
    upstream_network: '',
    ufw_enabled: false,
    environment: 'production',
    status: 'active',
    remark: '',
    share_user_ids: [],
    group_share_user_ids: []
  }
}

function defaultCredentialForm(type = 'ssh') {
  return {
    id: null,
    name: '',
    credential_type: type,
    host: '',
    port: '',
    username: '',
    secret: '',
    database_name: '',
    command: '',
    remark: ''
  }
}

function loadServers() {
  loading.value = true
  return listServers({ keyword: keyword.value, group_id: selectedGroup.value })
    .then((data) => {
      items.value = data.items || []
      counts.value = data.counts || {}
      groups.value = data.groups || []
      total.value = data.total || 0
    })
    .catch((error) => toast(error.message))
    .finally(() => {
      loading.value = false
    })
}

function selectGroup(value) {
  selectedGroup.value = value
  loadServers()
}

function serverStatusLabel(value) {
  const map = { active: '在线', maintenance: '维护', offline: '离线' }
  return map[value] || value || '-'
}

function serverIconLabel(value) {
  const option = iconOptions.find((item) => item.value === value)
  return option?.label || '服务器'
}

function coreIp(item) {
  return item.intranet_ip || item.public_ip || item.hostname || ''
}

function summaryLine(item) {
  return item.role || ''
}

function fieldValue(...parts) {
  return parts.filter(Boolean).join(' ')
}

function upstreamLine(item) {
  return [item.upstream_device, item.upstream_port, item.upstream_vlan].filter(Boolean).join(' · ')
}

function resetForm() {
  Object.assign(form, defaultForm())
}

function openCreate() {
  resetForm()
  formMode.value = 'create'
  formStep.value = 'base'
  showServerForm.value = true
  loadShareOptions()
}

function openEditFromDetail() {
  openEdit(selectedServer.value)
}

function openEdit(item) {
  Object.assign(form, defaultForm(), item, {
    icon: item.icon || 'linux',
    ufw_enabled: Boolean(item.ufw_enabled),
    group_name: item.group_name || '',
    share_user_ids: (item.share_user_ids || []).map((id) => Number(id)),
    group_share_user_ids: (item.group_share_user_ids || []).map((id) => Number(id))
  })
  formMode.value = 'edit'
  formStep.value = 'base'
  showServerForm.value = true
  loadShareOptions()
}

function closeServerForm() {
  showServerForm.value = false
  resetForm()
}

function pickEnvironment(event) {
  form.environment = environmentOptions[Number(event.detail.value)].value
}

function pickStatus(event) {
  form.status = editStatusOptions[Number(event.detail.value)].value
}

function pickUfw(event) {
  form.ufw_enabled = Boolean(ufwOptions[Number(event.detail.value)].value)
}

function onShareChange(event) {
  form.share_user_ids = (event.detail.value || []).map((id) => Number(id))
}

function onGroupShareChange(event) {
  form.group_share_user_ids = (event.detail.value || []).map((id) => Number(id))
}

function loadShareOptions() {
  if (shareUsers.value.length) {
    return
  }
  serverShareOptions()
    .then((data) => {
      shareUsers.value = data.users || []
      groups.value = data.groups || groups.value
    })
    .catch((error) => toast(error.message))
}

function saveServer() {
  if (!form.name) {
    toast('请填写服务器名称')
    formStep.value = 'base'
    return
  }
  saving.value = true
  const payload = { ...form }
  const action = formMode.value === 'edit' ? updateServer(form.id, payload) : createServer(payload)
  action
    .then((data) => {
      toast('保存成功')
      closeServerForm()
      if (showDetail.value && selectedServer.value.id === data.id) {
        selectedServer.value = data
      }
      loadServers()
    })
    .catch((error) => toast(error.message))
    .finally(() => {
      saving.value = false
    })
}

function openDetail(item) {
  selectedServer.value = item
  showDetail.value = true
  loadCredentials()
}

function closeDetail() {
  showDetail.value = false
  selectedServer.value = {}
  credentials.value = []
  Object.keys(revealedSecrets).forEach((key) => delete revealedSecrets[key])
}

function loadCredentials() {
  return listCredentials(selectedServer.value.id)
    .then((data) => {
      credentials.value = data.items || []
    })
    .catch((error) => toast(error.message))
}

function openCredentialForm(type) {
  Object.assign(credentialForm, defaultCredentialForm(type))
  showDataForm.value = true
}

function editCredential(item) {
  Object.assign(credentialForm, defaultCredentialForm(item.credential_type), item, { secret: '' })
  showDataForm.value = true
}

function closeDataForm() {
  showDataForm.value = false
  Object.assign(credentialForm, defaultCredentialForm())
}

function pickCredentialType(event) {
  credentialForm.credential_type = credentialTypeOptions[Number(event.detail.value)].value
}

function saveCredential() {
  if (!credentialForm.name) {
    toast('请填写资料名称')
    return
  }
  credentialSaving.value = true
  const payload = { ...credentialForm }
  if (credentialForm.id && !payload.secret) {
    delete payload.secret
  }
  const action = credentialForm.id ? updateCredential(credentialForm.id, payload) : createCredential(selectedServer.value.id, payload)
  action
    .then(() => {
      toast('资料已保存')
      closeDataForm()
      loadCredentials()
      loadServers()
    })
    .catch((error) => toast(error.message))
    .finally(() => {
      credentialSaving.value = false
    })
}

function copyText(text, message = '已复制') {
  if (!text) {
    toast('暂无可复制内容')
    return
  }
  uni.setClipboardData({
    data: String(text),
    success: () => toast(message)
  })
}

function copyCommand(item) {
  copyText(item.command, '命令已复制')
}

function maskedSecret(item) {
  if (!item.has_secret) {
    return '未保存'
  }
  return revealedSecrets[item.id] || '••••••••'
}

function toggleSecret(item) {
  if (revealedSecrets[item.id]) {
    delete revealedSecrets[item.id]
    return
  }
  revealCredential(item.id)
    .then((data) => {
      if (!data.secret) {
        toast('未保存敏感内容')
        return
      }
      revealedSecrets[item.id] = data.secret
    })
    .catch((error) => toast(error.message))
}

function copySecret(item) {
  revealCredential(item.id)
    .then((data) => {
      if (!data.secret) {
        toast('未保存敏感内容')
        return
      }
      copyText(data.secret, '密码已复制')
    })
    .catch((error) => toast(error.message))
}

function connectionHost(item) {
  const host = item.host || coreIp(selectedServer.value)
  return host || ''
}

function toast(title) {
  uni.showToast({ title: messageLabel(title), icon: 'none' })
}
</script>

<style scoped>
.servers-page {
  min-height: 100vh;
  padding: 22rpx 22rpx 72rpx;
  background: #f5f8fc;
}

button {
  padding: 0;
  border-radius: 0;
  line-height: normal;
}

button::after {
  border: 0;
}

.page-head,
.server-top,
.server-name-row,
.state-row,
.card-actions,
.detail-nav,
.hero-head,
.hero-tags,
.tabs,
.section-head,
.connection-head,
.row-actions,
.compact-row,
.sheet-header,
.sheet-actions {
  display: flex;
  align-items: center;
}

.page-head {
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 18rpx;
}

.head-copy {
  min-width: 0;
}

.page-title {
  color: #172033;
  font-size: 38rpx;
  font-weight: 800;
}

.page-subtitle {
  margin-top: 6rpx;
  color: #66758a;
  font-size: 24rpx;
}

.icon-add {
  width: 68rpx;
  height: 68rpx;
  border-radius: 50%;
  background: #1f6feb;
  color: #ffffff;
  font-size: 42rpx;
  font-weight: 600;
}

.search-card {
  padding: 18rpx;
  border: 1rpx solid #e3eaf3;
  border-radius: 8rpx;
  background: #ffffff;
  box-shadow: 0 8rpx 24rpx rgba(31, 84, 138, 0.06);
}

.search-input {
  height: 76rpx;
  padding: 0 22rpx;
  border-radius: 8rpx;
  background: #f3f6fa;
  color: #172033;
  font-size: 27rpx;
}

.placeholder {
  color: #99a6b6;
}

.filter-row,
.form-steps {
  display: flex;
  gap: 12rpx;
  margin-top: 16rpx;
  overflow-x: auto;
  white-space: nowrap;
}

.filter-pill,
.step-pill {
  flex: 0 0 auto;
  min-width: 96rpx;
  height: 54rpx;
  padding: 0 22rpx;
  border-radius: 999rpx;
  background: #eef3f8;
  color: #536478;
  font-size: 24rpx;
}

.filter-pill.active,
.step-pill.active {
  background: #e8f1ff;
  color: #1f6feb;
  font-weight: 700;
}

.status-text,
.empty-line {
  padding: 28rpx 0;
  color: #7a8797;
  font-size: 25rpx;
  text-align: center;
}

.empty-panel {
  margin-top: 26rpx;
  padding: 56rpx 28rpx;
  border: 1rpx dashed #cdd8e5;
  border-radius: 8rpx;
  background: #ffffff;
  text-align: center;
}

.empty-icon {
  width: 78rpx;
  height: 78rpx;
  margin: 0 auto 16rpx;
  border-radius: 50%;
  background: #eef5ff;
  color: #1f6feb;
  font-size: 46rpx;
  line-height: 78rpx;
}

.empty-title {
  color: #1f2937;
  font-size: 30rpx;
  font-weight: 700;
}

.empty-desc {
  margin-top: 10rpx;
  color: #6a7788;
  font-size: 25rpx;
  line-height: 1.55;
}

.server-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  margin-top: 18rpx;
}

.server-card {
  position: relative;
  overflow: hidden;
  border: 1rpx solid #e1e8f0;
  border-radius: 8rpx;
  background: #ffffff;
  box-shadow: 0 8rpx 24rpx rgba(31, 84, 138, 0.06);
}

.server-card.muted {
  opacity: 0.74;
}

.status-line {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  width: 8rpx;
  background: #2fa66a;
}

.status-maintenance .status-line {
  background: #f59f24;
}

.status-offline .status-line {
  background: #9aa4b2;
}

.server-main {
  padding: 22rpx 22rpx 20rpx 28rpx;
}

.server-top {
  gap: 18rpx;
}

.server-icon {
  flex: 0 0 auto;
  width: 64rpx;
  height: 64rpx;
  border-radius: 8rpx;
  background: #e8f1ff;
  color: #155fc5;
  font-size: 23rpx;
  font-weight: 800;
  line-height: 64rpx;
  text-align: center;
}

.server-icon.large {
  width: 84rpx;
  height: 84rpx;
  font-size: 28rpx;
  line-height: 84rpx;
}

.icon-database {
  background: #e9f8ef;
  color: #198754;
}

.icon-switch,
.icon-nas {
  background: #fff4df;
  color: #b06900;
}

.icon-web,
.icon-cloud {
  background: #eaf3ff;
  color: #1f6feb;
}

.icon-test {
  background: #f1f3f5;
  color: #667085;
}

.server-copy,
.hero-copy {
  min-width: 0;
  flex: 1;
}

.server-name-row {
  gap: 10rpx;
}

.server-name {
  overflow: hidden;
  color: #172033;
  font-size: 31rpx;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.env-tag {
  flex: 0 0 auto;
  padding: 5rpx 12rpx;
  border-radius: 999rpx;
  background: #eef5ff;
  color: #1f6feb;
  font-size: 21rpx;
  font-weight: 700;
}

.state-row {
  gap: 8rpx;
  margin-top: 8rpx;
  color: #657386;
  font-size: 24rpx;
}

.state-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: #2fa66a;
}

.state-dot.maintenance {
  background: #f59f24;
}

.state-dot.offline {
  background: #9aa4b2;
}

.core-ip {
  overflow: hidden;
  margin-left: 8rpx;
  color: #233246;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.purpose-line {
  overflow: hidden;
  margin-top: 16rpx;
  color: #536478;
  font-size: 25rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-actions {
  gap: 12rpx;
  margin-top: 18rpx;
}

.ghost-button,
.primary-light-button,
.more-button,
.primary-button,
.footer-button,
.footer-main {
  min-height: 64rpx;
  border-radius: 8rpx;
  font-size: 25rpx;
  font-weight: 700;
}

.ghost-button {
  flex: 1;
  background: #f3f6fa;
  color: #24415f;
}

.ghost-button.weak {
  color: #788697;
}

.primary-light-button {
  flex: 1;
  background: #e8f1ff;
  color: #1f6feb;
}

.more-button {
  width: 112rpx;
  background: #ffffff;
  color: #607083;
  border: 1rpx solid #dfe7ef;
}

.detail-page {
  position: fixed;
  inset: 0;
  z-index: 20;
  background: #f5f8fc;
}

.detail-scroll {
  height: calc(100vh - 112rpx - env(safe-area-inset-bottom));
  overflow-y: auto;
  padding: 18rpx 22rpx 28rpx;
}

.detail-nav {
  justify-content: space-between;
  min-height: 72rpx;
}

.back-button,
.more-link,
.close-button,
.mini-link,
.text-button,
.text-mini,
.danger-link {
  background: transparent;
}

.back-button {
  width: 72rpx;
  color: #20324a;
  font-size: 56rpx;
}

.detail-nav-title {
  color: #172033;
  font-size: 30rpx;
  font-weight: 800;
}

.more-link {
  width: 92rpx;
  color: #1f6feb;
  font-size: 25rpx;
}

.hero-card,
.info-card,
.connection-card,
.command-card,
.material-card,
.form-card {
  border: 1rpx solid #e1e8f0;
  border-radius: 8rpx;
  background: #ffffff;
}

.hero-card {
  padding: 24rpx;
}

.hero-head {
  gap: 18rpx;
}

.hero-name {
  color: #172033;
  font-size: 36rpx;
  font-weight: 850;
}

.hero-tags {
  gap: 10rpx;
  margin-top: 10rpx;
}

.status-badge {
  padding: 5rpx 13rpx;
  border-radius: 999rpx;
  background: #e8f7ef;
  color: #198754;
  font-size: 22rpx;
  font-weight: 700;
}

.status-badge.maintenance {
  background: #fff4df;
  color: #b06900;
}

.status-badge.offline {
  background: #edf1f5;
  color: #697586;
}

.hero-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
  margin-top: 22rpx;
}

.hero-item {
  min-width: 0;
  padding: 14rpx;
  border-radius: 8rpx;
  background: #f4f7fb;
}

.hero-item text,
.info-row text,
.compact-row text {
  display: block;
  color: #7a8797;
  font-size: 22rpx;
}

.hero-item strong,
.info-row strong,
.compact-row strong {
  display: block;
  overflow: hidden;
  margin-top: 5rpx;
  color: #1f2d3d;
  font-size: 25rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hero-note {
  margin-top: 16rpx;
  color: #344154;
  font-size: 25rpx;
  line-height: 1.55;
}

.muted-note {
  color: #718096;
}

.tabs {
  position: sticky;
  top: 0;
  z-index: 2;
  gap: 8rpx;
  margin: 18rpx -2rpx 14rpx;
  padding: 8rpx 0;
  background: #f5f8fc;
  overflow-x: auto;
}

.tab {
  flex: 0 0 auto;
  min-width: 128rpx;
  height: 60rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  background: #edf2f7;
  color: #5d6c80;
  font-size: 24rpx;
}

.tab.active {
  background: #1f6feb;
  color: #ffffff;
  font-weight: 800;
}

.tab-panel {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.info-card,
.connection-card,
.command-card,
.material-card {
  padding: 20rpx;
}

.section-head {
  justify-content: space-between;
  gap: 16rpx;
  margin: 2rpx 0 4rpx;
}

.section-title {
  color: #172033;
  font-size: 30rpx;
  font-weight: 800;
}

.text-button {
  min-width: 92rpx;
  height: 54rpx;
  border-radius: 999rpx;
  background: #e8f1ff;
  color: #1f6feb;
  font-size: 24rpx;
  font-weight: 700;
}

.info-list {
  margin-top: 12rpx;
}

.info-row,
.compact-row {
  justify-content: space-between;
  gap: 18rpx;
  padding: 18rpx 0;
  border-bottom: 1rpx solid #edf1f5;
}

.info-row:last-child,
.compact-row:last-child {
  border-bottom: 0;
}

.info-row strong {
  max-width: 470rpx;
  text-align: right;
}

.connection-card,
.command-card,
.material-card {
  box-shadow: 0 6rpx 18rpx rgba(31, 84, 138, 0.04);
}

.connection-head {
  justify-content: space-between;
  gap: 18rpx;
}

.connection-title,
.command-title,
.group-title {
  color: #172033;
  font-size: 28rpx;
  font-weight: 800;
}

.connection-meta,
.command-remark,
.connection-remark {
  margin-top: 6rpx;
  color: #6d7b8c;
  font-size: 23rpx;
  line-height: 1.5;
}

.mini-link {
  width: 72rpx;
  color: #1f6feb;
  font-size: 24rpx;
}

.credential-fields {
  margin-top: 12rpx;
}

.compact-row view {
  max-width: 470rpx;
  min-width: 0;
  text-align: right;
}

.secret-value {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10rpx;
}

.text-mini {
  display: inline-block;
  min-width: 56rpx;
  color: #1f6feb;
  font-size: 23rpx;
}

.command-box {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-top: 14rpx;
  padding: 14rpx 16rpx;
  border-radius: 8rpx;
  background: #f2f5f8;
}

.command-box.full {
  margin-top: 12rpx;
}

.command-box text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: #213246;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 23rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.command-box button {
  width: 74rpx;
  height: 46rpx;
  border-radius: 6rpx;
  background: #ffffff;
  color: #1f6feb;
  font-size: 23rpx;
}

.row-actions {
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 14rpx;
}

.ghost-button.small {
  flex: 0 0 auto;
  min-width: 132rpx;
  min-height: 54rpx;
  padding: 0 16rpx;
  font-size: 23rpx;
}

.danger-link {
  min-width: 82rpx;
  height: 54rpx;
  color: #c9352b;
  font-size: 23rpx;
}

.material-group {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.group-title {
  margin: 6rpx 4rpx 0;
  font-size: 25rpx;
}

.detail-footer {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 3;
  display: flex;
  gap: 12rpx;
  padding: 14rpx 22rpx calc(14rpx + env(safe-area-inset-bottom));
  border-top: 1rpx solid #dde5ee;
  background: rgba(255, 255, 255, 0.96);
}

.footer-main {
  flex: 1.4;
  background: #1f6feb;
  color: #ffffff;
}

.footer-button {
  flex: 1;
  background: #edf3fa;
  color: #25415f;
}

.form-mask {
  position: fixed;
  inset: 0;
  z-index: 30;
  display: flex;
  align-items: flex-end;
  background: rgba(20, 31, 45, 0.42);
}

.sheet-panel {
  width: 100%;
  max-height: 90vh;
  padding: 28rpx 28rpx calc(28rpx + env(safe-area-inset-bottom));
  overflow-y: auto;
  border-radius: 18rpx 18rpx 0 0;
  background: #f5f8fc;
}

.sheet-header {
  justify-content: space-between;
  gap: 18rpx;
}

.sheet-title {
  color: #172033;
  font-size: 33rpx;
  font-weight: 850;
}

.sheet-subtitle {
  margin-top: 6rpx;
  color: #6d7b8c;
  font-size: 23rpx;
}

.close-button {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: #e9eef5;
  color: #637083;
  font-size: 36rpx;
}

.form-card {
  margin-top: 18rpx;
  padding: 22rpx;
}

.form-card.soft {
  background: #ffffff;
}

.field + .field {
  margin-top: 20rpx;
}

.field-label {
  margin-bottom: 10rpx;
  color: #344154;
  font-size: 24rpx;
  font-weight: 700;
}

.two-col {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16rpx;
}

.input,
.picker-box {
  box-sizing: border-box;
  width: 100%;
  height: 80rpx;
  padding: 0 20rpx;
  border: 1rpx solid #d9e2ec;
  border-radius: 8rpx;
  background: #ffffff;
  color: #172033;
  font-size: 27rpx;
}

.picker-box {
  line-height: 80rpx;
}

.textarea {
  box-sizing: border-box;
  width: 100%;
  min-height: 150rpx;
  padding: 18rpx 20rpx;
  border: 1rpx solid #d9e2ec;
  border-radius: 8rpx;
  background: #ffffff;
  color: #172033;
  font-size: 27rpx;
  line-height: 1.5;
}

.small-textarea {
  min-height: 108rpx;
}

.icon-picker {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12rpx;
}

.icon-choice {
  min-height: 92rpx;
  border: 1rpx solid #dce5ef;
  border-radius: 8rpx;
  background: #ffffff;
  color: #536478;
  font-size: 22rpx;
}

.icon-choice text {
  display: block;
  color: #1f6feb;
  font-size: 25rpx;
  font-weight: 850;
}

.icon-choice .icon-label {
  display: block;
  margin-top: 6rpx;
}

.icon-choice.active {
  border-color: #1f6feb;
  background: #e8f1ff;
  color: #1f4e85;
}

.share-list {
  display: flex;
  flex-direction: column;
  max-height: 320rpx;
  overflow-y: auto;
  border: 1rpx solid #dce5ef;
  border-radius: 8rpx;
  background: #ffffff;
}

.share-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
  min-height: 82rpx;
  padding: 12rpx 16rpx;
  border-bottom: 1rpx solid #edf1f5;
}

.share-row:last-child {
  border-bottom: 0;
}

.share-copy {
  min-width: 0;
}

.share-name {
  overflow: hidden;
  color: #172033;
  font-size: 26rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.share-meta {
  margin-top: 4rpx;
  color: #728094;
  font-size: 22rpx;
}

.sheet-actions {
  justify-content: flex-end;
  gap: 12rpx;
  margin-top: 18rpx;
}

.sheet-actions .ghost-button,
.sheet-actions .primary-light-button,
.sheet-actions .primary-button {
  flex: 1;
}

.primary-button {
  background: #1f6feb;
  color: #ffffff;
}

.save-button {
  width: 100%;
  margin-top: 18rpx;
}

.servers-page {
  padding: 24rpx 24rpx 72rpx;
  background: #f4f7fb;
}

.page-head {
  margin-bottom: 20rpx;
}

.page-title {
  font-size: 34rpx;
  line-height: 1.2;
  letter-spacing: 0;
}

.page-subtitle {
  font-size: 24rpx;
  line-height: 1.4;
}

.icon-add {
  width: 64rpx;
  height: 64rpx;
  box-shadow: 0 8rpx 18rpx rgba(31, 111, 235, 0.18);
}

.search-card {
  padding: 18rpx 20rpx 20rpx;
  border-color: #e3e9f2;
  border-radius: 8rpx;
  box-shadow: none;
}

.search-input {
  height: 72rpx;
  padding: 0 20rpx;
  font-size: 26rpx;
}

.filter-row {
  gap: 10rpx;
  margin-top: 14rpx;
}

.filter-pill {
  min-width: 88rpx;
  height: 50rpx;
  padding: 0 18rpx;
  font-size: 23rpx;
}

.server-list {
  gap: 14rpx;
  margin-top: 16rpx;
}

.server-card {
  border-color: #e2e8f0;
  box-shadow: none;
}

.server-main {
  padding: 20rpx 20rpx 20rpx 28rpx;
}

.server-top {
  align-items: flex-start;
  gap: 16rpx;
}

.server-icon {
  width: 58rpx;
  height: 58rpx;
  margin-top: 2rpx;
  font-size: 22rpx;
  line-height: 58rpx;
}

.server-name-row {
  min-height: 34rpx;
  align-items: center;
  gap: 8rpx;
}

.server-name {
  font-size: 30rpx;
  line-height: 1.15;
}

.env-tag {
  padding: 4rpx 10rpx;
  font-size: 20rpx;
}

.state-row {
  gap: 8rpx;
  margin-top: 8rpx;
  font-size: 23rpx;
  line-height: 1.3;
}

.core-ip {
  margin-left: 6rpx;
}

.purpose-line {
  margin-top: 14rpx;
  font-size: 24rpx;
  line-height: 1.35;
}

.card-actions {
  display: grid;
  grid-template-columns: 1.15fr 1.15fr 0.75fr;
  gap: 10rpx;
  margin-top: 16rpx;
}

.card-actions .ghost-button,
.card-actions .primary-light-button,
.card-actions .more-button {
  width: 100%;
  min-width: 0;
  min-height: 58rpx;
  border-radius: 7rpx;
  font-size: 24rpx;
}

.card-actions .ghost-button,
.card-actions .more-button {
  background: #f3f6fa;
}

.card-actions .primary-light-button {
  background: #eaf2ff;
}

.detail-page {
  background: #f4f7fb;
}

.detail-scroll {
  height: calc(100vh - 104rpx - env(safe-area-inset-bottom));
  padding: 18rpx 24rpx 28rpx;
}

.detail-nav {
  display: grid;
  grid-template-columns: 88rpx 1fr 88rpx;
  min-height: 64rpx;
  margin-bottom: 8rpx;
}

.back-button {
  width: 64rpx;
  height: 64rpx;
  font-size: 48rpx;
  line-height: 60rpx;
  text-align: left;
}

.detail-nav-title {
  align-self: center;
  font-size: 30rpx;
  line-height: 1.2;
  text-align: center;
}

.more-link {
  justify-self: end;
  width: 88rpx;
  height: 64rpx;
  font-size: 25rpx;
}

.hero-card,
.info-card,
.connection-card,
.command-card,
.material-card {
  border-color: #e2e8f0;
  box-shadow: none;
}

.hero-card {
  padding: 22rpx;
}

.hero-head {
  align-items: flex-start;
  gap: 18rpx;
}

.server-icon.large {
  width: 74rpx;
  height: 74rpx;
  margin-top: 0;
  font-size: 26rpx;
  line-height: 74rpx;
}

.hero-name {
  font-size: 34rpx;
  line-height: 1.18;
}

.hero-tags {
  gap: 8rpx;
  margin-top: 10rpx;
}

.status-badge {
  padding: 4rpx 11rpx;
  font-size: 20rpx;
}

.hero-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10rpx;
  margin-top: 20rpx;
}

.hero-item {
  min-height: 72rpx;
  padding: 12rpx 14rpx;
}

.hero-item text,
.info-row text,
.compact-row text {
  font-size: 22rpx;
  line-height: 1.25;
}

.hero-item strong,
.info-row strong,
.compact-row strong {
  margin-top: 4rpx;
  font-size: 25rpx;
  line-height: 1.25;
}

.hero-note {
  margin-top: 14rpx;
  font-size: 25rpx;
}

.tabs {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8rpx;
  margin: 16rpx 0 14rpx;
  padding: 0;
  overflow: visible;
}

.tab {
  min-width: 0;
  width: 100%;
  height: 58rpx;
  padding: 0;
  font-size: 24rpx;
}

.tab-panel {
  gap: 12rpx;
}

.section-head {
  margin: 4rpx 0 8rpx;
}

.section-title {
  font-size: 29rpx;
  line-height: 1.25;
}

.text-button {
  min-width: 92rpx;
  height: 52rpx;
  font-size: 23rpx;
}

.info-card,
.connection-card,
.command-card,
.material-card {
  padding: 18rpx 20rpx;
}

.connection-head {
  align-items: flex-start;
}

.connection-title,
.command-title {
  font-size: 28rpx;
  line-height: 1.2;
}

.connection-meta,
.command-remark,
.connection-remark {
  font-size: 23rpx;
  line-height: 1.4;
}

.compact-row {
  align-items: flex-start;
  padding: 16rpx 0;
}

.compact-row view {
  max-width: 430rpx;
}

.secret-value {
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 8rpx 12rpx;
}

.text-mini {
  min-width: 52rpx;
  line-height: 1.4;
}

.command-box {
  gap: 12rpx;
  margin-top: 12rpx;
  padding: 12rpx 12rpx 12rpx 14rpx;
}

.command-box text {
  font-size: 22rpx;
  line-height: 1.45;
  white-space: normal;
  word-break: break-all;
}

.command-box button {
  flex: 0 0 auto;
  width: 68rpx;
  height: 44rpx;
  font-size: 22rpx;
}

.row-actions {
  gap: 8rpx;
  margin-top: 12rpx;
}

.ghost-button.small {
  min-width: 116rpx;
  min-height: 50rpx;
  font-size: 22rpx;
}

.danger-link {
  height: 50rpx;
  font-size: 22rpx;
}

.detail-footer {
  gap: 10rpx;
  padding: 12rpx 24rpx calc(12rpx + env(safe-area-inset-bottom));
}

.footer-main,
.footer-button {
  min-height: 60rpx;
  border-radius: 7rpx;
  font-size: 24rpx;
}

.action-mask {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  align-items: flex-end;
  background: rgba(21, 31, 44, 0.42);
}

.action-panel {
  width: 100%;
  padding: 14rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));
  border-radius: 18rpx 18rpx 0 0;
  background: #ffffff;
}

.action-handle {
  width: 72rpx;
  height: 8rpx;
  margin: 0 auto 18rpx;
  border-radius: 999rpx;
  background: #d8dee8;
}

.action-title {
  overflow: hidden;
  margin-bottom: 8rpx;
  color: #1d2939;
  font-size: 28rpx;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.action-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  min-height: 88rpx;
  padding: 14rpx 0;
  border-bottom: 1rpx solid #eef2f6;
  background: #ffffff;
  text-align: left;
}

.action-row.danger .action-label {
  color: #c9352b;
}

.action-label {
  display: block;
  color: #1f2d3d;
  font-size: 27rpx;
  font-weight: 700;
  line-height: 1.25;
}

.action-desc {
  display: block;
  margin-top: 5rpx;
  color: #7a8797;
  font-size: 22rpx;
  line-height: 1.35;
}

.action-arrow {
  flex: 0 0 auto;
  color: #a4adba;
  font-size: 42rpx;
}

.action-cancel {
  width: 100%;
  height: 66rpx;
  margin-top: 14rpx;
  border-radius: 8rpx;
  background: #f3f6fa;
  color: #344154;
  font-size: 26rpx;
  font-weight: 700;
}

/* Final mobile asset UI pass: one spacing, type, and control system. */
.servers-page,
.detail-page,
.sheet-panel,
.action-panel {
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
  color: #172033;
}

.servers-page {
  padding: 28rpx 30rpx 84rpx;
  background: #f5f7fb;
}

button,
input,
textarea {
  font-family: inherit;
}

.page-head {
  align-items: center;
  margin: 6rpx 0 22rpx;
}

.page-title {
  font-size: 34rpx;
  font-weight: 800;
  line-height: 1.18;
}

.page-subtitle {
  margin-top: 8rpx;
  color: #6b778a;
  font-size: 24rpx;
  line-height: 1.3;
}

.icon-add {
  width: 62rpx;
  height: 62rpx;
  border-radius: 50%;
  background: #4169e1;
  color: #fff;
  font-size: 40rpx;
  font-weight: 700;
  line-height: 58rpx;
  text-align: center;
  box-shadow: 0 10rpx 22rpx rgba(65, 105, 225, 0.24);
}

.search-card {
  padding: 18rpx;
  border: 1rpx solid #e5ebf3;
  border-radius: 8rpx;
  background: #ffffff;
  box-shadow: 0 4rpx 12rpx rgba(38, 61, 92, 0.04);
}

.search-input {
  box-sizing: border-box;
  height: 70rpx;
  padding: 0 22rpx;
  border-radius: 7rpx;
  background: #f3f6fa;
  color: #1f2d3d;
  font-size: 26rpx;
  line-height: 70rpx;
}

.filter-row {
  gap: 10rpx;
  margin-top: 14rpx;
}

.filter-pill {
  min-width: 86rpx;
  height: 50rpx;
  padding: 0 18rpx;
  border-radius: 8rpx;
  background: #eef3f8;
  color: #596a7d;
  font-size: 24rpx;
  font-weight: 650;
  line-height: 50rpx;
}

.filter-pill.active {
  background: #e8f0ff;
  color: #4169e1;
}

.server-list {
  gap: 16rpx;
  margin-top: 16rpx;
}

.server-card {
  border: 1rpx solid #e4eaf2;
  border-radius: 7rpx;
  background: #ffffff;
  box-shadow: 0 6rpx 18rpx rgba(28, 49, 78, 0.04);
}

.server-card.muted {
  opacity: 0.72;
}

.status-line {
  width: 6rpx;
  background: #46b676;
}

.status-maintenance .status-line {
  background: #f0a23a;
}

.status-offline .status-line {
  background: #a5adba;
}

.server-main {
  padding: 20rpx 20rpx 20rpx 28rpx;
}

.server-top {
  align-items: flex-start;
  gap: 16rpx;
}

.server-icon {
  width: 58rpx;
  height: 58rpx;
  margin-top: 2rpx;
  border-radius: 7rpx;
  background: #edf3ff;
  color: #4169e1;
  font-size: 22rpx;
  font-weight: 800;
  line-height: 58rpx;
}

.server-name-row {
  min-height: 36rpx;
  gap: 8rpx;
}

.server-name {
  font-size: 30rpx;
  font-weight: 800;
  line-height: 1.2;
}

.env-tag {
  padding: 4rpx 10rpx;
  border-radius: 6rpx;
  background: #eef4ff;
  color: #4169e1;
  font-size: 20rpx;
  font-weight: 750;
}

.state-row {
  gap: 8rpx;
  margin-top: 8rpx;
  color: #64748b;
  font-size: 23rpx;
  line-height: 1.35;
}

.state-dot {
  width: 12rpx;
  height: 12rpx;
}

.core-ip {
  margin-left: 4rpx;
  color: #253449;
  font-weight: 760;
}

.purpose-line {
  margin-top: 14rpx;
  color: #66758a;
  font-size: 24rpx;
  line-height: 1.35;
}

.card-actions {
  display: grid;
  grid-template-columns: 1.1fr 1.1fr 0.72fr;
  gap: 10rpx;
  margin-top: 16rpx;
}

.card-actions .ghost-button,
.card-actions .primary-light-button,
.card-actions .more-button {
  width: 100%;
  min-width: 0;
  min-height: 58rpx;
  border-radius: 7rpx;
  font-size: 24rpx;
  font-weight: 760;
  line-height: 58rpx;
}

.card-actions .ghost-button,
.card-actions .more-button {
  background: #f2f5f9;
  color: #253449;
}

.card-actions .primary-light-button {
  background: #eaf1ff;
  color: #4169e1;
}

.detail-page {
  background: #f5f7fb;
}

.detail-scroll {
  height: calc(100vh - 104rpx - env(safe-area-inset-bottom));
  padding: 18rpx 30rpx 28rpx;
}

.detail-nav {
  display: grid;
  grid-template-columns: 72rpx minmax(0, 1fr) 72rpx;
  min-height: 64rpx;
  margin-bottom: 10rpx;
}

.back-button {
  width: 64rpx;
  height: 64rpx;
  color: #1f2d3d;
  font-size: 48rpx;
  line-height: 58rpx;
  text-align: left;
}

.detail-nav-title {
  align-self: center;
  overflow: hidden;
  color: #172033;
  font-size: 30rpx;
  font-weight: 800;
  line-height: 1.2;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.more-link {
  justify-self: end;
  width: 72rpx;
  height: 64rpx;
  color: #4169e1;
  font-size: 24rpx;
  font-weight: 650;
  line-height: 64rpx;
}

.hero-card,
.info-card,
.connection-card,
.command-card,
.material-card,
.form-card {
  border: 1rpx solid #e4eaf2;
  border-radius: 8rpx;
  background: #ffffff;
  box-shadow: 0 4rpx 12rpx rgba(38, 61, 92, 0.035);
}

.hero-card {
  padding: 22rpx;
}

.hero-head {
  align-items: flex-start;
  gap: 18rpx;
}

.server-icon.large {
  width: 74rpx;
  height: 74rpx;
  font-size: 26rpx;
  line-height: 74rpx;
}

.hero-name {
  font-size: 34rpx;
  font-weight: 850;
  line-height: 1.18;
}

.status-badge {
  padding: 4rpx 11rpx;
  border-radius: 6rpx;
  font-size: 21rpx;
}

.hero-grid {
  gap: 10rpx;
  margin-top: 20rpx;
}

.hero-item {
  min-height: 72rpx;
  padding: 12rpx 14rpx;
  border-radius: 7rpx;
  background: #f4f7fb;
}

.hero-item text,
.info-row text,
.compact-row text {
  color: #8a96a8;
  font-size: 22rpx;
  font-weight: 600;
  line-height: 1.25;
}

.hero-item strong,
.info-row strong,
.compact-row strong {
  margin-top: 4rpx;
  color: #1f2d3d;
  font-size: 25rpx;
  font-weight: 650;
  line-height: 1.28;
}

.hero-note {
  margin-top: 14rpx;
  color: #475569;
  font-size: 25rpx;
  line-height: 1.5;
}

.tabs {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 0;
  margin: 18rpx 0 14rpx;
  padding: 0;
  background: transparent;
  overflow: visible;
}

.tab {
  position: relative;
  min-width: 0;
  width: 100%;
  height: 62rpx;
  border-radius: 0;
  background: transparent;
  color: #596a7d;
  font-size: 25rpx;
  font-weight: 700;
  line-height: 62rpx;
}

.tab.active {
  background: transparent;
  color: #4169e1;
}

.tab.active::after {
  position: absolute;
  right: 24rpx;
  bottom: 0;
  left: 24rpx;
  height: 4rpx;
  border-radius: 999rpx;
  background: #4169e1;
  content: "";
}

.section-title {
  font-size: 29rpx;
  font-weight: 800;
  line-height: 1.25;
}

.info-card,
.connection-card,
.command-card,
.material-card {
  padding: 20rpx;
}

.connection-head {
  align-items: flex-start;
}

.connection-title,
.command-title,
.group-title {
  font-size: 28rpx;
  font-weight: 800;
  line-height: 1.22;
}

.connection-meta,
.command-remark,
.connection-remark {
  color: #7a8797;
  font-size: 23rpx;
  line-height: 1.42;
}

.compact-row,
.info-row {
  align-items: flex-start;
  padding: 16rpx 0;
}

.compact-row view {
  max-width: 430rpx;
}

.command-box {
  border-radius: 7rpx;
  background: #f3f6fa;
}

.command-box text {
  color: #253449;
  font-size: 22rpx;
  line-height: 1.45;
  white-space: normal;
  word-break: break-all;
}

.detail-footer {
  gap: 10rpx;
  padding: 12rpx 30rpx calc(12rpx + env(safe-area-inset-bottom));
}

.footer-main,
.footer-button {
  min-height: 60rpx;
  border-radius: 7rpx;
  font-size: 25rpx;
  font-weight: 800;
  line-height: 60rpx;
}

.footer-main {
  background: #4169e1;
}

.footer-button {
  background: #edf3fa;
  color: #253449;
}

.action-mask,
.form-mask {
  background: rgba(20, 31, 45, 0.52);
}

.action-panel {
  padding: 14rpx 30rpx calc(18rpx + env(safe-area-inset-bottom));
  border-radius: 18rpx 18rpx 0 0;
}

.action-title {
  margin-bottom: 8rpx;
  font-size: 28rpx;
  font-weight: 800;
}

.action-row {
  box-sizing: border-box;
  min-height: 88rpx;
  padding: 14rpx 0;
}

.action-label {
  color: #172033;
  font-size: 27rpx;
  font-weight: 760;
}

.action-desc {
  color: #7a8797;
  font-size: 22rpx;
}

.sheet-panel {
  max-height: 88vh;
  padding: 22rpx 30rpx calc(24rpx + env(safe-area-inset-bottom));
  border-radius: 18rpx 18rpx 0 0;
  background: #f5f7fb;
}

.sheet-title {
  font-size: 31rpx;
  font-weight: 850;
  line-height: 1.2;
}

.sheet-subtitle {
  font-size: 23rpx;
  line-height: 1.35;
}

.close-button {
  width: 58rpx;
  height: 58rpx;
  border-radius: 50%;
  font-size: 34rpx;
  line-height: 54rpx;
}

.form-card {
  margin-top: 16rpx;
  padding: 20rpx;
}

.form-section-title {
  margin-bottom: 18rpx;
  color: #172033;
  font-size: 28rpx;
  font-weight: 800;
  line-height: 1.2;
}

.notice-box {
  margin-bottom: 18rpx;
  padding: 14rpx 16rpx;
  border-radius: 7rpx;
  background: #eef4ff;
  color: #52657a;
  font-size: 23rpx;
  line-height: 1.45;
}

.field + .field {
  margin-top: 18rpx;
}

.field-label {
  margin-bottom: 10rpx;
  color: #52657a;
  font-size: 23rpx;
  font-weight: 700;
}

.input,
.picker-box {
  height: 76rpx;
  padding: 0 18rpx;
  border: 1rpx solid #dfe7ef;
  border-radius: 7rpx;
  background: #ffffff;
  color: #172033;
  font-size: 26rpx;
  line-height: 76rpx;
}

.textarea {
  min-height: 142rpx;
  padding: 16rpx 18rpx;
  border: 1rpx solid #dfe7ef;
  border-radius: 7rpx;
  font-size: 26rpx;
}

.icon-picker {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10rpx;
}

.icon-choice {
  min-height: 84rpx;
  border-radius: 7rpx;
  font-size: 21rpx;
}

.share-row {
  min-height: 78rpx;
}

.sheet-actions {
  gap: 12rpx;
  margin-top: 18rpx;
}

.sheet-actions .ghost-button,
.sheet-actions .primary-button {
  min-height: 64rpx;
  border-radius: 7rpx;
  font-size: 25rpx;
  font-weight: 800;
  line-height: 64rpx;
}

.sheet-actions .ghost-button {
  background: #edf3fa;
  color: #253449;
}

.sheet-actions .primary-button,
.primary-button {
  background: #4169e1;
  color: #ffffff;
}

/* Keyring UI: compact server information wallet. */
.keyring-page,
.detail-page,
.sheet-panel {
  min-height: 100vh;
  background: #f5f7fb;
  color: #1f2937;
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.keyring-page {
  padding: 30rpx 30rpx 88rpx;
}

.keyring-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  padding-top: 6rpx;
}

.keyring-title {
  color: #111827;
  font-size: 40rpx;
  font-weight: 850;
  line-height: 1.15;
}

.keyring-subtitle {
  margin-top: 10rpx;
  color: #667085;
  font-size: 25rpx;
  line-height: 1.3;
}

.round-add {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: #3458e6;
  color: #ffffff;
  font-size: 42rpx;
  font-weight: 650;
  line-height: 60rpx;
  text-align: center;
  box-shadow: 0 10rpx 22rpx rgba(52, 88, 230, 0.22);
}

.simple-search {
  display: flex;
  align-items: center;
  gap: 14rpx;
  height: 72rpx;
  margin-top: 28rpx;
  padding: 0 22rpx;
  border: 1rpx solid #e5e7eb;
  border-radius: 16rpx;
  background: #ffffff;
}

.search-mark {
  position: relative;
  width: 28rpx;
  height: 28rpx;
  border: 3rpx solid #9ca3af;
  border-radius: 50%;
}

.search-mark::after {
  position: absolute;
  right: -8rpx;
  bottom: -6rpx;
  width: 12rpx;
  height: 3rpx;
  border-radius: 999rpx;
  background: #9ca3af;
  transform: rotate(45deg);
  content: "";
}

.simple-search-input {
  flex: 1;
  height: 70rpx;
  color: #1f2937;
  font-size: 26rpx;
  line-height: 70rpx;
}

.keyring-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 28rpx;
}

.keyring-card {
  display: flex;
  gap: 22rpx;
  padding: 24rpx 24rpx 20rpx;
  border: 1rpx solid #e5e7eb;
  border-radius: 14rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 24rpx rgba(15, 23, 42, 0.04);
}

.keyring-main {
  min-width: 0;
  flex: 1;
}

.keyring-line {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
}

.keyring-name {
  min-width: 0;
  overflow: hidden;
  color: #111827;
  font-size: 31rpx;
  font-weight: 850;
  line-height: 1.22;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.keyring-purpose {
  overflow: hidden;
  margin-top: 14rpx;
  color: #667085;
  font-size: 26rpx;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.env-chip {
  flex: 0 0 auto;
  padding: 5rpx 12rpx;
  border-radius: 8rpx;
  background: #eef4ff;
  color: #3458e6;
  font-size: 22rpx;
  font-weight: 760;
  line-height: 1.2;
}

.env-test {
  background: #ecfdf3;
  color: #16915a;
}

.env-staging {
  background: #fff7ed;
  color: #e07a17;
}

.env-backup {
  background: #f3f4f6;
  color: #667085;
}

.ssh-copy-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  min-width: 188rpx;
  height: 58rpx;
  margin-top: 24rpx;
  border-radius: 10rpx;
  background: #eef4ff;
  color: #3458e6;
  font-size: 25rpx;
  font-weight: 780;
  line-height: 58rpx;
}

.terminal-mini {
  position: relative;
  width: 28rpx;
  height: 28rpx;
  border-radius: 5rpx;
  background: #3458e6;
}

.terminal-mini::before {
  position: absolute;
  top: 8rpx;
  left: 7rpx;
  width: 8rpx;
  height: 8rpx;
  border-top: 3rpx solid #ffffff;
  border-right: 3rpx solid #ffffff;
  transform: rotate(45deg);
  content: "";
}

.asset-icon {
  position: relative;
  flex: 0 0 auto;
  width: 76rpx;
  height: 76rpx;
  border-radius: 18rpx;
  background: #eef4ff;
  color: #3458e6;
}

.asset-icon.large {
  width: 86rpx;
  height: 86rpx;
}

.asset-icon .icon-glyph {
  position: absolute;
  inset: 20rpx;
  border: 4rpx solid currentColor;
  border-radius: 7rpx;
}

.asset-icon .icon-glyph::before,
.asset-icon .icon-glyph::after {
  position: absolute;
  right: 6rpx;
  left: 6rpx;
  height: 3rpx;
  border-radius: 999rpx;
  background: currentColor;
  content: "";
}

.asset-icon .icon-glyph::before {
  top: 8rpx;
}

.asset-icon .icon-glyph::after {
  bottom: 8rpx;
}

.asset-icon-database {
  background: #ecfdf3;
  color: #16a05d;
}

.asset-icon-database .icon-glyph {
  border-radius: 50%;
  border-top-width: 5rpx;
  border-bottom-width: 5rpx;
}

.asset-icon-web {
  background: #fff7ed;
  color: #f08a24;
}

.asset-icon-web .icon-glyph {
  border-radius: 50%;
}

.asset-icon-web .icon-glyph::before {
  top: 50%;
  right: -3rpx;
  left: -3rpx;
}

.asset-icon-web .icon-glyph::after {
  top: -3rpx;
  bottom: -3rpx;
  left: 50%;
  width: 3rpx;
  height: auto;
}

.asset-icon-switch {
  background: #f4f0ff;
  color: #7c3aed;
}

.asset-icon-nas {
  background: #eefcff;
  color: #0ea5a8;
}

.asset-icon-cloud {
  background: #f1f5f9;
  color: #64748b;
}

.asset-icon-cloud .icon-glyph {
  inset: 24rpx 18rpx 22rpx;
  border-top-color: transparent;
  border-radius: 999rpx;
}

.asset-icon-test,
.asset-icon-other {
  background: #f3f4f6;
  color: #6b7280;
}

.keyring-detail-scroll {
  height: calc(100vh - 106rpx - env(safe-area-inset-bottom));
  overflow-y: auto;
  padding: 18rpx 30rpx 30rpx;
}

.keyring-detail-nav {
  display: grid;
  grid-template-columns: 72rpx minmax(0, 1fr) 72rpx;
  align-items: center;
  min-height: 72rpx;
  margin-bottom: 14rpx;
}

.back-button {
  width: 60rpx;
  height: 60rpx;
  color: #111827;
  font-size: 48rpx;
  line-height: 56rpx;
  text-align: left;
}

.detail-nav-title {
  overflow: hidden;
  color: #111827;
  font-size: 31rpx;
  font-weight: 850;
  line-height: 1.22;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.nav-edit {
  width: 72rpx;
  height: 60rpx;
  background: transparent;
  color: #3458e6;
  font-size: 25rpx;
  font-weight: 720;
  line-height: 60rpx;
}

.summary-card,
.plain-card,
.compact-connection-card,
.command-line-card,
.material-card.compact,
.remark-card {
  border: 1rpx solid #e5e7eb;
  border-radius: 14rpx;
  background: #ffffff;
  box-shadow: 0 8rpx 22rpx rgba(15, 23, 42, 0.035);
}

.summary-card {
  padding: 22rpx;
}

.summary-top {
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
}

.summary-title-area {
  min-width: 0;
  flex: 1;
}

.summary-name {
  overflow: hidden;
  color: #111827;
  font-size: 33rpx;
  font-weight: 850;
  line-height: 1.22;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-purpose {
  overflow: hidden;
  margin-top: 10rpx;
  color: #667085;
  font-size: 25rpx;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx 28rpx;
  margin-top: 24rpx;
}

.summary-field {
  min-width: 0;
}

.summary-field.wide {
  grid-column: 1 / -1;
}

.summary-field text,
.plain-row text,
.record-line text {
  display: block;
  color: #9ca3af;
  font-size: 22rpx;
  font-weight: 650;
  line-height: 1.25;
}

.summary-field strong,
.plain-row strong,
.record-line strong {
  display: block;
  overflow: hidden;
  margin-top: 7rpx;
  color: #1f2937;
  font-size: 25rpx;
  font-weight: 620;
  line-height: 1.3;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.detail-section {
  margin-top: 26rpx;
}

.section-head.compact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.section-title {
  color: #111827;
  font-size: 29rpx;
  font-weight: 850;
  line-height: 1.25;
}

.section-add {
  min-width: 96rpx;
  height: 46rpx;
  background: transparent;
  color: #3458e6;
  font-size: 24rpx;
  font-weight: 720;
  line-height: 46rpx;
  text-align: right;
}

.plain-card {
  padding: 4rpx 20rpx;
}

.plain-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  min-height: 68rpx;
  border-bottom: 1rpx solid #f0f2f5;
}

.plain-row:last-child {
  border-bottom: 0;
}

.plain-row text {
  flex: 0 0 auto;
}

.plain-row strong {
  margin-top: 0;
  text-align: right;
}

.compact-connection-card,
.material-card.compact {
  padding: 20rpx;
}

.compact-connection-card + .compact-connection-card,
.material-card.compact + .material-card.compact,
.command-line-card + .command-line-card {
  margin-top: 14rpx;
}

.record-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
}

.record-title {
  display: inline-block;
  margin-right: 10rpx;
  color: #111827;
  font-size: 29rpx;
  font-weight: 850;
  line-height: 1.25;
}

.type-chip {
  display: inline-block;
  padding: 4rpx 10rpx;
  border-radius: 8rpx;
  background: #ecfdf3;
  color: #148a56;
  font-size: 20rpx;
  font-weight: 720;
  line-height: 1.2;
}

.record-edit {
  width: 70rpx;
  height: 42rpx;
  background: transparent;
  color: #3458e6;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 42rpx;
  text-align: right;
}

.record-lines {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx 24rpx;
  margin-top: 18rpx;
}

.record-line {
  min-width: 0;
}

.secret-line {
  grid-column: 1 / -1;
}

.secret-tools {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 7rpx;
}

.secret-tools strong {
  flex: 1;
  min-width: 0;
  margin-top: 0;
}

.icon-action {
  position: relative;
  width: 42rpx;
  height: 42rpx;
  background: transparent;
}

.icon-action.eye::before {
  position: absolute;
  top: 12rpx;
  left: 5rpx;
  width: 30rpx;
  height: 18rpx;
  border: 3rpx solid #111827;
  border-radius: 50%;
  content: "";
}

.icon-action.eye::after {
  position: absolute;
  top: 17rpx;
  left: 16rpx;
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: #111827;
  content: "";
}

.icon-action.copy::before,
.icon-action.copy::after {
  position: absolute;
  width: 20rpx;
  height: 24rpx;
  border: 3rpx solid #111827;
  border-radius: 4rpx;
  content: "";
}

.icon-action.copy::before {
  top: 8rpx;
  left: 14rpx;
}

.icon-action.copy::after {
  top: 14rpx;
  left: 7rpx;
  background: #ffffff;
}

.record-remark {
  margin-top: 14rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.5;
}

.command-box {
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-top: 16rpx;
  padding: 14rpx 12rpx 14rpx 16rpx;
  border-radius: 10rpx;
  background: #f3f4f6;
}

.command-box.slim {
  margin-top: 8rpx;
}

.command-box text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  color: #1f2937;
  font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  font-size: 22rpx;
  line-height: 1.45;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.command-box button {
  flex: 0 0 auto;
  width: 66rpx;
  height: 44rpx;
  border-radius: 8rpx;
  background: #ffffff;
  color: #3458e6;
  font-size: 22rpx;
  font-weight: 700;
  line-height: 44rpx;
}

.command-line-card {
  padding: 16rpx 18rpx;
}

.command-line-title {
  color: #374151;
  font-size: 24rpx;
  font-weight: 720;
  line-height: 1.3;
}

.remark-card {
  padding: 18rpx 20rpx;
  color: #4b5563;
  font-size: 25rpx;
  line-height: 1.55;
}

.empty-line {
  padding: 20rpx 0;
  color: #9ca3af;
  font-size: 24rpx;
  text-align: left;
}

.detail-footer {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 3;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14rpx;
  padding: 14rpx 30rpx calc(14rpx + env(safe-area-inset-bottom));
  border-top: 1rpx solid #e5e7eb;
  background: rgba(255, 255, 255, 0.96);
}

.footer-main,
.footer-button {
  min-height: 64rpx;
  border-radius: 10rpx;
  font-size: 26rpx;
  font-weight: 800;
  line-height: 64rpx;
}

.footer-main {
  background: #3458e6;
  color: #ffffff;
}

.footer-button {
  border: 1rpx solid #3458e6;
  background: #ffffff;
  color: #3458e6;
}

.detail-footer .footer-main:only-child {
  grid-column: 1 / -1;
}

.form-icon {
  width: 46rpx;
  height: 46rpx;
  margin: 0 auto 6rpx;
  border-radius: 12rpx;
}

.form-icon .icon-glyph {
  inset: 12rpx;
  border-width: 3rpx;
}

.icon-choice text:first-child {
  display: none;
}

.icon-choice .icon-label {
  color: #52657a;
  font-size: 20rpx;
  font-weight: 650;
}

/* Final keyring reduction overrides. */
.keyring-page {
  padding: 34rpx 30rpx 72rpx;
  background: #f4f6fa;
}

.group-filter {
  width: 100%;
  margin-top: 20rpx;
  white-space: nowrap;
}

.group-pill {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  height: 56rpx;
  margin-right: 12rpx;
  padding: 0 18rpx;
  border-radius: 999rpx;
  background: #eef1f6;
  color: #667085;
  font-size: 24rpx;
  font-weight: 700;
  line-height: 56rpx;
}

.group-pill.active {
  background: #3458e6;
  color: #ffffff;
  box-shadow: 0 8rpx 18rpx rgba(52, 88, 230, 0.18);
}

.pill-icon,
.summary-meta-item .pill-icon {
  position: relative;
  display: inline-block;
  width: 26rpx;
  height: 26rpx;
  color: currentColor;
}

.group-mini::before,
.group-mini::after {
  position: absolute;
  left: 3rpx;
  width: 20rpx;
  height: 6rpx;
  border: 2rpx solid currentColor;
  border-radius: 4rpx;
  content: "";
}

.group-mini::before {
  top: 4rpx;
}

.group-mini::after {
  bottom: 4rpx;
}

.share-mini::before,
.share-mini::after {
  position: absolute;
  border: 2rpx solid currentColor;
  border-radius: 50%;
  content: "";
}

.share-mini::before {
  top: 5rpx;
  left: 2rpx;
  width: 10rpx;
  height: 10rpx;
}

.share-mini::after {
  right: 1rpx;
  bottom: 4rpx;
  width: 12rpx;
  height: 12rpx;
}

.keyring-list {
  margin-top: 22rpx;
}

.keyring-card {
  align-items: center;
  min-height: 118rpx;
  padding: 22rpx 24rpx;
  border-color: #e8edf4;
  border-radius: 12rpx;
  box-shadow: 0 8rpx 20rpx rgba(16, 24, 40, 0.035);
}

.keyring-line {
  align-items: center;
}

.keyring-ip {
  margin-top: 10rpx;
  color: #475467;
  font-size: 25rpx;
  font-weight: 620;
  line-height: 1.25;
}

.keyring-purpose {
  margin-top: 8rpx;
}

.env-chip {
  padding: 4rpx 10rpx;
  border-radius: 7rpx;
  font-size: 20rpx;
  font-weight: 760;
}

.keyring-detail-scroll {
  height: 100vh;
  padding: 18rpx 30rpx calc(34rpx + env(safe-area-inset-bottom));
}

.summary-card {
  padding: 22rpx;
  border-color: #e8edf4;
  border-radius: 12rpx;
  box-shadow: 0 8rpx 20rpx rgba(16, 24, 40, 0.035);
}

.summary-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 18rpx 22rpx;
  margin-top: 22rpx;
}

.summary-field text,
.record-line text {
  color: #98a2b3;
  font-size: 21rpx;
}

.summary-field strong,
.record-line strong {
  color: #1d2939;
  font-size: 24rpx;
}

.summary-flags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 18rpx;
}

.ufw-chip {
  padding: 7rpx 14rpx;
  border-radius: 999rpx;
  background: #e8f7ee;
  color: #15905b;
  font-size: 22rpx;
  font-weight: 760;
  line-height: 1.2;
}

.summary-meta {
  display: flex;
  justify-content: space-between;
  gap: 18rpx;
  margin-top: 20rpx;
  padding-top: 18rpx;
  border-top: 1rpx solid #eef2f6;
}

.summary-meta-item {
  display: inline-flex;
  align-items: center;
  min-width: 0;
  gap: 8rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.3;
}

.compact-connection-card {
  padding: 22rpx;
  border-color: #e8edf4;
  border-radius: 12rpx;
}

.record-title-wrap {
  display: grid;
  grid-template-columns: 52rpx minmax(0, 1fr) auto;
  align-items: center;
  min-width: 0;
  column-gap: 12rpx;
}

.record-type-icon {
  position: relative;
  width: 52rpx;
  height: 52rpx;
  border-radius: 10rpx;
  background: #eef4ff;
  color: #3458e6;
}

.record-type-icon .icon-glyph {
  position: absolute;
  inset: 14rpx;
  border: 3rpx solid currentColor;
  border-radius: 5rpx;
}

.record-type-icon .icon-glyph::before,
.record-type-icon .icon-glyph::after {
  position: absolute;
  right: 4rpx;
  left: 4rpx;
  height: 2rpx;
  border-radius: 999rpx;
  background: currentColor;
  content: "";
}

.record-type-icon .icon-glyph::before {
  top: 6rpx;
}

.record-type-icon .icon-glyph::after {
  bottom: 6rpx;
}

.record-type-mysql,
.record-type-database,
.record-type-redis {
  background: #ecfdf3;
  color: #16a05d;
}

.record-type-web,
.record-type-api {
  background: #f4f0ff;
  color: #7c3aed;
}

.record-type-switch {
  background: #fff7ed;
  color: #f08a24;
}

.record-title {
  overflow: hidden;
  margin-right: 0;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.record-lines {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx 18rpx;
}

.secret-line {
  grid-column: 1 / -1;
}

.secret-tools {
  gap: 10rpx;
}

.icon-action {
  width: 44rpx;
  height: 44rpx;
  border-radius: 8rpx;
  color: #667085;
}

.icon-action.eye::before {
  top: 13rpx;
  left: 5rpx;
  width: 30rpx;
  height: 17rpx;
  border-width: 2rpx;
  border-radius: 999rpx 999rpx 10rpx 10rpx;
  transform: rotate(0deg);
}

.icon-action.eye::after {
  top: 18rpx;
  left: 17rpx;
  width: 8rpx;
  height: 8rpx;
  background: #667085;
}

.icon-action.copy::before,
.icon-action.copy::after {
  border-width: 2rpx;
  border-color: #667085;
}

.command-box {
  padding: 12rpx 10rpx 12rpx 16rpx;
  border-radius: 8rpx;
  background: #f2f4f7;
}

.command-box text {
  white-space: normal;
}

.command-box button {
  color: #3458e6;
}

.detail-close {
  min-width: 92rpx;
  height: 56rpx;
  padding: 0 16rpx;
  border-radius: 28rpx;
  background: #eef3f8;
  color: #53687e;
  font-size: 22rpx;
  line-height: 56rpx;
}

.privacy-chip {
  margin-left: 10rpx;
  padding: 6rpx 10rpx;
  border-radius: 8rpx;
  background: #edf5ff;
  color: #5077a2;
  font-size: 19rpx;
}
</style>
