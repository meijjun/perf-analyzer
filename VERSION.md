# Linux 性能分析器 Web 版

## 版本信息

**当前版本**: V1.0.0  
**发布日期**: 2026-04-21  
**代码状态**: Stable  

---

## 核心功能

### 1. 实时监控仪表板 📊
- 每 5 秒自动刷新性能指标
- CPU/内存/磁盘/网络全方位监控
- 智能告警检测（支持阈值配置）
- 健康评分系统（0-100 分）
- 实时性能趋势图表

### 2. 远程设备管理 🔌
- 支持 SSH 协议连接
- 支持 Telnet 协议连接
- 支持密钥/密码认证
- 多设备管理

### 3. AI 性能分析 🤖
- 集成多个大模型提供商：
  - 阿里云通义千问
  - DeepSeek
  - 智谱 AI
  - 百度文心一言
  - 自定义 OpenAI 兼容模型
- 基于知识库的智能分析
- 自动识别性能瓶颈

### 4. 自动优化建议 🛠️
- 生成可执行优化脚本
- 包含风险提示和回滚方案
- 标准化六要素报告

### 5. 性能基线 📈
- 保存性能快照
- 对比当前状态与基线
- 识别性能退化

### 6. 专业知识库 📚
- 7 大领域参考文档
- 15 条瓶颈识别规则
- 5 个优化建议模板
- 实战案例参考

---

## 技术栈

### 后端
- Python 3.8+
- Flask 2.3+
- Paramiko 3.3+ (SSH)
- PyYAML 6.0+
- Requests 2.31+
- PsUtil 5.9+ (本地监控)

### 前端
- Vue 3.3+
- Element Plus 2.4+
- ECharts 5.4+
- Marked (Markdown 渲染)

### 部署
- 支持 Windows/Linux/macOS
- Docker 容器化部署
- Systemd 服务管理

---

## 项目结构

```
perf-analyzer-web/
├── backend/
│   ├── app.py                      # Flask 主程序
│   ├── services/
│   │   ├── monitor_service.py      # 实时监控服务
│   │   ├── optimizer_service.py    # 优化命令生成
│   │   ├── baseline_service.py     # 性能基线服务
│   │   ├── knowledge_base.py       # 知识库服务
│   │   ├── llm_service.py          # 大模型服务
│   │   ├── ssh_service.py          # SSH 服务
│   │   ├── telnet_service.py       # Telnet 服务
│   │   └── analysis_service.py     # 分析协调服务
│   ├── models/
│   │   └── config.py               # 配置管理
│   ├── logs/                       # 日志目录
│   └── config/
│       └── config.yaml.example     # 配置示例
├── frontend/
│   └── templates/
│       ├── index.html              # 主界面
│       └── dashboard.html          # 实时监控仪表板
├── docs/                           # 参考文档（7 个）
├── scripts/                        # 辅助脚本
├── reports/                        # 分析报告（运行时生成）
├── baselines/                      # 性能基线（运行时生成）
├── start.bat                       # Windows 启动脚本
├── start.sh                        # Linux 启动脚本
├── install.sh                      # Linux 安装脚本
├── requirements.txt                # Python 依赖
├── README.md                       # 项目说明
├── DEPLOYMENT.md                   # 部署指南
├── PROJECT_SUMMARY.md              # 项目总结
└── VERSION.md                      # 版本信息（本文件）
```

---

## 快速开始

### Windows
```cmd
# 1. 解压
tar -xzf perf-analyzer-web-v1.tar.gz

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置
copy backend\config\config.yaml.example backend\config\config.yaml
# 编辑 config.yaml 填入 API Key

# 4. 启动
start.bat

# 5. 访问
http://localhost:5000/dashboard
```

### Linux
```bash
# 1. 解压
tar -xzf perf-analyzer-web-v1.tar.gz
cd perf-analyzer-web

# 2. 安装
chmod +x install.sh
./install.sh --with-psutil

# 3. 配置
cp backend/config/config.yaml.example backend/config/config.yaml
# 编辑 config.yaml 填入 API Key

# 4. 启动
./start.sh

# 5. 访问
http://localhost:5000/dashboard
```

### Docker
```bash
# 1. 构建
docker-compose build

# 2. 启动
docker-compose up -d

# 3. 访问
http://localhost:5000/dashboard
```

---

## API 接口

### 监控 API
- `GET /api/monitor/current` - 当前指标
- `GET /api/monitor/summary` - 监控摘要
- `GET /api/monitor/history` - 历史数据
- `GET /api/monitor/alerts` - 告警列表

### 分析 API
- `POST /api/analyze` - 开始分析
- `GET /api/tasks/<id>` - 任务状态
- `GET /api/tasks/<id>/report` - 获取报告
- `GET /api/tasks/<id>/raw` - 原始数据

### 优化 API
- `POST /api/optimize/generate` - 生成优化命令

### 基线 API
- `POST /api/baseline/save` - 保存基线
- `GET /api/baseline/list` - 列出基线
- `POST /api/baseline/compare` - 对比基线

### 配置 API
- `GET /api/config/llm` - 获取大模型配置
- `POST /api/config/llm` - 更新配置
- `GET /api/targets` - 获取目标设备
- `POST /api/targets` - 添加设备

---

## 更新日志

### V1.0.0 (2026-04-21)

**新增功能**:
- ✅ 实时监控仪表板
- ✅ SSH/Telnet 远程连接
- ✅ 多模型支持（阿里云/DeepSeek/智谱/百度/自定义）
- ✅ 自动优化命令生成
- ✅ 性能基线管理
- ✅ 专业知识库集成
- ✅ 跨平台支持（Windows/Linux/macOS）
- ✅ Docker 容器化部署

**技术特性**:
- ✅ 实时数据采集和保存
- ✅ 详细的调试日志
- ✅ 自动 URL 补全（自定义模型）
- ✅ 多协议支持（SSH/Telnet）
- ✅ 健康评分系统
- ✅ 智能告警检测

**文档**:
- ✅ 完整的部署指南
- ✅ API 接口文档
- ✅ 使用教程
- ✅ 故障排查手册

---

## 已知问题

1. Windows 下本机监控部分指标不可用（需要 WSL）
2. Telnet 连接需要设备支持标准登录流程
3. 部分 Linux 发行版需要手动安装 sysstat

---

## 下一步计划 (V2.0)

- [ ] 告警通知集成（钉钉/企业微信）
- [ ] 容器/K8s 专项监控
- [ ] AI 智能诊断助手
- [ ] 性能预测功能
- [ ] Web UI 优化
- [ ] 多语言支持

---

## 贡献者

- 开发团队：AI 产品矩阵团队
- 技术支持：OpenClaw 社区
- 知识库：linux-performance-analyzer Skill

---

## 许可证

MIT License

---

**项目状态**: ✅ Stable  
**最后更新**: 2026-04-21  
**Git 标签**: v1.0.0
