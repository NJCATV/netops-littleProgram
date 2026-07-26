# 网管小程序（netops-littleProgram）

本仓库包含网管小程序前端、其业务后端、数据库迁移、部署样例和设计文档。它与统一网管共享 233 的受控入口，但保持独立构建和发布。

- 模块架构、数据库、端口与安全：[docs/module-contract.md](docs/module-contract.md)
- 小程序实现：`miniprogram/`、`miniapp/`
- 业务后端与 Alembic 迁移：`backend/`
- 部署与安全样例：`deploy/`

禁止提交真实 `.env`、OSS 凭据、用户导入文件、上传文件、SQLite 开发库或生产日志。
