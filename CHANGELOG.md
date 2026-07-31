# CHANGELOG

## 2026-07-31

### Fixed

- 修复小程序登录成功后，用户信息、动态菜单和管理接口仍落到旧版 `7003` 服务并返回 404 的问题。
- 小程序缓存的旧 `/api` 或 `/wx/api` 基址会自动迁移到 `/api/netops2026`，避免真机保留历史配置后继续请求退役接口。

### Changed

- 小程序认证、菜单、头像、OSS、系统管理、网管、Radius 和 AIOps 请求统一使用 `/api/netops2026` 公开命名空间。
- 动态菜单改用 `/api/netops2026/navigation`；管理接口改用 `/api/netops2026/admin/*`。

### Verification

- JSCN-233 已部署并优雅重载；登录、当前用户、动态菜单、管理查询、网管总览和 AIOps 公网接口回归通过。
- Radius 无关键词请求按设计返回 400；OSS 绑定和头像上传匿名请求返回 401，确认新路由已生效。

### Added

- 新增小程序 Radius 一键诊断页，支持账号/MAC 用户画像、认证/流量/会话诊断、ONU 一致性和 FTTH ONU 联查。
- 新增小程序 AIOps 运维看板，支持最新与历史 AI 报告、分类结论、关键证据和处置建议。
- 新增小程序 AI 运维助手，支持故障问答、建议问题和个人历史会话。
- 新增 Radius 与 AIOps 小程序 API 封装及三项动态菜单初始化配置。

### Changed

- 工作台兼容 Web 的 Radius、AIOps 和 AI 问答路径，并将多个 Web 子入口按对应移动页面去重。
- 网管移动端映射文档补充手机端范围取舍，复杂报表和后台配置继续保留在 Web。
- 小程序网络失败提示补充 `request:fail` 中文映射。

### Verification

- `miniapp/` 执行 `npm.cmd run build:mp-weixin` 通过。
- 执行 `python -m compileall backend/app backend/scripts/init_data.py` 通过。
- `git diff --check` 通过。
- H5 以 390×844 手机视口检查三个新增页面，控制台无 error/warn。

## 2026-07-28

### Added

- 登录后自动预热驾驶舱和 Radius 关键页面，并按登录范围保存最近一次成功快照，实现页面先展示、后台刷新。
- Accounting 异常账号增加平均速率与计数器回退记录，方便核验 TB 级流量是否具备持续速率证据。

### Changed

- 驾驶舱和 Radius 页面级服务端快照延长为 7 天保底，逻辑新鲜度仍为 1 分钟。
- 认证与 NAS 页面改为面向网络运维的认证量、通过率、拒绝原因和 NAS 处置优先级，移除空白的 NAS 状态事件观测。
- 会话与重连页使用 60 分钟活跃观察窗口，完善空数据说明，并以中文原因、协议代码和明确数量展示下线原因。

### Fixed

- 修复 Accounting 计数器回退时把新基线误算为流量增量的问题；查询端同步排除已有回退记录，避免异常账号流量虚高。

## 2026-07-20

### Added

- 新增脱敏会话交接材料，记录小程序迁移、网管筛选、现场工具、服务器与备份的关键决策和后续验收项。

## 2026-07-19

### Changed

- 水印相机从简化的图片叠加页升级为完整现场拍摄与 Canvas 水印页，恢复旧版字段、样式、拍照和保存能力。
- 高级水印设置改为旧版受控入口：闪光灯 2 秒内连按 5 次、输入 `2026` 后才能进入，权限有效期至当天零点。
- 水印位置改为小程序本地微信地图选择的地点名和地址，不再使用经纬度或后端反查；恢复默认和退出高级设置流程同步补回。

## 2026-07-19

### Added

- 质差和 OLT 性能页均支持按 OLT 筛选；质差统计新增端口异常聚合和低光/高光双色趋势。
- 恢复 uni-app 水印相机与 IPv4 计算器的现场可用能力。
- 功能管理页说明其菜单可见性职责，服务器资料详情提示共享规则及口令审计。

### Changed

- 质差明细先加载，耗时的统计结果独立汇总并显示加载提示；端口统计改由 ClickHouse 聚合，以降低首次查询耗时。
- 服务器详情内部导航改为关闭操作，消除与小程序导航栏重复的返回层级。

## 2026-07-17

### Added

- ONU 7 日光功率图增加月日与时间双行标签；疑似重复记录支持查看完整设备/端口/采集详情，并可切换为主记录加载对应历史。
- 质差管理新增 14 日趋势、OLT 质差排行和端口质差统计表。
- OLT 设备管理按区域和机房组折叠展示。
- BOSS 用户新增超级管理员密码二次验证、5 分钟敏感授权、脱敏列表、逐条详情和审计。
- 新增 `docs/NETOPS_SECURITY_HARDENING.md`，记录 233/236 服务器上线加固与验证清单。
- 新增 233 Nginx 限流、236 systemd 沙箱和双机防火墙收口模板；记录线上旧接口、CORS 回显及已知端口的只读核验结果。
- 新增 `zhiwei-api.service` Gunicorn/systemd 模板，并将 Gunicorn 23.0.0 纳入后端依赖。

### Changed

- 工作台将 Go 网管能力合并为单一“网管”分组，ONU 与 CM/CMTS 查询置顶；服务器管理、值班表、水印相机、IP 计算器归入“便捷工具”；系统入口按小程序实际路径去重。
- OLT 性能页默认只选择 CPU/内存异常，不再默认选择采集异常。
- BOSS 菜单最低角色调整为 `super_admin`。
- 新密码升级为 scrypt、12 位/三类字符；新建与重置用户使用随机临时密码。
- 小程序停止保存明文登录密码；JWT 默认有效期缩短到 8 小时。
- 后端 CORS 改为白名单并增加生产密钥校验、登录限流、API 禁止缓存及安全响应头。
- JSCN-233 Nginx 已配置敏感接口分区限流、429、可信客户端 IP 和隐藏版本号；UFW 已将 SSH/MySQL 从任意来源收口至管理内网。

### Fixed

- 兼容生产环境动态菜单中的旧版 Web 网管路径（如 `/dashboard`、`/onu-search`、`/quality`）。菜单现在会映射到对应的 uni-app 网管功能页，避免点击后出现“页面待迁移”。
- 菜单图标会在后端未下发可识别图标时，按已解析的网管功能页显示对应图标。
- 将登录后的 Tab 工作台迁移到新的 `pages/workbench/index` 路由，规避微信开发者工具对旧 `pages/menu/index` 模块的运行缓存，并保留动态菜单与网管路径兼容逻辑。

## 2026-07-15

### Added
- 新增 uni-app 网管中心，覆盖网络总览、ONU 查询、ONU 质差、OLT 性能、采集监控、OLT/CMTS 设备、CM 查询、BOSS 用户、设备组织、区域权限和告警规则。
- 新增 ONU 实时光功率、7 日历史、质差 Excel 导出、BOSS Excel 增量导入和 OLT 新设备检测。
- 新增 `miniapp/src/api/netops.js` 与网管公共指标卡、状态标签、空状态组件。
- 新增 `docs/NETOPS_MINIAPP_MODULE_MAPPING.md`。

### Changed
- 登录后菜单页升级为统一移动运维工作台，重新设计顶部信息层级、功能分组、菜单卡片和网管图标。
- 初始化菜单新增“网管中心”分组和 9 个权限入口，旧 ONU 占位菜单改为停用。
- 全局页面、内容卡片、搜索栏和按钮视觉统一为移动端网管设计体系。

### Verification
- `miniapp/` 执行 `npm.cmd run build:mp-weixin` 通过。
- `python -m compileall backend/app backend/scripts/init_data.py` 通过。
- H5 390×844 手机视口检查通过，控制台无 error/warn。

## 2026-06-03

### Changed
- 服务器管理页按“服务器资料速查工具 / 登录信息钥匙包”重新收敛：首页只保留标题、总数、搜索、分组筛选、新增入口和服务器卡片；卡片只展示图标、名称、IP、环境和用途，整卡点击进入详情。
- 服务器详情页移除底部固定操作栏和重复编辑入口，仅保留顶部右上角“编辑”；顶部摘要卡只展示名称、用途、环境、IP、位置、主机名、UFW 已启用标识、所属分组和轻量共享信息。
- 连接信息改为唯一主展示位置，SSH / MySQL / Web / API / 其他资料统一用连接卡片展示地址、端口、账号、密码、命令和备注，密码支持眼睛图标显示/隐藏和复制。
- 服务器管理接入分组能力：新增服务器分组表、分组共享表和服务器 `group_id`，列表支持按分组筛选，查询范围覆盖自己的服务器、直接共享服务器和共享分组下的服务器。
- 统一服务器、连接、搜索、分组、共享、编辑、眼睛和复制等图标为同一套线性 CSS 图标风格，移除字母占位图标。

### Removed
- 服务器首页移除复制 SSH、复制登录信息、详情、更多、在线/离线/维护统计、在线/离线状态、负责人、共享人数和资料组数等非速查信息。
- 服务器详情页移除常用命令、敏感资料、UFW 开关控制和底部复制/编辑按钮；命令和敏感内容仅保留在所属连接卡片内展示。

### Verification
- `miniapp/` 执行 `npm.cmd run build:mp-weixin` 通过。
- 仓库根目录执行 `python -m compileall backend/app backend/migrations/versions` 通过。

### Added
- 服务器管理新增图标选择、OS/版本、UFW、上联交换机、端口、VLAN、业务网段等字段，新增 Alembic 迁移 `d4e5f6a7b8c9_task14_server_asset_detail_fields.py`。
- 连接资料类型新增 API、交换机，继续沿用 `server_credentials.secret_cipher` 加密保存敏感内容。
- 服务器详情页新增“概览 / 连接 / 命令 / 密钥/资料”Tab，内置 SSH、MySQL、UFW、Linux 系统和交换机常用命令复制。

### Changed
- 重做 uni-app 服务器管理首页，改为移动端卡片列表，仅展示高频信息和快捷操作，不再展示共享人数、资料组数等低频字段。
- 按手机截图反馈二次收敛视觉：统一卡片、Tab、按钮和连接资料卡片对齐，替换系统默认“更多”菜单为自定义轻量菜单。
- 服务器新增/编辑改为分步骤录入：基础、连接提示、系统网络、备注资料。
- 敏感信息默认脱敏；复制含密码 SSH 命令、复制密码/Token/密钥前需要二次确认。

### Fixed
- 按参考图再次修复服务器管理页移动端对齐、字体权重和按钮高度，详情页标题改为当前服务器名称。
- 修复“更多/编辑”底部菜单在微信小程序端出现空白菜单行的问题，菜单项改为普通可点击行，避免原生 `button` 默认结构干扰。
- 编辑服务器弹层取消异常步骤式空行结构，改为基础信息、系统与网络、备注与可见范围三块分组表单。

### Removed
- 服务器管理首页移除在线/离线/维护统计、状态筛选、详情按钮、更多按钮和负责人等低频信息，首页只保留搜索、名称、用途、环境和复制 SSH。
- 服务器详情页移除 Tab 和常驻“更多”操作，改为基础信息、连接信息、常用命令、敏感资料、备注的纵向分组。
- 删除前端 `sshpass` 含密码 SSH 命令入口和相关残留逻辑，密码改为字段内显示/隐藏和单独复制。

### Verification
- `miniapp/` 执行 `npm.cmd run build:mp-weixin` 通过。
- 仓库根目录执行 `python -m compileall backend/app backend/migrations/versions` 通过。

## 2026-06-02

### Added
- 新增服务器管理：后端 `server_assets` 台账表、`server_credentials` 加密资料表、`/api/admin/servers` 接口和超级管理员菜单入口。
- 新增 uni-app “服务器管理”页面，支持搜索、状态筛选、新增、编辑、资料维护、密码复制和 SSH/MySQL 命令复制。
- 新增服务器归属与共享：服务器默认归属创建人，可通过复选用户共享给指定人员查看。
- 新增服务器资料模板：Redis、Kafka 支持按模板生成常用命令，资料支持删除。
- 新增 `gpt-taste` 作为前端设计辅助 skill，本地已安装到 `~/.codex/skills/gpt-taste/SKILL.md`，重启 Codex 后可用。
- 新增 `docs/SERVER_ASSET_MANAGEMENT_DESIGN.md`，沉淀服务器设备信息管理模块后续设计，覆盖多账号、端口服务、应用服务、数据库实例、防火墙规则、资产权限、审计日志和 Word/Excel 导入预览。

### Changed
- 服务器管理需求收敛为资产台账 + 加密资料管理 + 命令生成，不纳入 SSH 执行、监控采集、拓扑和复杂告警。
- 服务器管理页改为“设备卡片 -> 设备详情 -> 独立编辑资料”交互；状态筛选改为下拉，状态操作收敛为编辑设备中的标识。

### Security
- 本次只从外部 Word 中提炼字段结构和模块需求，没有导入真实服务器清单、账号密码、数据库口令、私钥或 token 到仓库。

## 2026-06-01

### Added
- 确认新平台数据库名为 `zhiwei_assistant`，并将 `.env.example` 的 `DATABASE_URL` 示例切换到该库。
- 新增统一工单池核心模型：`work_orders`、`work_order_logs`、`work_order_comments`。
- 新增 Task 10 Alembic 迁移，建立统一工单主表、工单日志表、工单评论表、来源工单去重约束和高频查询索引。
- 新增 `work_order_service`，支持统一工单号生成、内部工单创建、外部工单幂等入池和工单日志写入。

### Verification
- 仓库根目录执行 `python -m compileall backend/app backend/migrations/versions` 通过。
- 安装 `backend/requirements.txt` 后，迁移模块导入检查通过。
- Flask 应用工厂可加载新增的 `WorkOrder`、`WorkOrderLog`、`WorkOrderComment` 模型。
- 使用临时 SQLite 数据库执行 `flask db upgrade` 通过，迁移链可从初始版本升级到 Task 10。
- 已在服务器 `JSCN-233` 的 `/home/yvesyuan/PycharmProjects/anbo_wx` 拉取 Task 10 代码，创建并迁移 `zhiwei_assistant` 数据库。
- 服务器后端进程已重启，`GET /api/health` 返回正常。

## 2026-05-27

### Fixed
- 修正初始化脚本，不再向真实组织树自动补入“安播中心/奥体广电站/玄武广电站/六合广电站”等占位组织。
- 新增超级管理员“日志查看”入口和 `GET /api/admin/logs`，支持查看操作日志与登录日志。
- 登录页新增“记住密码”和“自动登录”开关；勾选记住密码后会回填账号和密码，勾选自动登录后可在无有效 token 时自动提交登录。
- 退出登录后会暂停本地密码自动登录，避免用户主动退出后被立即拉回系统。
- OSS 登录校验补齐旧项目一致的请求头，并兼容 `OSS_BASE_URL` 误配置为带 `/login` 的完整地址。
- OSS 登录校验补充移动端 User-Agent，避免 OSS 服务对默认 Python User-Agent 返回 500 异常页面。
- OSS 错误信息解析补充 `resultInfo` 字段，减少返回信息丢失。

### Verification
- `miniapp/` 执行 `npm.cmd run build:mp-weixin` 通过。
- 仓库根目录执行 `python -m compileall backend/app` 通过。
- 使用用户确认的 OSS 账号直连 OSS `/login` 验证通过：HTTP 200、返回 JSON、`returnCode=0`、响应头包含 `Authorization`。

## 2026-05-26

### Added
- 新增 `miniapp/` uni-app 小程序工程骨架，使用 Vue 3 + uni-app。
- 新增 uni-app 登录、菜单、我的、用户管理页面。
- 新增用户头像管理：后端用户头像字段、头像上传与访问接口，小程序“我的”页可拍照或从相册选择头像，菜单页和我的页展示头像。
- 新增 uni-app 请求封装、登录态缓存、动态菜单加载和用户管理接口封装。
- 新增改密、OSS 账号确认、组织管理、功能管理、水印相机、IP 计算器的 uni-app 页面入口，其中后三类工具/管理页面先作为迁移占位。
- 新增 uni-app 组织管理页面，支持组织列表、新增下级、编辑、启用和禁用。
- 新增 uni-app 功能管理页面，支持菜单列表、新增、编辑、启用和禁用。
- 新增组织启用接口 `POST /api/admin/orgs/{id}/enable`，并兼容 `GET /api/admin/orgs` 查询组织树。
- 新增前端中文标签映射，覆盖角色、用户类型、状态、OSS 绑定状态和常见接口错误。
- 新增组织删除接口 `DELETE /api/admin/orgs/{id}`，支持删除组织及其所有下级组织。
- 组织管理小程序页新增删除入口，删除前弹窗确认并提示下级组织数量。

### Fixed
- 新登录页移除注册、忘记密码和免登录入口。
- 菜单/我的改用 `pages.json` 原生 tabBar，避免旧原生小程序手写底部导航异常。
- 登录后不再强制跳转 OSS 绑定；OSS 绑定改为非强制提醒，未绑定用户仍可进入系统。
- 登录页会自动填入上次登录账号；已有有效 token 时自动校验并进入系统，用户仍可在“我的”页面退出登录以切换账号。
- OSS 绑定页新增“暂不绑定，进入系统”，菜单页对未绑定、待确认或校验失败状态按每次小程序启动提醒一次。
- OSS 绑定成功后默认不再覆盖小程序登录密码；新增“使用 OSS 密码作为小程序登录密码”勾选项，勾选后才覆盖。
- 用户管理页补齐用户类型筛选，并在新 uni-app 页面中统一筛选、新增、编辑、启停和重置密码流程。
- 修复 uni-app 小程序中按钮文字垂直位置偏移的问题，覆盖登录页密码显示按钮、用户管理搜索按钮、新增按钮和弹层关闭按钮。
- 优化手机端管理页排版：移除大面积顶部说明卡片，用户筛选改为可收起，组织管理改为可展开/折叠树形列表，功能管理卡片压缩无效信息。
- 管理页不再直接展示 `active`、`pending`、`internal`、`normal_user` 等英文状态或编码。
- 修复组织管理展开后三级组织跑到列表底部的问题，改为父级下方紧跟子级的树形顺序。

### Verification
- `miniapp/` 执行 `npm run build:mp-weixin` 通过。
- `backend/` 执行 `python3 -m compileall backend/app` 通过。

### Frontend Direction
- 明确小程序前端优先更换为 uni-app 实现。
- 明确现有 `miniprogram/` 原生小程序作为旧实现和迁移参考，不再作为长期前端主线继续扩展。

### Changed
- 确认 `统一工单池_含OSS融合_技术与实施总规划.md` 为项目唯一主纲。
- 重整根目录核心文档结构，统一为 `AGENTS.md`、`PROJECT_PLAN.md`、`PROJECT_STATUS.md`、`DATABASE_DESIGN.md`、`API_DESIGN.md`、`TASK_LOG.md`、`CHANGELOG.md`、`QUESTIONS.md`。
- 将旧版任务清单、旧 API 文档、旧 task log、旧小程序 README/ROADMAP/CHANGELOG、旧 AGENT/AGENTS 说明归档到 `docs/archive/`。
- 明确项目方向为统一用户体系、统一工单池、OSS 工单融合、运维工具聚合入口和后续 Web 管理端。
- 明确 OSS 工单必须进入统一工单主表，不得作为独立孤岛模块。

### Security
- 将 OSS 参考代码中的硬编码示例账号密码替换为占位值。

## 历史记录
- 2026-05-24 以前的后端、小程序、用户管理、组织管理、菜单管理和工作台开发记录已保留在 `docs/archive/docs_task-log.md`、`docs/archive/docs_api.md` 和 `docs/archive/miniprogram_CHANGELOG.md`。
