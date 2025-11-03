#!/usr/bin/env python3
"""
Launch script for the Hierarchical Agent System API server
"""
import os
import sys
import subprocess
import logging

def check_dependencies():
    """Check if required dependencies are available."""
    try:
        import fastapi
        import uvicorn
        return True
    except ImportError:
        return False

def main():
    """Main function to launch the API server."""
    print("🚀 Starting Hierarchical Agent System API server...")
    
    # Check if dependencies are available
    if not check_dependencies():
        print("❌ Required dependencies not found.")
        print("🔧 Please install dependencies: pip install -r requirements.txt")
        return
    
    # Set environment variables if not already set
    if not os.getenv("API_HOST"):
        os.environ["API_HOST"] = "0.0.0.0"
    if not os.getenv("API_PORT"):
        os.environ["API_PORT"] = "8000"
    
    # Configure logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    print(f"✅ Starting API server on {os.getenv('API_HOST')}:{os.getenv('API_PORT')}")
    print(f"📚 API documentation will be available at http://localhost:{os.getenv('API_PORT')}/docs")
    print(f"🔧 Log level: {log_level}")
    
    try:
        import uvicorn
        
        # Use import string for reload functionality
        uvicorn.run(
            "api.server:app",
            host=os.getenv("API_HOST", "0.0.0.0"),
            port=int(os.getenv("API_PORT", "8000")),
            log_level=log_level.lower(),
            reload=True
        )
    except KeyboardInterrupt:
        print("\n👋 API server stopped by user.")
    except Exception as e:
        print(f"❌ Error starting API server: {e}")

if __name__ == "__main__":
    main()