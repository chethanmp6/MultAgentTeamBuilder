"""
Tests for tool registry functionality.
"""
import pytest
from src.tools.tool_registry import ToolRegistry
from langchain.tools import BaseTool
from langchain_core.tools import tool


class MockCustomTool(BaseTool):
    """Mock custom tool for testing."""
    name: str = "mock_tool"
    description: str = "A mock tool for testing"
    
    def _run(self, query: str) -> str:
        return f"Mock result for: {query}"


class TestToolRegistry:
    """Test cases for ToolRegistry."""
    
    def test_initialization(self):
        """Test tool registry initialization."""
        registry = ToolRegistry()
        
        # Check that built-in tools are loaded
        built_in_tools = registry.get_built_in_tools()
        assert len(built_in_tools) > 0
        assert "web_search" in built_in_tools
        assert "calculator" in built_in_tools
        assert "file_reader" in built_in_tools
        assert "file_writer" in built_in_tools
        assert "code_executor" in built_in_tools
    
    def test_get_tool(self):
        """Test getting individual tools."""
        registry = ToolRegistry()
        
        # Test getting built-in tool
        calculator = registry.get_tool("calculator")
        assert calculator is not None
        assert callable(calculator)
        
        # Test getting non-existent tool
        nonexistent = registry.get_tool("nonexistent_tool")
        assert nonexistent is None
    
    def test_get_tools_by_names(self):
        """Test getting multiple tools by names."""
        registry = ToolRegistry()
        
        tool_names = ["calculator", "web_search", "nonexistent"]
        tools = registry.get_tools_by_names(tool_names)
        
        # Should return only the existing tools
        assert len(tools) == 2
    
    def test_register_function_as_tool(self):
        """Test registering a function as a custom tool."""
        registry = ToolRegistry()
        
        def custom_function(input_text: str) -> str:
            """A custom function for testing."""
            return f"Processed: {input_text}"
        
        # Register function
        success = registry.register_function_as_tool(
            name="custom_func",
            func=custom_function,
            description="A custom function tool"
        )
        
        assert success is True
        
        # Verify tool was registered
        tool = registry.get_tool("custom_func")
        assert tool is not None
    
    def test_list_all_tools(self):
        """Test listing all available tools."""
        registry = ToolRegistry()
        
        all_tools = registry.list_all_tools()
        assert isinstance(all_tools, dict)
        assert len(all_tools) > 0
        
        # Should include built-in tools
        assert "calculator" in all_tools
        assert "web_search" in all_tools
    
    def test_validate_tools(self):
        """Test tool validation."""
        registry = ToolRegistry()
        
        # Valid tools
        valid_tools = ["calculator", "web_search"]
        missing = registry.validate_tools(valid_tools)
        assert len(missing) == 0
        
        # Mix of valid and invalid tools
        mixed_tools = ["calculator", "nonexistent1", "web_search", "nonexistent2"]
        missing = registry.validate_tools(mixed_tools)
        assert len(missing) == 2
        assert "nonexistent1" in missing
        assert "nonexistent2" in missing
    
    def test_remove_custom_tool(self):
        """Test removing custom tools."""
        registry = ToolRegistry()
        
        # Register a custom tool first
        def test_func(input_text: str) -> str:
            """A test function for testing."""
            return input_text
        
        registry.register_function_as_tool(
            name="test_tool",
            func=test_func,
            description="Test tool"
        )
        
        # Verify it exists
        assert registry.get_tool("test_tool") is not None
        
        # Remove it
        success = registry.remove_custom_tool("test_tool")
        assert success is True
        
        # Verify it's gone
        assert registry.get_tool("test_tool") is None
        
        # Try removing non-existent tool
        success = registry.remove_custom_tool("nonexistent")
        assert success is False
    
    def test_built_in_calculator_tool(self):
        """Test the built-in calculator tool."""
        registry = ToolRegistry()
        calculator = registry.get_tool("calculator")
        
        # Test basic calculation
        result = calculator.invoke("2 + 2")
        assert "4" in result
        
        # Test invalid expression
        result = calculator.invoke("invalid expression")
        assert "Error" in result
    
    def test_built_in_web_search_tool(self):
        """Test the built-in web search tool."""
        registry = ToolRegistry()
        web_search = registry.get_tool("web_search")
        
        result = web_search.invoke("test query")
        assert "Web search results for: test query" in result
    
    def test_built_in_code_executor_tool(self):
        """Test the built-in code executor tool."""
        registry = ToolRegistry()
        code_executor = registry.get_tool("code_executor")
        
        # Test valid Python code
        result = code_executor.invoke("print('hello')")
        assert "executed successfully" in result.lower()
        
        # Test invalid code
        result = code_executor.invoke("invalid python code")
        assert "Error" in result
        
        # Test unsupported language
        result = code_executor.invoke({"code": "console.log('hello')", "language": "javascript"})
        assert "not supported" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__])