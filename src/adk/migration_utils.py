"""
Utilities for migrating from LangChain/LangGraph to Google ADK.
"""
from typing import Dict, Any, List, Optional, Union
import json
from datetime import datetime

from .configurable_agent_adk import ADKConfigurableAgent
from .hierarchical.hierarchical_agent_adk import ADKHierarchicalAgentTeam
from .config_loader_adk import ADKConfigLoader


class LangChainToADKMigrator:
    """Utility class for migrating LangChain components to ADK."""

    def __init__(self):
        self.migration_log: List[Dict[str, Any]] = []
        self.config_loader = ADKConfigLoader()

    def migrate_agent(self, langchain_agent, preserve_memory: bool = True) -> ADKConfigurableAgent:
        """
        Migrate a LangChain ConfigurableAgent to ADK.

        Args:
            langchain_agent: LangChain ConfigurableAgent instance
            preserve_memory: Whether to migrate memory data

        Returns:
            ADKConfigurableAgent instance
        """
        migration_entry = {
            "component": "single_agent",
            "source": "langchain",
            "target": "adk",
            "timestamp": datetime.now().isoformat(),
            "status": "started"
        }

        try:
            # Extract configuration from LangChain agent
            lc_config = langchain_agent.get_config()

            # Convert configuration to ADK format
            adk_config_data = self._convert_agent_config(lc_config)

            # Create ADK agent
            adk_agent = ADKConfigurableAgent(config_data=adk_config_data)

            # Migrate memory if requested and available
            if preserve_memory:
                migration_result = adk_agent.migrate_from_langchain_agent(langchain_agent)
                migration_entry["memory_migration"] = migration_result

            migration_entry["status"] = "completed"
            migration_entry["target_agent"] = {
                "name": adk_agent.config.agent.name,
                "framework": "google-adk",
                "model": adk_agent.config.llm.model
            }

        except Exception as e:
            migration_entry["status"] = "failed"
            migration_entry["error"] = str(e)
            raise

        finally:
            self.migration_log.append(migration_entry)

        return adk_agent

    def migrate_team(self, langchain_team, preserve_memory: bool = True) -> ADKHierarchicalAgentTeam:
        """
        Migrate a LangChain HierarchicalAgentTeam to ADK.

        Args:
            langchain_team: LangChain HierarchicalAgentTeam instance
            preserve_memory: Whether to migrate memory data

        Returns:
            ADKHierarchicalAgentTeam instance
        """
        migration_entry = {
            "component": "hierarchical_team",
            "source": "langchain",
            "target": "adk",
            "timestamp": datetime.now().isoformat(),
            "status": "started"
        }

        try:
            # Extract team information
            team_name = getattr(langchain_team, 'name', 'migrated_team')

            # Create ADK hierarchical team
            adk_team = ADKHierarchicalAgentTeam(name=f"adk_{team_name}")

            # Migrate team components
            migration_result = adk_team.migrate_from_langchain_team(langchain_team)
            migration_entry["team_migration"] = migration_result

            migration_entry["status"] = "completed"
            migration_entry["target_team"] = {
                "name": adk_team.name,
                "framework": "google-adk",
                "teams": len(adk_team.teams),
                "workers": len(adk_team.workers)
            }

        except Exception as e:
            migration_entry["status"] = "failed"
            migration_entry["error"] = str(e)
            raise

        finally:
            self.migration_log.append(migration_entry)

        return adk_team

    def _convert_agent_config(self, lc_config) -> Dict[str, Any]:
        """Convert LangChain agent configuration to ADK format."""
        # Convert Pydantic model to dict if needed
        if hasattr(lc_config, 'model_dump'):
            config_dict = lc_config.model_dump()
        elif hasattr(lc_config, 'dict'):
            config_dict = lc_config.dict()
        else:
            config_dict = dict(lc_config)

        # Use config loader to convert
        return self.config_loader._convert_langchain_to_adk(config_dict)

    def migrate_configuration_file(self, config_file: str, output_file: str = None) -> str:
        """
        Migrate a LangChain configuration file to ADK format.

        Args:
            config_file: Path to LangChain configuration file
            output_file: Path for ADK configuration file (optional)

        Returns:
            Path to the ADK configuration file
        """
        migration_entry = {
            "component": "configuration_file",
            "source": "langchain",
            "target": "adk",
            "timestamp": datetime.now().isoformat(),
            "status": "started",
            "source_file": config_file
        }

        try:
            # Load and convert configuration
            adk_config = self.config_loader.load_config(config_file)

            # Generate output file name if not provided
            if not output_file:
                base_name = config_file.replace('.yml', '').replace('.yaml', '')
                output_file = f"{base_name}_adk.yml"

            # Export ADK configuration
            self.config_loader.export_adk_config(output_file)

            migration_entry["status"] = "completed"
            migration_entry["target_file"] = output_file

        except Exception as e:
            migration_entry["status"] = "failed"
            migration_entry["error"] = str(e)
            raise

        finally:
            self.migration_log.append(migration_entry)

        return output_file

    def migrate_tools(self, langchain_tools: List) -> Dict[str, Any]:
        """
        Migrate LangChain tools to ADK format.

        Args:
            langchain_tools: List of LangChain tools

        Returns:
            Dictionary with migration results
        """
        migration_entry = {
            "component": "tools",
            "source": "langchain",
            "target": "adk",
            "timestamp": datetime.now().isoformat(),
            "status": "started"
        }

        from .tool_registry_adk import ADKToolRegistry
        registry = ADKToolRegistry()

        migrated_tools = []
        failed_tools = []

        try:
            for tool in langchain_tools:
                try:
                    adk_tool = registry.create_tool_from_langchain(tool)
                    if adk_tool:
                        migrated_tools.append(tool.name if hasattr(tool, 'name') else str(tool))
                    else:
                        failed_tools.append(str(tool))
                except Exception as e:
                    failed_tools.append(f"{str(tool)}: {str(e)}")

            migration_entry["status"] = "completed"
            migration_entry["migrated_tools"] = migrated_tools
            migration_entry["failed_tools"] = failed_tools

        except Exception as e:
            migration_entry["status"] = "failed"
            migration_entry["error"] = str(e)

        finally:
            self.migration_log.append(migration_entry)

        return {
            "migrated_tools": migrated_tools,
            "failed_tools": failed_tools,
            "registry_stats": registry.get_migration_stats()
        }

    def validate_migration(self,
                          langchain_component,
                          adk_component,
                          component_type: str) -> Dict[str, Any]:
        """
        Validate that migration was successful.

        Args:
            langchain_component: Original LangChain component
            adk_component: Migrated ADK component
            component_type: Type of component ("agent", "team", "config")

        Returns:
            Validation results
        """
        validation_result = {
            "component_type": component_type,
            "validation_timestamp": datetime.now().isoformat(),
            "checks": {},
            "overall_success": False
        }

        try:
            if component_type == "agent":
                validation_result["checks"] = self._validate_agent_migration(
                    langchain_component, adk_component
                )
            elif component_type == "team":
                validation_result["checks"] = self._validate_team_migration(
                    langchain_component, adk_component
                )
            elif component_type == "config":
                validation_result["checks"] = self._validate_config_migration(
                    langchain_component, adk_component
                )

            # Determine overall success
            failed_checks = [k for k, v in validation_result["checks"].items() if not v.get("passed", False)]
            validation_result["overall_success"] = len(failed_checks) == 0
            validation_result["failed_checks"] = failed_checks

        except Exception as e:
            validation_result["error"] = str(e)
            validation_result["overall_success"] = False

        return validation_result

    def _validate_agent_migration(self, lc_agent, adk_agent) -> Dict[str, Any]:
        """Validate agent migration."""
        checks = {}

        # Check basic functionality
        try:
            test_input = "Test migration validation"
            lc_result = lc_agent.run(test_input)
            adk_result = adk_agent.run(test_input)

            checks["functionality"] = {
                "passed": "response" in lc_result and "response" in adk_result,
                "lc_response_length": len(lc_result.get("response", "")),
                "adk_response_length": len(adk_result.get("response", ""))
            }
        except Exception as e:
            checks["functionality"] = {
                "passed": False,
                "error": str(e)
            }

        # Check tools
        try:
            lc_tools = lc_agent.get_available_tools()
            adk_tools = adk_agent.get_available_tools()

            common_tools = set(lc_tools.keys()).intersection(set(adk_tools.keys()))
            checks["tools"] = {
                "passed": len(common_tools) > 0,
                "lc_tool_count": len(lc_tools),
                "adk_tool_count": len(adk_tools),
                "common_tools": len(common_tools)
            }
        except Exception as e:
            checks["tools"] = {
                "passed": False,
                "error": str(e)
            }

        # Check memory
        try:
            lc_memory_stats = lc_agent.get_memory_stats()
            adk_memory_stats = adk_agent.get_memory_stats()

            checks["memory"] = {
                "passed": lc_memory_stats.get("memory_enabled") == adk_memory_stats.get("memory_enabled"),
                "lc_memory_enabled": lc_memory_stats.get("memory_enabled"),
                "adk_memory_enabled": adk_memory_stats.get("memory_enabled")
            }
        except Exception as e:
            checks["memory"] = {
                "passed": False,
                "error": str(e)
            }

        return checks

    def _validate_team_migration(self, lc_team, adk_team) -> Dict[str, Any]:
        """Validate team migration."""
        checks = {}

        # Check team structure
        try:
            lc_info = lc_team.get_hierarchy_info()
            adk_info = adk_team.get_hierarchy_info()

            checks["structure"] = {
                "passed": True,  # Basic structure exists
                "lc_teams": lc_info.get("total_teams", 0),
                "adk_teams": adk_info.get("total_teams", 0),
                "lc_workers": lc_info.get("total_workers", 0),
                "adk_workers": adk_info.get("total_workers", 0)
            }
        except Exception as e:
            checks["structure"] = {
                "passed": False,
                "error": str(e)
            }

        # Check coordinator
        try:
            checks["coordinator"] = {
                "passed": adk_team.coordinator is not None,
                "adk_coordinator_active": adk_team.coordinator is not None
            }
        except Exception as e:
            checks["coordinator"] = {
                "passed": False,
                "error": str(e)
            }

        return checks

    def _validate_config_migration(self, lc_config, adk_config) -> Dict[str, Any]:
        """Validate configuration migration."""
        checks = {}

        # Check model mapping
        try:
            if hasattr(lc_config, 'llm') and hasattr(adk_config, 'llm'):
                checks["model_mapping"] = {
                    "passed": adk_config.llm.provider == "google",
                    "source_provider": lc_config.llm.provider,
                    "target_provider": adk_config.llm.provider,
                    "source_model": lc_config.llm.model,
                    "target_model": adk_config.llm.model
                }
            else:
                checks["model_mapping"] = {"passed": False, "error": "LLM config not found"}
        except Exception as e:
            checks["model_mapping"] = {
                "passed": False,
                "error": str(e)
            }

        # Check framework specification
        try:
            checks["framework"] = {
                "passed": adk_config.agent.framework == "google-adk",
                "framework": adk_config.agent.framework
            }
        except Exception as e:
            checks["framework"] = {
                "passed": False,
                "error": str(e)
            }

        return checks

    def generate_migration_report(self) -> Dict[str, Any]:
        """Generate a comprehensive migration report."""
        total_migrations = len(self.migration_log)
        successful_migrations = len([m for m in self.migration_log if m["status"] == "completed"])
        failed_migrations = len([m for m in self.migration_log if m["status"] == "failed"])

        component_summary = {}
        for entry in self.migration_log:
            component = entry["component"]
            if component not in component_summary:
                component_summary[component] = {"total": 0, "successful": 0, "failed": 0}

            component_summary[component]["total"] += 1
            if entry["status"] == "completed":
                component_summary[component]["successful"] += 1
            else:
                component_summary[component]["failed"] += 1

        return {
            "migration_summary": {
                "total_migrations": total_migrations,
                "successful_migrations": successful_migrations,
                "failed_migrations": failed_migrations,
                "success_rate": successful_migrations / max(total_migrations, 1)
            },
            "component_summary": component_summary,
            "migration_log": self.migration_log,
            "report_timestamp": datetime.now().isoformat(),
            "framework_transition": {
                "source": "langchain/langgraph",
                "target": "google-adk"
            }
        }

    def export_migration_report(self, output_file: str = None) -> str:
        """Export migration report to file."""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"adk_migration_report_{timestamp}.json"

        report = self.generate_migration_report()

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        return output_file

    def clear_migration_log(self):
        """Clear the migration log."""
        self.migration_log = []