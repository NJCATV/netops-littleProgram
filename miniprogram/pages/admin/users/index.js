const {
  createUser,
  disableUser,
  enableUser,
  listUsers,
  resetPassword,
  updateUser,
  userOptions
} = require('../../../utils/adminUsers')

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

Page({
  data: {
    keyword: '',
    users: [],
    orgs: [],
    roleCodes: [],
    userTypes: [],
    statuses: [],
    ossBindStatuses: [],
    filterOrgOptions: [{ label: '全部组织', value: '' }],
    filterRoleOptions: [{ label: '全部角色', value: '' }],
    filterUserTypeOptions: [{ label: '全部类型', value: '' }],
    filterStatusOptions: [{ label: '全部状态', value: '' }],
    filterOssOptions: [{ label: '全部OSS', value: '' }],
    filters: {
      org_id: '',
      role_code: '',
      user_type: '',
      status: '',
      oss_bind_status: ''
    },
    selectedFilterOrgName: '全部组织',
    loading: false,
    saving: false,
    showForm: false,
    formMode: 'create',
    form: Object.assign({}, emptyForm),
    selectedOrgName: '请选择',
    selectedManageOrgName: '请选择'
  },

  onLoad() {
    this.loadOptions()
    this.loadUsers()
  },

  onKeywordInput(event) {
    this.setData({
      keyword: event.detail.value
    })
  },

  onSearch() {
    this.loadUsers()
  },

  loadOptions() {
    userOptions()
      .then((data) => {
        const orgs = data.orgs || []
        const roleCodes = data.role_codes || []
        const userTypes = data.user_types || []
        const statuses = data.statuses || []
        const ossBindStatuses = data.oss_bind_statuses || []
        this.setData({
          orgs,
          roleCodes,
          userTypes,
          statuses,
          ossBindStatuses,
          filterOrgOptions: [{ label: '全部组织', value: '' }].concat(orgs.map((item) => ({
            label: item.display_name || item.name,
            value: item.id
          }))),
          filterRoleOptions: [{ label: '全部角色', value: '' }].concat(roleCodes.map((item) => ({ label: item, value: item }))),
          filterUserTypeOptions: [{ label: '全部类型', value: '' }].concat(userTypes.map((item) => ({ label: item, value: item }))),
          filterStatusOptions: [{ label: '全部状态', value: '' }].concat(statuses.map((item) => ({ label: item, value: item }))),
          filterOssOptions: [{ label: '全部OSS', value: '' }].concat(ossBindStatuses.map((item) => ({ label: item, value: item })))
        })
      })
      .catch((error) => this.toast(error.message))
  },

  loadUsers() {
    this.setData({ loading: true })
    listUsers({
      keyword: this.data.keyword,
      org_id: this.data.filters.org_id,
      role_code: this.data.filters.role_code,
      user_type: this.data.filters.user_type,
      status: this.data.filters.status,
      oss_bind_status: this.data.filters.oss_bind_status,
      page_size: 50
    })
      .then((data) => {
        this.setData({
          users: data.items || []
        })
      })
      .catch((error) => this.toast(error.message))
      .finally(() => {
        this.setData({ loading: false })
      })
  },

  openCreate() {
    this.setData({
      showForm: true,
      formMode: 'create',
      form: Object.assign({}, emptyForm),
      selectedOrgName: '请选择',
      selectedManageOrgName: '请选择'
    })
  },

  openEdit(event) {
    const id = Number(event.currentTarget.dataset.id)
    const user = this.data.users.find((item) => item.id === id)
    if (!user) {
      return
    }

    this.setData({
      showForm: true,
      formMode: 'edit',
      form: {
        id: user.id,
        real_name: user.real_name || '',
        mobile: user.mobile || '',
        oss_account: user.oss_account || '',
        user_type: user.user_type || 'internal',
        role_code: user.role_code || 'normal_user',
        status: user.status || 'active',
        org_id: user.org_id || '',
        manage_org_id: user.manage_org_id || ''
      },
      selectedOrgName: user.org_name || '请选择',
      selectedManageOrgName: user.manage_org_name || '请选择'
    })
  },

  closeForm() {
    this.setData({
      showForm: false,
      form: Object.assign({}, emptyForm),
      selectedOrgName: '请选择',
      selectedManageOrgName: '请选择'
    })
  },

  onFormInput(event) {
    const field = event.currentTarget.dataset.field
    this.setData({
      [`form.${field}`]: event.detail.value
    })
  },

  onOrgChange(event) {
    const index = Number(event.detail.value)
    const org = this.data.orgs[index]
    this.setData({
      'form.org_id': org ? org.id : '',
      selectedOrgName: org ? (org.display_name || org.name) : '请选择'
    })
  },

  onManageOrgChange(event) {
    const index = Number(event.detail.value)
    const org = this.data.orgs[index]
    this.setData({
      'form.manage_org_id': org ? org.id : '',
      selectedManageOrgName: org ? (org.display_name || org.name) : '请选择'
    })
  },

  onRoleChange(event) {
    this.setData({
      'form.role_code': this.data.roleCodes[Number(event.detail.value)]
    })
  },

  onUserTypeChange(event) {
    this.setData({
      'form.user_type': this.data.userTypes[Number(event.detail.value)]
    })
  },

  onFilterOrgChange(event) {
    const option = this.data.filterOrgOptions[Number(event.detail.value)] || {}
    this.setData({
      'filters.org_id': option.value || '',
      selectedFilterOrgName: option.label || '全部组织'
    }, this.loadUsers)
  },

  onFilterChange(event) {
    const field = event.currentTarget.dataset.field
    const source = event.currentTarget.dataset.source
    const options = this.data[source] || []
    const option = options[Number(event.detail.value)] || {}
    this.setData({
      [`filters.${field}`]: option.value || ''
    }, this.loadUsers)
  },

  saveUser() {
    const form = this.data.form
    if (!form.real_name || !form.mobile || !form.org_id) {
      this.toast('请填写姓名、手机号和组织')
      return
    }

    const action = this.data.formMode === 'edit'
      ? updateUser(form.id, form)
      : createUser(form)

    this.setData({ saving: true })
    action
      .then((data) => {
        if (data.initial_password) {
          this.toast(`初始密码：${data.initial_password}`)
        } else {
          this.toast('保存成功')
        }
        this.closeForm()
        this.loadUsers()
      })
      .catch((error) => this.toast(error.message))
      .finally(() => {
        this.setData({ saving: false })
      })
  },

  toggleStatus(event) {
    const id = Number(event.currentTarget.dataset.id)
    const status = event.currentTarget.dataset.status
    const action = status === 'active' ? disableUser(id) : enableUser(id)
    action
      .then(() => {
        this.toast(status === 'active' ? '已禁用' : '已启用')
        this.loadUsers()
      })
      .catch((error) => this.toast(error.message))
  },

  resetUserPassword(event) {
    const id = Number(event.currentTarget.dataset.id)
    resetPassword(id)
      .then((data) => {
        this.toast(`初始密码：${data.initial_password}`)
        this.loadUsers()
      })
      .catch((error) => this.toast(error.message))
  },

  toast(title) {
    wx.showToast({
      title,
      icon: 'none'
    })
  }
})
