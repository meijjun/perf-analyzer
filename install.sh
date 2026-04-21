#!/bin/bash
# =============================================================================
# Linux 性能分析器 - 安装脚本
# 用法：./install.sh [选项]
# 选项:
#   --with-psutil   安装 psutil (增强系统监控)
#   --with-all      安装所有可选依赖
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_PSUTIL=false
INSTALL_ALL=false

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --with-psutil)
            INSTALL_PSUTIL=true
            shift
            ;;
        --with-all)
            INSTALL_ALL=true
            shift
            ;;
        -h|--help)
            echo "用法：$0 [选项]"
            echo "选项:"
            echo "  --with-psutil   安装 psutil (增强系统监控)"
            echo "  --with-all      安装所有可选依赖"
            echo "  -h,--help       显示帮助"
            exit 0
            ;;
        *)
            echo -e "${RED}未知选项：$1${NC}"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}"
echo "=============================================="
echo "  Linux 性能分析器 - 安装程序"
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

# 检查 pip
if ! command -v pip3 &> /dev/null; then
    echo -e "${YELLOW}⚠ pip3 未安装，尝试安装...${NC}"
    if command -v apt-get &> /dev/null; then
        sudo apt-get update && sudo apt-get install -y python3-pip
    elif command -v yum &> /dev/null; then
        sudo yum install -y python3-pip
    else
        echo -e "${RED}❌ 请手动安装 pip3${NC}"
        exit 1
    fi
fi

# 安装基础依赖
echo ""
echo "安装基础依赖..."
pip3 install -q -r "$SCRIPT_DIR/requirements.txt"
echo -e "${GREEN}✓${NC} 基础依赖安装完成"

# 安装可选依赖
if [ "$INSTALL_ALL" = true ]; then
    echo ""
    echo "安装所有可选依赖..."
    pip3 install -q psutil watchdog python-dotenv
    echo -e "${GREEN}✓${NC} 可选依赖安装完成"
elif [ "$INSTALL_PSUTIL" = true ]; then
    echo ""
    echo "安装 psutil..."
    pip3 install -q psutil
    echo -e "${GREEN}✓${NC} psutil 安装完成"
fi

# 创建目录结构
echo ""
echo "创建目录结构..."
mkdir -p "$SCRIPT_DIR/backend/logs"
mkdir -p "$SCRIPT_DIR/backend/config"
mkdir -p "$SCRIPT_DIR/reports"
mkdir -p "$SCRIPT_DIR/baselines"
mkdir -p "$SCRIPT_DIR/docs"
echo -e "${GREEN}✓${NC} 目录结构创建完成"

# 设置执行权限
echo ""
echo "设置执行权限..."
chmod +x "$SCRIPT_DIR/start.sh"
chmod +x "$SCRIPT_DIR/stop.sh"
chmod +x "$SCRIPT_DIR/check_windows.py"
chmod +x "$SCRIPT_DIR/test_new_features.py"
echo -e "${GREEN}✓${NC} 权限设置完成"

# 创建 systemd 服务文件（可选）
echo ""
if [ -d "/etc/systemd/system" ] && [ "$EUID" -eq 0 ]; then
    echo "是否创建 systemd 服务？(y/n): "
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        cat > /etc/systemd/system/perf-analyzer.service << EOF
[Unit]
Description=Linux Performance Analyzer
After=network.target

[Service]
Type=simple
User=$(whoami)
WorkingDirectory=$SCRIPT_DIR
ExecStart=/usr/bin/python3 -m flask --app backend.app run --host=0.0.0.0 --port=5000
Restart=always

[Install]
WantedBy=multi-user.target
EOF
        systemctl daemon-reload
        systemctl enable perf-analyzer.service
        echo -e "${GREEN}✓${NC} systemd 服务已创建"
        echo "  启动：systemctl start perf-analyzer"
        echo "  停止：systemctl stop perf-analyzer"
        echo "  状态：systemctl status perf-analyzer"
    fi
fi

# 完成
echo ""
echo -e "${GREEN}=============================================="
echo "  安装完成！"
echo "==============================================${NC}"
echo ""
echo "下一步:"
echo "  1. 编辑配置文件：backend/config/config.yaml"
echo "  2. 填入大模型 API Key"
echo "  3. 启动服务：./start.sh"
echo ""
echo "访问地址:"
echo "  实时监控：http://localhost:5000/dashboard"
echo "  主界面：http://localhost:5000/"
echo ""
