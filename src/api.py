from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.responses import JSONResponse
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "ok",
        "message": "Service is healthy"
    }) 