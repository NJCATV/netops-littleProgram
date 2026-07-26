# 部署文档

## 服务器
- 名称：JSCN-233
- SSH 用户：yvesyuan
- SSH 端口：5333
- API 入口：Nginx `/wx/api/`
- 后端部署路径：`/home/yvesyuan/PycharmProjects/anbo_wx/backend`

## 数据库
- MySQL 端口：6603
- MySQL 用户：anbo
- 数据库：anbo_wx
- 密码：写入服务器 `backend/.env`，不提交仓库。

## 首次部署
```bash
cd /home/yvesyuan/PycharmProjects
git clone git@github.com:NJCATV/littleProgram.git anbo_wx
cd anbo_wx/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

编辑 `.env`，填写真实 `DATABASE_URL`、`SECRET_KEY`、`JWT_SECRET_KEY`、`OSS_PASSWORD_SECRET_KEY`、默认超级管理员手机号和密码。

生成 OSS 加密密钥：
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 数据库迁移
```bash
cd /home/yvesyuan/PycharmProjects/anbo_wx/backend
source .venv/bin/activate
flask db init
flask db migrate -m "task1 initial models"
flask db upgrade
python scripts/init_data.py
```

## 启动命令
开发验证：
```bash
source .venv/bin/activate
python run.py
```

当前 Task 1 临时启动状态：
- 命令：`python run.py`
- 监听：`0.0.0.0:7001`
- 日志：`/tmp/anbo_wx_task1.log`
- 后续正式部署建议改为 Gunicorn + systemd。

Gunicorn：
```bash
source .venv/bin/activate
mkdir -p logs
gunicorn -w 2 -b 127.0.0.1:7001 wsgi:app --access-logfile logs/access.log --error-logfile logs/error.log
```

## 停止命令
临时 Gunicorn 进程：
```bash
pkill -f "gunicorn.*wsgi:app"
```

systemd 方式待创建服务文件后补充。

## 查看日志
```bash
tail -f logs/access.log
tail -f logs/error.log
```

## 健康检查
```bash
curl http://127.0.0.1:7001/api/health
```

Nginx 配置完成后：
```bash
curl https://anbo.njcatv.net:5772/wx/api/health
```

## 本地限制
按当前协作要求，本地不创建 Python 虚拟环境、不安装后端依赖；后端部署、迁移、初始化和测试均在 JSCN-233 服务器执行。
