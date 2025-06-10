#!/usr/bin/env python3
"""
Virtual Environment Setup Script for Tesseract + Vapi System

This script creates virtual environments for both components and installs dependencies.
Requires Python 3.11+
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, cwd=None, description=""):
    """Run a command and handle errors"""
    print(f"🔧 {description}")
    print(f"   Running: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command, 
            cwd=cwd, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def check_python_version():
    """Check if Python 3.11+ is available"""
    print("🔍 Checking Python version...")
    
    # Check current Python version
    version = sys.version_info
    if version.major == 3 and version.minor >= 11:
        python_cmd = sys.executable
        print(f"✅ Using Python {version.major}.{version.minor}.{version.micro} at {python_cmd}")
        return python_cmd
    
    # Try to find python3.11 specifically
    try:
        result = subprocess.run(['python3.11', '--version'], capture_output=True, text=True, check=True)
        print(f"✅ Found Python 3.11: {result.stdout.strip()}")
        return 'python3.11'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    # Try python3
    try:
        result = subprocess.run(['python3', '--version'], capture_output=True, text=True, check=True)
        version_str = result.stdout.strip()
        if '3.11' in version_str or '3.12' in version_str:
            print(f"✅ Found compatible Python: {version_str}")
            return 'python3'
    except (subprocess.CalledProcessError, FileNotFoundError):
        pass
    
    print("❌ Python 3.11+ not found!")
    print("   Please install Python 3.11+ first:")
    print("   • macOS: brew install python@3.11")
    print("   • Ubuntu/Debian: sudo apt install python3.11 python3.11-venv")
    print("   • Windows: Download from python.org")
    return None

def create_virtual_environment(python_cmd, venv_path, component_name):
    """Create a virtual environment"""
    print(f"\n📦 Setting up virtual environment for {component_name}")
    
    # Remove existing venv if it exists
    if venv_path.exists():
        print(f"   Removing existing virtual environment...")
        import shutil
        shutil.rmtree(venv_path)
    
    # Create new virtual environment
    success = run_command(
        [python_cmd, '-m', 'venv', str(venv_path)],
        description=f"Creating virtual environment for {component_name}"
    )
    
    if not success:
        return False
    
    # Get the correct python and pip paths for the venv
    if os.name == 'nt':  # Windows
        venv_python = venv_path / 'Scripts' / 'python.exe'
        venv_pip = venv_path / 'Scripts' / 'pip.exe'
    else:  # Unix/Linux/macOS
        venv_python = venv_path / 'bin' / 'python'
        venv_pip = venv_path / 'bin' / 'pip'
    
    # Upgrade pip
    success = run_command(
        [str(venv_python), '-m', 'pip', 'install', '--upgrade', 'pip'],
        description=f"Upgrading pip in {component_name} virtual environment"
    )
    
    return success and venv_python.exists()

def install_dependencies(venv_python, requirements_file, component_name):
    """Install dependencies in the virtual environment"""
    print(f"\n📋 Installing dependencies for {component_name}")
    
    if not requirements_file.exists():
        print(f"❌ Requirements file not found: {requirements_file}")
        return False
    
    return run_command(
        [str(venv_python), '-m', 'pip', 'install', '-r', str(requirements_file)],
        description=f"Installing {component_name} dependencies"
    )

def create_activation_scripts():
    """Create convenient activation scripts"""
    print("\n📝 Creating activation scripts...")
    
    base_dir = Path(__file__).parent
    
    # Create activation script for Unix/Linux/macOS
    activate_script = base_dir / "activate_venvs.sh"
    activate_content = '''#!/bin/bash
# Activation script for Tesseract + Vapi System Virtual Environments

echo "🚀 Tesseract + Vapi System Virtual Environment Setup"
echo "Choose which environment to activate:"
echo "1. Tesseract Engine"
echo "2. Vapi Agent Forge"
echo "3. Both (for development)"

read -p "Enter choice (1-3): " choice

case $choice in
    1)
        echo "🔧 Activating Tesseract Engine virtual environment..."
        source tesseract_engine/venv/bin/activate
        echo "✅ Tesseract Engine venv activated"
        echo "   Run: cd tesseract_engine && python main.py"
        ;;
    2)
        echo "🔧 Activating Vapi Agent Forge virtual environment..."
        source vapi_agent_forge/backend/venv/bin/activate
        echo "✅ Vapi Agent Forge venv activated"
        echo "   Run: cd vapi_agent_forge/backend && python main.py"
        ;;
    3)
        echo "🔧 Setting up development environment..."
        echo "   Note: You'll need separate terminals for each service"
        echo "   Terminal 1: source tesseract_engine/venv/bin/activate && cd tesseract_engine && python main.py"
        echo "   Terminal 2: source vapi_agent_forge/backend/venv/bin/activate && cd vapi_agent_forge/backend && python main.py"
        ;;
    *)
        echo "❌ Invalid choice"
        ;;
esac
'''
    
    with open(activate_script, 'w') as f:
        f.write(activate_content)
    
    # Make it executable
    activate_script.chmod(0o755)
    
    # Create Windows batch file
    activate_bat = base_dir / "activate_venvs.bat"
    bat_content = '''@echo off
echo 🚀 Tesseract + Vapi System Virtual Environment Setup
echo Choose which environment to activate:
echo 1. Tesseract Engine
echo 2. Vapi Agent Forge
echo 3. Both (for development)

set /p choice="Enter choice (1-3): "

if "%choice%"=="1" (
    echo 🔧 Activating Tesseract Engine virtual environment...
    call tesseract_engine\\venv\\Scripts\\activate.bat
    echo ✅ Tesseract Engine venv activated
    echo    Run: cd tesseract_engine && python main.py
) else if "%choice%"=="2" (
    echo 🔧 Activating Vapi Agent Forge virtual environment...
    call vapi_agent_forge\\backend\\venv\\Scripts\\activate.bat
    echo ✅ Vapi Agent Forge venv activated
    echo    Run: cd vapi_agent_forge/backend && python main.py
) else if "%choice%"=="3" (
    echo 🔧 Setting up development environment...
    echo    Note: You'll need separate terminals for each service
    echo    Terminal 1: tesseract_engine\\venv\\Scripts\\activate.bat && cd tesseract_engine && python main.py
    echo    Terminal 2: vapi_agent_forge\\backend\\venv\\Scripts\\activate.bat && cd vapi_agent_forge/backend && python main.py
) else (
    echo ❌ Invalid choice
)
'''
    
    with open(activate_bat, 'w') as f:
        f.write(bat_content)
    
    print(f"✅ Created activation scripts:")
    print(f"   • Unix/Linux/macOS: {activate_script}")
    print(f"   • Windows: {activate_bat}")

def main():
    print("🚀 Tesseract + Vapi System Virtual Environment Setup")
    print("=" * 60)
    
    # Check Python version
    python_cmd = check_python_version()
    if not python_cmd:
        sys.exit(1)
    
    base_dir = Path(__file__).parent
    
    # Setup Tesseract Engine
    tesseract_venv = base_dir / "tesseract_engine" / "venv"
    tesseract_requirements = base_dir / "tesseract_engine" / "requirements.txt"
    
    success = create_virtual_environment(python_cmd, tesseract_venv, "Tesseract Engine")
    if not success:
        print("❌ Failed to create Tesseract Engine virtual environment")
        sys.exit(1)
    
    # Get venv python path
    if os.name == 'nt':
        tesseract_python = tesseract_venv / 'Scripts' / 'python.exe'
    else:
        tesseract_python = tesseract_venv / 'bin' / 'python'
    
    success = install_dependencies(tesseract_python, tesseract_requirements, "Tesseract Engine")
    if not success:
        print("❌ Failed to install Tesseract Engine dependencies")
        sys.exit(1)
    
    # Setup Vapi Agent Forge
    forge_venv = base_dir / "vapi_agent_forge" / "backend" / "venv"
    forge_requirements = base_dir / "vapi_agent_forge" / "backend" / "requirements.txt"
    
    success = create_virtual_environment(python_cmd, forge_venv, "Vapi Agent Forge")
    if not success:
        print("❌ Failed to create Vapi Agent Forge virtual environment")
        sys.exit(1)
    
    # Get venv python path
    if os.name == 'nt':
        forge_python = forge_venv / 'Scripts' / 'python.exe'
    else:
        forge_python = forge_venv / 'bin' / 'python'
    
    success = install_dependencies(forge_python, forge_requirements, "Vapi Agent Forge")
    if not success:
        print("❌ Failed to install Vapi Agent Forge dependencies")
        sys.exit(1)
    
    # Create activation scripts
    create_activation_scripts()
    
    print("\n" + "=" * 60)
    print("✅ Virtual Environment Setup Complete!")
    print("=" * 60)
    print()
    print("📦 Virtual environments created:")
    print(f"   • Tesseract Engine: {tesseract_venv}")
    print(f"   • Vapi Agent Forge: {forge_venv}")
    print()
    print("🚀 To start the system:")
    print("   Option 1 - Use activation scripts:")
    if os.name == 'nt':
        print("     ./activate_venvs.bat")
    else:
        print("     ./activate_venvs.sh")
    print()
    print("   Option 2 - Manual activation:")
    print("     Terminal 1 (Tesseract):")
    if os.name == 'nt':
        print("       tesseract_engine\\venv\\Scripts\\activate.bat")
    else:
        print("       source tesseract_engine/venv/bin/activate")
    print("       cd tesseract_engine && python main.py")
    print()
    print("     Terminal 2 (Vapi Forge):")
    if os.name == 'nt':
        print("       vapi_agent_forge\\backend\\venv\\Scripts\\activate.bat")
    else:
        print("       source vapi_agent_forge/backend/venv/bin/activate")
    print("       cd vapi_agent_forge/backend && python main.py")
    print()
    print("   Option 3 - Use the updated startup script:")
    print("     python start_system.py")
    print()

if __name__ == "__main__":
    main() 