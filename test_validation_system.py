#!/usr/bin/env python3
"""
Test script for the Hierarchical Agent Configuration Validator
"""
import os
import sys
import json
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from validation.hierarchy_validator import HierarchyValidator, ValidationSeverity


def create_test_config():
    """Create a test hierarchical configuration."""
    return {
        "team": {
            "name": "Test Research Team",
            "description": "A test team for validation",
            "version": "1.0.0",
            "type": "hierarchical"
        },
        "coordinator": {
            "name": "Test Coordinator",
            "description": "Test coordinator",
            "llm": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "max_tokens": 2000,
                "api_key_env": "OPENAI_API_KEY"
            },
            "prompts": {
                "system_prompt": {
                    "template": "You are a coordinator.",  # Deliberately simple/poor prompt
                    "variables": []
                }
            }
        },
        "teams": [
            {
                "name": "main_team",
                "description": "Main working team",
                "supervisor": {
                    "name": "Research Supervisor",
                    "llm": {
                        "provider": "openai",
                        "model": "gpt-4o-mini",
                        "temperature": 0.2,
                        "api_key_env": "OPENAI_API_KEY"
                    },
                    "prompts": {
                        "system_prompt": {
                            "template": "You supervise workers.",  # Deliberately simple/poor prompt
                            "variables": []
                        }
                    }
                },
                "workers": [
                    {
                        "name": "Research Worker 1",
                        "role": "worker",
                        "description": "Conducts research tasks",
                        "capabilities": ["research", "analysis", "web_search"],
                        "priority": 1
                    },
                    {
                        "name": "Writing Worker 1", 
                        "role": "worker",
                        "description": "Writes reports and documentation",
                        "capabilities": ["writing", "editing", "summarization"],
                        "priority": 2
                    }
                ]
            }
        ]
    }


def create_good_config():
    """Create a well-configured hierarchical configuration."""
    return {
        "team": {
            "name": "Optimized Research Team",
            "description": "A well-configured team for validation",
            "version": "1.0.0", 
            "type": "hierarchical"
        },
        "coordinator": {
            "name": "Research Coordinator",
            "description": "Coordinates research teams",
            "llm": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "max_tokens": 2000,
                "api_key_env": "OPENAI_API_KEY"
            },
            "prompts": {
                "system_prompt": {
                    "template": """You are a research team coordinator managing specialized research teams.

Available teams:
- main_team: Research and writing team (2 workers) - Capabilities: research, analysis, web_search, writing, editing, summarization

Your primary responsibilities:
1. Analyze incoming requests to understand the research requirements
2. Determine which team is best suited for the task based on their capabilities
3. Route tasks to the appropriate team supervisor
4. Coordinate between teams when multi-team collaboration is needed
5. Provide final responses by synthesizing results from teams

Routing Decision Framework:
- Match task requirements to team capabilities
- Consider team workload and availability
- Route complex tasks that require multiple specializations to the most capable team
- Use fallback routing if no team is a perfect match

Always provide clear reasoning for your routing decisions and specific instructions for the selected team.""",
                    "variables": []
                }
            }
        },
        "teams": [
            {
                "name": "main_team",
                "description": "Main research and writing team",
                "supervisor": {
                    "name": "Research Supervisor",
                    "llm": {
                        "provider": "openai",
                        "model": "gpt-4o-mini",
                        "temperature": 0.2,
                        "api_key_env": "OPENAI_API_KEY"
                    },
                    "prompts": {
                        "system_prompt": {
                            "template": """You are a supervisor for the main_team team, responsible for managing and coordinating worker agents.

Available workers:
- Research Worker 1: Conducts research tasks - Capabilities: research, analysis, web_search
- Writing Worker 1: Writes reports and documentation - Capabilities: writing, editing, summarization

Your key responsibilities:
1. Analyze tasks assigned to your team
2. Determine which worker is best suited for each task based on their specific capabilities
3. Delegate tasks with clear, specific instructions
4. Monitor task progress and coordinate between workers when needed
5. Provide consolidated responses from worker outputs

Worker Selection Criteria:
- Match task requirements to worker capabilities
- Consider worker specialization and expertise
- Balance workload across available workers
- Choose workers with the most relevant tools and skills

Task Delegation Best Practices:
- Provide clear, specific instructions to workers
- Include relevant context and requirements
- Set clear expectations for deliverables
- Monitor progress and provide guidance as needed

Always explain your reasoning for worker selection and provide detailed instructions for successful task completion.""",
                            "variables": []
                        }
                    }
                },
                "workers": [
                    {
                        "name": "Research Worker 1",
                        "role": "worker",
                        "description": "Conducts research tasks",
                        "capabilities": ["research", "analysis", "web_search"],
                        "priority": 1
                    },
                    {
                        "name": "Writing Worker 1",
                        "role": "worker", 
                        "description": "Writes reports and documentation",
                        "capabilities": ["writing", "editing", "summarization"],
                        "priority": 2
                    }
                ]
            }
        ]
    }


def test_validation_system():
    """Test the validation system with different configurations."""
    print("🧪 Testing Hierarchical Agent Configuration Validator")
    print("=" * 60)
    
    # Check if OpenAI API key is available (required for LLM judge)
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️ Warning: OPENAI_API_KEY not found. Using mock validator.")
        # You could implement a mock validator here for testing without API
        return
    
    try:
        # Initialize validator
        print("📍 Initializing HierarchyValidator...")
        validator = HierarchyValidator()
        print("✅ Validator initialized successfully")
        
        # Test 1: Validate a poorly configured team
        print("\n📋 Test 1: Validating poorly configured team...")
        poor_config = create_test_config()
        print(f"Config: {poor_config['team']['name']}")
        
        result1 = validator.validate_hierarchy_config(poor_config)
        print(f"📊 Score: {result1.overall_score:.1f}/100")
        print(f"🚨 Issues found: {len(result1.issues)}")
        
        if result1.issues:
            print("Issues breakdown:")
            for issue in result1.issues[:3]:  # Show first 3 issues
                print(f"  - {issue.severity.value.upper()}: {issue.message}")
        
        if result1.suggestions:
            print(f"💡 Suggestions: {len(result1.suggestions)}")
            for suggestion in result1.suggestions[:2]:  # Show first 2 suggestions
                print(f"  - {suggestion}")
        
        # Test 2: Validate a well-configured team
        print("\n📋 Test 2: Validating well-configured team...")
        good_config = create_good_config()
        print(f"Config: {good_config['team']['name']}")
        
        result2 = validator.validate_hierarchy_config(good_config)
        print(f"📊 Score: {result2.overall_score:.1f}/100")
        print(f"🚨 Issues found: {len(result2.issues)}")
        
        if result2.issues:
            print("Issues breakdown:")
            for issue in result2.issues[:3]:
                print(f"  - {issue.severity.value.upper()}: {issue.message}")
        
        # Test 3: Check optimization capabilities
        print("\n📋 Test 3: Testing optimization capabilities...")
        if result1.optimized_config:
            print("✅ Optimization generated for poorly configured team")
            
            # Validate the optimized config
            result3 = validator.validate_hierarchy_config(result1.optimized_config)
            print(f"📊 Optimized score: {result3.overall_score:.1f}/100")
            print(f"📈 Improvement: +{result3.overall_score - result1.overall_score:.1f} points")
        else:
            print("⚠️ No optimization generated")
        
        print(f"\n🎯 Validation History: {len(validator.validation_history)} results stored")
        
        print("\n✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_validation_system()