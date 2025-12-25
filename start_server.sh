#!/bin/bash
# GitSee 服务启动脚本 (Linux/Mac)

echo "========================================"
echo "GitSee 服务启动中..."
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3"
    echo "请先安装 Python 3.7 或更高版本"
    echo ""
    echo "安装方法:"
    echo "  Ubuntu/Debian: sudo apt-get install python3"
    echo "  CentOS/RHEL:   sudo yum install python3"
    echo "  macOS:         brew install python3"
    exit 1
fi

# 检查 Python 版本
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "检测到 Python 版本: $PYTHON_VERSION"

# 提取主版本号和次版本号
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

# 检查版本是否符合要求
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 7 ]); then
    echo "错误: Python 版本过低 ($PYTHON_VERSION)"
    echo "GitSee 需要 Python 3.7 或更高版本"
    echo ""
    echo "建议操作:"
    echo "  1. 访问 https://www.python.org/downloads/ 下载最新版本"
    echo "  2. 或使用 pyenv 安装: pyenv install 3.11.0"
    exit 1
fi

# 切换到脚本所在目录
cd "$(dirname "$0")"

# 检查是否首次运行
if [ ! -f "data/gitsee.db" ]; then
    echo ""
    echo "检测到首次运行,正在初始化..."
    echo ""
    python3 setup.py

    if [ $? -ne 0 ]; then
        echo ""
        echo "初始化失败,请查看上方错误信息"
        exit 1
    fi
    echo ""
fi

# 启动 Flask 应用
echo "正在启动 Web 服务..."
echo "访问地址: http://localhost:5000"
echo "按 Ctrl+C 停止服务"
echo ""

# 在后台启动服务
python3 backend/app.py &
SERVER_PID=$!

# 等待服务启动
sleep 3

# 检查服务是否启动成功
if ps -p $SERVER_PID > /dev/null; then
    echo "服务启动成功!"
    echo "正在打开浏览器..."

    # 尝试打开浏览器(根据不同操作系统)
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        open http://localhost:5000
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v xdg-open &> /dev/null; then
            xdg-open http://localhost:5000
        elif command -v gnome-open &> /dev/null; then
            gnome-open http://localhost:5000
        else
            echo "请手动在浏览器中打开: http://localhost:5000"
        fi
    fi

    echo ""
    echo "服务正在运行. 按 Ctrl+C 停止服务."

    # 等待用户中断
    wait $SERVER_PID
else
    echo ""
    echo "服务启动失败,请检查错误信息"
    exit 1
fi
