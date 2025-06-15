#!/usr/bin/env python3
"""
LangGraph Research & Content Assistant
A conversational AI server that can research topics, summarize content, and generate intelligent responses.
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

import structlog
import uvicorn
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from research_graph import ResearchGraph
from config_manager import ConfigManager
from database import Database, ResearchJob

# Configure basic Python logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="ISO"),
        structlog.dev.ConsoleRenderer(colors=True)  # Use console renderer instead of JSON
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize components
config_manager = ConfigManager()
database = Database()
research_graph = ResearchGraph()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    logger.info("🚀 Starting LangGraph Research & Content Assistant")
    
    # Initialize database
    await database.init_db()
    
    # Initialize research graph
    await research_graph.initialize()
    
    logger.info("✅ LangGraph Research Assistant ready!")
    
    yield
    
    logger.info("🔄 Shutting down LangGraph Research Assistant")

app = FastAPI(
    title="LangGraph Research & Content Assistant",
    description="A conversational AI server for research, content generation, and intelligent assistance",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class ResearchRequest(BaseModel):
    query: str = Field(..., description="The research query or question")
    research_type: str = Field(default="comprehensive", description="Type of research: comprehensive, quick, deep")
    max_sources: int = Field(default=5, description="Maximum number of sources to research")
    include_summary: bool = Field(default=True, description="Whether to include a summary")

class ContentRequest(BaseModel):
    topic: str = Field(..., description="The topic for content generation")
    content_type: str = Field(default="article", description="Type of content: article, blog, summary, report")
    tone: str = Field(default="professional", description="Tone: professional, casual, academic, creative")
    length: str = Field(default="medium", description="Length: short, medium, long")

class VapiWebhookRequest(BaseModel):
    message: Dict[str, Any] = Field(..., description="The message from Vapi")
    call: Optional[Dict[str, Any]] = Field(None, description="Call information")

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime
    updated_at: datetime
    request_type: str
    input_data: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "LangGraph Research & Content Assistant",
        "version": "1.0.0",
        "status": "running",
        "capabilities": [
            "Research & Information Gathering",
            "Content Generation",
            "Document Summarization",
            "Question Answering",
            "Voice Assistant Integration"
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        active_jobs = await database.count_active_jobs()
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected",
            "active_jobs": active_jobs,
            "research_graph": "ready"
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@app.post("/research")
async def research_topic(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Research a topic and provide comprehensive information"""
    job_id = str(uuid.uuid4())
    
    logger.info("Starting research job", job_id=job_id, query=request.query)
    
    try:
        # Create job record
        job = await database.create_job(
            job_id=job_id,
            request_type="research",
            input_data=request.dict(),
            status="running"
        )
        
        # Start research in background
        background_tasks.add_task(
            run_research_job,
            job_id,
            request
        )
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": f"Research job started for: {request.query}",
            "estimated_time": "30-60 seconds"
        }
        
    except Exception as e:
        logger.error("Failed to start research job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start research: {str(e)}")

@app.post("/generate-content")
async def generate_content(request: ContentRequest, background_tasks: BackgroundTasks):
    """Generate content based on a topic"""
    job_id = str(uuid.uuid4())
    
    logger.info("Starting content generation job", job_id=job_id, topic=request.topic)
    
    try:
        # Create job record
        job = await database.create_job(
            job_id=job_id,
            request_type="content_generation",
            input_data=request.dict(),
            status="running"
        )
        
        # Start content generation in background
        background_tasks.add_task(
            run_content_generation_job,
            job_id,
            request
        )
        
        return {
            "job_id": job_id,
            "status": "started",
            "message": f"Content generation started for: {request.topic}",
            "estimated_time": "20-40 seconds"
        }
        
    except Exception as e:
        logger.error("Failed to start content generation job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start content generation: {str(e)}")

@app.post("/vapi-webhook")
async def vapi_webhook(request: VapiWebhookRequest, background_tasks: BackgroundTasks):
    """Handle Vapi webhook requests with immediate responses for cost efficiency"""
    try:
        message = request.message
        message_type = message.get("type", "unknown")
        
        logger.info("Received Vapi webhook", message_type=message_type)
        
        if message_type == "function-call":
            # Handle function calls from Vapi with immediate responses
            function_call = message.get("functionCall", {})
            function_name = function_call.get("name", "")
            
            if function_name == "research_topic":
                parameters = function_call.get("parameters", {})
                
                # Force quick research for voice calls to avoid long wait times
                parameters["research_type"] = "quick"
                parameters["max_sources"] = min(parameters.get("max_sources", 2), 2)
                
                research_request = ResearchRequest(**parameters)
                
                # Use quick research endpoint for immediate response
                result = await quick_research(research_request)
                
                if result.get("type") == "error":
                    return {
                        "result": result["summary"]
                    }
                else:
                    return {
                        "result": f"Here's what I found about {result['query']}: {result['summary']}"
                    }
                
            elif function_name == "generate_content":
                parameters = function_call.get("parameters", {})
                
                # Force shorter content for voice calls
                parameters["length"] = "short" if parameters.get("length") == "long" else parameters.get("length", "short")
                
                content_request = ContentRequest(**parameters)
                
                # Use quick content endpoint for immediate response
                result = await quick_content(content_request)
                
                if result.get("type") == "error":
                    return {
                        "result": result["content"]
                    }
                else:
                    # Return a summary of the content for voice delivery
                    content_text = result["content"]
                    if not isinstance(content_text, str):
                        content_text = str(content_text)
                    content_preview = content_text[:300] + "..." if len(content_text) > 300 else content_text
                    return {
                        "result": f"I've created {result['content_type']} content about {result['topic']}. Here's a preview: {content_preview}"
                    }
            
            else:
                return {
                    "result": f"I don't recognize the function '{function_name}'. I can help with research_topic or generate_content.",
                    "error": "unknown_function"
                }
        
        else:
            # Handle other message types with quick response
            return {
                "result": "Hello! I'm your Research & Content Assistant. I can quickly research topics or generate content for you. What would you like to explore?",
                "capabilities": ["Quick research", "Content generation", "Immediate answers"]
            }
            
    except Exception as e:
        logger.error("Vapi webhook error", error=str(e))
        return {
            "result": f"I encountered an error: {str(e)}. Please try again or rephrase your request.",
            "error": "processing_error"
        }

@app.get("/job-status/{job_id}")
async def get_job_status(job_id: str) -> JobStatusResponse:
    """Get the status of a research or content generation job"""
    try:
        job = await database.get_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobStatusResponse(**job)
        
    except Exception as e:
        logger.error("Failed to get job status", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get job status: {str(e)}")

@app.get("/jobs")
async def list_jobs(limit: int = 10, offset: int = 0):
    """List recent jobs"""
    try:
        jobs = await database.list_jobs(limit=limit, offset=offset)
        return {"jobs": jobs, "total": len(jobs)}
    except Exception as e:
        logger.error("Failed to list jobs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list jobs: {str(e)}")

@app.get("/jobs/search")
async def search_jobs(
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    query: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """Search and filter jobs with advanced criteria"""
    try:
        async with database.async_session() as session:
            from sqlalchemy import select, and_, or_
            
            # Build dynamic query
            conditions = []
            
            if status:
                conditions.append(ResearchJob.status == status)
            
            if request_type:
                conditions.append(ResearchJob.request_type == request_type)
            
            if query:
                # Search in input_data JSON and error_message
                conditions.append(
                    or_(
                        ResearchJob.input_data.contains(query),
                        ResearchJob.error_message.contains(query) if ResearchJob.error_message else False
                    )
                )
            
            # Build the query
            stmt = select(ResearchJob).order_by(ResearchJob.created_at.desc())
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            stmt = stmt.limit(limit).offset(offset)
            
            result = await session.execute(stmt)
            jobs = result.scalars().all()
            
            # Convert to dict format
            job_list = [
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
            
            return {
                "jobs": job_list,
                "total": len(job_list),
                "filters": {
                    "status": status,
                    "request_type": request_type,
                    "query": query
                },
                "pagination": {
                    "limit": limit,
                    "offset": offset
                }
            }
            
    except Exception as e:
        logger.error("Failed to search jobs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to search jobs: {str(e)}")

@app.get("/jobs/analytics")
async def get_job_analytics():
    """Get comprehensive analytics about jobs"""
    try:
        async with database.async_session() as session:
            from sqlalchemy import select, func, case
            from datetime import timedelta
            
            # Get total counts by status
            status_counts = await session.execute(
                select(
                    ResearchJob.status,
                    func.count(ResearchJob.job_id).label('count')
                ).group_by(ResearchJob.status)
            )
            
            status_stats = {row.status: row.count for row in status_counts}
            
            # Get counts by request type
            type_counts = await session.execute(
                select(
                    ResearchJob.request_type,
                    func.count(ResearchJob.job_id).label('count')
                ).group_by(ResearchJob.request_type)
            )
            
            type_stats = {row.request_type: row.count for row in type_counts}
            
            # Get recent activity (last 24 hours)
            recent_cutoff = datetime.utcnow() - timedelta(hours=24)
            recent_jobs = await session.execute(
                select(func.count(ResearchJob.job_id)).where(
                    ResearchJob.created_at >= recent_cutoff
                )
            )
            
            recent_count = recent_jobs.scalar() or 0
            
            # Get success rate
            total_completed = await session.execute(
                select(func.count(ResearchJob.job_id)).where(
                    ResearchJob.status.in_(["completed", "failed"])
                )
            )
            
            total_finished = total_completed.scalar() or 0
            completed_count = status_stats.get("completed", 0)
            success_rate = (completed_count / total_finished * 100) if total_finished > 0 else 0
            
            # Get average processing time for completed jobs
            avg_time_query = await session.execute(
                select(
                    func.avg(
                        func.julianday(ResearchJob.updated_at) - func.julianday(ResearchJob.created_at)
                    ).label('avg_days')
                ).where(ResearchJob.status == "completed")
            )
            
            avg_days = avg_time_query.scalar() or 0
            avg_minutes = avg_days * 24 * 60  # Convert days to minutes
            
            return {
                "summary": {
                    "total_jobs": sum(status_stats.values()),
                    "active_jobs": status_stats.get("running", 0) + status_stats.get("processing", 0),
                    "success_rate": f"{success_rate:.1f}%",
                    "recent_24h": recent_count,
                    "avg_processing_time_minutes": f"{avg_minutes:.1f}"
                },
                "status_breakdown": status_stats,
                "request_type_breakdown": type_stats,
                "performance_metrics": {
                    "completed": status_stats.get("completed", 0),
                    "failed": status_stats.get("failed", 0),
                    "running": status_stats.get("running", 0),
                    "processing": status_stats.get("processing", 0)
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error("Failed to get job analytics", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")

@app.delete("/jobs/{job_id}")
async def delete_job(job_id: str):
    """Delete a specific job"""
    try:
        async with database.async_session() as session:
            job = await session.get(ResearchJob, job_id)
            
            if not job:
                raise HTTPException(status_code=404, detail="Job not found")
            
            # Only allow deletion of completed or failed jobs
            if job.status in ["running", "processing"]:
                raise HTTPException(
                    status_code=400, 
                    detail="Cannot delete running jobs. Please wait for completion or cancel first."
                )
            
            await session.delete(job)
            await session.commit()
            
            logger.info("Job deleted", job_id=job_id)
            
            return {
                "message": f"Job {job_id} deleted successfully",
                "job_id": job_id,
                "status": "deleted"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to delete job", job_id=job_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete job: {str(e)}")

@app.post("/jobs/cleanup")
async def cleanup_old_jobs(days_old: int = 30):
    """Clean up old completed and failed jobs"""
    try:
        deleted_count = await database.cleanup_old_jobs(days_old)
        
        return {
            "message": f"Cleaned up {deleted_count} old jobs",
            "deleted_count": deleted_count,
            "days_old": days_old,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Failed to cleanup jobs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to cleanup jobs: {str(e)}")

@app.get("/jobs/export")
async def export_jobs(
    format: str = "json",
    status: Optional[str] = None,
    request_type: Optional[str] = None,
    limit: int = 100
):
    """Export jobs data in different formats"""
    try:
        # Get jobs with optional filtering
        async with database.async_session() as session:
            from sqlalchemy import select, and_
            
            conditions = []
            if status:
                conditions.append(ResearchJob.status == status)
            if request_type:
                conditions.append(ResearchJob.request_type == request_type)
            
            stmt = select(ResearchJob).order_by(ResearchJob.created_at.desc()).limit(limit)
            
            if conditions:
                stmt = stmt.where(and_(*conditions))
            
            result = await session.execute(stmt)
            jobs = result.scalars().all()
            
            # Convert to exportable format
            export_data = []
            for job in jobs:
                export_data.append({
                    "job_id": job.job_id,
                    "request_type": job.request_type,
                    "status": job.status,
                    "input_data": job.input_data,
                    "result": job.result,
                    "error_message": job.error_message,
                    "created_at": job.created_at.isoformat() if job.created_at else None,
                    "updated_at": job.updated_at.isoformat() if job.updated_at else None
                })
            
            if format.lower() == "csv":
                # For CSV, flatten the data structure
                import csv
                import io
                
                output = io.StringIO()
                if export_data:
                    fieldnames = ["job_id", "request_type", "status", "created_at", "updated_at", "error_message"]
                    writer = csv.DictWriter(output, fieldnames=fieldnames)
                    writer.writeheader()
                    
                    for job in export_data:
                        # Flatten for CSV
                        csv_row = {
                            "job_id": job["job_id"],
                            "request_type": job["request_type"],
                            "status": job["status"],
                            "created_at": job["created_at"],
                            "updated_at": job["updated_at"],
                            "error_message": job["error_message"]
                        }
                        writer.writerow(csv_row)
                
                return {
                    "format": "csv",
                    "data": output.getvalue(),
                    "total_records": len(export_data)
                }
            
            else:  # Default to JSON
                return {
                    "format": "json",
                    "data": export_data,
                    "total_records": len(export_data),
                    "export_timestamp": datetime.utcnow().isoformat()
                }
                
    except Exception as e:
        logger.error("Failed to export jobs", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to export jobs: {str(e)}")

@app.post("/quick-research")
async def quick_research(request: ResearchRequest):
    """Quick research with immediate response (for voice calls)"""
    import time
    start_time = time.time()
    
    try:
        # Force quick research mode for this endpoint
        request.research_type = "quick"
        
        print(f"🔍 QUICK RESEARCH STARTED: {request.query} at {datetime.utcnow().isoformat()}")
        logger.info("🔍 QUICK RESEARCH STARTED", 
                   query=request.query, 
                   research_type=request.research_type,
                   timestamp=datetime.utcnow().isoformat())
        
        # For voice calls, provide immediate brief research
        if request.research_type == "quick":
            print("📋 QUICK RESEARCH MODE - Using DuckDuckGo + Gemini")
            logger.info("📋 QUICK RESEARCH MODE - Using DuckDuckGo + Gemini")
            
            # Use only DuckDuckGo for fast results
            from langchain_community.tools import DuckDuckGoSearchRun
            
            print("🔧 Initializing DuckDuckGo search tool...")
            logger.info("🔧 Initializing DuckDuckGo search tool...")
            search_tool = DuckDuckGoSearchRun()
            
            print(f"🌐 Starting DuckDuckGo search for: {request.query}")
            logger.info("🌐 Starting DuckDuckGo search...", query=request.query)
            search_start = time.time()
            
            try:
                search_results = search_tool.run(request.query)
                search_time = time.time() - search_start
                
                print(f"✅ DuckDuckGo search completed in {search_time:.2f}s, results length: {len(str(search_results))}")
                logger.info("✅ DuckDuckGo search completed", 
                           search_time_seconds=f"{search_time:.2f}",
                           results_length=len(str(search_results)),
                           results_preview=str(search_results)[:200] + "...")
                
            except Exception as search_error:
                print(f"❌ DuckDuckGo search failed: {str(search_error)}")
                logger.error("❌ DuckDuckGo search failed", error=str(search_error))
                search_results = f"Search failed: {str(search_error)}"
            
            # Quick AI summary
            print("🤖 Starting AI summary generation with Google Gemini...")
            logger.info("🤖 Starting AI summary generation with Google Gemini...")
            ai_start = time.time()
            
            summary_prompt = f"""
            Based on this search result about "{request.query}":
            
            {str(search_results)[:1500]}
            
            Provide a concise, informative summary in 2-3 sentences that directly answers the query.
            Focus on the most important facts and insights.
            """
            
            print(f"📝 AI Prompt prepared, length: {len(summary_prompt)}")
            logger.info("📝 AI Prompt prepared", prompt_length=len(summary_prompt))
            
            try:
                response = await research_graph.llm.ainvoke(summary_prompt)
                quick_summary = response.content
                ai_time = time.time() - ai_start
                
                print(f"✅ AI summary generated in {ai_time:.2f}s, length: {len(quick_summary)}")
                logger.info("✅ AI summary generated", 
                           ai_time_seconds=f"{ai_time:.2f}",
                           summary_length=len(quick_summary),
                           summary_preview=quick_summary[:100] + "...")
                
            except Exception as ai_error:
                print(f"❌ AI summary generation failed: {str(ai_error)}")
                logger.error("❌ AI summary generation failed", error=str(ai_error))
                quick_summary = f"AI processing failed: {str(ai_error)}"
            
            total_time = time.time() - start_time
            
            result = {
                "query": request.query,
                "summary": quick_summary,
                "source": "DuckDuckGo + Google Gemini",
                "response_time": "immediate",
                "type": "quick_research",
                "processing_time_seconds": f"{total_time:.2f}",
                "search_time_seconds": f"{search_time:.2f}" if 'search_time' in locals() else "failed",
                "ai_time_seconds": f"{ai_time:.2f}" if 'ai_time' in locals() else "failed"
            }
            
            print(f"🎉 QUICK RESEARCH COMPLETED in {total_time:.2f}s for query: {request.query}")
            logger.info("🎉 QUICK RESEARCH COMPLETED", 
                       total_time_seconds=f"{total_time:.2f}",
                       success=True,
                       query=request.query)
            
            return result
            
        else:
            print("📋 COMPREHENSIVE RESEARCH MODE - Using background job")
            logger.info("📋 COMPREHENSIVE RESEARCH MODE - Using background job")
            # For comprehensive research, still use background jobs
            return await research_topic(request, BackgroundTasks())
            
    except Exception as e:
        total_time = time.time() - start_time
        print(f"❌ QUICK RESEARCH FAILED: {str(e)} in {total_time:.2f}s")
        logger.error("❌ QUICK RESEARCH FAILED", 
                    error=str(e), 
                    query=request.query,
                    total_time_seconds=f"{total_time:.2f}",
                    error_type=type(e).__name__)
        
        return {
            "query": request.query,
            "summary": f"I encountered an issue researching '{request.query}'. Could you try rephrasing your question?",
            "error": str(e),
            "type": "error",
            "processing_time_seconds": f"{total_time:.2f}"
        }

@app.post("/quick-content")
async def quick_content(request: ContentRequest):
    """Quick content generation with immediate response (for voice calls)"""
    try:
        logger.info("Quick content request", topic=request.topic)
        
        # For voice calls, generate shorter content immediately
        if request.length in ["short", "medium"]:
            content_prompt = f"""
            Create a {request.content_type} about "{request.topic}" with the following requirements:
            - Tone: {request.tone}
            - Length: {request.length} (keep it concise for voice delivery)
            - Make it engaging and informative
            - Structure it clearly with key points
            
            Focus on the most important information that would be valuable in a conversation.
            """
            
            response = await research_graph.llm.ainvoke(content_prompt)
            content = response.content
            
            return {
                "topic": request.topic,
                "content": content,
                "content_type": request.content_type,
                "tone": request.tone,
                "word_count": len(content.split()),
                "response_time": "immediate",
                "type": "quick_content"
            }
        else:
            # For long content, use background jobs
            return await generate_content(request, BackgroundTasks())
            
    except Exception as e:
        logger.error("Quick content generation failed", error=str(e))
        return {
            "topic": request.topic,
            "content": f"I had trouble generating content about '{request.topic}'. Could you provide more specific details?",
            "error": str(e),
            "type": "error"
        }

async def run_research_job(job_id: str, request: ResearchRequest):
    """Background task to run research job"""
    import time
    start_time = time.time()
    
    try:
        logger.info("🔬 COMPREHENSIVE RESEARCH JOB STARTED", 
                   job_id=job_id,
                   query=request.query,
                   research_type=request.research_type,
                   max_sources=request.max_sources,
                   include_summary=request.include_summary,
                   timestamp=datetime.utcnow().isoformat())
        
        # Update job status
        logger.info("📊 Updating job status to 'processing'", job_id=job_id)
        await database.update_job_status(job_id, "processing")
        
        # Run research using LangGraph
        logger.info("🔍 Starting LangGraph research workflow...", job_id=job_id)
        research_start = time.time()
        
        try:
            result = await research_graph.research_topic(
                query=request.query,
                research_type=request.research_type,
                max_sources=request.max_sources,
                include_summary=request.include_summary
            )
            
            research_time = time.time() - research_start
            logger.info("✅ LangGraph research completed", 
                       job_id=job_id,
                       research_time_seconds=f"{research_time:.2f}",
                       result_type=type(result).__name__,
                       result_keys=list(result.keys()) if isinstance(result, dict) else "non-dict")
            
        except Exception as research_error:
            research_time = time.time() - research_start
            logger.error("❌ LangGraph research failed", 
                        job_id=job_id,
                        error=str(research_error),
                        error_type=type(research_error).__name__,
                        research_time_seconds=f"{research_time:.2f}")
            raise research_error
        
        # Update job with results
        logger.info("💾 Saving research results to database...", job_id=job_id)
        db_start = time.time()
        
        try:
            await database.update_job_result(job_id, result, "completed")
            db_time = time.time() - db_start
            
            logger.info("✅ Results saved to database", 
                       job_id=job_id,
                       db_time_seconds=f"{db_time:.2f}")
            
        except Exception as db_error:
            db_time = time.time() - db_start
            logger.error("❌ Failed to save results to database", 
                        job_id=job_id,
                        error=str(db_error),
                        db_time_seconds=f"{db_time:.2f}")
            raise db_error
        
        total_time = time.time() - start_time
        logger.info("🎉 COMPREHENSIVE RESEARCH JOB COMPLETED", 
                   job_id=job_id,
                   total_time_seconds=f"{total_time:.2f}",
                   research_time_seconds=f"{research_time:.2f}",
                   db_time_seconds=f"{db_time:.2f}",
                   success=True)
        
    except Exception as e:
        total_time = time.time() - start_time
        logger.error("❌ COMPREHENSIVE RESEARCH JOB FAILED", 
                    job_id=job_id, 
                    error=str(e),
                    error_type=type(e).__name__,
                    total_time_seconds=f"{total_time:.2f}")
        
        try:
            await database.update_job_status(job_id, "failed", error_message=str(e))
            logger.info("📊 Job status updated to 'failed'", job_id=job_id)
        except Exception as status_error:
            logger.error("❌ Failed to update job status to 'failed'", 
                        job_id=job_id,
                        status_error=str(status_error))

async def run_content_generation_job(job_id: str, request: ContentRequest):
    """Background task to run content generation job"""
    try:
        logger.info("Executing content generation job", job_id=job_id)
        
        # Update job status
        await database.update_job_status(job_id, "processing")
        
        # Generate content using LangGraph
        result = await research_graph.generate_content(
            topic=request.topic,
            content_type=request.content_type,
            tone=request.tone,
            length=request.length
        )
        
        # Update job with results
        await database.update_job_result(job_id, result, "completed")
        
        logger.info("Content generation job completed", job_id=job_id)
        
    except Exception as e:
        logger.error("Content generation job failed", job_id=job_id, error=str(e))
        await database.update_job_status(job_id, "failed", error_message=str(e))

@app.get("/admin/database")
async def view_database(limit: int = 20):
    """Simple database viewer for monitoring (admin endpoint)"""
    try:
        # Get recent jobs with summary stats
        jobs = await database.list_jobs(limit=limit, offset=0)
        
        # Calculate stats
        total_jobs = len(jobs)
        completed_jobs = len([j for j in jobs if j.get('status') == 'completed'])
        failed_jobs = len([j for j in jobs if j.get('status') == 'failed'])
        running_jobs = len([j for j in jobs if j.get('status') in ['running', 'processing']])
        
        # Group by request type
        request_types = {}
        for job in jobs:
            req_type = job.get('request_type', 'unknown')
            request_types[req_type] = request_types.get(req_type, 0) + 1
        
        return {
            "database_stats": {
                "total_jobs": total_jobs,
                "completed": completed_jobs,
                "failed": failed_jobs,
                "running": running_jobs,
                "success_rate": f"{(completed_jobs/total_jobs*100):.1f}%" if total_jobs > 0 else "0%"
            },
            "request_types": request_types,
            "recent_jobs": jobs,
            "database_file": "langgraph_research.db",
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Database viewer failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Database viewer error: {str(e)}")

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8082))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    ) 