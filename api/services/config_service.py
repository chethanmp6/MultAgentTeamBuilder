"""
Configuration service for managing hierarchical agent configurations
"""
import yaml
import json
import tempfile
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import logging

from src.core.hierarchical_config_loader import HierarchicalConfigLoader
from src.core.config_loader import ConfigLoader
from ..models.config_models import (
    ConfigValidationRequest, ConfigValidationResponse,
    ConfigUploadRequest, ConfigUploadResponse,
    TemplateInfo, TemplateListResponse, TemplateResponse,
    ConfigExportRequest, ConfigExportResponse
)

logger = logging.getLogger(__name__)

class ConfigService:
    """Service for managing configurations and templates"""
    
    def __init__(self, storage: Dict[str, Any], config: Any):
        """Initialize config service"""
        self.storage = storage
        self.config = config
        self.uploaded_files: Dict[str, Dict[str, Any]] = storage.get("uploaded_files", {})
    
    async def validate_config(self, request: ConfigValidationRequest) -> ConfigValidationResponse:
        """Validate a configuration"""
        errors = []
        warnings = []
        
        try:
            if request.config_type == "hierarchical":
                # Use HierarchicalConfigLoader for validation
                loader = HierarchicalConfigLoader()
                
                # Create temp file for validation
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                    yaml.dump(request.config_data, f, default_flow_style=False)
                    temp_path = f.name
                
                try:
                    config = loader.load_config(temp_path)
                    
                    # Additional validation checks
                    if not config.teams:
                        warnings.append("No teams configured")
                    
                    if config.coordinator.llm.api_key_env:
                        if not os.getenv(config.coordinator.llm.api_key_env):
                            warnings.append(f"Environment variable {config.coordinator.llm.api_key_env} not set")
                    
                    # Check worker config files exist
                    for team in config.teams:
                        for worker in team.workers:
                            if not Path(worker.config_file).exists():
                                alt_path = Path(f"configs/examples/{worker.config_file}")
                                if not alt_path.exists():
                                    warnings.append(f"Worker config file not found: {worker.config_file}")
                    
                finally:
                    os.unlink(temp_path)
            
            else:
                # Use regular ConfigLoader for single agent validation
                loader = ConfigLoader()
                result = loader.validate_config(request.config_data)
                if not result:
                    errors.append("Configuration validation failed")
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
        
        return ConfigValidationResponse(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            config_type=request.config_type
        )
    
    async def upload_config(self, filename: str, content: bytes) -> ConfigUploadResponse:
        """Upload and process a configuration file"""
        try:
            # Generate file ID
            file_id = f"upload_{int(datetime.utcnow().timestamp())}"
            
            # Parse content based on file extension
            if filename.endswith(('.yml', '.yaml')):
                config_data = yaml.safe_load(content.decode('utf-8'))
            elif filename.endswith('.json'):
                config_data = json.loads(content.decode('utf-8'))
            else:
                raise ValueError("Unsupported file format. Use .yml, .yaml, or .json")
            
            # Determine config type
            config_type = "hierarchical" if "coordinator" in config_data else "single"
            
            # Validate the configuration
            validation_request = ConfigValidationRequest(
                config_data=config_data,
                config_type=config_type
            )
            validation_result = await self.validate_config(validation_request)
            
            # Store file info
            file_info = {
                "id": file_id,
                "filename": filename,
                "content": config_data,
                "config_type": config_type,
                "uploaded_at": datetime.utcnow(),
                "validation_result": validation_result
            }
            self.uploaded_files[file_id] = file_info
            
            return ConfigUploadResponse(
                file_id=file_id,
                filename=filename,
                validation_result=validation_result
            )
            
        except Exception as e:
            logger.error(f"Failed to upload config: {e}")
            raise ValueError(f"Failed to upload configuration: {str(e)}")
    
    async def list_templates(self) -> TemplateListResponse:
        """List available configuration templates"""
        templates = []
        
        # Search in configured template directories
        for template_dir in self.config.template_directories:
            template_path = Path(template_dir)
            if not template_path.exists():
                continue
            
            for template_file in template_path.glob("*.yml"):
                try:
                    template_info = await self._load_template_info(template_file)
                    if template_info:
                        templates.append(template_info)
                except Exception as e:
                    logger.warning(f"Failed to load template {template_file}: {e}")
        
        return TemplateListResponse(
            templates=templates,
            total=len(templates)
        )
    
    async def get_template(self, template_id: str) -> Optional[TemplateResponse]:
        """Get a specific template"""
        # Search for template file
        template_file = None
        for template_dir in self.config.template_directories:
            template_path = Path(template_dir) / f"{template_id}.yml"
            if template_path.exists():
                template_file = template_path
                break
        
        if not template_file:
            return None
        
        try:
            template_info = await self._load_template_info(template_file)
            if not template_info:
                return None
            
            # Load configuration data
            with open(template_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            return TemplateResponse(
                template=template_info,
                config_data=config_data
            )
            
        except Exception as e:
            logger.error(f"Failed to load template {template_id}: {e}")
            return None
    
    async def export_config(self, request: ConfigExportRequest) -> Optional[ConfigExportResponse]:
        """Export a team configuration"""
        # Get team configuration from storage
        teams = self.storage.get("teams", {})
        team_metadata = self.storage.get("team_metadata", {})
        
        if request.team_id not in teams:
            return None
        
        metadata = team_metadata.get(request.team_id, {})
        config_data = metadata.get("config_data", {})
        
        if not config_data:
            return None
        
        try:
            # Format content based on requested format
            if request.format == "json":
                content = json.dumps(config_data, indent=2)
                filename = f"{request.team_id}_config.json"
            else:
                content = yaml.dump(config_data, default_flow_style=False, indent=2)
                filename = f"{request.team_id}_config.yml"
            
            # Add metadata if requested
            if request.include_metadata:
                export_metadata = {
                    "exported_at": datetime.utcnow().isoformat(),
                    "team_id": request.team_id,
                    "team_name": metadata.get("name", "Unknown"),
                    "original_created_at": metadata.get("created_at", datetime.utcnow()).isoformat()
                }
                
                if request.format == "json":
                    config_with_metadata = {
                        "metadata": export_metadata,
                        "configuration": config_data
                    }
                    content = json.dumps(config_with_metadata, indent=2)
                else:
                    content = f"# Exported configuration\n# {yaml.dump(export_metadata, default_flow_style=False)}\n{content}"
            
            return ConfigExportResponse(
                team_id=request.team_id,
                format=request.format,
                content=content,
                filename=filename
            )
            
        except Exception as e:
            logger.error(f"Failed to export config for team {request.team_id}: {e}")
            return None
    
    async def _load_template_info(self, template_file: Path) -> Optional[TemplateInfo]:
        """Load template information from a file"""
        try:
            with open(template_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            # Extract template information
            team_info = config_data.get('team', {})
            template_id = template_file.stem
            
            # Determine type
            config_type = "hierarchical" if "coordinator" in config_data else "single"
            
            # Count teams and workers
            team_count = len(config_data.get('teams', []))
            worker_count = 0
            capabilities = set()
            
            for team in config_data.get('teams', []):
                workers = team.get('workers', [])
                worker_count += len(workers)
                for worker in workers:
                    capabilities.update(worker.get('capabilities', []))
            
            return TemplateInfo(
                id=template_id,
                name=team_info.get('name', template_id),
                description=team_info.get('description', 'No description'),
                type=config_type,
                file_path=str(template_file),
                created_at=datetime.fromtimestamp(template_file.stat().st_mtime),
                team_count=team_count,
                worker_count=worker_count,
                capabilities=list(capabilities)
            )
            
        except Exception as e:
            logger.error(f"Failed to load template info from {template_file}: {e}")
            return None