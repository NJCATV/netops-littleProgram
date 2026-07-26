# 本文件已归档

本文件已归档，当前项目以根目录 AGENTS.md 和《统一工单池_含OSS融合_技术与实施总规划.md》为准。

# CHANGELOG

## Fix - 优化安卓底部操作栏与按需注入

完成内容：
- 优化水印相机底部操作栏宽度计算，避免部分安卓机型保存按钮超出屏幕
- 重置底部操作按钮默认边距，提升窄屏兼容性
- 开启小程序组件按需注入

提交记录：
- commit message: fix: improve android camera actions layout

## Fix - 补充地理位置接口声明

完成内容：
- 在 `app.json` 中补充 `getLocation` 与 `chooseLocation` 接口声明
- 保留现有位置权限说明，满足微信提交前的接口配置检查

提交记录：
- commit message: fix: declare location private interfaces

## Fix - 调整水印相机巡检样式位置

完成内容：
- 调整水印相机巡检样式的预览位置，避免遮挡右上角操作按钮
- 提高相机右上角操作按钮层级

提交记录：
- commit message: fix: prevent inspection watermark from covering camera controls

## Fix - 精简水印相机字段

完成内容：
- 移除不再需要的环境字段配置
- 确认水印相机更多设置中不再展示该字段

提交记录：
- commit message: fix: remove unused watermark field

## Phase 0 - 项目初始化与工程规范

完成内容：
- 初始化 Git 仓库并配置 `main` 分支
- 配置远程仓库 `git@github.com:NJCATV/littleProgram.git`
- 新增基础目录：`pages`、`components`、`utils`
- 新增 `AGENTS.md`
- 新增 `README.md`
- 新增 `ROADMAP.md`
- 新增 `CHANGELOG.md`
- 新增 `.gitignore`，避免提交依赖、临时文件、日志文件和本地配置

提交记录：
- commit message: chore: initialize project docs and development rules

## Phase 1 - 首页与便捷工具入口

完成内容：
- 新增小程序基础入口文件：`app.js`、`app.json`、`app.wxss`
- 新增微信开发者工具配置 `project.config.json`
- 新增 `sitemap.json`
- 新增首页 `pages/index/index`
- 新增登录入口占位
- 新增注册入口占位
- 新增便捷工具免登录入口
- 新增工具列表页 `pages/tools/index`
- 新增水印相机工具入口
- 新增水印相机占位页 `pages/watermark-camera/index`
- 更新 `README.md` 当前功能与目录结构说明

提交记录：
- commit message: feat: add home page and tool entry

## Phase 2 - TDesign 引入与基础视觉风格

完成内容：
- 新增 `package.json`
- 新增 `package-lock.json`
- 安装 `tdesign-miniprogram`
- 在 `app.json` 中配置全局 TDesign 基础组件 `t-button`、`t-icon`
- 在 `app.wxss` 中配置 TDesign 品牌色、按钮圆角和基础网管风格变量
- 补充通用细线和状态文本样式
- 更新 `README.md` 的当前功能、目录结构和 TDesign 安装构建说明

提交记录：
- commit message: chore: integrate TDesign and base theme

## Phase 3 - 水印相机基础能力

完成内容：
- 在 `app.json` 中声明 `scope.camera` 相机权限用途
- 将水印相机占位页替换为基础相机页
- 接入微信小程序 `camera` 组件
- 支持后置和前置摄像头切换
- 支持拍照并保存临时图片路径
- 支持照片预览
- 支持重新拍照
- 保留后续阶段说明，不实现水印字段、定位、Canvas 合成和保存相册
- 更新 `README.md` 当前功能和权限说明

提交记录：
- commit message: feat: implement basic watermark camera

## Phase 4 - 水印字段编辑与样式切换

完成内容：
- 重做首页为登录表单布局，保留免登录使用入口
- 清理页面中面向开发阶段的提示文案
- 未开放功能统一提示“加速开发中，敬请期待”
- 新增 `utils/watermark.js`，集中维护水印字段、样式和时间格式化逻辑
- 水印相机新增日期、时间、定位、备注、人员/部门字段
- 支持水印字段启用和关闭
- 支持可编辑字段手动修改
- 支持四种水印样式切换

提交记录：
- commit message: feat: add editable watermark fields and styles

## Phase 5 - 定位

完成内容：
- 新增 `utils/location.js`，封装 `wx.getLocation`、`wx.chooseLocation` 和定位错误提示
- 在 `app.json` 中声明 `scope.userLocation` 权限用途
- 水印相机支持获取当前位置
- 水印相机支持地图选择位置
- 定位字段支持自动更新和手动编辑

提交记录：
- commit message: feat: add location picker

## Phase 6 - Canvas 合成与保存相册

完成内容：
- 新增 `utils/watermark-draw.js`，封装 Canvas 水印绘制逻辑
- 在 `app.json` 中声明 `scope.writePhotosAlbum` 权限用途
- 水印相机支持将原图和水印字段合成为新图片
- 水印相机支持四种水印样式对应的 Canvas 绘制
- 支持预览生成后的水印图片
- 支持保存生成后的水印图片到系统相册
- 增加保存相册权限异常提示
- 更新 `README.md` 当前功能和权限说明

提交记录：
- commit message: feat: generate and save watermarked photos

## Fix - 水印相机白屏与登录页精简

完成内容：
- 精简登录页顶部，仅保留应用名称
- 删除密码登录和验证码登录切换区域
- 将“手机号”改为“用户名/手机号”
- 调整登录输入逻辑，用户名或手机号均可输入
- 修复水印相机页可能导致开发者工具和真机白屏的兼容性写法
- 将水印相机页复杂 WXML 表达式改为页面数据字段
- 将水印工具中的对象展开写法改为更稳妥的 `Object.assign`
- 重新执行微信开发者工具 `build-npm` 和 `preview`

提交记录：
- commit message: fix: resolve watermark camera blank screen

## Fix - 精简水印相机操作界面

完成内容：
- 修复水印相机页面横向溢出导致右侧白边的问题
- 将水印相机改为相机工作台布局，默认在相机画面上叠加水印预览
- 主操作区仅保留拍照和保存两个按钮
- 将前后摄像头切换和闪光灯控制放到画面右上角
- 将定位、选点和水印字段设置收到底部设置区
- 保存时自动生成带水印图片并写入系统相册
- 将隐藏 Canvas 放入 1px 裁剪容器，避免影响页面宽度
- 重新执行微信开发者工具 `build-npm` 和 `preview`

提交记录：
- commit message: refactor: simplify watermark camera workflow

## Fix - 精简水印参数与保存流程

完成内容：
- 移除不再需要的环境信息模块及相关文档说明
- 移除不再需要的额外分类字段
- 日期和时间支持选择修改，并提供“今天”和“当前时间”快捷设置
- 定位改为进入页面后自动获取，更多面板保留重新定位和选择位置
- 修复备注和人员/部门同时开启时水印显示挤压的问题
- 修复保存按钮只生成图片但不保存到相册的问题
- 新增拍照后自动保存到相册开关

提交记录：
- commit message: refactor: streamline watermark controls and saving

## Fix - 调整水印相机保存与快捷操作

完成内容：
- 将底部四个快捷按钮调整为“选择日期/时间”“选择位置”“恢复默认”“更多”
- 移除更多面板中的快捷设置模块
- 将自动保存开关移到相机画面右上角
- 取消拍照预览图点击放大，保存完成仅提示“已保存”
- 调整隐藏 Canvas 渲染方式，避免真机保存图片出现局部放大或裁剪

提交记录：
- commit message: fix: adjust watermark camera saving and quick controls

## Fix - 区分水印样式视觉

完成内容：
- 将“简洁”调整为左上角纯文字样式
- 将“信息块”保留为左下角信息卡样式
- 将“底栏”调整为底部全宽记录栏样式
- 将“巡检”调整为右上角工单留痕样式
- 同步调整相机预览层和 Canvas 保存图的样式表现

提交记录：
- commit message: fix: differentiate watermark styles

## Feature - 新增网络/IP 地址计算器

完成内容：
- 在便捷工具页新增“网络/IP 地址计算器”入口
- 新增页面 `pages/ip-calculator/ip-calculator`
- 新增 `utils/ipCalc.js`，封装 IPv4、CIDR、掩码、反掩码、二进制和地址数计算逻辑
- 支持 IP/CIDR 计算网络地址、广播地址、可用地址范围、地址数量和二进制结果
- 支持 CIDR 与点分十进制子网掩码互相换算
- 支持根据需要的可用地址数量反推推荐 CIDR
- 支持关键结果复制到剪贴板

提交记录：
- commit message: feat: add network ip calculator

## Fix - 调整 IP 计算器复制按钮

完成内容：
- 调整网络/IP 地址计算器结果项复制按钮的垂直对齐
- 完成上传前代码审查和基础校验

提交记录：
- commit message: fix: align ip calculator copy buttons

## Refactor - 优化水印相机设置交互

完成内容：
- 将水印相机页面调整为固定 100vh 布局，主页面不再上下滚动
- 保持底部拍照、保存和快捷操作栏始终可见
- 将时间/日期调整为底部弹出卡片
- 将更多设置调整为底部弹出卡片，仅卡片内部滚动
- 默认操作只恢复水印设置，不清空已拍照片

提交记录：
- commit message: refactor: improve watermark camera settings interaction
