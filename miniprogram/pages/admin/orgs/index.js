const { createOrg, disableOrg, orgTree, updateOrg } = require('../../../utils/adminOrgs')

const emptyForm = {
  id: null,
  name: '',
  parent_id: '',
  sort_order: 0
}

Page({
  data: {
    orgs: [],
    loading: false,
    saving: false,
    showForm: false,
    formMode: 'create',
    form: Object.assign({}, emptyForm),
    selectedParentName: '一级组织'
  },

  onLoad() {
    this.loadOrgs()
  },

  loadOrgs() {
    this.setData({ loading: true })
    orgTree()
      .then((data) => this.setData({ orgs: data.items || [] }))
      .catch((error) => this.toast(error.message))
      .finally(() => this.setData({ loading: false }))
  },

  openCreate(event) {
    const parentId = event.currentTarget.dataset.parentId || ''
    const parent = this.data.orgs.find((item) => item.id === Number(parentId))
    this.setData({
      showForm: true,
      formMode: 'create',
      form: Object.assign({}, emptyForm, { parent_id: parentId }),
      selectedParentName: parent ? parent.name : '一级组织'
    })
  },

  openEdit(event) {
    const id = Number(event.currentTarget.dataset.id)
    const org = this.data.orgs.find((item) => item.id === id)
    if (!org) return
    this.setData({
      showForm: true,
      formMode: 'edit',
      form: {
        id: org.id,
        name: org.name,
        parent_id: org.parent_id || '',
        sort_order: org.sort_order || 0
      },
      selectedParentName: '保持不变'
    })
  },

  closeForm() {
    this.setData({ showForm: false, form: Object.assign({}, emptyForm) })
  },

  onFormInput(event) {
    const field = event.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: event.detail.value })
  },

  saveOrg() {
    const form = Object.assign({}, this.data.form, {
      sort_order: Number(this.data.form.sort_order || 0)
    })
    if (!form.name) {
      this.toast('请填写组织名称')
      return
    }
    const action = this.data.formMode === 'edit'
      ? updateOrg(form.id, form)
      : createOrg(form)
    this.setData({ saving: true })
    action
      .then(() => {
        this.toast('保存成功')
        this.closeForm()
        this.loadOrgs()
      })
      .catch((error) => this.toast(error.message))
      .finally(() => this.setData({ saving: false }))
  },

  disable(event) {
    const id = Number(event.currentTarget.dataset.id)
    disableOrg(id)
      .then(() => {
        this.toast('已禁用')
        this.loadOrgs()
      })
      .catch((error) => this.toast(error.message))
  },

  toast(title) {
    wx.showToast({ title, icon: 'none' })
  }
})
