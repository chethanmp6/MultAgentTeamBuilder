"""
Real-time Validation and Configuration Preview
"""
import streamlit as st
import yaml
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from .enhanced_agent_library import EnhancedAgentLibrary
from ..config.dynamic_template_generator import DynamicTemplateGenerator


class RealTimeValidator:
    """Real-time validation for team compositions and configurations."""
    
    def __init__(self, agent_library: EnhancedAgentLibrary, template_generator: DynamicTemplateGenerator):
        self.agent_library = agent_library
        self.template_generator = template_generator
        
    def validate_composition_live(self, composition: Dict[str, Any]) -> Dict[str, Any]:
        """Perform live validation of team composition."""
        validation = {
            "status": "valid",
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "completeness": 0.0,
            "recommendations": []
        }
        
        # Check coordinator
        coordinator_score = self._validate_coordinator(composition, validation)
        
        # Check teams
        teams_score = self._validate_teams(composition, validation)
        
        # Check overall balance
        balance_score = self._validate_balance(composition, validation)
        
        # Calculate completeness
        validation["completeness"] = (coordinator_score + teams_score + balance_score) / 3
        
        # Set overall status
        if validation["errors"]:
            validation["status"] = "invalid"
        elif validation["warnings"]:
            validation["status"] = "warning"
        else:
            validation["status"] = "valid"
        
        return validation
    
    def _validate_coordinator(self, composition: Dict[str, Any], validation: Dict[str, Any]) -> float:
        """Validate coordinator selection."""
        score = 0.0
        
        coordinator = composition.get('coordinator')
        if not coordinator:
            validation["errors"].append("No coordinator selected")
            return 0.0
        
        # Check if coordinator exists
        if coordinator not in self.agent_library.agents:
            validation["errors"].append(f"Coordinator '{coordinator}' not found")
            return 0.0
        
        coordinator_metadata = self.agent_library.agents[coordinator]
        
        # Check coordination capability
        if not coordinator_metadata.can_coordinate:
            validation["warnings"].append(f"'{coordinator_metadata.name}' may not be optimal as coordinator")
            score = 0.7
        else:
            score = 1.0
        
        # Check team size limits
        teams_count = len(composition.get('teams', {}))
        if coordinator_metadata.team_size_limit and teams_count > coordinator_metadata.team_size_limit:
            validation["warnings"].append(
                f"Team count ({teams_count}) exceeds coordinator's recommended limit ({coordinator_metadata.team_size_limit})"
            )
            score *= 0.9
        
        return score
    
    def _validate_teams(self, composition: Dict[str, Any], validation: Dict[str, Any]) -> float:
        """Validate teams configuration."""
        teams = composition.get('teams', {})
        
        if not teams:
            validation["errors"].append("No teams defined")
            return 0.0
        
        total_score = 0.0
        valid_teams = 0
        
        for team_id, team_data in teams.items():
            team_score = self._validate_single_team(team_id, team_data, validation)
            total_score += team_score
            if team_score > 0:
                valid_teams += 1
        
        return total_score / len(teams) if teams else 0.0
    
    def _validate_single_team(self, team_id: str, team_data: Dict[str, Any], validation: Dict[str, Any]) -> float:
        """Validate a single team."""
        score = 0.0
        team_name = team_data.get('name', f'Team {team_id}')
        
        # Check supervisor
        supervisor = team_data.get('supervisor')
        if not supervisor:
            validation["warnings"].append(f"Team '{team_name}' has no supervisor")
            score = 0.5
        else:
            if supervisor not in self.agent_library.agents:
                validation["errors"].append(f"Supervisor '{supervisor}' not found in team '{team_name}'")
                return 0.0
            
            supervisor_metadata = self.agent_library.agents[supervisor]
            if not supervisor_metadata.can_supervise:
                validation["warnings"].append(f"'{supervisor_metadata.name}' may not be optimal as supervisor in team '{team_name}'")
                score = 0.7
            else:
                score = 1.0
        
        # Check workers
        workers = team_data.get('workers', [])
        if not workers:
            validation["warnings"].append(f"Team '{team_name}' has no workers")
            score *= 0.6
        else:
            valid_workers = 0
            for worker_id in workers:
                if worker_id not in self.agent_library.agents:
                    validation["errors"].append(f"Worker '{worker_id}' not found in team '{team_name}'")
                else:
                    valid_workers += 1
            
            if valid_workers == 0:
                score = 0.0
            else:
                worker_ratio = valid_workers / len(workers)
                score *= worker_ratio
        
        return score
    
    def _validate_balance(self, composition: Dict[str, Any], validation: Dict[str, Any]) -> float:
        """Validate overall team balance and capabilities."""
        score = 1.0
        
        # Collect all capabilities
        all_capabilities = set()
        coordinator = composition.get('coordinator')
        if coordinator and coordinator in self.agent_library.agents:
            coordinator_metadata = self.agent_library.agents[coordinator]
            all_capabilities.update([cap.value for cap in coordinator_metadata.capabilities])
        
        total_agents = 1 if coordinator else 0
        
        for team_data in composition.get('teams', {}).values():
            supervisor = team_data.get('supervisor')
            if supervisor and supervisor in self.agent_library.agents:
                supervisor_metadata = self.agent_library.agents[supervisor]
                all_capabilities.update([cap.value for cap in supervisor_metadata.capabilities])
                total_agents += 1
            
            for worker_id in team_data.get('workers', []):
                if worker_id in self.agent_library.agents:
                    worker_metadata = self.agent_library.agents[worker_id]
                    all_capabilities.update([cap.value for cap in worker_metadata.capabilities])
                    total_agents += 1
        
        # Check essential capabilities
        essential_capabilities = {"web_search", "research", "writing"}
        missing_capabilities = essential_capabilities - all_capabilities
        
        if missing_capabilities:
            validation["suggestions"].append(
                f"Consider adding agents with: {', '.join(missing_capabilities)}"
            )
            score *= 0.9
        
        # Check team size balance
        if total_agents < 3:
            validation["warnings"].append("Team is quite small - consider adding more agents")
            score *= 0.8
        elif total_agents > 20:
            validation["warnings"].append("Team is quite large - consider splitting into smaller teams")
            score *= 0.9
        
        return score
    
    def generate_live_preview(self, composition: Dict[str, Any], team_name: str, team_description: str) -> Optional[str]:
        """Generate live YAML preview of the configuration."""
        try:
            if not composition.get('coordinator') or not composition.get('teams'):
                return None
            
            # Build teams data for template generator
            teams_data = []
            for team_id, team_data in composition['teams'].items():
                if team_data.get('supervisor'):
                    teams_data.append({
                        'name': team_data.get('name', f'Team {team_id}'),
                        'description': team_data.get('description', ''),
                        'supervisor_id': team_data['supervisor'],
                        'worker_ids': team_data.get('workers', []),
                        'specialization': 'general',
                        'max_workers': 10
                    })
            
            if not teams_data:
                return None
            
            # Create team configuration
            team_config = self.template_generator.create_team_config(
                team_name=team_name or "Dynamic Team",
                team_description=team_description or "Dynamically created team",
                coordinator_id=composition['coordinator'],
                teams_data=teams_data
            )
            
            # Generate YAML
            yaml_content = self.template_generator.generate_yaml_config(team_config)
            return yaml_content
            
        except Exception as e:
            return f"# Error generating preview: {str(e)}"
    
    def get_completion_suggestions(self, composition: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get suggestions for completing the team composition."""
        suggestions = []
        
        # Suggest coordinator if missing
        if not composition.get('coordinator'):
            coordinators = self.agent_library.get_coordinators()
            if coordinators:
                top_coordinator = max(coordinators.items(), key=lambda x: x[1].compatibility_score)
                suggestions.append({
                    "type": "coordinator",
                    "message": f"Add '{top_coordinator[1].name}' as coordinator",
                    "agent_id": top_coordinator[0],
                    "priority": "high"
                })
        
        # Suggest teams if missing
        if not composition.get('teams'):
            supervisors = self.agent_library.get_supervisors()
            if supervisors:
                top_supervisor = max(supervisors.items(), key=lambda x: x[1].compatibility_score)
                suggestions.append({
                    "type": "team",
                    "message": f"Create a team with '{top_supervisor[1].name}' as supervisor",
                    "agent_id": top_supervisor[0],
                    "priority": "high"
                })
        
        # Suggest workers for teams without workers
        for team_id, team_data in composition.get('teams', {}).items():
            if not team_data.get('workers'):
                workers = self.agent_library.get_workers()
                if workers:
                    # Get supervisor's compatible workers if supervisor exists
                    supervisor_id = team_data.get('supervisor')
                    if supervisor_id:
                        compatible_workers = self.agent_library.get_recommended_workers_for_supervisor(supervisor_id, 3)
                        if compatible_workers:
                            worker_id = compatible_workers[0]
                            worker_metadata = self.agent_library.agents[worker_id]
                            suggestions.append({
                                "type": "worker",
                                "message": f"Add '{worker_metadata.name}' to team '{team_data.get('name', team_id)}'",
                                "agent_id": worker_id,
                                "team_id": team_id,
                                "priority": "medium"
                            })
        
        return suggestions
    
    def calculate_team_metrics(self, composition: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate team composition metrics."""
        metrics = {
            "total_agents": 0,
            "coordinators": 0,
            "supervisors": 0,
            "workers": 0,
            "capabilities_coverage": 0.0,
            "avg_compatibility": 0.0,
            "team_balance_score": 0.0
        }
        
        all_capabilities = set()
        compatibility_scores = []
        
        # Count coordinator
        coordinator = composition.get('coordinator')
        if coordinator and coordinator in self.agent_library.agents:
            metrics["coordinators"] = 1
            metrics["total_agents"] += 1
            coordinator_metadata = self.agent_library.agents[coordinator]
            all_capabilities.update([cap.value for cap in coordinator_metadata.capabilities])
            compatibility_scores.append(coordinator_metadata.compatibility_score)
        
        # Count teams and workers
        for team_data in composition.get('teams', {}).values():
            supervisor = team_data.get('supervisor')
            if supervisor and supervisor in self.agent_library.agents:
                metrics["supervisors"] += 1
                metrics["total_agents"] += 1
                supervisor_metadata = self.agent_library.agents[supervisor]
                all_capabilities.update([cap.value for cap in supervisor_metadata.capabilities])
                compatibility_scores.append(supervisor_metadata.compatibility_score)
            
            for worker_id in team_data.get('workers', []):
                if worker_id in self.agent_library.agents:
                    metrics["workers"] += 1
                    metrics["total_agents"] += 1
                    worker_metadata = self.agent_library.agents[worker_id]
                    all_capabilities.update([cap.value for cap in worker_metadata.capabilities])
                    compatibility_scores.append(worker_metadata.compatibility_score)
        
        # Calculate capabilities coverage
        total_possible_capabilities = len(self.agent_library.get_statistics()['capabilities'])
        if total_possible_capabilities > 0:
            metrics["capabilities_coverage"] = len(all_capabilities) / total_possible_capabilities
        
        # Calculate average compatibility
        if compatibility_scores:
            metrics["avg_compatibility"] = sum(compatibility_scores) / len(compatibility_scores)
        
        # Calculate team balance score
        if metrics["total_agents"] > 0:
            # Ideal ratios: 1 coordinator, 20-40% supervisors, 60-80% workers
            coord_ratio = metrics["coordinators"] / metrics["total_agents"]
            supervisor_ratio = metrics["supervisors"] / metrics["total_agents"]
            worker_ratio = metrics["workers"] / metrics["total_agents"]
            
            coord_score = 1.0 if coord_ratio == 1/metrics["total_agents"] else 0.5
            supervisor_score = 1.0 if 0.2 <= supervisor_ratio <= 0.4 else 0.8
            worker_score = 1.0 if 0.6 <= worker_ratio <= 0.8 else 0.8
            
            metrics["team_balance_score"] = (coord_score + supervisor_score + worker_score) / 3
        
        return metrics