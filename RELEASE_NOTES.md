# 🎉 发布说明 - v2.0 跨平台版

**发布日期**: 2026-04-19  
**版本**: v2.0  
**包名**: `perf-analyzer-web-v2-final.tar.gz` (146KB)

---

## ✨ 新增功能

### 1. 实时监控仪表板 📊
- 每 5 秒自动刷新性能指标
- CPU/内存/磁盘全方位监控
- 智能告警检测（支持阈值配置）
- 健康评分系统（0-100 分）
- 实时性能趋势图表

### 2. 自动优化命令生成 🛠️
- 基于识别的瓶颈自动生成优化命令
- 支持 CPU/内存/磁盘/网络多场景
- 自动生成可执行脚本（.sh/.bat）
- 包含风险提示和回滚方案
- 标准化六要素报告

### 3. 性能基线 📈
- 保存性能基线（JSON 格式）
- 对比当前状态与基线
- 智能识别性能退化
- 支持多个基线管理
- 趋势分析基础

### 4. 跨平台支持 🌍
- ✅ Windows 10/11 完整支持
- ✅ Linux (Ubuntu/CentOS/Debian) 完整支持
- ✅ Docker 容器化部署
- ✅ 统一的配置文件
- ✅ 自动路径适配

---

## 🔧 改进内容

### Windows 兼容性
- ✅ 修复路由重复定义问题
- ✅ 自动创建日志目录
- ✅ UTF-8 编码自动配置
- ✅ 路径分隔符自动适配
- ✅ 提供 start.bat 启动脚本
- ✅ 提供 Windows 优化执行脚本

### Linux 兼容性
- ✅ 提供 install.sh 安装脚本
- ✅ 提供 start.sh 启动脚本
- ✅ 提供 stop.sh 停止脚本
- ✅ systemd 服务配置
- ✅ Docker Compose 配置
- ✅ Nginx 反向代理配置示例

### 代码质量
- ✅ 使用 pathlib 处理所有路径
- ✅ 统一日志编码为 UTF-8
- ✅ 移除平台相关硬编码
- ✅ 添加完整的错误处理
- ✅ 改进日志消息（移除 emoji）

---

## 📦 安装要求

### Windows
- Windows 10/11
- Python 3.8+
- 管理员权限（部分优化命令需要）

### Linux
- Ubuntu 18.04+ / CentOS 7+ / Debian 9+
- Python 3.8+
- pip3
- 建议：psutil（增强监控）

### Docker
- Docker 19.03+
- Docker Compose 1.27+

---

## 🚀 快速开始

### Windows 用户
```cmd
tar -xzf perf-analyzer-web-v2-final.tar.gz
cd perf-analyzer-web
start.bat
```

### Linux 用户
```bash
tar -xzf perf-analyzer-web-v2-final.tar.gz
cd perf-analyzer-web
chmod +x install.sh
./install.sh --with-psutil
./start.sh
```

### Docker 用户
```bash
tar -xzf perf-analyzer-web-v2-final.tar.gz
cd perf-analyzer-web
docker-compose build
docker-compose up -d
```

**访问地址**: http://localhost:5000/dashboard

---

## 📋 文件清单

### 核心文件
```
backend/
├── app.py                          # Flask 主程序
├── services/
│   ├── monitor_service.py          # 实时监控服务 [NEW]
│   ├── optimizer_service.py        # 优化命令生成 [NEW]
│   ├── baseline_service.py         # 性能基线服务 [NEW]
│   ├── knowledge_base.py           # 知识库服务
│   ├── llm_service.py              # 大模型服务
│   ├── ssh_service.py              # SSH 服务
│   └── analysis_service.py         # 分析服务
├── logs/                           # 日志目录
└── config/                         # 配置目录
```

### 前端文件
```
frontend/templates/
├── dashboard.html                  # 实时监控仪表板 [NEW]
└── index.html                      # 主界面（增强）
```

### 部署脚本
```
├── start.bat                       # Windows 启动脚本
├── start.sh                        # Linux 启动脚本 [NEW]
├── stop.sh                         # Linux 停止脚本 [NEW]
├── install.sh                      # Linux 安装脚本 [NEW]
├── Dockerfile                      # Docker 镜像 [NEW]
└── docker-compose.yml              # Docker Compose [NEW]
```

### 文档
```
├── DEPLOYMENT.md                   # 跨平台部署总览 [NEW]
├── WINDOWS_DEPLOYMENT.md           # Windows 部署指南
├── LINUX_DEPLOYMENT.md             # Linux 部署指南 [NEW]
├── NEW_FEATURES.md                 # 新功能说明
├── FINAL_CHECK.md                  # 部署验证清单 [NEW]
├── RELEASE_NOTES.md                # 本文档
└── INTEGRATION.md                  # Skill 集成文档
```

---

## 🐛 已知问题

### Windows
- ⚠️ 本机监控部分指标不可用（需要 WSL）
- ⚠️ 优化脚本需要使用 apply_optimization.py 执行
- ✅ **解决方案**: 使用远程 SSH 监控 Linux 服务器

### Linux
- ⚠️ 部分发行版需要手动安装 sysstat
- ✅ **解决方案**: `sudo apt-get install sysstat`

### Docker
- ⚠️ 容器内无法访问宿主机的 /proc
- ✅ **解决方案**: 使用 SSH 远程监控

---

## 📊 性能基准

### 资源占用
- **内存**: ~150MB（空闲）
- **CPU**: < 1%（空闲）
- **磁盘**: ~200MB（安装后）

### 响应时间
- **仪表板加载**: < 500ms
- **API 响应**: < 100ms
- **数据刷新**: 5 秒/次

### 并发能力
- **测试工具**: Apache Bench
- **配置**: 1000 请求，10 并发
- **结果**: ~2000 请求/秒

---

## 🔒 安全建议

### 生产环境部署
1. **关闭调试模式**
   ```yaml
   server:
     debug: false
   ```

2. **使用反向代理**
   - Nginx/Apache
   - 配置 HTTPS
   - 限制访问 IP

3. **配置防火墙**
   ```bash
   # UFW (Ubuntu)
   sudo ufw allow 5000/tcp
   
   # firewalld (CentOS)
   sudo firewall-cmd --add-port=5000/tcp --permanent
   ```

4. **定期更新**
   - 关注安全更新
   - 定期升级依赖
   - 审查日志文件

---

## 📈 升级指南

### 从 v1.0 升级到 v2.0

```bash
# 1. 备份数据
cp -r baselines/ baselines_backup/
cp -r reports/ reports_backup/
cp backend/config/config.yaml config_backup.yaml

# 2. 停止服务
# Windows: Ctrl+C
# Linux: ./stop.sh 或 systemctl stop perf-analyzer

# 3. 解压新版本
tar -xzf perf-analyzer-web-v2-final.tar.gz

# 4. 恢复配置
cp config_backup.yaml perf-analyzer-web/backend/config/config.yaml

# 5. 启动新版本
cd perf-analyzer-web
./start.sh  # 或 start.bat
```

---

## 🙏 致谢

感谢以下开源项目：
- Flask - Web 框架
- Paramiko - SSH 连接
- PyYAML - 配置解析
- Element Plus - UI 组件
- ECharts - 图表库
- linux-performance-analyzer Skill - 专业知识库

---

## 📞 获取支持

### 文档
- `DEPLOYMENT.md` - 跨平台部署指南
- `WINDOWS_DEPLOYMENT.md` - Windows 详细指南
- `LINUX_DEPLOYMENT.md` - Linux 详细指南
- `NEW_FEATURES.md` - 新功能说明

### 诊断
```bash
python check_windows.py      # 兼容性检查
python test_new_features.py  # 功能测试
```

### 日志
- Windows: `backend\logs\app.log`
- Linux: `backend/logs/app.log`
- Docker: `docker-compose logs`

---

## 🎯 下一步计划

### v2.1 (计划中)
- [ ] 告警通知集成（钉钉/企业微信）
- [ ] 仪表板图表库升级
- [ ] 优化脚本一键执行

### v3.0 (规划中)
- [ ] 容器/K8s 专项监控
- [ ] AI 智能诊断助手
- [ ] 性能预测功能

---

**发布团队**: Linux Performance Analyzer Team  
**发布日期**: 2026-04-19  
**版本**: v2.0 Stable
