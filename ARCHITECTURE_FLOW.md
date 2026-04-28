# 远程监控分析完整执行流程

**版本**: V1.2  
**更新时间**: 2026-04-28  
**文档**: 远程性能分析系统架构与执行流程

---

## 📊 系统架构总览

```
┌─────────────────────────────────────────────────────────────┐
│                     前端界面 (Vue 3 + Element Plus)          │
│  http://localhost:5000/                                     │
│  - 设备管理                                                  │
│  - 模型选择 (阿里云/DeepSeek/智谱/华为云)                    │
│  - 开始分析按钮                                              │
│  - 进度显示                                                  │
│  - 报告查看                                                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    Flask 后端 (app.py)                       │
│  API 路由：                                                  │
│  - POST /api/analyze - 启动分析任务                          │
│  - GET /api/tasks/<id> - 查询任务状态                        │
│  - GET /api/reports - 获取报告列表                           │
│  - GET /api/settings - 获取系统设置                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    服务层 (Services)                         │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ AnalysisService │→ │ SSHService   │  │ TelnetService│   │
│  │ (分析协调器)    │  │ (SSH 连接)    │  │ (Telnet 连接) │   │
│  └────────┬────────┘  └──────────────┘  └──────────────┘   │
│           ↓                                                  │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────┐   │
│  │ LLMService      │  │ KnowledgeBase│  │ SettingsSvc  │   │
│  │ (大模型调用)    │  │ (知识库)     │  │ (系统设置)   │   │
│  └─────────────────┘  └──────────────┘  └──────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                    远程设备层                                │
│  SSH/Telnet 协议连接 Linux 服务器                            │
│  - 192.168.1.108:23 (测试设备)                              │
│  - 其他用户配置的设备                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 完整执行流程（8 个步骤）

### 步骤 1: 用户发起分析请求

**前端操作**:
1. 用户在首页左侧选择目标设备
2. 选择大模型提供商（阿里云/DeepSeek/智谱/华为云）
3. 选择具体模型
4. 点击"开始分析"按钮

**前端代码**:
```javascript
// index.html
const startAnalysis = async () => {
    const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            target_id: selectedTarget.value.id,
            provider: selectedProvider.value,
            model: selectedModel.value
        })
    })
    const data = await res.json()
    if (data.success) {
        pollTaskStatus(data.task_id)  // 轮询任务状态
    }
}
```

**API 请求**:
```http
POST /api/analyze
Content-Type: application/json

{
    "target_id": "20260428171044",
    "provider": "custom",
    "model": "multimodal-latest"
}
```

---

### 步骤 2: 后端创建分析任务

**后端处理** (`app.py`):
```python
@app.route('/api/analyze', methods=['POST'])
def start_analysis():
    # 1. 创建任务 ID
    task_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 2. 初始化任务状态
    running_tasks[task_id] = {
        'status': 'pending',
        'progress': 0,
        'current_step': '准备中',
        'created_at': datetime.now().isoformat()
    }
    
    # 3. 启动异步线程执行分析
    thread = threading.Thread(
        target=analysis_service.run_analysis,
        args=(target_id, provider, model, task_id, running_tasks)
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'success': True,
        'task_id': task_id,
        'message': '分析任务已启动'
    })
```

**输出**:
```json
{
    "success": true,
    "task_id": "task_20260428193000",
    "message": "分析任务已启动"
}
```

---

### 步骤 3: 加载目标设备配置

**分析服务** (`analysis_service.py`):
```python
def run_analysis(self, target_id, provider, model, task_id, running_tasks):
    # 1. 加载配置文件
    config_manager = ConfigManager('../config/config.yaml')
    targets = config_manager.get_targets()
    
    # 2. 查找目标设备
    target = next((t for t in targets if t.get('id') == target_id), None)
    
    # target 示例:
    # {
    #     "id": "20260428171044",
    #     "name": "测试设备",
    #     "host": "192.168.1.108",
    #     "port": 23,
    #     "protocol": "telnet",
    #     "username": "admin",
    #     "auth": "password",
    #     "password": "admin123"
    # }
    
    # 3. 更新任务状态
    self._update_task(running_tasks, task_id, {
        'progress': 20,
        'current_step': f"连接 {target.get('host')}..."
    })
```

**配置文件** (`config.yaml`):
```yaml
targets:
  - id: "20260428171044"
    name: "测试设备"
    host: "192.168.1.108"
    port: 23
    protocol: telnet
    username: admin
    auth: password
    password: admin123
```

---

### 步骤 4: 建立远程连接（SSH/Telnet）

**根据协议选择连接方式**:

#### 方案 A: Telnet 连接
```python
if protocol == 'telnet':
    telnet_service = TelnetService()
    
    # 1. 建立连接
    if not telnet_service.connect(target):
        # 连接失败处理
        return
    
    # 2. 登录
    telnet_service.login(
        username=target['username'],
        password=target.get('password')
    )
```

**Telnet 服务** (`telnet_service.py`):
```python
def connect(self, target):
    import telnetlib
    self.client = telnetlib.Telnet(
        target['host'],
        target['port'],
        timeout=10
    )
    return True

def login(self, username, password):
    # 读取登录提示
    self.client.read_until(b"login: ")
    self.client.write(username.encode() + b"\n")
    
    if password:
        self.client.read_until(b"Password: ")
        self.client.write(password.encode() + b"\n")
```

#### 方案 B: SSH 连接
```python
else:  # SSH
    if not self.ssh_service.connect(target):
        return
    
    # SSH 连接细节
    self.client = paramiko.SSHClient()
    self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    if target['auth'] == 'password':
        self.client.connect(
            hostname=target['host'],
            port=target['port'],
            username=target['username'],
            password=target.get('password')
        )
    else:  # 密钥认证
        self.client.connect(
            hostname=target['host'],
            port=target['port'],
            username=target['username'],
            key_filename=target.get('key_path')
        )
```

---

### 步骤 5: 采集性能数据

**采集命令列表**:
```python
commands = [
    # CPU
    "top -bn1 | head -20",
    "uptime",
    
    # 内存
    "free -m",
    
    # 磁盘
    "df -h",
    "iostat -x 1 2",
    
    # 网络
    "cat /proc/net/dev",
    "netstat -an | head -30",
    
    # 进程
    "ps aux --sort=-%cpu | head -20",
    
    # 内核消息
    "dmesg | tail -50"
]
```

**采集过程**:
```python
def collect_performance_data(self):
    perf_data = {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'commands': {}
    }
    
    for cmd in commands:
        # 执行命令
        stdin, stdout, stderr = self.client.exec_command(cmd)
        output = stdout.read().decode('utf-8')
        error = stderr.read().decode('utf-8')
        
        # 保存结果
        perf_data['commands'][cmd] = {
            'output': output,
            'error': error,
            'exit_code': stdout.channel.recv_exit_status()
        }
    
    return perf_data
```

**采集的数据示例**:
```
=== top -bn1 | head -20 ===
top - 19:30:00 up 3 days,  2:15,  1 user,  load average: 0.52, 0.58, 0.54
Tasks: 149 total,   1 running, 147 sleeping,   0 stopped,   1 zombie
%Cpu(s):  5.2 us,  2.1 sy,  0.0 ni, 92.5 id,  0.2 wa,  0.0 hi,  0.0 si,  0.0 st
MiB Mem :   7266.7 total,   1541.6 free,   3315.3 used,   2409.7 buff/cache

=== free -m ===
              total        used        free      shared  buff/cache   available
Mem:           7266        3315        1541          98        2409        3567
Swap:          8192           1        8191

=== df -h ===
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   32G   16G  67% /
```

---

### 步骤 6: 解析性能指标

**指标提取** (`analysis_service.py`):
```python
def _extract_metrics(self, perf_data):
    metrics = {}
    
    # 1. CPU 使用率
    cpu_output = perf_data['commands']['top -bn1 | head -20']['output']
    cpu_match = re.search(r'Cpu\(s\):.*?(\d+\.?\d*)% id', cpu_output)
    if cpu_match:
        idle = float(cpu_match.group(1))
        metrics['cpu_usage'] = round(100 - idle, 1)
    
    # 2. 内存使用率
    mem_output = perf_data['commands']['free -m']['output']
    mem_lines = mem_output.strip().split('\n')
    if len(mem_lines) > 1:
        parts = mem_lines[1].split()
        total = float(parts[1])
        used = float(parts[2])
        metrics['memory_usage'] = round((used / total) * 100, 1)
    
    # 3. 磁盘使用率
    disk_output = perf_data['commands']['df -h']['output']
    disk_match = re.search(r'/dev/sda1.*?(\d+)%', disk_output)
    if disk_match:
        metrics['disk_usage'] = int(disk_match.group(1))
    
    # 4. 系统负载
    load_match = re.search(r'load average: ([\d.]+)', cpu_output)
    if load_match:
        metrics['load_1min'] = float(load_match.group(1))
    
    return metrics
```

**提取的指标**:
```json
{
    "cpu_usage": 7.5,
    "memory_usage": 45.6,
    "disk_usage": 67,
    "load_1min": 0.52
}
```

---

### 步骤 7: 知识库识别瓶颈

**知识库服务** (`knowledge_base.py`):
```python
def identify_bottlenecks(self, metrics):
    bottlenecks = []
    
    # CPU 瓶颈检测
    if metrics.get('cpu_usage', 0) > 80:
        bottlenecks.append({
            'type': 'cpu',
            'severity': 'critical' if metrics['cpu_usage'] > 90 else 'warning',
            'description': f"CPU 使用率过高 ({metrics['cpu_usage']}%)",
            'suggestion': '检查高 CPU 占用进程，考虑优化或扩容'
        })
    
    # 内存瓶颈检测
    if metrics.get('memory_usage', 0) > 85:
        bottlenecks.append({
            'type': 'memory',
            'severity': 'critical' if metrics['memory_usage'] > 95 else 'warning',
            'description': f"内存使用率过高 ({metrics['memory_usage']}%)",
            'suggestion': '检查内存泄漏，考虑增加内存或优化应用'
        })
    
    # 磁盘瓶颈检测
    if metrics.get('disk_usage', 0) > 80:
        bottlenecks.append({
            'type': 'disk',
            'severity': 'warning',
            'description': f"磁盘使用率过高 ({metrics['disk_usage']}%)",
            'suggestion': '清理无用文件，考虑扩容磁盘'
        })
    
    return bottlenecks
```

**识别结果示例**:
```json
[
    {
        "type": "disk",
        "severity": "warning",
        "description": "磁盘使用率过高 (67%)",
        "suggestion": "清理无用文件，考虑扩容磁盘"
    }
]
```

---

### 步骤 8: 调用大模型分析

**准备提示词**:
```python
def generate_analysis_prompt(self, metrics, bottlenecks, raw_data):
    prompt = f"""你是一个 Linux 性能分析专家。请分析以下性能数据：

## 性能指标
- CPU 使用率：{metrics.get('cpu_usage')}%
- 内存使用率：{metrics.get('memory_usage')}%
- 磁盘使用率：{metrics.get('disk_usage')}%
- 系统负载：{metrics.get('load_1min')}

## 识别的瓶颈
{json.dumps(bottlenecks, indent=2, ensure_ascii=False)}

## 原始数据
{raw_data}

## 要求
1. 分析系统性能状况
2. 识别主要瓶颈和原因
3. 提供具体的优化建议
4. 给出优化命令示例

请使用 Markdown 格式输出分析报告。
"""
    return prompt
```

**调用大模型** (`llm_service.py`):
```python
def analyze(self, provider, model, prompt):
    # 加载配置
    config = self.config_manager.get_llm_config()
    provider_config = config.get(provider, {})
    
    if provider == 'custom':  # 华为云
        api_url = provider_config.get('api_url')
        api_key = provider_config.get('api_key')
        
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}'
        }
        
        payload = {
            'model': model,
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 16000
        }
        
        response = requests.post(api_url, json=payload, headers=headers)
        result = response.json()
        
        return {
            'success': True,
            'content': result['choices'][0]['message']['content']
        }
    
    # 其他提供商（阿里云/DeepSeek/智谱）类似处理
```

**大模型返回**:
```markdown
# Linux 性能分析报告

## 总体评估
系统整体运行正常，磁盘使用率需要关注。

## 详细分析

### 1. CPU 使用率：7.5% ✅
- 状态：正常
- 说明：CPU 资源充足

### 2. 内存使用率：45.6% ✅
- 状态：正常
- 说明：内存使用合理

### 3. 磁盘使用率：67% ⚠️
- 状态：需要关注
- 说明：使用率较高，建议清理

## 优化建议

### 1. 磁盘清理
```bash
# 清理 apt 缓存
sudo apt-get clean

# 查找大文件
sudo find / -type f -size +100M

# 清理日志
sudo journalctl --vacuum-time=7d
```

### 2. 监控建议
- 部署磁盘空间监控
- 设置 80% 告警阈值
```
```

---

## 📁 数据流与文件保存

### 保存的文件

**1. 分析报告** (`reports/{task_id}.md`):
```
reports/task_20260428193000.md
- 大模型生成的分析报告
- Markdown 格式
- 包含优化建议
```

**2. 指标数据** (`reports/{task_id}_data.json`):
```json
{
    "perf_data": {...},      // 原始采集数据
    "metrics": {...},         // 提取的指标
    "bottlenecks": [...],     // 识别的瓶颈
    "target": {...},          // 目标设备信息
    "provider": "custom",
    "model": "multimodal-latest"
}
```

**3. 原始数据** (`reports/{task_id}_raw.txt`):
```
=== 性能分析原始数据 ===
任务 ID: task_20260428193000
时间：2026-04-28T19:30:00
目标设备：192.168.1.108:23
协议：telnet
大模型：custom/multimodal-latest

=== 性能指标 ===
{...}

=== 识别的瓶颈 ===
- [warning] 磁盘使用率过高 (67%)

=== 原始采集数据 ===
top -bn1 输出...
free -m 输出...
df -h 输出...
```

---

## 🎯 任务状态轮询

**前端轮询** (每 2 秒):
```javascript
const pollTaskStatus = async (taskId) => {
    const poll = async () => {
        const res = await fetch(`/api/tasks/${taskId}`)
        const data = await res.json()
        
        if (data.success) {
            const task = data.data
            taskProgress.value = task.progress  // 0-100
            currentStep.value = task.current_step
            
            if (task.status === 'completed') {
                // 分析完成
                loadReports()  // 刷新报告列表
            } else if (task.status === 'failed') {
                // 分析失败
                ElMessage.error(task.error)
            } else {
                // 继续轮询
                setTimeout(poll, 2000)
            }
        }
    }
    poll()
}
```

**任务状态变化**:
```
pending (0%) → running (20%) → 连接中 (30%) → 采集中 (40%) → 
解析中 (50%) → 大模型分析中 (60%) → 生成报告 (80%) → completed (100%)
```

---

## ⚙️ 系统设置影响

**设置文件** (`data/settings.json`):
```json
{
    "collection": {
        "duration_minutes": 10,      // 采集时长
        "max_collections": 10,       // 最大采集次数
        "interval_seconds": 60       // 采集间隔
    },
    "analysis": {
        "timeout_seconds": 300,      // 分析超时
        "max_retries": 3             // 最大重试
    }
}
```

**设置影响**:
- `timeout_seconds`: 大模型调用超时时间
- `max_retries`: 失败重试次数
- `duration_minutes`: 未来扩展长时间监控时使用

---

## 📊 完整流程图

```
用户操作
    ↓
[前端] 点击"开始分析"
    ↓
POST /api/analyze
    ↓
[Flask] 创建任务 → task_id
    ↓
[Thread] 异步执行 analysis_service.run_analysis()
    ↓
┌─────────────────────────────────────────┐
│  1. 加载目标配置 (20%)                  │
│     - 从 config.yaml 读取设备信息         │
│  2. 建立连接 (30%)                      │
│     - SSH 或 Telnet                      │
│  3. 采集性能数据 (30%)                  │
│     - 执行 10+ 个 Linux 命令              │
│     - 保存原始数据                       │
│  4. 解析指标 (40%)                      │
│     - CPU、内存、磁盘、负载              │
│  5. 识别瓶颈 (50%)                      │
│     - 基于知识库规则                     │
│  6. 生成提示词 (50%)                    │
│     - 结合指标 + 瓶颈 + 原始数据          │
│  7. 调用大模型 (60%)                    │
│     - 阿里云/DeepSeek/智谱/华为云        │
│  8. 保存报告 (80%)                      │
│     - .md 报告文件                       │
│     - .json 数据文件                      │
│     - .txt 原始数据                       │
│  9. 完成任务 (100%)                     │
└─────────────────────────────────────────┘
    ↓
[前端] 轮询检测到 completed
    ↓
刷新报告列表
    ↓
用户查看报告
```

---

## 🔧 关键代码位置

| 组件 | 文件 | 关键方法 |
|------|------|----------|
| **前端** | `frontend/templates/index.html` | `startAnalysis()`, `pollTaskStatus()` |
| **API 路由** | `backend/app.py` | `@app.route('/api/analyze')` |
| **分析服务** | `backend/services/analysis_service.py` | `run_analysis()` |
| **SSH 服务** | `backend/services/ssh_service.py` | `connect()`, `collect_performance_data()` |
| **Telnet 服务** | `backend/services/telnet_service.py` | `connect()`, `login()` |
| **大模型服务** | `backend/services/llm_service.py` | `analyze()` |
| **知识库** | `backend/services/knowledge_base.py` | `identify_bottlenecks()`, `generate_analysis_prompt()` |
| **配置管理** | `backend/models/config.py` | `get_targets()` |
| **设置服务** | `backend/services/settings_service.py` | `get_settings()` |

---

## 📝 配置示例

### 添加设备 (config.yaml)
```yaml
targets:
  - id: "device-001"
    name: "生产服务器"
    host: "192.168.1.100"
    port: 22
    protocol: ssh
    username: "root"
    auth: "key"
    key_path: "~/.ssh/id_rsa"
```

### 配置大模型 (config.yaml)
```yaml
llm:
  custom:
    api_url: "https://yfmodelhub.dahuatech.com/v1/"
    api_key: "CodeAgentSharedKey"
    model_name: "multimodal-latest"
    enabled: true
    models:
      - multimodal-latest
    capabilities:
      - chat
      - image_input
      - tool_use
    context_length: 256000
    max_tokens: 16000
```

### 系统设置 (data/settings.json)
```json
{
    "collection": {
        "duration_minutes": 10,
        "max_collections": 10,
        "interval_seconds": 60
    },
    "analysis": {
        "timeout_seconds": 300,
        "max_retries": 3
    }
}
```

---

## 🎯 总结

**核心特点**:
1. **异步执行** - 使用线程池，不阻塞 API 响应
2. **状态追踪** - 实时进度更新，用户可见
3. **多协议支持** - SSH 和 Telnet 自动切换
4. **多模型支持** - 阿里云/DeepSeek/智谱/华为云
5. **知识库增强** - 基于 linux-performance-analyzer Skill
6. **数据持久化** - 报告、指标、原始数据三重保存

**技术栈**:
- 前端：Vue 3 + Element Plus
- 后端：Flask + Python 3
- 协议：Paramiko (SSH) + telnetlib
- AI: 多模型 API 调用
- 知识库：Markdown 规则引擎

**数据流**:
```
用户 → Flask API → AnalysisService → SSH/Telnet → 
Linux 命令 → 指标提取 → 知识库 → 大模型 → 报告生成
```

---

**文档版本**: V1.0  
**创建时间**: 2026-04-28  
**维护者**: 性能分析器开发团队
