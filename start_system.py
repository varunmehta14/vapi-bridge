#!/usr/bin/env python3
"""
Tesseract + Vapi System Startup Script (Virtual Environment Support)

This script helps you start the complete system with proper coordination
and provides helpful setup instructions. Supports virtual environments.
"""

import subprocess
import time
import os
import sys
import signal
import requests
from pathlib import Path

class SystemManager:
    def __init__(self):
        self.processes = []
        self.base_dir = Path(__file__).parent
        
    def find_python_executable(self, component_dir):
        """Find the best Python executable (venv or system)"""
        # Check for virtual environment first
        venv_dir = component_dir / "venv"
        
        if venv_dir.exists():
            if os.name == 'nt':  # Windows
                venv_python = venv_dir / 'Scripts' / 'python.exe'
            else:  # Unix/Linux/macOS
                venv_python = venv_dir / 'bin' / 'python'
            
            if venv_python.exists():
                print(f"   Using virtual environment: {venv_python}")
                return str(venv_python)
        
        # Fall back to system Python
        print(f"   No virtual environment found, using system Python")
        return sys.executable
        
    def check_dependencies(self):
        """Check if required dependencies are installed"""
        print("🔍 Checking system dependencies...")
        
        # Check Python version
        version = sys.version_info
        if version.major == 3 and version.minor >= 11:
            print(f"✅ Python {version.major}.{version.minor}.{version.micro} meets requirements (3.11+)")
        elif version.major == 3 and version.minor >= 8:
            print(f"⚠️  Python {version.major}.{version.minor}.{version.micro} will work but 3.11+ is recommended")
        else:
            print(f"❌ Python {version.major}.{version.minor}.{version.micro} is too old. Python 3.11+ is required")
            print("   Install Python 3.11+ and run setup_venv.py first")
            return False
        
        # Check if virtual environments exist
        tesseract_venv = self.base_dir / "tesseract_engine" / "venv"
        forge_venv = self.base_dir / "vapi_agent_forge" / "backend" / "venv"
        
        if tesseract_venv.exists() and forge_venv.exists():
            print("✅ Virtual environments detected")
            return True
        elif tesseract_venv.exists() or forge_venv.exists():
            print("⚠️  Partial virtual environment setup detected")
            print("   Run: python setup_venv.py to complete setup")
        else:
            print("ℹ️  No virtual environments found")
            print("   Recommended: Run 'python setup_venv.py' for better isolation")
            
            # Check if required packages are installed in system Python
            missing_packages = []
            
            try:
                import fastapi
                import uvicorn
                import sqlalchemy
                import yaml
                import httpx
            except ImportError as e:
                missing_packages.append(str(e).split("'")[1])
            
            if missing_packages:
                print(f"❌ Missing packages: {', '.join(missing_packages)}")
                print("   Option 1: Run 'python setup_venv.py' (recommended)")
                print("   Option 2: Install manually:")
                print("     cd tesseract_engine && pip install -r requirements.txt")
                print("     cd vapi_agent_forge/backend && pip install -r requirements.txt")
                return False
                
        print("✅ All dependencies are available")
        return True
    
    def start_tesseract_engine(self):
        """Start the Tesseract Workflow Engine"""
        print("🚀 Starting Tesseract Workflow Engine...")
        
        tesseract_dir = self.base_dir / "tesseract_engine"
        if not tesseract_dir.exists():
            print("❌ tesseract_engine directory not found")
            return False
        
        # Find the best Python executable
        python_cmd = self.find_python_executable(tesseract_dir)
            
        try:
            process = subprocess.Popen(
                [python_cmd, "main.py"],
                cwd=tesseract_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes.append(("Tesseract Engine", process))
            
            # Wait a moment and check if it started successfully
            time.sleep(3)
            if process.poll() is None:
                print("✅ Tesseract Engine started successfully (port 8081)")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Tesseract Engine failed to start:")
                print(f"   stdout: {stdout.decode()}")
                print(f"   stderr: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start Tesseract Engine: {str(e)}")
            return False
    
    def start_vapi_forge(self):
        """Start the Vapi Agent Forge"""
        print("🔧 Starting Vapi Agent Forge...")
        
        forge_dir = self.base_dir / "vapi_agent_forge" / "backend"
        if not forge_dir.exists():
            print("❌ vapi_agent_forge/backend directory not found")
            return False
        
        # Find the best Python executable
        python_cmd = self.find_python_executable(forge_dir)
            
        try:
            process = subprocess.Popen(
                [python_cmd, "main.py"],
                cwd=forge_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.processes.append(("Vapi Agent Forge", process))
            
            # Wait a moment and check if it started successfully
            time.sleep(3)
            if process.poll() is None:
                print("✅ Vapi Agent Forge started successfully (port 8000)")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ Vapi Agent Forge failed to start:")
                print(f"   stdout: {stdout.decode()}")
                print(f"   stderr: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start Vapi Agent Forge: {str(e)}")
            return False
    
    def check_services(self):
        """Check if services are responding"""
        print("🔍 Checking service health...")
        
        services = [
            ("Tesseract Engine", "http://localhost:8081/", 8081),
            ("Vapi Agent Forge", "http://localhost:8000/", 8000)
        ]
        
        all_healthy = True
        for name, url, port in services:
            try:
                response = requests.get(url, timeout=5)
                if response.status_code == 200:
                    print(f"✅ {name} is healthy on port {port}")
                else:
                    print(f"⚠️  {name} returned status {response.status_code}")
                    all_healthy = False
            except requests.RequestException:
                print(f"❌ {name} is not responding on port {port}")
                all_healthy = False
        
        return all_healthy
    
    def show_ngrok_instructions(self):
        """Show instructions for setting up ngrok"""
        print("\n" + "="*60)
        print("🌐 CRITICAL: Setup Ngrok for Vapi Integration")
        print("="*60)
        print()
        print("Vapi requires a public HTTPS URL to send webhooks.")
        print("Follow these steps in a NEW TERMINAL WINDOW:")
        print()
        print("1. Start ngrok:")
        print("   ngrok http 8000")
        print()
        print("2. Copy the HTTPS URL (e.g., https://abc123.ngrok.io)")
        print()
        print("3. Set environment variable:")
        print("   export PUBLIC_SERVER_URL='https://your-ngrok-url.ngrok.io'")
        print()
        print("4. Set your Vapi API key:")
        print("   export VAPI_API_KEY='your_vapi_api_key'")
        print()
        print("5. Create Vapi assistant:")
        if (self.base_dir / "vapi_agent_forge" / "backend" / "venv").exists():
            if os.name == 'nt':
                print("   vapi_agent_forge\\backend\\venv\\Scripts\\activate.bat")
            else:
                print("   source vapi_agent_forge/backend/venv/bin/activate")
        print("   cd vapi_agent_forge/backend && python orchestrator.py")
        print()
        print("6. Start Next.js Control Panel:")
        print("   cd vapi_agent_forge/frontend && npm run dev")
        print("   Then open: http://localhost:3000")
        print()
        
    def show_status(self):
        """Show current system status"""
        print("\n" + "="*60)
        print("📊 System Status")
        print("="*60)
        
        print(f"🔧 Active processes: {len(self.processes)}")
        for name, process in self.processes:
            status = "Running" if process.poll() is None else "Stopped"
            print(f"   • {name}: {status}")
        
        print()
        print("🌐 Service URLs:")
        print("   • Tesseract Engine: http://localhost:8081")
        print("   • Vapi Agent Forge: http://localhost:8000")
        print("   • Control Panel: http://localhost:3000 (npm run dev)")
        
        # Check virtual environments
        tesseract_venv = self.base_dir / "tesseract_engine" / "venv"
        forge_venv = self.base_dir / "vapi_agent_forge" / "backend" / "venv"
        
        print()
        print("📦 Virtual Environments:")
        print(f"   • Tesseract Engine: {'✅ Active' if tesseract_venv.exists() else '❌ Not found'}")
        print(f"   • Vapi Agent Forge: {'✅ Active' if forge_venv.exists() else '❌ Not found'}")
        
        # Check environment variables
        public_url = os.getenv("PUBLIC_SERVER_URL", "Not set")
        vapi_key = os.getenv("VAPI_API_KEY", "Not set")
        
        print()
        print("🔑 Environment:")
        print(f"   • PUBLIC_SERVER_URL: {public_url}")
        print(f"   • VAPI_API_KEY: {'Set' if vapi_key != 'Not set' else 'Not set'}")
        
    def cleanup(self):
        """Clean up processes"""
        print("\n🛑 Shutting down services...")
        for name, process in self.processes:
            if process.poll() is None:
                print(f"   Stopping {name}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
        print("✅ All services stopped")
    
    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        print(f"\n📡 Received signal {signum}")
        self.cleanup()
        sys.exit(0)

def main():
    print("🚀 Tesseract + Vapi System Startup (Virtual Environment Support)")
    print("="*70)
    
    manager = SystemManager()
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    try:
        # Check dependencies
        if not manager.check_dependencies():
            print("\n💡 Tip: Run 'python setup_venv.py' to set up virtual environments")
            sys.exit(1)
        
        # Start services
        if not manager.start_tesseract_engine():
            sys.exit(1)
        
        if not manager.start_vapi_forge():
            manager.cleanup()
            sys.exit(1)
        
        # Wait for services to fully start
        time.sleep(3)
        
        # Check service health
        if not manager.check_services():
            print("⚠️  Some services may not be fully ready")
        
        # Show setup instructions
        manager.show_ngrok_instructions()
        manager.show_status()
        
        print("\n" + "="*60)
        print("✅ System is running! Press Ctrl+C to stop.")
        print("="*60)
        
        # Keep the script running
        try:
            while True:
                time.sleep(1)
                # Check if processes are still alive
                for name, process in manager.processes:
                    if process.poll() is not None:
                        print(f"⚠️  {name} has stopped unexpectedly")
                        
        except KeyboardInterrupt:
            pass
            
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
    finally:
        manager.cleanup()

if __name__ == "__main__":
    main() 