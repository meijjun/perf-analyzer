# 采集设置集成方案

**版本**: V1.3  
**日期**: 2026-04-28  
**目标**: 将采集时长/次数/间隔设置与现有采集功能整合

---

## 📊 当前状态分析

### 现有采集模式（V1.2）

**特点**: **一次性采集**
```
用户点击"开始分析"
    ↓
连接设备
    ↓
执行 10+ 个命令（top, free, df, etc.）
    ↓
采集完成（约 5-10 秒）
    ↓
AI 分析 → 生成报告
```

**代码位置**: `backend/services/analysis_service.py`
```python
# 一次性采集
perf_data = self.ssh_service.collect_performance_data()
```

**问题**: 
- 设置中的 `duration_minutes`, `max_collections`, `interval_seconds` **未被使用**
- 这些设置是为**持续监控**设计的，但当前系统只做单次分析

---

## 🎯 两种采集模式

### 模式 A: 单次分析（当前模式）

**用途**: 快速诊断，AI 生成优化建议  
**流程**: 连接 → 采集一次 → 分析 → 报告  
**耗时**: 5-10 秒  
**设置影响**: ❌ 不使用采集设置

### 模式 B: 持续监控（新增模式）

**用途**: 长时间性能追踪，趋势分析  
**流程**: 连接 → 循环采集 N 次 → 保存数据 → （可选）分析  
**耗时**: 由设置决定（如 10 分钟）  
**设置影响**: ✅ 使用采集设置

---

## 🔧 集成方案

### 方案 1: 双模式切换（推荐）⭐

**实现**: 在首页添加"采集模式"选择

**UI 设计**:
```
┌─────────────────────────────────────┐
│ 🔍 性能分析                          │
├─────────────────────────────────────┤
│ 采集模式：                          │
│ ○ 单次分析（快速诊断）              │
│ ● 持续监控（性能追踪）              │
│                                     │
│ 采集设置：                          │
│ - 采集时长：10 分钟                  │
│ - 采集次数：10 次                    │
│ - 采集间隔：60 秒                    │
│                                     │
│ 目标设备：[测试设备 ▼]              │
│ 大模型：[Custom/multimodal-latest▼] │
│                                     │
│        [开始分析]                    │
└─────────────────────────────────────┘
```

**后端逻辑**:
```python
@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    data = request.json
    mode = data.get('mode', 'single')  # 'single' or 'continuous'
    
    if mode == 'single':
        # 现有逻辑 - 单次分析
        thread = threading.Thread(
            target=analysis_service.run_analysis,
            args=(target_id, provider, model, task_id, running_tasks)
        )
    else:
        # 新增逻辑 - 持续监控
        settings = settings_service.get_collection_settings()
        thread = threading.Thread(
            target=analysis_service.run_continuous_monitoring,
            args=(target_id, settings, task_id, running_tasks)
        )
    
    thread.start()
```

**新增服务方法**:
```python
# analysis_service.py
def run_continuous_monitoring(self, target_id, settings, task_id, running_tasks):
    """持续监控模式"""
    
    duration_minutes = settings['duration_minutes']
    max_collections = settings['max_collections']
    interval_seconds = settings['interval_seconds']
    
    # 计算实际采集次数
    if duration_minutes > 0:
        calculated_collections = (duration_minutes * 60) // interval_seconds
        max_collections = min(max_collections, calculated_collections)
    
    logger.info(f"[任务 {task_id}] 持续监控 - 时长:{duration_minutes}分钟, "
                f"次数:{max_collections}, 间隔:{interval_seconds}秒")
    
    # 连接设备
    if not self.ssh_service.connect(target):
        return
    
    all_metrics = []
    
    for i in range(max_collections):
        # 更新进度
        progress = int((i / max_collections) * 80)  # 80% 用于采集
        self._update_task(running_tasks, task_id, {
            'progress': progress,
            'current_step': f'第 {i+1}/{max_collections} 次采集'
        })
        
        # 采集数据
        perf_data = self.ssh_service.collect_performance_data()
        metrics = self._extract_metrics(perf_data)
        metrics['collection_index'] = i + 1
        all_metrics.append(metrics)
        
        # 保存中间数据
        self._save_continuous_data(task_id, i, metrics)
        
        # 等待下次采集（最后一次不等待）
        if i < max_collections - 1:
            time.sleep(interval_seconds)
    
    # 断开连接
    self.ssh_service.disconnect()
    
    # 生成趋势报告
    self._generate_trend_report(task_id, all_metrics)
    
    # 完成任务
    self._update_task(running_tasks, task_id, {
        'status': 'completed',
        'progress': 100
    })
```

**输出文件**:
```
reports/
  task_20260428193000/
    ├── metrics.json          # 所有采集的指标（时间序列）
    ├── trend_report.md       # 趋势分析报告
    └── chart_data.csv        # 图表数据（可导入 Excel）
```

---

### 方案 2: 设置仅用于持续监控（简化版）

**实现**: 保持当前单次分析不变，设置仅在选择"持续监控"时生效

**UI**:
```
☐ 启用持续监控
  如果勾选，显示：
  - 采集时长：[10] 分钟
  - 采集次数：[10] 次
  - 采集间隔：[60] 秒
```

**优点**: 
- 不改变现有单次分析流程
- 新增功能独立，风险低

**缺点**:
- 设置页面可能让人困惑（为什么单次分析时不生效）

---

### 方案 3: 设置影响单次分析的采样深度

**实现**: 将设置解释为"采样深度"

**参数映射**:
- `max_collections` → 每个命令重复执行次数（取平均）
- `interval_seconds` → 命令间等待时间
- `duration_minutes` → 忽略（或用于超时控制）

**示例**:
```python
# max_collections = 3
# 每个命令执行 3 次，取平均值

for cmd in commands:
    results = []
    for i in range(max_collections):
        output = execute_command(cmd)
        results.append(parse(output))
        time.sleep(interval_seconds)
    
    # 取平均
    metrics[cmd] = average(results)
```

**优点**:
- 设置对所有分析生效
- 提高数据准确性

**缺点**:
- 分析时间变长（用户可能觉得慢）
- 与设置名称的直观理解不符

---

## 💡 推荐实施方案

**采用方案 1: 双模式切换**

**理由**:
1. **清晰明确** - 用户知道选择的是什么模式
2. **向后兼容** - 现有单次分析不受影响
3. **灵活扩展** - 未来可以添加更多模式
4. **设置合理** - 设置只在对应模式下生效

---

## 📋 实施步骤

### 步骤 1: 修改前端 UI

**文件**: `frontend/templates/index.html`

**新增字段**:
```javascript
const analysisMode = ref('single');  // 'single' or 'continuous'
```

**新增 UI**:
```html
<div class="form-group">
    <label>采集模式</label>
    <el-radio-group v-model="analysisMode">
        <el-radio label="single">单次分析（快速诊断）</el-radio>
        <el-radio label="continuous">持续监控（性能追踪）</el-radio>
    </el-radio-group>
</div>

<div v-if="analysisMode === 'continuous'" class="form-group">
    <el-alert 
        title="持续监控模式" 
        type="info" 
        :closable="false"
        show-icon>
        将采集 {{ settings.collection.max_collections }} 次数据，
        间隔 {{ settings.collection.interval_seconds }} 秒，
        预计耗时 {{ (settings.collection.max_collections * settings.collection.interval_seconds / 60).toFixed(1) }} 分钟
    </el-alert>
</div>
```

**修改 API 调用**:
```javascript
const startAnalysis = async () => {
    const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            target_id: selectedTarget.value.id,
            provider: selectedProvider.value,
            model: selectedModel.value,
            mode: analysisMode.value  // 新增：模式选择
        })
    })
    // ...
}
```

---

### 步骤 2: 修改后端 API

**文件**: `backend/app.py`

```python
@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    data = request.json
    target_id = data.get('target_id')
    provider = data.get('provider')
    model = data.get('model')
    mode = data.get('mode', 'single')  # 新增：模式参数
    
    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 初始化任务
    running_tasks[task_id] = {
        'status': 'pending',
        'progress': 0,
        'current_step': '准备中',
        'mode': mode  # 记录模式
    }
    
    # 根据模式选择执行方法
    if mode == 'single':
        thread = threading.Thread(
            target=analysis_service.run_analysis,
            args=(target_id, provider, model, task_id, running_tasks)
        )
    else:  # continuous
        settings = settings_service.get_collection_settings()
        thread = threading.Thread(
            target=analysis_service.run_continuous_monitoring,
            args=(target_id, settings, task_id, running_tasks)
        )
    
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'mode': mode,
        'message': f'{"持续监控" if mode == "continuous" else "分析"}任务已启动'
    })
```

---

### 步骤 3: 实现持续监控服务

**文件**: `backend/services/analysis_service.py`

```python
import time
from datetime import datetime

def run_continuous_monitoring(self, target_id, settings, task_id, running_tasks):
    """持续监控模式"""
    try:
        logger.info(f"[任务 {task_id}] 开始持续监控")
        
        # 1. 加载目标配置
        from models.config import ConfigManager
        config_manager = ConfigManager('../config/config.yaml')
        targets = config_manager.get_targets()
        target = next((t for t in targets if t.get('id') == target_id), None)
        
        if not target:
            self._update_task(running_tasks, task_id, {
                'status': 'failed',
                'error': '目标设备不存在'
            })
            return
        
        # 2. 解析设置
        duration_minutes = settings['duration_minutes']
        max_collections = settings['max_collections']
        interval_seconds = settings['interval_seconds']
        
        # 根据时长计算最大采集次数
        if duration_minutes > 0:
            calculated = (duration_minutes * 60) // interval_seconds
            max_collections = min(max_collections, calculated)
        
        logger.info(f"[任务 {task_id}] 监控参数 - 次数:{max_collections}, "
                    f"间隔:{interval_seconds}s, 预计:{max_collections*interval_seconds/60:.1f}分钟")
        
        # 3. 建立连接
        self._update_task(running_tasks, task_id, {
            'progress': 10,
            'current_step': f"连接 {target.get('host')}..."
        })
        
        if not self.ssh_service.connect(target):
            self._update_task(running_tasks, task_id, {
                'status': 'failed',
                'error': 'SSH 连接失败'
            })
            return
        
        # 4. 循环采集
        all_metrics = []
        start_time = datetime.now()
        
        for i in range(max_collections):
            if self._should_stop(running_tasks, task_id):
                logger.info(f"[任务 {task_id}] 监控被用户中断")
                break
            
            # 更新进度
            progress = 10 + int((i / max_collections) * 80)
            self._update_task(running_tasks, task_id, {
                'progress': progress,
                'current_step': f'第 {i+1}/{max_collections} 次采集'
            })
            
            # 采集数据
            perf_data = self.ssh_service.collect_performance_data()
            metrics = self._extract_metrics(perf_data)
            metrics['timestamp'] = datetime.now().isoformat()
            metrics['collection_index'] = i + 1
            all_metrics.append(metrics)
            
            # 保存中间数据
            self._save_continuous_data(task_id, i, metrics)
            
            logger.info(f"[任务 {task_id}] 第 {i+1} 次采集完成 - "
                       f"CPU:{metrics.get('cpu_usage')}% "
                       f"内存:{metrics.get('memory_usage')}%")
            
            # 等待（最后一次不等待）
            if i < max_collections - 1:
                time.sleep(interval_seconds)
        
        # 5. 断开连接
        self.ssh_service.disconnect()
        
        # 6. 生成趋势报告
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        self._update_task(running_tasks, task_id, {
            'progress': 90,
            'current_step': '生成趋势报告...'
        })
        
        report_path = self._generate_trend_report(task_id, all_metrics, duration)
        
        # 7. 完成任务
        self._update_task(running_tasks, task_id, {
            'status': 'completed',
            'progress': 100,
            'current_step': '完成',
            'result': {
                'collections': len(all_metrics),
                'duration_seconds': duration,
                'report_path': report_path
            }
        })
        
        logger.info(f"[任务 {task_id}] 持续监控完成 - 采集{len(all_metrics)}次，耗时{duration:.1f}秒")
        
    except Exception as e:
        logger.error(f"[任务 {task_id}] 持续监控失败：{e}")
        self._update_task(running_tasks, task_id, {
            'status': 'failed',
            'error': str(e)
        })

def _should_stop(self, running_tasks, task_id):
    """检查是否应该停止监控"""
    task = running_tasks.get(task_id, {})
    return task.get('status') == 'stopped'

def _save_continuous_data(self, task_id, index, metrics):
    """保存持续监控数据"""
    import json
    import os
    
    # 创建任务目录
    task_dir = f"../reports/{task_id}"
    os.makedirs(task_dir, exist_ok=True)
    
    # 保存为 JSON Lines 格式
    jsonl_path = f"{task_dir}/metrics.jsonl"
    with open(jsonl_path, 'a', encoding='utf-8') as f:
        f.write(json.dumps(metrics, ensure_ascii=False) + '\n')
    
    # 同时保存最新数据到单独文件（用于实时查看）
    latest_path = f"{task_dir}/latest.json"
    with open(latest_path, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2, ensure_ascii=False)

def _generate_trend_report(self, task_id, all_metrics, duration_seconds):
    """生成趋势分析报告"""
    import os
    
    report_path = f"../reports/{task_id}/trend_report.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    # 计算统计信息
    if not all_metrics:
        return None
    
    cpu_values = [m.get('cpu_usage', 0) for m in all_metrics]
    mem_values = [m.get('memory_usage', 0) for m in all_metrics]
    
    report = f"""# 性能监控趋势报告

**任务 ID**: {task_id}  
**监控时长**: {duration_seconds:.1f} 秒  
**采集次数**: {len(all_metrics)} 次  
**采集间隔**: {duration_seconds/len(all_metrics):.1f} 秒

## 统计摘要

### CPU 使用率
- 平均值：{sum(cpu_values)/len(cpu_values):.1f}%
- 最大值：{max(cpu_values):.1f}%
- 最小值：{min(cpu_values):.1f}%

### 内存使用率
- 平均值：{sum(mem_values)/len(mem_values):.1f}%
- 最大值：{max(mem_values):.1f}%
- 最小值：{min(mem_values):.1f}%

## 趋势分析

（此处可以添加趋势描述，如"CPU 使用率呈上升趋势"等）

## 原始数据

数据文件：
- `metrics.jsonl` - 所有采集数据（JSON Lines 格式）
- `latest.json` - 最后一次采集数据

## 建议

（根据趋势给出建议）
"""
    
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    # 同时生成 CSV 格式（方便导入 Excel）
    csv_path = f"../reports/{task_id}/chart_data.csv"
    import csv
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['时间戳', '采集次序', 'CPU 使用率', '内存使用率', '磁盘使用率', '系统负载'])
        
        for m in all_metrics:
            writer.writerow([
                m.get('timestamp', ''),
                m.get('collection_index', 0),
                m.get('cpu_usage', 0),
                m.get('memory_usage', 0),
                m.get('disk_usage', 0),
                m.get('load_1min', 0)
            ])
    
    logger.info(f"[任务 {task_id}] 趋势报告已生成：{report_path}")
    return report_path
```

---

### 步骤 4: 修改任务状态 API

**文件**: `backend/app.py`

```python
@app.route('/api/tasks/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态（支持持续监控）"""
    if task_id not in running_tasks:
        return jsonify({
            'success': False,
            'error': '任务不存在'
        }), 404
    
    task = running_tasks[task_id]
    
    # 如果是持续监控模式，附加额外信息
    if task.get('mode') == 'continuous' and task.get('status') == 'running':
        # 可以从正在采集的数据中获取实时指标
        task_dir = f"../reports/{task_id}"
        latest_path = f"{task_dir}/latest.json"
        
        if os.path.exists(latest_path):
            import json
            with open(latest_path, 'r', encoding='utf-8') as f:
                latest_metrics = json.load(f)
            task['latest_metrics'] = latest_metrics
    
    return jsonify({
        'success': True,
        'data': task
    })
```

---

## 📊 设置参数使用总结

| 参数 | 单次分析模式 | 持续监控模式 |
|------|-------------|-------------|
| `duration_minutes` | ❌ 不使用 | ✅ 控制总时长 |
| `max_collections` | ❌ 不使用 | ✅ 控制采集次数 |
| `interval_seconds` | ❌ 不使用 | ✅ 控制采集间隔 |
| `timeout_seconds` | ✅ 分析超时 | ✅ 分析超时 |
| `max_retries` | ✅ 重试次数 | ✅ 重试次数 |

---

## 🎯 用户体验优化

### 1. 进度显示优化

**单次分析**:
```
[=====>          ] 45% - 调用大模型分析...
```

**持续监控**:
```
[=====>          ] 45% - 第 5/10 次采集
预计剩余：3 分钟
```

### 2. 结果展示优化

**单次分析**:
- 显示 AI 生成的优化建议
- 提供报告下载

**持续监控**:
- 显示趋势图表（CPU/内存随时间变化）
- 提供 CSV 数据导出
- 可选：生成 AI 分析报告

### 3. 中断支持

**新增功能**: 允许用户中断持续监控

```javascript
// 前端
const stopMonitoring = async (taskId) => {
    await fetch(`/api/tasks/${taskId}/stop`, { method: 'POST' })
}
```

```python
# 后端
@app.route('/api/tasks/<task_id>/stop', methods=['POST'])
def stop_task(task_id):
    if task_id in running_tasks:
        running_tasks[task_id]['status'] = 'stopped'
    return jsonify({'success': True})
```

---

## 📝 总结

### 当前状态
- ✅ 设置页面已创建
- ✅ 设置已保存到 `data/settings.json`
- ❌ 设置未在实际采集流程中使用

### 需要实现
1. ✅ 前端添加模式选择 UI
2. ✅ 后端 API 支持 mode 参数
3. ✅ 实现 `run_continuous_monitoring()` 方法
4. ✅ 趋势报告生成
5. ✅ 数据持久化（JSONL/CSV）
6. ✅ 中断支持

### 实施优先级
1. **高**: 双模式切换基础功能
2. **中**: 趋势报告生成
3. **低**: 实时图表展示

---

**文档版本**: V1.0  
**创建时间**: 2026-04-28  
**下一步**: 实施方案 1（双模式切换）
