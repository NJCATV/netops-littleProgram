<template>
  <view class="page manage-page">
    <view class="compact-bar">
      <view>
        <view class="bar-title">组织管理</view>
        <view class="bar-subtitle">共 {{ orgs.length }} 个组织</view>
      </view>
      <view class="bar-actions">
        <button class="ghost-button" @tap="expandAll">{{ allExpanded ? '全部收起' : '全部展开' }}</button>
        <button class="add-button" @tap="openCreate(null)"><text>+</text></button>
      </view>
    </view>

    <view class="tips">点击左侧 + 展开下级；子级会紧跟在父级下方。</view>

    <view v-if="loading" class="status-text">加载中...</view>
    <view v-else-if="visibleOrgs.length === 0" class="panel empty-panel">暂无组织</view>

    <view v-else class="tree-list">
      <view v-for="row in visibleOrgs" :key="row.id" class="panel tree-row" :class="`level-${row.level}`">
        <view class="tree-main">
          <view class="indent" :style="{ width: `${(row.level - 1) * 34}rpx` }"></view>
          <button class="expand-button" :class="{ hidden: !row.hasChildren }" @tap="toggleExpand(row)">
            {{ isExpanded(row.id) ? '−' : '+' }}
          </button>
          <view class="tree-copy">
            <view class="item-head">
              <view class="item-title">{{ row.name }}</view>
              <text class="tag" :class="{ danger: row.status !== 'active' }">{{ statusLabel(row.status) }}</text>
            </view>
            <view class="item-meta">{{ row.pathLabel }}｜排序 {{ row.sort_order }}｜下级 {{ row.childCount }}</view>
          </view>
        </view>
        <view class="action-row">
          <button v-if="row.level < 3" class="secondary-button mini-button" @tap="openCreate(row)">下级</button>
          <button class="secondary-button mini-button" @tap="openEdit(row)">编辑</button>
          <button class="secondary-button mini-button" @tap="toggleStatus(row)">
            {{ row.status === 'active' ? '禁用' : '启用' }}
          </button>
          <button class="secondary-button mini-button danger-button" @tap="confirmDelete(row)">删除</button>
        </view>
      </view>
    </view>

    <view v-if="showForm" class="form-mask" @tap="closeForm">
      <view class="form-panel" @tap.stop>
        <view class="form-header">
          <view class="form-title">{{ formMode === 'edit' ? '编辑组织' : '新增组织' }}</view>
          <button class="close-button" @tap="closeForm">×</button>
        </view>

        <view v-if="parentName" class="parent-tip">上级组织：{{ parentName }}</view>
        <view class="field">
          <view class="field-label">组织名称</view>
          <input v-model.trim="form.name" class="input" placeholder="请输入组织名称" placeholder-class="placeholder" />
        </view>
        <view class="field">
          <view class="field-label">排序</view>
          <input v-model="form.sort_order" class="input" type="number" />
        </view>
        <button class="primary-button save-button" :loading="saving" :disabled="saving" @tap="saveOrg">保存</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { createOrg, deleteOrg, disableOrg, enableOrg, listOrgs, updateOrg } from '../../../api/adminOrgs'
import { requireLogin } from '../../../api/auth'
import { messageLabel, statusLabel } from '../../../utils/labels'

const orgs = ref([])
const loading = ref(false)
const saving = ref(false)
const showForm = ref(false)
const formMode = ref('create')
const parentName = ref('')
const expandedIds = ref(new Set())
const form = reactive({
  id: null,
  parent_id: '',
  name: '',
  sort_order: 0
})

const roots = computed(() => buildTree(orgs.value))
const allExpandableIds = computed(() => flattenTree(roots.value).filter((row) => row.hasChildren).map((row) => row.id))
const allExpanded = computed(() => allExpandableIds.value.length > 0 && allExpandableIds.value.every((id) => expandedIds.value.has(id)))
const visibleOrgs = computed(() => flattenVisible(roots.value))

onLoad(() => {
  requireLogin()
    .then(loadOrgs)
    .catch((error) => {
      if (error.message !== '未登录') {
        toast(error.message)
      }
    })
})

function loadOrgs() {
  loading.value = true
  return listOrgs()
    .then((data) => {
      orgs.value = data.items || []
      expandedIds.value = new Set()
    })
    .catch((error) => toast(error.message))
    .finally(() => {
      loading.value = false
    })
}

function buildTree(items) {
  const map = new Map()
  items.forEach((item) => {
    map.set(item.id, { ...item, children: [] })
  })

  const result = []
  map.forEach((item) => {
    const parent = map.get(item.parent_id)
    if (parent) {
      parent.children.push(item)
    } else {
      result.push(item)
    }
  })

  const sorter = (a, b) => (a.sort_order - b.sort_order) || (a.id - b.id)
  const sortDeep = (nodes) => {
    nodes.sort(sorter)
    nodes.forEach((node) => sortDeep(node.children))
  }
  sortDeep(result)
  return result
}

function rowOf(node, ancestry) {
  const names = ancestry.concat(node.name)
  return {
    ...node,
    hasChildren: node.children.length > 0,
    childCount: node.children.length,
    pathLabel: names.join(' / ')
  }
}

function flattenTree(nodes, ancestry = []) {
  return nodes.flatMap((node) => [rowOf(node, ancestry)].concat(flattenTree(node.children, ancestry.concat(node.name))))
}

function flattenVisible(nodes, ancestry = []) {
  const rows = []
  nodes.forEach((node) => {
    rows.push(rowOf(node, ancestry))
    if (expandedIds.value.has(node.id)) {
      rows.push(...flattenVisible(node.children, ancestry.concat(node.name)))
    }
  })
  return rows
}

function isExpanded(id) {
  return expandedIds.value.has(id)
}

function toggleExpand(row) {
  if (!row.hasChildren) {
    return
  }
  const next = new Set(expandedIds.value)
  if (next.has(row.id)) {
    next.delete(row.id)
  } else {
    next.add(row.id)
  }
  expandedIds.value = next
}

function expandAll() {
  if (allExpanded.value) {
    expandedIds.value = new Set()
    return
  }
  expandedIds.value = new Set(allExpandableIds.value)
}

function resetForm() {
  Object.assign(form, { id: null, parent_id: '', name: '', sort_order: 0 })
  parentName.value = ''
}

function openCreate(parent) {
  resetForm()
  formMode.value = 'create'
  if (parent) {
    form.parent_id = parent.id
    parentName.value = parent.name
  }
  showForm.value = true
}

function openEdit(row) {
  Object.assign(form, {
    id: row.id,
    parent_id: row.parent_id || '',
    name: row.name || '',
    sort_order: row.sort_order || 0
  })
  parentName.value = ''
  formMode.value = 'edit'
  showForm.value = true
}

function closeForm() {
  showForm.value = false
  resetForm()
}

function saveOrg() {
  if (!form.name) {
    toast('请填写组织名称')
    return
  }

  saving.value = true
  const payload = { ...form }
  const action = formMode.value === 'edit' ? updateOrg(form.id, payload) : createOrg(payload)
  action
    .then(() => {
      toast('保存成功')
      closeForm()
      loadOrgs()
    })
    .catch((error) => toast(error.message))
    .finally(() => {
      saving.value = false
    })
}

function toggleStatus(row) {
  const action = row.status === 'active' ? disableOrg(row.id) : enableOrg(row.id)
  action
    .then(() => {
      toast(row.status === 'active' ? '已禁用' : '已启用')
      loadOrgs()
    })
    .catch((error) => toast(error.message))
}

function confirmDelete(row) {
  const count = flattenTree([row]).length
  uni.showModal({
    title: '删除组织',
    content: `确认删除“${row.name}”及其 ${count - 1} 个下级组织？关联用户会变为未分配组织。`,
    confirmText: '删除',
    confirmColor: '#c9352b',
    success(result) {
      if (!result.confirm) {
        return
      }
      deleteOrg(row.id)
        .then((data) => {
          toast(`已删除 ${data.deleted_count || count} 个组织`)
          loadOrgs()
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
  margin-bottom: 12rpx;
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

.tips {
  margin-bottom: 14rpx;
  color: #6b7785;
  font-size: 23rpx;
}

.bar-actions,
.action-row,
.tree-main,
.item-head {
  display: flex;
  align-items: center;
}

.bar-actions,
.action-row {
  gap: 10rpx;
}

.ghost-button,
.add-button,
.expand-button,
.close-button {
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: normal;
}

.ghost-button {
  min-width: 132rpx;
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

.tree-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.tree-row {
  padding: 18rpx;
  border-left: 6rpx solid #c7d8ea;
}

.tree-row.level-1 {
  border-left-color: #1f6feb;
}

.tree-row.level-2 {
  border-left-color: #3b8f6b;
}

.tree-row.level-3 {
  border-left-color: #b7791f;
}

.tree-main {
  gap: 12rpx;
}

.indent {
  flex: 0 0 auto;
  height: 1rpx;
}

.expand-button {
  flex: 0 0 44rpx;
  width: 44rpx;
  height: 44rpx;
  border: 1rpx solid #d9e1ea;
  background: #ffffff;
  color: #285b8f;
  font-size: 28rpx;
  font-weight: 700;
}

.expand-button.hidden {
  opacity: 0;
}

.tree-copy {
  flex: 1;
  min-width: 0;
}

.item-head {
  justify-content: space-between;
  gap: 16rpx;
}

.item-title {
  overflow: hidden;
  color: #1f2933;
  font-size: 29rpx;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.item-meta {
  margin-top: 6rpx;
  overflow: hidden;
  color: #6b7785;
  font-size: 23rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  flex-wrap: wrap;
  margin-top: 14rpx;
}

.mini-button {
  min-width: 88rpx;
  min-height: 54rpx;
  line-height: 54rpx;
  font-size: 24rpx;
}

.danger-button {
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

.parent-tip {
  margin-bottom: 20rpx;
  color: #6b7785;
  font-size: 25rpx;
}

.field + .field {
  margin-top: 22rpx;
}

.save-button {
  width: 100%;
  margin-top: 30rpx;
}
</style>
