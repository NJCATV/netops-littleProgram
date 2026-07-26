const {
  createMenu,
  disableMenu,
  enableMenu,
  listMenus,
  updateMenu
} = require('../../../utils/adminMenus')

const emptyForm = {
  id: null,
  menu_key: '',
  name: '',
  icon: 'app',
  path: '',
  group_name: '全部功能',
  min_role: 'normal_user',
  user_type: 'internal',
  sort_order: 0,
  enabled: true,
  remark: ''
}

Page({
  data: {
    menus: [],
    commonMenus: [],
    otherMenus: [],
    loading: false,
    saving: false,
    showForm: false,
    formMode: 'create',
    form: Object.assign({}, emptyForm),
    roleCodes: ['normal_user', 'org_admin', 'super_admin'],
    userTypes: ['internal', 'external', 'system', 'all'],
    groups: ['我的常用', '全部功能', '管理工具']
  },

  goBack() {
    wx.navigateBack()
  },

  onLoad() {
    this.loadMenus()
  },

  loadMenus() {
    this.setData({ loading: true })
    listMenus()
      .then((data) => {
        const menus = data.items || []
        this.setData({
          menus,
          commonMenus: menus.filter((item) => item.group_name === '我的常用'),
          otherMenus: menus.filter((item) => item.group_name !== '我的常用')
        })
      })
      .catch((error) => this.toast(error.message))
      .finally(() => this.setData({ loading: false }))
  },

  openCreate() {
    this.setData({
      showForm: true,
      formMode: 'create',
      form: Object.assign({}, emptyForm)
    })
  },

  openEdit(event) {
    const id = Number(event.currentTarget.dataset.id)
    const menu = this.data.menus.find((item) => item.id === id)
    if (!menu) return
    this.setData({
      showForm: true,
      formMode: 'edit',
      form: Object.assign({}, menu)
    })
  },

  closeForm() {
    this.setData({ showForm: false, form: Object.assign({}, emptyForm) })
  },

  onFormInput(event) {
    const field = event.currentTarget.dataset.field
    this.setData({ [`form.${field}`]: event.detail.value })
  },

  onRoleChange(event) {
    this.setData({ 'form.min_role': this.data.roleCodes[Number(event.detail.value)] })
  },

  onUserTypeChange(event) {
    this.setData({ 'form.user_type': this.data.userTypes[Number(event.detail.value)] })
  },

  onGroupChange(event) {
    this.setData({ 'form.group_name': this.data.groups[Number(event.detail.value)] })
  },

  saveMenu() {
    const form = Object.assign({}, this.data.form, {
      sort_order: Number(this.data.form.sort_order || 0)
    })
    if (!form.menu_key || !form.name || !form.icon || !form.group_name) {
      this.toast('请填写功能标识、名称、图标和分组')
      return
    }

    const action = this.data.formMode === 'edit'
      ? updateMenu(form.id, form)
      : createMenu(form)
    this.setData({ saving: true })
    action
      .then(() => {
        this.toast('保存成功')
        this.closeForm()
        this.loadMenus()
      })
      .catch((error) => this.toast(error.message))
      .finally(() => this.setData({ saving: false }))
  },

  toggleMenu(event) {
    const id = Number(event.currentTarget.dataset.id)
    const enabled = Number(event.currentTarget.dataset.enabled) === 1
    const action = enabled ? disableMenu(id) : enableMenu(id)
    action
      .then(() => {
        this.toast(enabled ? '已停用' : '已启用')
        this.loadMenus()
      })
      .catch((error) => this.toast(error.message))
  },

  toast(title) {
    wx.showToast({ title, icon: 'none' })
  }
})
