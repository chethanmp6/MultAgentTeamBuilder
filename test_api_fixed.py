#!/usr/bin/env python3
"""
Test script to verify the fixed API documentation works correctly
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api_workflow():
    """Test the complete API workflow with corrected format"""
    
    print("🚀 Testing Hierarchical Agent System API")
    print("=" * 50)
    
    # Step 1: Test health endpoint
    print("\n1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        response.raise_for_status()
        health = response.json()
        print(f"✅ API is healthy - Status: {health['status']}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False
    
    # Step 2: Create a team with correct format
    print("\n2. Creating a test team...")
    team_config = {
        "name": "API Test Team",
        "description": "Team created to test the corrected API documentation",
        "config_data": {
            "team": {
                "name": "API Test Team",
                "description": "Team created to test the corrected API documentation",
                "version": "1.0.0",
                "type": "hierarchical"
            },
            "coordinator": {
                "name": "API Test Coordinator",
                "description": "Coordinates test tasks for API validation",
                "llm": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "temperature": 0.3,
                    "api_key_env": "OPENAI_API_KEY"
                },
                "prompts": {
                    "system_prompt": {
                        "template": "You are a test coordinator managing API validation tasks."
                    },
                    "decision_prompt": {
                        "template": "Route this API test task: {user_input}"
                    }
                }
            },
            "teams": [
                {
                    "name": "Test Execution Team",
                    "description": "Team that executes API test scenarios",
                    "supervisor": {
                        "name": "Test Supervisor",
                        "description": "Supervises API test execution",
                        "config_file": "configs/examples/research_supervisor.yml"
                    },
                    "workers": [
                        {
                            "name": "API Tester",
                            "role": "worker",
                            "description": "Executes API validation tests",
                            "capabilities": ["testing", "validation", "api_testing"],
                            "config_file": "configs/examples/web_browser_agent.yml"
                        }
                    ]
                }
            ]
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/teams/", json=team_config, timeout=10)
        response.raise_for_status()
        team = response.json()
        team_id = team["id"]
        print(f"✅ Team created successfully - ID: {team_id}")
    except Exception as e:
        print(f"❌ Team creation failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return False
    
    # Step 3: Execute a task with correct format
    print("\n3. Executing a test task...")
    execution_request = {
        "input_text": "Provide a summary of the benefits of using hierarchical agent systems for complex tasks",
        "parameters": {
            "format": "bullet_points",
            "target_audience": "software developers",
            "detail_level": "intermediate"
        },
        "timeout_seconds": 120
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/executions/{team_id}/execute", 
            json=execution_request, 
            timeout=10
        )
        response.raise_for_status()
        execution = response.json()
        execution_id = execution["execution_id"]
        print(f"✅ Task execution started - ID: {execution_id}")
        print(f"   Status: {execution['status']['status']}")
    except Exception as e:
        print(f"❌ Task execution failed: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"   Response: {e.response.text}")
        return False
    
    # Step 4: Check execution status
    print("\n4. Checking execution status...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/executions/{execution_id}", timeout=5)
        response.raise_for_status()
        status = response.json()
        print(f"✅ Execution status retrieved")
        print(f"   Status: {status.get('status', {}).get('status', 'unknown')}")
        print(f"   Progress: {status.get('status', {}).get('progress', 0)}%")
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return False
    
    # Step 5: Test team listing
    print("\n5. Testing team listing...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/teams/", timeout=5)
        response.raise_for_status()
        teams = response.json()
        print(f"✅ Team listing successful")
        print(f"   Found {len(teams)} teams")
    except Exception as e:
        print(f"❌ Team listing failed: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 All API tests passed! Documentation is now accurate.")
    print("\nKey corrections made:")
    print("• Team creation uses 'config_data' field with full hierarchical schema")
    print("• Task execution uses 'input_text' field instead of 'task'")
    print("• Parameters are passed in 'parameters' object")
    print("• All examples updated to match actual API implementation")
    
    return True

if __name__ == "__main__":
    success = test_api_workflow()
    exit(0 if success else 1)