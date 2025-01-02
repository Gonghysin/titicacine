#!/bin/bash

# 定义变量
SERVER="root@45.192.101.86"
PORT="17471"

# 连接到服务器并停止服务
ssh -p $PORT $SERVER << 'EOF'
cd /var/www/myproject

echo "正在停止服务..."

# 停止 FastAPI 服务
pkill -f "uvicorn main:app" || true
echo "FastAPI 服务已停止"

# 停止 Celery Worker
pkill -f "celery worker" || true
echo "Celery worker 已停止"

# 停止 Flower 监控
pkill -f "flower" || true
echo "Flower 监控已停止"

# 验证服务是否已停止
echo "检查服务状态..."
ps aux | grep -E "uvicorn|celery|flower"

echo "所有服务已停止！"
EOF 