#!/usr/bin/env python3
"""
Monitor webhook calls to see if tools are being triggered during voice calls
"""

import time
import sqlite3
import json
from datetime import datetime, timedelta

def monitor_webhooks():
    """Monitor webhook calls and tool executions"""
    
    print("🔍 Starting webhook monitoring...")
    print("📞 Make a voice call now and try these queries:")
    print("   - 'Research artificial intelligence trends'")
    print("   - 'Create content about machine learning'")
    print("   - 'What is quantum computing?'")
    print("   - 'Generate a summary about blockchain technology'")
    print("\n⏰ Monitoring for tool calls (Press Ctrl+C to stop)...")
    
    last_check = datetime.now()
    
    try:
        while True:
            # Check for recent interactions
            conn = sqlite3.connect('vapi_forge.db')
            cursor = conn.cursor()
            
            # Get recent interactions (last 30 seconds)
            cutoff_time = (datetime.now() - timedelta(seconds=30)).isoformat()
            
            cursor.execute('''
                SELECT i.interaction_type, i.content, i.timestamp, va.name as agent_name
                FROM interactions i
                LEFT JOIN voice_agents va ON i.voice_agent_id = va.id
                WHERE i.timestamp > ? AND i.user_id = 4
                ORDER BY i.timestamp DESC
            ''', (cutoff_time,))
            
            recent_interactions = cursor.fetchall()
            conn.close()
            
            # Display new interactions
            for interaction in recent_interactions:
                interaction_time = datetime.fromisoformat(interaction[2])
                if interaction_time > last_check:
                    print(f"\n🔔 NEW INTERACTION:")
                    print(f"   Time: {interaction[2]}")
                    print(f"   Type: {interaction[0]}")
                    print(f"   Agent: {interaction[3] or 'Unknown'}")
                    print(f"   Content: {interaction[1][:100]}...")
                    
                    if "tool" in interaction[0].lower():
                        print(f"   🎯 TOOL CALL DETECTED!")
            
            last_check = datetime.now()
            time.sleep(2)  # Check every 2 seconds
            
    except KeyboardInterrupt:
        print(f"\n✅ Monitoring stopped.")
        
        # Show summary of recent activity
        conn = sqlite3.connect('vapi_forge.db')
        cursor = conn.cursor()
        
        # Get all interactions from the last 10 minutes
        cutoff_time = (datetime.now() - timedelta(minutes=10)).isoformat()
        
        cursor.execute('''
            SELECT i.interaction_type, i.content, i.timestamp, va.name as agent_name
            FROM interactions i
            LEFT JOIN voice_agents va ON i.voice_agent_id = va.id
            WHERE i.timestamp > ? AND i.user_id = 4
            ORDER BY i.timestamp DESC
        ''', (cutoff_time,))
        
        all_recent = cursor.fetchall()
        conn.close()
        
        print(f"\n📊 SUMMARY - Last 10 minutes:")
        if all_recent:
            for interaction in all_recent:
                print(f"   {interaction[2]} | {interaction[0]} | {interaction[1][:50]}...")
        else:
            print(f"   No interactions found in the last 10 minutes")

def check_webhook_logs():
    """Check if webhook endpoint is receiving calls"""
    print("🔍 Checking webhook endpoint status...")
    
    # This would typically check server logs, but we'll check the database
    conn = sqlite3.connect('vapi_forge.db')
    cursor = conn.cursor()
    
    # Get recent interactions
    cursor.execute('''
        SELECT COUNT(*) as total, 
               SUM(CASE WHEN interaction_type LIKE '%tool%' THEN 1 ELSE 0 END) as tool_calls
        FROM interactions 
        WHERE user_id = 4 AND timestamp > datetime('now', '-1 hour')
    ''')
    
    result = cursor.fetchone()
    conn.close()
    
    total_interactions = result[0] if result else 0
    tool_calls = result[1] if result else 0
    
    print(f"📊 Last hour statistics:")
    print(f"   Total interactions: {total_interactions}")
    print(f"   Tool calls: {tool_calls}")
    
    if tool_calls > 0:
        print(f"   ✅ Tools are being called!")
    else:
        print(f"   ⚠️  No tool calls detected")

if __name__ == "__main__":
    print("🎯 Webhook Monitoring Tool")
    print("=" * 50)
    
    # First check current status
    check_webhook_logs()
    
    print("\n" + "=" * 50)
    
    # Start monitoring
    monitor_webhooks() 