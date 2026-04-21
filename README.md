# 🚀 Web 版 Linux 性能分析器

基于 Web 的智能化 Linux 性能分析平台，支持多大大模型切换分析。

## ✨ 功能特性

- 🌐 **Web 界面** - 无需安装客户端，浏览器即可访问
- 🤖 **多模型支持** - 阿里云通义千问、DeepSeek、智谱 AI、百度文心一言
- 🔄 **模型切换** - 一键切换不同大模型进行分析对比
- 📚 **专业知识库** - 集成 linux-performance-analyzer Skill，包含 7 大领域参考文档
- 📊 **实时进度** - 可视化展示分析进度和步骤
- 📄 **报告管理** - 自动保存历史报告，随时查看
- 🎯 **设备管理** - 支持配置多个目标设备
- 🔐 **安全连接** - SSH 密钥/密码认证
- 🛠️ **快速命令** - 场景化快速诊断命令，一键复制

## 🏗️ 项目结构

```
perf-analyzer-web/
├── backend/
│   ├── app.py              # Flask 主程序
│   ├── services/
│   │   ├── llm_service.py   # 大模型服务
│   │   ├── ssh_service.py   # SSH 连接服务
│   │   └── analysis_service.py  # 分析协调服务
│   └── models/
│       └── config.py        # 配置管理
├── frontend/
│   └── templates/
│       └── index.html       # 主页面
├── config/
│   └── config.yaml          # 配置文件
├── requirements.txt
└── README.md
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd perf-analyzer-web
pip install -r requirements.txt
```

### 2. 配置大模型 API Key

编辑 `config/config.yaml`，填入您的 API Key：

```yaml
llm:
  aliyun:
    api_key: "sk-xxx"  # 阿里云
  deepseek:
    api_key: "xxx"     # DeepSeek
  zhipu:
    api_key: "xxx"     # 智谱 AI
```

### 3. 启动服务

```bash
cd backend
python app.py
```

### 4. 访问界面

打开浏览器访问：http://localhost:5000

## 📋 使用指南

### 添加目标设备

1. 点击"添加设备"按钮
2. 填写设备信息（名称、IP、端口、认证方式）
3. 点击"添加"保存

### 开始性能分析

1. 在左侧选择目标设备
2. 选择大模型提供商和具体模型
3. 点击"开始分析"
4. 等待分析完成，查看报告

### 切换大模型

- **阿里云通义千问**: qwen-turbo, qwen-plus, qwen-max
- **DeepSeek**: deepseek-chat, deepseek-coder
- **智谱 AI**: glm-4, glm-3-turbo, glm-4-flash
- **百度文心一言**: ernie-bot-4, ernie-bot

### 查看历史报告

点击"历史报告"标签页，可以：
- 查看之前的分析报告
- 重新查看报告内容
- 下载报告文件

## 🔑 获取 API Key

### 阿里云通义千问
1. 访问 https://dashscope.console.aliyun.com/
2. 登录/注册阿里云账号
3. 创建 API Key

### DeepSeek
1. 访问 https://platform.deepseek.com/
2. 注册/登录账号
3. 在控制台获取 API Key

### 智谱 AI
1. 访问 https://open.bigmodel.cn/
2. 注册/登录账号
3. 创建 API Key

### 百度文心一言
1. 访问 https://console.bce.baidu.com/
2. 创建应用获取 API Key 和 Secret Key

## 📊 分析流程

```
1. 连接设备 (SSH/Telnet)
   ↓
2. 收集性能数据
   - CPU 信息
   - 内存信息
   - 磁盘 I/O
   - 网络信息
   - 进程信息
   ↓
3. 调用大模型分析
   ↓
4. 生成标准化报告
   - 问题识别
   - 原因分析
   - 优化建议
   - 验证方案
```

## ⚙️ 配置说明

### 服务器配置

```yaml
server:
  host: "0.0.0.0"  # 监听地址
  port: 5000       # 监听端口
  debug: true      # 调试模式
```

### 分析配置

```yaml
analysis:
  default_provider: "aliyun"  # 默认提供商
  default_model: "qwen-max"   # 默认模型
  timeout: 120                # 超时时间（秒）
```

## 🔧 API 接口

### 设备管理
- `GET /api/targets` - 获取设备列表
- `POST /api/targets` - 添加设备
- `DELETE /api/targets/<id>` - 删除设备

### 大模型
- `GET /api/llm/providers` - 获取可用提供商
- `GET /api/llm/models?provider=aliyun` - 获取模型列表
- `GET /api/config/llm` - 获取配置
- `POST /api/config/llm` - 更新配置

### 分析任务
- `POST /api/analyze` - 开始分析
- `GET /api/tasks/<id>` - 获取任务状态
- `GET /api/tasks/<id>/report` - 获取报告

### 报告管理
- `GET /api/reports` - 获取报告列表
- `GET /api/reports/<filename>` - 获取报告内容

## 🛠️ 开发说明

### 添加新的大模型提供商

1. 在 `backend/services/llm_service.py` 中创建新的 Provider 类
2. 继承 `LLMProvider` 基类
3. 实现 `get_name()`, `get_models()`, `analyze()` 方法
4. 在 `LLMService._init_providers()` 中注册

### 自定义分析提示词

编辑 `backend/services/analysis_service.py` 中的 `ANALYSIS_PROMPT` 常量。

## 📝 注意事项

1. **网络安全**: 生产环境请关闭 debug 模式，使用 HTTPS
2. **API 费用**: 大模型调用会产生费用，请注意用量
3. **SSH 安全**: 建议使用密钥认证，妥善保管私钥
4. **并发限制**: 大模型 API 可能有并发限制，注意错峰使用

## 📄 许可证

MIT License

---

*让性能分析更智能、更简单* 🚀
