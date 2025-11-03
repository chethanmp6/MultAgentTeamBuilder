#!/usr/bin/env python3
"""
Script to run the moved test files from the tests directory
"""
import subprocess
import sys
import os
from pathlib import Path

def run_test_file(test_file: str):
    """Run a specific test file from the tests directory."""
    test_path = Path("tests") / test_file
    
    if not test_path.exists():
        print(f"❌ Test file not found: {test_path}")
        return False
    
    print(f"🧪 Running {test_file}...")
    print("=" * 50)
    
    try:
        result = subprocess.run(
            [sys.executable, str(test_path)],
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ {test_file} completed successfully")
            return True
        else:
            print(f"❌ {test_file} failed with return code {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running {test_file}: {e}")
        return False

def main():
    """Main function to run moved test files."""
    print("🚀 Running Moved Test Files")
    print("=" * 50)
    
    # List of moved test files
    test_files = [
        "test_simple_builder.py",
        "validate_simple_team_builder.py", 
        "test_dynamic_builder.py",
        "validate_implementation.py"
    ]
    
    results = []
    
    for test_file in test_files:
        success = run_test_file(test_file)
        results.append((test_file, success))
        print()  # Add spacing between tests
    
    # Print summary
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_file, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {test_file}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All moved tests are working correctly!")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
    
    return passed == len(results)

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 