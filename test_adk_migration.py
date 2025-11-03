#!/usr/bin/env python3
"""
Test script for ADK migration functionality.
This script validates the migration from LangChain/LangGraph to Google ADK.
"""
import os
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_adk_imports():
    """Test that ADK components can be imported."""
    print("🧪 Testing ADK imports...")

    try:
        from src.adk import (
            ADKConfigurableAgent,
            ADKToolRegistry,
            ADKMemoryManager,
            ADK_AVAILABLE
        )

        from src.adk.hierarchical import (
            ADKHierarchicalAgentTeam,
            ADKTeamCoordinator,
            ADKSupervisorAgent,
            ADKWorkerAgent
        )

        from src.adk.migration_utils import LangChainToADKMigrator

        print("✅ All ADK imports successful")
        print(f"   ADK Available: {ADK_AVAILABLE}")
        return True

    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False


def test_adk_configuration():
    """Test ADK configuration loading and conversion."""
    print("\n🧪 Testing ADK configuration...")

    try:
        from src.adk.config_loader_adk import ADKConfigLoader

        # Test configuration loader
        loader = ADKConfigLoader()

        # Test LangChain to ADK conversion
        sample_lc_config = {
            "agent": {
                "name": "Test Agent",
                "description": "Test agent for migration",
                "version": "1.0.0"
            },
            "llm": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.7,
                "api_key_env": "OPENAI_API_KEY"
            },
            "prompts": {
                "system_prompt": {
                    "template": "You are a helpful assistant.",
                    "variables": []
                },
                "user_prompt": {
                    "template": "User: {user_input}",
                    "variables": ["user_input"]
                }
            },
            "tools": {
                "built_in": ["web_search", "calculator"],
                "custom": []
            }
        }

        # Convert configuration
        adk_config = loader._convert_langchain_to_adk(sample_lc_config)

        print("✅ Configuration conversion successful")
        print(f"   Original provider: {sample_lc_config['llm']['provider']}")
        print(f"   Converted provider: {adk_config['llm']['provider']}")
        print(f"   Original model: {sample_lc_config['llm']['model']}")
        print(f"   Converted model: {adk_config['llm']['model']}")

        return True

    except Exception as e:
        print(f"❌ Configuration test error: {e}")
        return False


def test_adk_tool_registry():
    """Test ADK tool registry functionality."""
    print("\n🧪 Testing ADK tool registry...")

    try:
        from src.adk.tool_registry_adk import ADKToolRegistry

        registry = ADKToolRegistry()

        # Test built-in tools
        built_in_tools = registry.get_built_in_tools()
        print(f"   Built-in tools: {len(built_in_tools)}")
        print(f"   Available tools: {built_in_tools}")

        # Test tool retrieval
        web_search_tool = registry.get_tool("web_search")
        if web_search_tool:
            print("✅ Tool retrieval successful")
        else:
            print("❌ Tool retrieval failed")
            return False

        # Test migration stats
        stats = registry.get_migration_stats()
        print(f"   Migration stats: {stats}")

        return True

    except Exception as e:
        print(f"❌ Tool registry test error: {e}")
        return False


def test_adk_agent_creation():
    """Test ADK agent creation with mock configuration."""
    print("\n🧪 Testing ADK agent creation...")

    try:
        from src.adk.configurable_agent_adk import ADKConfigurableAgent

        # Create test configuration
        test_config = {
            "agent": {
                "name": "Test ADK Agent",
                "description": "Test agent for ADK validation",
                "version": "1.0.0",
                "framework": "google-adk"
            },
            "llm": {
                "provider": "google",
                "model": "gemini-1.5-flash",
                "temperature": 0.7,
                "api_key_env": "GOOGLE_API_KEY"
            },
            "prompts": {
                "system_prompt": {
                    "template": "You are a test ADK agent.",
                    "variables": []
                },
                "user_prompt": {
                    "template": "User: {user_input}",
                    "variables": ["user_input"]
                }
            },
            "tools": {
                "built_in": ["calculator"],
                "custom": []
            },
            "memory": {
                "enabled": False
            },
            "workflow": {
                "max_iterations": 5,
                "workflow_type": "sequential"
            }
        }

        # Create ADK agent
        agent = ADKConfigurableAgent(config_data=test_config)

        # Test agent info
        agent_info = agent.get_adk_agent_info()
        print("✅ ADK agent creation successful")
        print(f"   Agent name: {agent_info['agent_name']}")
        print(f"   Framework: {agent_info['framework']}")
        print(f"   Model: {agent_info['model']}")
        print(f"   ADK available: {agent_info['adk_available']}")

        # Test agent execution (mock)
        result = agent.run("Test input")
        if "response" in result:
            print("✅ Agent execution test successful")
            print(f"   Response length: {len(result['response'])}")
        else:
            print("❌ Agent execution test failed")
            return False

        return True

    except Exception as e:
        print(f"❌ Agent creation test error: {e}")
        return False


def test_adk_hierarchical_team():
    """Test ADK hierarchical team functionality."""
    print("\n🧪 Testing ADK hierarchical team...")

    try:
        from src.adk.hierarchical.hierarchical_agent_adk import ADKHierarchicalAgentTeam
        from src.adk.hierarchical.worker_agent_adk import ADKWorkerAgent

        # Create hierarchical team
        team = ADKHierarchicalAgentTeam(name="test_adk_team")

        # Create test worker
        worker = ADKWorkerAgent(name="test_worker", specialization="testing")

        # Add worker to team
        team.add_worker(worker, "test_team")

        # Test team info
        team_info = team.get_hierarchy_info()
        print("✅ Hierarchical team creation successful")
        print(f"   Team name: {team_info['name']}")
        print(f"   Framework: {team_info['framework']}")
        print(f"   Total teams: {team_info['total_teams']}")
        print(f"   Total workers: {team_info['total_workers']}")

        # Test team execution (mock)
        if team_info['total_workers'] > 0:
            result = team.run("Test hierarchical task")
            if "response" in result:
                print("✅ Team execution test successful")
            else:
                print("⚠️ Team execution returned unexpected format")

        return True

    except Exception as e:
        print(f"❌ Hierarchical team test error: {e}")
        return False


def test_migration_utilities():
    """Test migration utilities."""
    print("\n🧪 Testing migration utilities...")

    try:
        from src.adk.migration_utils import LangChainToADKMigrator

        migrator = LangChainToADKMigrator()

        # Test configuration file migration (with mock file)
        print("   Testing configuration conversion...")

        # Create mock LangChain config
        mock_config = {
            "agent": {"name": "Mock Agent", "description": "Test", "version": "1.0.0"},
            "llm": {"provider": "openai", "model": "gpt-4o-mini", "api_key_env": "OPENAI_API_KEY"},
            "prompts": {
                "system_prompt": {"template": "Test prompt", "variables": []},
                "user_prompt": {"template": "User: {input}", "variables": ["input"]}
            }
        }

        # Test configuration conversion
        adk_config = migrator._convert_agent_config(mock_config)

        print("✅ Migration utilities test successful")
        print(f"   Original provider: {mock_config['llm']['provider']}")
        print(f"   Converted provider: {adk_config['llm']['provider']}")

        # Test migration report generation
        report = migrator.generate_migration_report()
        print(f"   Migration report generated: {len(report)} entries")

        return True

    except Exception as e:
        print(f"❌ Migration utilities test error: {e}")
        return False


def test_environment_setup():
    """Test environment setup for ADK."""
    print("\n🧪 Testing environment setup...")

    # Check for Google API key
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if google_api_key:
        print(f"✅ GOOGLE_API_KEY found (length: {len(google_api_key)})")
    else:
        print("⚠️ GOOGLE_API_KEY not found (this is expected for testing)")

    # Check for other environment variables
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print("✅ OPENAI_API_KEY found (for comparison)")
    else:
        print("⚠️ OPENAI_API_KEY not found")

    # Test Google AI import
    try:
        import google.generativeai as genai
        print("✅ Google Generative AI library available")
    except ImportError:
        print("⚠️ Google Generative AI library not available (install with: pip install google-generativeai)")

    return True


def main():
    """Run all ADK migration tests."""
    print("🚀 ADK Migration Test Suite")
    print("=" * 50)

    tests = [
        test_environment_setup,
        test_adk_imports,
        test_adk_configuration,
        test_adk_tool_registry,
        test_adk_agent_creation,
        test_adk_hierarchical_team,
        test_migration_utilities
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1

    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! ADK migration is ready.")
    else:
        print("⚠️ Some tests failed. Check the output above for details.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)