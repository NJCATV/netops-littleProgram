# API_DESIGN

## 一、设计原则
- API 设计以 `统一工单池_含OSS融合_技术与实施总规划.md` 为准。
- 所有响应保持统一格式：`code`、`message`、`data`。
- 内部接口使用 Bearer Token。
- 外部系统推送与回调支持 token 或 HMAC 签名。
- 工单状态变更必须通过动作接口，不允许前端直接修改 `status`。

## 二、认证与当前用户

> 小程序公开接口统一使用 `/api/netops2026` 命名空间。旧 `/api/*` 路由只作为后端内部兼容或 2025 Web 过渡接口，不再作为小程序调用契约。

### POST /api/netops2026/auth/login
登录接口，支持手机号、用户名或 OSS 账号映射登录。

### GET /api/netops2026/auth/me
返回当前用户、角色、权限、菜单摘要和下一步动作。

`next_action` 当前只用于强制首次修改初始密码：
- `change_password`：用户仍为初始密码，必须先改密。
- `home`：允许进入系统。

OSS 绑定为非强制行为。未绑定、待确认或校验失败的用户允许进入系统，前端在每次重新打开小程序后提醒一次，并可在“我的”页面主动绑定。

客户端登录体验：
- 登录成功后保存上次登录账号，用于下次打开登录页自动填入。
- 客户端不保存明文密码。
- 已有有效 token 时，登录页通过 `GET /api/netops2026/auth/me` 校验并自动进入系统。
- 用户在“我的”页面退出登录后清理 token 和当前用户缓存。

### POST /api/netops2026/auth/change-password
修改当前用户密码。

### POST /api/netops2026/auth/logout
退出登录，客户端清理 token；后续如引入 token 黑名单，再由后端吊销。

## 三、菜单接口

### GET /api/menus
返回当前用户可见菜单。

查询逻辑：
- 按角色权限过滤。
- 按用户类型过滤。
- 菜单入口聚合统一工单、OSS 查询、网管工具和管理功能。

## 四、用户管理接口

### GET /api/netops2026/admin/users
用户列表。

筛选参数：
- `keyword`
- `org_id`
- `role_code`
- `user_type`
- `status`
- `oss_bind_status`
- `page`
- `page_size`

### GET /api/netops2026/admin/users/options
返回组织、角色、状态、用户类型、OSS 绑定状态等选项。

### POST /api/netops2026/admin/users
新增用户。

### PUT /api/netops2026/admin/users/{id}
编辑用户。

### POST /api/netops2026/admin/users/{id}/enable
启用用户。

### POST /api/netops2026/admin/users/{id}/disable
禁用用户。

### POST /api/netops2026/admin/users/{id}/reset-password
重置用户密码。

## 五、组织与菜单管理接口

### GET /api/netops2026/admin/orgs
返回组织列表和组织树。

### GET /api/netops2026/admin/orgs/tree
返回组织列表和组织树。

### POST /api/netops2026/admin/orgs
新增组织。

### PUT /api/netops2026/admin/orgs/{id}
编辑组织。

### POST /api/netops2026/admin/orgs/{id}/enable
启用组织。

### POST /api/netops2026/admin/orgs/{id}/disable
禁用组织。

### DELETE /api/netops2026/admin/orgs/{id}
删除组织及其所有下级组织。删除前会清空相关用户的所属组织和管理组织字段，避免外键约束阻塞。

### GET /api/netops2026/admin/menus
返回功能菜单列表。

### POST /api/netops2026/admin/menus
新增功能菜单。

### PUT /api/netops2026/admin/menus/{id}
编辑功能菜单。

### POST /api/netops2026/admin/menus/{id}/enable
启用功能菜单。

### POST /api/netops2026/admin/menus/{id}/disable
禁用功能菜单。

## 六、服务器管理接口

服务器管理第一版做设备资产台账和加密资料管理，不提供远程命令执行。SSH 密码、MySQL 密码、密钥等敏感值必须加密存储；查看明文需走单独接口并写操作日志。

权限规则：
- 每台服务器有归属用户 `owner_id`。
- 归属用户和超级管理员可以编辑服务器、资料和共享范围。
- 被共享用户可以查看服务器和资料明文，但不能编辑服务器或资料。
- 超级管理员可以查看全部服务器。

### GET /api/netops2026/admin/servers
查看当前用户可见的服务器清单。

查询参数：
- `keyword`：按名称、主机名、内网 IP、公网 IP、用途、负责人、操作系统、上联设备模糊搜索。
- `status`：`active`、`maintenance`、`offline`。
- `environment`：`production`、`staging`、`test`、`backup`。
- `group_id`：服务器分组 ID；`ungrouped` 表示未分组。

返回字段补充：
- `groups`：当前用户可见的分组列表，用于首页分组筛选。

### POST /api/netops2026/admin/servers
新增服务器资产。

请求字段：
- `name`：服务器名称，必填。
- `group_name`：所属分组名称；为空则不归属分组，填写新名称时自动创建当前用户的分组。
- `icon`
- `hostname`
- `intranet_ip`
- `public_ip`
- `role`：用途。
- `location`
- `owner_name`
- `os_name`
- `os_version`
- `upstream_device`
- `upstream_port`
- `upstream_vlan`
- `upstream_network`
- `ufw_enabled`
- `environment`
- `status`
- `remark`
- `share_user_ids`：可见用户 ID 数组。
- `group_share_user_ids`：分组共享用户 ID 数组；被共享用户可查看该分组下的服务器并参与搜索。

### PUT /api/netops2026/admin/servers/{id}
编辑服务器资产。

### GET /api/netops2026/admin/servers/share-options
返回可选共享用户列表和当前用户可见分组列表，用于前端复选选择可见用户和维护分组共享。

### POST /api/netops2026/admin/servers/{id}/status
更新服务器状态。

请求字段：
- `status`：`active`、`maintenance`、`offline`。

### GET /api/netops2026/admin/servers/{id}/credentials
查看服务器资料列表。列表只返回资料元数据、是否已保存密文和可复制命令，不返回明文密码。

### POST /api/netops2026/admin/servers/{id}/credentials
新增服务器资料。

请求字段：
- `name`：资料名称，必填。
- `credential_type`：`ssh`、`mysql`、`database`、`redis`、`kafka`、`api`、`web`、`switch`、`other`。
- `host`：为空时可使用服务器 IP 或主机名生成命令。
- `port`：端口，如 SSH `5333`、MySQL `6603`、Redis `6379`、Kafka `9092`。
- `username`
- `secret`：密码或密钥，后端加密保存。
- `database_name`
- `command`：自定义命令；为空时后端生成安全命令。
- `remark`

### PUT /api/netops2026/admin/servers/credentials/{id}
编辑服务器资料。`secret` 留空表示清空；不传 `secret` 表示不修改密文。

### DELETE /api/netops2026/admin/servers/credentials/{id}
删除服务器资料。

### POST /api/netops2026/admin/servers/credentials/{id}/reveal
查看并返回资料明文。该接口必须写入操作日志。

## 七、后台日志接口

### GET /api/netops2026/admin/logs
超级管理员查看后台日志。

查询参数：
- `type`：`operation` 或 `login`，默认 `operation`。
- `keyword`：按人员、手机号、IP、模块、动作、详情或登录失败原因模糊搜索。
- `page`
- `page_size`

日志现状：
- 登录日志记录在 `login_logs`。
- 后台操作日志记录在 `operation_logs`。
- 初始化脚本、数据导入脚本等离线任务当前不自动写入操作日志，只能通过数据时间戳和部署记录追溯。

## 八、统一工单接口

当前已完成基础数据层：
- `work_orders`
- `work_order_logs`
- `work_order_comments`
- 工单号生成、内部工单创建、外部工单幂等同步和工单日志写入服务

V2 基础接口已统一落在 `/api/netops2026/work-orders`，旧 `/api/work-orders` 仅保留为历史设计说明。

### GET /api/netops2026/work-orders
统一工单列表。

筛选查询参数：
- `keyword`：统一工单号、外部工单号、客户名、电话、业务号、地址
- `source_system`：`INTERNAL`、`OSS`、`EXT_*`
- `status`
- `priority`
- `order_type`
- `business_type`
- `assignee_id`
- `created_from`
- `created_to`
- `updated_from`
- `updated_to`
- `scope`：`self`、`team`、`all`
- `page`
- `page_size`
- `sort`

### GET /api/netops2026/work-orders/{id}
统一工单详情。

### POST /api/netops2026/work-orders
创建内部工单。

### POST /api/netops2026/work-orders/{id}/actions/{action}
工单状态动作接口。

动作示例：
- `accept`
- `start`
- `assign`
- `pause`
- `resume`
- `complete`
- `close`
- `reopen`
- `sync_external`

规则：
- 后端根据当前状态、用户权限和动作计算新状态。
- 前端不得直接提交目标 `status`。
- 每次动作必须写入 `work_order_logs`。

### POST /api/netops2026/work-orders/{id}/comments

新增工单备注。

### POST /api/netops2026/work-orders/{id}/installation/attempts

创建或返回当前智能装维施工轮次。重复调用不会重复创建草稿轮次；后续重新施工会创建新轮次并保留旧证据。

### POST /api/netops2026/work-orders/{id}/installation/photos

向当前施工轮次上传智能体证据，使用 `multipart/form-data`：文件字段为 `photo`，并传 `agent_code`；可选 `photo_role`、`captured_at`、经纬度和 `watermark_json`。支持经文件头核验的 JPG、PNG、WebP，默认单张最大 8 MiB，每个智能体每轮最多 5 张。

### GET /api/netops2026/work-orders/installation/photos/{photo_id}/file

读取施工原图。必须登录且当前用户可见该照片所属工单，不提供公开裸链。

### POST /api/netops2026/work-orders/{id}/installation/agents/{agent_code}/run

对当前轮次指定智能体的有效证据执行质检。业务后端使用最小 `installation.agent.run` 服务身份签名调用 AIOps，成功后保存稳定版本号、配置快照、事实、逐项评分和模型运行摘要；失败保留运行记录和脱敏错误。重复的 `pending` 运行返回 409。

五个 `agent_code` 为 `site_environment`、`onu_label`、`optical_power`、`speed_test`、`splitter_box`。

## 八、现场记录与文件接口

### POST /api/work-orders/{id}/site-records
新增现场施工记录。

### GET /api/work-orders/{id}/site-records
查询现场施工记录。

### POST /api/files/upload
文件上传接口，支持现场照片、水印照片和附件。

### POST /api/netops2026/files/avatar
上传当前用户头像。请求为 `multipart/form-data`，文件字段名为 `avatar`，支持 JPG、PNG、WebP，默认最大 2MB。成功后更新当前用户 `avatar_url` 并返回最新用户信息。

### GET /api/netops2026/files/avatars/{filename}
读取用户头像文件。

施工照片统一使用上述智能装维照片接口；头像继续使用独立头像接口。

## 九、评价接口

### POST /api/work-orders/{id}/evaluations
提交客户评价。

### GET /api/work-orders/{id}/evaluations
查看评价信息。

评价防伪：
- 第一阶段预留验证码/短信适配器。
- 评价提交需记录校验方式和提交时间。

## 十、OSS 接口

当前已实现接口：

### POST /api/netops2026/auth/bind-oss
校验并绑定当前用户 OSS 账号。该接口调用正式 OSS `/login` 进行账号密码校验，成功后加密保存 OSS 密码并更新绑定状态。绑定失败不会阻断用户进入小程序。

请求字段：
- `oss_account`：OSS 账号。
- `oss_password`：OSS 密码。
- `use_oss_password_for_login`：可选布尔值，默认 `false`。为 `true` 时，绑定成功后使用 OSS 密码覆盖小程序登录密码。

待实现接口：

### GET /api/oss/accounts/me
查询当前用户 OSS 绑定状态。

### POST /api/oss/accounts/me
绑定 OSS 账号。

### PUT /api/oss/accounts/me
更新 OSS 账号。

### DELETE /api/oss/accounts/me
解绑 OSS 账号。

### GET /api/oss/work-orders
查询 OSS 原始工单。

查询参数：
- `oss_order_id`
- `customer_name`
- `customer_phone`
- `service_no`
- `address`
- `oss_status`
- `created_from`
- `created_to`

当前 V2 路径为 `GET /api/netops2026/oss/work-orders`。服务端从当前平台用户的 `external_accounts` 读取 OSS 绑定，登录后自动补齐施工区域、本地网和区域参数；token 不落库。

### GET /api/oss/work-orders/{external_order_id}
查询 OSS 原始工单详情。

当前 V2 使用 `POST /api/netops2026/oss/work-orders/detail`，请求体包含 `woNbr`，可选 `soNbr/localNetId/comeHis`。

### POST /api/oss/work-orders/{external_order_id}/sync
将 OSS 工单同步入统一工单池。

规则：
- 使用 `source_system=OSS`。
- 使用 `external_order_id` 去重。
- 原始状态写入 `external_status`。
- 原始载荷写入 `source_payload_json`。

当前 V2 使用 `POST /api/netops2026/oss/work-orders/sync`，接收查询结果中的单条 `order`；使用 `woNbr` 幂等入池并同时写入 `work_order_external_refs`。

### GET /api/netops2026/oss/work-orders/picked
查询当前 OSS 身份已领取的工单。施工区域、本地网、员工编号等参数由服务端登录资料补齐。

### POST /api/netops2026/oss/work-orders/claim
领取 OSS 工单并幂等同步到统一工单池。请求体传入查询结果中的单条 `order`；同一用户重复领取同一 `woNbr` 复用同一 outbox 事件，不重复调用 OSS。

### POST /api/netops2026/oss/work-orders/{work_order_id}/return
将本地已完工工单加入 OSS 回单队列。调用人必须可见该工单，且当前施工轮次必须已有客户签字；接口只入队，不在用户请求内阻塞重试。

### POST /api/netops2026/oss/work-orders/outbox/{outbox_id}/retry
组织管理员或超级管理员手工重试一条失败事件。后台任务 `python scripts/process_oss_outbox.py` 负责正常派发，失败按 1 分钟、5 分钟、15 分钟、1 小时、6 小时、24 小时退避，最多尝试 6 次。

所有领取和回单操作均使用幂等键，并写入 `oss_sync_logs`；OSS 凭据和 token 不进入 outbox 或审计载荷。

### POST /api/oss/work-orders/{external_order_id}/refresh
刷新 OSS 原始状态。

### POST /api/oss/work-orders/{external_order_id}/push-status
将平台状态回推 OSS。是否第一阶段启用待确认。

## 十一、服务器资产管理接口

服务器资产管理用于登记和查询公司服务器、网络设备、数据库实例、应用服务、账号、端口和防火墙规则。详细设计见 `docs/SERVER_ASSET_MANAGEMENT_DESIGN.md`。

权限原则：
- 基础资产信息、网络信息、应用信息、凭据信息分级授权。
- 普通列表和详情接口不得返回明文密码、私钥、token 或数据库口令。
- 查看或复制敏感凭据、生成连接命令、修改资产权限必须写审计日志。
- 连接命令默认不包含密码；密码复制是单独动作。

### GET /api/server-assets
服务器资产列表。

查询参数：
- `keyword`：名称、IP、端口、账号、应用、数据库、备注
- `host`
- `ip`
- `port`
- `protocol`
- `username`
- `asset_type`
- `environment`
- `status`
- `owner_org_id`
- `maintainer_user_id`
- `tag`
- `page`
- `page_size`

### GET /api/server-assets/{id}
服务器资产详情。后端按用户权限裁剪返回资产主档、端口、账号、应用、数据库、防火墙、审计摘要等信息。

### POST /api/server-assets
新增服务器资产。

### PUT /api/server-assets/{id}
编辑服务器资产。

### DELETE /api/server-assets/{id}
软删除服务器资产。

### GET /api/server-assets/{id}/accounts
查询服务器访问账号。

### POST /api/server-assets/{id}/accounts
新增服务器访问账号。

### PUT /api/server-assets/{id}/accounts/{account_id}
编辑服务器访问账号。

### DELETE /api/server-assets/{id}/accounts/{account_id}
删除或停用服务器访问账号。

### POST /api/server-assets/{id}/accounts/{account_id}/credential
新增或更新账号凭据。凭据必须加密存储。

### POST /api/server-assets/{id}/accounts/{account_id}/commands
生成连接命令。

请求字段：
- `command_type`：`ssh`、`scp`、`mysql`、`redis`、`serial`
- `host_type`：`primary`、`intranet`、`public`、`manage`
- `include_password`：默认 `false`，第一版建议不支持返回带密码命令

示例返回：
- `ssh -p 5333 username@172.25.60.20`
- `mysql -h 172.25.60.20 -P 3306 -u username -p`

### POST /api/server-assets/{id}/accounts/{account_id}/secret/reveal
查看或复制敏感凭据。必须具备凭据权限，可按配置要求二次验证，并必须写审计日志。

### GET/POST/PUT/DELETE /api/server-assets/{id}/ports
管理资产端口和服务。

### GET/POST/PUT/DELETE /api/server-assets/{id}/applications
管理资产上的应用服务。

### GET/POST/PUT/DELETE /api/server-assets/{id}/databases
管理数据库实例。

### GET/POST/PUT/DELETE /api/server-assets/{id}/firewall-rules
管理防火墙、Nginx、代理、路由或访问策略。

### GET /api/server-assets/{id}/acl
查询资产授权配置。

### PUT /api/server-assets/{id}/acl
更新资产授权配置。

### GET /api/server-assets/options
查询资产类型、环境、状态、协议、服务类型、标签等选项。

### POST /api/server-assets/import/preview
上传 Word、Excel 或 CSV 并生成导入预览，不直接入库。

### POST /api/server-assets/import/commit
人工确认字段映射后提交导入。识别到密码、token、私钥时必须进入加密凭据，不进入普通备注明文。

## 十二、外部系统接入接口

### POST /api/integrations/work-orders
外部系统推送工单入统一工单池。

### POST /api/integrations/work-orders/{external_order_id}/status
外部系统推送状态更新。

### GET /api/integrations/endpoints
管理外部系统接入配置。

## 十三、回调机制
- 工单状态变化后，根据 `integration_endpoints.callback_url` 生成回调任务。
- 回调请求记录到 `integration_callback_logs`。
- 回调失败需记录响应并按策略重试。
- HMAC 签名应基于原始请求体生成和校验。

## 十四、网管平台接口复用

小程序网管页面复用现有 `/api/netops2026` 接口和统一 Bearer Token。接口源码由 `newGoColletor/backend/ops-platform-api/ops_platform_api.py` 维护。

主要接口组：
- `/dashboard`：网络运行总览。
- `/onu/search`、`/onu/history`、`/onu/realtime-power`：ONU 查询、历史和实时光功率。
- `/onu/quality-daily`、`/onu/quality-daily/export`：质差管理和导出。
- `/olt/performance`、`/olt/performance/detail`：OLT 性能与板卡/端口详情。
- `/collector/overview`、`/collector/tasks`、`/collector/devices`、`/collector/history`：采集监控。
- `/olt/devices`、`/olt/probe`：OLT 设备与新设备检测。
- `/cm/search`、`/cmts/devices`：CM 查询与 CMTS 管理。
- `/boss/users`、`/boss/users/import`：BOSS 用户查询和 Excel 增量导入。
- `/device-orgs`、`/organization-mappings`：设备组织和用户组织区域映射。
- `/settings`、`/settings/quality/onu-rx-rule`、`/settings/performance/olt-rule`：告警规则。
- `/radius/profile`：按账号或终端 MAC 生成 Radius 用户画像，包含认证、会话、流量、问题线索和 ONU 一致性核验。
- `/aiops/ai-runs`、`/aiops/ai-runs/{run_uid}`：AIOps 分析历史和单次分析报告。
- `/aiops/runtime/overview`、`/aiops/runtime/freshness`：AIOps 来源数据量和数据新鲜度。
- `/aiops/fault-kb/chat`、`/aiops/fault-kb/chat/sessions`：AI 运维问答和个人历史会话。

移动端页面映射见 `docs/NETOPS_MINIAPP_MODULE_MAPPING.md`。

### BOSS 敏感资料安全约束

- `POST /api/netops2026/boss/access`：仅 `super_admin`；使用当前小程序登录密码二次验证，返回 5 分钟内有效的敏感访问令牌。
- `GET /api/netops2026/boss/users`：仅 `super_admin`，必须携带 `X-Boss-Access`；关键词至少 4 位、禁止 `%`/`_` 通配符、每页最多 20 条，列表字段脱敏。
- `GET /api/netops2026/boss/users/{id}`：仅 `super_admin`，必须携带 `X-Boss-Access`；逐条返回完整详情并写审计。
- `POST /api/netops2026/boss/users/import`：仅 `super_admin`，必须携带 `X-Boss-Access`；只允许不超过 10MB 的 xlsx 文件并写审计。
- 授权、查询、详情、导入均限流并写 `operation_logs`；查询审计只保存关键词 SHA-256，不保存明文关键词。
- BOSS 响应统一 `Cache-Control: no-store`；小程序敏感授权不写本地存储。
