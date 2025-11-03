"""
API Configuration settings
"""
import os
from typing import Optional
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class APIConfig(BaseModel):
    """API configuration settings"""
    
    # Server settings
    host: str = os.getenv("API_HOST", "0.0.0.0")
    port: int = int(os.getenv("API_PORT", "8000"))
    debug: bool = os.getenv("API_DEBUG", "false").lower() == "true"
    
    # CORS settings
    cors_origins: list = ["*"]  # In production, specify exact origins
    
    # File upload settings
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    allowed_file_types: list = [".yml", ".yaml", ".json"]
    
    # Execution settings
    default_timeout: int = 600  # 10 minutes
    max_concurrent_executions: int = 10
    
    # Storage settings (in production, use a proper database)
    storage_type: str = "memory"  # memory, sqlite, postgresql, etc.
    
    # Security settings
    enable_api_keys: bool = os.getenv("ENABLE_API_KEYS", "false").lower() == "true"
    api_key_header: str = "X-API-Key"
    
    # Logging settings
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    enable_request_logging: bool = True
    
    # Template directories
    template_directories: list = [
        "configs/examples/hierarchical",
        "configs/templates"
    ]
    
    # Agent library settings
    agent_library_directory: str = "configs/examples"