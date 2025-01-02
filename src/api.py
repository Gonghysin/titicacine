from fastapi import FastAPI
from starlette.responses import JSONResponse
import uvicorn

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

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, http="h11", loop="none") 