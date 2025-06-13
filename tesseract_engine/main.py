from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
import time
from datetime import datetime

from database import DatabaseManager
from manager import EngagementManager
from monitoring import init_monitoring, monitoring
from database_config import db_config

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

# Initialize components
db_manager = DatabaseManager()
engagement_manager = EngagementManager(db_manager)
monitoring_manager = init_monitoring(app)

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    if not db_manager.init_db():
        raise Exception("Failed to initialize database")
    
    # Initialize monitoring metrics
    monitoring_manager.update_db_pool_metrics(db_config.get_connection_info())
    
    # Log startup
    monitoring_manager.log_workflow_event(
        "system_startup",
        {"status": "success", "timestamp": datetime.utcnow().isoformat()}
    )

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
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

# Dependency for database session
def get_db():
    with db_config.get_db_session() as session:
        yield session

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
    start_time = time.time()
    
    try:
        # Track workflow request
        monitoring_manager.track_workflow_request(workflow_name, "initiated")
        
        # Trigger the workflow
        result = engagement_manager.trigger_workflow(
            workflow_name=workflow_name,
            user_id=user_id,
            input_params=workflow_input.input_params
        )
        
        # Start background task
        background_tasks.add_task(
            engagement_manager.simulate_workflow_execution,
            result["job_id"]
        )
        
        # Track execution time
        monitoring_manager.track_workflow_execution(workflow_name, start_time)
        
        # Log successful workflow initiation
        monitoring_manager.log_workflow_event(
            "workflow_initiated",
            {
                "workflow_name": workflow_name,
                "user_id": user_id,
                "job_id": result["job_id"]
            }
        )
        
        return WorkflowResponse(**result)
        
    except ValueError as e:
        monitoring_manager.log_error(
            "workflow_validation_error",
            str(e),
            {"workflow_name": workflow_name, "user_id": user_id}
        )
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        monitoring_manager.log_error(
            "workflow_execution_error",
            str(e),
            {"workflow_name": workflow_name, "user_id": user_id}
        )
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
            error_message=job.error_message,
            created_at=job.created_at.isoformat(),
            updated_at=job.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        monitoring_manager.log_error(
            "job_status_error",
            str(e),
            {"job_id": job_id}
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/workflows")
async def list_workflows():
    """
    List all available workflows
    
    Returns:
        List of available workflows with their descriptions
    """
    try:
        with db_config.get_db_session() as db:
            workflows = db.query(db_manager.Workflow).all()
            
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
        monitoring_manager.log_error(
            "workflow_list_error",
            str(e)
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        db_status = db_config.init_db()
        
        # Get active jobs count
        with db_config.get_db_session() as db:
            status_counts = {
                status: db.query(db_manager.Job).filter(db_manager.Job.status == status).count()
                for status in ['pending', 'running', 'completed', 'failed']
            }
        
        # Update monitoring metrics
        monitoring_manager.update_active_jobs(status_counts)
        
        return {
            "status": "healthy" if db_status else "degraded",
            "database": "connected" if db_status else "disconnected",
            "active_jobs": status_counts,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        monitoring_manager.log_error(
            "health_check_error",
            str(e)
        )
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    ) 