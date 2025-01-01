from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
import json
from dotenv import load_dotenv
from workflow_processor import WorkflowProcessor
import redis
from urllib.parse import urlparse

# 加载环境变量
load_dotenv()

# Redis 连接
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
url = urlparse(redis_url)
redis_client = redis.Redis(
    host=url.hostname,
    port=url.port,
    password=url.password,
    ssl=True if url.scheme == 'rediss' else False
)

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
    return {
        "status": "ok",
        "message": "API 服务正常运行",
        "version": "1.0.0"
    }

class ProcessRequest(BaseModel):
    topic: str
    mode: str = "1"

@app.post("/api/process")
async def process_video(request: ProcessRequest):
    """处理视频接口"""
    try:
        # 创建任务ID
        task_id = str(uuid.uuid4())
        
        # 存储任务信息到 Redis
        task_data = {
            "status": "pending",
            "progress": 0,
            "message": "任务已创建",
            "topic": request.topic,
            "mode": request.mode
        }
        redis_client.setex(f"task:{task_id}", 3600, json.dumps(task_data))  # 1小时过期
        
        # 启动异步处理
        processor = WorkflowProcessor()
        try:
            result = processor.process_workflow(request.topic, request.mode)
            task_data.update({
                "status": "completed",
                "progress": 100,
                "message": "处理完成",
                "result": result
            })
        except Exception as e:
            task_data.update({
                "status": "failed",
                "progress": 0,
                "message": str(e)
            })
        finally:
            redis_client.setex(f"task:{task_id}", 3600, json.dumps(task_data))
        
        return {
            "status": "success",
            "message": "任务已创建",
            "task_id": task_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status/{task_id}")
async def get_task_status(task_id: str):
    """获取任务状态"""
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