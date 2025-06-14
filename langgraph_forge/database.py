#!/usr/bin/env python3
"""
Database module for LangGraph Research & Content Assistant
Handles job tracking and data persistence.
"""

import asyncio
import json
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

import structlog
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

logger = structlog.get_logger()

Base = declarative_base()

class ResearchJob(Base):
    """Database model for research and content generation jobs"""
    __tablename__ = "research_jobs"
    
    job_id = Column(String, primary_key=True)
    request_type = Column(String, nullable=False)  # research, content_generation, vapi_research, etc.
    status = Column(String, nullable=False, default="created")  # created, running, processing, completed, failed
    input_data = Column(JSON, nullable=False)
    result = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

class Database:
    """Database manager for the LangGraph Research Assistant"""
    
    def __init__(self):
        self.engine = None
        self.async_session = None
        
    async def init_db(self):
        """Initialize the database connection and create tables"""
        try:
            # Use SQLite for simplicity (can be changed to PostgreSQL later)
            database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./langgraph_research.db")
            
            self.engine = create_async_engine(
                database_url,
                echo=False,
                future=True
            )
            
            self.async_session = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database initialized successfully", database_url=database_url)
            
        except Exception as e:
            logger.error("Failed to initialize database", error=str(e))
            raise
    
    async def create_job(self, job_id: str, request_type: str, input_data: Dict[str, Any], 
                        status: str = "created") -> Dict[str, Any]:
        """Create a new job record"""
        try:
            async with self.async_session() as session:
                job = ResearchJob(
                    job_id=job_id,
                    request_type=request_type,
                    status=status,
                    input_data=input_data
                )
                
                session.add(job)
                await session.commit()
                
                # Return job data as dict
                return {
                    "job_id": job.job_id,
                    "request_type": job.request_type,
                    "status": job.status,
                    "input_data": job.input_data,
                    "result": job.result,
                    "error_message": job.error_message,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at
                }
                
        except Exception as e:
            logger.error("Failed to create job", job_id=job_id, error=str(e))
            raise
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get a job by ID"""
        try:
            async with self.async_session() as session:
                job = await session.get(ResearchJob, job_id)
                
                if not job:
                    return None
                
                return {
                    "job_id": job.job_id,
                    "request_type": job.request_type,
                    "status": job.status,
                    "input_data": job.input_data,
                    "result": job.result,
                    "error_message": job.error_message,
                    "created_at": job.created_at,
                    "updated_at": job.updated_at
                }
                
        except Exception as e:
            logger.error("Failed to get job", job_id=job_id, error=str(e))
            raise
    
    async def update_job_status(self, job_id: str, status: str, error_message: Optional[str] = None):
        """Update job status"""
        try:
            async with self.async_session() as session:
                job = await session.get(ResearchJob, job_id)
                
                if job:
                    job.status = status
                    job.updated_at = datetime.now(timezone.utc)
                    if error_message:
                        job.error_message = error_message
                    
                    await session.commit()
                    logger.info("Job status updated", job_id=job_id, status=status)
                else:
                    logger.warning("Job not found for status update", job_id=job_id)
                    
        except Exception as e:
            logger.error("Failed to update job status", job_id=job_id, error=str(e))
            raise
    
    async def update_job_result(self, job_id: str, result: Dict[str, Any], status: str = "completed"):
        """Update job with results"""
        try:
            async with self.async_session() as session:
                job = await session.get(ResearchJob, job_id)
                
                if job:
                    job.result = result
                    job.status = status
                    job.updated_at = datetime.now(timezone.utc)
                    
                    await session.commit()
                    logger.info("Job result updated", job_id=job_id, status=status)
                else:
                    logger.warning("Job not found for result update", job_id=job_id)
                    
        except Exception as e:
            logger.error("Failed to update job result", job_id=job_id, error=str(e))
            raise
    
    async def list_jobs(self, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """List jobs with pagination"""
        try:
            async with self.async_session() as session:
                from sqlalchemy import select
                
                stmt = select(ResearchJob).order_by(ResearchJob.created_at.desc()).limit(limit).offset(offset)
                result = await session.execute(stmt)
                jobs = result.scalars().all()
                
                return [
                    {
                        "job_id": job.job_id,
                        "request_type": job.request_type,
                        "status": job.status,
                        "input_data": job.input_data,
                        "result": job.result,
                        "error_message": job.error_message,
                        "created_at": job.created_at,
                        "updated_at": job.updated_at
                    }
                    for job in jobs
                ]
                
        except Exception as e:
            logger.error("Failed to list jobs", error=str(e))
            raise
    
    async def count_active_jobs(self) -> int:
        """Count active (running/processing) jobs"""
        try:
            async with self.async_session() as session:
                from sqlalchemy import select, func
                
                stmt = select(func.count(ResearchJob.job_id)).where(
                    ResearchJob.status.in_(["running", "processing", "created"])
                )
                result = await session.execute(stmt)
                count = result.scalar() or 0
                
                return count
                
        except Exception as e:
            logger.error("Failed to count active jobs", error=str(e))
            return 0
    
    async def cleanup_old_jobs(self, days_old: int = 30):
        """Clean up old completed jobs"""
        try:
            async with self.async_session() as session:
                from sqlalchemy import delete
                from datetime import timedelta
                
                cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_old)
                
                stmt = delete(ResearchJob).where(
                    ResearchJob.created_at < cutoff_date,
                    ResearchJob.status.in_(["completed", "failed"])
                )
                
                result = await session.execute(stmt)
                await session.commit()
                
                deleted_count = result.rowcount
                logger.info("Cleaned up old jobs", deleted_count=deleted_count, days_old=days_old)
                
                return deleted_count
                
        except Exception as e:
            logger.error("Failed to cleanup old jobs", error=str(e))
            return 0 