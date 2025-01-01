#!/bin/bash

# 定义颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${RED}停止 YouTube 视频转文章服务...${NC}"

# 停止 API 服务
echo -e "${GREEN}1. 停止 API 服务...${NC}"
pkill -f "python src/run_api.py"

# 停止 Flower
echo -e "${GREEN}2. 停止 Flower 监控...${NC}"
pkill -f "celery.*flower"

# 停止 Celery Worker
echo -e "${GREEN}3. 停止 Celery Worker...${NC}"
pkill -f "python src/run_worker.py"

# 停止 Redis
echo -e "${GREEN}4. 停止 Redis 服务器...${NC}"
redis-cli shutdown

echo -e "\n${GREEN}所有服务已停止${NC}" 