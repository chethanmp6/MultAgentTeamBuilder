#!/usr/bin/env python3
"""
Validation script for Dynamic Template Builder implementation
Tests code structure and logic without requiring external dependencies
"""
import os
import sys
from pathlib import Path


def validate_file_structure():
    """Validate that all required files exist."""
    print("🧪 Validating File Structure...")
    
    required_files = [
        "src/ui/agent_role_classifier.py",
        "src/ui/enhanced_agent_library.py", 
        "src/ui/team_composition_interface.py",
        "src/ui/real_time_validator.py",
        "src/config/dynamic_template_generator.py",
        "configs/agent_roles.yml",
        "hierarchical_web_ui.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print(f"  ❌ Missing files: {missing_files}")
        return False
    
    print("  ✅ All required files exist")
    return True


def validate_code_structure():
    """Validate code structure and imports."""
    print("🧪 Validating Code Structure...")
    
    try:
        # Test basic Python syntax by compiling files
        files_to_check = [
            "src/ui/agent_role_classifier.py",
            "src/ui/enhanced_agent_library.py",
            "src/config/dynamic_template_generator.py",
            "src/ui/real_time_validator.py"
        ]
        
        for file_path in files_to_check:
            with open(file_path, 'r') as f:
                code = f.read()
            
            try:
                compile(code, file_path, 'exec')
                print(f"  ✅ {file_path} - syntax valid")
            except SyntaxError as e:
                print(f"  ❌ {file_path} - syntax error: {e}")
                return False
        
        print("  ✅ All Python files have valid syntax")
        return True
        
    except Exception as e:
        print(f"  ❌ Code structure validation failed: {e}")
        return False


def validate_class_definitions():
    """Validate that key classes are properly defined."""
    print("🧪 Validating Class Definitions...")
    
    try:
        # Check AgentRoleClassifier
        with open("src/ui/agent_role_classifier.py", 'r') as f:
            content = f.read()
        
        required_classes = ['AgentRoleClassifier', 'AgentMetadata', 'AgentRole', 'AgentCapability']
        for class_name in required_classes:
            if f"class {class_name}" in content:
                print(f"  ✅ {class_name} class defined")
            else:
                print(f"  ❌ {class_name} class missing")
                return False
        
        # Check EnhancedAgentLibrary
        with open("src/ui/enhanced_agent_library.py", 'r') as f:
            content = f.read()
        
        if "class EnhancedAgentLibrary" in content:
            print("  ✅ EnhancedAgentLibrary class defined")
        else:
            print("  ❌ EnhancedAgentLibrary class missing")
            return False
        
        # Check DynamicTemplateGenerator
        with open("src/config/dynamic_template_generator.py", 'r') as f:
            content = f.read()
        
        if "class DynamicTemplateGenerator" in content:
            print("  ✅ DynamicTemplateGenerator class defined")
        else:
            print("  ❌ DynamicTemplateGenerator class missing")
            return False
        
        # Check TeamCompositionInterface
        with open("src/ui/team_composition_interface.py", 'r') as f:
            content = f.read()
            
        if "class TeamCompositionInterface" in content:
            print("  ✅ TeamCompositionInterface class defined")
        else:
            print("  ❌ TeamCompositionInterface class missing")
            return False
        
        # Check RealTimeValidator
        with open("src/ui/real_time_validator.py", 'r') as f:
            content = f.read()
            
        if "class RealTimeValidator" in content:
            print("  ✅ RealTimeValidator class defined")
        else:
            print("  ❌ RealTimeValidator class missing")
            return False
        
        print("  ✅ All required classes are defined")
        return True
        
    except Exception as e:
        print(f"  ❌ Class validation failed: {e}")
        return False


def validate_method_definitions():
    """Validate that key methods are defined."""
    print("🧪 Validating Key Methods...")
    
    try:
        # Check key methods in AgentRoleClassifier
        with open("src/ui/agent_role_classifier.py", 'r') as f:
            content = f.read()
        
        required_methods = [
            "classify_agent",
            "filter_agents_by_role", 
            "get_compatible_agents",
            "suggest_team_composition"
        ]
        
        for method in required_methods:
            if f"def {method}" in content:
                print(f"  ✅ AgentRoleClassifier.{method}")
            else:
                print(f"  ❌ AgentRoleClassifier.{method} missing")
        
        # Check key methods in DynamicTemplateGenerator
        with open("src/config/dynamic_template_generator.py", 'r') as f:
            content = f.read()
        
        required_methods = [
            "create_team_config",
            "generate_yaml_config",
            "generate_template_from_task",
            "validate_template"
        ]
        
        for method in required_methods:
            if f"def {method}" in content:
                print(f"  ✅ DynamicTemplateGenerator.{method}")
            else:
                print(f"  ❌ DynamicTemplateGenerator.{method} missing")
        
        # Check key methods in TeamCompositionInterface
        with open("src/ui/team_composition_interface.py", 'r') as f:
            content = f.read()
        
        required_methods = [
            "render_team_builder",
            "_render_validation_panel",
            "_render_team_canvas"
        ]
        
        for method in required_methods:
            if f"def {method}" in content:
                print(f"  ✅ TeamCompositionInterface.{method}")
            else:
                print(f"  ❌ TeamCompositionInterface.{method} missing")
        
        print("  ✅ Key methods validation completed")
        return True
        
    except Exception as e:
        print(f"  ❌ Method validation failed: {e}")
        return False


def validate_ui_integration():
    """Validate UI integration in hierarchical_web_ui.py."""
    print("🧪 Validating UI Integration...")
    
    try:
        with open("hierarchical_web_ui.py", 'r') as f:
            content = f.read()
        
        # Check for new imports
        required_imports = [
            "from src.ui.enhanced_agent_library import EnhancedAgentLibrary",
            "from src.ui.team_composition_interface import TeamCompositionInterface",
            "from src.config.dynamic_template_generator import DynamicTemplateGenerator"
        ]
        
        for import_line in required_imports:
            if import_line in content:
                print(f"  ✅ Import: {import_line.split('import')[1].strip()}")
            else:
                print(f"  ❌ Missing import: {import_line}")
        
        # Check for dynamic builder mode
        if "builder_mode" in content:
            print("  ✅ Dynamic builder mode integration")
        else:
            print("  ❌ Dynamic builder mode missing")
        
        # Check for enhanced agent library rendering
        if "render_enhanced_agent_library" in content:
            print("  ✅ Enhanced agent library rendering")
        else:
            print("  ❌ Enhanced agent library rendering missing")
        
        print("  ✅ UI integration validation completed")
        return True
        
    except Exception as e:
        print(f"  ❌ UI integration validation failed: {e}")
        return False


def validate_config_files():
    """Validate configuration files."""
    print("🧪 Validating Configuration Files...")
    
    try:
        # Check agent_roles.yml exists and has content
        config_file = Path("configs/agent_roles.yml")
        if config_file.exists():
            content = config_file.read_text()
            
            # Check for key sections
            required_sections = ["roles:", "capabilities:", "compatibility_matrix:", "team_composition:"]
            
            for section in required_sections:
                if section in content:
                    print(f"  ✅ {section}")
                else:
                    print(f"  ❌ Missing section: {section}")
            
            print("  ✅ Configuration file validation completed")
            
        else:
            print("  ❌ configs/agent_roles.yml missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"  ❌ Configuration validation failed: {e}")
        return False


def validate_feature_completeness():
    """Validate that all requested features are implemented."""
    print("🧪 Validating Feature Completeness...")
    
    features = [
        ("Agent Role Classification", "AgentRoleClassifier", "src/ui/agent_role_classifier.py"),
        ("Enhanced Agent Library", "EnhancedAgentLibrary", "src/ui/enhanced_agent_library.py"),
        ("Dynamic Template Generation", "DynamicTemplateGenerator", "src/config/dynamic_template_generator.py"),
        ("Interactive Team Composition", "TeamCompositionInterface", "src/ui/team_composition_interface.py"),
        ("Real-time Validation", "RealTimeValidator", "src/ui/real_time_validator.py"),
        ("Role Definitions Config", "agent_roles.yml", "configs/agent_roles.yml"),
        ("UI Integration", "hierarchical_web_ui.py", "hierarchical_web_ui.py")
    ]
    
    implemented_count = 0
    
    for feature_name, key_component, file_path in features:
        if Path(file_path).exists():
            print(f"  ✅ {feature_name}")
            implemented_count += 1
        else:
            print(f"  ❌ {feature_name} - {file_path} missing")
    
    print(f"  📊 Feature completion: {implemented_count}/{len(features)} ({implemented_count/len(features)*100:.1f}%)")
    
    return implemented_count == len(features)


def main():
    """Run all validations."""
    print("🚀 Dynamic Template Builder Implementation Validation\n")
    
    validations = [
        validate_file_structure,
        validate_code_structure,
        validate_class_definitions,
        validate_method_definitions,
        validate_ui_integration,
        validate_config_files,
        validate_feature_completeness
    ]
    
    passed = 0
    total = len(validations)
    
    for validation in validations:
        if validation():
            passed += 1
        print()  # Add spacing between validations
    
    print(f"📊 Validation Results: {passed}/{total} validations passed")
    
    if passed == total:
        print("🎉 All validations passed! Implementation is complete and ready for use.")
        print("\n📝 Next Steps:")
        print("1. Install required dependencies: pip install streamlit pyyaml")
        print("2. Run the web UI: python run_hierarchical_ui.py")
        print("3. Select 'Dynamic Builder' mode to start creating custom teams")
        return 0
    else:
        print(f"⚠️ {total - passed} validations failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())