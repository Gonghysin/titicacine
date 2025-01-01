from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.workflow_processor import WorkflowProcessor
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

class ProcessRequest(BaseModel):
    topic: str
    mode: str = "1"

@app.get("/")
async def read_root():
    return {"message": "欢迎使用 YouTube 视频转文章 API"}

@app.post("/process")
async def process_video(request: ProcessRequest):
    try:
        # 初始化处理器
        processor = WorkflowProcessor()
        
        # 处理视频
        result = processor.process_workflow(request.topic, request.mode)
        
        if result:
            return {
                "status": "success",
                "message": "处理完成",
                "result": result
            }
        else:
            raise HTTPException(status_code=500, detail="处理失败")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 