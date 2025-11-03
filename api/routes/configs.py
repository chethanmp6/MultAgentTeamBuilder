"""
Configuration management API routes
"""
from fastapi import APIRouter, HTTPException, Depends, Request, File, UploadFile
from typing import Optional

from ..models.config_models import (
    ConfigValidationRequest, ConfigValidationResponse,
    ConfigUploadResponse, TemplateListResponse, TemplateResponse,
    ConfigExportRequest, ConfigExportResponse
)
from ..services.config_service import ConfigService

router = APIRouter()

def get_config_service(request: Request) -> ConfigService:
    """Dependency to get config service"""
    return ConfigService(request.app.app_state, request.app.app_state["config"])

@router.post("/validate", response_model=ConfigValidationResponse)
async def validate_config(
    request: ConfigValidationRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Validate a configuration"""
    try:
        return await config_service.validate_config(request)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate config: {str(e)}")

@router.post("/upload", response_model=ConfigUploadResponse)
async def upload_config(
    file: UploadFile = File(...),
    config_service: ConfigService = Depends(get_config_service)
):
    """Upload a configuration file"""
    try:
        # Validate file type
        if not file.filename.endswith(('.yml', '.yaml', '.json')):
            raise HTTPException(
                status_code=400, 
                detail="Invalid file type. Only .yml, .yaml, and .json files are supported"
            )
        
        # Read file content
        content = await file.read()
        
        return await config_service.upload_config(file.filename, content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload config: {str(e)}")

@router.get("/templates", response_model=TemplateListResponse)
async def list_templates(
    config_service: ConfigService = Depends(get_config_service)
):
    """List available configuration templates"""
    try:
        return await config_service.list_templates()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list templates: {str(e)}")

@router.get("/templates/{template_id}", response_model=TemplateResponse)
async def get_template(
    template_id: str,
    config_service: ConfigService = Depends(get_config_service)
):
    """Get a specific configuration template"""
    try:
        template = await config_service.get_template(template_id)
        if not template:
            raise HTTPException(status_code=404, detail=f"Template {template_id} not found")
        return template
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")

@router.post("/export", response_model=ConfigExportResponse)
async def export_config(
    request: ConfigExportRequest,
    config_service: ConfigService = Depends(get_config_service)
):
    """Export a team configuration"""
    try:
        result = await config_service.export_config(request)
        if not result:
            raise HTTPException(status_code=404, detail=f"Team {request.team_id} not found or has no configuration")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export config: {str(e)}")