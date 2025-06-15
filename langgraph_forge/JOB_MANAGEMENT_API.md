# LangGraph Forge - Job Management API

## Overview

The LangGraph Forge provides comprehensive job management capabilities for tracking research and content generation tasks. This document outlines all available job-related endpoints.

## Database Schema

### ResearchJob Table
```sql
CREATE TABLE research_jobs (
    job_id VARCHAR PRIMARY KEY,
    request_type VARCHAR NOT NULL,  -- research, content_generation, vapi_research, etc.
    status VARCHAR NOT NULL DEFAULT 'created',  -- created, running, processing, completed, failed
    input_data JSON NOT NULL,
    result JSON,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Endpoints

### 1. List Jobs
**GET** `/jobs`

List jobs with pagination.

**Parameters:**
- `limit` (int, optional): Number of jobs to return (default: 10)
- `offset` (int, optional): Number of jobs to skip (default: 0)

**Response:**
```json
{
    "jobs": [
        {
            "job_id": "uuid-string",
            "request_type": "research",
            "status": "completed",
            "input_data": {...},
            "result": {...},
            "error_message": null,
            "created_at": "2024-01-01T12:00:00Z",
            "updated_at": "2024-01-01T12:05:00Z"
        }
    ],
    "total": 25
}
```

### 2. Search Jobs
**GET** `/jobs/search`

Search and filter jobs with advanced criteria.

**Parameters:**
- `status` (string, optional): Filter by job status (created, running, processing, completed, failed)
- `request_type` (string, optional): Filter by request type (research, content_generation, etc.)
- `query` (string, optional): Search in input data and error messages
- `limit` (int, optional): Number of results (default: 20)
- `offset` (int, optional): Pagination offset (default: 0)

**Example:**
```bash
GET /jobs/search?status=completed&request_type=research&limit=10
```

**Response:**
```json
{
    "jobs": [...],
    "total": 15,
    "filters": {
        "status": "completed",
        "request_type": "research",
        "query": null
    },
    "pagination": {
        "limit": 10,
        "offset": 0
    }
}
```

### 3. Job Analytics
**GET** `/jobs/analytics`

Get comprehensive analytics about job performance.

**Response:**
```json
{
    "summary": {
        "total_jobs": 150,
        "active_jobs": 3,
        "success_rate": "92.5%",
        "recent_24h": 12,
        "avg_processing_time_minutes": "2.3"
    },
    "status_breakdown": {
        "completed": 120,
        "failed": 8,
        "running": 2,
        "processing": 1
    },
    "request_type_breakdown": {
        "research": 85,
        "content_generation": 45,
        "vapi_research": 20
    },
    "performance_metrics": {
        "completed": 120,
        "failed": 8,
        "running": 2,
        "processing": 1
    },
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### 4. Get Job Status
**GET** `/job-status/{job_id}`

Get detailed status of a specific job.

**Response:**
```json
{
    "job_id": "uuid-string",
    "status": "completed",
    "created_at": "2024-01-01T12:00:00Z",
    "updated_at": "2024-01-01T12:05:00Z",
    "request_type": "research",
    "input_data": {
        "query": "AI developments",
        "research_type": "comprehensive"
    },
    "result": {
        "summary": "...",
        "sources": [...]
    },
    "error_message": null
}
```

### 5. Delete Job
**DELETE** `/jobs/{job_id}`

Delete a specific job (only completed or failed jobs).

**Response:**
```json
{
    "message": "Job uuid-string deleted successfully",
    "job_id": "uuid-string",
    "status": "deleted"
}
```

**Error Cases:**
- `404`: Job not found
- `400`: Cannot delete running jobs

### 6. Export Jobs
**GET** `/jobs/export`

Export jobs data in different formats.

**Parameters:**
- `format` (string, optional): Export format - "json" or "csv" (default: json)
- `status` (string, optional): Filter by status
- `request_type` (string, optional): Filter by request type
- `limit` (int, optional): Maximum records to export (default: 100)

**Example:**
```bash
GET /jobs/export?format=csv&status=completed&limit=50
```

**JSON Response:**
```json
{
    "format": "json",
    "data": [...],
    "total_records": 45,
    "export_timestamp": "2024-01-01T12:00:00Z"
}
```

**CSV Response:**
```json
{
    "format": "csv",
    "data": "job_id,request_type,status,created_at,updated_at,error_message\n...",
    "total_records": 45
}
```

### 7. Cleanup Old Jobs
**POST** `/jobs/cleanup`

Clean up old completed and failed jobs.

**Parameters:**
- `days_old` (int, optional): Delete jobs older than this many days (default: 30)

**Example:**
```bash
POST /jobs/cleanup?days_old=60
```

**Response:**
```json
{
    "message": "Cleaned up 25 old jobs",
    "deleted_count": 25,
    "days_old": 60,
    "timestamp": "2024-01-01T12:00:00Z"
}
```

### 8. Admin Database View
**GET** `/admin/database`

Administrative view of database statistics and recent jobs.

**Parameters:**
- `limit` (int, optional): Number of recent jobs to include (default: 20)

**Response:**
```json
{
    "database_stats": {
        "total_jobs": 150,
        "completed": 120,
        "failed": 8,
        "running": 2,
        "success_rate": "92.5%"
    },
    "request_types": {
        "research": 85,
        "content_generation": 45,
        "vapi_research": 20
    },
    "recent_jobs": [...],
    "database_file": "langgraph_research.db",
    "timestamp": "2024-01-01T12:00:00Z"
}
```

## Job Status Flow

```
created → running → processing → completed
                              → failed
```

**Status Descriptions:**
- `created`: Job record created, waiting to start
- `running`: Job is actively being processed
- `processing`: Job is in processing phase (e.g., analyzing results)
- `completed`: Job finished successfully with results
- `failed`: Job encountered an error and could not complete

## Request Types

- `research`: Research and information gathering tasks
- `content_generation`: Content creation tasks
- `vapi_research`: Research tasks initiated via VAPI webhook
- `quick_research`: Fast research with immediate response
- `comprehensive_research`: In-depth research with multiple sources

## Usage Examples

### Python Client Example

```python
import httpx
import asyncio

async def get_job_analytics():
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8082/jobs/analytics")
        if response.status_code == 200:
            analytics = response.json()
            print(f"Total jobs: {analytics['summary']['total_jobs']}")
            print(f"Success rate: {analytics['summary']['success_rate']}")
        return analytics

# Run the example
analytics = asyncio.run(get_job_analytics())
```

### cURL Examples

```bash
# Get job analytics
curl -X GET "http://localhost:8082/jobs/analytics"

# Search completed research jobs
curl -X GET "http://localhost:8082/jobs/search?status=completed&request_type=research"

# Export jobs as CSV
curl -X GET "http://localhost:8082/jobs/export?format=csv&limit=100"

# Clean up old jobs
curl -X POST "http://localhost:8082/jobs/cleanup?days_old=30"

# Delete a specific job
curl -X DELETE "http://localhost:8082/jobs/12345-uuid-string"
```

## Testing

Use the provided test script to verify all endpoints:

```bash
cd langgraph_forge
python test_job_endpoints.py
```

This will test all job management endpoints and demonstrate their usage.

## Error Handling

All endpoints return appropriate HTTP status codes:

- `200`: Success
- `400`: Bad request (e.g., trying to delete running job)
- `404`: Resource not found
- `500`: Internal server error

Error responses include descriptive messages:

```json
{
    "detail": "Job not found"
}
```

## Performance Considerations

- Use pagination (`limit`/`offset`) for large result sets
- The analytics endpoint may be slower with large databases
- Export operations are limited to prevent memory issues
- Database cleanup should be run periodically to maintain performance 