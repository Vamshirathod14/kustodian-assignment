from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uuid
import asyncio

from database import init_db, create_job, get_job, get_logs, update_job_status
from automation import run_automation
from websocket_manager import manager

app = FastAPI(title="Kustodian Browser Automation")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class JobRequest(BaseModel):
    url: str
    goal: str

class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str

background_tasks_store = {}

@app.on_event("startup")
async def startup():
    await init_db()
    print("✅ Database initialized")

@app.post("/api/jobs", response_model=JobResponse)
async def create_job_endpoint(request: JobRequest):
    job_id = str(uuid.uuid4())[:8]
    await create_job(job_id, request.url, request.goal)
    
    asyncio.create_task(run_automation(job_id, request.url, request.goal, manager))
    background_tasks_store[job_id] = True
    
    return JobResponse(
        job_id=job_id,
        status="queued",
        message="Job created and queued for execution"
    )

@app.get("/api/jobs/{job_id}")
async def get_job_status(job_id: str):
    job = await get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@app.get("/api/jobs/{job_id}/logs")
async def get_job_logs(job_id: str):
    logs = await get_logs(job_id)
    return {"logs": logs}

@app.websocket("/ws/{job_id}")
async def websocket_endpoint(websocket: WebSocket, job_id: str):
    await manager.connect(job_id, websocket)
    try:
        logs = await get_logs(job_id)
        for log in logs:
            await websocket.send_json({
                "type": log["event_type"],
                "message": log["message"],
                "step": log["step_number"],
                "job_id": job_id,
                "historic": True
            })
        
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(job_id, websocket)

@app.get("/api/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
