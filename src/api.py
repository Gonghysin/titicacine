from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
import json
from dotenv import load_dotenv
import sys
import logging
import traceback
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 记录环境信息
logger.info(f"Current file: {__file__}")
logger.info(f"Current directory: {os.getcwd()}")
logger.info(f"Directory contents: {os.listdir(os.getcwd())}")

# 添加 src 目录到 Python 路径
try:
    if '/var/task' in os.getcwd():  # Vercel 环境
        sys.path.append('/var/task/src')
    else:  # 本地环境
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.append(current_dir)
except Exception as e:
    logger.error(f"Failed to set Python path: {e}")

logger.info(f"Python path: {sys.path}")

# 导入 WorkflowProcessor
try:
    if os.path.exists(os.path.join(os.getcwd(), 'src', 'workflow_processor.py')):
        logger.info("Found workflow_processor.py in src directory")
    else:
        logger.error("workflow_processor.py not found in src directory")
        
    from workflow_processor import WorkflowProcessor
    logger.info("Successfully imported WorkflowProcessor")
except ImportError as e:
    logger.error(f"Failed to import WorkflowProcessor: {e}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    raise

import redis
from urllib.parse import urlparse

# 加载环境变量
load_dotenv()

# Redis 连接
redis_url = os.getenv('REDIS_URL')
if not redis_url:
    logger.error("REDIS_URL environment variable is not set")
    redis_url = 'redis://localhost:6379'

logger.info(f"Connecting to Redis at: {redis_url.replace(redis_url.split('@')[0], '***')}")

url = urlparse(redis_url)
try:
    redis_client = redis.Redis(
        host=url.hostname,
        port=url.port,
        password=url.password,
        ssl=True if url.scheme == 'rediss' else False,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5
    )
    # 测试连接
    redis_client.ping()
    logger.info("Redis connection successful")
except Exception as e:
    logger.error(f"Redis connection error: {str(e)}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    # 在开发环境中可以继续运行，在生产环境中应该停止
    if os.getenv('VERCEL_ENV') == 'production':
        raise

# 创建 FastAPI 应用
app = FastAPI(title="YouTube 视频转文章 API")

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api")
async def read_root():
    """API 状态检查"""
    try:
        # 测试 Redis 连接
        redis_client.ping()
        redis_status = "connected"
    except:
        redis_status = "disconnected"
    
    return {
        "status": "ok",
        "message": "API 服务正常运行",
        "version": "1.0.0",
        "redis_status": redis_status,
        "environment": os.getenv('VERCEL_ENV', 'development')
    }

class ProcessRequest(BaseModel):
    topic: str
    mode: str = "1"

async def process_task(task_id: str, request: ProcessRequest):
    """后台任务处理"""
    logger.info(f"Starting task processing for task_id: {task_id}")
    try:
        # 更新任务状态为处理中
        task_data = {
            "status": "processing",
            "progress": 10,
            "message": "正在处理任务...",
            "topic": request.topic,
            "mode": request.mode
        }
        redis_client.setex(f"task:{task_id}", 3600, json.dumps(task_data))
        logger.info(f"Task {task_id} status updated to processing")
        
        # 处理任务
        processor = WorkflowProcessor()
        logger.info(f"Starting workflow processing for task {task_id}")
        result = processor.process_workflow(request.topic, request.mode)
        logger.info(f"Workflow processing completed for task {task_id}")
        
        # 更新任务状态为完成
        task_data.update({
            "status": "completed",
            "progress": 100,
            "message": "处理完成",
            "result": result
        })
    except Exception as e:
        logger.error(f"Task processing error for task {task_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        task_data = {
            "status": "failed",
            "progress": 0,
            "message": f"处理失败: {str(e)}"
        }
    finally:
        try:
            redis_client.setex(f"task:{task_id}", 3600, json.dumps(task_data))
            logger.info(f"Final status update for task {task_id}: {task_data['status']}")
        except Exception as e:
            logger.error(f"Failed to update task status: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")

@app.post("/api/process")
async def process_video(request: ProcessRequest, background_tasks: BackgroundTasks):
    """处理视频接口"""
    logger.info(f"Received process request for topic: {request.topic}")
    try:
        # 创建任务ID
        task_id = str(uuid.uuid4())
        logger.info(f"Created task ID: {task_id}")
        
        # 初始化任务状态
        task_data = {
            "status": "pending",
            "progress": 0,
            "message": "任务已创建",
            "topic": request.topic,
            "mode": request.mode
        }
        
        # 尝试存储到Redis
        try:
            redis_client.setex(f"task:{task_id}", 3600, json.dumps(task_data))
            logger.info(f"Task {task_id} initialized in Redis")
        except Exception as e:
            logger.error(f"Failed to store task in Redis: {str(e)}")
            raise HTTPException(status_code=500, detail="无法创建任务状态")
        
        # 启动后台任务
        try:
            background_tasks.add_task(process_task, task_id, request)
            logger.info(f"Background task added for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to start background task: {str(e)}")
            raise HTTPException(status_code=500, detail="无法启动后台任务")
        
        return {
            "status": "success",
            "message": "任务已创建",
            "task_id": task_id
        }
    except Exception as e:
        logger.error(f"Failed to create task: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    logger.info(f"Checking status for task: {task_id}")
    try:
        task_data = redis_client.get(f"task:{task_id}")
        if not task_data:
            logger.warning(f"Task {task_id} not found")
            raise HTTPException(status_code=404, detail="任务不存在")
            
        task = json.loads(task_data)
        logger.info(f"Retrieved status for task {task_id}: {task['status']}")
        return {
            "status": task["status"],
            "progress": task["progress"],
            "message": task["message"],
            "result": task.get("result")
        }
    except redis.RedisError as e:
        logger.error(f"Redis error while getting task status: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="无法获取任务状态")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error for task {task_id}: {str(e)}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail="任务状态数据无效") 