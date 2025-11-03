#!/usr/bin/env python3
"""
Launch script for the Simple Team Builder Web UI
"""
import subprocess
import sys
import os

def check_dependencies():
    """Check if required dependencies are available."""
    try:
        import streamlit
        import yaml
        import langchain_core
        print("✅ All dependencies are available")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False

def activate_venv_and_run():
    """Activate virtual environment and run Streamlit."""
    venv_path = os.path.join(os.path.dirname(__file__), '.venv')
    if os.path.exists(venv_path):
        print("🔧 Activating virtual environment...")
        if sys.platform == "win32":
            # Windows
            activate_script = os.path.join(venv_path, 'Scripts', 'activate.bat')
            cmd = f'"{activate_script}" && python -m streamlit run hierarchical_web_ui.py'
            subprocess.run(cmd, shell=True)
        else:
            # Unix/Linux/macOS
            activate_script = os.path.join(venv_path, 'bin', 'activate')
            cmd = f'source "{activate_script}" && python -m streamlit run hierarchical_web_ui.py'
            subprocess.run(cmd, shell=True, executable='/bin/bash')
    else:
        print("❌ Virtual environment not found. Please run: python3 -m venv .venv")
        print("Then: source .venv/bin/activate && pip install -r requirements.txt")

def main():
    """Main function to launch the Simple Team Builder Web UI."""
    print("🚀 Launching Simple Team Builder Web UI...")
    print("=" * 50)
    
    # Check dependencies
    if check_dependencies():
        print("✅ Dependencies check passed")
    else:
        print("❌ Dependencies check failed")
        print("🔧 Attempting to use virtual environment...")
        activate_venv_and_run()
        return
    
    # Launch the hierarchical web UI (which includes simple team builder)
    try:
        print("🌐 Starting Streamlit server...")
        print("📱 The Simple Team Builder will be available in your browser")
        print("🔗 URL: http://localhost:8501")
        print("=" * 50)
        
        # Run the hierarchical web UI which includes the simple team builder
        subprocess.run([sys.executable, "-m", "streamlit", "run", "hierarchical_web_ui.py"])
        
    except KeyboardInterrupt:
        print("\n👋 Simple Team Builder stopped by user.")
    except Exception as e:
        print(f"❌ Error starting Simple Team Builder: {e}")
        print("🔧 Attempting to use virtual environment...")
        activate_venv_and_run()

if __name__ == "__main__":
    main() 