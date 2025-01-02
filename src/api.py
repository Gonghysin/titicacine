from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.responses import JSONResponse
from pydantic import BaseModel
import logging
import uuid

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProcessRequest(BaseModel):
    topic: str
    mode: str = "1"

app = FastAPI()

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
    return {
        "status": "ok",
        "message": "API 服务正常运行"
    }

@app.post("/api/process")
async def process_video(request: ProcessRequest):
    """处理视频接口"""
    try:
        # 导入处理器（延迟导入以减少启动时间）
        from workflow_processor import WorkflowProcessor
        processor = WorkflowProcessor()
        
        # 开始处理
        result = processor.process_workflow(request.topic, request.mode)
        
        return {
            "status": "success",
            "message": "处理完成",
            "result": result
        }
    except Exception as e:
        logger.error(f"处理失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "ok",
        "message": "Service is healthy"
    }) 