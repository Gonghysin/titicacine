from fastapi import FastAPI
from starlette.responses import JSONResponse

app = FastAPI()

@app.get("/")
async def root():
    return JSONResponse({
        "status": "ok",
        "message": "API service is running"
    })

@app.get("/health")
async def health_check():
    return JSONResponse({
        "status": "ok",
        "message": "Service is healthy"
    }) 