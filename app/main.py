import uuid
from typing import Dict, List, Optional
from fastapi import FastAPI, BackgroundTasks, HTTPException, Path
from pydantic import BaseModel, Field

from app.config import settings
from app.agents.watcher import watcher_graph
from app.schemas.state import StructuralClause

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Regulatory structural watcher ingest microservice",
    version="1.0.0"
)

# In-memory execution storage instance
jobs_store: Dict[str, dict] = {}

class TriggerRequest(BaseModel):
    url: str = Field(
        default="mock://rbi-circular-investment-portfolio",
        description="Target reference URL (or mock:// sequence) for document extraction."
    )
    raw_text: Optional[str] = Field(
        default=None,
        description="Explicit document string representation override to bypass active download requests."
    )

class TriggerResponse(BaseModel):
    task_id: str = Field(..., description="Unique verification hash representing processing execution.")
    status: str = Field(..., description="Initial task execution status.")
    source_url: str = Field(..., description="The context identifier being evaluated.")

class JobStatusResponse(BaseModel):
    task_id: str
    status: str
    errors: List[str]
    clauses_count: int
    clauses: List[StructuralClause]

async def run_watcher_pipeline(task_id: str, url: str, raw_text: Optional[str]) -> None:
    initial_state = {
        "raw_text": raw_text if raw_text else "",
        "source_url": url,
        "clauses": [],
        "status": "INITIALIZED",
        "errors": []
    }
    
    try:
        # LangGraph State-Graph Execution
        result_state = await watcher_graph.ainvoke(initial_state)
        
        # Serialize result structures safely for the endpoint store
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

@app.post(f"{settings.API_V1_STR}/watcher/trigger", response_model=TriggerResponse, status_code=202)
async def trigger_watcher(payload: TriggerRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    
    jobs_store[task_id] = {
        "status": "PROCESSING",
        "errors": [],
        "clauses": []
    }
    
    background_tasks.add_task(
        run_watcher_pipeline,
        task_id,
        payload.url,
        payload.raw_text
    )
    
    return TriggerResponse(
        task_id=task_id,
        status="PROCESSING",
        source_url=payload.url
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