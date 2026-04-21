@echo off
chcp 65001 >nul
echo ============================================
echo 性能优化脚本（Windows 版）
echo ============================================
echo.

REM 从 JSON 文件读取优化命令
if "%~1"=="" (
    echo 用法：generate_optimization.bat [优化计划 JSON 文件]
    echo 示例：generate_optimization.bat ..\reports\optimization_plan_20260419.json
    exit /b 1
)

set JSON_FILE=%~1

if not exist "%JSON_FILE%" (
    echo 错误：文件不存在：%JSON_FILE%
    exit /b 1
)

echo 正在读取优化计划...
echo.

REM 解析 JSON 并执行命令（简化版，实际应使用 Python 解析）
echo ⚠️  注意：Windows 批处理解析 JSON 能力有限
echo 建议使用 Python 脚本执行：
echo.
echo python ..\backend\apply_optimization.py "%JSON_FILE%"
echo.

pause
