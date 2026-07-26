<template>
  <view class="camera-page">
    <view class="camera-stage">
      <camera
        v-if="showCamera"
        class="camera-frame"
        :device-position="devicePosition"
        :flash="flashMode"
        @error="cameraError"
      />
      <image v-else class="camera-frame" :src="photoPath" mode="aspectFill" />

      <view class="camera-tools">
        <view @tap="toggleAutoSave">{{ autoSave ? '自动存' : '手动存' }}</view>
        <view @tap="switchDevice">切换</view>
        <view @tap="toggleFlash">{{ flashLabel }}</view>
      </view>

      <view class="watermark-preview" :class="`style-${style}`">
        <text v-for="field in enabledFields" :key="field.key">{{ field.label }}：{{ field.value }}</text>
      </view>
    </view>

    <view class="bottom-panel">
      <view class="status">{{ statusText }}</view>
      <view class="actions">
        <button class="secondary-button" @tap="chooseImage">相册</button>
        <button class="secondary-button" @tap="retakeOrCapture">{{ showCamera ? '拍照' : '重拍' }}</button>
        <button class="primary-button" :loading="saving" @tap="save">保存</button>
      </view>
      <view class="setting-links">
        <text @tap="restoreDefaults">默认</text>
        <text @tap="chooseMapLocation">重新定位</text>
        <text v-if="isAdminMode" @tap="openSettings">更多</text>
      </view>
    </view>

    <view v-if="showPinDialog" class="mask pin-mask" @tap="closePinDialog">
      <view class="pin-dialog" @tap.stop>
        <view class="pin-title">高级水印设置</view>
        <view class="pin-tip">请输入管理口令</view>
        <input v-model="pinValue" class="pin-input" type="number" maxlength="4" password focus />
        <view class="pin-actions">
          <button class="secondary-button" @tap="closePinDialog">取消</button>
          <button class="primary-button" @tap="unlockAdminMode">确认</button>
        </view>
      </view>
    </view>

    <view v-if="settingsVisible" class="mask" @tap="settingsVisible=false">
      <view class="sheet" @tap.stop>
        <view class="sheet-head"><text class="sheet-title">水印设置</text><text @tap="settingsVisible=false">完成</text></view>
        <scroll-view scroll-y class="sheet-body">
          <view class="section-label">水印模板</view>
          <view class="style-row">
            <view v-for="item in styles" :key="item.value" :class="{ active: style === item.value }" @tap="style=item.value">{{ item.label }}</view>
          </view>
          <view v-for="field in fields" :key="field.key" class="field-row">
            <view class="field-head"><text>{{ field.label }}</text><switch :checked="field.enabled" color="#2f5f8f" @change="field.enabled=$event.detail.value" /></view>
            <picker v-if="field.key==='siteType'" :range="siteTypes" @change="field.value=siteTypes[$event.detail.value]"><view class="field-value">{{ field.value }}</view></picker>
            <picker v-else-if="field.key==='date'" mode="date" :value="field.value" @change="field.value=$event.detail.value"><view class="field-value">{{ field.value }}</view></picker>
            <picker v-else-if="field.key==='time'" mode="time" :value="field.value" @change="field.value=$event.detail.value"><view class="field-value">{{ field.value }}</view></picker>
            <view v-else-if="field.key==='location'" class="location-edit"><input v-model="field.value" class="field-input" /><text @tap="chooseMapLocation">地图选择</text></view>
            <input v-else v-model="field.value" class="field-input" />
          </view>
          <button class="restore-button" @tap="restoreDefaults">恢复默认水印</button>
          <view class="admin-exit" @tap="exitAdminMode">退出高级设置</view>
        </scroll-view>
      </view>
    </view>

    <canvas canvas-id="watermarkCanvas" class="canvas" :style="{ width: canvasWidth + 'px', height: canvasHeight + 'px' }" />
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const ADMIN_MODE_STORAGE_KEY = 'watermark_admin_mode'
const ADMIN_MODE_PIN = '2026'
const FLASH_UNLOCK_TAP_COUNT = 5
const FLASH_UNLOCK_TAP_INTERVAL = 2000

const now = () => {
  const date = new Date()
  const pad = value => String(value).padStart(2, '0')
  return { date: `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`, time: `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}` }
}

const createDefaultFields = () => {
  const stamp = now()
  return [
    { key: 'date', label: '日期', value: stamp.date, enabled: true },
    { key: 'time', label: '时间', value: stamp.time, enabled: true },
    { key: 'location', label: '定位', value: '正在获取位置', enabled: true },
    { key: 'note', label: '备注', value: '现场支撑', enabled: true },
    { key: 'operator', label: '人员/部门', value: '江苏有线南京分公司', enabled: true },
    { key: 'siteType', label: '现场类型', value: '现场巡检', enabled: true }
  ]
}

const fields = ref(createDefaultFields())
const styles = [{ value: 'simple', label: '简洁' }, { value: 'panel', label: '信息块' }, { value: 'bar', label: '底栏' }, { value: 'stamp', label: '巡检' }]
const siteTypes = ['现场巡检', '网络运维', '装维支撑', '工程支撑', '故障处理']
const style = ref('panel')
const showCamera = ref(true)
const devicePosition = ref('back')
const flashMode = ref('off')
const photoPath = ref('')
const saving = ref(false)
const autoSave = ref(false)
const settingsVisible = ref(false)
const showPinDialog = ref(false)
const pinValue = ref('')
const isAdminMode = ref(false)
const statusText = ref('正在获取当前位置')
const canvasWidth = ref(1)
const canvasHeight = ref(1)
let camera = null
let flashTapCount = 0
let flashTapTimer = null

const enabledFields = computed(() => fields.value.filter(item => item.enabled && item.value))
const flashLabel = computed(() => ({ off: '闪光', on: '常亮', auto: '自动' })[flashMode.value])
const field = key => fields.value.find(item => item.key === key)

onMounted(() => {
  camera = uni.createCameraContext()
  restoreAdminMode()
  getLocation()
})

onBeforeUnmount(() => {
  camera = null
  clearTimeout(flashTapTimer)
})

function refreshTime () {
  const stamp = now()
  field('date').value = stamp.date
  field('time').value = stamp.time
}

function restoreAdminMode () {
  const saved = uni.getStorageSync(ADMIN_MODE_STORAGE_KEY)
  if (saved && saved.enabled && Number(saved.expiresAt) > Date.now()) isAdminMode.value = true
  else uni.removeStorageSync(ADMIN_MODE_STORAGE_KEY)
}

function nextMidnight () {
  const date = new Date()
  date.setHours(24, 0, 0, 0)
  return date.getTime()
}

function recordFlashTap () {
  flashTapCount += 1
  clearTimeout(flashTapTimer)
  if (flashTapCount >= FLASH_UNLOCK_TAP_COUNT) {
    flashTapCount = 0
    showPinDialog.value = true
    return
  }
  flashTapTimer = setTimeout(() => { flashTapCount = 0 }, FLASH_UNLOCK_TAP_INTERVAL)
}

function closePinDialog () {
  showPinDialog.value = false
  pinValue.value = ''
}

function unlockAdminMode () {
  if (pinValue.value !== ADMIN_MODE_PIN) {
    uni.showToast({ title: '口令不正确', icon: 'none' })
    return
  }
  isAdminMode.value = true
  uni.setStorageSync(ADMIN_MODE_STORAGE_KEY, { enabled: true, expiresAt: nextMidnight() })
  closePinDialog()
  settingsVisible.value = true
}

function openSettings () {
  if (isAdminMode.value) settingsVisible.value = true
}

function exitAdminMode () {
  uni.removeStorageSync(ADMIN_MODE_STORAGE_KEY)
  isAdminMode.value = false
  settingsVisible.value = false
  statusText.value = '已退出高级设置'
}

function setLocation (text) {
  if (text) field('location').value = text
}

function getLocation () {
  statusText.value = '正在获取当前位置'
  uni.getLocation({
    type: 'gcj02',
    success: response => {
      const directAddress = response.address || response.name || ''
      setLocation(directAddress || '当前位置已获取，请重新定位选择位置')
      statusText.value = directAddress ? '当前位置已更新' : '当前位置已获取'
    },
    fail: () => {
      setLocation('位置不可用')
      statusText.value = '定位失败，仍可生成照片'
    }
  })
}

function chooseMapLocation () {
  uni.chooseLocation({
    success: response => {
      const location = [response.name, response.address].filter(Boolean).join(' · ')
      setLocation(location || '已选择位置')
      statusText.value = '当前位置已更新'
    },
    fail: () => uni.showToast({ title: '未选择位置', icon: 'none' })
  })
}

function switchDevice () { devicePosition.value = devicePosition.value === 'back' ? 'front' : 'back' }
function toggleFlash () {
  flashMode.value = flashMode.value === 'off' ? 'on' : flashMode.value === 'on' ? 'auto' : 'off'
  recordFlashTap()
}
function toggleAutoSave () {
  autoSave.value = !autoSave.value
  statusText.value = autoSave.value ? '拍照后将自动保存' : '拍照后需手动保存'
}
function cameraError () { statusText.value = '相机启动失败，请检查相机权限' }
function retakeOrCapture () {
  if (!showCamera.value) {
    photoPath.value = ''
    showCamera.value = true
    return
  }
  capture()
}
function capture () {
  if (!camera) camera = uni.createCameraContext()
  camera.takePhoto({
    quality: 'high',
    success: response => {
      photoPath.value = response.tempImagePath
      showCamera.value = false
      refreshTime()
      statusText.value = '照片已拍摄'
      if (autoSave.value) save()
    },
    fail: () => uni.showToast({ title: '拍照失败', icon: 'none' })
  })
}
function chooseImage () {
  uni.chooseImage({
    count: 1,
    sizeType: ['original', 'compressed'],
    sourceType: ['album'],
    success: response => {
      photoPath.value = response.tempFilePaths[0]
      showCamera.value = false
      refreshTime()
      statusText.value = '已选择照片'
    }
  })
}

function restoreDefaults () {
  uni.showModal({
    title: '恢复默认',
    content: '将恢复默认水印字段、样式和开关，不会清空已拍照片。',
    confirmText: '恢复',
    success: result => {
      if (!result.confirm) return
      fields.value = createDefaultFields()
      style.value = 'panel'
      getLocation()
      uni.showToast({ title: '已恢复默认水印', icon: 'success' })
    }
  })
}

function drawWatermark (context, width, height) {
  const lines = enabledFields.value
  if (!lines.length) return
  const fontSize = Math.max(22, Math.round(width * 0.026))
  const padding = Math.max(22, Math.round(width * 0.024))
  const lineHeight = Math.round(fontSize * 1.5)
  const shownLines = lines.slice(0, style.value === 'bar' ? 3 : 6)
  let x = padding
  let y = height - (padding * 2 + lineHeight * shownLines.length) - padding
  let panelWidth = Math.min(width - padding * 2, Math.round(width * 0.72))
  let panelHeight = padding * 2 + lineHeight * shownLines.length

  if (style.value === 'simple') {
    x = padding
    y = padding
    panelWidth = 0
    panelHeight = 0
  } else if (style.value === 'bar') {
    x = 0
    y = height - (padding * 2 + lineHeight * shownLines.length + fontSize)
    panelWidth = width
    panelHeight = height - y
  } else if (style.value === 'stamp') {
    panelWidth = Math.min(width - padding * 2, Math.round(width * 0.58))
    panelHeight += fontSize
    x = width - panelWidth - padding
    y = padding
  }

  if (style.value !== 'simple') {
    context.setGlobalAlpha(0.78)
    context.setFillStyle(style.value === 'stamp' ? '#f6f8fa' : '#17212c')
    context.fillRect(x, y, panelWidth, panelHeight)
    context.setGlobalAlpha(1)
    context.setFillStyle('#2f8cc8')
    context.fillRect(x, y, style.value === 'bar' ? panelWidth : 8, 8)
  }
  context.setFontSize(fontSize)
  context.setFillStyle(style.value === 'stamp' ? '#202832' : '#ffffff')
  shownLines.forEach((item, index) => context.fillText(`${item.label}：${String(item.value).slice(0, 36)}`, x + padding, y + padding + fontSize + index * lineHeight))
}

function save () {
  if (!photoPath.value) {
    uni.showToast({ title: '请先拍照或从相册选择', icon: 'none' })
    return
  }
  saving.value = true
  refreshTime()
  uni.getImageInfo({
    src: photoPath.value,
    success: info => {
      const scale = Math.min(1, 1280 / info.width)
      const width = Math.round(info.width * scale)
      const height = Math.round(info.height * scale)
      canvasWidth.value = width
      canvasHeight.value = height
      setTimeout(() => {
        const context = uni.createCanvasContext('watermarkCanvas')
        context.drawImage(photoPath.value, 0, 0, width, height)
        drawWatermark(context, width, height)
        context.draw(false, () => {
          uni.canvasToTempFilePath({
            canvasId: 'watermarkCanvas', destWidth: width, destHeight: height, fileType: 'jpg', quality: 0.92,
            success: result => uni.saveImageToPhotosAlbum({
              filePath: result.tempFilePath,
              success: () => { statusText.value = '已保存到相册'; uni.showToast({ title: '已保存', icon: 'success' }) },
              fail: () => uni.showToast({ title: '请允许保存到相册', icon: 'none' }),
              complete: () => { saving.value = false }
            }),
            fail: () => { saving.value = false; uni.showToast({ title: '生成失败', icon: 'none' }) }
          })
        })
      }, 60)
    },
    fail: () => { saving.value = false; uni.showToast({ title: '读取图片失败', icon: 'none' }) }
  })
}
</script>

<style scoped>
.camera-page{position:fixed;inset:0;display:flex;flex-direction:column;background:#111820}.camera-stage{position:relative;flex:1;min-height:0;overflow:hidden}.camera-frame{position:absolute;inset:0;width:100%;height:100%;z-index:1}.camera-tools{position:absolute;z-index:3;right:24rpx;top:24rpx;display:flex;flex-direction:column;gap:14rpx}.camera-tools view{min-width:78rpx;padding:16rpx 12rpx;border:1rpx solid #ffffff88;background:#122033cc;color:#fff;font-size:21rpx;text-align:center}.watermark-preview{position:absolute;z-index:3;left:26rpx;bottom:26rpx;max-width:80%;padding:16rpx 20rpx;background:#17212cbb;color:#fff;font-size:22rpx;line-height:1.5}.watermark-preview text{display:block}.style-simple{top:26rpx;bottom:auto;background:transparent;text-shadow:1rpx 1rpx 4rpx #000}.style-bar{left:0;right:0;bottom:0;max-width:none}.style-stamp{left:auto;right:26rpx;top:190rpx;bottom:auto;background:#f6f8fad9;color:#202832;border-top:8rpx solid #2f8cc8}.bottom-panel{position:relative;z-index:4;padding:16rpx 24rpx calc(24rpx + env(safe-area-inset-bottom));background:#fff}.status{color:#697788;font-size:21rpx}.actions{display:grid;grid-template-columns:repeat(3,1fr);gap:12rpx;margin-top:14rpx}.actions button{min-height:74rpx;font-size:24rpx}.setting-links{display:flex;justify-content:space-between;margin-top:16rpx;color:#2f5f8f;font-size:23rpx}.mask{position:fixed;z-index:20;inset:0;display:flex;align-items:flex-end;background:#0008}.pin-mask{align-items:center;justify-content:center}.pin-dialog{width:560rpx;padding:42rpx 32rpx;border-radius:22rpx;background:#fff}.pin-title{color:#1b2c40;font-size:32rpx;font-weight:700;text-align:center}.pin-tip{margin-top:16rpx;color:#728094;font-size:24rpx;text-align:center}.pin-input{height:76rpx;margin-top:26rpx;padding:0 18rpx;border:1rpx solid #d5dee8;border-radius:10rpx;background:#f8fafc;font-size:30rpx}.pin-actions{display:grid;grid-template-columns:1fr 1fr;gap:16rpx;margin-top:28rpx}.pin-actions button{margin:0}.sheet{width:100%;height:74vh;border-radius:24rpx 24rpx 0 0;background:#fff}.sheet-head{display:flex;justify-content:space-between;padding:26rpx;border-bottom:1rpx solid #e6ebf0;color:#2f5f8f}.sheet-title{color:#25364a;font-size:29rpx;font-weight:700}.sheet-body{height:calc(74vh - 90rpx);padding:0 24rpx}.section-label{margin-top:24rpx;color:#728094;font-size:22rpx}.style-row{display:grid;grid-template-columns:repeat(4,1fr);gap:10rpx;margin:16rpx 0 20rpx}.style-row view{padding:16rpx 4rpx;border:1rpx solid #d5dee8;text-align:center;color:#5b6a7c;font-size:22rpx}.style-row .active{border-color:#2f5f8f;background:#e8eef4;color:#2f5f8f}.field-row{padding:18rpx 0;border-top:1rpx solid #edf1f5}.field-head{display:flex;justify-content:space-between;color:#25364a;font-size:25rpx}.field-value,.field-input{box-sizing:border-box;width:100%;min-height:66rpx;margin-top:10rpx;padding:0 14rpx;border:1rpx solid #dce3eb;background:#f8fafc;color:#34465a;font-size:23rpx;line-height:66rpx}.location-edit{display:flex;gap:12rpx;align-items:center}.location-edit .field-input{flex:1}.location-edit text{flex:none;margin-top:10rpx;color:#2f5f8f;font-size:22rpx}.restore-button{margin:30rpx 0 22rpx;border:1rpx solid #cbd7e3;background:#fff;color:#2f5f8f;font-size:24rpx}.admin-exit{padding:22rpx 0 50rpx;color:#b0413e;font-size:24rpx;text-align:center}.canvas{position:fixed;left:0;top:0;opacity:0;pointer-events:none}
</style>
