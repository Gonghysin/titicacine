from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import uuid
import json
from dotenv import load_dotenv
import logging
import redis
from urllib.parse import urlparse

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 加载环境变量
load_dotenv()

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

# Redis 连接
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
redis_client = None

try:
    url = urlparse(redis_url)
    redis_client = redis.Redis(
        host=url.hostname,
        port=url.port,
        password=url.password,
        ssl=url.scheme == 'rediss',
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5
    )
    redis_client.ping()
    logger.info("Redis connection successful")
except Exception as e:
    logger.error(f"Redis connection error: {str(e)}")
    # 在开发环境中继续运行
    if os.getenv('VERCEL_ENV') != 'production':
        redis_client = None

class ProcessRequest(BaseModel):
    topic: str
    mode: str = "1"

# 静态文件服务
try:
    app.mount("/static", StaticFiles(directory="src/static"), name="static")
except Exception as e:
    logger.error(f"Failed to mount static files: {str(e)}")

@app.get("/")
async def read_root():
    """提供前端页面"""
    try:
        return FileResponse('src/static/index.html')
    except Exception as e:
        logger.error(f"Failed to serve index.html: {str(e)}")
        return {"status": "error", "message": "无法加载页面"}

@app.get("/api")
async def check_api():
    """API 状态检查"""
    redis_status = "disconnected"
    try:
        if redis_client:
            redis_client.ping()
            redis_status = "connected"
    except:
        pass
    
    return {
        "status": "ok",
        "message": "API 服务正常运行",
        "redis_status": redis_status
    }

async def process_task(task_id: str, request: ProcessRequest):
    """后台任务处理"""
    if not redis_client:
        logger.error("Redis client not available")
        return
        
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
        
        # 导入处理器（延迟导入以减少启动时间）
        from workflow_processor import WorkflowProcessor
        processor = WorkflowProcessor()
        result = processor.process_workflow(request.topic, request.mode)
        
        # 更新任务状态为完成
        task_data.update({
            "status": "completed",
            "progress": 100,
            "message": "处理完成",
            "result": result
        })
    except Exception as e:
        logger.error(f"Task processing error: {str(e)}")
        task_data = {
            "status": "failed",
            "progress": 0,
            "message": f"处理失败: {str(e)}"
        }
    finally:
        try:
            if redis_client:
                redis_client.setex(f"task:{task_id}", 3600, json.dumps(task_data))
        except Exception as e:
            logger.error(f"Failed to update task status: {str(e)}")

@app.post("/api/process")
async def process_video(request: ProcessRequest, background_tasks: BackgroundTasks):
    """处理视频接口"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis 服务不可用")
        
    try:
        task_id = str(uuid.uuid4())
        task_data = {
            "status": "pending",
            "progress": 0,
            "message": "任务已创建",
            "topic": request.topic,
            "mode": request.mode
        }
        
        redis_client.setex(f"task:{task_id}", 3600, json.dumps(task_data))
        background_tasks.add_task(process_task, task_id, request)
        
        return {
            "status": "success",
            "message": "任务已创建",
            "task_id": task_id
        }
    except Exception as e:
        logger.error(f"Failed to create task: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
    if not redis_client:
        raise HTTPException(status_code=503, detail="Redis 服务不可用")
        
    try:
        task_data = redis_client.get(f"task:{task_id}")
        if not task_data:
            raise HTTPException(status_code=404, detail="任务不存在")
            
        task = json.loads(task_data)
        return {
            "status": task["status"],
            "progress": task["progress"],
            "message": task["message"],
            "result": task.get("result")
        }
    except redis.RedisError as e:
        logger.error(f"Redis error: {str(e)}")
        raise HTTPException(status_code=500, detail="无法获取任务状态")
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        raise HTTPException(status_code=500, detail="任务状态数据无效") 