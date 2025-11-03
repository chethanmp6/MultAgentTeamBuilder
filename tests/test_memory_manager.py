"""
Tests for memory manager functionality.
"""
import pytest
from datetime import datetime, timedelta
from langchain_core.messages import HumanMessage, AIMessage

from src.memory.memory_manager import MemoryManager
from src.core.config_loader import MemoryConfig, MemoryTypesConfig, MemoryStorageConfig, MemorySettingsConfig


@pytest.fixture
def memory_config():
    """Create a test memory configuration."""
    return MemoryConfig(
        enabled=True,
        provider="langmem",
        types=MemoryTypesConfig(
            semantic=True,
            episodic=True,
            procedural=True
        ),
        storage=MemoryStorageConfig(
            backend="memory"
        ),
        settings=MemorySettingsConfig(
            max_memory_size=100,
            retention_days=7,
            background_processing=True
        )
    )


@pytest.fixture
def disabled_memory_config():
    """Create a disabled memory configuration."""
    return MemoryConfig(
        enabled=False,
        provider="langmem",
        types=MemoryTypesConfig(),
        storage=MemoryStorageConfig(),
        settings=MemorySettingsConfig()
    )


class TestMemoryManager:
    """Test cases for MemoryManager."""
    
    def test_initialization(self, memory_config):
        """Test memory manager initialization."""
        manager = MemoryManager(memory_config)
        
        assert manager.config == memory_config
        assert isinstance(manager.semantic_memory, dict)
        assert isinstance(manager.episodic_memory, list)
        assert isinstance(manager.procedural_memory, dict)
    
    def test_disabled_memory(self, disabled_memory_config):
        """Test behavior when memory is disabled."""
        manager = MemoryManager(disabled_memory_config)
        
        messages = [HumanMessage(content="Test message")]
        response = AIMessage(content="Test response")
        
        # Store interaction should do nothing
        manager.store_interaction(messages, response)
        assert len(manager.episodic_memory) == 0
        
        # Retrieve memory should return empty
        memory = manager.retrieve_memory("test query")
        assert memory == {}
    
    def test_store_and_retrieve_episodic_memory(self, memory_config):
        """Test storing and retrieving episodic memory."""
        manager = MemoryManager(memory_config)
        
        messages = [HumanMessage(content="What is Python programming?")]
        response = AIMessage(content="Python is a programming language")
        
        # Store interaction
        manager.store_interaction(messages, response)
        
        # Check that it was stored
        assert len(manager.episodic_memory) == 1
        episode = manager.episodic_memory[0]
        assert episode["messages"][0]["content"] == "What is Python programming?"
        assert episode["response"]["content"] == "Python is a programming language"
    
    def test_semantic_memory_extraction(self, memory_config):
        """Test semantic memory extraction."""
        manager = MemoryManager(memory_config)
        
        messages = [HumanMessage(content="Python is a programming language")]
        response = AIMessage(content="Yes, Python is popular for data science")
        
        # Store interaction
        manager.store_interaction(messages, response)
        
        # Check semantic memory was updated
        assert len(manager.semantic_memory) > 0
    
    def test_procedural_memory_update(self, memory_config):
        """Test procedural memory updates."""
        manager = MemoryManager(memory_config)
        
        messages = [HumanMessage(content="How do I install Python packages?")]
        response = AIMessage(content="Successfully completed pip install command")
        
        # Store interaction
        manager.store_interaction(messages, response)
        
        # Check procedural memory was updated
        assert len(manager.procedural_memory) > 0
        
        # Store another successful interaction with same pattern
        manager.store_interaction(messages, response)
        
        # Success count should increase
        pattern_id = list(manager.procedural_memory.keys())[0]
        assert manager.procedural_memory[pattern_id]["success_count"] >= 1
    
    def test_search_semantic_memory(self, memory_config):
        """Test searching semantic memory."""
        manager = MemoryManager(memory_config)
        
        # Add some semantic facts
        manager.semantic_memory["fact1"] = {
            "fact": "Python is a programming language",
            "confidence": 0.9,
            "timestamp": datetime.now().isoformat()
        }
        manager.semantic_memory["fact2"] = {
            "fact": "Java is also a programming language",
            "confidence": 0.8,
            "timestamp": datetime.now().isoformat()
        }
        
        # Search for relevant facts
        results = manager._search_semantic_memory("Python programming")
        assert len(results) > 0
        assert any("Python" in result for result in results)
    
    def test_search_episodic_memory(self, memory_config):
        """Test searching episodic memory."""
        manager = MemoryManager(memory_config)
        
        # Add some episodes
        messages1 = [HumanMessage(content="Tell me about Python")]
        response1 = AIMessage(content="Python is great for programming")
        manager.store_interaction(messages1, response1)
        
        messages2 = [HumanMessage(content="What about Java?")]
        response2 = AIMessage(content="Java is also a good language")
        manager.store_interaction(messages2, response2)
        
        # Search episodes
        results = manager._search_episodic_memory("Python programming")
        assert len(results) > 0
    
    def test_get_relevant_context(self, memory_config):
        """Test getting relevant context."""
        manager = MemoryManager(memory_config)
        
        # Add some memory data
        messages = [HumanMessage(content="Python is excellent for data science")]
        response = AIMessage(content="Yes, with libraries like pandas and numpy")
        manager.store_interaction(messages, response)
        
        # Get context
        context = manager.get_relevant_context("Python data science")
        assert isinstance(context, str)
        # Context should contain relevant information if memory is working
    
    def test_memory_cleanup(self, memory_config):
        """Test memory cleanup based on size and retention."""
        # Set very small limits for testing
        memory_config.settings.max_memory_size = 2
        memory_config.settings.retention_days = 1
        
        manager = MemoryManager(memory_config)
        
        # Add more episodes than the limit
        for i in range(5):
            messages = [HumanMessage(content=f"Message {i}")]
            response = AIMessage(content=f"Response {i}")
            manager.store_interaction(messages, response)
        
        # Should be cleaned up to max size
        assert len(manager.episodic_memory) <= memory_config.settings.max_memory_size
    
    def test_memory_stats(self, memory_config):
        """Test getting memory statistics."""
        manager = MemoryManager(memory_config)
        
        # Add some data
        messages = [HumanMessage(content="Test message")]
        response = AIMessage(content="Test response")
        manager.store_interaction(messages, response)
        
        stats = manager.get_stats()
        assert stats["memory_enabled"] is True
        assert "semantic_facts" in stats
        assert "episodic_interactions" in stats
        assert "procedural_patterns" in stats
        assert stats["retention_days"] == 7
        assert stats["max_memory_size"] == 100
    
    def test_clear_memory(self, memory_config):
        """Test clearing all memory."""
        manager = MemoryManager(memory_config)
        
        # Add some data
        messages = [HumanMessage(content="Test message")]
        response = AIMessage(content="Test response")
        manager.store_interaction(messages, response)
        
        # Verify data exists
        assert len(manager.episodic_memory) > 0 or len(manager.semantic_memory) > 0
        
        # Clear memory
        manager.clear_memory()
        
        # Verify all memory is cleared
        assert len(manager.episodic_memory) == 0
        assert len(manager.semantic_memory) == 0
        assert len(manager.procedural_memory) == 0
        assert len(manager.memory_store) == 0
    
    def test_export_import_history(self, memory_config):
        """Test exporting and importing memory history."""
        manager = MemoryManager(memory_config)
        
        # Add some data
        messages = [HumanMessage(content="Test message")]
        response = AIMessage(content="Test response")
        manager.store_interaction(messages, response)
        
        # Export history
        history_json = manager.export_history()
        assert isinstance(history_json, str)
        assert "semantic_memory" in history_json
        assert "episodic_memory" in history_json
        
        # Clear memory and import
        manager.clear_memory()
        manager.import_history(history_json)
        
        # Verify data was restored
        stats_after = manager.get_stats()
        assert stats_after["episodic_interactions"] > 0
    
    def test_store_individual_memory(self, memory_config):
        """Test storing individual memory items."""
        manager = MemoryManager(memory_config)
        
        content = HumanMessage(content="Important information to remember")
        manager.store_memory(content)
        
        assert len(manager.memory_store) > 0


if __name__ == "__main__":
    pytest.main([__file__])