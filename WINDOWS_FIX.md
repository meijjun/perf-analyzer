# Windows 运行问题修复

## 问题描述

在 Windows 上运行时出现 `UnicodeEncodeError: 'gbk' codec can't encode character` 错误。

**原因**: Windows 控制台默认使用 GBK 编码，无法正确处理日志中的 emoji 字符。

---

## 解决方案

### 方案 1: 使用 start.bat 启动（推荐）

```cmd
cd perf-analyzer-web
start.bat
```

这个脚本会自动：
- 切换代码页为 UTF-8 (65001)
- 设置环境变量 `PYTHONIOENCODING=utf-8`

### 方案 2: 手动设置环境变量

```cmd
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
cd backend
python app.py
```

### 方案 3: 修改系统默认编码（永久）

1. 打开注册表编辑器 (`regedit`)
2. 导航到：`HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Nls\CodePage`
3. 修改 `ACP` 值为 `65001`
4. 重启电脑

⚠️ **注意**: 修改系统编码可能影响其他程序，谨慎操作。

---

## 快速启动命令

### PowerShell (推荐)
```powershell
$env:PYTHONUTF8=1
$env:PYTHONIOENCODING="utf-8"
cd backend
python app.py
```

### CMD
```cmd
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
cd backend
python app.py
```

---

## 验证修复

启动后应该看到：
```
2026-04-19 22:30:00,000 - __main__ - INFO - Web Performance Analyzer starting...
2026-04-19 22:30:00,001 - __main__ - INFO - Working directory: D:\AI_Project\perf-analyzer-web
 * Serving Flask app 'app'
 * Running on http://127.0.0.1:5000
```

**没有** `UnicodeEncodeError` 错误。

---

## 访问地址

启动成功后，在浏览器访问：
- http://localhost:5000
- http://127.0.0.1:5000

---

## 其他注意事项

1. **日志文件**: 日志会保存在 `logs/app.log`，使用 UTF-8 编码
2. **配置文件**: `config/config.yaml` 使用 UTF-8 编码保存
3. **参考文档**: `docs/` 目录下的 Markdown 文件使用 UTF-8 编码

如果遇到其他编码问题，请确保：
- 使用 UTF-8 编码编辑所有文件
- Python 脚本第一行添加 `# -*- coding: utf-8 -*-`（Python 2 需要）
- 在 PowerShell 中运行 `chcp 65001` 切换代码页

---

## 常见问题

### Q: 为什么日志中看不到 emoji 了？

A: 为了兼容 Windows 控制台，日志消息已改为纯文本。但 Web 界面仍然显示 emoji。

### Q: 可以在 Windows 上正常运行吗？

A: 是的，按照上述方案设置后可以正常运行。已在 Windows 10/11 上测试。

### Q: 使用 PyCharm 等 IDE 可以吗？

A: 可以。在 IDE 中：
1. 打开设置 → 文件编码 → 设置为 UTF-8
2. 运行配置中添加环境变量 `PYTHONUTF8=1`

---

*最后更新：2026-04-19*
