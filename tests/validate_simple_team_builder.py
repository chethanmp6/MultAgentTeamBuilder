#!/usr/bin/env python3
"""
Quick validation script for Simple Team Builder
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def validate_dependencies():
    """Validate that all required dependencies are available."""
    print("🔍 Validating dependencies...")
    
    required_modules = [
        'streamlit',
        'yaml', 
        'langchain_core',
        'langchain',
        'langgraph',
        'plotly'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError:
            print(f"  ❌ {module}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n❌ Missing modules: {', '.join(missing_modules)}")
        print("💡 Run: pip install -r requirements.txt")
        return False
    
    print("✅ All dependencies available")
    return True

def validate_configs():
    """Validate that agent configurations are available."""
    print("\n🔍 Validating agent configurations...")
    
    config_dir = Path("configs/examples")
    if not config_dir.exists():
        print("❌ configs/examples directory not found")
        return False
    
    yaml_files = list(config_dir.glob("*.yml"))
    if not yaml_files:
        print("❌ No .yml files found in configs/examples/")
        return False
    
    print(f"✅ Found {len(yaml_files)} configuration files:")
    for file in yaml_files:
        print(f"  📄 {file.name}")
    
    return True

def validate_modules():
    """Validate that all required modules can be imported."""
    print("\n🔍 Validating module imports...")
    
    required_modules = [
        'src.ui.simple_team_builder',
        'src.config.simple_template_generator',
        'src.ui.enhanced_agent_library',
        'src.ui.agent_role_classifier',
        'src.core.config_loader',
        'src.hierarchical.hierarchical_agent'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
            print(f"  ✅ {module}")
        except ImportError as e:
            print(f"  ❌ {module}: {e}")
            missing_modules.append(module)
    
    if missing_modules:
        print(f"\n❌ Missing modules: {', '.join(missing_modules)}")
        return False
    
    print("✅ All modules can be imported")
    return True

def validate_web_ui():
    """Validate that the web UI can be started."""
    print("\n🔍 Validating web UI...")
    
    try:
        # Test if we can import the web UI
        import hierarchical_web_ui
        print("  ✅ hierarchical_web_ui.py can be imported")
        
        # Test if streamlit can run
        import streamlit as st
        print("  ✅ Streamlit is available")
        
        return True
    except Exception as e:
        print(f"  ❌ Web UI validation failed: {e}")
        return False

def main():
    """Main validation function."""
    print("🚀 Simple Team Builder Validation")
    print("=" * 50)
    
    checks = [
        ("Dependencies", validate_dependencies),
        ("Configurations", validate_configs),
        ("Modules", validate_modules),
        ("Web UI", validate_web_ui)
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"❌ {name} check failed with error: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 50)
    print("📊 Validation Results:")
    
    passed = 0
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"  {name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} checks passed")
    
    if passed == len(results):
        print("🎉 All validations passed! Simple Team Builder should work correctly.")
        print("\n🚀 To start the Simple Team Builder:")
        print("   python run_simple_team_builder.py")
        print("   or")
        print("   streamlit run hierarchical_web_ui.py")
    else:
        print("❌ Some validations failed. Please check the errors above.")
        print("\n💡 Common solutions:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Activate virtual environment: source .venv/bin/activate")
        print("   3. Check file permissions and paths")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 