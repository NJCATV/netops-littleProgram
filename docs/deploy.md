# 233 部署说明

## 运行位置

| 项目 | 当前生产值 |
| --- | --- |
| 主机 | JSCN-233（`172.31.1.233`） |
| SSH | `5333/tcp`，仅管理网段 |
| 源码目录 | `/srv/netops/netops-littleProgram` |
| 后端工作目录 | `/srv/netops/netops-littleProgram/backend` |
| 服务单元 | `netops-platform-api.service` |
| BFF 监听 | `127.0.0.1:7001` |
| 浏览器入口 | `https://anbo.njcatv.net:5772/` |
| API 前缀 | `/api/netops2026/` |

运行时环境变量文件位于 `/etc/netops/netops-littleProgram.env`，权限为
`root:www-data`、`0640`。该文件、虚拟环境、上传文件、日志、数据库导出及 OSS
凭据均不得提交到 Git。

## 数据库

平台后端仍连接 233 本机 MySQL 的历史物理 schema `anbo_wx`。这是数据库兼容
名称，不是部署目录、服务名或公开 API 名称；不要在新脚本和新 URL 中使用它。

## 发布流程

生产发布通过 `netops-ops/deploy/233/cutover-netops-names.sh` 管理。脚本会在
`/var/backups/netops/` 创建 Nginx 和目标目录备份，随后同步以下仓库到
`/srv/netops/`：

1. `netops-littleProgram`：宿主 Flask 应用与数据库迁移；
2. `netops-platform-api`：嵌入式 `netops2026` BFF 适配层；
3. `netops-portal-web`：已构建的统一门户静态资源。

脚本在切换前执行 `nginx -t`，启动 `netops-platform-api.service`，并以 TLS SNI
验证新路由返回未登录状态 `401`、旧 `/wx/*` 路由返回 `410`。失败时自动恢复旧
Nginx 和旧服务单元；不要手工覆盖生产目录绕过该流程。

## 常用核验

```bash
systemctl is-active netops-platform-api.service
systemctl is-enabled netops-platform-api.service
curl -k --resolve anbo.njcatv.net:5772:127.0.0.1 \
  -o /dev/null -w '%{http_code}\n' \
  https://anbo.njcatv.net:5772/api/netops2026/auth/me
curl -k --resolve anbo.njcatv.net:5772:127.0.0.1 \
  -o /dev/null -w '%{http_code}\n' \
  https://anbo.njcatv.net:5772/wx/api/health
```

预期依次为服务 `active`、`enabled`、新 API `401`、旧路径 `410`。
