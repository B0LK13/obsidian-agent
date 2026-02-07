"""B0LK13v2 PKM-Agent - Main Application"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(
    title="B0LK13v2 PKM-Agent",
    description="AI-powered Personal Knowledge Management",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/^")
async def root():
    return {
        "status": "running",
        "service": "B0LK13v2 PKM-Agent",
        "version": "0.1.0"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/api/v1/tasks")
async def list_tasks():
    return {"tasks": [], "total": 0}

if __name__ == "__main__":
    print("🚀 Starting B0LK13v2 PKM-Agent...")
    print("📖 Docs: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
