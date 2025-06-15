#!/usr/bin/env python3
"""
Script to fix the VAPI webhook response format
"""

import re

def fix_webhook_format():
    """Fix the webhook to use VAPI's required response format"""
    
    # Read the main.py file
    with open('vapi_agent_forge/backend/main.py', 'r') as f:
        content = f.read()
    
    # Find and replace the fast webhook function
    old_pattern = r'@app\.post\("/webhook/vapi-fast"\)\nasync def handle_vapi_fast_tool_call\(request: Request\):.*?return \{"error": f"Fast webhook error: \{str\(e\)\}"\}'
    
    new_webhook = '''@app.post("/webhook/vapi-fast")
async def handle_vapi_fast_tool_call(request: Request):
    """
    Ultra-fast webhook for VAPI tool calls - uses VAPI's required response format
    Response format: {"results": [{"toolCallId": "...", "result": "..."}]}
    """
    print(f"\\n🚀 VAPI FAST WEBHOOK at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Get the raw JSON data from Vapi
        raw_data = await request.json()
        
        # Quick extraction without detailed logging
        tool_call_id = None
        tool_name = None
        tool_parameters = {}
        
        if "message" in raw_data:
            message = raw_data["message"]
            tool_calls = message.get("toolCalls", []) or message.get("toolCallList", [])
            
            if tool_calls:
                tool_call = tool_calls[0]
                tool_call_id = tool_call.get("id")
                if "function" in tool_call:
                    tool_name = tool_call["function"]["name"]
                    tool_parameters = tool_call["function"].get("arguments", {})
                    
                    if isinstance(tool_parameters, str):
                        try:
                            tool_parameters = json.loads(tool_parameters)
                        except:
                            tool_parameters = {}
        
        print(f"⚡ Fast processing: {tool_name} with ID: {tool_call_id}")
        
        # Validate required fields per VAPI documentation
        if not tool_call_id:
            return {
                "results": [{
                    "toolCallId": "unknown",
                    "error": "Missing tool call ID"
                }]
            }
        
        if not tool_name:
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "error": "No tool call found"
                }]
            }
        
        # For research tools, provide immediate response with actual research
        if tool_name == "quick_research":
            query = tool_parameters.get("query", "unknown topic")
            
            # Make a VERY fast research call with short timeout
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        "http://localhost:8082/quick-research",
                        json={
                            "query": query,
                            "research_type": "quick",
                            "max_sources": 1  # Reduced for speed
                        },
                        timeout=3.0  # Very short timeout
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        summary = result.get("summary", "")
                        source = result.get("source", "")
                        
                        # Format as single-line string (VAPI requirement - no line breaks)
                        formatted_result = f"Based on my research on '{query}', here\\'s what I found: {summary}"
                        if source:
                            formatted_result += f" (Source: {source})"
                        
                        # Use VAPI\\'s exact required format
                        vapi_response = {
                            "results": [{
                                "toolCallId": tool_call_id,
                                "result": formatted_result
                            }]
                        }
                        
                        print(f"⚡ Fast research completed for: {query}")
                        return vapi_response
                        
            except Exception as e:
                print(f"⚠️ Fast research failed, using fallback: {e}")
            
            # Fallback if research fails or times out
            return {
                "results": [{
                    "toolCallId": tool_call_id,
                    "result": f"I\\'m researching \\'{query}\\' for you. Please give me a moment to gather the information."
                }]
            }
        
        # For other tools, return generic fast response
        return {
            "results": [{
                "toolCallId": tool_call_id,
                "result": f"Processing your {tool_name} request..."
            }]
        }
        
    except Exception as e:
        print(f"❌ Fast webhook error: {e}")
        return {
            "results": [{
                "toolCallId": tool_call_id or "unknown",
                "error": f"Fast webhook error: {str(e)}"
            }]
        }'''
    
    # Replace the function using regex with DOTALL flag
    content = re.sub(old_pattern, new_webhook, content, flags=re.DOTALL)
    
    # Write back to file
    with open('vapi_agent_forge/backend/main.py', 'w') as f:
        f.write(content)
    
    print("✅ Webhook format fixed!")

if __name__ == "__main__":
    fix_webhook_format() 