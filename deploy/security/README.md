# JSCN-233 / JSCN-236 部署收口模板

本目录只保存无密码、无密钥的部署模板。应用前必须先确认 SSH 管理网段、233/236 实际业务地址和维护窗口，并备份现有 Nginx、UFW、systemd 与环境变量配置。

## 233

1. 将 `jscn233-nginx.conf.example` 中的证书路径、域名和 upstream 与线上配置合并。
   Nginx 备份必须放到 `/etc/nginx/backups/` 等非 `sites-enabled/*` 目录，避免通配 include 把备份重复加载。
2. 删除现有 Nginx 中所有 `Access-Control-Allow-Origin *`、`$http_origin` 回显和宽泛的 `Access-Control-Allow-Methods`；CORS 只由 Flask 的 `CORS_ORIGINS` 精确白名单处理。
3. Gunicorn 只监听 `127.0.0.1:7001`。Redis 只监听回环地址。MySQL `6603` 不向非必要网段开放。
4. UFW 默认拒绝入站，仅放行业务 HTTPS 端口和管理网段 SSH；不要在未验证新的 SSH 会话前关闭现有会话。
5. 使用 `zhiwei-api.service.example` 将微信 API 改为 systemd 管理的 Gunicorn，并只绑定 `127.0.0.1:7001`；部署前确保 `uploads` 与 `logs` 是唯一需要写入的目录。

## 236

1. MySQL `3339` 只允许 233 业务地址和明确的 DBA 管理网段。
2. 采集代理 `18086` 只允许 233 业务地址；健康检查也不得作为匿名公网探针暴露。
3. 轮换采集代理 Token，配置文件权限设为 `0600`，服务使用独立低权限账号。
4. 将 `collector-systemd-override.conf.example` 按实际可写目录调整后，通过 `systemctl edit <service>` 合并；先执行 `systemd-analyze verify` 再重启。

## 防火墙规则骨架

以下命令中的尖括号必须替换，不能原样执行：

```bash
# 233
ufw default deny incoming
ufw allow from <MANAGEMENT_CIDR> to any port 22 proto tcp
ufw allow 5772/tcp
ufw deny 6603/tcp
ufw deny 6379/tcp
ufw deny 7001/tcp

# 236
ufw default deny incoming
ufw allow from <MANAGEMENT_CIDR> to any port 22 proto tcp
ufw allow from <JSCN_233_IP> to any port 3339 proto tcp
ufw allow from <JSCN_233_IP> to any port 18086 proto tcp
ufw deny 3339/tcp
ufw deny 18086/tcp
```

UFW 使用首个匹配规则时需结合当前规则顺序核验；部署前后均执行 `ufw status numbered`，并从 233 与非授权主机分别做连通性测试。
