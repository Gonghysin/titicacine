#!/bin/bash

# 定义变量
SERVER="root@45.192.101.86"
PORT="17471"
REMOTE_DIR="/var/www/myproject"

# 检查必要文件是否存在
echo "检查必要文件..."
REQUIRED_FILES=("requirements.txt" ".env" "index.py" "src")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -e "$file" ]; then
        echo "错误: $file 不存在！"
        exit 1
    fi
done

# 创建临时目录并复制文件
echo "准备项目文件..."
TEMP_DIR=$(mktemp -d)
cp -r *.py *.txt *.json .env src/ tests/ docs/ "$TEMP_DIR" 2>/dev/null || true

# 上传项目文件
echo "正在上传项目文件..."
scp -P $PORT -r "$TEMP_DIR"/* $SERVER:$REMOTE_DIR/

# 清理临时目录
rm -rf "$TEMP_DIR"

# 连接到服务器并设置环境
echo "配置服务器环境..."
ssh -p $PORT $SERVER << 'EOF'
cd /var/www/myproject || exit 1

# 确保 Redis 正在运行
if ! systemctl is-active --quiet redis-server; then
    echo "启动 Redis 服务..."
    systemctl start redis-server
fi

# 确保虚拟环境存在并激活
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3.9 -m venv venv
fi
source venv/bin/activate

# 设置环境变量
set -a
source .env
set +a

# 停止现有的服务
echo "停止现有服务..."
pkill -f "uvicorn index:app" || true
pkill -f "celery" || true
pkill -f "flower" || true

# 等待服务完全停止
sleep 2

# 启动后台服务
echo "启动服务..."
nohup uvicorn index:app --host 0.0.0.0 --port 8000 > uvicorn.log 2>&1 &
echo "FastAPI 服务已启动在端口 8000"

# 启动 Celery Worker
nohup celery -A src.celery_app worker --loglevel=info > celery_worker.log 2>&1 &
echo "Celery worker 已启动"

# 启动 Flower 监控
nohup celery -A src.celery_app flower --port=5555 > flower.log 2>&1 &
echo "Flower 监控已启动在端口 5555"

# 等待服务启动
sleep 5

# 检查服务状态
echo "检查服务状态..."
if pgrep -f "uvicorn index:app" > /dev/null; then
    echo "✓ FastAPI 服务正在运行"
else
    echo "✗ FastAPI 服务启动失败"
fi

if pgrep -f "celery.*worker" > /dev/null; then
    echo "✓ Celery worker 正在运行"
else
    echo "✗ Celery worker 启动失败"
fi

if pgrep -f "flower" > /dev/null; then
    echo "✓ Flower 监控正在运行"
else
    echo "✗ Flower 监控启动失败"
fi

# 显示日志末尾，以便查看可能的错误
echo -e "\n最近的日志:"
echo "=== FastAPI 日志 ==="
tail -n 5 uvicorn.log
echo "=== Celery 日志 ==="
tail -n 5 celery_worker.log
echo "=== Flower 日志 ==="
tail -n 5 flower.log

echo -e "\n部署完成！"
echo "FastAPI 服务运行在: http://$(hostname -I | awk '{print $1}'):8000"
echo "Flower 监控面板运行在: http://$(hostname -I | awk '{print $1}'):5555"
EOF 