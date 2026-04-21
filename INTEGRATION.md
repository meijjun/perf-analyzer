# 🔌 Skill 集成文档

## linux-performance-analyzer Skill 集成

### 集成概述

已将 **linux-performance-analyzer-1.0.0** Skill 完整集成到 Web 版性能分析器中，增强了以下能力：

1. **专业知识库** - 7 大领域参考文档
2. **智能瓶颈识别** - 基于规则的性能瓶颈自动识别
3. **标准化报告** - 问题/原因/方案/风险/验证/回滚六要素
4. **快速诊断命令** - 场景化命令速查

---

## 📚 集成的参考文档

| 文档 | 内容 | 用途 |
|------|------|------|
| **cpu.md** | CPU 调优全维度手册 | 上下文切换、NUMA、绑核、perf 火焰图 |
| **memory.md** | 内存调优全维度手册 | OOM、Swap、THP、内存泄漏 |
| **disk_io.md** | 磁盘 I/O 调优手册 | 调度器、预读、fio 测试 |
| **network.md** | 网络调优全维度手册 | TCP 栈、BBR、高并发 |
| **kernel_params.md** | 内核参数速查全表 | sysctl 参数默认值/建议值 |
| **compile_optimization.md** | 编译优化指南 | GCC/Clang/PGO/LTO |
| **case_studies.md** | 5 大实战案例 | MySQL/Nginx/Java/K8s |

---

## 🔍 新增功能

### 1. 参考文档标签页

在 Web 界面新增「📚 参考文档」标签页，提供：

- **文档卡片** - 7 个专业领域文档，按类别着色
- **文档查看** - 在线浏览 Markdown 格式文档
- **快速命令** - 每个文档关联场景化诊断命令

### 2. 智能瓶颈识别

基于 Skill 的规则引擎，自动识别：

| 瓶颈类型 | 识别规则 |
|---------|---------|
| **CPU** | load > 核数×2、CPU > 90%、上下文切换 > 50 万/秒 |
| **内存** | 可用内存 < 10%、Swap > 30%、OOM 事件 |
| **磁盘 I/O** | util > 95%、await > 50ms |
| **网络** | TCP 重传 > 5%、TIME_WAIT > 1 万 |

### 3. 优化建议模板

为每类瓶颈提供标准化优化方案：

```
【问题】观察到的指标数据
【原因】根因推断
【方案】具体优化命令
【风险】副作用和注意事项
【验证】效果验证命令
【回滚】回滚方案
```

### 4. 快速诊断命令

按场景提供 5 组快速命令：

#### CPU 场景
```bash
uptime && cat /proc/loadavg      # 负载概览
mpstat -P ALL 1 3                # CPU 使用率
vmstat 1 5                       # 上下文切换
ps aux --sort=-%cpu | head -10   # 高 CPU 进程
```

#### 内存场景
```bash
free -h                          # 内存状态
cat /proc/meminfo | head -20     # 内存详情
ps aux --sort=-%mem | head -10   # 高内存进程
dmesg | grep -iE 'oom|killed'    # OOM 历史
```

#### 磁盘场景
```bash
df -h                            # 磁盘空间
iostat -xz 1 3                   # I/O 统计
iotop -o -b -n 3 | head -10      # 高 I/O 进程
```

#### 网络场景
```bash
ss -s                            # 连接统计
ss -ant | awk '{print $1}' | sort | uniq -c  # 连接状态
netstat -s | grep -iE 'fail|error|drop'      # 网络错误
```

---

## 📁 集成的文件

### 后端新增
```
backend/services/
└── knowledge_base.py          # 知识库服务（核心）
    ├── KnowledgeBase 类
    ├── 瓶颈识别规则
    ├── 优化建议模板
    └── 文档检索功能
```

### 前端新增
```
frontend/templates/index.html
    ├── 参考文档标签页
    ├── 文档卡片展示
    ├── 文档查看对话框
    └── 快速命令对话框
```

### 参考文档
```
docs/
├── SKILL.md                   # Skill 集成说明
├── cpu.md                     # 来自 Skill
├── memory.md                  # 来自 Skill
├── disk_io.md                 # 来自 Skill
├── network.md                 # 来自 Skill
├── kernel_params.md           # 来自 Skill
├── compile_optimization.md    # 来自 Skill
└── case_studies.md            # 来自 Skill
```

### 采集脚本
```
scripts/
├── collect_snapshot.sh        # 一键系统快照（来自 Skill）
└── perf_monitor.sh            # 持续监控告警（来自 Skill）
```

---

## 🔧 API 接口

### 新增 API

#### 获取参考文档
```http
GET /api/docs/<filename>
```

**响应示例**:
```json
{
  "success": true,
  "data": "# CPU 调优参考手册\n\n## 目录..."
}
```

#### 获取快速命令
```http
GET /api/analysis/quick-commands?scenario=cpu
```

**响应示例**:
```json
{
  "success": true,
  "data": [
    {"desc": "负载概览", "cmd": "uptime && cat /proc/loadavg"},
    {"desc": "CPU 使用率", "cmd": "mpstat -P ALL 1 3"},
    ...
  ]
}
```

---

## 🎯 使用场景

### 场景 1: 系统变慢

1. 选择目标设备
2. 点击「开始分析」
3. 查看 AI 生成的报告（基于 Skill 知识库增强）
4. 参考「📚 参考文档」→「CPU 调优」深入了解

### 场景 2: 内存不足告警

1. 点击「📚 参考文档」→「内存调优」
2. 点击「快速命令」→ 复制内存诊断命令
3. 在目标设备执行命令
4. 根据文档建议优化 swappiness、THP 等参数

### 场景 3: 高并发网络问题

1. 查看历史报告，对比基线
2. 参考「网络调优」文档
3. 应用 TIME_WAIT 优化、连接队列调整等建议

---

## 📊 分析流程对比

### 集成前
```
用户请求 → SSH 连接 → 采集数据 → 大模型分析 → 生成报告
```

### 集成后（增强）
```
用户请求 → SSH 连接 → 采集数据
    ↓
指标提取 → 瓶颈识别（Skill 规则引擎）
    ↓
生成提示词（注入 Skill 知识库）→ 大模型分析
    ↓
标准化报告（六要素） + 参考文档链接
```

**改进点**:
- ✅ 瓶颈识别更准确（基于规则 + AI）
- ✅ 优化建议更专业（来自 Skill 最佳实践）
- ✅ 报告格式更规范（六要素模板）
- ✅ 可追溯参考文档（深入学习）

---

## 🚀 后续优化方向

1. **案例库集成** - 将 case_studies.md 的 5 大案例做成交互式向导
2. **参数修改助手** - 一键生成 sysctl 配置文件
3. **基线对比** - 保存性能基线，自动对比异常
4. **告警通知** - 集成钉钉/企业微信告警
5. **容器专项** - 增强 K8s/Docker 性能分析能力

---

## 📝 版本信息

- **Skill 版本**: linux-performance-analyzer-1.0.0
- **集成日期**: 2026-04-19
- **集成方式**: 知识库 + 规则引擎 + 参考文档
- **文件来源**: /home/admin/openclaw/workspace/linux-performance-analyzer-1.0.0/

---

*集成文档由 Web 版性能分析器生成*
