# ✅ Windows 部署最终检查清单

## 🎯 已修复的问题

### 1. 路由重复定义 ✅
**问题**: `AssertionError: View function mapping is overwriting an existing endpoint function: dashboard`

**修复**: 删除了重复的 dashboard 路由定义

**验证**: 
```bash
python3 -c "from backend.app import app; print('✅ 路由加载成功')"
```

### 2. 日志路径问题 ✅
**问题**: `FileNotFoundError: [Errno 2] No such file or directory: '../logs/app.log'`

**修复**: 使用 Path 对象自动创建日志目录
```python
log_dir = Path(__file__).parent / 'logs'
log_dir.mkdir(parents=True, exist_ok=True)
logging.FileHandler(log_dir / 'app.log', encoding='utf-8')
```

### 3. 编码问题 ✅
**问题**: `UnicodeEncodeError: 'gbk' codec can't encode character`

**修复**: 
- 日志使用 UTF-8 编码
- 提供 start.bat 自动设置代码页
- 日志消息改用纯文本（移除 emoji）

### 4. 路径分隔符 ✅
**问题**: Windows 使用反斜杠 `\`

**修复**: 所有路径使用 pathlib.Path 对象
```python
from pathlib import Path
config_path = Path('../config/config.yaml')
```

---

## 📋 Windows 部署步骤

### 步骤 1: 解压文件
```cmd
cd D:\AI_Project
tar -xzf perf-analyzer-web-v2.tar.gz
```

### 步骤 2: 安装依赖
```cmd
cd D:\AI_Project\perf-analyzer-web
pip install -r requirements.txt
```

### 步骤 3: 首次启动测试
```cmd
start.bat
```

**预期输出**:
```
============================================
Web 版性能分析器
============================================

正在启动服务...

2026-04-19 22:50:00,000 - models.config - INFO - 配置文件不存在，创建默认配置
2026-04-19 22:50:00,001 - services.knowledge_base - INFO - Loaded doc: cpu.md
...
2026-04-19 22:50:00,100 - __main__ - INFO - Web Performance Analyzer starting...
2026-04-19 22:50:00,101 - __main__ - INFO - Working directory: D:\AI_Project\perf-analyzer-web
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000
 * Running on http://192.168.x.x:5000
```

**没有错误** = ✅ 成功

### 步骤 4: 访问仪表板
浏览器打开：http://localhost:5000/dashboard

**预期显示**:
- ✅ 实时监控仪表板页面加载
- ✅ CPU/内存/磁盘指标卡片显示
- ✅ 健康评分显示
- ✅ 每 5 秒自动刷新

---

## 🔍 功能验证清单

### 基础功能
- [ ] Flask 服务启动成功
- [ ] 无编码错误
- [ ] 无路径错误
- [ ] 日志文件正常创建

### 实时监控
- [ ] 仪表板页面可访问
- [ ] 指标数据正常显示
- [ ] 每 5 秒自动刷新
- [ ] 健康评分计算正确

### 性能基线
- [ ] 可以保存基线
- [ ] 可以列出基线
- [ ] 可以对比基线

### 优化命令
- [ ] 可以生成优化计划
- [ ] 脚本文件正确创建
- [ ] 包含回滚命令

### 参考文档
- [ ] 文档页面可访问
- [ ] 7 个参考文档正常加载

---

## ⚠️ Windows 特定注意事项

### 1. 监控数据来源

**本机监控（Windows）**:
- CPU 使用率：✅ 通过模拟 `/proc/stat`
- 内存使用率：✅ 通过模拟 `/proc/meminfo`
- 磁盘 I/O：⚠️ 部分指标不可用
- 网络统计：⚠️ 部分指标不可用

**建议**: 安装 psutil 增强支持
```cmd
pip install psutil
```

**远程监控（Linux 服务器）**:
- ✅ 所有功能完全支持
- 需要在 Web 界面配置 SSH 连接

### 2. 优化命令执行

**不要直接运行 .sh 脚本**，使用：
```cmd
python backend\apply_optimization.py reports\optimization_plan.json
```

### 3. 系统命令

Windows 下不可用的 Linux 命令：
- `sysctl` → Windows 注册表
- `vmstat` → 任务管理器
- `iostat` → 性能监视器
- `/proc/*` → WMI 或注册表

**解决方案**:
1. 使用 WSL 2
2. 使用远程 Linux 服务器
3. 等待后续 Windows 原生支持更新

---

## 🐛 故障排查

### 问题 1: 启动失败

**症状**: 出现错误信息

**解决**:
1. 查看日志：`backend\logs\app.log`
2. 运行检查：`python check_windows.py`
3. 重新安装依赖：`pip install -r requirements.txt --force-reinstall`

### 问题 2: 页面空白

**症状**: 浏览器显示空白页

**解决**:
1. 按 F12 打开开发者工具
2. 查看 Console 错误
3. 检查 Flask 服务是否正常启动
4. 清除浏览器缓存

### 问题 3: 监控无数据

**症状**: 所有指标显示 0

**解决**:
1. 本机监控：安装 psutil
   ```cmd
   pip install psutil
   ```
2. 或者配置远程 SSH 连接监控 Linux 服务器

### 问题 4: 中文乱码

**症状**: 日志或页面中文乱码

**解决**:
```cmd
chcp 65001
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
```

---

## ✅ 验证命令

运行完整测试：
```cmd
cd perf-analyzer-web
python test_new_features.py
```

**预期输出**:
```
============================================================
🧪 新功能测试
============================================================

1️⃣ 测试实时监控服务...
   ✓ 监控器已创建
   ✓ 当前指标：CPU xx%
   ...

2️⃣ 测试优化命令生成...
   ✓ 生成优化计划：系统性能优化方案
   ...

3️⃣ 测试性能基线...
   ✓ 基线已保存：...\baseline_xxx.json
   ...

============================================================
✅ 所有新功能测试通过！
============================================================
```

---

## 📞 获取支持

如果以上步骤无法解决问题：

1. **查看日志**: `backend\logs\app.log`
2. **运行检查**: `python check_windows.py`
3. **查看文档**: `WINDOWS_DEPLOYMENT.md`
4. **提供信息**:
   - Windows 版本
   - Python 版本 (`python --version`)
   - 错误日志全文
   - 网络环境（是否有代理）

---

*最后更新：2026-04-19*  
*版本：v2.0 Windows 正式版*
