#!/usr/bin/env python3
"""
LangGraph Research & Content Generation Workflows
Uses LangGraph to create intelligent research and content generation workflows.
"""

import asyncio
import json
import os
from typing import Dict, List, Optional, Any, TypedDict
from datetime import datetime

import structlog
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from langgraph.graph import StateGraph, END

# Import search tools
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False

logger = structlog.get_logger()

class ResearchState(TypedDict):
    """State for research workflow"""
    query: str
    research_type: str
    max_sources: int
    include_summary: bool
    sources: List[Dict[str, Any]]
    summaries: List[str]
    final_report: str
    current_step: str
    error: Optional[str]

class ContentState(TypedDict):
    """State for content generation workflow"""
    topic: str
    content_type: str
    tone: str
    length: str
    research_data: Optional[Dict[str, Any]]
    outline: str
    content: str
    current_step: str
    error: Optional[str]

class ResearchGraph:
    """LangGraph-based research and content generation system"""
    
    def __init__(self):
        self.llm = None
        self.search_tools = []
        self.research_workflow = None
        self.content_workflow = None
        
    async def initialize(self):
        """Initialize the research graph with LLM and tools"""
        try:
            # Initialize Google Gemini LLM
            google_api_key = os.getenv("GOOGLE_API_KEY")
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY environment variable is required")
            
            self.llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.1,
                google_api_key=google_api_key
            )
            
            # Initialize search tools
            self._initialize_search_tools()
            
            # Build workflows
            self._build_research_workflow()
            self._build_content_workflow()
            
            logger.info("ResearchGraph initialized successfully with Google Gemini")
            
        except Exception as e:
            logger.error("Failed to initialize ResearchGraph", error=str(e))
            raise
    
    def _initialize_search_tools(self):
        """Initialize available search tools"""
        self.search_tools = []
        
        # DuckDuckGo search (always available)
        try:
            ddg_search = DuckDuckGoSearchRun()
            self.search_tools.append(ddg_search)
            logger.info("DuckDuckGo search tool initialized")
        except Exception as e:
            logger.warning("Failed to initialize DuckDuckGo search", error=str(e))
        
        # Wikipedia search
        try:
            wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
            self.search_tools.append(wikipedia)
            logger.info("Wikipedia search tool initialized")
        except Exception as e:
            logger.warning("Failed to initialize Wikipedia search", error=str(e))
        
        # Tavily search (if available)
        if TAVILY_AVAILABLE:
            tavily_api_key = os.getenv("TAVILY_API_KEY")
            if tavily_api_key:
                try:
                    self.tavily_client = TavilyClient(api_key=tavily_api_key)
                    logger.info("Tavily search client initialized")
                except Exception as e:
                    logger.warning("Failed to initialize Tavily search", error=str(e))
    
    def _build_research_workflow(self):
        """Build the research workflow using LangGraph"""
        workflow = StateGraph(ResearchState)
        
        # Add nodes
        workflow.add_node("plan_research", self._plan_research)
        workflow.add_node("search_sources", self._search_sources)
        workflow.add_node("analyze_sources", self._analyze_sources)
        workflow.add_node("generate_summary", self._generate_summary)
        workflow.add_node("compile_report", self._compile_report)
        
        # Add edges
        workflow.set_entry_point("plan_research")
        workflow.add_edge("plan_research", "search_sources")
        workflow.add_edge("search_sources", "analyze_sources")
        workflow.add_edge("analyze_sources", "generate_summary")
        workflow.add_edge("generate_summary", "compile_report")
        workflow.add_edge("compile_report", END)
        
        self.research_workflow = workflow.compile()
    
    def _build_content_workflow(self):
        """Build the content generation workflow using LangGraph"""
        workflow = StateGraph(ContentState)
        
        # Add nodes
        workflow.add_node("research_topic", self._research_for_content)
        workflow.add_node("create_outline", self._create_content_outline)
        workflow.add_node("generate_content", self._generate_content_body)
        workflow.add_node("refine_content", self._refine_content)
        
        # Add edges
        workflow.set_entry_point("research_topic")
        workflow.add_edge("research_topic", "create_outline")
        workflow.add_edge("create_outline", "generate_content")
        workflow.add_edge("generate_content", "refine_content")
        workflow.add_edge("refine_content", END)
        
        self.content_workflow = workflow.compile()
    
    # Research workflow nodes
    async def _plan_research(self, state: ResearchState) -> ResearchState:
        """Plan the research strategy based on query and type"""
        try:
            query = state["query"]
            research_type = state["research_type"]
            
            planning_prompt = f"""
            You are a research planner. Create a research strategy for the following query:
            Query: {query}
            Research Type: {research_type}
            
            Plan the most effective approach to research this topic. Consider:
            1. What specific aspects should be investigated?
            2. What types of sources would be most valuable?
            3. What search terms would be most effective?
            
            Provide a focused research plan in 2-3 sentences.
            """
            
            response = await self.llm.ainvoke(planning_prompt)
            plan = response.content
            
            logger.info("Research plan created", query=query, plan=plan)
            
            state["current_step"] = "planned"
            return state
            
        except Exception as e:
            logger.error("Research planning failed", error=str(e))
            state["error"] = str(e)
            return state
    
    async def _search_sources(self, state: ResearchState) -> ResearchState:
        """Search for relevant sources using available tools"""
        try:
            query = state["query"]
            max_sources = state["max_sources"]
            sources = []
            
            # Search with DuckDuckGo
            if self.search_tools:
                try:
                    ddg_results = self.search_tools[0].run(query)
                    sources.append({
                        "source": "DuckDuckGo",
                        "content": ddg_results,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.warning("DuckDuckGo search failed", error=str(e))
            
            # Search Wikipedia if available
            if len(self.search_tools) > 1:
                try:
                    wiki_results = self.search_tools[1].run(query)
                    sources.append({
                        "source": "Wikipedia",
                        "content": wiki_results,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.warning("Wikipedia search failed", error=str(e))
            
            # Search with Tavily if available
            if hasattr(self, 'tavily_client'):
                try:
                    tavily_results = self.tavily_client.search(
                        query=query,
                        search_depth="advanced",
                        max_results=3
                    )
                    sources.append({
                        "source": "Tavily",
                        "content": tavily_results,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                except Exception as e:
                    logger.warning("Tavily search failed", error=str(e))
            
            state["sources"] = sources[:max_sources]
            state["current_step"] = "sources_found"
            
            logger.info("Sources found", query=query, source_count=len(sources))
            return state
            
        except Exception as e:
            logger.error("Source search failed", error=str(e))
            state["error"] = str(e)
            return state
    
    async def _analyze_sources(self, state: ResearchState) -> ResearchState:
        """Analyze and extract key information from sources"""
        try:
            query = state["query"]
            sources = state["sources"]
            summaries = []
            
            for source in sources:
                analysis_prompt = f"""
                Analyze the following source for information relevant to: {query}
                
                Source: {source['source']}
                Content: {source['content'][:2000]}...
                
                Extract the most important and relevant information. Focus on:
                1. Key facts and data points
                2. Important insights or conclusions
                3. Credible details that answer the query
                
                Provide a concise summary (2-3 paragraphs):
                """
                
                response = await self.llm.ainvoke(analysis_prompt)
                summary = response.content
                
                summaries.append({
                    "source": source["source"],
                    "summary": summary,
                    "timestamp": source["timestamp"]
                })
            
            state["summaries"] = summaries
            state["current_step"] = "sources_analyzed"
            
            logger.info("Sources analyzed", query=query, summary_count=len(summaries))
            return state
            
        except Exception as e:
            logger.error("Source analysis failed", error=str(e))
            state["error"] = str(e)
            return state
    
    async def _generate_summary(self, state: ResearchState) -> ResearchState:
        """Generate a comprehensive summary from analyzed sources"""
        try:
            query = state["query"]
            summaries = state["summaries"]
            include_summary = state["include_summary"]
            
            if not include_summary:
                state["current_step"] = "summary_skipped"
                return state
            
            # Combine all summaries
            combined_info = "\n\n".join([
                f"From {s['source']}:\n{s['summary']}" 
                for s in summaries
            ])
            
            summary_prompt = f"""
            Based on the research conducted for: {query}
            
            Research findings:
            {combined_info}
            
            Create a comprehensive, well-structured summary that:
            1. Directly addresses the original query
            2. Synthesizes information from multiple sources
            3. Highlights the most important findings
            4. Provides actionable insights where appropriate
            5. Maintains accuracy and cites source variety
            
            Structure the summary with clear sections and bullet points where helpful.
            """
            
            response = await self.llm.ainvoke(summary_prompt)
            final_summary = response.content
            
            state["final_report"] = final_summary
            state["current_step"] = "summary_generated"
            
            logger.info("Summary generated", query=query)
            return state
            
        except Exception as e:
            logger.error("Summary generation failed", error=str(e))
            state["error"] = str(e)
            return state
    
    async def _compile_report(self, state: ResearchState) -> ResearchState:
        """Compile final research report"""
        try:
            query = state["query"]
            research_type = state["research_type"]
            sources = state["sources"]
            summaries = state["summaries"]
            final_summary = state.get("final_report", "")
            
            # Create comprehensive report
            report = {
                "query": query,
                "research_type": research_type,
                "timestamp": datetime.utcnow().isoformat(),
                "summary": final_summary,
                "sources_used": len(sources),
                "detailed_findings": summaries,
                "methodology": "LangGraph-powered multi-source research with Google Gemini AI analysis",
                "confidence": "High" if len(sources) >= 2 else "Medium"
            }
            
            state["final_report"] = report
            state["current_step"] = "completed"
            
            logger.info("Research report compiled", query=query)
            return state
            
        except Exception as e:
            logger.error("Report compilation failed", error=str(e))
            state["error"] = str(e)
            return state
    
    # Content generation workflow nodes
    async def _research_for_content(self, state: ContentState) -> ContentState:
        """Research the topic for content generation"""
        try:
            topic = state["topic"]
            
            # Use research workflow for background information
            research_state = {
                "query": f"comprehensive information about {topic}",
                "research_type": "quick",
                "max_sources": 3,
                "include_summary": True,
                "sources": [],
                "summaries": [],
                "final_report": "",
                "current_step": "starting",
                "error": None
            }
            
            # Run mini research
            research_result = await self.research_workflow.ainvoke(research_state)
            
            state["research_data"] = research_result.get("final_report", {})
            state["current_step"] = "research_completed"
            
            logger.info("Content research completed", topic=topic)
            return state
            
        except Exception as e:
            logger.error("Content research failed", error=str(e))
            state["error"] = str(e)
            return state
    
    async def _create_content_outline(self, state: ContentState) -> ContentState:
        """Create an outline for the content"""
        try:
            topic = state["topic"]
            content_type = state["content_type"]
            tone = state["tone"]
            length = state["length"]
            research_data = state.get("research_data", {})
            
            outline_prompt = f"""
            Create a detailed outline for {content_type} about: {topic}
            
            Requirements:
            - Tone: {tone}
            - Length: {length}
            - Content Type: {content_type}
            
            Background Research:
            {research_data.get('summary', 'No specific research data available')[:1000]}
            
            Create a clear, logical outline with:
            1. Compelling introduction
            2. 3-5 main sections with subsections
            3. Strong conclusion
            4. Appropriate call-to-action (if applicable)
            
            Format as a structured outline with bullet points.
            """
            
            response = await self.llm.ainvoke(outline_prompt)
            outline = response.content
            
            state["outline"] = outline
            state["current_step"] = "outline_created"
            
            logger.info("Content outline created", topic=topic)
            return state
            
        except Exception as e:
            logger.error("Outline creation failed", error=str(e))
            state["error"] = str(e)
            return state
    
    async def _generate_content_body(self, state: ContentState) -> ContentState:
        """Generate the main content body"""
        try:
            topic = state["topic"]
            content_type = state["content_type"]
            tone = state["tone"]
            length = state["length"]
            outline = state["outline"]
            research_data = state.get("research_data", {})
            
            content_prompt = f"""
            Write a complete {content_type} about: {topic}
            
            Requirements:
            - Tone: {tone}
            - Length: {length}
            - Follow this outline: {outline}
            
            Background Information:
            {research_data.get('summary', '')[:1500]}
            
            Write engaging, informative content that:
            1. Captures attention from the start
            2. Provides valuable information
            3. Maintains the specified tone throughout
            4. Includes relevant examples where appropriate
            5. Ends with a strong conclusion
            
            Make it comprehensive but readable. Use formatting like headers, bullet points, and paragraphs appropriately.
            """
            
            response = await self.llm.ainvoke(content_prompt)
            content = response.content
            
            state["content"] = content
            state["current_step"] = "content_generated"
            
            logger.info("Content body generated", topic=topic, content_length=len(content))
            return state
            
        except Exception as e:
            logger.error("Content generation failed", error=str(e))
            state["error"] = str(e)
            return state
    
    async def _refine_content(self, state: ContentState) -> ContentState:
        """Refine and polish the content"""
        try:
            topic = state["topic"]
            content = state["content"]
            tone = state["tone"]
            content_type = state["content_type"]
            
            refinement_prompt = f"""
            Review and refine this {content_type} about {topic}:
            
            {content}
            
            Improve it by:
            1. Enhancing clarity and readability
            2. Ensuring consistent {tone} tone
            3. Adding transitions between sections
            4. Checking for completeness
            5. Polishing language and flow
            
            Return the refined version that's ready for publication.
            """
            
            response = await self.llm.ainvoke(refinement_prompt)
            refined_content = response.content
            
            # Create final content package
            final_content = {
                "title": f"{content_type.title()} about {topic}",
                "content": refined_content,
                "outline": state["outline"],
                "metadata": {
                    "topic": topic,
                    "content_type": content_type,
                    "tone": tone,
                    "length": state["length"],
                    "word_count": len(refined_content.split()),
                    "generated_at": datetime.utcnow().isoformat(),
                    "ai_model": "Google Gemini Pro"
                },
                "research_sources": state.get("research_data", {}).get("sources_used", 0)
            }
            
            state["content"] = final_content
            state["current_step"] = "completed"
            
            logger.info("Content refined and completed", topic=topic)
            return state
            
        except Exception as e:
            logger.error("Content refinement failed", error=str(e))
            state["error"] = str(e)
            return state
    
    # Public methods
    async def research_topic(self, query: str, research_type: str = "comprehensive", 
                           max_sources: int = 5, include_summary: bool = True) -> Dict[str, Any]:
        """Research a topic using the LangGraph workflow"""
        try:
            initial_state = {
                "query": query,
                "research_type": research_type,
                "max_sources": max_sources,
                "include_summary": include_summary,
                "sources": [],
                "summaries": [],
                "final_report": "",
                "current_step": "starting",
                "error": None
            }
            
            result = await self.research_workflow.ainvoke(initial_state)
            
            if result.get("error"):
                raise Exception(result["error"])
            
            return result["final_report"]
            
        except Exception as e:
            logger.error("Research workflow failed", query=query, error=str(e))
            raise
    
    async def generate_content(self, topic: str, content_type: str = "article", 
                             tone: str = "professional", length: str = "medium") -> Dict[str, Any]:
        """Generate content using the LangGraph workflow"""
        try:
            initial_state = {
                "topic": topic,
                "content_type": content_type,
                "tone": tone,
                "length": length,
                "research_data": None,
                "outline": "",
                "content": "",
                "current_step": "starting",
                "error": None
            }
            
            result = await self.content_workflow.ainvoke(initial_state)
            
            if result.get("error"):
                raise Exception(result["error"])
            
            return result["content"]
            
        except Exception as e:
            logger.error("Content generation workflow failed", topic=topic, error=str(e))
            raise 