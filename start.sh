#!/bin/bash
# =============================================================================
# Linux 性能分析器 - 启动脚本 (Linux/Unix)
# 用法：./start.sh [选项]
# 选项:
#   --port PORT     指定端口 (默认：5000)
#   --host HOST     指定主机 (默认：0.0.0.0)
#   --debug         启用调试模式
#   --daemon        后台运行
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
PORT=5000
HOST="0.0.0.0"
DEBUG=false
DAEMON=false
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --port)
            PORT="$2"
            shift 2
            ;;
        --host)
            HOST="$2"
            shift 2
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        --daemon)
            DAEMON=true
            shift
            ;;
        -h|--help)
            echo "用法：$0 [选项]"
            echo "选项:"
            echo "  --port PORT     指定端口 (默认：5000)"
            echo "  --host HOST     指定主机 (默认：0.0.0.0)"
            echo "  --debug         启用调试模式"
            echo "  --daemon        后台运行"
            echo "  -h,--help       显示帮助"
            exit 0
            ;;
        *)
            echo -e "${RED}未知选项：$1${NC}"
            echo "使用 -h 或 --help 查看帮助"
            exit 1
            ;;
    esac
done

# 打印横幅
echo -e "${BLUE}"
echo "=============================================="
echo "  Linux 性能分析器 v2.0"
echo "  实时监控 | 优化命令 | 性能基线"
echo "=============================================="
echo -e "${NC}"

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ 错误：未找到 python3${NC}"
    echo "请安装 Python 3.8+"
    exit 1
fi

PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}✓${NC} Python 版本：$PYTHON_VERSION"

# 检查依赖
echo ""
echo "检查依赖..."
REQUIRED_PACKAGES=("flask" "flask_cors" "paramiko" "pyyaml" "requests")
MISSING_PACKAGES=()

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! python3 -c "import $pkg" 2>/dev/null; then
        MISSING_PACKAGES+=("$pkg")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo -e "${YELLOW}⚠ 缺少依赖包：${MISSING_PACKAGES[*]}${NC}"
    echo "正在安装..."
    pip3 install -q "${MISSING_PACKAGES[@]}"
    echo -e "${GREEN}✓${NC} 依赖安装完成"
else
    echo -e "${GREEN}✓${NC} 所有依赖已安装"
fi

# 检查并创建必要目录
echo ""
echo "检查目录结构..."
mkdir -p "$SCRIPT_DIR/backend/logs"
mkdir -p "$SCRIPT_DIR/backend/config"
mkdir -p "$SCRIPT_DIR/reports"
mkdir -p "$SCRIPT_DIR/baselines"
mkdir -p "$SCRIPT_DIR/docs"
echo -e "${GREEN}✓${NC} 目录结构就绪"

# 检查配置文件
if [ ! -f "$SCRIPT_DIR/backend/config/config.yaml" ]; then
    echo ""
    echo -e "${YELLOW}⚠ 配置文件不存在，创建默认配置...${NC}"
    cat > "$SCRIPT_DIR/backend/config/config.yaml" << 'EOF'
# Linux 性能分析器配置文件

llm:
  aliyun:
    api_key: ""  # 填入阿里云 API Key
    enabled: true
  deepseek:
    api_key: ""  # 填入 DeepSeek API Key
    enabled: true
  zhipu:
    api_key: ""  # 填入智谱 AI API Key
    enabled: true

analysis:
  default_provider: "aliyun"
  default_model: "qwen-max"
  timeout: 120

server:
  host: "0.0.0.0"
  port: 5000
  debug: false
EOF
    echo -e "${GREEN}✓${NC} 配置文件已创建：backend/config/config.yaml"
    echo -e "${YELLOW}提示：请编辑配置文件填入大模型 API Key${NC}"
fi

# 启动服务
echo ""
echo -e "${BLUE}启动服务...${NC}"
echo "  主机：$HOST"
echo "  端口：$PORT"
echo "  调试：$DEBUG"
echo "  后台：$DAEMON"
echo ""

cd "$SCRIPT_DIR/backend"

if [ "$DAEMON" = true ]; then
    # 后台运行
    nohup python3 app.py > ../logs/server.log 2>&1 &
    PID=$!
    echo $PID > ../logs/server.pid
    echo -e "${GREEN}✓${NC} 服务已在后台启动 (PID: $PID)"
    echo ""
    echo "日志文件：$SCRIPT_DIR/logs/server.log"
    echo "停止服务：kill $PID 或 ./stop.sh"
else
    # 前台运行
    echo -e "${GREEN}=============================================="
    echo "服务已启动"
    echo "==============================================${NC}"
    echo ""
    echo -e "访问地址:"
    echo -e "  ${BLUE}实时监控仪表板:${NC} http://localhost:$PORT/dashboard"
    echo -e "  ${BLUE}主界面:${NC} http://localhost:$PORT/"
    echo -e "  ${BLUE}API 测试:${NC} http://localhost:$PORT/api/health"
    echo ""
    echo -e "${YELLOW}按 Ctrl+C 停止服务${NC}"
    echo ""
    
    # 设置环境变量
    export FLASK_APP=app.py
    export FLASK_ENV=development
    
    # 启动 Flask
    if [ "$DEBUG" = true ]; then
        python3 app.py
    else
        python3 -c "
import os
os.environ['FLASK_APP'] = 'app.py'
os.environ['FLASK_ENV'] = 'production'
from app import app
app.run(host='$HOST', port=$PORT, debug=False, threaded=True)
"
    fi
fi
