# Windows 部署指南

## 📋 部署前检查

### 系统要求
- ✅ Windows 10/11
- ✅ Python 3.8+
- ✅ 管理员权限（部分优化命令需要）

### 环境准备

1. **安装 Python**
   ```
   下载地址：https://www.python.org/downloads/
   安装时勾选 "Add Python to PATH"
   ```

2. **安装依赖**
   ```cmd
   cd perf-analyzer-web
   pip install -r requirements.txt
   ```

3. **设置环境变量（可选但推荐）**
   ```cmd
   setx PYTHONUTF8 1
   setx PYTHONIOENCODING utf-8
   ```

---

## 🚀 快速启动

### 方法 1: 使用启动脚本（推荐）

```cmd
cd perf-analyzer-web
start.bat
```

**自动完成**:
- ✅ 切换代码页为 UTF-8
- ✅ 设置 Python 环境变量
- ✅ 启动 Flask 服务

### 方法 2: 手动启动

```cmd
cd perf-analyzer-web\backend
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python app.py
```

### 方法 3: PowerShell

```powershell
cd perf-analyzer-web\backend
$env:PYTHONUTF8=1
$env:PYTHONIOENCODING="utf-8"
python app.py
```

---

## 🌐 访问服务

启动成功后，在浏览器访问：

| 功能 | 地址 |
|------|------|
| **实时监控仪表板** | http://localhost:5000/dashboard |
| **主界面** | http://localhost:5000/ |
| **API 测试** | http://localhost:5000/api/health |

---

## 📊 功能兼容性

### ✅ 完全兼容功能

| 功能 | Windows 支持 | 说明 |
|------|-------------|------|
| 实时监控 | ✅ | 本机模式完美支持 |
| 性能基线 | ✅ | JSON 存储，跨平台 |
| 优化命令生成 | ✅ | 自动生成命令 |
| 参考文档 | ✅ | 网页浏览 |
| 大模型分析 | ✅ | API 调用 |
| 设备管理 | ✅ | 配置管理 |

### ⚠️ 需要注意的功能

| 功能 | Windows 支持 | 注意事项 |
|------|-------------|----------|
| SSH 远程连接 | ⚠️ | 需要安装 Paramiko，部分命令需调整 |
| 优化命令执行 | ⚠️ | Linux 命令在 Windows 下不可用，需使用 apply_optimization.py |
| 系统监控命令 | ⚠️ | 部分 Linux 命令（vmstat, iostat）需安装 WSL 或替代工具 |

### ❌ 不支持的功能

| 功能 | 替代方案 |
|------|---------|
| sysctl 命令 | Windows 注册表调整 |
| /proc 文件系统 | Windows Performance Monitor |
| bash 脚本 | .bat 或 PowerShell 脚本 |

---

## 🔧 Windows 特定配置

### 1. 日志路径

已自动适配 Windows：
```python
# 自动使用反斜杠
logs/app.log  →  D:\AI_Project\perf-analyzer-web\backend\logs\app.log
```

### 2. 性能基线存储

```python
# 自动使用 pathlib 处理路径
../baselines/ → D:\AI_Project\perf-analyzer-web\baselines\
```

### 3. 优化脚本执行

**不要直接运行生成的 .sh 脚本**，使用：

```cmd
python backend\apply_optimization.py reports\optimization_plan.json
```

---

## 🛠️ 常见问题解决

### Q1: 启动时出现编码错误

**错误**: `UnicodeEncodeError: 'gbk' codec can't encode character`

**解决**:
```cmd
chcp 65001
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
python app.py
```

或直接使用 `start.bat`

### Q2: 找不到模块

**错误**: `ModuleNotFoundError: No module named 'xxx'`

**解决**:
```cmd
pip install -r requirements.txt
```

如果还有问题：
```cmd
pip install flask flask-cors paramiko pyyaml requests
```

### Q3: 端口被占用

**错误**: `OSError: [WinError 10048] Only one usage of each socket address`

**解决**:
1. 修改端口：编辑 `app.py`，将 `port=5000` 改为其他端口
2. 或者关闭占用 5000 端口的程序

### Q4: 权限不足

**错误**: `Permission denied` 或 `Access is denied`

**解决**:
- 以管理员身份运行 CMD/PowerShell
- 或者右键 `start.bat` → "以管理员身份运行"

### Q5: 监控数据显示 0

**原因**: Windows 下部分 Linux 命令不可用

**解决**:
- 安装 WSL (Windows Subsystem for Linux)
- 或者使用远程 SSH 连接 Linux 服务器

---

## 📁 目录结构（Windows）

```
D:\AI_Project\perf-analyzer-web\
├── backend\
│   ├── app.py                    # 主程序
│   ├── services\
│   │   ├── monitor_service.py    # 实时监控
│   │   ├── optimizer_service.py  # 优化命令
│   │   ├── baseline_service.py   # 性能基线
│   │   └── ...
│   ├── logs\                      # 日志目录（自动创建）
│   ├── apply_optimization.py     # Windows 优化执行脚本
│   └── generate_optimization.bat # Windows 脚本生成器
├── frontend\templates\
│   ├── dashboard.html            # 实时监控仪表板
│   └── index.html                # 主界面
├── docs\                          # 参考文档
├── reports\                       # 优化报告
├── baselines\                     # 性能基线
├── start.bat                      # Windows 启动脚本
└── requirements.txt               # Python 依赖
```

---

## 🔍 性能监控建议（Windows）

### 本机监控

如果是监控 Windows 本机：
- ✅ CPU 使用率 - 通过 `/proc/stat` 模拟
- ✅ 内存使用率 - 通过 `/proc/meminfo` 模拟
- ⚠️ 磁盘 I/O - 部分指标不可用
- ⚠️ 网络统计 - 部分指标不可用

**建议**: 安装 psutil 增强 Windows 支持
```cmd
pip install psutil
```

### 远程监控 Linux 服务器

如果是通过 SSH 监控 Linux 服务器：
- ✅ 所有功能完全支持
- ✅ 需要配置 SSH 连接
- ✅ 在 Web 界面添加目标设备

---

## 📊 性能优化建议（Windows 环境）

### 1. 使用 WSL 2

安装 WSL 2 可以获得完整的 Linux 兼容性：
```cmd
wsl --install
```

### 2. 使用 Docker

在 Docker 中运行获得最佳兼容性：
```cmd
docker run -p 5000:5000 perf-analyzer-web
```

### 3. 远程 Linux 服务器

最佳方案：在 Linux 服务器上运行，Windows 只作为访问端

---

## 🎯 验证安装

运行检查脚本：
```cmd
cd perf-analyzer-web
python check_windows.py
```

运行功能测试：
```cmd
cd perf-analyzer-web
python test_new_features.py
```

访问仪表板验证：
```
http://localhost:5000/dashboard
```

---

## 📞 获取帮助

如果遇到问题：

1. 查看日志文件：`backend\logs\app.log`
2. 运行检查脚本：`python check_windows.py`
3. 查看本文档的常见问题部分

---

*最后更新：2026-04-19*  
*版本：v2.0 Windows 版*
