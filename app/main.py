from fastapi import FastAPI
from .config import settings


app = FastAPI(
    title="Система управления командой",
    description="MVP для управления командой",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"message": "Team Management System API"}


@app.get("/health")
async def health_check():
    return {"status": "все ок", "environment": settings.environment}
