# 网管 Web → 微信小程序模块映射

## 目标

将 `F:/codeXSpace/newGoColletor/web/ops-platform` 的网管能力迁入 `miniapp/`，复用现有 `/api/netops2026` 接口、统一登录 token、用户组织范围和角色权限，不在小程序内复制采集逻辑或数据库访问逻辑。

## 页面映射

| Web 模块 | 小程序页面 | 主要能力 |
|---|---|---|
| 统一驾驶舱 | `/pages/netops/dashboard/index` | OLT、采集成功率、质差、性能告警、7 日趋势、高风险 ONU |
| 单台 ONU 查询 | `/pages/netops/onu/index` | MAC/GDF/姓名/地址查询、主记录、重复记录、7 日历史、实时光功率 |
| ONU 质差管理 | `/pages/netops/quality/index` | 日期、原因、关键字筛选、统计、分页、Excel 导出、跳转 ONU |
| OLT 性能看板 | `/pages/netops/performance/index` | CPU/内存/采集异常筛选、设备利用率、板卡和端口详情 |
| 采集监控 | `/pages/netops/collector/index` | 设备状态、采集任务、采集历史、失败原因 |
| OLT 设备管理 / 新设备检测 | `/pages/netops/devices/index` | 设备列表、新增编辑、启停、SNMP 检测 |
| CM MAC 查询 / CMTS 管理 | `/pages/netops/hfc/index` | CM 信号、端口、CMTS 信息、CMTS 新增编辑 |
| Radius 管理系统 | `/pages/netops/radius/index` | 按 GDF/GDC 账号或终端 MAC 汇总认证、流量、会话、问题诊断和 ONU 一致性核验 |
| AIOps 运维看板 / 运维中心 | `/pages/netops/aiops/index` | 最新 AI 研判、必须处理/关注/恢复/降噪分类、证据、处置建议和历史报告 |
| AI 问答 | `/pages/netops/ai-assistant/index` | 故障知识、值班经验和 AIOps 数据问答，支持历史会话 |
| BOSS 用户管理 | `/pages/netops/boss-users/index` | 用户资料搜索、跳转 ONU、管理员 Excel 增量导入 |
| 设备组织 / 权限映射 / 系统配置 | `/pages/netops/admin/index` | 区域机房树、组织区域映射、ONU/OLT 告警阈值 |
| 用户 / 用户组织 / 菜单权限 | 现有 `/pages/admin/*` | 继续复用小程序已有用户、组织和功能管理页面 |

## 接口边界

- 小程序请求统一使用 `miniapp/src/api/request.js` 中的 Bearer token。
- 网管请求封装位于 `miniapp/src/api/netops.js`，统一加 `/netops2026` 前缀。
- 后端网管路由源码仍由 `newGoColletor/backend/ops-platform-api/ops_platform_api.py` 维护，部署时对应服务器 `backend/app/routes/netops2026.py`。
- BOSS 用户不再沿用普通网管权限：仅 `super_admin` 可见和访问，且必须先通过 `/boss/access` 二次验证；列表脱敏、详情逐条审计。
- 小程序仓库只负责移动端页面、菜单和交互，不直接连接 Go Collector、MySQL、ClickHouse、Redis 或采集代理。
- Radius 一键诊断使用 `/radius/profile`。
- AIOps 看板使用 `/aiops/ai-runs`、`/aiops/ai-runs/{run_uid}`、`/aiops/runtime/overview` 和 `/aiops/runtime/freshness`。
- AI 运维问答使用 `/aiops/fault-kb/chat` 和 `/aiops/fault-kb/chat/sessions`。

## 移动端范围取舍

- 接入 Radius 一键诊断，不迁移认证明细大表、完整风险报表、Accounting 全量报表和 CSV 导出；这些能力继续保留在 Web。
- 接入 AIOps 最新研判、历史报告、证据和建议查看，不在手机端提供模型、规则、任务、审计等系统配置。
- 接入 AI 运维问答和个人历史会话，不在手机端提供知识库管理。
- 基础设施拓扑、系统审计、批量管理等低频且信息密集的页面继续使用 Web。

## 移动端设计约束

- 页面使用浅灰底、白色内容区、少量状态色，不照搬 Web 表格。
- 数据列表转换为纵向卡片，优先展示故障定位必需字段。
- 管理动作按角色隐藏；普通用户可查询，组织管理员和系统管理员可维护对应配置。
- 加载、空数据、失败、禁用、质差和告警均有明确状态反馈。
