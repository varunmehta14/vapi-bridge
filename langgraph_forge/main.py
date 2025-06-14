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
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from research_graph import ResearchGraph
from config_manager import ConfigManager
from database import Database, ResearchJob

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.JSONRenderer()
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
                    content_preview = result["content"][:300] + "..." if len(result["content"]) > 300 else result["content"]
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

@app.post("/quick-research")
async def quick_research(request: ResearchRequest):
    """Quick research with immediate response (for voice calls)"""
    try:
        logger.info("Quick research request", query=request.query)
        
        # For voice calls, provide immediate brief research
        if request.research_type == "quick":
            # Use only DuckDuckGo for fast results
            from langchain_community.tools import DuckDuckGoSearchRun
            
            search_tool = DuckDuckGoSearchRun()
            search_results = search_tool.run(request.query)
            
            # Quick AI summary
            summary_prompt = f"""
            Based on this search result about "{request.query}":
            
            {search_results[:1500]}
            
            Provide a concise, informative summary in 2-3 sentences that directly answers the query.
            Focus on the most important facts and insights.
            """
            
            response = await research_graph.llm.ainvoke(summary_prompt)
            quick_summary = response.content
            
            return {
                "query": request.query,
                "summary": quick_summary,
                "source": "DuckDuckGo + Google Gemini",
                "response_time": "immediate",
                "type": "quick_research"
            }
        else:
            # For comprehensive research, still use background jobs
            return await research_topic(request, BackgroundTasks())
            
    except Exception as e:
        logger.error("Quick research failed", error=str(e))
        return {
            "query": request.query,
            "summary": f"I encountered an issue researching '{request.query}'. Could you try rephrasing your question?",
            "error": str(e),
            "type": "error"
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
    try:
        logger.info("Executing research job", job_id=job_id)
        
        # Update job status
        await database.update_job_status(job_id, "processing")
        
        # Run research using LangGraph
        result = await research_graph.research_topic(
            query=request.query,
            research_type=request.research_type,
            max_sources=request.max_sources,
            include_summary=request.include_summary
        )
        
        # Update job with results
        await database.update_job_result(job_id, result, "completed")
        
        logger.info("Research job completed", job_id=job_id)
        
    except Exception as e:
        logger.error("Research job failed", job_id=job_id, error=str(e))
        await database.update_job_status(job_id, "failed", error_message=str(e))

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