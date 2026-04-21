# Linux Performance Analyzer Skill

> 本目录包含来自 linux-performance-analyzer-1.0.0 Skill 的专业参考文档，为 Web 版性能分析器提供知识库支持。

## 文档索引

| 文档 | 内容 | 用途 |
|------|------|------|
| [cpu.md](cpu.md) | CPU 调优全维度手册 | 上下文切换、NUMA、绑核、perf 火焰图 |
| [memory.md](memory.md) | 内存调优全维度手册 | OOM、Swap、THP、内存泄漏 |
| [disk_io.md](disk_io.md) | 磁盘 I/O 调优手册 | 调度器、预读、fio 测试 |
| [network.md](network.md) | 网络调优全维度手册 | TCP 栈、BBR、高并发 |
| [kernel_params.md](kernel_params.md) | 内核参数速查全表 | sysctl 参数默认值/建议值 |
| [compile_optimization.md](compile_optimization.md) | 编译优化指南 | GCC/Clang/PGO/LTO |
| [case_studies.md](case_studies.md) | 5 大实战案例 | MySQL/Nginx/Java/K8s |

## 分析工作流

```
1️⃣ 采集现场数据 → scripts/collect_snapshot.sh
        ↓
2️⃣ 识别瓶颈类型 → CPU / 内存 / I/O / 网络 / 编译
        ↓
3️⃣ 查阅参考文档 → 对照本目录对应文档
        ↓
4️⃣ 输出标准化报告 → 问题/原因/方案/风险/验证/回滚
        ↓
5️⃣ 实施优化并验证 → 执行命令 → 对比效果
```

## 快速诊断命令

```bash
# 10 步排查法
uptime                    # 负载
free -h                   # 内存
df -h                     # 磁盘
top -bn1 | head -20       # CPU + 进程
vmstat 1 3                # 上下文切换
iostat -xz 1 3            # I/O
ss -s                     # 网络
dmesg | tail -50          # 内核日志
dmesg | grep -i oom       # OOM 事件
```

## 告警阈值

| 指标 | 正常 | 警告 | 严重 |
|------|------|------|------|
| CPU 使用率 | < 60% | > 70% | > 90% |
| 内存可用 | > 30% | < 20% | < 10% |
| Swap 使用率 | 0% | > 10% | > 30% |
| load average | < 核数 | > 核数×1.5 | > 核数×2 |
| 上下文切换/秒 | < 5 万 | > 10 万 | > 50 万 |

---

*来自 linux-performance-analyzer-1.0.0 Skill*
