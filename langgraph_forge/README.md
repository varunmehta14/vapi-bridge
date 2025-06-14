# LangGraph Research & Content Assistant

An intelligent AI-powered research and content generation system built with LangGraph workflows and Google Gemini. This server provides comprehensive research capabilities and high-quality content creation through voice and API interfaces.

## 🚀 Features

### Research Capabilities
- **Multi-Source Research**: Combines web search, Wikipedia, and academic sources
- **Intelligent Analysis**: Uses LangGraph workflows with Google Gemini to synthesize information
- **Comprehensive Reports**: Generates detailed research summaries with citations
- **Real-time Processing**: Background job processing with status tracking

### Content Generation
- **Multiple Content Types**: Articles, blogs, reports, marketing copy, social media content
- **Tone Adaptation**: Professional, casual, academic, creative, and more
- **Research-Backed**: Automatically researches topics before content creation
- **Quality Refinement**: Multi-step workflow ensures high-quality output

### Voice Integration
- **Vapi Compatible**: Seamless integration with voice assistants
- **Real-time Responses**: Handles voice commands and provides spoken feedback
- **YAML Configuration**: Uses same config format as existing voice systems

## 🏗️ Architecture

### LangGraph Workflows
1. **Research Workflow**: Plan → Search → Analyze → Summarize → Report
2. **Content Workflow**: Research → Outline → Generate → Refine

### Technology Stack
- **LangGraph**: Workflow orchestration and state management
- **Google Gemini**: Advanced AI model for analysis and content generation
- **LangChain**: LLM interactions and tool integrations
- **FastAPI**: Modern async web framework
- **SQLAlchemy**: Database ORM with async support
- **Structured Logging**: Comprehensive observability

## 📋 Prerequisites

- Python 3.11+
- Google Gemini API key
- Optional: Tavily API key for enhanced web search

## 🛠️ Installation

1. **Clone and Setup**:
```bash
cd langgraph_forge
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Environment Configuration**:
```bash
# Copy example environment file
cp env_example.txt .env

# Edit .env file with your API keys
GOOGLE_API_KEY=your_google_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here  # Optional
```

3. **Run the Server**:
```bash
python main.py
# Server starts on http://localhost:8082
```

## 🎯 Usage

### API Endpoints

#### Research Topic
```bash
POST /research
{
  "query": "artificial intelligence trends 2024",
  "research_type": "comprehensive",
  "max_sources": 5,
  "include_summary": true
}
```

#### Generate Content
```bash
POST /generate-content
{
  "topic": "sustainable energy solutions",
  "content_type": "article",
  "tone": "professional",
  "length": "medium"
}
```

#### Job Status
```bash
GET /job-status/{job_id}
```

#### Health Check
```bash
GET /health
```

### Voice Integration

The server handles Vapi webhook requests at `/vapi-webhook` and supports:
- Function calls for research and content generation
- Real-time job status updates
- Natural language responses

### YAML Configuration

Compatible with existing agent builder frontend:

```yaml
assistant:
  name: "Smart Research Assistant"
  model:
    provider: "google"
    model: "gemini-pro"
    system_prompt_template: |
      You are an intelligent Research & Content Assistant...
  voice:
    provider: "playht"
    voiceId: "jennifer-playht"
  firstMessage: "Hello! I'm your Smart Research Assistant..."

tools:
  - name: "research_topic"
    description: "Conduct comprehensive research..."
    parameters:
      type: "object"
      properties:
        query:
          type: "string"
          description: "Research query or topic"
        # ... additional parameters
    action:
      type: "api_call"
      method: "POST"
      url: "http://localhost:8082/research"
      # ... action configuration
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key (required) | - |
| `TAVILY_API_KEY` | Tavily search API key (optional) | - |
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./langgraph_research.db` |
| `PORT` | Server port | `8082` |
| `HOST` | Server host | `0.0.0.0` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Research Types

- **Comprehensive**: Thorough multi-source research (default)
- **Quick**: Fast research with essential information
- **Deep**: Extensive research with detailed analysis

### Content Types

- **Article**: Long-form informative content
- **Blog**: Engaging blog-style posts
- **Report**: Structured analytical reports
- **Summary**: Concise information summaries
- **Marketing**: Promotional and sales content
- **Social**: Social media optimized content
- **Email**: Email marketing content

## 🔄 Integration with Existing System

This server is designed to work seamlessly with the existing voice assistant infrastructure:

1. **Frontend Compatibility**: Uses same YAML configuration format
2. **Port Separation**: Runs on port 8082 (vs 8081 for Tesseract, 8000 for Vapi Forge)
3. **API Consistency**: Follows same patterns as other services
4. **Voice Integration**: Compatible with Vapi webhook system

## 🏃‍♂️ Quick Start Examples

### Research a Topic
```bash
curl -X POST "http://localhost:8082/research" \
     -H "Content-Type: application/json" \
     -d '{
       "query": "quantum computing applications",
       "research_type": "comprehensive",
       "max_sources": 3
     }'
```

### Generate Content
```bash
curl -X POST "http://localhost:8082/generate-content" \
     -H "Content-Type: application/json" \
     -d '{
       "topic": "remote work productivity",
       "content_type": "blog",
       "tone": "casual",
       "length": "medium"
     }'
```

### Check Job Status
```bash
curl "http://localhost:8082/job-status/your-job-id-here"
```

## 🛡️ Error Handling

The system includes comprehensive error handling:
- Database connection failures
- API rate limiting
- Search service timeouts
- LLM generation errors
- Invalid configuration validation

All errors are logged with structured logging for easy debugging.

## 📊 Monitoring

Built-in monitoring includes:
- Job status tracking
- Database health checks
- API response times
- Error rate monitoring
- Resource usage metrics

## 🔮 Future Enhancements

- **Document Upload**: Research from uploaded documents
- **Multi-language Support**: Content in multiple languages
- **Advanced Analytics**: Research trend analysis
- **Integration APIs**: Connect with CRM, content management systems
- **Collaborative Features**: Team research projects
- **Custom Sources**: Add proprietary data sources
- **Multimodal Capabilities**: Leverage Gemini's vision and audio processing

## 🤝 Contributing

This server follows the same patterns as the existing system:
1. Maintain API compatibility
2. Follow structured logging practices
3. Include comprehensive error handling
4. Write type-annotated code
5. Add tests for new features

## 📄 License

Same license as the parent project.

---

**Note**: This is a completely different use case from the workflow automation in Tesseract Engine. While Tesseract focuses on business process automation, this LangGraph server specializes in research, content creation, and knowledge synthesis using Google Gemini's advanced AI capabilities - making it perfect for content creators, researchers, marketers, and anyone needing intelligent information processing. 