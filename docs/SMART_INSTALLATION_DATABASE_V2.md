# 智能装维数据模型（智维平台融合版）

## 基本原则

- 智能装维是现有智维平台的一项业务功能，不是独立系统。
- 生产环境只使用智维平台数据库 `anbo_wx`。
- 用户、组织和权限直接复用 `users`、`org_units`、`users.role_code`，不创建第二套账号、角色或成员关系表。
- 公单通账号直接复用 `users.oss_account`、`users.oss_password_cipher`、`users.oss_bind_status`，不创建 `external_accounts`。
- 工单、照片、五项智能检测结果、签字和回单日志通过当前用户 ID、组织 ID 和统一工单 ID 关联。

## 新增业务表

- `work_orders`：智维平台统一工单主表；OSS 工单通过 `source_system + external_order_id` 去重。
- `work_order_assignments / work_order_logs / work_order_comments / work_order_external_refs`：派单、状态流转、沟通和外部编号。
- `installation_cases / installation_attempts`：智能装维任务及多轮整改记录。
- `installation_photos / file_objects`：五类现场证据及文件元数据。
- `installation_ai_runs`：五个智能体每次执行的配置快照、评分、是否通过和说明。
- `installation_signatures`：客户签字。
- `oss_sync_logs / integration_outbox`：公单通请求审计和可靠回单。
- `export_jobs / export_job_items`：Web 管理端批量导出任务。

## 用户与数据范围

- 作业人员只能查看本人创建或承接的工单。
- 组织管理员可查看本组织及下级组织工单。
- 智维平台 `super_admin` 可管理全平台工单和五个智能体定义。
- 所有照片、AI 运行、签字和导出记录都可追溯到现有 `users.id`，不复制用户资料。

## 迁移约束

- Alembic 从生产库当前版本原位升级，只新增智能装维业务表和菜单。
- 初始化脚本只补齐组织根节点与菜单，不创建、不覆盖任何生产用户。
- 上线前后必须核对用户数、用户主键、密码哈希和 OSS 绑定字段保持不变。
