# 服务器设备信息管理模块设计

## 一、模块定位

服务器设备信息管理模块用于登记、查询和审计公司服务器、网络设备、数据库实例、应用服务、账号凭据、端口、防火墙和访问命令等运维资产信息。

本模块属于“运维工具聚合入口”和“资产台账”能力，不替代统一工单池。后续服务器巡检、故障处理、变更申请、账号授权申请可以关联到统一工单，但资产主数据本身独立建模。

设计目标：
- 统一登记公司服务器和相关运维信息。
- 支持按名称、IP、端口、账号、系统、应用、数据库、机房位置、标签快速查询。
- 支持一台服务器多账号、多端口、多数据库、多应用、多防火墙规则。
- 支持按角色、组织、用户、标签配置查看权限和凭据权限。
- 支持一键生成 SSH、SCP、MySQL、Redis、串口等常用登录/连接命令。
- 所有密码、token、私钥、数据库口令必须加密存储，不允许明文写入仓库或普通日志。

## 二、现有资料结构观察

用户提供的 `F:/有线南京-同步/服务器信息.docx` 是现有资产信息来源之一。该文件不纳入仓库，不导入真实密码到文档。

从 Word 结构看，现有信息大致包含：
- SSH/串口连接列表：名称、主机、端口、协议、用户名、说明、修改时间。
- Nginx/访问策略：访问来源、请求端口、页面资源目录、Nginx 判断逻辑、后端 API 转发目标、返回说明。
- 网络接口：接口、IP、掩码、网关、备注。
- 服务器清单：IP、网关、掩码、机房位置、系统、业务信息、硬件信息。
- 混合备注：账号、数据库连接、应用目录、服务端口、防火墙或访问限制。

因此第一版不能只做“SSH 密码本”，应按资产主档拆分为多个子表，保留非结构化备注，并逐步把 Word 中的混合信息规范化。

## 三、核心对象

### 1. 服务器资产

服务器资产是主对象，表示一台物理机、虚拟机、云主机、网络设备、串口设备或跳板入口。

关键字段：
- 资产名称
- 资产编码
- 主机地址/IP
- 内网 IP、公网 IP、管理 IP
- 资产类型：`physical`、`virtual_machine`、`cloud_host`、`network_device`、`serial_console`、`database_host`、`other`
- 环境：`prod`、`test`、`dev`、`office`、`lab`
- 状态：`active`、`inactive`、`retired`、`unknown`
- 机房/位置/机柜/U 位
- 操作系统与版本
- 硬件信息
- 归属部门、负责人、维护人
- 标签
- 备注

### 2. 访问账号

一台资产可以有多个账号，例如 root、普通运维账号、应用账号、数据库管理账号。

关键字段：
- 资产 ID
- 协议：`ssh`、`serial`、`rdp`、`mysql`、`redis`、`http_admin`、`other`
- 主机地址，可继承资产主机
- 端口
- 用户名
- 认证方式：`password`、`private_key`、`token`、`none`
- 凭据引用
- 是否默认账号
- 账号用途说明
- 状态

密码和私钥不进入该表明文字段，只保存凭据引用。

### 3. 加密凭据

用于保存密码、私钥、token、数据库口令等敏感内容。

关键字段：
- 凭据类型：`password`、`private_key`、`token`、`db_password`
- 加密密文
- 脱敏提示，例如长度、末尾 2 位或备注，不保存明文片段
- 密钥版本
- 最近轮换时间
- 过期时间
- 状态

设计要求：
- 使用应用层加密，密钥来自 `.env`，不得提交仓库。
- 后端只在用户具备凭据权限时解密。
- 查看、复制、生成带敏感参数的命令必须写审计日志。
- 列表、搜索、普通详情接口永不返回明文密码。

### 4. 端口与服务

记录服务器上开放端口、协议和对应服务。

关键字段：
- 资产 ID
- 端口
- 协议：`tcp`、`udp`、`serial`
- 服务类型：`ssh`、`http`、`https`、`mysql`、`redis`、`nginx`、`app`、`api`、`other`
- 监听地址
- 对外范围：`intranet`、`public`、`localhost`、`restricted`
- 服务说明
- 状态

### 5. 应用服务

记录部署在服务器上的应用。

关键字段：
- 资产 ID
- 应用名称
- 应用类型：`backend`、`frontend`、`worker`、`nginx`、`database`、`monitoring`、`other`
- 运行用户
- 部署目录
- 启动方式：`systemd`、`supervisor`、`docker`、`pm2`、`script`、`manual`
- 访问 URL
- 关联端口
- 配置目录
- 日志目录
- 备份目录
- 备注

### 6. 数据库实例

记录 MySQL、Redis、PostgreSQL 等数据库实例。

关键字段：
- 资产 ID
- 数据库类型
- 主机
- 端口
- 实例名/库名
- 账号名
- 凭据引用
- 字符集
- 业务用途
- 备份策略
- 状态

### 7. 防火墙与访问策略

记录防火墙、Nginx 白名单、反向代理、端口放行等访问规则。

关键字段：
- 资产 ID
- 规则类型：`firewall`、`nginx`、`security_group`、`route`、`proxy`
- 来源地址/来源网段
- 目标地址
- 目标端口
- 协议
- 动作：`allow`、`deny`、`redirect`、`proxy`
- 规则说明
- 配置位置
- 状态

### 8. 权限与审计

权限必须拆成“资产基础信息权限”和“凭据权限”两层。

建议权限：
- `server_asset.view_basic`：查看资产基础信息。
- `server_asset.view_network`：查看 IP、端口、网络和防火墙信息。
- `server_asset.view_app`：查看应用和数据库非敏感信息。
- `server_asset.view_command`：生成不含密码的连接命令。
- `server_asset.view_secret`：查看或复制敏感凭据。
- `server_asset.edit`：新增和编辑资产。
- `server_asset.manage_acl`：配置资产权限。
- `server_asset.audit`：查看资产访问审计。

授权维度：
- 角色授权。
- 组织授权。
- 指定用户授权。
- 标签授权，例如 `核心系统`、`OSS`、`监控`、`测试`。
- 资产级覆盖授权。

审计场景：
- 查看资产详情。
- 查看或复制凭据。
- 生成连接命令。
- 新增、编辑、删除资产。
- 修改权限。
- 批量导入。

## 四、数据库设计建议

### server_assets

- `id`
- `asset_code`
- `name`
- `asset_type`
- `environment`
- `status`
- `primary_host`
- `intranet_ip`
- `public_ip`
- `manage_ip`
- `os_name`
- `os_version`
- `location`
- `rack`
- `u_position`
- `hardware_info`
- `owner_org_id`
- `owner_user_id`
- `maintainer_user_id`
- `tags_json`
- `remark`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `deleted_at`

索引：
- `asset_code` 唯一索引。
- `primary_host`、`intranet_ip`、`public_ip`、`manage_ip`。
- `asset_type`、`environment`、`status`。
- `owner_org_id`、`maintainer_user_id`。

### server_access_accounts

- `id`
- `asset_id`
- `protocol`
- `host`
- `port`
- `username`
- `auth_type`
- `credential_id`
- `is_default`
- `purpose`
- `status`
- `last_verified_at`
- `created_at`
- `updated_at`

索引：
- `asset_id`
- `protocol + host + port`
- `username`

### server_credentials

- `id`
- `credential_type`
- `ciphertext`
- `secret_hint`
- `key_version`
- `expires_at`
- `rotated_at`
- `status`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

### server_ports

- `id`
- `asset_id`
- `port`
- `protocol`
- `service_type`
- `listen_addr`
- `exposure`
- `description`
- `status`
- `created_at`
- `updated_at`

### server_applications

- `id`
- `asset_id`
- `app_name`
- `app_type`
- `run_user`
- `deploy_path`
- `start_mode`
- `service_name`
- `access_url`
- `config_path`
- `log_path`
- `backup_path`
- `related_ports_json`
- `remark`
- `status`
- `created_at`
- `updated_at`

### server_databases

- `id`
- `asset_id`
- `db_type`
- `host`
- `port`
- `instance_name`
- `database_name`
- `username`
- `credential_id`
- `charset`
- `business_purpose`
- `backup_policy`
- `status`
- `created_at`
- `updated_at`

### server_firewall_rules

- `id`
- `asset_id`
- `rule_type`
- `source`
- `target_host`
- `target_port`
- `protocol`
- `action`
- `config_path`
- `description`
- `status`
- `created_at`
- `updated_at`

### server_asset_acls

- `id`
- `asset_id`
- `subject_type`：`role`、`org`、`user`、`tag`
- `subject_id`
- `permissions_json`
- `created_by`
- `created_at`

### server_asset_audit_logs

- `id`
- `asset_id`
- `account_id`
- `credential_id`
- `user_id`
- `action`
- `detail`
- `ip`
- `created_at`

## 五、API 设计建议

### 资产列表

`GET /api/server-assets`

查询参数：
- `keyword`
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

返回基础信息，不返回敏感凭据。

### 资产详情

`GET /api/server-assets/{id}`

按当前用户权限返回不同字段：
- 基础权限：资产主档。
- 网络权限：端口、网络、防火墙。
- 应用权限：应用、数据库非敏感字段。
- 凭据权限：仅返回可执行的凭据动作，不默认返回明文。

### 新增/编辑资产

- `POST /api/server-assets`
- `PUT /api/server-assets/{id}`
- `DELETE /api/server-assets/{id}`

删除建议第一阶段做软删除。

### 账号与凭据

- `GET /api/server-assets/{id}/accounts`
- `POST /api/server-assets/{id}/accounts`
- `PUT /api/server-assets/{id}/accounts/{account_id}`
- `DELETE /api/server-assets/{id}/accounts/{account_id}`
- `POST /api/server-assets/{id}/accounts/{account_id}/credential`
- `POST /api/server-assets/{id}/accounts/{account_id}/verify`

### 生成连接命令

`POST /api/server-assets/{id}/accounts/{account_id}/commands`

请求字段：
- `command_type`：`ssh`、`scp`、`mysql`、`redis`、`serial`
- `host_type`：`primary`、`intranet`、`public`、`manage`
- `include_password`：默认 `false`，第一版建议不支持返回带密码命令。

示例返回：
- SSH：`ssh -p 5333 username@172.25.60.20`
- SCP：`scp -P 5333 ./file username@172.25.60.20:/target/path`
- MySQL：`mysql -h 172.25.60.20 -P 3306 -u username -p`
- Redis：`redis-cli -h 172.25.60.20 -p 6379 -a '<password>'`，默认不返回密码，只提示单独复制。
- 串口：按实际客户端生成提示，例如 `screen /dev/ttyUSB0 115200`，Windows COM 口仅记录命令模板。

生成命令必须写审计日志。

### 凭据查看/复制

`POST /api/server-assets/{id}/accounts/{account_id}/secret/reveal`

规则：
- 只有 `server_asset.view_secret` 权限可调用。
- 可选二次确认，例如再次输入登录密码。
- 返回短时有效结果，不缓存到前端持久存储。
- 必须写审计日志。
- 可按配置限制只允许“复制”，不允许页面明文展示。

### 应用、数据库、端口、防火墙

- `GET/POST/PUT/DELETE /api/server-assets/{id}/ports`
- `GET/POST/PUT/DELETE /api/server-assets/{id}/applications`
- `GET/POST/PUT/DELETE /api/server-assets/{id}/databases`
- `GET/POST/PUT/DELETE /api/server-assets/{id}/firewall-rules`

### 权限配置

- `GET /api/server-assets/{id}/acl`
- `PUT /api/server-assets/{id}/acl`
- `GET /api/server-assets/options`

### 导入

`POST /api/server-assets/import/preview`

用途：上传 Word、Excel 或 CSV 后先生成预览，不直接入库。

`POST /api/server-assets/import/commit`

用途：人工确认映射后提交入库。

导入要求：
- Word 原文可保存为非公开附件或仅保存导入批次，不写入仓库。
- 自动识别 IP、SSH 命令、端口、用户名、数据库关键字、Nginx 关键字。
- 识别到密码、token、私钥时进入加密凭据，不进入备注明文。
- 导入结果必须显示“可结构化字段”和“待人工确认字段”。

## 六、小程序页面设计

### 菜单入口

菜单分组建议放在“运维工具”或“资产管理”：
- 服务器资产
- 服务器账号
- 端口与服务
- 数据库实例
- 访问审计

### 服务器资产列表

首屏重点：
- 搜索框：名称/IP/端口/账号/应用。
- 快捷筛选：生产、测试、公网、内网、有数据库、有防火墙、最近更新。
- 列表项展示：名称、IP、环境、系统、主要端口、标签、负责人。

手机端避免大面积卡片说明，使用紧凑列表。

### 资产详情

详情页分组：
- 概览：名称、IP、位置、系统、负责人、标签。
- 连接：SSH/串口/数据库账号，支持复制命令。
- 应用：部署目录、服务名、日志目录、访问 URL。
- 数据库：类型、端口、库名、用途、备份策略。
- 网络：端口、防火墙、Nginx/代理。
- 备注：非敏感补充说明。
- 审计：最近访问、最近修改。

### 交互原则

- 普通详情页不展示密码。
- “复制 SSH 命令”和“复制密码”拆成两个动作。
- 复制密码前要求二次确认，后端记录审计。
- 如果用户没有凭据权限，只能看到账号存在和命令模板。
- 对高危资产显示“核心系统”或“敏感资产”标签。

## 七、和统一工单池的关系

服务器资产模块不绕过统一工单池，也不把工单功能塞进资产表。

后续关联方式：
- 工单可关联一个或多个 `server_assets`。
- 服务器巡检记录可生成内部工单。
- 服务器故障、变更、账号授权可以走统一工单动作流。
- 资产详情页可显示最近关联工单。
- 工单详情页可显示关联服务器资产。

建议后续新增关联表：

`work_order_server_assets`
- `id`
- `work_order_id`
- `asset_id`
- `relation_type`：`fault_target`、`change_target`、`inspection_target`、`reference`
- `created_at`

## 八、实施拆分建议

### ServerAsset Task 1：设计和文档

- 产出本设计文档。
- 更新数据库设计和 API 设计。
- 确认不导入真实密码。

### ServerAsset Task 2：后端核心模型

- 建立服务器资产、账号、凭据、端口、应用、数据库、防火墙、ACL、审计模型。
- 建 Alembic 迁移。
- 凭据加密密钥走 `.env`。

### ServerAsset Task 3：资产列表和详情 API

- 实现列表、详情、选项接口。
- 按权限裁剪字段。
- 接入操作日志。

### ServerAsset Task 4：账号、凭据和命令生成

- 实现多账号管理。
- 实现凭据加密保存。
- 实现 SSH/MySQL/Redis/串口命令生成。
- 查看或复制凭据写审计。

### ServerAsset Task 5：uni-app 页面

- 实现服务器资产列表。
- 实现详情页分组。
- 实现复制命令、复制密码、权限提示。

### ServerAsset Task 6：Word/Excel 导入

- 先做导入预览和人工确认。
- 再做提交入库。
- 敏感内容进入凭据密文，不进入普通备注。

## 九、待确认问题

- 是否允许小程序端查看或复制服务器密码，还是只允许 Web 管理端执行该动作。
- 凭据查看是否需要二次验证登录密码或管理员审批。
- 是否需要和现有 SSH 客户端生成特定格式，例如 Xshell、FinalShell、MobaXterm。
- 是否第一版支持私钥上传。
- 是否允许生成带密码的命令。建议第一版不允许。
- Word 导入后的原始附件是否保存到系统内，若保存，应作为敏感附件限制下载。
