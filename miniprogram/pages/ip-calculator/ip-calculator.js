const ipCalc = require('../../utils/ipCalc')

function resultItem(label, value, copyable, emphasis) {
  return {
    label: label,
    value: String(value === undefined || value === null ? '' : value),
    copyable: !!copyable,
    emphasis: emphasis ? 'emphasis' : ''
  }
}

Page({
  data: {
    activeTab: 'network',
    networkIp: '',
    networkCidr: '24',
    networkResults: [],
    networkError: '',
    cidrMaskInput: '24',
    cidrMaskResults: [],
    maskInput: '',
    maskResults: [],
    maskError: '',
    requiredHostCount: '',
    requiredResults: [],
    requiredError: ''
  },

  switchTab(event) {
    this.setData({
      activeTab: event.currentTarget.dataset.tab
    })
  },

  onInput(event) {
    const key = event.currentTarget.dataset.key
    const patch = {}

    patch[key] = event.detail.value
    this.setData(patch)
  },

  showError(message, key) {
    const patch = {}

    if (key) {
      patch[key] = message
      this.setData(patch)
    }

    wx.showToast({
      title: message,
      icon: 'none'
    })
  },

  calculateNetwork() {
    try {
      const result = ipCalc.calculateNetwork(this.data.networkIp, this.data.networkCidr)
      const rows = [
        resultItem('CIDR 表示', result.cidr, true, true),
        resultItem('子网掩码', result.subnetMask, true, false),
        resultItem('反掩码 / Wildcard Mask', result.wildcardMask, true, false),
        resultItem('网络地址', result.networkAddress, true, true),
        resultItem('广播地址', result.broadcastAddress, true, true),
        resultItem('第一个可用地址', result.firstUsableAddress, true, false),
        resultItem('最后一个可用地址', result.lastUsableAddress, true, false),
        resultItem('可用地址范围', result.usableRange, true, true),
        resultItem('总地址数', result.totalCount, false, false),
        resultItem('可用地址数', result.usableCount, false, false),
        resultItem('IP 二进制', result.ipBinary, false, false),
        resultItem('掩码二进制', result.maskBinary, false, false),
        resultItem('网络地址二进制', result.networkBinary, false, false)
      ]

      if (result.note) {
        rows.push(resultItem('备注', result.note, false, false))
      }

      this.setData({
        networkResults: rows,
        networkError: ''
      })
    } catch (error) {
      this.setData({ networkResults: [] })
      this.showError(error.message || '计算失败', 'networkError')
    }
  },

  clearNetwork() {
    this.setData({
      networkIp: '',
      networkCidr: '24',
      networkResults: [],
      networkError: ''
    })
  },

  calculateCidrMask() {
    try {
      const cidr = Number(this.data.cidrMaskInput)
      const mask = ipCalc.cidrToMask(this.data.cidrMaskInput)
      const rows = [
        resultItem('CIDR', '/' + cidr, true, true),
        resultItem('子网掩码', mask, true, true),
        resultItem('反掩码', ipCalc.cidrToWildcard(cidr), true, false),
        resultItem('二进制掩码', ipCalc.ipToBinary(mask), false, false),
        resultItem('十六进制掩码', ipCalc.maskToHex(mask), false, false)
      ]

      this.setData({
        cidrMaskResults: rows,
        maskError: ''
      })
    } catch (error) {
      this.setData({ cidrMaskResults: [] })
      this.showError(error.message || '换算失败', 'maskError')
    }
  },

  calculateMaskCidr() {
    try {
      const cidr = ipCalc.maskToCidr(this.data.maskInput)
      const rows = [
        resultItem('CIDR', '/' + cidr, true, true),
        resultItem('反掩码', ipCalc.maskToWildcard(this.data.maskInput), true, false),
        resultItem('二进制掩码', ipCalc.ipToBinary(this.data.maskInput), false, false),
        resultItem('十六进制掩码', ipCalc.maskToHex(this.data.maskInput), false, false)
      ]

      this.setData({
        maskResults: rows,
        maskError: ''
      })
    } catch (error) {
      this.setData({ maskResults: [] })
      this.showError(error.message || '请输入合法且连续的子网掩码。', 'maskError')
    }
  },

  clearMask() {
    this.setData({
      cidrMaskInput: '24',
      cidrMaskResults: [],
      maskInput: '',
      maskResults: [],
      maskError: ''
    })
  },

  calculateRequired() {
    try {
      const result = ipCalc.calculateRequiredCidr(this.data.requiredHostCount)
      let rows = []

      if (result.mode === 'dual') {
        rows = [
          resultItem('点到点推荐', '/' + result.pointToPoint.cidr, true, true),
          resultItem('点到点子网掩码', result.pointToPoint.mask, true, false),
          resultItem('点到点地址数', '总地址数 ' + result.pointToPoint.totalCount + '，可用地址数 ' + result.pointToPoint.usableCount, true, false),
          resultItem('普通网络推荐', '/' + result.normal.cidr, true, true),
          resultItem('普通网络子网掩码', result.normal.mask, true, false),
          resultItem('普通网络地址数', '总地址数 ' + result.normal.totalCount + '，可用地址数 ' + result.normal.usableCount, true, false),
          resultItem('说明', result.pointToPoint.description + '；' + result.normal.description, false, false)
        ]
      } else {
        rows = [
          resultItem('推荐 CIDR', '/' + result.recommendedCidr, true, true),
          resultItem('推荐子网掩码', result.recommendedMask, true, true),
          resultItem('总地址数', result.totalCount, true, false),
          resultItem('可用地址数', result.usableCount, true, false),
          resultItem('说明', result.description, false, false)
        ]
      }

      this.setData({
        requiredResults: rows,
        requiredError: ''
      })
    } catch (error) {
      this.setData({ requiredResults: [] })
      this.showError(error.message || '反推失败', 'requiredError')
    }
  },

  clearRequired() {
    this.setData({
      requiredHostCount: '',
      requiredResults: [],
      requiredError: ''
    })
  },

  copyValue(event) {
    const value = event.currentTarget.dataset.value

    if (!value) {
      return
    }

    wx.setClipboardData({
      data: value,
      success: function () {
        wx.showToast({
          title: '已复制',
          icon: 'success'
        })
      }
    })
  }
})
