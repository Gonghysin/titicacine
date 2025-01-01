#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}启动 YouTube 视频转文章服务...${NC}"

# 检查 Redis 是否已经运行
if ! pgrep redis-server > /dev/null; then
    echo -e "${GREEN}1. 启动 Redis 服务器...${NC}"
    redis-server &
    sleep 2
else
    echo -e "${GREEN}Redis 服务器已在运行${NC}"
fi

# 启动 Celery Worker
echo -e "${GREEN}2. 启动 Celery Worker...${NC}"
python src/run_worker.py &
sleep 2

# 启动 Flower
echo -e "${GREEN}3. 启动 Flower 监控...${NC}"
celery -A src.celery_app.celery_app flower &
sleep 2

# 启动 API 服务
echo -e "${GREEN}4. 启动 API 服务...${NC}"
python src/run_api.py &

# 打印访问信息
echo -e "\n${BLUE}所有服务已启动:${NC}"
echo -e "- Web 界面: ${GREEN}http://localhost:8000${NC}"
echo -e "- Flower 监控: ${GREEN}http://localhost:5555${NC}"

# 等待用户输入以关闭所有服务
echo -e "\n${BLUE}按 Ctrl+C 停止所有服务${NC}"
wait 