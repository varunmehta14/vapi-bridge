#!/usr/bin/env python3
"""
Code to add to your LangGraph service to handle Vapi webhooks
Add this to your LangGraph FastAPI app (the one running on port 8082)
"""

# Add these imports to your LangGraph service
from fastapi import Request
import httpx
import json

# Add this endpoint to your LangGraph FastAPI app
async def add_webhook_endpoint_to_langgraph_app(app):
    """
    Add this function call to your LangGraph service initialization
    """
    
    @app.post("/webhook/tool-call")
    async def proxy_webhook_to_backend(request: Request):
        """Proxy Vapi webhook calls to the backend service"""
        try:
            # Get the raw data from Vapi
            raw_data = await request.json()
            print(f"🔄 [LangGraph] Received webhook call from Vapi")
            print(f"📡 [LangGraph] Data: {json.dumps(raw_data, indent=2)}")
            
            # Forward to the Vapi Agent Forge backend
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8000/webhook/tool-call",
                    json=raw_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30.0
                )
                
                response.raise_for_status()
                result = response.json()
                
                print(f"✅ [LangGraph] Backend response: {json.dumps(result, indent=2)}")
                return result
                
        except httpx.HTTPError as e:
            error_msg = f"Backend connection failed: {str(e)}"
            print(f"❌ [LangGraph] {error_msg}")
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"Webhook proxy error: {str(e)}"
            print(f"❌ [LangGraph] {error_msg}")
            return {"error": error_msg}
    
    @app.get("/webhook/health")
    async def webhook_health():
        """Health check for webhook proxy"""
        return {
            "status": "healthy", 
            "proxy_target": "http://localhost:8000",
            "service": "LangGraph webhook proxy"
        }
    
    print("✅ [LangGraph] Webhook endpoints added successfully")

# Example of how to integrate this into your LangGraph service:
"""
# In your LangGraph main.py or app.py file:

from fastapi import FastAPI
app = FastAPI()

# Your existing LangGraph endpoints...
@app.post("/quick-research")
async def quick_research(request: ResearchRequest):
    # Your existing code...
    pass

@app.post("/generate-content") 
async def generate_content(request: ContentRequest):
    # Your existing code...
    pass

# ADD THIS LINE to enable webhook proxying:
await add_webhook_endpoint_to_langgraph_app(app)

# Or manually add the webhook endpoint:
@app.post("/webhook/tool-call")
async def proxy_webhook_to_backend(request: Request):
    import httpx
    import json
    
    try:
        raw_data = await request.json()
        print(f"🔄 Proxying webhook to backend: {json.dumps(raw_data, indent=2)}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/webhook/tool-call",
                json=raw_data,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            print(f"✅ Backend response: {json.dumps(result, indent=2)}")
            return result
            
    except Exception as e:
        print(f"❌ Webhook proxy error: {str(e)}")
        return {"error": f"Webhook proxy failed: {str(e)}"}
"""

if __name__ == "__main__":
    print("📋 Instructions to add webhook to your LangGraph service:")
    print("=" * 60)
    print("1. Open your LangGraph service code (the one running on port 8082)")
    print("2. Add the webhook endpoint code shown above")
    print("3. Restart your LangGraph service")
    print("4. Test with: curl -X POST https://d6c5-2603-8000-baf0-4690-4c7d-38bd-11e8-5920.ngrok-free.app/webhook/tool-call")
    print("\n🎯 This will enable Vapi → LangGraph → Backend → LangGraph API flow") 