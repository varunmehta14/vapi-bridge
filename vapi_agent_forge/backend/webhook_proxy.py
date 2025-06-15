#!/usr/bin/env python3
"""
Webhook proxy to forward Vapi webhook calls from LangGraph service to backend
Add this to your LangGraph service or run as a separate service on port 8082
"""

from fastapi import FastAPI, Request
import httpx
import json

app = FastAPI()

BACKEND_URL = "http://localhost:8000"

@app.post("/webhook/tool-call")
async def proxy_webhook(request: Request):
    """Proxy webhook calls to the backend service"""
    try:
        # Get the raw data from Vapi
        raw_data = await request.json()
        
        print(f"🔄 Proxying webhook call to backend...")
        print(f"📡 Data: {json.dumps(raw_data, indent=2)}")
        
        # Forward to backend
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BACKEND_URL}/webhook/tool-call",
                json=raw_data,
                headers={"Content-Type": "application/json"},
                timeout=30.0
            )
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Backend response: {json.dumps(result, indent=2)}")
            return result
            
    except Exception as e:
        print(f"❌ Proxy error: {str(e)}")
        return {"error": f"Proxy failed: {str(e)}"}

@app.get("/webhook/health")
async def webhook_health():
    """Health check for webhook proxy"""
    return {"status": "healthy", "proxy_target": BACKEND_URL}

if __name__ == "__main__":
    import uvicorn
    print("🔄 Starting webhook proxy on port 8083...")
    print(f"📡 Forwarding to: {BACKEND_URL}")
    uvicorn.run(app, host="0.0.0.0", port=8083) 