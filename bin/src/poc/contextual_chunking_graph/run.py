#!/usr/bin/env python3
"""
Simple runner script for the Contextual Chunking Graph-Powered RAG system.
This script sets up the environment and runs the application using uv.
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Main runner function."""
    project_dir = Path(__file__).parent
    os.chdir(project_dir)
    
    print("=== Setting up Contextual Chunking Graph-Powered RAG ===")
    
    # Check if .env file exists and has been configured
    env_file = project_dir / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
        if "<your-" in content:
            print("⚠️  Please configure your API keys in the .env file first!")
            print("   Edit .env and replace the placeholder values with your actual API keys.")
            return 1
    else:
        print("⚠️  .env file not found. Please create it from sample.env and add your API keys.")
        return 1
    
    print("✅ Environment file configured")
    
    # Check if uv is installed
    try:
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
        print("✅ uv is installed")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ uv is not installed. Please install it first:")
        print("   curl -LsSf https://astral.sh/uv/install.sh | sh")
        return 1
    
    # Install dependencies
    print("📦 Installing dependencies with uv...")
    try:
        subprocess.run(["uv", "sync"], check=True)
        print("✅ Dependencies installed")
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return 1
    
    # Run the application
    print("🚀 Starting the RAG system...")
    print("Note: If you encounter library errors, try running the demo first:")
    print("      uv run python demo.py")
    print()
    
    try:
        # First try to run a simple import test
        result = subprocess.run(
            ["uv", "run", "python", "-c", "import contextual_chunking_graph; print('Package imports OK')"], 
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            print("⚠️  Package import test failed:")
            print(result.stderr)
            print("\nThis might be due to missing system libraries.")
            print("Would you like to run the demo instead? (y/n): ", end="")
            choice = input().lower().strip()
            if choice in ['y', 'yes']:
                subprocess.run(["uv", "run", "python", "demo.py"], check=True)
                return 0
            else:
                print("You can try running:")
                print("  uv run python demo.py")
                print("  uv run python -m contextual_chunking_graph.main")
                return 1
        
        # If import test passes, run the main application
        subprocess.run(["uv", "run", "python", "-m", "contextual_chunking_graph.main"], check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to run application: {e}")
        print("\nTry running the demo instead:")
        print("  uv run python demo.py")
        return 1
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())