<template>
  <view class="page manage-page">
    <view class="compact-bar">
      <view>
        <view class="bar-title">用户管理</view>
        <view class="bar-subtitle">共 {{ total }} 人</view>
      </view>
      <view class="bar-actions">
        <button class="ghost-button" @tap="showFilters = !showFilters">
          {{ showFilters ? '收起筛选' : filterSummary }}
        </button>
        <button class="add-button" @tap="openCreate"><text>+</text></button>
      </view>
    </view>

    <view class="search-row">
      <input
        v-model.trim="keyword"
        class="search-input"
        placeholder="姓名 / 手机号 / OSS 账号"
        placeholder-class="placeholder"
        confirm-type="search"
        @confirm="loadUsers"
      />
      <button class="search-button" @tap="loadUsers">搜索</button>
    </view>

    <view v-if="showFilters" class="filter-panel">
      <picker :range="filterOrgOptions" range-key="label" @change="onFilterOrgChange">
        <view class="filter-pill">{{ selectedFilterOrgName }}</view>
      </picker>
      <picker :range="filterRoleOptions" range-key="label" @change="onFilterChange('role_code', filterRoleOptions, $event)">
        <view class="filter-pill">{{ labelOf(filters.role_code, filterRoleOptions, '全部角色') }}</view>
      </picker>
      <picker :range="filterUserTypeOptions" range-key="label" @change="onFilterChange('user_type', filterUserTypeOptions, $event)">
        <view class="filter-pill">{{ labelOf(filters.user_type, filterUserTypeOptions, '全部类型') }}</view>
      </picker>
      <picker :range="filterStatusOptions" range-key="label" @change="onFilterChange('status', filterStatusOptions, $event)">
        <view class="filter-pill">{{ labelOf(filters.status, filterStatusOptions, '全部状态') }}</view>
      </picker>
      <picker :range="filterOssOptions" range-key="label" @change="onFilterChange('oss_bind_status', filterOssOptions, $event)">
        <view class="filter-pill">{{ labelOf(filters.oss_bind_status, filterOssOptions, '全部OSS') }}</view>
      </picker>
      <button class="clear-button" @tap="clearFilters">清空筛选</button>
    </view>

    <view v-if="loading" class="status-text">加载中...</view>
    <view v-else-if="users.length === 0" class="panel empty-panel">暂无用户</view>

    <view v-else class="list">
      <view v-for="item in users" :key="item.id" class="panel item-card">
        <view class="item-head">
          <view class="item-title">{{ item.real_name }}</view>
          <text class="tag" :class="{ danger: item.status !== 'active' }">{{ statusLabel(item.status) }}</text>
        </view>
        <view class="item-meta">{{ item.mobile }}｜{{ item.org_name || '未分配组织' }}</view>
        <view class="tag-row">
          <text class="tag">{{ roleLabel(item.role_code) }}</text>
          <text class="tag">{{ userTypeLabel(item.user_type) }}</text>
          <text class="tag">{{ ossStatusLabel(item.oss_bind_status) }}</text>
        </view>
        <view class="action-row">
          <button class="secondary-button mini-button" @tap="openEdit(item)">编辑</button>
          <button class="secondary-button mini-button" @tap="toggleStatus(item)">
            {{ item.status === 'active' ? '禁用' : '启用' }}
          </button>
          <button class="secondary-button mini-button" @tap="resetUserPassword(item)">重置</button>
        </view>
      </view>
    </view>

    <view v-if="showForm" class="form-mask" @tap="closeForm">
      <view class="form-panel" @tap.stop>
        <view class="form-header">
          <view class="form-title">{{ formMode === 'edit' ? '编辑用户' : '新增用户' }}</view>
          <button class="close-button" @tap="closeForm">×</button>
        </view>

        <view class="field">
          <view class="field-label">姓名</view>
          <input v-model.trim="form.real_name" class="input" placeholder="请输入姓名" placeholder-class="placeholder" />
        </view>
        <view class="field">
          <view class="field-label">手机号</view>
          <input v-model.trim="form.mobile" class="input" type="number" placeholder="请输入手机号" placeholder-class="placeholder" />
        </view>
        <view class="field">
          <view class="field-label">OSS 账号</view>
          <input v-model.trim="form.oss_account" class="input" placeholder="可选" placeholder-class="placeholder" />
        </view>
        <view class="field">
          <view class="field-label">所属组织</view>
          <picker :range="orgs" range-key="display_name" @change="onOrgChange">
            <view class="picker-value">{{ selectedOrgName }}</view>
          </picker>
        </view>
        <view class="field">
          <view class="field-label">角色</view>
          <picker :range="rolePickerOptions" range-key="label" @change="onRoleChange">
            <view class="picker-value">{{ roleLabel(form.role_code) }}</view>
          </picker>
        </view>
        <view class="field">
          <view class="field-label">用户类型</view>
          <picker :range="userTypePickerOptions" range-key="label" @change="onUserTypeChange">
            <view class="picker-value">{{ userTypeLabel(form.user_type) }}</view>
          </picker>
        </view>
        <view v-if="form.role_code === 'org_admin'" class="field">
          <view class="field-label">管理组织</view>
          <picker :range="orgs" range-key="display_name" @change="onManageOrgChange">
            <view class="picker-value">{{ selectedManageOrgName }}</view>
          </picker>
        </view>

        <button class="primary-button save-button" :loading="saving" :disabled="saving" @tap="saveUser">保存</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import {
  createUser,
  disableUser,
  enableUser,
  listUsers,
  resetPassword,
  updateUser,
  userOptions
} from '../../../api/adminUsers'
import { requireLogin } from '../../../api/auth'
import { messageLabel, option, ossStatusLabel, roleLabel, statusLabel, userTypeLabel } from '../../../utils/labels'

const emptyForm = {
  id: null,
  real_name: '',
  mobile: '',
  oss_account: '',
  user_type: 'internal',
  role_code: 'normal_user',
  status: 'active',
  org_id: '',
  manage_org_id: ''
}

const keyword = ref('')
const users = ref([])
const total = ref(0)
const orgs = ref([])
const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const showFilters = ref(false)
const formMode = ref('create')
const form = reactive({ ...emptyForm })
const selectedOrgName = ref('请选择')
const selectedManageOrgName = ref('请选择')
const selectedFilterOrgName = ref('全部组织')
const filterOrgOptions = ref([option('全部组织', '')])
const filterRoleOptions = ref([option('全部角色', '')])
const filterUserTypeOptions = ref([option('全部类型', '')])
const filterStatusOptions = ref([option('全部状态', '')])
const filterOssOptions = ref([option('全部OSS', '')])
const rolePickerOptions = ref([])
const userTypePickerOptions = ref([])
const filters = reactive({
  org_id: '',
  role_code: '',
  user_type: '',
  status: '',
  oss_bind_status: ''
})

const activeFilterCount = computed(() => Object.values(filters).filter(Boolean).length)
const filterSummary = computed(() => (activeFilterCount.value ? `筛选 ${activeFilterCount.value}` : '筛选'))

onLoad(() => {
  requireLogin()
    .then(() => Promise.all([loadOptions(), loadUsers()]))
    .catch((error) => {
      if (error.message !== '未登录') {
        toast(error.message)
      }
    })
})

function loadOptions() {
  return userOptions()
    .then((data) => {
      const optionOrgs = data.orgs || []
      const roleCodes = data.role_codes || []
      const userTypes = data.user_types || []
      const statuses = data.statuses || []
      const ossStatuses = data.oss_bind_statuses || []

      orgs.value = optionOrgs
      rolePickerOptions.value = roleCodes.map((item) => option(roleLabel(item), item))
      userTypePickerOptions.value = userTypes.map((item) => option(userTypeLabel(item), item))
      filterOrgOptions.value = [option('全部组织', '')].concat(optionOrgs.map((item) => option(item.display_name || item.name, item.id)))
      filterRoleOptions.value = [option('全部角色', '')].concat(roleCodes.map((item) => option(roleLabel(item), item)))
      filterUserTypeOptions.value = [option('全部类型', '')].concat(userTypes.map((item) => option(userTypeLabel(item), item)))
      filterStatusOptions.value = [option('全部状态', '')].concat(statuses.map((item) => option(statusLabel(item), item)))
      filterOssOptions.value = [option('全部OSS', '')].concat(ossStatuses.map((item) => option(ossStatusLabel(item), item)))
    })
    .catch((error) => toast(error.message))
}

function loadUsers() {
  loading.value = true
  return listUsers({
    keyword: keyword.value,
    org_id: filters.org_id,
    role_code: filters.role_code,
    user_type: filters.user_type,
    status: filters.status,
    oss_bind_status: filters.oss_bind_status,
    page_size: 50
  })
    .then((data) => {
      users.value = data.items || []
      total.value = data.total || users.value.length
    })
    .catch((error) => toast(error.message))
    .finally(() => {
      loading.value = false
    })
}

function resetForm() {
  Object.assign(form, emptyForm)
  selectedOrgName.value = '请选择'
  selectedManageOrgName.value = '请选择'
}

function openCreate() {
  resetForm()
  formMode.value = 'create'
  showForm.value = true
}

function openEdit(user) {
  Object.assign(form, {
    id: user.id,
    real_name: user.real_name || '',
    mobile: user.mobile || '',
    oss_account: user.oss_account || '',
    user_type: user.user_type || 'internal',
    role_code: user.role_code || 'normal_user',
    status: user.status || 'active',
    org_id: user.org_id || '',
    manage_org_id: user.manage_org_id || ''
  })
  selectedOrgName.value = user.org_name || '请选择'
  selectedManageOrgName.value = user.manage_org_name || '请选择'
  formMode.value = 'edit'
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  resetForm()
}

function onOrgChange(event) {
  const org = orgs.value[Number(event.detail.value)]
  form.org_id = org ? org.id : ''
  selectedOrgName.value = org ? (org.display_name || org.name) : '请选择'
}

function onManageOrgChange(event) {
  const org = orgs.value[Number(event.detail.value)]
  form.manage_org_id = org ? org.id : ''
  selectedManageOrgName.value = org ? (org.display_name || org.name) : '请选择'
}

function onRoleChange(event) {
  const item = rolePickerOptions.value[Number(event.detail.value)]
  form.role_code = item ? item.value : form.role_code
}

function onUserTypeChange(event) {
  const item = userTypePickerOptions.value[Number(event.detail.value)]
  form.user_type = item ? item.value : form.user_type
}

function onFilterOrgChange(event) {
  const item = filterOrgOptions.value[Number(event.detail.value)] || {}
  filters.org_id = item.value || ''
  selectedFilterOrgName.value = item.label || '全部组织'
  loadUsers()
}

function onFilterChange(field, options, event) {
  const item = options[Number(event.detail.value)] || {}
  filters[field] = item.value || ''
  loadUsers()
}

function clearFilters() {
  Object.assign(filters, { org_id: '', role_code: '', user_type: '', status: '', oss_bind_status: '' })
  selectedFilterOrgName.value = '全部组织'
  loadUsers()
}

function labelOf(value, options, fallback) {
  const item = options.find((entry) => entry.value === value)
  return item ? item.label : fallback
}

function saveUser() {
  if (!form.real_name || !form.mobile || !form.org_id) {
    toast('请填写姓名、手机号和组织')
    return
  }

  saving.value = true
  const payload = { ...form }
  const action = formMode.value === 'edit' ? updateUser(form.id, payload) : createUser(payload)

  action
    .then((data) => {
      toast(data.initial_password ? `初始密码：${data.initial_password}` : '保存成功')
      closeForm()
      loadUsers()
    })
    .catch((error) => toast(error.message))
    .finally(() => {
      saving.value = false
    })
}

function toggleStatus(user) {
  const action = user.status === 'active' ? disableUser(user.id) : enableUser(user.id)
  action
    .then(() => {
      toast(user.status === 'active' ? '已禁用' : '已启用')
      loadUsers()
    })
    .catch((error) => toast(error.message))
}

function resetUserPassword(user) {
  uni.showModal({
    title: '重置密码',
    content: `确认重置 ${user.real_name} 的密码？`,
    success(result) {
      if (!result.confirm) {
        return
      }
      resetPassword(user.id)
        .then((data) => {
          toast(`初始密码：${data.initial_password}`)
          loadUsers()
        })
        .catch((error) => toast(error.message))
    }
  })
}

function toast(title) {
  uni.showToast({ title: messageLabel(title), icon: 'none' })
}
</script>

<style scoped>
.manage-page {
  padding: 18rpx 20rpx 48rpx;
}

.compact-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 18rpx;
}

.bar-title {
  color: #1f2933;
  font-size: 34rpx;
  font-weight: 700;
}

.bar-subtitle {
  margin-top: 4rpx;
  color: #6b7785;
  font-size: 23rpx;
}

.bar-actions,
.search-row,
.action-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.ghost-button,
.add-button,
.search-button,
.clear-button,
.close-button {
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: normal;
}

.ghost-button {
  min-width: 116rpx;
  height: 60rpx;
  padding: 0 18rpx;
  border: 1rpx solid #d9e1ea;
  background: #ffffff;
  color: #285b8f;
  font-size: 24rpx;
}

.add-button {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  background: #1f6feb;
  color: #ffffff;
  font-size: 38rpx;
  font-weight: 600;
}

.search-row {
  margin-bottom: 14rpx;
}

.search-input {
  flex: 1;
  height: 70rpx;
  padding: 0 20rpx;
  border: 1rpx solid #d9e1ea;
  border-radius: 4rpx;
  background: #ffffff;
  color: #1f2933;
  font-size: 25rpx;
}

.search-button {
  width: 108rpx;
  height: 70rpx;
  background: #1f6feb;
  color: #ffffff;
  font-size: 25rpx;
}

.filter-panel {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.filter-pill,
.clear-button {
  height: 62rpx;
  padding: 0 16rpx;
  overflow: hidden;
  border: 1rpx solid #d9e1ea;
  border-radius: 4rpx;
  background: #ffffff;
  color: #4b5968;
  font-size: 23rpx;
  line-height: 62rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clear-button {
  color: #c9352b;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.item-card {
  padding: 22rpx;
}

.item-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.item-title {
  overflow: hidden;
  color: #1f2933;
  font-size: 30rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  margin-top: 8rpx;
  color: #6b7785;
  font-size: 24rpx;
  line-height: 1.5;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
  margin-top: 12rpx;
}

.tag {
  flex: 0 0 auto;
  padding: 4rpx 12rpx;
  border-radius: 4rpx;
  background: #e8eef4;
  color: #285b8f;
  font-size: 22rpx;
}

.tag.danger {
  background: #fdeceb;
  color: #c9352b;
}

.action-row {
  justify-content: flex-end;
  margin-top: 16rpx;
}

.mini-button {
  min-width: 98rpx;
  min-height: 54rpx;
  line-height: 54rpx;
  font-size: 24rpx;
}

.empty-panel {
  padding: 40rpx 24rpx;
  color: #6b7785;
  text-align: center;
}

.form-mask {
  position: fixed;
  inset: 0;
  z-index: 10;
  display: flex;
  align-items: flex-end;
  background: rgba(31, 41, 51, 0.38);
}

.form-panel {
  width: 100%;
  max-height: 86vh;
  padding: 30rpx 32rpx 44rpx;
  overflow-y: auto;
  border-radius: 16rpx 16rpx 0 0;
  background: #ffffff;
}

.form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.form-title {
  color: #1f2933;
  font-size: 34rpx;
  font-weight: 700;
}

.close-button {
  width: 64rpx;
  height: 64rpx;
  background: #f0f3f6;
  color: #6b7785;
  font-size: 38rpx;
}

.field + .field {
  margin-top: 22rpx;
}

.picker-value {
  min-height: 80rpx;
  padding: 0 22rpx;
  border: 1rpx solid #d9e1ea;
  border-radius: 4rpx;
  background: #ffffff;
  color: #1f2933;
  font-size: 26rpx;
  line-height: 80rpx;
}

.save-button {
  width: 100%;
  margin-top: 30rpx;
}
</style>
