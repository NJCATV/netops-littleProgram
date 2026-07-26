# 小程序模块架构与安全边界

## 设计

`miniprogram/` 与 `miniapp/` 为小程序客户端实现；`backend/` 是 Flask 业务 API，包含用户、组织、菜单、工单、服务器资产和 OSS 关联能力。数据库演进使用 Alembic migration 管理。

## 数据库

开发默认可使用本地 SQLite；生产必须通过 `DATABASE_URL` 指向受控数据库。数据模型、迁移和权限逻辑在 `backend/app/` 与 `backend/migrations/`，真实连接串只保存在服务器 `.env`。

## 端口与安全

| 接口 | 策略 |
| --- | --- |
| 233:5772 | Nginx TLS 统一入口，向客户端暴露 |
| 127.0.0.1:7001 | Gunicorn 业务 API，仅供 Nginx 反向代理 |
| 233 MySQL 6603 | 仅必要管理网段和应用账号 |

生产 CORS 使用明确白名单；Nginx 不回显任意 Origin；Redis/数据库不向客户端开放。具体样例见 `deploy/security/`。
