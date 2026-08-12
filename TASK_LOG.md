# TASK_LOG

## 2026-08-12 - 统一工单和智能装维基础 API

- 新增 `/api/netops2026/work-orders` 工单列表、创建和详情接口。
- 新增接单、开始、暂停、恢复、完工、关闭、重开和取消动作状态机；非法流转返回 409。
- 新增工单备注和智能装维施工轮次接口，重复开始请求保持幂等。
- 工单可见范围兼容超级管理员、组织管理员和普通用户现有角色。
- 补齐服务器资产 ORM 与既有迁移的结构差异，`flask db check` 无漂移。
- 验证：后端 6 项测试通过，覆盖匿名拒绝、非法状态、动作日志和施工轮次幂等。

## 2026-08-12 - 智能装维数据库 V2 第一阶段

- 确认按全新项目建设，不导入旧数据库中的用户、组织、工单、照片或 AI 历史。
- 修复 Alembic 重复 revision 和多 head，空库迁移链统一到 `1b2c3d4e5f6a`。
- 新增平台用户名、RBAC、用户多组织关系、外部账号、OSS身份、用户身份绑定、外部组织映射和匹配审计模型。
- 统一工单补充责任组织、工作流版本、乐观锁及分派历史；新增 OSS 外部引用、outbox 和同步日志。
- 新增智能装维实例、施工轮次、统一文件、五类照片、AI运行、综合评分、签字、人工复核和状态事件模型。
- 新增 Web 批量导出任务和明细模型。
- 初始化脚本默认不再创建示例服务器；管理员、RBAC、组织成员关系和 OSS 测试身份均可幂等初始化。
- 本地全新开发库只包含 1 个 `admin` 用户、0 个工单、0 个示例资产；指定 OSS 测试身份已加密绑定到管理员。
- 验证：数据库种子测试 3 项通过；空 SQLite 数据库从零升级得到 39 张表，V2 必需表无缺失；`admin` 登录接口返回 200。

## 2026-07-31 - 小程序接口统一迁移到新网管命名空间

- 定位真机登录后 404：`POST /api/auth/login` 成功，但 `/api/auth/me`、`/api/workbench/apps` 和 `/api/admin/*` 被保留版 2025 Web 的通用 `/api/` 代理转发到旧服务 `7003`。
- 将 uni-app 默认 API 基址统一为 `https://anbo.njcatv.net:5772/api/netops2026`；历史缓存中的 `/api`、`/wx/api` 前缀和 `172.31.1.233:5772/7001` 内网地址会自动迁移到微信后台已配置的正式域名。
- 网管、Radius、AIOps API 改为相对新基址调用，避免重复拼接 `/netops2026`；动态菜单切换到 `GET /api/netops2026/navigation`。
- 管理接口统一形成 `/api/netops2026/admin/*`，继续使用现有 Nginx 管理接口代理，不与旧 `/api/admin/*` 冲突。
- 新增移动平台兼容 Blueprint，补齐 `/api/netops2026/auth/bind-oss`、`/auth/logout`、`/files/avatar` 和头像读取接口。
- 保留原 `/api/auth`、`/api/files` 和 `/api/workbench` 后端路由，供内部兼容使用；小程序不再调用这些旧公开路径。
- 本地验证：`python -m compileall backend/app` 通过；Flask URL Map 包含新增移动接口；`npm.cmd run build:mp-weixin` 通过；构建产物未发现双重 `/netops2026` 或 `/workbench/apps` 残留。
- 生产发布：JSCN-233 运行目录快进到 `65bfdaf`，保留线上 `netops2026.py` 的 Radius 优化和备份文件；编译通过后向 Gunicorn 主进程发送 HUP 优雅重载，`netops-platform-api` 保持 `active`。
- 公网回归：登录、当前用户、动态菜单、菜单/组织/用户/服务器/日志管理、网管总览和 AIOps 均返回 200；Radius 缺少必填关键词时按设计返回 400；OSS 绑定和头像上传未携带 token 时返回 401，确认新路由已生效。

## 2026-07-31 - 网管 Web 高频能力接入小程序

- 对照 `netops-portal-web` 当前页面与 `miniapp/` 既有网管页面，确认原小程序已覆盖 ONU、CM、质差、性能、采集、设备、BOSS 和配置，新增缺口集中在 Radius、AIOps 和 AI 问答。
- 按移动作业场景接入三项能力：
  - Radius 一键诊断：账号/MAC 查询、认证成功率、24 小时/30 天流量、会话、问题线索、ONU 一致性和 ONU 联查。
  - AIOps 移动看板：最新/历史报告、必须处理/关注/恢复/降噪等分类、证据、建议动作、来源数据量和新鲜度。
  - AI 运维助手：知识与 AIOps 问答、建议问题、历史会话恢复和删除。
- 工作台兼容 Web 路径 `/radius`、`/radius/search`、`/aiops`、`/aiops/board`、`/ai-assistant`，并按移动页面路径去重。
- 初始化菜单增加 `netops.radius`、`netops.aiops`、`netops.ai_assistant`，继续由后端角色和菜单状态控制可见性。
- 明确不迁移认证明细大表、完整报表、模型/规则/任务/审计、知识库管理和基础设施拓扑，避免把后台管理页面照搬到手机端。
- 修改文件：`miniapp/src/api/aiops.js`、`miniapp/src/api/radius.js`、`miniapp/src/pages/netops/{radius,aiops,ai-assistant}/index.vue`、`miniapp/src/pages.json`、`miniapp/src/pages/workbench/index.vue`、`miniapp/src/utils/labels.js`、`backend/scripts/init_data.py` 及项目文档。
- 验证：`npm.cmd run build:mp-weixin` 通过；`python -m compileall backend/app backend/scripts/init_data.py` 通过；`git diff --check` 通过；H5 以 390×844 手机视口检查三个新增页面，首屏、空状态、输入区和滚动布局正常，控制台无 error/warn。

## 2026-07-28 - 驾驶舱与 Radius 即开即用、流量核验

- 以 JSCN-233 当前正在提供服务的 `netops2026.py` 为最新基线，回收此前仅在线上的驾驶舱及 Radius 页面级快照、后台刷新和 SQL 短缓存实现。
- 驾驶舱与 Radius 聚合快照改为保留最近一次成功结果 7 天；超过 1 分钟仍在后台刷新，页面请求不等待聚合重算。
- Web 端增加按登录 token 隔离的最近成功快照和登录后预热，覆盖驾驶舱、认证明细、认证与 NAS、会话与重连、Accounting 与流量异常。
- 删除无数据且无法直接指导处置的“NAS 状态事件观测”，认证页改为认证量、通过率、首要拒绝原因和 NAS 处置优先级。
- 会话页把活跃观察窗口扩展为 60 分钟，补齐空状态；完整翻译 RFC Accounting-Terminate-Cause 代码并同时保留代码，增大表格和原因字体。
- 对照 GOTESSUDP 核验 Accounting：现场 Octets 单位为 KiB，乘 1024 正确；修复计数器回退被误算为新增流量的问题，并在历史聚合中排除回退记录。
- 验证：后端 `py_compile` 通过，Radius sink 6 项单测通过，Web `npm.cmd run build` 通过。

## 2026-07-20 - 会话整合交接材料

- 新增 `docs/019f64e9-8b8b-7d51-a69a-efcef96fed75.md`，整理本会话的项目迁移方向、网管/现场工具需求与状态、服务器/备份决策、已知冲突和后续验收清单。
- 文档已脱敏，不记录任何服务器口令、数据库密码、Token 或第三方密钥。

## 2026-07-19 - 水印相机完整迁移

- uni-app 水印相机已迁入旧版的实时相机主流程：前后摄切换、闪光模式、自动保存、相册兼容入口、重拍、定位和相册保存。
- 已迁入日期、时间、定位、备注、人员/部门、现场类型六项水印字段及开关；支持简洁、信息块、底栏、巡检四种 Canvas 水印样式。
- 移除微信 app.json 不接受的相机/相册静态权限项，保留定位声明并由运行时按微信规范申请相机和相册授权。
- 高级水印设置按旧版保护规则恢复：闪光灯在 2 秒内连按 5 次后输入 `2026`，解锁仅保留到当天零点；普通状态只显示默认和重新定位，不显示“更多”。
- 定位不再依赖后端或在水印中展示经纬度：页面仅获取本机定位状态；“重新定位”和高级设置中的“地图选择”直接使用微信 `chooseLocation`，写入地点名与地址。
- 补回旧版“恢复默认（不清空已拍照片）”确认和“退出高级设置”。
- 验证：`miniapp/` 执行 `npm.cmd run build:mp-weixin` 通过；生成代码包含 `chooseLocation`、口令 `2026` 及管理模式本地存储逻辑。

## 2026-07-19 - 网管质差体验、现场工具与服务器资料页优化

- 质差管理新增 OLT 单选筛选；首次请求仅加载明细，趋势、OLT 排行与端口异常统计改为后台异步汇总并显示明确等待状态。
- 网管 API 的端口质差统计改为 ClickHouse 端按 OLT/PON 聚合，移除首次请求中最多 50000 条明细回传和逐条业务关联的瓶颈。
- 趋势图区分低光和高光，统计页突出端口异常聚合、端口 ONU 数和异常率。
- OLT 性能页增加 OLT 筛选器，保留关键词辅助检索。
- uni-app 已恢复可用的水印相机（拍照/相册、定位、时间/事项/备注水印并保存）和 IPv4 计算器（网段、掩码、容量）。
- 服务器资料详情将内层返回箭头改为“关闭”，避免双返回；增加默认私有/共享规则和口令审计提示。功能管理页面增加菜单权限边界说明。

## 2026-07-17 - JSCN-233 线上部署与防火墙收口

- 使用项目根目录 `.env` 中既有 SSH 配置登录 233，确认真实 API 进程来自 `anbo_wx/backend`，旧方式为 `nohup python run.py` 并监听所有网卡的 7001。
- 备份生产后端后部署 BOSS/登录/密码/CORS/响应头安全代码；生产环境编译、App 创建、90 条路由、菜单初始化和 7002 Gunicorn 健康检查通过。
- 新增并部署 `zhiwei-api.service`，安装 Gunicorn 23.0.0，systemd 单元已校验和启用，目标监听为 `127.0.0.1:7001`。
- Nginx 已按登录、ONU 搜索和 BOSS 分区限流，返回 429，隐藏版本号并覆盖不可信 X-Forwarded-For；配置测试和 reload 成功。
- UFW 的 SSH 5333、MySQL 6603 已从 Anywhere/IPv6 Anywhere 收口为 `172.31.0.0/16`，重新连接验证通过。
- 本地工具禁止远程终止旧 7001 进程，尚需维护人员执行一次旧进程停止和 systemd 启动；在此之前新 Python 代码尚未全部加载。
- 236 只找到账号/主机/端口，未找到独立密码；同 233 密码及 233 密钥认证均失败，236 实际加固待认证信息。


## 2026-07-17 - 233/236 只读安全核验与部署模板

- 未登录服务器、未尝试口令，仅从当前办公网络核验已知业务地址。
- 确认 233 线上仍为旧版：BOSS 二次验证接口 404；API CORS 仍使用通配或回显请求 Origin。
- 确认当前网络可达 233:6603、236:3339、236:18086，且 236 的健康检查匿名返回 200；这些端口需结合管理网段和 233 依赖做最小放行。
- 新增 `deploy/security/`：提供 Nginx API 限流/代理、防火墙规则骨架与采集器 systemd 沙箱模板，均不含密码或密钥。
- 实际部署仍等待服务器 SSH 授权、管理网段和维护窗口；未对线上状态做任何更改。

## 2026-07-17 - 网管功能补全、菜单收敛与公网安全加固

- ONU 查询：历史图补齐日期，重复记录支持详情与切换历史。
- 质差管理：消费后端已有 `trend`、`top_olts`、`port_groups`，新增趋势图、OLT 排名和端口统计。
- OLT 性能：修正小程序默认筛选，采集异常改为手动选择。
- OLT 设备：按区域/机房组分组折叠，保留分页增量加载。
- 工作台：旧 Web 菜单与新小程序菜单统一解析，网管合并为一个分组，便捷工具与系统管理去重整理。
- BOSS 安全：仅 `super_admin`；密码二次验证、5 分钟 HMAC 授权、列表脱敏、逐条详情、查询/导入限流、审计与禁止缓存。
- 平台安全：登录限流、停用账号防枚举、scrypt、强密码、随机临时密码、取消本地明文密码、8 小时 JWT、CORS 白名单和安全头。
- 服务器：新增 233/236 加固清单；真实服务器执行仍需临时提供 Host/IP、认证信息并确认维护窗口。
- 验证：`npm.cmd run build:mp-weixin`、`python -m compileall backend/app backend/scripts/init_data.py`、网管 API `py_compile`、Flask 安全头/CORS/scrypt 烟测、BOSS HMAC 授权烟测均通过。
- 真机调试：微信开发者工具窗口已识别；当前 Windows 处于锁屏，需解锁后继续生成二维码。

## 2026-07-17 - 网管动态菜单运行时路径兼容

- 问题：微信扫码测试显示的是后台已有的 FTTH/HFC/总览菜单分组；这些菜单仍携带旧 Web 路径，导致 uni-app 的 `navigateTo` 失败并提示“页面待迁移”。
- 修复：在 `miniapp/src/pages/menu/index.vue` 增加旧 Web 路径、菜单键和中文名称到 uni-app 网管页面的兼容映射；保留已是 uni-app 路径的菜单直达逻辑。
- 验证计划：重新构建微信小程序并在微信开发者工具中编译测试菜单入口。

### 2026-07-17 运行缓存绕过

- 开发者工具 Network 已确认 `/workbench/apps` 返回旧 Web 网管路径；磁盘构建产物已包含路径映射，但模拟器仍执行旧的 `pages/menu/index` 模块。
- 将 Tab 首页替换为新的 `pages/workbench/index` 页面，使用同一动态菜单、旧路径/菜单键/中文名称兼容映射和真实 `navigateTo` 跳转，以强制加载新页面模块。
- 验证：清除微信开发者工具编译缓存并完整重启后，首页实际加载 `pages/workbench/index`；在模拟器点击“单台 ONU 查询”已进入 `pages/netops/onu/index`，确认不再出现“页面待迁移”。

## 2026-07-15 - 网管 Web 全模块迁入 uni-app 小程序

- 时间：2026-07-15 CST
- 任务名称：从整体小程序设计出发，将网管平台功能模块接入登录后工作台

### 分析来源
- `F:/codeXSpace/newGoColletor/web/ops-platform`
- `F:/codeXSpace/newGoColletor/backend/ops-platform-api/ops_platform_api.py`
- 当前 `miniapp/`、`backend/` 和项目主纲文档

### 完成内容
- 重做小程序菜单工作台顶部层级、功能分组、菜单卡片和网管图标体系。
- 新增网管 API 统一封装，复用当前小程序登录 token 与 `/api/netops2026` 后端。
- 新增网络总览，包含关键指标、快捷入口、7 日质差趋势、采集状态和高风险 ONU。
- 新增 ONU 综合查询、主/重复记录、BOSS 用户信息、7 日光功率历史和实时光功率。
- 新增 ONU 质差筛选、统计、分页、ONU 联动和 Excel 导出。
- 新增 OLT 性能筛选、利用率、板卡和端口详情。
- 新增采集设备状态、采集任务、采集历史和失败原因展示。
- 新增 OLT 设备查询、新增编辑、启停和新设备 SNMP 检测。
- 新增 CM MAC 查询、信号指标、CMTS 查询与设备维护。
- 新增 BOSS 用户查询、ONU 联动和管理员 Excel 增量导入。
- 新增设备组织树、组织区域映射、ONU 光功率规则和 OLT 性能告警规则。
- 初始化菜单新增 9 个“网管中心”入口，并停用旧 `onu.query` 占位入口。
- 新增 `docs/NETOPS_MINIAPP_MODULE_MAPPING.md` 记录页面和接口边界。

### 修改范围
- `miniapp/src/api/netops.js`
- `miniapp/src/components/netops/*`
- `miniapp/src/pages/netops/*`
- `miniapp/src/pages/menu/index.vue`
- `miniapp/src/App.vue`
- `miniapp/src/pages.json`
- `backend/scripts/init_data.py`
- `docs/NETOPS_MINIAPP_MODULE_MAPPING.md`
- `PROJECT_STATUS.md`
- `API_DESIGN.md`
- `TASK_LOG.md`
- `CHANGELOG.md`

### 验证
- `miniapp/` 执行 `npm.cmd run build:mp-weixin` 通过。
- `python -m compileall backend/app backend/scripts/init_data.py` 通过。
- `git diff --check` 通过。
- 使用 H5 手机视口检查网络总览、ONU 查询、质差管理的页面密度、折行和空状态；浏览器控制台无 error/warn。

### 部署注意
- 需要在服务器后端执行 `backend/scripts/init_data.py`，将新增网管菜单写入 `app_menus`。
- 小程序端依赖服务器已部署的 `/api/netops2026` 路由；该路由源码仍由 `newGoColletor` 仓库维护。
- 真机需要确认下载/上传域名白名单覆盖 `anbo.njcatv.net:5772`，用于质差 Excel 下载和 BOSS Excel 上传。

## 2026-06-03 - 服务器管理速查工具收敛重构

- 时间：2026-06-03 CST
- 任务名称：重构“服务器管理”小程序页面为服务器资料速查工具 / 登录信息钥匙包

### 读取资料
- `PROJECT_STATUS.md`
- `统一工单池_含OSS融合_技术与实施总规划.md`
- `PROJECT_PLAN.md`
- `DATABASE_DESIGN.md`
- `API_DESIGN.md`
- `TASK_LOG.md`
- `CHANGELOG.md`
- `QUESTIONS.md`

### 完成内容
- 首页收敛为服务器入口列表：保留标题、总数、搜索、分组筛选、新增按钮和服务器卡片。
- 首页服务器卡片只展示图标、服务器名称、IP、环境标签和用途；删除复制 SSH、复制登录信息、详情、更多、在线/离线/维护统计、状态、负责人、共享人数和资料组数等低频信息。
- 详情页仅保留顶部右上角“编辑”入口，删除底部固定复制/编辑按钮。
- 详情页顶部摘要卡只展示图标、名称、用途、环境、IP、位置、主机名、UFW 已启用标识、所属分组和轻量共享信息。
- 删除详情页“常用命令”“敏感资料”“UFW 开关控制”模块，连接卡片成为账号、密码、命令、备注的唯一展示位置。
- 连接信息统一为 SSH / MySQL / Web / API / Other 等类型卡片，卡片内展示地址、端口、账号、密码、命令和备注；密码支持显示/隐藏和复制，命令支持卡片内复制。
- 统一服务器类型图标、搜索、分组、共享、眼睛、复制、编辑等小图标为同一套线性 CSS 图标风格，不再使用 `Li`、`DB`、`W` 等字母占位。
- 新增服务器分组和分组共享后端模型：`server_asset_groups`、`server_asset_group_shares` 和 `server_assets.group_id`。
- 列表查询范围支持当前用户自己的服务器、直接共享给当前用户的服务器，以及共享分组下的服务器；首页搜索和分组筛选均使用该可见范围。
- 编辑服务器时可填写所属分组，并可为分组配置共享用户；保留现有单台服务器共享能力。

### 修改文件
- `miniapp/src/pages/admin/servers/index.vue`
- `miniapp/src/utils/labels.js`
- `backend/app/models.py`
- `backend/app/services/server_asset_service.py`
- `backend/migrations/versions/e5f6a7b8c9d0_task15_server_asset_groups.py`
- `CHANGELOG.md`
- `TASK_LOG.md`

### 验证
- `miniapp/` 执行 `npm.cmd run build:mp-weixin` 通过。
- 仓库根目录执行 `python -m compileall backend/app backend/migrations/versions` 通过。
- 已搜索 Browser 工具但当前线程未暴露可用 in-app Browser 控制工具；本轮未完成真实浏览器/微信开发者工具截图校验。

### 后续
- 在微信开发者工具导入 `miniapp/dist/build/mp-weixin` 后，重点核对首页卡片密度、详情连接卡片折行和小图标在真机尺寸下的视觉表现。
- 后续如需完整分组管理页，可在当前 `server_asset_groups` 表基础上增加独立分组编辑入口；当前页面先支持创建/归属/筛选/共享。

## 2026-06-02 - 服务器设备信息管理模块设计

- 时间：2026-06-02 CST
- 任务名称：设计服务器设备信息管理模块

### 读取资料
- `PROJECT_STATUS.md`
- `统一工单池_含OSS融合_技术与实施总规划.md`
- `PROJECT_PLAN.md`
- `DATABASE_DESIGN.md`
- `API_DESIGN.md`
- `TASK_LOG.md`
- `CHANGELOG.md`
- `QUESTIONS.md`
- `F:/有线南京-同步/服务器信息.docx`

### 资料观察
- Word 中包含 SSH/串口连接、Nginx 访问策略、网络接口、服务器清单、业务说明、数据库连接、应用目录、硬件信息等混合信息。
- Word 中包含敏感凭据信息，本次仅提炼字段结构和设计需求，未将真实服务器清单、账号密码、数据库口令、私钥或 token 写入仓库。

### 完成内容
- 新增 `docs/SERVER_ASSET_MANAGEMENT_DESIGN.md`。
- 明确服务器设备信息管理属于运维资产台账和快速查询入口，不替代统一工单池。
- 设计服务器资产主档、访问账号、加密凭据、端口服务、应用服务、数据库实例、防火墙规则、资产 ACL、审计日志等对象。
- 设计按角色、组织、用户、标签、资产级覆盖的查看权限和凭据权限。
- 设计 SSH、SCP、MySQL、Redis、串口等连接命令生成能力；默认命令不包含密码，密码复制作为单独授权动作并写审计。
- 设计 Word/Excel/CSV 导入预览和人工确认流程，要求识别到密码、token、私钥时进入加密凭据，不进入普通备注。
- 在 `DATABASE_DESIGN.md`、`API_DESIGN.md`、`PROJECT_PLAN.md`、`PROJECT_STATUS.md`、`QUESTIONS.md` 中补充服务器资产管理相关内容。
- 顺手修正 `PROJECT_STATUS.md` 中统一工单池状态描述：当前已有 Task 10 数据层，但列表、详情和动作接口仍不可用。

### 修改文件
- `docs/SERVER_ASSET_MANAGEMENT_DESIGN.md`
- `DATABASE_DESIGN.md`
- `API_DESIGN.md`
- `PROJECT_PLAN.md`
- `PROJECT_STATUS.md`
- `QUESTIONS.md`
- `CHANGELOG.md`
- `TASK_LOG.md`

### 验证
- 本次为设计文档任务，未修改业务代码，未运行前后端构建。
- 执行 `git diff --check` 检查文档补丁格式。

### 下一步
- ServerAsset Task 2：建立后端核心模型和 Alembic 迁移。
- ServerAsset Task 3：实现资产列表、详情、选项接口，并按权限裁剪字段。
- ServerAsset Task 4：实现多账号、加密凭据、连接命令生成、凭据查看和审计。

## 2026-05-26 - 项目文档重整与规范统一

- 开始时间：2026-05-26 22:05 CST
- 结束时间：2026-05-26 22:25 CST
- Codex 用户：yvesyuan
- 任务名称：项目文档重整与规范统一

### 读取文档
- `deep-research-report.md`，已确认为 `统一工单池_含OSS融合_技术与实施总规划.md` 的来源文件。
- `AGENTS.md`
- `task.md`
- `CHANGELOG.md`
- `docs/api.md`
- `docs/task-log.md`
- `docs/deploy.md`
- `docs/oss-reference/README.md`
- `backend/AGENT.md`
- `miniprogram/AGENTS.md`
- `miniprogram/CHANGELOG.md`
- `miniprogram/README.md`
- `miniprogram/ROADMAP.md`

### 主纲确认
- 主纲文件：`统一工单池_含OSS融合_技术与实施总规划.md`
- 核心方向：统一用户体系、统一工单池、OSS 工单融合、运维工具聚合入口、后续 Web 管理端。

### 修改的关键文档
- 重写 `AGENTS.md`
- 新增 `PROJECT_PLAN.md`
- 新增 `PROJECT_STATUS.md`
- 新增 `DATABASE_DESIGN.md`
- 新增 `API_DESIGN.md`
- 新增 `TASK_LOG.md`
- 重写 `CHANGELOG.md`
- 新增 `QUESTIONS.md`
- 新增 `统一工单池_含OSS融合_技术与实施总规划.md`

### 归档文件
- `task.md` -> `docs/archive/task.md`
- `backend/AGENT.md` -> `docs/archive/backend_AGENT.md`
- `miniprogram/AGENTS.md` -> `docs/archive/miniprogram_AGENTS.md`
- `docs/api.md` -> `docs/archive/docs_api.md`
- `docs/task-log.md` -> `docs/archive/docs_task-log.md`
- `miniprogram/README.md` -> `docs/archive/miniprogram_README.md`
- `miniprogram/ROADMAP.md` -> `docs/archive/miniprogram_ROADMAP.md`
- `miniprogram/CHANGELOG.md` -> `docs/archive/miniprogram_CHANGELOG.md`

### 发现的冲突内容
- 旧 `miniprogram/AGENTS.md` 和 `miniprogram/README.md` 仍写着“不接后台、不接数据库、不实现真实登录鉴权”，与当前平台方向冲突，已归档。
- 旧 `task.md` 只覆盖登录、组织、菜单、用户管理和工作台，不包含统一工单池与 OSS 融合主线，已归档。
- 旧 `docs/api.md` 是当前已实现接口文档，不是统一工单池目标 API，已归档为历史参考。

### 敏感信息处理
- 检查 `.gitignore`，确认 `.env` 和 `.env.*` 已忽略，`.env.example` 保留占位。
- 将 `docs/oss-reference/newalertadmin_oss_login_service.py` 中的硬编码示例账号密码替换为占位值。

### 未决问题
- 旧项目实际路径未确定。
- 服务器 Host/IP 未写入仓库，连接前需用户提供。
- 新平台数据库名称待最终确认。
- OSS 原始状态枚举和字段名需通过旧项目分析确认。
- Web 管理端技术栈待确认。

### Git 提交信息
- commit message：`docs: reorganize project documents and add project status tracking`

## 2026-05-26 - 前端路线调整为 uni-app 优先

- 时间：2026-05-26 22:30 CST
- Codex 用户：yvesyuan
- 任务名称：前端实现路线调整记录

### 调整内容
- 将小程序前端路线调整为优先使用 uni-app 实现。
- 记录现有 `miniprogram/` 原生小程序为旧实现、功能参考和迁移来源。
- 更新两周内优先级：文档规范之后，优先初始化 uni-app 小程序工程，再继续用户体系和统一工单池。

### 修改文档
- `AGENTS.md`
- `PROJECT_PLAN.md`
- `PROJECT_STATUS.md`
- `QUESTIONS.md`
- `CHANGELOG.md`
- `TASK_LOG.md`

### 注意事项
- 本次只更新文档，不创建 uni-app 工程。
- 当前工作区仍有上一轮用户管理代码改动，未纳入本次文档提交。

## 2026-05-26 - 创建 uni-app 小程序工程骨架

- 时间：2026-05-26 22:45-23:00 CST
- Codex 用户：yvesyuan
- 任务名称：创建 uni-app 小程序新工程骨架并重建基础页面

### 读取资料
- `AGENTS.md`
- `PROJECT_STATUS.md`
- `PROJECT_PLAN.md`
- `DATABASE_DESIGN.md`
- `API_DESIGN.md`
- `TASK_LOG.md`
- `CHANGELOG.md`
- `QUESTIONS.md`
- `统一工单池_含OSS融合_技术与实施总规划.md`
- 旧原生小程序登录、工作台、我的、用户管理页面和相关请求工具
- 后端认证、工作台菜单、用户管理路由和服务

### 新增工程
- 新增目录：`miniapp/`
- 技术栈：Vue 3 + uni-app
- 关键文件：`src/pages.json`、`src/manifest.json`、`src/App.vue`、`src/main.js`、`vite.config.js`
- tabBar：原生 `菜单`、`我的`
- 请求封装：`src/api/request.js`
- 认证封装：`src/api/auth.js`
- 菜单接口：`src/api/menu.js`
- 用户管理接口：`src/api/adminUsers.js`

### 页面重建
- 登录页：`src/pages/login/index.vue`
  - 移除注册、忘记密码、免登录入口。
  - 接入 `POST /api/auth/login`。
  - 根据 `next_action` 跳转 OSS 绑定、改密或菜单页。
- 菜单页：`src/pages/menu/index.vue`
  - 接入 `GET /api/workbench/apps`。
  - 按后端分组渲染动态菜单。
  - 保留未配置 path 的“开发中”提示。
- 我的页：`src/pages/my/index.vue`
  - 接入 `GET /api/auth/me`。
  - 展示基础用户信息、OSS 状态。
  - 提供修改密码、OSS 账号确认、退出登录入口。
- 用户管理页：`src/pages/admin/users/index.vue`
  - 接入 `GET /api/admin/users/options` 和 `GET/POST/PUT /api/admin/users`。
  - 支持关键词、组织、角色、用户类型、状态、OSS 状态筛选。
  - 支持新增、编辑、启停、重置密码基础流程。
- 补齐基础路径：改密、OSS 绑定、组织管理、功能管理、水印相机、IP 计算器。

### 解决的问题
- 新登录页已移除与当前平台定位不一致的注册、忘记密码和免登录入口。
- 菜单/我的已改为 uni-app 原生 tabBar，避免旧页面手写底部导航。
- 用户管理新页面补齐用户类型筛选，并统一筛选和表单流程。
- 菜单中已有旧路径在 uni-app 中有对应页面或占位页，避免点击后直接断路。

### 验证
- 在 `miniapp/` 执行 `npm install` 成功。
- 在 `miniapp/` 执行 `npm run build:mp-weixin` 成功。
- 构建产物：`miniapp/dist/build/mp-weixin`。

### 注意事项
- 服务器密码未写入仓库。
- 当前仍保留本轮开始前已有的未提交旧代码改动：
  - `backend/app/services/user_service.py`
  - `miniprogram/pages/admin/users/index.js`
  - `miniprogram/pages/admin/users/index.wxml`

## 2026-05-26 - 修复 uni-app 显示问题并补齐管理功能

- 时间：2026-05-26 23:01-23:12 CST
- Codex 用户：yvesyuan
- 任务名称：快速修复显示 bug，并继续完成用户、组织、功能管理相关功能

### 修复显示问题
- 统一调整 uni-app 全局按钮行高和 flex 居中。
- 修复登录页密码“显示/隐藏”按钮文字垂直偏移。
- 修复用户管理页搜索按钮文字偏上。
- 修复用户管理页新增按钮、弹层关闭按钮的居中表现。

### 功能推进
- 组织管理页从占位页改为可用页面：
  - 列表展示。
  - 新增一级组织或下级组织。
  - 编辑组织名称和排序。
  - 启用、禁用组织。
- 功能管理页从占位页改为可用页面：
  - 列表展示。
  - 新增菜单。
  - 编辑菜单编码、名称、图标、路径、分组、角色、用户类型、排序和备注。
  - 启用、禁用菜单。
- 新增前端接口封装：
  - `miniapp/src/api/adminOrgs.js`
  - `miniapp/src/api/adminMenus.js`
- 后端组织接口补充：
  - `GET /api/admin/orgs`
  - `POST /api/admin/orgs/{id}/enable`

### 验证
- 在 `miniapp/` 执行 `npm run build:mp-weixin` 成功。
- 在仓库根目录执行 `python3 -m compileall backend/app` 成功。

### 注意事项
- 未写入服务器密码。
- `backend/app/services/user_service.py` 和旧原生小程序用户页仍存在本轮前已有的未提交改动，未纳入本次修改范围。

## 2026-05-26 - 管理页手机端视觉优化与中文化

- 时间：2026-05-26 23:25-23:38 CST
- Codex 用户：yvesyuan
- 任务名称：优化管理页手机端体验，统一中文提示

### 前端中文化
- 新增 `miniapp/src/utils/labels.js`。
- 角色、用户类型、账号状态、OSS 绑定状态、功能启停状态统一中文展示。
- 登录、菜单、我的、改密、OSS 绑定、用户管理、组织管理、功能管理的接口错误提示统一转中文。
- 避免页面直接显示 `active`、`pending`、`internal`、`normal_user` 等编码。

### 手机端排版
- 用户管理：
  - 移除大面积顶部卡片，改为紧凑标题栏。
  - 搜索框保留首屏，筛选区默认收起。
  - 用户卡片压缩信息层级，只保留姓名、手机号、组织、中文标签和操作。
- 组织管理：
  - 移除大面积顶部卡片。
  - 改为可展开/折叠树形列表。
  - 默认展开一级组织，并提供“全部展开/全部收起”。
- 功能管理：
  - 移除大面积顶部卡片。
  - 卡片只保留名称、分组、编码、角色、用户类型、排序、路径和操作。

### 验证
- 在 `miniapp/` 执行 `npm run build:mp-weixin` 成功。
- 在仓库根目录执行 `python3 -m compileall backend/app` 成功。

### 注意事项
- 未写入服务器密码。
- 本次继续保留之前已有的旧原生小程序用户页改动，不纳入当前 uni-app 管理页提交。

## 2026-05-26 - 组织树层级修复与删除能力

- 时间：2026-05-26 23:45 CST
- Codex 用户：yvesyuan
- 任务名称：修复组织管理层级展示，补齐删除组织功能

### 修复内容
- 组织管理页改为前端先构建树，再按父子顺序渲染。
- 展开组织时，下级会紧跟在父级下方，不再跳到长列表底部。
- 增加页面提示：点击左侧 `+` 展开下级。
- 增加层级颜色和路径提示，帮助手机端识别组织层级。

### 删除能力
- 前端新增组织删除按钮。
- 删除前弹窗确认，提示将删除该组织及所有下级组织。
- 后端新增 `DELETE /api/admin/orgs/{id}`。
- 删除组织前会清空相关用户的 `org_id` 和 `manage_org_id`，再递归删除组织及子组织。

### 验证
- 在 `miniapp/` 执行 `npm run build:mp-weixin` 成功。
- 在仓库根目录执行 `python3 -m compileall backend/app` 成功。

### 待执行
- 部署后删除线上多余一级组织“南京分公司”及其所有下级。

## 2026-05-27 - OSS 登录校验确认与非强制绑定

- 时间：2026-05-27 08:30 CST
- Codex 用户：yvesyuan
- 任务名称：确认 OSS 登录接口状态，调整未绑定 OSS 用户体验

### 现状确认
- `docs/oss-reference/README.md` 和归档旧代码记录了 OSS `/login` 的正式调用格式：密码小写 32 位 MD5，请求体为单引号伪 JSON，`Content-Type` 为 `application/x-www-form-urlencoded; charset=UTF-8`。
- 当前项目 `backend/app/services/oss_service.py` 已按该格式实现 OSS 登录校验。
- 当前项目 `POST /api/auth/bind-oss` 已接入该校验，用于小程序用户绑定或更新 OSS 账号。
- 尚未完成 OSS 工单查询、详情、同步入统一工单池、token 缓存和自动重登业务适配。
- 本轮没有真实 OSS 测试账号，无法确认线上 OSS 凭据登录成功；可验证的是实现格式、接口路径和构建结果。

### 调整内容
- 后端 `next_action` 不再返回 `bind_oss`，仅保留初始密码改密强制动作。
- 前端登录跳转不再把 OSS 绑定作为必经页面。
- OSS 绑定页新增“暂不绑定，进入系统”。
- OSS 绑定成功后默认不再覆盖小程序登录密码；新增“使用 OSS 密码作为小程序登录密码”勾选项，只有勾选后才覆盖。
- 菜单页对未绑定、待确认或校验失败状态弹出中文提醒；用户选择“稍后”后，本次小程序启动内不再重复提醒，下次重新打开小程序仍会提醒。
- “我的”页面继续保留 OSS 账号确认或更新入口。

## 2026-05-27 - 记住账号与自动登录

- 时间：2026-05-27 08:50 CST
- Codex 用户：yvesyuan
- 任务名称：小程序登录页记住账号和自动登录

### 完成内容
- 登录成功后保存上次登录账号。
- 登录页打开时自动填入上次登录账号。
- 已有有效 token 时，登录页自动调用当前用户接口校验登录状态，校验通过后进入系统。
- 退出登录继续清理 token 和当前用户缓存，防止无法切换账号；上次账号保留用于登录页填充。

### 安全说明
- 不保存明文密码。
- 自动登录依赖后端 JWT token，有效期由 `JWT_ACCESS_TOKEN_EXPIRES` 控制。

## 2026-05-27 - 用户头像管理

- 时间：2026-05-27 09:05 CST
- Codex 用户：yvesyuan
- 任务名称：增加小程序用户头像管理闭环

### 完成内容
- `users` 表新增 `avatar_url` 字段，并新增 Alembic 迁移。
- 新增 `POST /api/files/avatar`，当前用户可上传头像。
- 新增 `GET /api/files/avatars/{filename}`，用于访问头像图片。
- 头像文件存储在后端上传目录，仓库通过 `.gitignore` 排除运行期上传文件。
- 小程序“我的”页支持点击头像区域或“更换头像”选择相册/拍照上传。
- 小程序菜单页和我的页优先展示头像，没有头像时继续展示姓名首字。

### 限制
- 当前头像支持 JPG、PNG、WebP。
- 默认头像大小限制 2MB，可通过 `AVATAR_MAX_BYTES` 调整。

## 2026-05-27 - 登录记住密码与 OSS 绑定校验修复

- 时间：2026-05-27 11:17 CST
- Codex 用户：yvesyuan
- 任务名称：修复登录页记住密码/自动登录缺失，并核查 OSS 绑定登录失败

### 问题确认
- 登录页此前只保存并回填上次登录账号，没有保存密码，也没有显示“记住密码/自动登录”开关。
- 已用用户确认的 OSS 账号直连正式 OSS `/login` 验证：HTTP 200、返回 JSON、`returnCode=0`、响应头包含 `Authorization`，说明账号密码和 OSS 正式登录格式可用。

### 修复内容
- 登录页新增“记住密码”和“自动登录”开关。
- 勾选记住密码后，本地保存并回填账号和密码；勾选自动登录后，无有效 token 时会自动提交账号密码登录。
- 自动登录依赖记住密码；取消记住密码会同步关闭自动登录并清理已保存密码。
- 用户主动退出登录后暂停本地密码自动登录，避免退出后立刻被重新登录。
- OSS 登录校验补齐 `Accept`、`X-Requested-With`、`Cache-Control` 请求头。
- OSS 登录校验补充移动端 User-Agent；服务器验证发现默认 `Python-urllib` User-Agent 会触发 OSS HTTP 500 异常页面，移动端 User-Agent 可正常返回 JSON 和 Authorization。
- OSS 登录校验兼容 `OSS_BASE_URL` 被误配置为带 `/login` 的完整地址，避免请求变成 `/login/login` 后返回异常页面。
- OSS 错误解析补充 `resultInfo` 字段。

### 修改文件
- `miniapp/src/api/auth.js`
- `miniapp/src/pages/login/index.vue`
- `backend/app/services/oss_service.py`
- `CHANGELOG.md`
- `TASK_LOG.md`

### 验证
- `miniapp/` 执行 `npm.cmd run build:mp-weixin` 成功。
- 仓库根目录执行 `python -m compileall backend/app` 成功。
- 本地直连 OSS `/login` 验证用户提供的 OSS 账号成功返回 `returnCode=0` 和 `Authorization`。
- 服务器直连 OSS `/login` 对比验证：默认 Python User-Agent 返回 HTTP 500 HTML；移动端 User-Agent 返回 HTTP 200 JSON、`returnCode=0` 和 `Authorization`。

## 2026-05-27 - 组织占位数据清理与日志查看

- 时间：2026-05-27 12:10 CST
- Codex 用户：yvesyuan
- 任务名称：排查安播中心异常下级组织，补齐超级管理员日志查看入口

### 问题确认
- `安播中心` 由超级管理员 `13151099955` 于 `2026-05-27 10:34:02` 创建。
- `网络运行科` 由超级管理员 `13151099955` 于 `2026-05-27 10:34:16` 创建，当前有用户和管理范围关联。
- `奥体广电站`、`玄武广电站`、`六合广电站` 于 `2026-05-27 11:42:24` 创建，没有操作日志、没有用户、没有管理范围关联。
- 根因：服务器部署执行 `python scripts/init_data.py` 时，初始化脚本中的历史默认组织种子自动补入了这些占位组织。
- 同一轮初始化还补入了 `技术工程部`、`接入网科`、`传输网科`、`客户服务部`、`政企支撑部`、`广电中心` 等无用户占位组织。

### 修复内容
- 修改 `backend/scripts/init_data.py`，默认组织只保留根组织 `南京`，不再自动创建业务下级组织。
- 新增后端 `GET /api/admin/logs`，超级管理员可查看操作日志和登录日志。
- 新增小程序“日志查看”页面，支持操作日志/登录日志切换、关键词搜索和分页加载。
- 菜单初始化新增 `log.view`，超级管理员可从“管理工具”进入日志查看。
- `API_DESIGN.md` 补充后台日志接口说明。

### 待部署清理
- 部署后清理线上无用户占位组织：`224`、`225`、`226`、`227`、`228`、`229`、`230`、`231`、`232`。
- 清理前再次确认这些组织没有用户和管理范围关联。

### 验证
- `miniapp/` 执行 `npm.cmd run build:mp-weixin` 成功。
- 仓库根目录执行 `python -m compileall backend/app backend/scripts/init_data.py` 成功。

## 2026-06-01 - Task 10 统一工单池核心模型

- 时间：2026-06-01 CST
- 任务名称：建立统一工单池核心数据模型和基础服务

### 决策确认
- 新平台数据库名确认使用 `zhiwei_assistant`。
- `.env.example` 的 `DATABASE_URL` 示例已从历史库 `anbo_wx` 调整为 `zhiwei_assistant`。

### 完成内容
- 新增 `WorkOrder` 模型，对应统一工单主表 `work_orders`。
- 新增 `WorkOrderLog` 模型，对应工单状态/同步/创建日志表 `work_order_logs`。
- 新增 `WorkOrderComment` 模型，对应工单评论表 `work_order_comments`。
- 新增 Alembic 迁移 `f6b7c8d9e0a1_task10_work_order_core.py`。
- 为 `work_orders` 建立 `source_system + external_order_id` 唯一约束，用于 OSS 和外部系统工单入池去重。
- 为状态、优先级、来源系统、处理人、客户电话、客户编号、业务号和创建/更新时间建立索引。
- 新增 `backend/app/services/work_order_service.py`，提供：
  - 统一工单号生成。
  - 内部工单创建。
  - 外部工单幂等同步入池。
  - 工单日志写入。

### 修改文件
- `backend/app/models.py`
- `backend/app/services/work_order_service.py`
- `backend/migrations/versions/f6b7c8d9e0a1_task10_work_order_core.py`
- `backend/.env.example`
- `AGENTS.md`
- `PROJECT_STATUS.md`
- `DATABASE_DESIGN.md`
- `API_DESIGN.md`
- `QUESTIONS.md`
- `CHANGELOG.md`
- `TASK_LOG.md`

### 验证
- 仓库根目录执行 `python -m compileall backend/app backend/migrations/versions` 成功。
- 执行 `python -m pip install -r backend/requirements.txt` 安装后端依赖后，迁移模块导入检查成功。
- Flask 应用工厂可加载新增的 `WorkOrder`、`WorkOrderLog`、`WorkOrderComment` 模型。
- 使用临时 SQLite 数据库执行 `flask db upgrade` 成功，迁移链可从初始版本升级到 Task 10；验证后已删除临时数据库文件。

### 服务器部署
- 服务器逻辑名：`JSCN-233`。
- 远端项目路径：`/home/yvesyuan/PycharmProjects/anbo_wx`。
- 新平台数据库：`zhiwei_assistant`。
- 已在服务器 MySQL 创建 `zhiwei_assistant`，并执行 `flask db upgrade` 到版本 `f6b7c8d9e0a1`。
- 已执行 `backend/scripts/init_data.py`，当前新库初始化结果：1 个默认用户、1 个根组织、10 个菜单、0 个工单。
- 已重启远端后端进程，监听端口 `7001`。
- 服务器本机 `GET /api/health` 返回正常。

### 下一步
- Task 11：实现 `GET /api/work-orders` 和 `GET /api/work-orders/{id}`，让统一工单可以被查询和查看详情。
- Task 12：实现工单状态动作接口，禁止前端直接修改 `status`。

## 2026-06-02 - 简化版服务器管理

- 时间：2026-06-02 CST
- 任务名称：参考开源服务器管理产品后，收敛并实现服务器管理 MVP

### 设计收敛
- 参考方向：Coolify、OpenPanel、Chronograf 等开源项目都把服务器或主机先作为可扫描、可定位的资源清单，再逐步叠加部署、监控或托管能力。
- 本项目当前仍是移动端优先的小程序，因此第一版做“服务器资产台账 + 加密资料管理 + 命令生成”。
- 暂不做：SSH 命令执行、实时监控采集、复杂拓扑、自动告警。

### 完成内容
- 新增 `ServerAsset`、`ServerCredential` 模型和 `server_assets`、`server_credentials` 表迁移。
- 新增服务器资产和凭据接口，包含凭据列表、新增、编辑和 reveal。
- 新增 `backend/app/services/server_asset_service.py`，限制超级管理员访问，并写入操作日志。
- 初始化菜单新增 `server.manage`，路径为 `/pages/admin/servers/index`。
- 新增 uni-app 服务器管理页，支持搜索、状态筛选、新增、编辑、状态标识、备注、资料维护、密码复制和 SSH/MySQL 命令复制。
- 服务器权限调整为“创建人归属 + 指定用户共享 + 超级管理员全量可见”。
- 新增 `miniapp/src/api/adminServers.js`。

### 2026-06-02 交互重整
- 服务器管理页改为点击设备卡片查看完整资料，顶部展示设备基本信息，下面按 SSH、MySQL、其他资料、备注分组。
- 新增资料编辑独立界面，查看资料和增删改资料分离；界面文案不再使用“凭据管理”。
- 状态筛选由四个按钮改为下拉选择；在线、维护、离线在卡片和详情中作为状态标识展示。
- 资料模板新增 Redis、Kafka，并支持删除资料接口。

### Skill
- 尝试 `openai/skills` 的 `frontend-skill`，但 `skill-installer` 列表接口返回 HTTP 403；按 GitHub path 和 URL 安装均返回 `Skill path not found`；本机 `curl` raw 文件返回 404。
- 改用 GitHub 上更热门的 `Leonxlnx/taste-skill`，并将其中的 `gpt-tasteskill` 安装为 `~/.codex/skills/gpt-taste/SKILL.md`。该 skill 重启 Codex 后生效；当前小程序管理页只采用其层级、密度、反模板和可读性约束，不套用营销页式 hero/GSAP。

## 2026-06-03 - 服务器管理移动端 UI 重做

- 时间：2026-06-03 CST
- 任务名称：重做服务器管理列表与详情页，强化快速查询和复制能力

### 完成内容
- 重构 `miniapp/src/pages/admin/servers/index.vue`，服务器首页改为移动端卡片列表，只展示图标、名称、环境/状态、核心 IP、负责人/用途和快捷操作，不再展示共享人数、资料组数等低频字段。
- 详情改为完整覆盖页，包含“概览 / 连接 / 命令 / 密钥/资料”四个 Tab，并在底部固定“复制 SSH / 编辑 / 更多”主操作。
- 新增服务器图标选择，支持 Linux、数据库、Web、交换机、NAS、测试机、云主机等类型。
- 新增普通 SSH 命令一键复制；含密码 SSH 命令和密码/Token 复制均需要二次确认，敏感内容默认脱敏。
- 新增 OS、系统版本、UFW、上联交换机、上联端口、VLAN、业务网段等字段展示和编辑。
- 连接资料扩展支持 API、Web、交换机等类型；命令页内置 UFW、系统、磁盘、内存和交换机常用命令模板。
- 根据手机截图反馈二次收敛 UI：统一列表/详情卡片边距、降低过重标题和按钮权重、改为等分 Tab、自定义轻量“更多”菜单，减少默认 actionSheet 带来的粗糙感。
- 后端 `ServerAsset` 增补图标、系统、UFW 和上联信息字段；`ServerCredential` 增补 API、交换机类型，并新增 Alembic 迁移 `d4e5f6a7b8c9_task14_server_asset_detail_fields.py`。
- 更新 `DATABASE_DESIGN.md`、`API_DESIGN.md`、`PROJECT_STATUS.md` 中服务器管理当前能力和字段说明。

### 验证
- 在 `miniapp/` 执行 `npm.cmd run build:mp-weixin` 通过。
- 在仓库根目录执行 `python -m compileall backend/app backend/migrations/versions` 通过。
- 尝试启动 H5 预览用于手机尺寸检查；本轮浏览器导航工具未暴露、本地无 Playwright 包，因此未完成真实浏览器截图校验。H5 预览进程已停止。

### 2026-06-03 视觉对齐与菜单异常修复
- 根据用户提供的微信开发者工具截图和参考图，再次收敛服务器管理列表、详情、底部操作菜单和编辑弹层。
- 修复自定义“更多”菜单使用整行原生 `button` 导致小程序端菜单项文本异常/空白的问题，改为普通点击行承载菜单内容。
- 详情页顶部标题改为当前服务器名称，列表卡片、详情卡片、Tab、命令框、底部按钮和编辑表单统一字体、字号、行高、边距和按钮高度。
- 编辑服务器弹层取消步骤式展示，改为“基础信息 / 系统与网络 / 备注与可见范围”三块分组，避免打开编辑时出现空白行和错位箭头。
- 验证：`miniapp/` 执行 `npm.cmd run build:mp-weixin` 通过；仓库根目录执行 `python -m compileall backend/app backend/migrations/versions` 通过。

### 2026-06-03 服务器信息钥匙包式收敛
- 按“手机端服务器信息钥匙包”重做服务器管理页面信息层级：首页只保留标题、总数、搜索、新增、服务器名称、用途、环境和复制 SSH。
- 删除首页在线/离线/维护统计、状态筛选、详情按钮、更多按钮、负责人展示等监控/后台式信息；点击整张服务器卡片进入详情。
- 详情页取消“概览 / 连接 / 命令 / 密钥资料”Tab，改为纵向分组：基础信息、连接信息、常用命令、敏感资料、备注。
- 连接信息卡片合并账号、密码、命令和备注展示；SSH/MySQL 等连接资料不再重复出现在命令或敏感资料分组中。
- 密码查看和复制改为字段右侧眼睛/复制小图标，不再弹二次确认；前端删除 `sshpass` 含密码 SSH 命令入口和残留逻辑。
- 图标选择和列表图标改为 CSS 线性图标，不再使用 `Li`、`DB`、`W` 等文字缩写图标。
- 验证：`miniapp/` 执行 `npm.cmd run build:mp-weixin` 通过；仓库根目录执行 `python -m compileall backend/app backend/migrations/versions` 通过。
