from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import uuid
from dotenv import load_dotenv

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

# 模拟任务存储
tasks = {}

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
        
        # 存储任务信息
        tasks[task_id] = {
            "status": "pending",
            "progress": 0,
            "message": "任务已创建",
            "topic": request.topic,
            "mode": request.mode
        }
        
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
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
        
    task = tasks[task_id]
    return {
        "status": task["status"],
        "progress": task["progress"],
        "message": task["message"]
    } 