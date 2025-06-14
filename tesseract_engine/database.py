from sqlalchemy import Column, String, Text, DateTime, JSON
try:
    from sqlalchemy.orm import declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from typing import Dict, Any, Optional
import json
import logging
from database_config import db_config

# Configure logging
logger = logging.getLogger(__name__)

Base = declarative_base()

class Workflow(Base):
    __tablename__ = "workflows"
    
    name = Column(String, primary_key=True)
    description = Column(Text)
    required_params = Column(JSON)

class Job(Base):
    __tablename__ = "jobs"
    
    job_id = Column(String, primary_key=True)
    workflow_name = Column(String)
    user_id = Column(String)
    status = Column(String, default="pending")
    input_params = Column(JSON)
    results = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    error_message = Column(Text, nullable=True)

class DatabaseManager:
    def __init__(self):
        self.engine = db_config.engine
        self.SessionLocal = db_config.SessionLocal
        self.Workflow = Workflow
        self.Job = Job
        
    def init_db(self):
        """Initialize database and seed with default workflows"""
        try:
            Base.metadata.create_all(bind=self.engine)
            self._seed_workflows()
            logger.info("Database initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Database initialization failed: {str(e)}")
            return False
    
    def _seed_workflows(self):
        """Seed the database with default workflows"""
        with db_config.get_db_session() as db:
            try:
                # Check if workflows already exist
                existing_workflow = db.query(Workflow).filter(Workflow.name == "financial_analysis").first()
                if existing_workflow:
                    return
                    
                # Seed financial_analysis workflow
                financial_workflow = Workflow(
                    name="financial_analysis",
                    description="Comprehensive financial analysis of a company including credit risk assessment, financial health metrics, and market positioning",
                    required_params=["company_name", "analysis_type"]
                )
                db.add(financial_workflow)
                db.commit()
                logger.info("Default workflows seeded successfully")
            except Exception as e:
                logger.error(f"Failed to seed workflows: {str(e)}")
                raise
    
    def get_workflow(self, workflow_name: str) -> Optional[Workflow]:
        """Get a workflow by name"""
        with db_config.get_db_session() as db:
            try:
                return db.query(Workflow).filter(Workflow.name == workflow_name).first()
            except Exception as e:
                logger.error(f"Failed to get workflow {workflow_name}: {str(e)}")
                raise
    
    def create_job(self, job_id: str, workflow_name: str, user_id: str, input_params: Dict[str, Any]) -> dict:
        """Create a new job entry and return its data as a dict"""
        with db_config.get_db_session() as db:
            try:
                job = Job(
                    job_id=job_id,
                    workflow_name=workflow_name,
                    user_id=user_id,
                    input_params=input_params,
                    status="pending"
                )
                db.add(job)
                db.commit()
                # Access all needed fields before session closes
                job_data = {
                    "job_id": job.job_id,
                    "status": job.status,
                    "workflow_name": job.workflow_name,
                    "user_id": job.user_id,
                    "message": f"Workflow '{workflow_name}' has been initiated successfully"
                }
                return job_data
            except Exception as e:
                logger.error(f"Failed to create job {job_id}: {str(e)}")
                raise
    
    def update_job_status(self, job_id: str, status: str, results: Optional[Dict[str, Any]] = None, error_message: Optional[str] = None):
        """Update job status and results"""
        with db_config.get_db_session() as db:
            try:
                job = db.query(Job).filter(Job.job_id == job_id).first()
                if job:
                    job.status = status
                    if results:
                        job.results = results
                    if error_message:
                        job.error_message = error_message
                    db.commit()
                    logger.info(f"Updated job {job_id} status to {status}")
            except Exception as e:
                logger.error(f"Failed to update job {job_id}: {str(e)}")
                raise
    
    def get_job(self, job_id: str) -> Optional[dict]:
        """Get a job by job_id and return as dict"""
        with db_config.get_db_session() as db:
            try:
                job = db.query(Job).filter(Job.job_id == job_id).first()
                if job:
                    return {
                        "job_id": job.job_id,
                        "status": job.status,
                        "workflow_name": job.workflow_name,
                        "user_id": job.user_id,
                        "input_params": job.input_params,
                        "results": job.results,
                        "error_message": job.error_message,
                        "created_at": job.created_at.isoformat() if job.created_at else None,
                        "updated_at": job.updated_at.isoformat() if job.updated_at else None
                    }
                return None
            except Exception as e:
                logger.error(f"Failed to get job {job_id}: {str(e)}")
                raise
    
    def get_jobs_by_user(self, user_id: str) -> list[Job]:
        """Get all jobs for a specific user"""
        with db_config.get_db_session() as db:
            try:
                return db.query(Job).filter(Job.user_id == user_id).order_by(Job.created_at.desc()).all()
            except Exception as e:
                logger.error(f"Failed to get jobs for user {user_id}: {str(e)}")
                raise
    
    def get_jobs_by_status(self, status: str) -> list[Job]:
        """Get all jobs with a specific status"""
        with db_config.get_db_session() as db:
            try:
                return db.query(Job).filter(Job.status == status).order_by(Job.created_at.desc()).all()
            except Exception as e:
                logger.error(f"Failed to get jobs with status {status}: {str(e)}")
                raise 