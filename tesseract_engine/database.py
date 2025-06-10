from sqlalchemy import create_engine, Column, String, Text, DateTime, JSON
try:
    from sqlalchemy.orm import declarative_base
except ImportError:
    from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import Dict, Any, Optional
import json

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

class DatabaseManager:
    def __init__(self, db_url: str = "sqlite:///tesseract.db"):
        self.engine = create_engine(db_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.Workflow = Workflow  # Make classes accessible to main.py
        self.Job = Job
        
    def init_db(self):
        """Initialize database and seed with default workflows"""
        Base.metadata.create_all(bind=self.engine)
        self._seed_workflows()
    
    def _seed_workflows(self):
        """Seed the database with default workflows"""
        db = self.SessionLocal()
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
        finally:
            db.close()
    
    def get_workflow(self, workflow_name: str) -> Optional[Workflow]:
        """Get a workflow by name"""
        db = self.SessionLocal()
        try:
            return db.query(Workflow).filter(Workflow.name == workflow_name).first()
        finally:
            db.close()
    
    def create_job(self, job_id: str, workflow_name: str, user_id: str, input_params: Dict[str, Any]) -> Job:
        """Create a new job entry"""
        db = self.SessionLocal()
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
            db.refresh(job)
            return job
        finally:
            db.close()
    
    def update_job_status(self, job_id: str, status: str, results: Optional[Dict[str, Any]] = None):
        """Update job status and results"""
        db = self.SessionLocal()
        try:
            job = db.query(Job).filter(Job.job_id == job_id).first()
            if job:
                job.status = status
                if results:
                    job.results = results
                db.commit()
        finally:
            db.close()
    
    def get_job(self, job_id: str) -> Optional[Job]:
        """Get a job by job_id"""
        db = self.SessionLocal()
        try:
            return db.query(Job).filter(Job.job_id == job_id).first()
        finally:
            db.close() 