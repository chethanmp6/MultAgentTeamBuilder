"""
ADK-compatible tool registry for managing built-in and custom tools.
Migrated from LangChain-based tool_registry.py to Google ADK.
"""
import importlib
import inspect
from typing import Dict, Any, List, Callable, Optional, Union
from functools import wraps

# ADK imports (with fallback for development)
try:
    from google_adk.tools import Tool
    from google_adk import Agent
    ADK_AVAILABLE = True
except ImportError:
    # Fallback for development/testing
    print("Warning: Google ADK not available. Using mock implementations.")

    class Tool:
        def __init__(self, name: str, description: str, func: Callable):
            self.name = name
            self.description = description
            self.func = func

    class Agent:
        pass

    ADK_AVAILABLE = False


class ADKToolRegistry:
    """ADK-compatible registry for managing available tools for agents."""

    def __init__(self):
        self._built_in_tools: Dict[str, Tool] = {}
        self._custom_tools: Dict[str, Tool] = {}
        self._initialize_built_in_tools()

    def _initialize_built_in_tools(self):
        """Initialize built-in tools in ADK format."""

        def adk_tool(name: str, description: str):
            """Decorator to create ADK tools."""
            def decorator(func: Callable) -> Tool:
                if ADK_AVAILABLE:
                    return Tool(name=name, description=description, func=func)
                else:
                    # Mock implementation for development
                    return Tool(name, description, func)
            return decorator

        @adk_tool("web_search", "Search the web for information using Google Search")
        def web_search(query: str) -> Dict[str, Any]:
            """
            Search the web for information.

            Args:
                query: The search query string

            Returns:
                Dictionary with search results and metadata
            """
            # In real ADK implementation, this would use Google Search API
            return {
                "query": query,
                "results": [
                    {
                        "title": f"Search result for: {query}",
                        "url": "https://example.com",
                        "snippet": f"Information about {query}"
                    }
                ],
                "status": "success",
                "total_results": 1
            }

        @adk_tool("calculator", "Perform mathematical calculations")
        def calculator(expression: str) -> Dict[str, Any]:
            """
            Calculate mathematical expressions safely.

            Args:
                expression: Mathematical expression to evaluate

            Returns:
                Dictionary with calculation result and metadata
            """
            try:
                # Safe evaluation of mathematical expressions
                allowed_chars = set('0123456789+-*/.() ')
                if not all(c in allowed_chars for c in expression):
                    raise ValueError("Invalid characters in expression")

                result = eval(expression)
                return {
                    "expression": expression,
                    "result": result,
                    "status": "success"
                }
            except Exception as e:
                return {
                    "expression": expression,
                    "error": str(e),
                    "status": "error"
                }

        @adk_tool("file_reader", "Read contents from a file")
        def file_reader(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
            """
            Read contents of a file.

            Args:
                file_path: Path to the file to read
                encoding: File encoding (default: utf-8)

            Returns:
                Dictionary with file contents and metadata
            """
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    content = f.read()
                return {
                    "file_path": file_path,
                    "content": content,
                    "size": len(content),
                    "status": "success"
                }
            except Exception as e:
                return {
                    "file_path": file_path,
                    "error": str(e),
                    "status": "error"
                }

        @adk_tool("file_writer", "Write content to a file")
        def file_writer(file_path: str, content: str, encoding: str = "utf-8") -> Dict[str, Any]:
            """
            Write content to a file.

            Args:
                file_path: Path to the file to write
                content: Content to write to the file
                encoding: File encoding (default: utf-8)

            Returns:
                Dictionary with operation result and metadata
            """
            try:
                with open(file_path, 'w', encoding=encoding) as f:
                    f.write(content)
                return {
                    "file_path": file_path,
                    "bytes_written": len(content.encode(encoding)),
                    "status": "success"
                }
            except Exception as e:
                return {
                    "file_path": file_path,
                    "error": str(e),
                    "status": "error"
                }

        @adk_tool("code_executor", "Execute code in a safe environment")
        def code_executor(code: str, language: str = "python") -> Dict[str, Any]:
            """
            Execute code in specified language (with safety restrictions).

            Args:
                code: Code to execute
                language: Programming language (currently supports 'python')

            Returns:
                Dictionary with execution result and metadata
            """
            if language.lower() != "python":
                return {
                    "code": code,
                    "language": language,
                    "error": f"Language {language} not supported",
                    "status": "error"
                }

            try:
                # Create a restricted execution environment
                exec_globals = {
                    "__builtins__": {
                        "print": print,
                        "len": len,
                        "str": str,
                        "int": int,
                        "float": float,
                        "list": list,
                        "dict": dict,
                        "range": range
                    }
                }

                # Capture stdout
                import io
                import sys
                old_stdout = sys.stdout
                sys.stdout = captured_output = io.StringIO()

                try:
                    exec(code, exec_globals)
                    output = captured_output.getvalue()
                finally:
                    sys.stdout = old_stdout

                return {
                    "code": code,
                    "language": language,
                    "output": output,
                    "status": "success"
                }
            except Exception as e:
                return {
                    "code": code,
                    "language": language,
                    "error": str(e),
                    "status": "error"
                }

        @adk_tool("gemini_chat", "Chat with Google Gemini model")
        def gemini_chat(prompt: str, model: str = "gemini-1.5-flash") -> Dict[str, Any]:
            """
            Chat with Google Gemini model directly.

            Args:
                prompt: Input prompt for the model
                model: Gemini model to use

            Returns:
                Dictionary with model response and metadata
            """
            # This would integrate with actual Gemini API in production
            return {
                "prompt": prompt,
                "model": model,
                "response": f"Gemini response to: {prompt}",
                "status": "success"
            }

        # Register built-in tools
        self._built_in_tools = {
            "web_search": web_search,
            "calculator": calculator,
            "file_reader": file_reader,
            "file_writer": file_writer,
            "code_executor": code_executor,
            "gemini_chat": gemini_chat
        }

    def get_built_in_tools(self) -> List[str]:
        """Get list of available built-in tools."""
        return list(self._built_in_tools.keys())

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """Get a tool by name."""
        if tool_name in self._built_in_tools:
            return self._built_in_tools[tool_name]
        elif tool_name in self._custom_tools:
            return self._custom_tools[tool_name]
        return None

    def get_tools_by_names(self, tool_names: List[str]) -> List[Tool]:
        """Get multiple tools by their names."""
        tools = []
        for name in tool_names:
            tool = self.get_tool(name)
            if tool:
                tools.append(tool)
        return tools

    def register_custom_tool(self,
                           name: str,
                           function_name: str,
                           description: str,
                           module_path: Optional[str] = None,
                           parameters: Dict[str, Any] = None) -> bool:
        """
        Register a custom tool from a module or function.

        Args:
            name: Tool name
            function_name: Function name (replaces class_name from LangChain)
            description: Tool description
            module_path: Optional module path for external functions
            parameters: Optional parameters for the function

        Returns:
            True if registration successful, False otherwise
        """
        try:
            if module_path:
                # Import function from module
                module = importlib.import_module(module_path)
                tool_function = getattr(module, function_name)
            else:
                # Assume function is available in current scope
                # This is a simplified implementation
                return False

            # Create ADK tool
            if ADK_AVAILABLE:
                tool_instance = Tool(name=name, description=description, func=tool_function)
            else:
                tool_instance = Tool(name, description, tool_function)

            self._custom_tools[name] = tool_instance
            return True

        except Exception as e:
            print(f"Error registering custom tool {name}: {str(e)}")
            return False

    def register_function_as_tool(self,
                                name: str,
                                func: Callable,
                                description: str) -> bool:
        """
        Register a function as a custom ADK tool.

        Args:
            name: Tool name
            func: Function to register
            description: Tool description

        Returns:
            True if registration successful, False otherwise
        """
        try:
            if ADK_AVAILABLE:
                tool_instance = Tool(name=name, description=description, func=func)
            else:
                tool_instance = Tool(name, description, func)

            self._custom_tools[name] = tool_instance
            return True
        except Exception as e:
            print(f"Error registering function as tool {name}: {str(e)}")
            return False

    def list_all_tools(self) -> Dict[str, str]:
        """List all available tools with their descriptions."""
        all_tools = {}

        # Add built-in tools
        for name, tool in self._built_in_tools.items():
            if hasattr(tool, 'description'):
                all_tools[name] = tool.description
            else:
                all_tools[name] = f"Built-in ADK tool: {name}"

        # Add custom tools
        for name, tool in self._custom_tools.items():
            if hasattr(tool, 'description'):
                all_tools[name] = tool.description
            else:
                all_tools[name] = f"Custom ADK tool: {name}"

        return all_tools

    def remove_custom_tool(self, name: str) -> bool:
        """Remove a custom tool."""
        if name in self._custom_tools:
            del self._custom_tools[name]
            return True
        return False

    def validate_tools(self, tool_names: List[str]) -> List[str]:
        """Validate that all specified tools exist. Returns list of missing tools."""
        missing_tools = []
        for name in tool_names:
            if name not in self._built_in_tools and name not in self._custom_tools:
                missing_tools.append(name)
        return missing_tools

    def get_adk_tools_for_agent(self, tool_names: List[str]) -> List[Tool]:
        """
        Get tools in ADK format for agent initialization.

        Args:
            tool_names: List of tool names to retrieve

        Returns:
            List of ADK Tool objects
        """
        adk_tools = []
        for name in tool_names:
            tool = self.get_tool(name)
            if tool:
                adk_tools.append(tool)
            else:
                print(f"Warning: Tool '{name}' not found")

        return adk_tools

    def create_tool_from_langchain(self, langchain_tool) -> Optional[Tool]:
        """
        Convert a LangChain tool to ADK format.

        Args:
            langchain_tool: LangChain BaseTool instance

        Returns:
            ADK Tool instance or None if conversion fails
        """
        try:
            name = getattr(langchain_tool, 'name', 'unknown_tool')
            description = getattr(langchain_tool, 'description', 'Converted from LangChain')

            # Create a wrapper function for the LangChain tool
            def adk_wrapper(*args, **kwargs):
                return langchain_tool.run(*args, **kwargs)

            if ADK_AVAILABLE:
                return Tool(name=name, description=description, func=adk_wrapper)
            else:
                return Tool(name, description, adk_wrapper)

        except Exception as e:
            print(f"Error converting LangChain tool to ADK: {str(e)}")
            return None

    def get_migration_stats(self) -> Dict[str, Any]:
        """Get statistics about the tool migration."""
        return {
            "total_tools": len(self._built_in_tools) + len(self._custom_tools),
            "built_in_tools": len(self._built_in_tools),
            "custom_tools": len(self._custom_tools),
            "adk_available": ADK_AVAILABLE,
            "tool_list": list(self._built_in_tools.keys()) + list(self._custom_tools.keys())
        }