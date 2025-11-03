"""
HTTP client for communicating with the Hierarchical Agent System API
"""
import httpx
import json
import os
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import streamlit as st
import logging

logger = logging.getLogger(__name__)

class APIClient:
    """HTTP client for the Hierarchical Agent System API"""
    
    def __init__(self, base_url: str = None, timeout: int = 60):
        """Initialize API client"""
        self.base_url = base_url or os.getenv("API_BASE_URL", "http://localhost:8000")
        self.timeout = timeout
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Add API key if configured
        api_key = os.getenv("API_KEY")
        if api_key:
            self.headers["X-API-Key"] = api_key
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except:
                error_detail = str(e)
            
            logger.error(f"API request failed: {method} {url} - {error_detail}")
            raise APIError(f"API request failed: {error_detail}", status_code=e.response.status_code)
            
        except httpx.RequestError as e:
            logger.error(f"Network error: {method} {url} - {str(e)}")
            raise APIError(f"Network error: {str(e)}")
    
    def _make_sync_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make synchronous HTTP request to API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    **kwargs
                )
                response.raise_for_status()
                return response.json()
                
        except httpx.HTTPStatusError as e:
            error_detail = "Unknown error"
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", str(e))
            except:
                error_detail = str(e)
            
            logger.error(f"API request failed: {method} {url} - {error_detail}")
            raise APIError(f"API request failed: {error_detail}", status_code=e.response.status_code)
            
        except httpx.RequestError as e:
            logger.error(f"Network error: {method} {url} - {str(e)}")
            raise APIError(f"Network error: {str(e)}")
    
    # Team Management Methods
    def create_team(self, name: str, description: str = None, config_data: Dict[str, Any] = None, 
                   config_file_path: str = None, template_id: str = None) -> Dict[str, Any]:
        """Create a new hierarchical team"""
        payload = {
            "name": name,
            "description": description,
            "config_data": config_data,
            "config_file_path": config_file_path,
            "template_id": template_id
        }
        return self._make_sync_request("POST", "/api/v1/teams/", json=payload)
    
    def get_team(self, team_id: str) -> Dict[str, Any]:
        """Get a specific team"""
        return self._make_sync_request("GET", f"/api/v1/teams/{team_id}")
    
    def list_teams(self, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """List all teams"""
        params = {"limit": limit, "offset": offset}
        return self._make_sync_request("GET", "/api/v1/teams/", params=params)
    
    def update_team(self, team_id: str, name: str = None, description: str = None, 
                   config_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update a team"""
        payload = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description"] = description
        if config_data is not None:
            payload["config_data"] = config_data
            
        return self._make_sync_request("PUT", f"/api/v1/teams/{team_id}", json=payload)
    
    def delete_team(self, team_id: str) -> Dict[str, Any]:
        """Delete a team"""
        return self._make_sync_request("DELETE", f"/api/v1/teams/{team_id}")
    
    def get_team_status(self, team_id: str) -> Dict[str, Any]:
        """Get team status"""
        return self._make_sync_request("GET", f"/api/v1/teams/{team_id}/status")
    
    # Configuration Methods
    def validate_config(self, config_data: Dict[str, Any], config_type: str = "hierarchical") -> Dict[str, Any]:
        """Validate a configuration"""
        payload = {
            "config_data": config_data,
            "config_type": config_type
        }
        return self._make_sync_request("POST", "/api/v1/configs/validate", json=payload)
    
    def upload_config(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        """Upload a configuration file"""
        files = {"file": (filename, file_content)}
        
        # Remove content-type header for file upload
        headers = {k: v for k, v in self.headers.items() if k.lower() != "content-type"}
        
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(
                    f"{self.base_url}/api/v1/configs/upload",
                    headers=headers,
                    files=files
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            raise APIError(f"Failed to upload config: {str(e)}")
    
    def upload_config_from_streamlit(self, uploaded_file) -> Dict[str, Any]:
        """Upload a configuration file from Streamlit file uploader"""
        if uploaded_file is not None:
            file_content = uploaded_file.read()
            return self.upload_config(file_content, uploaded_file.name)
        else:
            raise APIError("No file provided")
    
    def list_templates(self) -> Dict[str, Any]:
        """List available configuration templates"""
        return self._make_sync_request("GET", "/api/v1/configs/templates")
    
    def get_template(self, template_id: str) -> Dict[str, Any]:
        """Get a specific configuration template"""
        return self._make_sync_request("GET", f"/api/v1/configs/templates/{template_id}")
    
    def export_config(self, team_id: str, format: str = "yaml", include_metadata: bool = True) -> Dict[str, Any]:
        """Export a team configuration"""
        payload = {
            "team_id": team_id,
            "format": format,
            "include_metadata": include_metadata
        }
        return self._make_sync_request("POST", "/api/v1/configs/export", json=payload)
    
    # Agent Library Methods
    def search_agents(self, query: str = None, capabilities: List[str] = None, role: str = None,
                     limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """Search agents"""
        payload = {
            "query": query,
            "capabilities": capabilities,
            "role": role,
            "limit": limit,
            "offset": offset
        }
        return self._make_sync_request("POST", "/api/v1/agents/search", json=payload)
    
    def list_agents(self, query: str = None, role: str = None, capabilities: str = None,
                   limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """List agents with optional filtering"""
        params = {
            "limit": limit,
            "offset": offset
        }
        if query:
            params["query"] = query
        if role:
            params["role"] = role
        if capabilities:
            params["capabilities"] = capabilities
            
        return self._make_sync_request("GET", "/api/v1/agents/", params=params)
    
    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific agent"""
        return self._make_sync_request("GET", f"/api/v1/agents/{agent_id}")
    
    def check_agent_compatibility(self, agent_ids: List[str]) -> Dict[str, Any]:
        """Check compatibility between agents"""
        payload = {"agent_ids": agent_ids}
        return self._make_sync_request("POST", "/api/v1/agents/compatibility", json=payload)
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Get statistics about the agent library"""
        return self._make_sync_request("GET", "/api/v1/agents/stats")
    
    def get_team_suggestions(self, task_description: str, preferred_team_size: int = None,
                           required_capabilities: List[str] = None, team_type: str = "hierarchical") -> Dict[str, Any]:
        """Get team composition suggestions for a task"""
        payload = {
            "task_description": task_description,
            "preferred_team_size": preferred_team_size,
            "required_capabilities": required_capabilities,
            "team_type": team_type
        }
        return self._make_sync_request("POST", "/api/v1/agents/team-suggestions", json=payload)
    
    # Execution Methods
    def execute_task(self, team_id: str, input_text: str, worker_id: str = None,
                    timeout_seconds: int = None, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a task on a hierarchical team"""
        payload = {
            "input_text": input_text,
            "worker_id": worker_id,
            "timeout_seconds": timeout_seconds,
            "parameters": parameters
        }
        return self._make_sync_request("POST", f"/api/v1/executions/{team_id}/execute", json=payload)
    
    def execute_worker_task(self, team_id: str, worker_id: str, input_text: str,
                           timeout_seconds: int = None, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a task on a specific worker"""
        payload = {
            "input_text": input_text,
            "timeout_seconds": timeout_seconds,
            "parameters": parameters
        }
        return self._make_sync_request("POST", f"/api/v1/executions/{team_id}/workers/{worker_id}/execute", json=payload)
    
    def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """Get execution status and results"""
        return self._make_sync_request("GET", f"/api/v1/executions/{execution_id}")
    
    def list_executions(self, team_id: str = None, status: str = None, limit: int = 50,
                       offset: int = 0, order_by: str = "created_at", order_direction: str = "desc") -> Dict[str, Any]:
        """List executions with filtering and pagination"""
        params = {
            "limit": limit,
            "offset": offset,
            "order_by": order_by,
            "order_direction": order_direction
        }
        if team_id:
            params["team_id"] = team_id
        if status:
            params["status"] = status
            
        return self._make_sync_request("GET", "/api/v1/executions/", params=params)
    
    def cancel_execution(self, execution_id: str, reason: str = None) -> Dict[str, Any]:
        """Cancel a running execution"""
        payload = {"reason": reason}
        return self._make_sync_request("POST", f"/api/v1/executions/{execution_id}/cancel", json=payload)
    
    # Health Check Methods
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        return self._make_sync_request("GET", "/health")
    
    def get_api_info(self) -> Dict[str, Any]:
        """Get API information"""
        return self._make_sync_request("GET", "/")


class APIError(Exception):
    """API-specific exception"""
    def __init__(self, message: str, status_code: int = None):
        super().__init__(message)
        self.status_code = status_code


# Singleton instance for Streamlit
@st.cache_resource
def get_api_client() -> APIClient:
    """Get cached API client instance"""
    return APIClient()


# Helper functions for Streamlit integration
def handle_api_error(func):
    """Decorator to handle API errors in Streamlit"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except APIError as e:
            st.error(f"API Error: {str(e)}")
            if e.status_code:
                st.error(f"Status Code: {e.status_code}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {str(e)}")
            return None
    return wrapper