#!/usr/bin/env python3
"""
Test script for the enhanced job management endpoints in LangGraph Forge
Demonstrates how to interact with the job database and analytics.
"""

import asyncio
import httpx
import json
from datetime import datetime

# Configuration
LANGGRAPH_BASE_URL = "http://localhost:8082"

async def test_job_endpoints():
    """Test all the job management endpoints"""
    
    async with httpx.AsyncClient() as client:
        print("🧪 Testing LangGraph Forge Job Management Endpoints")
        print("=" * 60)
        
        # 1. Test basic health check
        print("\n1. 🏥 Health Check")
        try:
            response = await client.get(f"{LANGGRAPH_BASE_URL}/health")
            if response.status_code == 200:
                health_data = response.json()
                print(f"✅ Service is healthy")
                print(f"   Active jobs: {health_data.get('active_jobs', 0)}")
                print(f"   Database: {health_data.get('database', 'unknown')}")
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Cannot connect to LangGraph service: {e}")
            return
        
        # 2. Test job analytics
        print("\n2. 📊 Job Analytics")
        try:
            response = await client.get(f"{LANGGRAPH_BASE_URL}/jobs/analytics")
            if response.status_code == 200:
                analytics = response.json()
                print(f"✅ Analytics retrieved successfully")
                print(f"   Total jobs: {analytics['summary']['total_jobs']}")
                print(f"   Active jobs: {analytics['summary']['active_jobs']}")
                print(f"   Success rate: {analytics['summary']['success_rate']}")
                print(f"   Recent 24h: {analytics['summary']['recent_24h']}")
                print(f"   Status breakdown: {analytics['status_breakdown']}")
                print(f"   Request types: {analytics['request_type_breakdown']}")
            else:
                print(f"❌ Analytics failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Analytics error: {e}")
        
        # 3. Test listing all jobs
        print("\n3. 📋 List All Jobs")
        try:
            response = await client.get(f"{LANGGRAPH_BASE_URL}/jobs?limit=5")
            if response.status_code == 200:
                jobs_data = response.json()
                jobs = jobs_data.get('jobs', [])
                print(f"✅ Retrieved {len(jobs)} recent jobs")
                
                for i, job in enumerate(jobs[:3], 1):  # Show first 3 jobs
                    print(f"   Job {i}:")
                    print(f"     ID: {job['job_id'][:8]}...")
                    print(f"     Type: {job['request_type']}")
                    print(f"     Status: {job['status']}")
                    print(f"     Created: {job['created_at']}")
            else:
                print(f"❌ List jobs failed: {response.status_code}")
        except Exception as e:
            print(f"❌ List jobs error: {e}")
        
        # 4. Test job search with filters
        print("\n4. 🔍 Search Jobs (Completed)")
        try:
            response = await client.get(f"{LANGGRAPH_BASE_URL}/jobs/search?status=completed&limit=3")
            if response.status_code == 200:
                search_data = response.json()
                jobs = search_data.get('jobs', [])
                print(f"✅ Found {len(jobs)} completed jobs")
                
                for job in jobs:
                    print(f"   - {job['job_id'][:8]}... ({job['request_type']}) - {job['status']}")
            else:
                print(f"❌ Search failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Search error: {e}")
        
        # 5. Test job search by request type
        print("\n5. 🔍 Search Jobs (Research Type)")
        try:
            response = await client.get(f"{LANGGRAPH_BASE_URL}/jobs/search?request_type=research&limit=3")
            if response.status_code == 200:
                search_data = response.json()
                jobs = search_data.get('jobs', [])
                print(f"✅ Found {len(jobs)} research jobs")
                
                for job in jobs:
                    input_data = job.get('input_data', {})
                    query = input_data.get('query', 'Unknown query')
                    print(f"   - {job['job_id'][:8]}... Query: '{query[:50]}...'")
            else:
                print(f"❌ Search by type failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Search by type error: {e}")
        
        # 6. Create a test research job
        print("\n6. 🧪 Create Test Research Job")
        try:
            test_request = {
                "query": "What are the latest developments in artificial intelligence?",
                "research_type": "quick",
                "max_sources": 2
            }
            
            response = await client.post(f"{LANGGRAPH_BASE_URL}/quick-research", json=test_request)
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Test research completed")
                print(f"   Query: {result.get('query', 'N/A')}")
                print(f"   Summary: {result.get('summary', 'N/A')[:100]}...")
                print(f"   Source: {result.get('source', 'N/A')}")
            else:
                print(f"❌ Test research failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Test research error: {e}")
        
        # 7. Test export functionality
        print("\n7. 📤 Export Jobs (JSON)")
        try:
            response = await client.get(f"{LANGGRAPH_BASE_URL}/jobs/export?format=json&limit=5")
            if response.status_code == 200:
                export_data = response.json()
                print(f"✅ Exported {export_data['total_records']} jobs")
                print(f"   Format: {export_data['format']}")
                print(f"   Export timestamp: {export_data['export_timestamp']}")
            else:
                print(f"❌ Export failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Export error: {e}")
        
        # 8. Test database admin view
        print("\n8. 🔧 Admin Database View")
        try:
            response = await client.get(f"{LANGGRAPH_BASE_URL}/admin/database?limit=5")
            if response.status_code == 200:
                admin_data = response.json()
                stats = admin_data.get('database_stats', {})
                print(f"✅ Database admin view retrieved")
                print(f"   Total jobs: {stats.get('total_jobs', 0)}")
                print(f"   Success rate: {stats.get('success_rate', '0%')}")
                print(f"   Running: {stats.get('running', 0)}")
                print(f"   Failed: {stats.get('failed', 0)}")
                print(f"   Database file: {admin_data.get('database_file', 'unknown')}")
            else:
                print(f"❌ Admin view failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Admin view error: {e}")
        
        print("\n" + "=" * 60)
        print("🎉 Job endpoint testing completed!")
        print("\n📚 Available Endpoints:")
        print("   GET  /jobs                    - List jobs with pagination")
        print("   GET  /jobs/search             - Search/filter jobs")
        print("   GET  /jobs/analytics          - Get job analytics")
        print("   GET  /jobs/export             - Export jobs data")
        print("   GET  /job-status/{job_id}     - Get specific job status")
        print("   DELETE /jobs/{job_id}         - Delete a job")
        print("   POST /jobs/cleanup            - Clean up old jobs")
        print("   GET  /admin/database          - Admin database view")

async def demonstrate_job_lifecycle():
    """Demonstrate a complete job lifecycle"""
    
    async with httpx.AsyncClient() as client:
        print("\n🔄 Demonstrating Job Lifecycle")
        print("=" * 40)
        
        # Create a research job
        print("1. Creating research job...")
        research_request = {
            "query": "Benefits of renewable energy",
            "research_type": "comprehensive",
            "max_sources": 3
        }
        
        try:
            response = await client.post(f"{LANGGRAPH_BASE_URL}/research", json=research_request)
            if response.status_code == 200:
                job_data = response.json()
                job_id = job_data['job_id']
                print(f"✅ Job created: {job_id}")
                
                # Monitor job status
                print("2. Monitoring job status...")
                for i in range(5):  # Check status 5 times
                    await asyncio.sleep(2)  # Wait 2 seconds
                    
                    status_response = await client.get(f"{LANGGRAPH_BASE_URL}/job-status/{job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        current_status = status_data['status']
                        print(f"   Status check {i+1}: {current_status}")
                        
                        if current_status in ['completed', 'failed']:
                            print(f"✅ Job finished with status: {current_status}")
                            if current_status == 'completed' and status_data.get('result'):
                                result = status_data['result']
                                print(f"   Result summary: {str(result)[:100]}...")
                            break
                    else:
                        print(f"❌ Status check failed: {status_response.status_code}")
                        break
                else:
                    print("⏰ Job still running after monitoring period")
                    
            else:
                print(f"❌ Job creation failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Job lifecycle error: {e}")

if __name__ == "__main__":
    print("🚀 LangGraph Forge Job Management Test Suite")
    print("Make sure LangGraph Forge is running on http://localhost:8082")
    print()
    
    # Run the tests
    asyncio.run(test_job_endpoints())
    
    # Demonstrate job lifecycle
    asyncio.run(demonstrate_job_lifecycle()) 