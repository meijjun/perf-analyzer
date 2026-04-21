# Linux 性能分析器 Web 版 - 项目总结文档

**版本**: v2.0  
**发布日期**: 2026-04-20  
**项目类型**: Web 应用 + AI 性能分析  
**开发周期**: 2 天  

---

## 📋 目录

1. [项目概述](#项目概述)
2. [核心功能](#核心功能)
3. [技术架构](#技术架构)
4. [安装部署](#安装部署)
5. [使用教程](#使用教程)
6. [API 文档](#api 文档)
7. [开发指南](#开发指南)
8. [故障排查](#故障排查)
9. [最佳实践](#最佳实践)

---

## 项目概述

### 背景
基于 linux-performance-analyzer-1.0.0 Skill 开发的全栈 Web 应用，提供 Linux 系统性能监控、分析和优化的完整解决方案。

### 目标用户
- 系统管理员
- DevOps 工程师
- 后端开发人员
- 性能优化工程师

### 核心价值
- 🎯 **实时监控** - 5 秒刷新，全方位性能监控
- 🤖 **AI 分析** - 基于大模型的智能性能分析
- 🛠️ **自动优化** - 一键生成可执行优化脚本
- 📊 **性能基线** - 建立基线，识别性能退化
- 🌍 **跨平台** - Windows/Linux/Docker全支持

---

## 核心功能

### 1. 实时监控仪表板 📊

**功能描述**:
- 每 5 秒自动采集性能指标
- CPU/内存/磁盘/网络全方位监控
- 智能告警检测（支持阈值配置）
- 健康评分系统（0-100 分）
- 实时性能趋势图表（ECharts）

**技术实现**:
```python
# backend/services/monitor_service.py
class RealTimeMonitor:
    - 采集间隔：5 秒
    - 数据历史：最近 100 个数据点
    - 告警历史：最近 50 条告警
    - 回调机制：支持 WebSocket 推送
```

**界面**:
- 4 个指标卡片（CPU/内存/磁盘/健康评分）
- 性能趋势图表
- 实时告警列表
- 自动刷新按钮

### 2. 自动优化命令生成 🛠️

**功能描述**:
- 基于识别的瓶颈自动生成优化命令
- 支持 CPU/内存/磁盘/网络多场景
- 自动生成可执行脚本（.sh/.bat）
- 包含风险提示和回滚方案
- 标准化六要素报告

**优化场景**:
| 场景 | 优化项 | 风险等级 |
|------|--------|----------|
| CPU 过高 | 减少上下文切换、性能模式 | 低 |
| 内存不足 | 降低 swappiness、清理缓存 | 中 |
| 磁盘 I/O 慢 | 调整调度器、增大预读 | 中 |
| 网络慢 | TIME_WAIT 回收、增大队列 | 低 |

**输出示例**:
```bash
#!/bin/bash
# 系统性能优化方案
# 生成时间：2026-04-20T00:00:00

set -e

# 步骤 1: 减少上下文切换
sysctl -w kernel.sched_min_granularity_ns=10000000

# 步骤 2: 降低 Swap 使用倾向
sysctl -w vm.swappiness=10

# 验证
uptime
free -h
```

### 3. 性能基线 📈

**功能描述**:
- 保存性能基线（JSON 格式）
- 对比当前状态与基线
- 智能识别性能退化（>20% 变化）
- 支持多个基线管理
- 趋势分析基础

**使用场景**:
1. 系统正常时保存基线
2. 性能问题时对比基线
3. 定期更新基线
4. 多环境基线对比

**API**:
```http
POST /api/baseline/save
GET  /api/baseline/list
POST /api/baseline/compare
```

### 4. 专业知识库 📚

**集成内容**:
- 7 个专业参考文档（来自 Skill）
- 15 条瓶颈识别规则
- 5 个优化建议模板
- 4 个场景快速命令

**文档分类**:
| 文档 | 内容 | 用途 |
|------|------|------|
| cpu.md | CPU 调优全维度手册 | 上下文切换、NUMA、绑核 |
| memory.md | 内存调优全维度手册 | OOM、Swap、THP |
| disk_io.md | 磁盘 I/O 调优手册 | 调度器、预读、fio |
| network.md | 网络调优全维度手册 | TCP 栈、BBR、高并发 |
| kernel_params.md | 内核参数速查全表 | sysctl 参数 |
| compile_optimization.md | 编译优化指南 | GCC/Clang/PGO/LTO |
| case_studies.md | 5 大实战案例 | MySQL/Nginx/Java/K8s |

---

## 技术架构

### 整体架构

```
┌─────────────────────────────────────────────┐
│              前端 (Vue 3 + Element Plus)     │
├─────────────────────────────────────────────┤
│  dashboard.html  - 实时监控仪表板            │
│  index.html      - 主界面                    │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│         后端 (Flask + Python 3.8+)          │
├─────────────────────────────────────────────┤
│  app.py          - Flask 主程序              │
│  services/       - 业务服务层                │
│    ├── monitor_service.py   - 实时监控      │
│    ├── optimizer_service.py - 优化命令      │
│    ├── baseline_service.py  - 性能基线      │
│    ├── knowledge_base.py    - 知识库        │
│    ├── llm_service.py       - 大模型        │
│    ├── ssh_service.py       - SSH 连接      │
│    └── analysis_service.py  - 分析协调      │
└─────────────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────┐
│              数据存储层                      │
├─────────────────────────────────────────────┤
│  config.yaml     - 配置文件                  │
│  reports/        - 分析报告                  │
│  baselines/      - 性能基线                  │
│  logs/           - 日志文件                  │
└─────────────────────────────────────────────┘
```

### 技术栈

#### 后端
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.8+ | 开发语言 |
| Flask | 2.3+ | Web 框架 |
| Flask-CORS | 4.0+ | 跨域支持 |
| Paramiko | 3.3+ | SSH 连接 |
| PyYAML | 6.0+ | 配置解析 |
| Requests | 2.31+ | HTTP 请求 |

#### 前端
| 技术 | 版本 | 用途 |
|------|------|------|
| Vue 3 | 3.3+ | 前端框架 |
| Element Plus | 2.4+ | UI 组件库 |
| ECharts | 5.4+ | 图表库 |
| Marked | 最新 | Markdown 渲染 |

#### 部署
| 技术 | 用途 |
|------|------|
| Docker | 容器化部署 |
| systemd | Linux 服务管理 |
| Nginx | 反向代理 |

### 代码统计

| 模块 | 文件数 | 代码行数 |
|------|--------|---------|
| 后端服务 | 7 | ~2500 行 |
| 前端页面 | 2 | ~900 行 |
| 部署脚本 | 6 | ~400 行 |
| 文档 | 10 | ~3000 行 |
| **总计** | **25** | **~6800 行** |

---

## 安装部署

### 系统要求

| 平台 | 要求 |
|------|------|
| **Windows** | Windows 10/11, Python 3.8+ |
| **Linux** | Ubuntu 18.04+/CentOS 7+, Python 3.8+ |
| **Docker** | Docker 19.03+, Docker Compose 1.27+ |

### 快速部署

#### Windows
```cmd
# 1. 解压
tar -xzf perf-analyzer-web-v2-final.tar.gz

# 2. 启动
cd perf-analyzer-web
start.bat

# 3. 访问
http://localhost:5000/dashboard
```

#### Linux
```bash
# 1. 解压
tar -xzf perf-analyzer-web-v2-final.tar.gz
cd perf-analyzer-web

# 2. 安装
chmod +x install.sh
./install.sh --with-psutil

# 3. 启动
./start.sh

# 4. 访问
http://localhost:5000/dashboard
```

#### Docker
```bash
# 1. 构建
docker-compose build

# 2. 启动
docker-compose up -d

# 3. 访问
http://localhost:5000/dashboard
```

### 配置文件

编辑 `backend/config/config.yaml`:

```yaml
# 大模型 API Key 配置
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

# 服务器配置
server:
  host: "0.0.0.0"
  port: 5000
  debug: false  # 生产环境设为 false
```

### 生产环境部署

#### 1. 使用 Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

#### 2. Systemd 服务
```ini
[Unit]
Description=Linux Performance Analyzer
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/perf-analyzer-web
ExecStart=/usr/local/bin/gunicorn -w 4 -b 127.0.0.1:5000 backend.app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 3. Nginx 反向代理
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## 使用教程

### 入门教程

#### 1. 首次使用

**步骤 1**: 配置大模型 API Key
1. 编辑 `backend/config/config.yaml`
2. 填入至少一个大模型的 API Key
3. 保存并重启服务

**步骤 2**: 添加目标设备
1. 访问 http://localhost:5000/
2. 点击"添加设备"
3. 填写设备信息（名称、IP、SSH 认证）
4. 点击"添加"

**步骤 3**: 开始分析
1. 选择目标设备
2. 选择大模型
3. 点击"开始分析"
4. 等待分析完成

#### 2. 实时监控

**访问仪表板**:
```
http://localhost:5000/dashboard
```

**功能说明**:
- **指标卡片**: CPU/内存/磁盘/健康评分
- **趋势图表**: 最近 10 分钟性能趋势
- **告警列表**: 最近 20 条告警
- **自动刷新**: 每 5 秒自动更新

**设置告警阈值**:
编辑 `backend/services/monitor_service.py`:
```python
DEFAULT_THRESHOLDS = {
    'cpu_critical': 90,      # CPU 严重阈值
    'cpu_warning': 70,       # CPU 警告阈值
    'memory_critical': 85,   # 内存严重阈值
    'memory_warning': 60,    # 内存警告阈值
    # ... 更多配置
}
```

#### 3. 性能基线使用

**保存基线**:
```bash
curl -X POST http://localhost:5000/api/baseline/save \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": {...},
    "name": "production-baseline",
    "description": "生产环境基线"
  }'
```

**对比基线**:
1. 访问主界面
2. 点击"性能基线"标签
3. 选择要对比的基线
4. 查看对比结果

### 进阶教程

#### 1. 自定义监控指标

编辑 `backend/services/monitor_service.py`:
```python
def _collect_metrics(self):
    metrics = {
        # 添加自定义指标
        'custom_metric': self._collect_custom_metric()
    }
    return metrics
```

#### 2. 添加优化场景

编辑 `backend/services/optimizer_service.py`:
```python
def _add_custom_optimizations(self, plan, metrics, order):
    plan.add_step(
        name="自定义优化",
        command="echo '优化命令'",
        description="优化描述",
        order=order
    )
```

#### 3. 集成告警通知

添加钉钉通知:
```python
def send_dingtalk_alert(message):
    webhook = "https://oapi.dingtalk.com/robot/send?access_token=xxx"
    requests.post(webhook, json={
        "msgtype": "markdown",
        "markdown": {"title": "性能告警", "text": message}
    })
```

---

## API 文档

### 基础 API

#### 健康检查
```http
GET /api/health
```

**响应**:
```json
{
  "status": "ok",
  "timestamp": "2026-04-20T00:00:00",
  "version": "2.0.0"
}
```

### 监控 API

#### 获取当前指标
```http
GET /api/monitor/current
```

**响应**:
```json
{
  "success": true,
  "data": {
    "cpu": {"usage_percent": 45.2},
    "memory": {"usage_percent": 62.1},
    "disk": {"partitions": [...]},
    "network": {"interfaces": [...]}
  }
}
```

#### 获取监控摘要
```http
GET /api/monitor/summary
```

**响应**:
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "health_score": 85,
    "cpu_usage": 45.2,
    "memory_usage": 62.1,
    "active_alerts": 0
  }
}
```

#### 获取历史数据
```http
GET /api/monitor/history?minutes=10
```

#### 获取告警列表
```http
GET /api/monitor/alerts?limit=20
```

### 优化 API

#### 生成优化命令
```http
POST /api/optimize/generate
Content-Type: application/json

{
  "bottlenecks": [
    {"type": "cpu", "severity": "critical"}
  ],
  "metrics": {...}
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "plan": {
      "title": "系统性能优化方案",
      "steps": [...],
      "risks": [...],
      "verify_commands": [...],
      "rollback_commands": [...]
    },
    "script_path": "/path/to/script.sh"
  }
}
```

### 基线 API

#### 保存基线
```http
POST /api/baseline/save
Content-Type: application/json

{
  "metrics": {...},
  "name": "production-baseline",
  "description": "生产环境基线"
}
```

#### 列出基线
```http
GET /api/baseline/list
```

#### 对比基线
```http
POST /api/baseline/compare
Content-Type: application/json

{
  "metrics": {...},
  "baseline_name": "production-baseline"
}
```

---

## 开发指南

### 环境搭建

#### 1. 开发环境
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux
venv\Scripts\activate     # Windows

# 安装依赖
pip install -r requirements.txt

# 安装开发依赖
pip install pytest pytest-cov flake8
```

#### 2. 项目结构
```
perf-analyzer-web/
├── backend/
│   ├── app.py              # Flask 主程序
│   ├── services/           # 业务服务
│   ├── models/             # 数据模型
│   └── logs/               # 日志目录
├── frontend/
│   └── templates/          # HTML 模板
├── docs/                   # 参考文档
├── scripts/                # 辅助脚本
├── reports/                # 报告输出
├── baselines/              # 基线数据
└── tests/                  # 测试用例
```

### 代码规范

#### Python 代码
- 遵循 PEP 8 规范
- 使用 type hints
- 函数添加 docstring
- 异常处理要完整

```python
def analyze_metrics(metrics: Dict[str, Any]) -> List[Dict]:
    """
    分析性能指标
    
    Args:
        metrics: 性能指标字典
        
    Returns:
        瓶颈列表
        
    Raises:
        ValueError: 指标格式错误
    """
    pass
```

#### 前端代码
- 使用 Vue 3 Composition API
- 组件化开发
- 响应式数据管理
- 错误边界处理

### 测试

#### 运行测试
```bash
# 单元测试
python -m pytest tests/ -v

# 覆盖率测试
pytest --cov=backend --cov-report=html

# 功能测试
python test_new_features.py
```

#### 编写测试
```python
def test_monitor_service():
    monitor = get_monitor()
    metrics = monitor.get_current_metrics()
    assert 'cpu' in metrics
    assert 'memory' in metrics
```

### 调试技巧

#### 1. 启用调试模式
编辑 `backend/config/config.yaml`:
```yaml
server:
  debug: true
```

#### 2. 查看日志
```bash
# 实时查看日志
tail -f backend/logs/app.log

# Systemd 日志
journalctl -u perf-analyzer -f

# Docker 日志
docker-compose logs -f
```

#### 3. 使用 Flask Debugger
访问错误页面时，使用 Debugger PIN 进行交互式调试。

---

## 故障排查

### 常见问题

#### 1. 启动失败

**错误**: `ModuleNotFoundError`

**解决**:
```bash
pip install -r requirements.txt
```

**错误**: `Port already in use`

**解决**:
```bash
# 查找占用端口的进程
lsof -i:5000

# 杀死进程
kill -9 <PID>

# 或修改端口
./start.sh --port 8080
```

#### 2. 页面空白

**检查**:
1. 浏览器 Console 错误
2. Flask 日志
3. 网络请求状态

**解决**:
```bash
# 清除浏览器缓存
# 重启 Flask 服务
# 检查前端文件路径
```

#### 3. 监控数据为 0

**原因**: 缺少系统监控工具

**解决**:
```bash
# 安装 sysstat
sudo apt-get install sysstat

# 安装 psutil
pip install psutil
```

#### 4. 编码错误 (Windows)

**错误**: `UnicodeEncodeError: 'gbk' codec can't encode`

**解决**:
```cmd
chcp 65001
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
```

### 日志分析

#### 日志位置
- **应用日志**: `backend/logs/app.log`
- **Systemd**: `journalctl -u perf-analyzer`
- **Docker**: `docker-compose logs`

#### 日志级别
```python
logger.debug()    # 调试信息
logger.info()     # 一般信息
logger.warning()  # 警告
logger.error()    # 错误
logger.critical() # 严重错误
```

---

## 最佳实践

### 性能优化

#### 1. 使用 Gunicorn
```bash
# 生产环境使用 Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 backend.app:app
```

#### 2. 启用缓存
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'simple'})

@cache.cached(timeout=60)
def get_metrics():
    pass
```

#### 3. 数据库优化
- 使用连接池
- 添加索引
- 定期清理旧数据

### 安全建议

#### 1. 配置防火墙
```bash
# UFW
sudo ufw allow 5000/tcp
sudo ufw enable

# firewalld
sudo firewall-cmd --add-port=5000/tcp --permanent
sudo firewall-cmd --reload
```

#### 2. 使用 HTTPS
```bash
# Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

#### 3. 限制访问
```nginx
# Nginx 配置
location / {
    allow 192.168.1.0/24;
    deny all;
}
```

### 监控与维护

#### 1. 日志轮转
```bash
# /etc/logrotate.d/perf-analyzer
/path/to/logs/*.log {
    daily
    rotate 7
    compress
    missingok
}
```

#### 2. 健康检查
```bash
# Crontab
*/5 * * * * curl -f http://localhost:5000/api/health || echo "Service down"
```

#### 3. 定期备份
```bash
# 备份脚本
tar -czf backup_$(date +%Y%m%d).tar.gz baselines/ reports/
```

---

## 附录

### A. 依赖清单

#### Python 依赖
```txt
flask>=2.3.0
flask-cors>=4.0.0
paramiko>=3.3.0
pyyaml>=6.0
requests>=2.31.0
psutil>=5.9.0  # 可选
```

#### 前端依赖
```html
<!-- CDN 加载 -->
Vue 3.3.4
Element Plus 2.4.2
ECharts 5.4.3
Marked (latest)
```

### B. 端口说明

| 端口 | 用途 |
|------|------|
| 5000 | Flask 开发服务器 |
| 8000 | Gunicorn (推荐) |
| 443 | HTTPS (生产) |

### C. 文件权限

```bash
# Linux 权限设置
chmod 755 start.sh stop.sh install.sh
chmod 644 backend/config/config.yaml
chmod 600 backend/logs/*.log
```

### D. 环境变量

```bash
# 推荐设置
export FLASK_APP=app.py
export FLASK_ENV=production
export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8
```

---

**文档版本**: v2.0  
**最后更新**: 2026-04-20  
**维护者**: Linux Performance Analyzer Team
