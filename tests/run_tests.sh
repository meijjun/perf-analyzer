#!/bin/bash
# 自动化测试运行脚本

set -e

echo "======================================"
echo "🧪 Web 版性能分析器 - 自动化测试"
echo "======================================"
echo ""

# 切换到项目目录
cd "$(dirname "$0")/.."

# 检查依赖
echo "📦 检查测试依赖..."
python3 -c "import unittest" 2>/dev/null || {
    echo "❌ unittest 不可用"
    exit 1
}

python3 -c "import flask" 2>/dev/null || {
    echo "❌ Flask 未安装，请先运行：pip install -r requirements.txt"
    exit 1
}

echo "✅ 依赖检查通过"
echo ""

# 创建测试报告目录
mkdir -p tests/reports

# 测试计数器
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 运行单个测试文件
run_test() {
    local test_file=$1
    local test_name=$(basename "$test_file" .py)
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📋 运行测试：$test_name"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    if python3 -m unittest "$test_file" -v 2>&1; then
        echo "✅ $test_name 通过"
        ((PASSED_TESTS++)) || true
    else
        echo "❌ $test_name 失败"
        ((FAILED_TESTS++)) || true
    fi
    ((TOTAL_TESTS++)) || true
    echo ""
}

# 运行所有单元测试
echo "🚀 开始运行测试套件..."
echo ""

# 1. 配置管理测试
run_test "tests.test_config"

# 2. SSH 服务测试
run_test "tests.test_ssh_service"

# 3. 大模型服务测试
run_test "tests.test_llm_service"

# 4. API 接口测试
run_test "tests.test_api"

# 5. 集成测试
run_test "tests.test_integration"

# 生成测试报告
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📊 测试报告"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "总测试数：$TOTAL_TESTS"
echo "✅ 通过：$PASSED_TESTS"
echo "❌ 失败：$FAILED_TESTS"
echo ""

if [ $FAILED_TESTS -eq 0 ]; then
    echo "🎉 所有测试通过！"
    echo ""
    
    # 生成 HTML 报告
    cat > tests/reports/test_summary.txt << EOF
测试报告
========
生成时间：$(date)

总测试数：$TOTAL_TESTS
通过：$PASSED_TESTS
失败：$FAILED_TESTS

状态：✅ 所有测试通过
EOF
    
    echo "📄 测试报告已保存到：tests/reports/test_summary.txt"
    exit 0
else
    echo "⚠️  有测试失败，请检查上方输出"
    echo ""
    
    # 生成失败报告
    cat > tests/reports/test_summary.txt << EOF
测试报告
========
生成时间：$(date)

总测试数：$TOTAL_TESTS
通过：$PASSED_TESTS
失败：$FAILED_TESTS

状态：❌ 有测试失败
EOF
    
    exit 1
fi
