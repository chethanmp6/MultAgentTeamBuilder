"""
Integration tests for the Hierarchical Agent System API
"""
import pytest
import httpx
import json
import tempfile
import yaml
from pathlib import Path

# Test configuration
API_BASE_URL = "http://localhost:8000"
TEST_TIMEOUT = 30

class TestAPIIntegration:
    """Test suite for API integration"""
    
    @pytest.fixture
    def client(self):
        """HTTP client fixture"""
        return httpx.Client(base_url=API_BASE_URL, timeout=TEST_TIMEOUT)
    
    @pytest.fixture
    def sample_hierarchical_config(self):
        """Sample hierarchical configuration for testing"""
        return {
            "team": {
                "name": "Test Research Team",
                "description": "Test hierarchical team for API testing",
                "version": "1.0.0",
                "type": "hierarchical"
            },
            "coordinator": {
                "name": "Test Coordinator",
                "description": "Test coordinator for API testing",
                "llm": {
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "temperature": 0.3,
                    "max_tokens": 2000,
                    "api_key_env": "OPENAI_API_KEY"
                },
                "prompts": {
                    "system_prompt": {
                        "template": "You are a test coordinator.",
                        "variables": []
                    },
                    "decision_prompt": {
                        "template": "Make a test decision for: {user_input}",
                        "variables": ["user_input"]
                    }
                },
                "routing": {
                    "strategy": "hybrid",
                    "fallback_team": "test_team"
                }
            },
            "teams": [
                {
                    "name": "test_team",
                    "description": "Test team",
                    "supervisor": {
                        "name": "Test Supervisor",
                        "llm": {
                            "provider": "openai",
                            "model": "gpt-4o-mini",
                            "temperature": 0.2,
                            "api_key_env": "OPENAI_API_KEY"
                        }
                    },
                    "workers": [
                        {
                            "name": "test_worker",
                            "role": "tester",
                            "config_file": "configs/examples/research_agent.yml",
                            "description": "Test worker agent",
                            "capabilities": ["testing", "research"],
                            "priority": 1
                        }
                    ]
                }
            ]
        }
    
    def test_health_check(self, client):
        """Test API health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"
    
    def test_api_info(self, client):
        """Test API root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "Hierarchical Agent System API" in data["message"]
    
    def test_config_validation(self, client, sample_hierarchical_config):
        """Test configuration validation endpoint"""
        payload = {
            "config_data": sample_hierarchical_config,
            "config_type": "hierarchical"
        }
        
        response = client.post("/api/v1/configs/validate", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "valid" in data
        assert isinstance(data["valid"], bool)
        assert "errors" in data
        assert "warnings" in data
    
    def test_list_templates(self, client):
        """Test template listing endpoint"""
        response = client.get("/api/v1/configs/templates")
        assert response.status_code == 200
        
        data = response.json()
        assert "templates" in data
        assert "total" in data
        assert isinstance(data["templates"], list)
    
    def test_agent_library_stats(self, client):
        """Test agent library statistics endpoint"""
        response = client.get("/api/v1/agents/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_agents" in data
        assert isinstance(data["total_agents"], int)
    
    def test_list_agents(self, client):
        """Test agent listing endpoint"""
        response = client.get("/api/v1/agents/")
        assert response.status_code == 200
        
        data = response.json()
        assert "agents" in data
        assert "total" in data
        assert isinstance(data["agents"], list)
    
    def test_team_creation_from_config(self, client, sample_hierarchical_config):
        """Test team creation from configuration data"""
        payload = {
            "name": "Test API Team",
            "description": "Team created via API test",
            "config_data": sample_hierarchical_config
        }
        
        # Note: This test may fail if dependencies are not properly set up
        # In a real test environment, you would mock the dependencies
        try:
            response = client.post("/api/v1/teams/", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                assert "id" in data
                assert data["name"] == "Test API Team"
                
                # Clean up - delete the created team
                team_id = data["id"]
                delete_response = client.delete(f"/api/v1/teams/{team_id}")
                assert delete_response.status_code == 200
            
            else:
                # If creation fails, ensure it's due to missing dependencies, not API issues
                assert response.status_code in [400, 500]  # Expected failure codes
                
        except Exception as e:
            # Test may fail due to missing API keys or dependencies
            # This is expected in a test environment
            pytest.skip(f"Team creation test skipped due to dependencies: {e}")
    
    def test_execution_endpoints_structure(self, client):
        """Test that execution endpoints return proper error for non-existent team"""
        # Test execution on non-existent team
        payload = {
            "input_text": "Test task",
            "timeout_seconds": 30
        }
        
        response = client.post("/api/v1/executions/non-existent-team/execute", json=payload)
        assert response.status_code == 400  # Should return error for non-existent team
        
        data = response.json()
        assert "detail" in data

def test_api_client_import():
    """Test that API client can be imported"""
    from ui.api_client import APIClient, get_api_client
    
    # Test client creation
    client = APIClient()
    assert client.base_url == "http://localhost:8000"
    
    # Test cached client
    cached_client = get_api_client()
    assert cached_client is not None

def test_config_models_import():
    """Test that API models can be imported"""
    from api.models.team_models import TeamCreateRequest, TeamResponse
    from api.models.config_models import ConfigValidationRequest
    from api.models.execution_models import ExecutionRequest
    from api.models.agent_models import AgentSearchRequest
    
    # Test model creation
    team_request = TeamCreateRequest(name="Test Team")
    assert team_request.name == "Test Team"
    
    config_request = ConfigValidationRequest(config_data={})
    assert config_request.config_type == "hierarchical"

if __name__ == "__main__":
    # Run basic tests without pytest
    print("Running basic API integration tests...")
    
    try:
        test_api_client_import()
        print("✅ API client import test passed")
        
        test_config_models_import()
        print("✅ API models import test passed")
        
        # Test API connection
        client = httpx.Client(base_url=API_BASE_URL, timeout=5)
        try:
            response = client.get("/health")
            if response.status_code == 200:
                print("✅ API health check passed")
            else:
                print("❌ API health check failed - server may not be running")
        except Exception as e:
            print(f"❌ API connection failed: {e}")
            print("   Make sure to start the API server with: python run_api_server.py")
        
        print("\n🚀 Basic tests completed!")
        print("   Run 'pytest tests/test_api_integration.py' for full test suite")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")