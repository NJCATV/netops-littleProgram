# DATABASE_DESIGN

## 一、设计原则
- 本项目按全新系统建设，不导入旧数据库内容；旧库只作为功能分析参考。
- 数据库设计以 `统一工单池_含OSS融合_技术与实施总规划.md` 为准。
- 统一工单主表必须容纳内部工单、OSS 工单和外部系统工单。
- OSS 原始状态和原始载荷保留，但平台列表、权限、SLA、统计必须使用统一字段。
- 高频筛选字段结构化；来源系统差异放入 JSON。
- 密码、token、OSS 凭据不得明文存储。
- 服务器资产账号、数据库口令、私钥、token 等敏感凭据必须加密存储，列表和普通详情接口不得返回明文。
- 智能装维 V2 的权威结构见 `docs/SMART_INSTALLATION_DATABASE_V2.md`。
- OSS 账号和身份使用 `external_accounts / external_identities / user_external_identity_links`，`users.oss_*` 只在兼容期保留。
- 智能装维通过 `installation_cases.work_order_id` 接入统一工单，不建立独立 OSS 工单主表。

## 二、用户与权限域

### users
当前代码已有 `users` 表雏形，后续需演进为统一用户表。

关键字段：
- `id`
- `username`
- `mobile`
- `real_name`
- `avatar_url`
- `password_hash`
- `user_type`
- `status`
- `org_id`
- `last_login_at`
- `created_at`
- `updated_at`

### roles
- `id`
- `code`
- `name`
- `scope_type`
- `status`
- `created_at`
- `updated_at`

### permissions
- `id`
- `code`
- `name`
- `module`
- `action`
- `created_at`
- `updated_at`

### menus
当前代码已有 `app_menus`，后续统一命名建议为 `menus`。

关键字段：
- `id`
- `parent_id`
- `code`
- `name`
- `path`
- `icon`
- `menu_group`
- `sort_order`
- `visible`
- `status`
- `created_at`
- `updated_at`

### user_roles
- `id`
- `user_id`
- `role_id`
- `created_at`
- 唯一约束：`user_id + role_id`

### role_permissions
- `id`
- `role_id`
- `permission_id`
- `created_at`
- 唯一约束：`role_id + permission_id`

## 三、统一工单域

### work_orders
统一工单主表。OSS 工单和外部系统工单都必须进入该表。

必须支持字段：
- `id`
- `order_no`：平台统一工单号
- `source_system`：`INTERNAL`、`OSS`、`EXT_*`
- `source_module`
- `external_order_id`
- `external_status`
- `sync_mode`：`import_only`、`bidirectional`、`disabled`
- `source_payload_json`
- `title`
- `description`
- `order_type`
- `business_type`
- `status`
- `priority`
- `assignee_id`
- `creator_id`
- `customer_name`
- `customer_phone`
- `customer_no`
- `service_no`
- `address_text`
- `longitude`
- `latitude`
- `closed_at`
- `created_at`
- `updated_at`

索引建议：
- `source_system + external_order_id` 唯一或准唯一索引
- `status`
- `priority`
- `assignee_id`
- `created_at`
- `updated_at`
- `customer_phone`
- `service_no`

### work_order_logs
- `id`
- `work_order_id`
- `actor_id`
- `action`
- `from_status`
- `to_status`
- `detail`
- `created_at`

### work_order_comments
- `id`
- `work_order_id`
- `user_id`
- `content`
- `created_at`
- `updated_at`

## 四、运维资产域

### server_assets
服务器管理第一版记录设备资产台账、人工状态和加密资料，不做监控采集或 SSH 执行。

关键字段：
- `id`
- `owner_id`
- `name`
- `icon`
- `hostname`
- `intranet_ip`
- `public_ip`
- `role`
- `location`
- `owner_name`
- `os_name`
- `os_version`
- `upstream_device`
- `upstream_port`
- `upstream_vlan`
- `upstream_network`
- `ufw_enabled`
- `environment`：`production`、`staging`、`test`、`backup`
- `status`：`active`、`maintenance`、`offline`
- `remark`
- `last_checked_at`
- `created_at`
- `updated_at`

索引建议：
- `name`
- `hostname`
- `intranet_ip`
- `status`
- `environment`

### server_asset_shares
服务器共享表。记录某台服务器额外共享给哪些用户查看。

关键字段：
- `id`
- `server_id`
- `user_id`
- `created_at`

唯一约束：
- `server_id + user_id`

### server_credentials
服务器资料表。SSH、MySQL、Redis、Kafka、Web 等连接资料按类型保存；密码、密钥、数据库密码等敏感值只保存加密后的 `secret_cipher`。

关键字段：
- `id`
- `server_id`
- `name`
- `credential_type`：`ssh`、`mysql`、`database`、`redis`、`kafka`、`api`、`web`、`switch`、`other`
- `host`
- `port`
- `username`
- `secret_cipher`
- `database_name`
- `command`
- `remark`
- `created_at`
- `updated_at`

安全约束：
- 不在列表接口返回明文。
- 查看明文必须走 reveal 接口并写操作日志。
- SSH/MySQL 命令默认不拼接密码，避免复制命令时泄露。

### work_order_site_records
- `id`
- `work_order_id`
- `user_id`
- `record_type`
- `content`
- `longitude`
- `latitude`
- `address_text`
- `created_at`

### work_order_photos
- `id`
- `work_order_id`
- `site_record_id`
- `file_id`
- `photo_type`
- `watermark_text`
- `created_at`

### work_order_evaluations
- `id`
- `work_order_id`
- `customer_phone`
- `score`
- `content`
- `verify_method`
- `verify_token_hash`
- `submitted_at`

## 四、OSS 与外部集成域

### external_accounts
用于保存 OSS 等外部系统账号绑定关系。

- `id`
- `user_id`
- `system_name`
- `external_username`
- `credential_cipher`
- `status`
- `last_verified_at`
- `created_at`
- `updated_at`

### integration_endpoints
- `id`
- `app_id`
- `system_name`
- `auth_mode`
- `token_hash`
- `secret_ref`
- `callback_url`
- `status`
- `created_at`
- `updated_at`

### integration_inbound_logs
- `id`
- `endpoint_id`
- `source_system`
- `request_headers_json`
- `request_body_json`
- `signature_valid`
- `result`
- `work_order_id`
- `created_at`

### integration_callback_logs
- `id`
- `work_order_id`
- `target_system`
- `callback_url`
- `request_body_json`
- `response_status`
- `response_body`
- `retry_count`
- `next_retry_at`
- `created_at`
- `updated_at`

## 五、审计与配置域

## 五、服务器资产管理域

服务器资产管理用于登记公司服务器、网络设备、串口设备、数据库实例、应用服务、账号凭据、端口和防火墙规则。该模块属于运维工具聚合入口和资产台账，不替代统一工单池；后续巡检、故障、变更、账号授权可通过关联表接入统一工单。

详细设计见 `docs/SERVER_ASSET_MANAGEMENT_DESIGN.md`。

### server_assets
服务器或设备主档。

- `id`
- `group_id`
- `asset_code`
- `name`
- `asset_type`：`physical`、`virtual_machine`、`cloud_host`、`network_device`、`serial_console`、`database_host`、`other`
- `environment`：`prod`、`test`、`dev`、`office`、`lab`
- `status`：`active`、`inactive`、`retired`、`unknown`
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

### server_access_accounts
服务器或数据库等访问账号。一台资产可配置多个账号。

- `id`
- `asset_id`
- `protocol`：`ssh`、`serial`、`rdp`、`mysql`、`redis`、`http_admin`、`other`
- `host`
- `port`
- `username`
- `auth_type`：`password`、`private_key`、`token`、`none`
- `credential_id`
- `is_default`
- `purpose`
- `status`
- `last_verified_at`
- `created_at`
- `updated_at`

### server_credentials
加密保存密码、私钥、token 和数据库口令。

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
资产级权限配置，支持按角色、组织、用户或标签授权。

- `id`
- `asset_id`
- `subject_type`：`role`、`org`、`user`、`tag`
- `subject_id`
- `permissions_json`
- `created_by`
- `created_at`

### server_asset_groups
服务器分组，用于把服务器组织为后端、数据库、核心交换机、视频平台、测试环境等一级速查分组。当前实现中服务器可通过 `server_assets.group_id` 归属一个分组。

- `id`
- `owner_id`
- `name`
- `created_at`
- `updated_at`

唯一约束：
- `owner_id + name`

### server_asset_group_shares
服务器分组共享表。被共享用户可以查看该分组下的服务器，并可在首页搜索这些服务器。

- `id`
- `group_id`
- `user_id`
- `created_at`

唯一约束：
- `group_id + user_id`

### server_asset_audit_logs
记录资产查看、凭据查看/复制、命令生成、权限修改等敏感操作。

- `id`
- `asset_id`
- `account_id`
- `credential_id`
- `user_id`
- `action`
- `detail`
- `ip`
- `created_at`

## 六、审计与配置域

### operation_logs
当前代码已有 `operation_logs`，后续保持为统一审计表。

- `id`
- `user_id`
- `module`
- `action`
- `target_type`
- `target_id`
- `detail`
- `ip`
- `created_at`

### system_configs
- `id`
- `config_key`
- `config_value`
- `value_type`
- `remark`
- `created_at`
- `updated_at`

## 七、当前代码与目标设计差异
- 当前已有 `users`、`org_units`、`app_menus`、`login_logs`、`operation_logs`。
- 新平台数据库名已确认为 `zhiwei_assistant`。
- 当前尚无独立 `roles`、`permissions`、`user_roles`、`role_permissions`。
- 当前尚无统一工单池相关表。
- 当前 OSS 绑定字段仍在 `users` 表中，后续建议迁移到 `external_accounts`。
- 当前菜单表名为 `app_menus`，后续可迁移或兼容为 `menus`。
- 当前已具备简化版服务器资产台账、共享可见性和加密资料表；更细的端口服务、应用服务、数据库实例、防火墙规则、资产 ACL 等完整设计仍待后续逐步实现。
