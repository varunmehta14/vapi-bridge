from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn

from database import DatabaseManager
from manager import EngagementManager

app = FastAPI(
    title="Tesseract Workflow Engine",
    description="Backend engine for managing and executing workflows",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Initialize database and manager
db_manager = DatabaseManager()
engagement_manager = EngagementManager(db_manager)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    db_manager.init_db()

# Pydantic models for request/response
class WorkflowInput(BaseModel):
    input_params: Dict[str, Any]

class UserInput(BaseModel):
    user_input: str

class WorkflowResponse(BaseModel):
    job_id: str
    status: str
    workflow_name: str
    user_id: str
    message: str

class GeneralResponse(BaseModel):
    response: str

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    workflow_name: str
    user_id: str
    input_params: Dict[str, Any]
    results: Optional[Dict[str, Any]] = None
    created_at: str

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Tesseract Workflow Engine is running",
        "status": "healthy",
        "version": "1.0.0"
    }

@app.post("/run_workflow/{workflow_name}/{user_id}", response_model=WorkflowResponse)
async def run_workflow(
    workflow_name: str, 
    user_id: str, 
    workflow_input: WorkflowInput,
    background_tasks: BackgroundTasks
):
    """
    Primary endpoint to trigger a specific workflow
    
    Args:
        workflow_name: Name of the workflow to execute
        user_id: Unique identifier for the user
        workflow_input: Input parameters for the workflow
        background_tasks: FastAPI background tasks for async execution
        
    Returns:
        WorkflowResponse with job details
    """
    try:
        # Trigger the workflow and get job information
        result = engagement_manager.trigger_workflow(
            workflow_name=workflow_name,
            user_id=user_id,
            input_params=workflow_input.input_params
        )
        
        # Start background task to simulate workflow execution
        background_tasks.add_task(
            engagement_manager.simulate_workflow_execution,
            result["job_id"]
        )
        
        return WorkflowResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/receive_user_input/{user_id}", response_model=GeneralResponse)
async def receive_user_input(user_id: str, user_input: UserInput):
    """
    Primary endpoint for general user queries that don't fit specific workflows
    
    Args:
        user_id: Unique identifier for the user
        user_input: The user's raw input/question
        
    Returns:
        GeneralResponse with the system's response
    """
    try:
        result = engagement_manager.handle_general_query(
            user_id=user_id,
            user_input=user_input.user_input
        )
        
        return GeneralResponse(**result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/job_status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """
    Get the status and results of a specific job
    
    Args:
        job_id: Unique identifier for the job
        
    Returns:
        JobStatusResponse with job details and results
    """
    try:
        job = db_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
        
        return JobStatusResponse(
            job_id=job.job_id,
            status=job.status,
            workflow_name=job.workflow_name,
            user_id=job.user_id,
            input_params=job.input_params,
            results=job.results,
            created_at=job.created_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/workflows")
async def list_workflows():
    """
    List all available workflows
    
    Returns:
        List of available workflows with their descriptions
    """
    try:
        db = db_manager.SessionLocal()
        workflows = db.query(db_manager.Workflow).all()
        db.close()
        
        return {
            "workflows": [
                {
                    "name": workflow.name,
                    "description": workflow.description,
                    "required_params": workflow.required_params
                }
                for workflow in workflows
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    ) 