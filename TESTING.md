# 🧪 测试文档

## 测试套件结构

```
tests/
├── test_config.py          # 配置管理测试
├── test_ssh_service.py     # SSH 服务测试
├── test_llm_service.py     # 大模型服务测试
├── test_api.py             # API 接口测试
├── test_integration.py     # 集成测试
├── test_runner.py          # 统一测试运行器
├── run_tests.sh            # Shell 测试脚本
└── reports/                # 测试报告输出目录
```

## 测试覆盖

### 单元测试

#### 1. 配置管理测试 (`test_config.py`)
- ✅ 默认配置创建
- ✅ 获取大模型配置
- ✅ 更新大模型配置
- ✅ 添加目标设备
- ✅ 删除目标设备
- ✅ 获取服务器配置

#### 2. SSH 服务测试 (`test_ssh_service.py`)
- ✅ SSH 服务初始化
- ✅ 使用密钥连接
- ✅ 使用密码连接
- ✅ 连接失败处理
- ✅ 执行命令
- ✅ 未连接时执行命令
- ✅ 收集性能数据
- ✅ 断开连接
- ✅ 连接测试功能

#### 3. 大模型服务测试 (`test_llm_service.py`)
- ✅ 阿里云提供商初始化
- ✅ DeepSeek 提供商初始化
- ✅ 智谱 AI 提供商初始化
- ✅ 阿里云分析成功
- ✅ 阿里云分析失败
- ✅ DeepSeek 分析
- ✅ 获取可用提供商列表
- ✅ 获取指定提供商模型
- ✅ 使用有效提供商分析
- ✅ 使用无效提供商分析

#### 4. API 接口测试 (`test_api.py`)
- ✅ 健康检查接口
- ✅ 获取大模型提供商列表
- ✅ 获取模型列表
- ✅ 获取目标设备列表
- ✅ 添加目标设备
- ✅ 添加目标设备（缺少字段）
- ✅ 删除目标设备
- ✅ 开始分析（无目标）
- ✅ 获取报告列表
- ✅ 404 错误处理
- ✅ 主页访问
- ✅ 静态文件服务

#### 5. 集成测试 (`test_integration.py`)
- ✅ 完整工作流程
- ✅ SSH 连接模拟
- ✅ 大模型分析模拟
- ✅ 错误处理
- ✅ 配置加载性能
- ✅ 大模型服务初始化性能

## 运行测试

### 方式 1: 使用 Shell 脚本（推荐）

```bash
cd perf-analyzer-web
chmod +x tests/run_tests.sh
./tests/run_tests.sh
```

### 方式 2: 使用 Python 测试运行器

```bash
cd perf-analyzer-web
python3 tests/test_runner.py
```

### 方式 3: 运行单个测试文件

```bash
# 运行配置测试
python3 -m unittest tests.test_config -v

# 运行 SSH 服务测试
python3 -m unittest tests.test_ssh_service -v

# 运行大模型服务测试
python3 -m unittest tests.test_llm_service -v

# 运行 API 测试
python3 -m unittest tests.test_api -v

# 运行集成测试
python3 -m unittest tests.test_integration -v
```

### 方式 4: 使用 pytest

```bash
# 安装 pytest
pip install -r tests/requirements-test.txt

# 运行所有测试
pytest tests/ -v

# 运行特定测试
pytest tests/test_config.py -v

# 生成覆盖率报告
pytest tests/ --cov=backend --cov-report=html
```

## 测试报告

测试完成后，报告会自动生成到 `tests/reports/` 目录：

- `test_report_YYYYMMDD_HHMMSS.json` - JSON 格式详细报告
- `test_report_YYYYMMDD_HHMMSS.txt` - 文本格式报告
- `test_summary.txt` - 测试摘要

### 报告内容

```json
{
  "timestamp": "2026-04-18T16:00:00",
  "total_tests": 35,
  "passed": 35,
  "failures": 0,
  "errors": 0,
  "success": true,
  "details": {
    "failures": [],
    "errors": []
  }
}
```

## 持续集成

### GitHub Actions 示例

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r tests/requirements-test.txt
      
      - name: Run tests
        run: |
          python tests/test_runner.py
```

## 测试最佳实践

### 1. 添加新测试

在对应模块的测试文件中添加测试方法：

```python
def test_new_feature(self):
    """测试新功能"""
    # Arrange - 准备数据
    expected = "expected_result"
    
    # Act - 执行操作
    result = some_function()
    
    # Assert - 验证结果
    self.assertEqual(result, expected)
```

### 2. Mock 外部依赖

对于 SSH 连接、API 调用等外部依赖，使用 Mock：

```python
@patch('services.ssh_service.paramiko.SSHClient')
def test_ssh_connect(self, mock_ssh_client):
    mock_client = Mock()
    mock_ssh_client.return_value = mock_client
    
    # 测试逻辑...
```

### 3. 测试覆盖率

定期检查测试覆盖率：

```bash
pytest --cov=backend --cov-report=term-missing
```

目标覆盖率：
- 核心服务：> 80%
- API 接口：> 90%
- 配置管理：> 95%

## 常见问题

### Q: 测试失败怎么办？

A: 
1. 查看测试报告中的错误信息
2. 检查是否是环境问题（依赖、配置）
3. 检查是否是代码逻辑问题
4. 修复后重新运行测试

### Q: 如何跳过某些测试？

A: 使用 `@unittest.skip` 装饰器：

```python
@unittest.skip("暂时跳过")
def test_something(self):
    pass
```

### Q: 测试运行太慢？

A: 
1. 使用 Mock 减少真实 IO 操作
2. 并行运行测试：`pytest -n auto`
3. 优化测试 setup/teardown

## 测试检查清单

在提交代码前，确保：

- [ ] 所有单元测试通过
- [ ] 所有集成测试通过
- [ ] 测试覆盖率达标
- [ ] 测试报告已生成
- [ ] 没有测试警告

---

*测试是质量的保障，不是负担* 🧪
