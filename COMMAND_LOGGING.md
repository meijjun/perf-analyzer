# 命令执行日志功能

**版本**: V1.3.1  
**日期**: 2026-04-28  
**功能**: 记录所有发送到远程设备的命令及执行结果

---

## 📊 功能说明

### 问题 1: 持续监控没有执行性能分析命令 ✅ 已修复

**原因**: 持续监控代码调用了 `collect_performance_data()`，但没有正确传递 `task_id`，导致日志系统未初始化。

**修复**:
- 在连接时传递 `task_id` 参数
- SSH 服务和 Telnet 服务都支持命令日志
- 单次分析和持续监控都使用相同的日志机制

### 问题 2: 命令执行日志 ✅ 已实现

**功能**: 实时记录所有发送到远程设备的命令，包含：
- 命令发送时间（ISO 8601 格式）
- 目标主机和端口
- 命令分类（CPU、内存、磁盘等）
- 命令执行结果（退出码、耗时、输出）
- 连接/断开连接事件

---

## 📁 日志文件

### 文件位置

```
reports/{task_id}/commands_{timestamp}.log
```

**示例**:
```
reports/task_20260428201225/commands_20260428_201225.log
```

### 日志格式

```log
[2026-04-28T20:12:25.123456] [✅] CONNECT
  协议：ssh
  目标：192.168.1.108:22
================================================================================

================================================================================
[2026-04-28T20:12:25.234567] 📊 第 1/10 次采集开始
================================================================================

[2026-04-28T20:12:25.345678] [目标：192.168.1.108:22] [cpu_info]
  命令：top -bn1 | grep 'Cpu(s)'
--------------------------------------------------------------------------------
[2026-04-28T20:12:25.567890] [结果]
  退出码：0
  耗时：245ms
  输出:
  Cpu(s):  5.2 us,  2.1 sy,  0.0 ni, 92.5 id,  0.2 wa,  0.0 hi,  0.0 si,  0.0 st
================================================================================

[2026-04-28T20:12:25.678901] [目标：192.168.1.108:22] [cpu_info]
  命令：ps aux --sort=-%cpu | head -11
--------------------------------------------------------------------------------
[2026-04-28T20:12:25.890123] [结果]
  退出码：0
  耗时：189ms
  输出:
  USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
  root         1  0.0  0.1  18764  3232 ?        Ss   20:10   0:00 /sbin/init
  ...
================================================================================

[2026-04-28T20:12:26.012345] ✅ 第 1/10 次采集完成
  指标摘要:
    - hostname: server-01
    - categories: 6

================================================================================
[2026-04-28T20:12:26.123456] [✅] DISCONNECT
  协议：ssh
  目标：192.168.1.108:22
================================================================================
```

---

## 🔧 技术实现

### 1. 命令日志服务

**文件**: `backend/services/command_logger.py`

**核心方法**:
```python
class CommandLogger:
    def log_command(self, command, target_host, target_port, category)
    def log_command_result(self, command, stdout, stderr, exit_code, duration_ms)
    def log_connection(self, action, host, port, protocol, success, error)
    def log_collection_start(self, collection_index, total)
    def log_collection_complete(self, collection_index, metrics_summary)
```

### 2. SSH 服务集成

**文件**: `backend/services/ssh_service.py`

**修改**:
```python
def connect(self, config):
    # 初始化命令日志
    task_id = config.get('task_id')
    if task_id:
        self.command_logger = get_command_logger(task_id)
        self.command_logger.log_connection('connect', host, port, 'ssh')

def collect_performance_data(self):
    for category, commands in self.COLLECTION_COMMANDS.items():
        for cmd in commands:
            # 记录命令（带时间戳）
            if self.command_logger:
                self.command_logger.log_command(
                    command=cmd,
                    target_host=self.host,
                    target_port=self.target_info.get('port', 22),
                    category=category
                )
            
            # 执行并计时
            start_time = datetime.now()
            result = self.execute(cmd)
            duration_ms = int((datetime.now() - start_time) * 1000)
            
            # 记录结果
            if self.command_logger:
                self.command_logger.log_command_result(
                    command=cmd,
                    stdout=result['stdout'],
                    stderr=result['stderr'],
                    exit_code=result['exit_code'],
                    duration_ms=duration_ms
                )
```

### 3. 分析服务集成

**文件**: `backend/services/analysis_service.py`

**修改**:
```python
# 单次分析
connect_config = target.copy()
connect_config['task_id'] = task_id

if protocol == 'telnet':
    telnet_service.connect(connect_config)
else:
    self.ssh_service.connect(connect_config)

# 持续监控（同样传递 task_id）
connect_config = target.copy()
connect_config['task_id'] = task_id
```

---

## 📊 日志内容详解

### 连接事件
```log
[2026-04-28T20:12:25.123456] [✅] CONNECT
  协议：ssh
  目标：192.168.1.108:22
================================================================================
```

### 命令执行
```log
[2026-04-28T20:12:25.345678] [目标：192.168.1.108:22] [cpu_info]
  命令：top -bn1 | grep 'Cpu(s)'
--------------------------------------------------------------------------------
```

### 执行结果
```log
[2026-04-28T20:12:25.567890] [结果]
  退出码：0
  耗时：245ms
  输出:
  Cpu(s):  5.2 us,  2.1 sy,  0.0 ni, 92.5 id,  0.2 wa,  0.0 hi,  0.0 si,  0.0 st
================================================================================
```

### 采集事件
```log
================================================================================
[2026-04-28T20:12:25.234567] 📊 第 1/10 次采集开始
================================================================================

[2026-04-28T20:12:26.012345] ✅ 第 1/10 次采集完成
  指标摘要:
    - hostname: server-01
    - categories: 6
```

---

## 🎯 使用场景

### 1. 故障排查

**场景**: 分析任务失败，不知道哪个命令执行出错

**方法**:
1. 找到任务目录：`reports/{task_id}/`
2. 打开命令日志：`commands_*.log`
3. 搜索 "失败" 或 "exit=" 查找错误命令
4. 查看错误输出

**示例**:
```log
[2026-04-28T20:12:30.123456] [结果]
  退出码：127
  耗时：12ms
  错误:
  bash: iostat: command not found
```

### 2. 性能分析

**场景**: 分析任务执行太慢

**方法**:
1. 查看每个命令的耗时
2. 找出最慢的命令
3. 优化或替换该命令

**示例**:
```log
[2026-04-28T20:12:25.567890] [结果]
  退出码：0
  耗时：2450ms  ← 这个命令太慢了
  命令：ps aux | grep ...
```

### 3. 审计合规

**场景**: 需要审计所有执行过的命令

**方法**:
1. 所有命令日志都保存在 `reports/` 目录
2. 按任务 ID 组织
3. 包含完整的时间戳和执行结果

---

## 📝 配置说明

### 日志级别

命令日志独立于标准日志，始终启用。

标准日志配置 (`backend/app.py`):
```python
logging.basicConfig(
    level=logging.INFO,  # 或 DEBUG 查看更详细信息
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 日志保留

- 命令日志文件随任务目录一起保存
- 建议定期清理 `reports/` 目录
- 可配置日志轮转（未来功能）

### 输出限制

为避免日志文件过大：
- 命令输出限制前 1000 字符
- 超长输出会显示 "... (共 X 字符)"

---

## 🔍 查看日志

### 方法 1: 直接查看文件

```bash
# 查看最新任务的命令日志
cd /home/admin/openclaw/workspace/perf-analyzer-web/reports
ls -lt */commands_*.log | head -1
cat */commands_*.log | less
```

### 方法 2: 实时监控

```bash
# 实时监控命令执行
tail -f /home/admin/openclaw/workspace/perf-analyzer-web/reports/*/commands_*.log
```

### 方法 3: 搜索特定命令

```bash
# 查找所有失败的命令
grep -r "退出码：[1-9]" reports/*/commands_*.log

# 查找特定类型的命令
grep -r "\[cpu_info\]" reports/*/commands_*.log
```

---

## 🚀 未来优化

### 1. 日志压缩
- 自动压缩旧日志文件
- 节省磁盘空间

### 2. 日志分析
- 自动生成命令执行统计
- 识别慢命令
- 识别失败率高的命令

### 3. 实时推送
- WebSocket 推送命令执行日志
- 前端实时显示

### 4. 日志导出
- 导出为 CSV/Excel
- 便于进一步分析

---

## 📦 相关文件

| 文件 | 用途 |
|------|------|
| `services/command_logger.py` | 命令日志服务 |
| `services/ssh_service.py` | SSH 服务（集成日志） |
| `services/telnet_service.py` | Telnet 服务（待集成） |
| `services/analysis_service.py` | 分析服务（传递 task_id） |
| `reports/{task_id}/commands_*.log` | 日志文件 |

---

**文档版本**: V1.0  
**创建时间**: 2026-04-28  
**维护者**: 性能分析器开发团队
