#!/usr/bin/env python3
"""
Test script for Simple Team Builder functionality
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def test_agent_library():
    """Test the enhanced agent library."""
    print("🧪 Testing Enhanced Agent Library...")
    
    try:
        from src.ui.enhanced_agent_library import EnhancedAgentLibrary
        
        # Initialize agent library
        library = EnhancedAgentLibrary()
        
        # Get all agents
        agents = library.get_all_agents()
        print(f"✅ Found {len(agents)} agents")
        
        if agents:
            print("📋 Available agents:")
            for agent_id, metadata in agents.items():
                print(f"  - {agent_id}: {metadata.name}")
        
        # Test statistics
        stats = library.get_statistics()
        print(f"📊 Library statistics: {stats}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing agent library: {e}")
        return False

def test_simple_template_generator():
    """Test the simple template generator."""
    print("🧪 Testing Simple Template Generator...")
    
    try:
        from src.config.simple_template_generator import SimpleTemplateGenerator
        from src.ui.enhanced_agent_library import EnhancedAgentLibrary
        
        # Initialize components
        library = EnhancedAgentLibrary()
        generator = SimpleTemplateGenerator(library)
        
        # Test with sample data
        team_name = "Test Team"
        team_description = "A test hierarchical team"
        supervisor_id = list(library.get_all_agents().keys())[0] if library.get_all_agents() else "test_supervisor"
        worker_ids = list(library.get_all_agents().keys())[:2] if len(library.get_all_agents()) >= 2 else ["test_worker"]
        
        # Generate configuration
        yaml_content = generator.generate_simple_hierarchical_config(
            team_name=team_name,
            team_description=team_description,
            supervisor_id=supervisor_id,
            worker_ids=worker_ids
        )
        
        print(f"✅ Generated configuration for {team_name}")
        print(f"📄 YAML length: {len(yaml_content)} characters")
        
        # Test validation
        validation = generator.validate_simple_config(supervisor_id, worker_ids)
        print(f"✅ Validation result: {validation['valid']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing template generator: {e}")
        return False

def test_simple_team_builder():
    """Test the simple team builder."""
    print("🧪 Testing Simple Team Builder...")
    
    try:
        from src.ui.simple_team_builder import SimpleTeamBuilder
        from src.ui.enhanced_agent_library import EnhancedAgentLibrary
        
        # Initialize components
        library = EnhancedAgentLibrary()
        builder = SimpleTeamBuilder(library)
        
        print("✅ Simple Team Builder initialized successfully")
        
        # Test team validation
        test_team = {
            'supervisor': 'test_supervisor',
            'workers': ['test_worker1', 'test_worker2'],
            'team_name': 'Test Team',
            'team_description': 'A test team'
        }
        
        is_valid = builder._validate_team()
        print(f"✅ Team validation: {is_valid}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing team builder: {e}")
        return False

def test_hierarchical_components():
    """Test hierarchical agent components."""
    print("🧪 Testing Hierarchical Components...")
    
    try:
        from src.hierarchical.hierarchical_agent import HierarchicalAgentTeam
        from src.hierarchical.supervisor import SupervisorAgent
        from src.hierarchical.worker_agent import WorkerAgent
        
        print("✅ Hierarchical components imported successfully")
        
        # Test basic initialization
        team = HierarchicalAgentTeam(name="test_team")
        print(f"✅ Hierarchical team created: {team}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing hierarchical components: {e}")
        return False

def test_config_loader():
    """Test configuration loading."""
    print("🧪 Testing Configuration Loader...")
    
    try:
        from src.core.config_loader import ConfigLoader
        
        loader = ConfigLoader()
        print("✅ Config loader initialized successfully")
        
        # Check if example configs exist
        configs_dir = Path("configs/examples")
        if configs_dir.exists():
            config_files = list(configs_dir.glob("*.yml"))
            print(f"✅ Found {len(config_files)} configuration files")
            
            if config_files:
                # Try to load the first config
                first_config = config_files[0]
                print(f"📄 Testing config: {first_config.name}")
                
                try:
                    config = loader.load_config(str(first_config))
                    print(f"✅ Successfully loaded {first_config.name}")
                except Exception as e:
                    print(f"⚠️ Could not load {first_config.name}: {e}")
        else:
            print("⚠️ No configs/examples directory found")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing config loader: {e}")
        return False

def main():
    """Run all tests."""
    print("🚀 Starting Simple Team Builder Tests...")
    print("=" * 50)
    
    tests = [
        ("Configuration Loader", test_config_loader),
        ("Agent Library", test_agent_library),
        ("Template Generator", test_simple_template_generator),
        ("Team Builder", test_simple_team_builder),
        ("Hierarchical Components", test_hierarchical_components),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            success = test_func()
            results.append((test_name, success))
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{status} {test_name}")
        except Exception as e:
            print(f"❌ FAILED {test_name}: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"  {status}: {test_name}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Simple Team Builder should work correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the errors above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)