#!/bin/bash
# 停止后台运行的服务

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/logs/server.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "正在停止服务 (PID: $PID)..."
        kill $PID
        rm -f "$PID_FILE"
        echo "✓ 服务已停止"
    else
        echo "⚠ 服务未运行 (PID 文件存在但进程不存在)"
        rm -f "$PID_FILE"
    fi
else
    # 尝试通过端口查找进程
    PORT=5000
    PID=$(lsof -t -i:$PORT 2>/dev/null | head -1)
    if [ -n "$PID" ]; then
        echo "发现运行在端口 $PORT 的进程 (PID: $PID)"
        echo "正在停止..."
        kill $PID
        echo "✓ 服务已停止"
    else
        echo "ℹ 未找到运行的服务"
    fi
fi
