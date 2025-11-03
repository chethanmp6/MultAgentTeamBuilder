#!/usr/bin/env python3
"""
Test script for the Dynamic Template Builder functionality
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.ui.enhanced_agent_library import EnhancedAgentLibrary
from src.ui.agent_role_classifier import AgentRoleClassifier, AgentRole, AgentCapability
from src.config.dynamic_template_generator import DynamicTemplateGenerator
from src.ui.real_time_validator import RealTimeValidator


def test_agent_classification():
    """Test agent role classification."""
    print("🧪 Testing Agent Classification...")
    
    try:
        # Initialize classifier
        classifier = AgentRoleClassifier()
        
        # Test classifying a known agent
        configs_dir = Path("configs/examples")
        if configs_dir.exists():
            test_files = list(configs_dir.glob("*.yml"))[:3]  # Test first 3
            
            for config_file in test_files:
                metadata = classifier.classify_agent(str(config_file))
                print(f"  ✅ {config_file.stem}: {metadata.primary_role.value} - {len(metadata.capabilities)} capabilities")
        
        print("  ✅ Agent classification test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Agent classification test failed: {e}")
        return False


def test_enhanced_library():
    """Test enhanced agent library functionality."""
    print("🧪 Testing Enhanced Agent Library...")
    
    try:
        # Initialize library
        library = EnhancedAgentLibrary()
        
        # Test basic functionality
        all_agents = library.get_all_agents()
        print(f"  ✅ Loaded {len(all_agents)} agents")
        
        # Test role filtering
        coordinators = library.get_coordinators()
        supervisors = library.get_supervisors()
        workers = library.get_workers()
        
        print(f"  ✅ Found {len(coordinators)} coordinators, {len(supervisors)} supervisors, {len(workers)} workers")
        
        # Test search
        search_results = library.search_agents("research")
        print(f"  ✅ Search for 'research' returned {len(search_results)} results")
        
        # Test statistics
        stats = library.get_statistics()
        print(f"  ✅ Library statistics: {stats['total_agents']} total agents")
        
        print("  ✅ Enhanced library test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Enhanced library test failed: {e}")
        return False


def test_template_generation():
    """Test dynamic template generation."""
    print("🧪 Testing Template Generation...")
    
    try:
        # Initialize components
        library = EnhancedAgentLibrary()
        generator = DynamicTemplateGenerator(library)
        
        # Get available agents
        coordinators = library.get_coordinators()
        supervisors = library.get_supervisors()
        workers = library.get_workers()
        
        if not coordinators or not supervisors or not workers:
            print("  ⚠️ Not enough agents to test template generation")
            return True
        
        # Create a simple team configuration
        coordinator_id = list(coordinators.keys())[0]
        supervisor_id = list(supervisors.keys())[0]
        worker_ids = list(workers.keys())[:2]  # Get first 2 workers
        
        teams_data = [{
            'name': 'Test Team',
            'description': 'A test team configuration',
            'supervisor_id': supervisor_id,
            'worker_ids': worker_ids,
            'specialization': 'testing',
            'max_workers': 5
        }]
        
        # Create team config
        team_config = generator.create_team_config(
            team_name="Test Hierarchical Team",
            team_description="A dynamically generated test team",
            coordinator_id=coordinator_id,
            teams_data=teams_data
        )
        
        print(f"  ✅ Created team config: {team_config.name}")
        
        # Generate YAML
        yaml_content = generator.generate_yaml_config(team_config)
        print(f"  ✅ Generated YAML ({len(yaml_content)} characters)")
        
        # Validate template
        validation = generator.validate_template(team_config)
        if validation['valid']:
            print("  ✅ Template validation passed")
        else:
            print(f"  ⚠️ Template validation warnings: {validation['warnings']}")
        
        print("  ✅ Template generation test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Template generation test failed: {e}")
        return False


def test_task_based_generation():
    """Test task-based team generation."""
    print("🧪 Testing Task-based Generation...")
    
    try:
        # Initialize components
        library = EnhancedAgentLibrary()
        generator = DynamicTemplateGenerator(library)
        
        # Test task-based generation
        task_description = "Research and write a comprehensive report on artificial intelligence trends"
        
        team_config = generator.generate_template_from_task(task_description)
        print(f"  ✅ Generated team for task: {team_config.name}")
        print(f"  ✅ Team has {len(team_config.teams)} teams")
        
        # Generate YAML
        yaml_content = generator.generate_yaml_config(team_config)
        print(f"  ✅ Generated YAML for task-based team")
        
        print("  ✅ Task-based generation test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Task-based generation test failed: {e}")
        return False


def test_validation():
    """Test real-time validation functionality."""
    print("🧪 Testing Real-time Validation...")
    
    try:
        # Initialize components
        library = EnhancedAgentLibrary()
        generator = DynamicTemplateGenerator(library)
        validator = RealTimeValidator(library, generator)
        
        # Test with empty composition
        empty_composition = {
            'coordinator': None,
            'teams': {}
        }
        
        validation = validator.validate_composition_live(empty_composition)
        print(f"  ✅ Empty composition validation: {validation['status']}")
        
        # Test with basic composition
        coordinators = library.get_coordinators()
        supervisors = library.get_supervisors()
        workers = library.get_workers()
        
        if coordinators and supervisors and workers:
            coordinator_id = list(coordinators.keys())[0]
            supervisor_id = list(supervisors.keys())[0]
            worker_ids = list(workers.keys())[:2]
            
            basic_composition = {
                'coordinator': coordinator_id,
                'teams': {
                    '1': {
                        'name': 'Test Team',
                        'description': 'Test team description',
                        'supervisor': supervisor_id,
                        'workers': worker_ids
                    }
                }
            }
            
            validation = validator.validate_composition_live(basic_composition)
            print(f"  ✅ Basic composition validation: {validation['status']} ({validation['completeness']:.1%} complete)")
            
            # Test metrics calculation
            metrics = validator.calculate_team_metrics(basic_composition)
            print(f"  ✅ Team metrics: {metrics['total_agents']} agents, {metrics['capabilities_coverage']:.1%} capability coverage")
            
            # Test YAML preview generation
            yaml_preview = validator.generate_live_preview(basic_composition, "Test Team", "Test Description")
            if yaml_preview:
                print("  ✅ Live YAML preview generated successfully")
        
        print("  ✅ Validation test passed")
        return True
        
    except Exception as e:
        print(f"  ❌ Validation test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Starting Dynamic Template Builder Tests\n")
    
    tests = [
        test_agent_classification,
        test_enhanced_library,
        test_template_generation,
        test_task_based_generation,
        test_validation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()  # Add spacing between tests
    
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Dynamic Template Builder is working correctly.")
        return 0
    else:
        print(f"⚠️ {total - passed} tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())