const {
  WATERMARK_STYLE_OPTIONS,
  FIELD_OPTIONS,
  createDefaultFields,
  getEnabledWatermarkLines,
  formatDate,
  formatTime
} = require('../../utils/watermark')
const {
  getCurrentLocation,
  chooseMapLocation,
  formatCoordinateText,
  getLocationErrorMessage
} = require('../../utils/location')
const { drawWatermark } = require('../../utils/watermark-draw')

const SITE_TYPE_OPTIONS = ['现场巡检', '网络运维', '装维支撑', '工程支撑', '故障处理']
const ADMIN_MODE_STORAGE_KEY = 'watermark_admin_mode'
const ADMIN_MODE_PIN = '2026'
const FLASH_UNLOCK_TAP_COUNT = 5
const FLASH_UNLOCK_TAP_INTERVAL = 2000

function buildFieldRows(fields) {
  return FIELD_OPTIONS.map(function (item) {
    const field = fields[item.key] || {
      label: item.label,
      value: '',
      enabled: false
    }

    return {
      key: item.key,
      label: item.label,
      editable: item.editable,
      isDate: item.key === 'date',
      isTime: item.key === 'time',
      isDateTime: item.key === 'date' || item.key === 'time',
      isLocation: item.key === 'location',
      isSiteType: item.key === 'siteType',
      value: field.value,
      pickerValue: item.key === 'time' ? field.value.slice(0, 5) : field.value,
      enabled: field.enabled,
      placeholder: '请输入' + item.label
    }
  })
}

function buildStyleOptions(activeKey) {
  return WATERMARK_STYLE_OPTIONS.map(function (item) {
    return {
      key: item.key,
      label: item.label,
      activeClass: activeKey === item.key ? 'active' : ''
    }
  })
}

function buildPreviewLines(fields) {
  return getEnabledWatermarkLines(fields).map(function (item) {
    return {
      key: item.key,
      text: item.label + '：' + item.value
    }
  })
}

function getWatermarkClass(style) {
  if (style === 'simple') {
    return 'watermark-simple-style'
  }

  if (style === 'bar') {
    return 'watermark-bar-style'
  }

  if (style === 'stamp') {
    return 'watermark-stamp-style'
  }

  return 'watermark-panel-style'
}

function mergeLocationText(location) {
  const name = location.name || ''
  const address = location.address || ''

  if (name && address && address.indexOf(name) === -1) {
    return name + ' ' + address
  }

  return name || address || formatCoordinateText(location.latitude, location.longitude)
}

function getTodayAdminExpiresAt() {
  const expiresAt = new Date()

  expiresAt.setHours(24, 0, 0, 0)
  return expiresAt.getTime()
}

function isAdminCacheValid() {
  const cache = wx.getStorageSync(ADMIN_MODE_STORAGE_KEY)

  if (!cache || typeof cache !== 'object') {
    return false
  }

  return cache.enabled === true && Number(cache.expiresAt) > Date.now()
}

Page({
  data: {
    cameraReady: false,
    cameraError: '',
    devicePosition: 'back',
    deviceLabel: '后置摄像头',
    cameraStateText: '后置摄像头',
    photoPath: '',
    hasPhoto: false,
    showCamera: true,
    disableCameraControls: false,
    isTaking: false,
    flashMode: 'off',
    flashLabel: '闪光',
    watermarkStyle: 'panel',
    watermarkClass: getWatermarkClass('panel'),
    watermarkPreviewLines: [],
    styleOptions: buildStyleOptions('panel'),
    fieldOptions: [],
    watermarkFields: {},
    currentLocation: null,
    isLocating: false,
    locationStatus: '正在获取定位',
    outputPath: '',
    hasOutput: false,
    statusText: '调整水印参数后可直接拍照保存',
    isGenerating: false,
    isSaving: false,
    photoButtonText: '拍照',
    autoSave: false,
    autoSaveText: '自动保存',
    autoSaveClass: '',
    isAdminMode: false,
    showDateTimeSheet: false,
    showMoreSheet: false,
    showPinDialog: false,
    pinValue: '',
    dateTimeSnapshot: null,
    siteTypeOptions: SITE_TYPE_OPTIONS,
    siteTypeIndex: 0,
    canvasWidth: 750,
    canvasHeight: 1000,
    canvasStyle: 'width: 750px; height: 1000px;'
  },

  onLoad() {
    const watermarkFields = createDefaultFields()
    const isAdminMode = isAdminCacheValid()

    this.setData({
      isAdminMode,
      watermarkFields,
      fieldOptions: buildFieldRows(watermarkFields),
      watermarkPreviewLines: buildPreviewLines(watermarkFields),
      siteTypeIndex: this.getSiteTypeIndex(watermarkFields.siteType.value)
    })

    this.getCurrentPosition()
  },

  onReady() {
    this.cameraContext = wx.createCameraContext()
  },

  onUnload() {
    this.clearFlashTapTimer()
  },

  refreshWatermarkState(extra) {
    const patch = Object.assign({
      fieldOptions: buildFieldRows(this.data.watermarkFields),
      watermarkPreviewLines: buildPreviewLines(this.data.watermarkFields),
      outputPath: '',
      hasOutput: false
    }, extra || {})

    this.setData(patch)
  },

  getSiteTypeIndex(value) {
    const index = SITE_TYPE_OPTIONS.indexOf(value)

    return index >= 0 ? index : 0
  },

  onCameraReady() {
    this.setData({
      cameraReady: true,
      cameraError: ''
    })
  },

  onCameraError(event) {
    const detail = event.detail || {}
    this.setData({
      cameraReady: false,
      cameraError: detail.errMsg || '相机启动失败，请检查微信相机权限'
    })
  },

  switchDevice() {
    const nextPosition = this.data.devicePosition === 'back' ? 'front' : 'back'

    this.setData({
      devicePosition: nextPosition,
      deviceLabel: nextPosition === 'back' ? '后置摄像头' : '前置摄像头',
      cameraStateText: nextPosition === 'back' ? '后置摄像头' : '前置摄像头',
      cameraReady: false,
      cameraError: ''
    })
  },

  toggleFlash() {
    const nextMode = this.data.flashMode === 'off'
      ? 'on'
      : this.data.flashMode === 'on'
        ? 'auto'
        : 'off'

    const nextLabel = nextMode === 'off'
      ? '闪光'
      : nextMode === 'on'
        ? '常亮'
        : '自动'

    this.setData({
      flashMode: nextMode,
      flashLabel: nextLabel
    })

    this.recordFlashTap()
  },

  recordFlashTap() {
    this.flashTapCount = (this.flashTapCount || 0) + 1
    this.clearFlashTapTimer()

    if (this.flashTapCount >= FLASH_UNLOCK_TAP_COUNT) {
      this.flashTapCount = 0
      this.openPinDialog()
      return
    }

    this.flashTapTimer = setTimeout(() => {
      this.flashTapCount = 0
      this.flashTapTimer = null
    }, FLASH_UNLOCK_TAP_INTERVAL)
  },

  clearFlashTapTimer() {
    if (this.flashTapTimer) {
      clearTimeout(this.flashTapTimer)
      this.flashTapTimer = null
    }
  },

  openPinDialog() {
    this.setData({
      showPinDialog: true,
      pinValue: ''
    })
  },

  closePinDialog() {
    this.setData({
      showPinDialog: false,
      pinValue: ''
    })
  },

  onPinInput(event) {
    const pinValue = event.detail.value.replace(/\D/g, '').slice(0, 4)

    this.setData({ pinValue })
  },

  confirmPin() {
    if (this.data.pinValue !== ADMIN_MODE_PIN) {
      wx.showToast({
        title: 'PIN 不正确',
        icon: 'none'
      })
      return
    }

    wx.setStorageSync(ADMIN_MODE_STORAGE_KEY, {
      enabled: true,
      expiresAt: getTodayAdminExpiresAt()
    })
    this.setData({
      isAdminMode: true,
      showPinDialog: false,
      pinValue: '',
      statusText: '高级设置已开启'
    })
  },

  handlePhotoTap() {
    if (this.data.hasPhoto) {
      this.retakePhoto()
      return
    }

    this.takePhoto()
  },

  takePhoto() {
    if (this.data.isTaking) {
      return
    }

    if (!this.cameraContext) {
      this.cameraContext = wx.createCameraContext()
    }

    this.setData({ isTaking: true })

    this.cameraContext.takePhoto({
      quality: 'high',
      success: (result) => {
        this.setData({
          photoPath: result.tempImagePath,
          hasPhoto: true,
          showCamera: false,
          cameraStateText: '预览',
          disableCameraControls: true,
          photoButtonText: '重拍',
          statusText: '照片已拍摄，可直接保存水印图',
          outputPath: '',
          hasOutput: false,
          cameraError: ''
        }, () => {
          if (this.data.autoSave) {
            this.handleSaveTap()
          }
        })
      },
      fail: (error) => {
        this.setData({
          cameraError: error.errMsg || '拍照失败，请重试'
        })
      },
      complete: () => {
        this.setData({ isTaking: false })
      }
    })
  },

  retakePhoto() {
    this.setData({
      photoPath: '',
      hasPhoto: false,
      showCamera: true,
      cameraStateText: this.data.deviceLabel,
      disableCameraControls: false,
      outputPath: '',
      hasOutput: false,
      statusText: '调整水印参数后可直接拍照保存',
      photoButtonText: '拍照',
      cameraReady: false,
      cameraError: ''
    })
  },

  selectWatermarkStyle(event) {
    if (!this.data.isAdminMode) {
      return
    }

    const watermarkStyle = event.currentTarget.dataset.style

    this.setData({
      watermarkStyle,
      watermarkClass: getWatermarkClass(watermarkStyle),
      styleOptions: buildStyleOptions(watermarkStyle),
      outputPath: '',
      hasOutput: false
    })
  },

  openDateTimeSheet() {
    if (!this.data.isAdminMode) {
      return
    }

    this.setData({
      showDateTimeSheet: true,
      showMoreSheet: false,
      dateTimeSnapshot: {
        date: this.data.watermarkFields.date.value,
        time: this.data.watermarkFields.time.value
      }
    })
  },

  closeDateTimeSheet() {
    this.setData({
      showDateTimeSheet: false,
      dateTimeSnapshot: null
    })
  },

  cancelDateTimeSheet() {
    const snapshot = this.data.dateTimeSnapshot

    if (snapshot) {
      const patch = {
        'watermarkFields.date.value': snapshot.date,
        'watermarkFields.time.value': snapshot.time
      }

      this.setData(patch, () => {
        this.refreshWatermarkState({
          showDateTimeSheet: false,
          dateTimeSnapshot: null
        })
      })
      return
    }

    this.closeDateTimeSheet()
  },

  restoreCurrentDateTime() {
    this.updateFieldValue('date', formatDate())
    this.updateFieldValue('time', formatTime())
  },

  openMoreSheet() {
    if (!this.data.isAdminMode) {
      return
    }

    this.setData({
      showMoreSheet: true,
      showDateTimeSheet: false
    })
  },

  exitAdminMode() {
    wx.setStorageSync(ADMIN_MODE_STORAGE_KEY, false)
    this.setData({
      isAdminMode: false,
      showMoreSheet: false,
      showDateTimeSheet: false,
      statusText: '已恢复标准模式'
    })
  },

  closeMoreSheet() {
    this.setData({
      showMoreSheet: false
    })
  },

  stopSheetTap() {},

  toggleAutoSave() {
    const autoSave = !this.data.autoSave

    this.setAutoSave(autoSave)
  },

  setAutoSave(autoSave) {
    this.setData({
      autoSave: autoSave,
      autoSaveClass: autoSave ? 'active' : '',
      statusText: autoSave ? '拍照后将自动保存到相册' : '拍照后可手动保存'
    })
  },

  toggleField(event) {
    if (!this.data.isAdminMode) {
      return
    }

    const key = event.currentTarget.dataset.key
    const field = this.data.watermarkFields[key]
    const patch = {}

    if (!field) {
      return
    }

    patch['watermarkFields.' + key + '.enabled'] = event.detail.value

    this.setData(patch, () => {
      this.refreshWatermarkState()
    })
  },

  onFieldInput(event) {
    if (!this.data.isAdminMode) {
      return
    }

    const key = event.currentTarget.dataset.key

    this.updateFieldValue(key, event.detail.value)
  },

  onDateChange(event) {
    if (!this.data.isAdminMode) {
      return
    }

    this.updateFieldValue('date', event.detail.value)
  },

  onTimeChange(event) {
    if (!this.data.isAdminMode) {
      return
    }

    this.updateFieldValue('time', event.detail.value)
  },

  onSiteTypeChange(event) {
    if (!this.data.isAdminMode) {
      return
    }

    const index = Number(event.detail.value)
    const value = SITE_TYPE_OPTIONS[index] || SITE_TYPE_OPTIONS[0]

    this.updateFieldValue('siteType', value, {
      siteTypeIndex: index
    })
  },

  updateFieldValue(key, value, extra) {
    const patch = {}

    patch['watermarkFields.' + key + '.value'] = value

    this.setData(patch, () => {
      this.refreshWatermarkState(extra)
    })
  },

  restoreDefault() {
    wx.showModal({
      title: '恢复默认',
      content: '将恢复默认水印字段、样式和开关，不会清空已拍照片。',
      confirmText: '恢复',
      success: (result) => {
        if (!result.confirm) {
          return
        }

        const watermarkFields = createDefaultFields()

        this.setData({
          watermarkFields,
          watermarkStyle: 'panel',
          watermarkClass: getWatermarkClass('panel'),
          styleOptions: buildStyleOptions('panel'),
          siteTypeIndex: this.getSiteTypeIndex(watermarkFields.siteType.value),
          showDateTimeSheet: false,
          showMoreSheet: false,
          statusText: '水印设置已恢复默认'
        }, () => {
          this.refreshWatermarkState()
          this.getCurrentPosition()
        })
      }
    })
  },

  getCurrentPosition() {
    if (this.data.isLocating) {
      return
    }

    this.setData({
      isLocating: true,
      locationStatus: '正在获取当前位置',
      statusText: '正在获取当前位置'
    })

    getCurrentLocation()
      .then((location) => this.applyLocation(location))
      .catch((error) => {
        this.setData({
          locationStatus: getLocationErrorMessage(error),
          statusText: getLocationErrorMessage(error)
        })
      })
      .then(() => {
        this.setData({ isLocating: false })
      })
      .catch(() => {
        this.setData({ isLocating: false })
      })
  },

  choosePosition() {
    if (!this.data.isAdminMode) {
      return
    }

    chooseMapLocation()
      .then((location) => {
        const locationText = mergeLocationText(location)

        this.updateLocationField({
          latitude: location.latitude,
          longitude: location.longitude,
          address: locationText,
          adcode: ''
        }, '位置已选择')
      })
      .catch((error) => {
        const message = error && error.errMsg && error.errMsg.indexOf('cancel') >= 0
          ? '已取消选择位置'
          : getLocationErrorMessage(error)

        this.setData({
          locationStatus: message,
          statusText: message
        })

        wx.showToast({
          title: message,
          icon: 'none'
        })
      })
  },

  applyLocation(location) {
    const coordinateText = formatCoordinateText(location.latitude, location.longitude)

    this.updateLocationField({
      latitude: location.latitude,
      longitude: location.longitude,
      address: coordinateText,
      adcode: ''
    }, '定位已更新')
    return Promise.resolve()
  },

  updateLocationField(location, statusText) {
    const watermarkFields = Object.assign({}, this.data.watermarkFields, {
      location: {
        label: this.data.watermarkFields.location.label,
        value: location.address,
        enabled: this.data.watermarkFields.location.enabled
      }
    })

    this.setData({
      currentLocation: location,
      watermarkFields: watermarkFields,
      locationStatus: statusText,
      statusText: statusText
    }, () => {
      this.refreshWatermarkState()
    })
  },

  handleSaveTap() {
    if (!this.data.hasPhoto) {
      wx.showToast({
        title: '请先拍照',
        icon: 'none'
      })
      return
    }

    if (this.data.hasOutput && this.data.outputPath) {
      this.saveWatermarkedPhoto()
      return
    }

    this.generateWatermarkedPhoto(function () {
      this.saveWatermarkedPhoto()
    }.bind(this))
  },

  generateWatermarkedPhoto(callback) {
    if (!this.data.photoPath || this.data.isGenerating) {
      return
    }

    this.setData({
      isGenerating: true,
      statusText: '正在生成水印图片'
    })

    wx.getImageInfo({
      src: this.data.photoPath,
      success: (imageInfo) => {
        const maxWidth = 1280
        const scale = Math.min(1, maxWidth / imageInfo.width)
        const canvasWidth = Math.round(imageInfo.width * scale)
        const canvasHeight = Math.round(imageInfo.height * scale)

        this.setData({
          canvasWidth,
          canvasHeight,
          canvasStyle: 'width: ' + canvasWidth + 'px; height: ' + canvasHeight + 'px;'
        }, () => {
          this.drawWatermarkedImage(canvasWidth, canvasHeight, callback)
        })
      },
      fail: () => {
        this.setData({
          isGenerating: false,
          statusText: '读取照片失败，请重新拍照'
        })
      }
    })
  },

  drawWatermarkedImage(canvasWidth, canvasHeight, callback) {
    const ctx = wx.createCanvasContext('watermarkCanvas', this)

    ctx.drawImage(this.data.photoPath, 0, 0, canvasWidth, canvasHeight)
    drawWatermark(ctx, {
      width: canvasWidth,
      height: canvasHeight,
      fields: this.data.watermarkFields,
      style: this.data.watermarkStyle
    })

    ctx.draw(false, () => {
      wx.canvasToTempFilePath({
        canvasId: 'watermarkCanvas',
        width: canvasWidth,
        height: canvasHeight,
        destWidth: canvasWidth,
        destHeight: canvasHeight,
        fileType: 'jpg',
        quality: 0.92,
        success: (result) => {
          this.setData({
            outputPath: result.tempFilePath,
            hasOutput: true,
            statusText: '水印图片已生成',
            isGenerating: false
          }, () => {
            if (typeof callback === 'function') {
              callback()
            }
          })
        },
        fail: () => {
          this.setData({
            statusText: '水印图片生成失败，请重试',
            isGenerating: false
          })
        }
      }, this)
    })
  },

  saveWatermarkedPhoto() {
    if (!this.data.outputPath || this.data.isSaving) {
      return
    }

    this.setData({
      isSaving: true,
      statusText: '正在保存到相册'
    })

    wx.saveImageToPhotosAlbum({
      filePath: this.data.outputPath,
      success: () => {
        this.setData({
          statusText: '已保存到相册'
        })
        wx.showToast({
          title: '已保存',
          icon: 'success'
        })
      },
      fail: (error) => {
        const message = error && error.errMsg && error.errMsg.includes('auth')
          ? '相册权限未开启，请在小程序设置中允许保存到相册'
          : '保存失败，请稍后重试'

        this.setData({
          statusText: message
        })
      },
      complete: () => {
        this.setData({
          isSaving: false
        })
      }
    })
  }
})
