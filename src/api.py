from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
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

@app.get("/")
async def read_root():
    """测试接口"""
    return {
        "status": "ok",
        "message": "API 服务正常运行",
        "version": "1.0.0"
    }

class ProcessRequest(BaseModel):
    topic: str
    mode: str = "1"

@app.post("/process")
async def process_video(request: ProcessRequest):
    """处理视频接口"""
    try:
        return {
            "status": "success",
            "message": "API 接口正常",
            "request": request.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 