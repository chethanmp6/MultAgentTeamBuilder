"""
Tests for configuration loader functionality.
"""
import pytest
import yaml
import tempfile
import os
from src.core.config_loader import ConfigLoader, AgentConfiguration


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "agent": {
            "name": "Test Agent",
            "description": "A test agent",
            "version": "1.0.0"
        },
        "llm": {
            "provider": "openai",
            "model": "gpt-3.5-turbo",
            "temperature": 0.7,
            "max_tokens": 1000,
            "api_key_env": "TEST_API_KEY"
        },
        "prompts": {
            "system_prompt": {
                "template": "You are a test assistant. Context: {context}",
                "variables": ["context"]
            },
            "user_prompt": {
                "template": "User query: {query}",
                "variables": ["query"]
            }
        },
        "graph": {
            "nodes": [
                {"name": "start", "type": "input", "config": {}},
                {"name": "agent", "type": "agent", "config": {}},
                {"name": "end", "type": "output", "config": {}}
            ],
            "edges": [
                {"from": "start", "to": "agent"},
                {"from": "agent", "to": "end"}
            ],
            "entry_point": "start"
        }
    }


@pytest.fixture
def config_file(sample_config):
    """Create a temporary config file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
        yaml.dump(sample_config, f)
        return f.name


class TestConfigLoader:
    """Test cases for ConfigLoader."""
    
    def test_load_valid_config(self, config_file, sample_config):
        """Test loading a valid configuration."""
        # Set required environment variable
        os.environ["TEST_API_KEY"] = "test_key"
        
        loader = ConfigLoader()
        config = loader.load_config(config_file)
        
        assert isinstance(config, AgentConfiguration)
        assert config.agent.name == sample_config["agent"]["name"]
        assert config.llm.provider == sample_config["llm"]["provider"]
        assert config.llm.model == sample_config["llm"]["model"]
        
        # Clean up
        os.unlink(config_file)
        del os.environ["TEST_API_KEY"]
    
    def test_load_nonexistent_file(self):
        """Test loading a non-existent configuration file."""
        loader = ConfigLoader()
        
        with pytest.raises(FileNotFoundError):
            loader.load_config("nonexistent.yml")
    
    def test_invalid_yaml(self):
        """Test loading invalid YAML."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            
            loader = ConfigLoader()
            with pytest.raises(ValueError, match="Invalid YAML"):
                loader.load_config(f.name)
            
            os.unlink(f.name)
    
    def test_missing_api_key_env(self, config_file):
        """Test validation when API key environment variable is missing."""
        loader = ConfigLoader()
        
        # Ensure the test API key is not set
        if "TEST_API_KEY" in os.environ:
            del os.environ["TEST_API_KEY"]
        
        with pytest.raises(ValueError, match="Environment variable TEST_API_KEY not found"):
            loader.load_config(config_file)
        
        os.unlink(config_file)
    
    def test_get_prompt_template(self, config_file):
        """Test getting formatted prompt templates."""
        os.environ["TEST_API_KEY"] = "test_key"
        
        loader = ConfigLoader()
        config = loader.load_config(config_file)
        
        # Test system prompt with variable substitution
        formatted = loader.get_prompt_template("system_prompt", context="test context")
        expected = "You are a test assistant. Context: test context"
        assert formatted == expected
        
        # Test user prompt
        formatted = loader.get_prompt_template("user_prompt", query="test query")
        expected = "User query: test query"
        assert formatted == expected
        
        # Clean up
        os.unlink(config_file)
        del os.environ["TEST_API_KEY"]
    
    def test_validate_config(self, sample_config):
        """Test configuration validation."""
        os.environ["TEST_API_KEY"] = "test_key"
        
        loader = ConfigLoader()
        
        # Valid config should validate
        assert loader.validate_config(sample_config) is True
        
        # Invalid config should not validate
        invalid_config = sample_config.copy()
        del invalid_config["agent"]
        assert loader.validate_config(invalid_config) is False
        
        del os.environ["TEST_API_KEY"]
    
    def test_config_with_memory(self, sample_config):
        """Test configuration with memory settings."""
        os.environ["TEST_API_KEY"] = "test_key"
        
        # Add memory configuration
        sample_config["memory"] = {
            "enabled": True,
            "provider": "langmem",
            "types": {
                "semantic": True,
                "episodic": True,
                "procedural": False
            },
            "storage": {
                "backend": "memory"
            },
            "settings": {
                "max_memory_size": 5000,
                "retention_days": 30,
                "background_processing": True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(sample_config, f)
            f.flush()
            
            loader = ConfigLoader()
            config = loader.load_config(f.name)
            
            assert config.memory.enabled is True
            assert config.memory.provider == "langmem"
            assert config.memory.types.semantic is True
            assert config.memory.types.procedural is False
            assert config.memory.settings.max_memory_size == 5000
            
            os.unlink(f.name)
        
        del os.environ["TEST_API_KEY"]
    
    def test_config_with_tools(self, sample_config):
        """Test configuration with tools."""
        os.environ["TEST_API_KEY"] = "test_key"
        
        # Add tools configuration
        sample_config["tools"] = {
            "built_in": ["web_search", "calculator"],
            "custom": [
                {
                    "name": "custom_tool",
                    "module_path": "custom.tools",
                    "class_name": "CustomTool",
                    "description": "A custom tool",
                    "parameters": {"param1": "value1"}
                }
            ]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(sample_config, f)
            f.flush()
            
            loader = ConfigLoader()
            config = loader.load_config(f.name)
            
            assert len(config.tools.built_in) == 2
            assert "web_search" in config.tools.built_in
            assert len(config.tools.custom) == 1
            assert config.tools.custom[0].name == "custom_tool"
            
            os.unlink(f.name)
        
        del os.environ["TEST_API_KEY"]


if __name__ == "__main__":
    pytest.main([__file__])