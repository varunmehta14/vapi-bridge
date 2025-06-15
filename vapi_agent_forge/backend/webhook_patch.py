# Copy and paste this code into your LangGraph service (port 8082)
# Add this after your existing endpoints

@app.post("/webhook/tool-call")
async def proxy_webhook_to_backend(request: Request):
    """Proxy Vapi webhook calls to the backend service"""
    import httpx
    import json
    
    try:
        raw_data = await request.json()
        print(f"🔄 [LangGraph] Received webhook from Vapi: {json.dumps(raw_data, indent=2)}")
        
        # Forward to Vapi Agent Forge backend
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
            
    except Exception as e:
        error_msg = f"Webhook proxy failed: {str(e)}"
        print(f"❌ [LangGraph] {error_msg}")
        return {"error": error_msg}

@app.get("/webhook/health")
async def webhook_health():
    """Health check for webhook proxy"""
    return {"status": "healthy", "proxy_target": "http://localhost:8000"}

# Don't forget to add these imports at the top of your file:
# from fastapi import Request
# import httpx
# import json 