# Linux 部署指南

## 📋 系统要求

- **操作系统**: Ubuntu 18.04+, CentOS 7+, Debian 9+, 或其他 Linux 发行版
- **Python**: 3.8 或更高版本
- **内存**: 至少 512MB
- **磁盘**: 至少 1GB 可用空间

---

## 🚀 快速部署

### 方法 1: 一键安装脚本（推荐）

```bash
# 解压文件
tar -xzf perf-analyzer-web-windows-ready.tar.gz
cd perf-analyzer-web

# 运行安装脚本
chmod +x install.sh
./install.sh --with-psutil

# 启动服务
./start.sh
```

**访问地址**:
- 实时监控：http://localhost:5000/dashboard
- 主界面：http://localhost:5000/

### 方法 2: 手动安装

```bash
# 1. 安装 Python 3.8+
# Ubuntu/Debian:
sudo apt-get update
sudo apt-get install -y python3 python3-pip

# CentOS/RHEL:
sudo yum install -y python3 python3-pip

# 2. 安装依赖
cd perf-analyzer-web
pip3 install -r requirements.txt

# (可选) 安装增强监控
pip3 install psutil

# 3. 创建目录
mkdir -p backend/logs backend/config reports baselines

# 4. 启动服务
cd backend
python3 app.py
```

### 方法 3: Docker 部署

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看状态
docker-compose ps
docker-compose logs -f

# 4. 停止服务
docker-compose down
```

---

## 🔧 配置说明

### 1. 大模型 API Key 配置

编辑 `backend/config/config.yaml`:

```yaml
llm:
  aliyun:
    api_key: "sk-xxx"  # 阿里云 DashScope
    enabled: true
  deepseek:
    api_key: "xxx"     # DeepSeek
    enabled: true
  zhipu:
    api_key: "xxx"     # 智谱 AI
    enabled: true
```

**获取 API Key**:
- **阿里云**: https://dashscope.console.aliyun.com/
- **DeepSeek**: https://platform.deepseek.com/
- **智谱 AI**: https://open.bigmodel.cn/

### 2. 服务器配置

编辑 `backend/config/config.yaml`:

```yaml
server:
  host: "0.0.0.0"  # 监听所有网卡
  port: 5000       # 端口号
  debug: false     # 生产环境关闭调试
```

### 3. 自定义端口

```bash
./start.sh --port 8080
```

---

## 🎯 高级部署

### 1. Systemd 服务（开机自启）

创建服务文件 `/etc/systemd/system/perf-analyzer.service`:

```ini
[Unit]
Description=Linux Performance Analyzer
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/perf-analyzer-web
ExecStart=/usr/bin/python3 -m flask --app backend.app run --host=0.0.0.0 --port=5000
Restart=always
Environment=FLASK_APP=app.py
Environment=FLASK_ENV=production

[Install]
WantedBy=multi-user.target
```

**管理命令**:
```bash
# 重新加载配置
sudo systemctl daemon-reload

# 启用服务
sudo systemctl enable perf-analyzer

# 启动服务
sudo systemctl start perf-analyzer

# 查看状态
sudo systemctl status perf-analyzer

# 查看日志
sudo journalctl -u perf-analyzer -f

# 停止服务
sudo systemctl stop perf-analyzer
```

### 2. Nginx 反向代理

安装 Nginx:
```bash
sudo apt-get install -y nginx  # Ubuntu/Debian
sudo yum install -y nginx      # CentOS/RHEL
```

配置 Nginx (`/etc/nginx/sites-available/perf-analyzer`):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置:
```bash
sudo ln -s /etc/nginx/sites-available/perf-analyzer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 3. HTTPS 配置（Let's Encrypt）

```bash
# 安装 Certbot
sudo apt-get install -y certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 📊 性能优化

### 1. 使用 Gunicorn（生产环境）

```bash
# 安装
pip3 install gunicorn

# 启动
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

Systemd 配置 (`/etc/systemd/system/perf-analyzer.service`):

```ini
[Service]
User=your_user
WorkingDirectory=/path/to/perf-analyzer-web
ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:5000 backend.app:app
Restart=always
```

### 2. 使用 Redis 缓存（可选）

```bash
# 安装 Redis
sudo apt-get install -y redis-server

# 配置应用使用 Redis
# 编辑 backend/app.py 添加 Redis 缓存
```

### 3. 日志轮转

创建 `/etc/logrotate.d/perf-analyzer`:

```
/path/to/perf-analyzer-web/backend/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 your_user your_user
}
```

---

## 🔍 监控与维护

### 查看日志

```bash
# 应用日志
tail -f backend/logs/app.log

# Systemd 日志
sudo journalctl -u perf-analyzer -f

# Nginx 日志
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 性能监控

```bash
# 查看进程
ps aux | grep perf-analyzer

# 查看端口占用
netstat -tlnp | grep 5000
# 或
ss -tlnp | grep 5000

# 查看资源使用
top -p $(pgrep -f "python.*app.py")
```

### 备份数据

```bash
# 备份基线数据
tar -czf baselines_backup_$(date +%Y%m%d).tar.gz baselines/

# 备份配置
cp backend/config/config.yaml config_backup_$(date +%Y%m%d).yaml

# 备份报告
tar -czf reports_backup_$(date +%Y%m%d).tar.gz reports/
```

---

## 🐛 故障排查

### 问题 1: 端口被占用

**错误**: `OSError: [Errno 98] Address already in use`

**解决**:
```bash
# 查找占用端口的进程
lsof -i:5000
# 或
netstat -tlnp | grep 5000

# 杀死进程
kill -9 <PID>

# 或修改端口
./start.sh --port 8080
```

### 问题 2: 权限不足

**错误**: `Permission denied`

**解决**:
```bash
# 设置正确权限
chmod -R 755 /path/to/perf-analyzer-web
chown -R your_user:your_user /path/to/perf-analyzer-web
```

### 问题 3: Python 版本过低

**错误**: `SyntaxError` 或 `ModuleNotFoundError`

**解决**:
```bash
# 安装 Python 3.10
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt-get update
sudo apt-get install -y python3.10 python3.10-venv python3.10-distutils

# 使用虚拟环境
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 问题 4: 依赖安装失败

**错误**: `Could not find a version that satisfies the requirement`

**解决**:
```bash
# 升级 pip
pip3 install --upgrade pip

# 清除缓存
pip3 cache purge

# 使用国内镜像
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 5: 监控数据为 0

**原因**: 缺少系统监控工具

**解决**:
```bash
# 安装 sysstat (提供 iostat, mpstat 等)
sudo apt-get install -y sysstat

# 安装 iotop
sudo apt-get install -y iotop

# 安装 psutil (Python 库)
pip3 install psutil
```

---

## 📈 性能基准测试

```bash
# 使用 ab (Apache Bench) 测试
ab -n 1000 -c 10 http://localhost:5000/api/health

# 使用 wrk 测试
wrk -t12 -c400 -d30s http://localhost:5000/api/health
```

---

## 📞 获取支持

### 日志位置
- 应用日志：`backend/logs/app.log`
- Systemd 日志：`journalctl -u perf-analyzer`
- Nginx 日志：`/var/log/nginx/`

### 诊断命令
```bash
# 检查 Python 版本
python3 --version

# 检查依赖
pip3 list | grep -E "flask|paramiko|pyyaml"

# 检查服务状态
systemctl status perf-analyzer

# 检查端口
netstat -tlnp | grep 5000

# 运行诊断脚本
./check_windows.py
```

---

*最后更新：2026-04-19*  
*版本：v2.0 Linux 正式版*
