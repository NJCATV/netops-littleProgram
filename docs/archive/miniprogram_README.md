# 本文件已归档

本文件已归档，当前项目以根目录 AGENTS.md 和《统一工单池_含OSS融合_技术与实施总规划.md》为准。

# 江苏有线南京分公司智维助手

## 项目简介

本项目是「江苏有线南京分公司智维助手」微信小程序，面向江苏有线南京分公司内部网络运维、装维、工程支撑人员，提供便捷工具入口和现场辅助能力。

## 小程序名称

江苏有线南京分公司智维助手

## 功能定位

- 内部网络运维工具助手
- 装维和工程支撑现场辅助工具
- 不接后台、不接数据库、不使用云开发
- 当前不实现真实登录鉴权

## 当前已实现功能

- Phase 0：项目初始化与工程规范
- 新增基础目录：`pages`、`components`、`utils`
- 新增工程文档：`AGENTS.md`、`README.md`、`ROADMAP.md`、`CHANGELOG.md`
- Phase 1：首页与便捷工具入口
- 首页包含登录、注册占位入口
- 首页提供便捷工具免登录入口
- 便捷工具页提供水印相机工具入口
- 便捷工具页提供网络/IP 地址计算器入口
- Phase 2：TDesign 引入与基础视觉风格
- 已安装 `tdesign-miniprogram`
- 已在 `app.json` 配置全局 TDesign 基础组件
- 已设置灰白蓝灰网管风格基础样式变量
- Phase 3：水印相机基础能力
- 水印相机页已接入 `camera` 组件
- 支持前后摄像头切换
- 支持拍照、照片预览和重新拍照
- Phase 4：水印字段编辑与样式切换
- 首页已调整为登录表单布局，并保留免登录使用入口
- 未开放功能统一提示“加速开发中，敬请期待”
- 水印相机支持字段启用、关闭和手动编辑
- 水印相机支持四种水印样式切换
- Phase 5：定位
- 新增定位和地图选点工具函数
- 水印相机支持自动获取当前位置、选择位置、手动编辑定位文本
- Phase 6：Canvas 合成与保存相册
- 新增 Canvas 水印绘制工具函数
- 水印相机支持生成带水印图片
- 支持预览生成结果
- 支持保存到系统相册
- 网络/IP 地址计算器
- 支持 IP/CIDR 计算网络地址、广播地址、可用地址范围和地址数量
- 支持 CIDR 与子网掩码互相换算
- 支持根据可用地址数量反推推荐 CIDR

## 技术栈

- 微信小程序原生开发
- WXML / WXSS / JavaScript / JSON
- TDesign Miniprogram
- JavaScript 工具函数
- Git / GitHub

## 目录结构说明

```text
.
├── AGENTS.md          # Codex 后续开发规则
├── README.md          # 项目工程说明
├── ROADMAP.md         # 阶段开发计划
├── CHANGELOG.md       # 阶段变更记录
├── app.js             # 小程序入口脚本
├── app.json           # 小程序全局配置
├── app.wxss           # 小程序全局样式
├── project.config.json # 微信开发者工具项目配置
├── sitemap.json       # 小程序索引配置
├── package.json       # npm 依赖配置
├── package-lock.json  # npm 锁定文件
├── pages/             # 小程序页面
│   ├── index/         # 首页
│   ├── tools/         # 便捷工具列表页
│   ├── watermark-camera/ # 水印相机工具页
│   └── ip-calculator/ # 网络/IP 地址计算器
├── components/        # 通用组件
└── utils/             # 通用工具函数
    └── watermark.js   # 水印字段、样式和时间工具
    └── location.js    # 定位和地图选点工具
    └── watermark-draw.js # Canvas 水印绘制工具
    └── ipCalc.js      # IPv4 网络和掩码计算工具
```

## Windows 本地开发说明

1. 安装微信开发者工具。
2. 安装 Node.js LTS。
3. 使用 PowerShell 或 Git Bash 进入项目目录。
4. 克隆或拉取仓库后，使用微信开发者工具打开本目录。
5. 后续如引入 npm 依赖，先执行安装，再在微信开发者工具中构建 npm。

## 微信开发者工具运行步骤

1. 打开微信开发者工具。
2. 选择「导入项目」。
3. 项目目录选择本仓库目录。
4. AppID 使用项目实际 AppID；没有 AppID 时可先选择测试号或游客模式进行本地预览。
5. 导入后检查 `app.json` 页面路径配置。
6. 如已安装 TDesign Miniprogram，执行「工具」->「构建 npm」。
7. 编译并预览小程序。

## TDesign Miniprogram 安装与构建 npm 步骤

后续 Phase 2 引入 TDesign Miniprogram 时执行：

```powershell
npm.cmd install
```

然后在微信开发者工具中执行：

```text
工具 -> 构建 npm
```

构建后根据 TDesign 官方组件路径在 `app.json` 或页面 JSON 中配置 `usingComponents`。

注意：不要提交 `node_modules` 或微信开发者工具构建生成的 `miniprogram_npm`，只提交 `package.json`、`package-lock.json` 以及小程序源码配置。

## 微信小程序后台权限和合法域名

后续使用定位、相册保存能力时，需要在微信小程序后台和开发者工具中检查：

- 开启位置相关权限说明。
- 使用相机和相册能力时，在 `app.json` 中补充必要的权限说明。
- 当前已声明 `scope.camera` 用于水印相机基础拍照。
- 当前已声明 `scope.userLocation` 用于记录现场位置。
- 当前已声明 `scope.writePhotosAlbum` 用于保存水印图片到相册。
- 本项目不接后台、不接数据库、不使用云开发。

## 后续开发说明

- 按 `ROADMAP.md` 分阶段开发。
- 每个阶段完成后更新 `CHANGELOG.md`。
- 每个阶段独立提交并推送到远程仓库。
- 每次提交前检查 `git status`，避免提交 `node_modules`、临时文件、日志文件和真实密钥。
- 新增工具时使用独立页面，入口统一放在便捷工具页。
- 通用 UI 放入 `components`，通用能力放入 `utils`。
