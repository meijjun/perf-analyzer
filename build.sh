#!/bin/bash
# 性能分析器打包脚本
# 用法：./build.sh [版本号]

set -e

# 获取版本号
VERSION=${1:-$(cat VERSION 2>/dev/null || echo "1.0.0")}
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
PACKAGE_NAME="perf-analyzer-v${VERSION}_${TIMESTAMP}"

echo "📦 开始打包 性能分析器 v${VERSION}"
echo "================================"

# 进入项目根目录
cd "$(dirname "$0")"
PROJECT_ROOT=$(pwd)

# 创建临时目录
BUILD_DIR="${PROJECT_ROOT}/build"
TEMP_DIR="${BUILD_DIR}/${PACKAGE_NAME}"

echo "📁 清理旧的构建文件..."
rm -rf "${BUILD_DIR}"
mkdir -p "${BUILD_DIR}"

echo "📋 复制项目文件..."
# 复制整个项目（排除 build 目录）
rsync -a --exclude='build/' "${PROJECT_ROOT}/" "${TEMP_DIR}/"

# 排除不需要的文件
cd "${TEMP_DIR}"
rm -rf __pycache__
rm -rf backend/__pycache__
rm -rf backend/services/__pycache__
rm -rf frontend/__pycache__
rm -rf frontend/templates/__pycache__
find . -name "*.pyc" -delete
find . -name "*.pyo" -delete
find . -name ".git" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "build" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "logs" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "data" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name "*.log" -delete

cd "${BUILD_DIR}"

echo "📦 创建 tar.xz 压缩包..."
tar -cJf "${PACKAGE_NAME}.tar.xz" "${PACKAGE_NAME}"

# 显示包信息
PACKAGE_SIZE=$(du -h "${PACKAGE_NAME}.tar.xz" | cut -f1)
echo ""
echo "✅ 打包完成!"
echo "================================"
echo "文件名：${PACKAGE_NAME}.tar.xz"
echo "文件大小：${PACKAGE_SIZE}"
echo "文件路径：${BUILD_DIR}/${PACKAGE_NAME}.tar.xz"
echo ""

# 创建 VERSION 文件
echo "${VERSION}" > "${PROJECT_ROOT}/VERSION"

echo "📝 版本信息已更新：v${VERSION}"
echo "================================"
