<template>
  <view class="page manage-page">
    <view class="compact-bar">
      <view>
        <view class="bar-title">权限配置</view>
        <view class="bar-subtitle">共 {{ menus.length }} 个功能</view>
      </view>
      <button class="add-button" @tap="openCreate"><text>+</text></button>
    </view>

    <view v-if="loading" class="status-text">加载中...</view>
    <view v-else-if="menus.length === 0" class="panel empty-panel">暂无功能菜单</view>

    <view v-else class="list">
      <view v-for="item in menus" :key="item.id" class="panel item-card">
        <view class="item-head">
          <view class="item-title">{{ item.name }}</view>
          <text class="tag" :class="{ danger: !item.enabled }">{{ enabledLabel(item.enabled) }}</text>
        </view>
        <view class="item-meta">{{ item.group_name }}｜{{ item.menu_key }}</view>
        <view class="tag-row">
          <text class="tag">{{ roleLabel(item.min_role) }}</text>
          <text class="tag">{{ userTypeLabel(item.user_type) }}</text>
          <text class="tag">排序 {{ item.sort_order }}</text>
        </view>
        <view class="path-text">{{ item.path || '未配置页面路径' }}</view>
        <view class="action-row">
          <button class="secondary-button mini-button" @tap="openEdit(item)">编辑</button>
          <button v-if="item.menu_key !== 'menu.manage'" class="secondary-button mini-button" @tap="toggleEnabled(item)">
            {{ item.enabled ? '禁用' : '启用' }}
          </button>
          <button v-if="item.menu_key !== 'menu.manage'" class="secondary-button mini-button delete-button" @tap="confirmDelete(item)">删除</button>
        </view>
      </view>
    </view>

    <view v-if="showForm" class="form-mask" @tap="closeForm">
      <view class="form-panel" @tap.stop>
        <view class="form-header">
          <view class="form-title">{{ formMode === 'edit' ? '编辑功能' : '新增功能' }}</view>
          <button class="close-button" @tap="closeForm">×</button>
        </view>

        <view class="field">
          <view class="field-label">菜单编码</view>
          <input v-model.trim="form.menu_key" class="input" placeholder="如 user.manage" placeholder-class="placeholder" />
        </view>
        <view class="field">
          <view class="field-label">名称</view>
          <input v-model.trim="form.name" class="input" placeholder="请输入功能名称" placeholder-class="placeholder" />
        </view>
        <view class="field">
          <view class="field-label">图标</view>
          <input v-model.trim="form.icon" class="input" placeholder="如 usergroup" placeholder-class="placeholder" />
        </view>
        <view class="field">
          <view class="field-label">页面路径</view>
          <input v-model.trim="form.path" class="input" placeholder="/pages/admin/users/index" placeholder-class="placeholder" />
        </view>
        <view class="field">
          <view class="field-label">分组</view>
          <input v-model.trim="form.group_name" class="input" placeholder="如 管理工具" placeholder-class="placeholder" />
        </view>
        <view class="field">
          <view class="field-label">最小角色</view>
          <picker :range="roleOptions" range-key="label" @change="onRoleChange">
            <view class="picker-value">{{ roleLabel(form.min_role) }}</view>
          </picker>
        </view>
        <view class="field">
          <view class="field-label">用户类型</view>
          <picker :range="userTypeOptions" range-key="label" @change="onUserTypeChange">
            <view class="picker-value">{{ userTypeLabel(form.user_type) }}</view>
          </picker>
        </view>
        <view class="field">
          <view class="field-label">排序</view>
          <input v-model="form.sort_order" class="input" type="number" />
        </view>
        <view class="field">
          <view class="field-label">备注</view>
          <input v-model.trim="form.remark" class="input" placeholder="可选" placeholder-class="placeholder" />
        </view>
        <button class="primary-button save-button" :loading="saving" :disabled="saving" @tap="saveMenu">保存</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { createMenu, deleteMenu, disableMenu, enableMenu, listMenus, updateMenu } from '../../../api/adminMenus'
import { requireLogin } from '../../../api/auth'
import { invalidateMenuCache } from '../../../api/menu'
import { enabledLabel, messageLabel, option, roleLabel, userTypeLabel } from '../../../utils/labels'

const emptyForm = {
  id: null,
  menu_key: '',
  name: '',
  icon: '',
  path: '',
  group_name: '',
  min_role: 'normal_user',
  user_type: 'internal',
  enabled: true,
  sort_order: 0,
  remark: ''
}

const menus = ref([])
const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const formMode = ref('create')
const form = reactive({ ...emptyForm })
const roleOptions = ['normal_user', 'org_admin', 'super_admin'].map((item) => option(roleLabel(item), item))
const userTypeOptions = ['internal', 'external', 'system', 'all'].map((item) => option(userTypeLabel(item), item))

onLoad(() => {
  requireLogin()
    .then(loadMenus)
    .catch((error) => {
      if (error.message !== '未登录') {
        toast(error.message)
      }
    })
})

function loadMenus() {
  loading.value = true
  return listMenus()
    .then((data) => {
      menus.value = data.items || []
    })
    .catch((error) => toast(error.message))
    .finally(() => {
      loading.value = false
    })
}

function resetForm() {
  Object.assign(form, emptyForm)
}

function openCreate() {
  resetForm()
  formMode.value = 'create'
  showForm.value = true
}

function openEdit(item) {
  Object.assign(form, {
    ...emptyForm,
    ...item,
    remark: item.remark || ''
  })
  formMode.value = 'edit'
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  resetForm()
}

function onRoleChange(event) {
  const item = roleOptions[Number(event.detail.value)]
  form.min_role = item ? item.value : form.min_role
}

function onUserTypeChange(event) {
  const item = userTypeOptions[Number(event.detail.value)]
  form.user_type = item ? item.value : form.user_type
}

function saveMenu() {
  if (!form.menu_key || !form.name || !form.icon || !form.path || !form.group_name) {
    toast('请填写编码、名称、图标、页面路径和分组')
    return
  }

  saving.value = true
  const payload = { ...form }
  const action = formMode.value === 'edit' ? updateMenu(form.id, payload) : createMenu(payload)
  action
    .then(() => {
      invalidateMenuCache()
      toast('保存成功')
      closeForm()
      loadMenus()
    })
    .catch((error) => toast(error.message))
    .finally(() => {
      saving.value = false
    })
}

function confirmDelete(item) {
  uni.showModal({
    title: '删除功能',
    content: `确认删除“${item.name}”？删除后该入口和对应接口将立即不可用。`,
    confirmColor: '#c9352b',
    success(result) {
      if (!result.confirm) return
      deleteMenu(item.id)
        .then(() => {
          invalidateMenuCache()
          toast('已删除')
          loadMenus()
        })
        .catch((error) => toast(error.message))
    }
  })
}

function toggleEnabled(item) {
  const action = item.enabled ? disableMenu(item.id) : enableMenu(item.id)
  action
    .then(() => {
      invalidateMenuCache()
      toast(item.enabled ? '已禁用' : '已启用')
      loadMenus()
    })
    .catch((error) => toast(error.message))
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

.add-button,
.close-button {
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: normal;
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

.item-meta,
.path-text {
  margin-top: 8rpx;
  color: #6b7785;
  font-size: 24rpx;
  line-height: 1.5;
}

.path-text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 12rpx;
  margin-top: 16rpx;
}

.mini-button {
  min-width: 98rpx;
  min-height: 54rpx;
  line-height: 54rpx;
  font-size: 24rpx;
}

.delete-button {
  border-color: #efc7c4;
  color: #c9352b;
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
