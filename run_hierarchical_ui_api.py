#!/usr/bin/env python3
"""
Launch script for the Hierarchical Agent Teams Web UI (API Version)
"""
import subprocess
import sys
import os

def check_streamlit():
    """Check if Streamlit is available."""
    try:
        import streamlit
        return True
    except ImportError:
        return False

def main():
    """Main function to launch the Hierarchical Web UI (API Version)."""
    print("🏢 Launching Hierarchical Agent Teams Web UI (API Version)...")
    
    # Check if Streamlit is available
    if check_streamlit():
        print("✅ Streamlit is available. Starting Hierarchical Web UI (API Version)...")
        print("📝 This version uses REST APIs instead of direct function calls")
        print("🔧 Make sure the API server is running on http://localhost:8000")
        print("   You can start it with: python run_api_server.py")
        
        try:
            subprocess.run([sys.executable, "-m", "streamlit", "run", "hierarchical_web_ui_api_complete.py"])
        except KeyboardInterrupt:
            print("\n👋 Hierarchical Web UI (API Version) stopped by user.")
        except Exception as e:
            print(f"❌ Error starting Hierarchical Web UI (API Version): {e}")
    else:
        print("❌ Streamlit is not installed.")
        print("🔧 Please install dependencies: pip install -r requirements.txt")

if __name__ == "__main__":
    main()