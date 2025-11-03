"""
Pydantic models for configuration-related API requests and responses
"""
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime

class ConfigValidationRequest(BaseModel):
    """Request model for configuration validation"""
    config_data: Dict[str, Any] = Field(..., description="Configuration data to validate")
    config_type: Literal["hierarchical", "single"] = Field("hierarchical", description="Type of configuration")

class ConfigValidationResponse(BaseModel):
    """Response model for configuration validation"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    config_type: str
    validated_at: datetime = Field(default_factory=datetime.utcnow)

class ConfigUploadRequest(BaseModel):
    """Request model for configuration file upload"""
    filename: str
    content_type: str
    file_size: int

class ConfigUploadResponse(BaseModel):
    """Response model for configuration upload"""
    file_id: str
    filename: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    validation_result: Optional[ConfigValidationResponse] = None

class TemplateInfo(BaseModel):
    """Information about a configuration template"""
    id: str
    name: str
    description: str
    type: Literal["hierarchical", "single"]
    file_path: str
    created_at: datetime
    team_count: Optional[int] = None
    worker_count: Optional[int] = None
    capabilities: List[str] = []

class TemplateListResponse(BaseModel):
    """Response model for listing templates"""
    templates: List[TemplateInfo]
    total: int

class TemplateResponse(BaseModel):
    """Response model for a specific template"""
    template: TemplateInfo
    config_data: Dict[str, Any]

class ConfigExportRequest(BaseModel):
    """Request model for exporting configuration"""
    team_id: str
    format: Literal["yaml", "json"] = "yaml"
    include_metadata: bool = True

class ConfigExportResponse(BaseModel):
    """Response model for configuration export"""
    team_id: str
    format: str
    content: str
    filename: str
    exported_at: datetime = Field(default_factory=datetime.utcnow)