# 智能装维数据库 V2

## 1. 已确认边界

- 本项目按全新系统建设，不导入旧数据库中的用户、组织、工单、照片、AI 结果或日志。
- 旧项目只用于理解功能、OSS 请求格式和页面流程。
- 平台用户以 `users` 为唯一主档；OSS 账号是外部身份，不是平台用户主键。
- `work_orders` 是唯一工单主表；智能装维通过 `installation_cases` 关联工单，不建立第二套工单主表。
- 测试管理员通过环境变量初始化，测试 OSS 账号通过 `external_accounts` 绑定；密码不得进入仓库。

## 2. 用户和外部身份

### 平台身份

- `users`：平台登录账号，支持独立 `username`；手机号可以为空。
- `roles / permissions / user_roles / role_permissions`：可扩展 RBAC。
- `user_org_memberships`：支持主组织、兼职组织和管理组织，并保留有效期。

现有 `role_code / org_id / manage_org_id` 暂时作为兼容字段。新接口逐步切换到关系表后再移除，避免一次切换影响现有小程序。

### OSS 身份

- `external_accounts`：保存用户与 OSS 账号关系及加密凭据。
- `external_identities`：保存 OSS 的账号、`sysUserId`、`staffId` 等身份。
- `user_external_identity_links`：保存平台用户与 OSS 身份的确认关系。
- `external_org_mappings`：保存 OSS 区域、施工区域与平台组织的映射。
- `identity_match_logs`：记录自动候选、人工确认和冲突处理。

自动匹配顺序为：已确认绑定、`sysUserId`、`staffId`、账号、唯一手机号/OA。姓名和组织只能生成候选，不能自动确认。

## 3. 统一工单

- `work_orders`：平台唯一工单主表，保存责任组织、当前处理人、流程版本和乐观锁版本。
- `work_order_external_refs`：保存 OSS 工单号、业务单号、外部状态和原始快照。
- `work_order_assignments`：保存领取、转派、退回全过程，并保存人员和组织名称快照。
- `work_order_logs / work_order_comments`：继续保存状态动作和业务备注。
- `integration_outbox / oss_sync_logs`：保存幂等回单任务及每次 OSS 调用结果。

## 4. 智能装维

- `installation_cases`：一张统一工单最多一个智能装维实例。
- `installation_attempts`：每次施工或重拍形成独立轮次，旧轮次只标记被替代，不删除。
- `file_objects`：统一保存文件元数据、存储键和 SHA-256。
- `installation_photos`：保存标准照片、附加照片、位置、水印和质量检测结果。
- `installation_ai_runs`：保存五智能体单次执行、配置版本、事实提取和规则评分。
- `installation_final_evaluations`：保存综合评分版本。
- `installation_signatures / installation_manual_reviews`：保存签字和人工复核。
- `installation_status_events`：保存完整施工状态时间线。

五个标准智能体编码固定为：

1. `site_environment`：用户门牌及现场环境核验。
2. `onu_label`：ONU 标签识别。
3. `optical_power`：光功率检测。
4. `speed_test`：宽带测速检测。
5. `splitter_box`：光分箱施工质量检测。

AIOps 配置使用稳定的 `agent_version_uid`；业务库同时保存配置快照，保证以后修改识别范围或评分标准时，历史工单仍可还原。

## 5. 文件和导出

- `export_jobs / export_job_items`：Web 端批量导出后台任务。
- 导出结果也进入 `file_objects`，设置到期时间并记录申请人。
- 原始照片下载、批量导出和人工复核分别授权并写审计。

## 6. 初始化和迁移

- Alembic 已整理为单一迁移链；空库统一升级到 `1b2c3d4e5f6a`。
- `scripts/init_data.py` 默认只初始化根组织、管理员、RBAC 和菜单。
- `SEED_DEMO_DATA=false` 时不创建示例服务器或其他业务数据。
- `BOOTSTRAP_OSS_ACCOUNT` 和 `BOOTSTRAP_OSS_PASSWORD` 仅从环境变量读取。
- 初始化脚本可重复执行，不重复创建管理员、角色、组织成员关系或 OSS 身份绑定。
