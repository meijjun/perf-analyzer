# 🚀 跨平台部署总览

**Linux 性能分析器 v2.0** - 支持 Windows 和 Linux 双平台部署

---

## 📦 快速开始

### Windows 用户

```cmd
# 1. 解压
tar -xzf perf-analyzer-web-windows-ready.tar.gz

# 2. 启动
cd perf-analyzer-web
start.bat

# 3. 访问
http://localhost:5000/dashboard
```

### Linux 用户

```bash
# 1. 解压
tar -xzf perf-analyzer-web-windows-ready.tar.gz
cd perf-analyzer-web

# 2. 安装
chmod +x install.sh
./install.sh --with-psutil

# 3. 启动
./start.sh

# 4. 访问
http://localhost:5000/dashboard
```

### Docker 用户

```bash
# 1. 构建
docker-compose build

# 2. 启动
docker-compose up -d

# 3. 访问
http://localhost:5000/dashboard
```

---

## 📋 平台对比

| 功能 | Windows | Linux | Docker |
|------|---------|-------|--------|
| **启动方式** | start.bat | ./start.sh | docker-compose up |
| **停止方式** | Ctrl+C | Ctrl+C 或 ./stop.sh | docker-compose down |
| **后台运行** | 不支持 | --daemon 参数 | 默认后台 |
| **系统监控** | 基础支持 | 完整支持 | 完整支持 |
| **SSH 远程** | ✅ | ✅ | ✅ |
| **优化脚本** | apply_optimization.py | 直接执行 | 直接执行 |
| **开机自启** | 任务计划程序 | systemd | --restart |
| **推荐场景** | 开发测试 | 生产环境 | 生产环境 |

---

## 🎯 核心功能（全平台通用）

### 1. 实时监控仪表板
- 📊 每 5 秒自动刷新
- ❤️ 健康评分系统
- 🚨 智能告警检测
- 📈 性能趋势图表

### 2. 自动优化命令生成
- 🛠️ 基于瓶颈自动生成
- 📝 包含风险提示
- ↩️ 自动回滚方案
- 💾 保存为可执行脚本

### 3. 性能基线
- 📊 保存性能快照
- 📈 对比当前状态
- 🔍 识别性能退化
- 💾 JSON 格式存储

### 4. 专业知识库
- 📚 7 大领域参考文档
- 🛠️ 场景化快速命令
- 📖 5 大实战案例
- ⚙️ 内核参数速查

---

## 🔧 配置文件

所有平台使用同一配置文件：`backend/config/config.yaml`

```yaml
# 大模型配置
llm:
  aliyun:
    api_key: "sk-xxx"  # 填入你的 API Key
    enabled: true
  deepseek:
    api_key: "xxx"
    enabled: true

# 服务器配置
server:
  host: "0.0.0.0"
  port: 5000
  debug: false  # 生产环境设为 false
```

---

## 📊 部署场景

### 场景 1: 本地开发测试

**推荐**: Windows + start.bat

```cmd
cd perf-analyzer-web
start.bat
```

**优点**:
- ✅ 快速启动
- ✅ 调试方便
- ✅ 无需配置

### 场景 2: 生产环境（自有服务器）

**推荐**: Linux + systemd

```bash
# 安装
./install.sh --with-all

# 配置 systemd 服务
sudo cp perf-analyzer.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable perf-analyzer
sudo systemctl start perf-analyzer
```

**优点**:
- ✅ 开机自启
- ✅ 自动重启
- ✅ 完整监控

### 场景 3: 生产环境（容器化）

**推荐**: Docker

```bash
docker-compose up -d
```

**优点**:
- ✅ 环境隔离
- ✅ 易于迁移
- ✅ 资源限制

### 场景 4: 监控远程 Linux 服务器

**推荐**: 任意平台 + SSH 连接

1. 在任意平台启动服务
2. Web 界面添加 SSH 目标设备
3. 远程采集性能数据

**优点**:
- ✅ 跨平台监控
- ✅ 集中管理
- ✅ 无需在被监控服务器安装

---

## 🐛 故障排查

### 通用检查

```bash
# 1. 检查 Python 版本
python3 --version  # 或 python --version

# 2. 检查依赖
pip3 list | grep -E "flask|paramiko"

# 3. 检查端口
netstat -tlnp | grep 5000

# 4. 查看日志
tail -f backend/logs/app.log
```

### Windows 特定

```cmd
# 编码问题
chcp 65001
set PYTHONUTF8=1

# 使用 start.bat
start.bat
```

### Linux 特定

```bash
# 权限问题
chmod +x start.sh
./start.sh

# 端口权限（非 root 不能用 80 端口）
./start.sh --port 8080

# 查看 systemd 状态
systemctl status perf-analyzer
```

---

## 📈 性能优化建议

### 所有平台

1. **安装 psutil**
   ```bash
   pip install psutil
   ```

2. **使用生产服务器**
   ```bash
   # Windows: 不要用于生产
   # Linux: 使用 Gunicorn
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
   ```

3. **启用缓存**
   - 配置 Redis
   - 减少重复计算

### Linux 专属

1. **使用 systemd**
   - 自动重启
   - 日志管理
   - 资源限制

2. **配置 Nginx**
   - 反向代理
   - 负载均衡
   - HTTPS

3. **日志轮转**
   ```bash
   sudo apt-get install logrotate
   ```

---

## 📞 获取支持

### 文档

| 文档 | 内容 |
|------|------|
| **WINDOWS_DEPLOYMENT.md** | Windows 详细部署指南 |
| **LINUX_DEPLOYMENT.md** | Linux 详细部署指南 |
| **NEW_FEATURES.md** | 新功能说明 |
| **FINAL_CHECK.md** | 部署验证清单 |

### 诊断工具

```bash
# Windows & Linux
python check_windows.py
python test_new_features.py

# Linux only
./start.sh --help
systemctl status perf-analyzer

# Docker
docker-compose ps
docker-compose logs
```

### 日志位置

| 平台 | 日志路径 |
|------|---------|
| **Windows** | `backend\logs\app.log` |
| **Linux** | `backend/logs/app.log` |
| **Docker** | `docker-compose logs` |
| **Systemd** | `journalctl -u perf-analyzer` |

---

## 🎉 部署完成验证

访问以下地址验证部署成功：

1. **实时监控仪表板**
   ```
   http://localhost:5000/dashboard
   ```
   - ✅ 页面加载正常
   - ✅ 指标数据刷新
   - ✅ 健康评分显示

2. **API 测试**
   ```
   http://localhost:5000/api/health
   ```
   - ✅ 返回 JSON 数据
   - ✅ status: "ok"

3. **参考文档**
   ```
   http://localhost:5000/ → 点击"参考文档"
   ```
   - ✅ 7 个文档卡片显示
   - ✅ 可以查看文档内容

---

*最后更新：2026-04-19*  
*版本：v2.0 跨平台版*
