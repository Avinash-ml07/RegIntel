import uuid
from typing import Dict, List, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, Path
from pydantic import BaseModel, Field

from app.config import settings
from app.agents.watcher import watcher_graph
from app.schemas.state import StructuralClause

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Regulatory ingestion microservice supporting both online and offline operations",
    version="1.0.0"
)

# In-memory execution storage instance
jobs_store: Dict[str, dict] = {}

# --- Request/Response Models ---

class TriggerRequest(BaseModel):
    url: str = Field(
        default="mock://rbi-circular-investment-portfolio",
        description="Target reference URL or mock:// identifier."
    )
    raw_text: Optional[str] = Field(
        default=None,
        description="Explicit document string representation override."
    )

class TriggerLocalRequest(BaseModel):
    file_path: Optional[str] = Field(
        default=None,
        description="Relative file name inside your local regulatory_dropbox folder, or absolute path."
    )
    raw_text: Optional[str] = Field(
        default=None,
        description="Optional text payload block to run pipeline processing directly."
    )

class TriggerResponse(BaseModel):
    task_id: str = Field(..., description="Unique validation hash representing processing execution.")
    status: str = Field(..., description="Initial task execution status.")
    source_resource: Optional[str] = Field(None, description="The processed target resource.")

class JobStatusResponse(BaseModel):
    task_id: str
    status: str
    errors: List[str]
    clauses_count: int
    clauses: List[StructuralClause]

# --- Background Task Runner ---

async def run_watcher_pipeline(task_id: str, source_resource: Optional[str], raw_text: Optional[str]) -> None:
    initial_state = {
        "raw_text": raw_text if raw_text else "",
        "source_url": source_resource if source_resource else "",
        "clauses": [],
        "status": "INITIALIZED",
        "errors": []
    }
    
    try:
        # LangGraph State-Graph Execution
        result_state = await watcher_graph.ainvoke(initial_state)
        
        clauses_data = []
        for clause in result_state.get("clauses", []):
            if hasattr(clause, "model_dump"):
                clauses_data.append(clause.model_dump())
            else:
                clauses_data.append(dict(clause))

        jobs_store[task_id] = {
            "status": result_state.get("status", "COMPLETED"),
            "errors": result_state.get("errors", []),
            "clauses": clauses_data
        }
    except Exception as e:
        jobs_store[task_id] = {
            "status": "FAILED",
            "errors": [f"Pipeline execution engine crash: {str(e)}"],
            "clauses": []
        }

# --- Router Endpoints ---

@app.post(f"{settings.API_V1_STR}/watcher/trigger", response_model=TriggerResponse, status_code=202)
async def trigger_watcher(payload: TriggerRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    jobs_store[task_id] = {"status": "PROCESSING", "errors": [], "clauses": []}
    
    background_tasks.add_task(run_watcher_pipeline, task_id, payload.url, payload.raw_text)
    
    return TriggerResponse(
        task_id=task_id,
        status="PROCESSING",
        source_resource=payload.url
    )

@app.post(f"{settings.API_V1_STR}/watcher/trigger-local", response_model=TriggerResponse, status_code=202)
async def trigger_local_watcher(payload: TriggerLocalRequest, background_tasks: BackgroundTasks):
    if not payload.file_path and not payload.raw_text:
        raise HTTPException(status_code=400, detail="Local trigger requires either 'file_path' or 'raw_text'.")
        
    task_id = str(uuid.uuid4())
    jobs_store[task_id] = {"status": "PROCESSING", "errors": [], "clauses": []}
    
    background_tasks.add_task(run_watcher_pipeline, task_id, payload.file_path, payload.raw_text)
    
    return TriggerResponse(
        task_id=task_id,
        status="PROCESSING",
        source_resource=payload.file_path
    )

@app.get(f"{settings.API_V1_STR}/watcher/status/{{task_id}}", response_model=JobStatusResponse)
async def get_watcher_status(task_id: str = Path(..., description="Task execution sequence hash code")):
    if task_id not in jobs_store:
        raise HTTPException(status_code=404, detail="Execution reference target does not exist.")
    
    job = jobs_store[task_id]
    return JobStatusResponse(
        task_id=task_id,
        status=job["status"],
        errors=job["errors"],
        clauses_count=len(job["clauses"]),
        clauses=[StructuralClause(**c) for c in job["clauses"]]
    )