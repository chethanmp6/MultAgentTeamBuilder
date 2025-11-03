# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Installation & Setup
```bash
# Automated setup (recommended)
python setup.py

# Or manual setup
pip install -r requirements.txt
cp env.example .env
# Edit .env file and add your API keys
```

Required environment variables:
```bash
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
GROQ_API_KEY=your-groq-api-key-here
```

### Testing
```bash
# Run all tests with comprehensive test runner
python run_tests.py --all

# Run specific test categories
python run_tests.py --unit      # Unit tests
python run_tests.py --integration  # Integration tests
python run_tests.py --lint      # Code quality checks
python run_tests.py --quick     # Quick smoke test

# Traditional pytest commands
pytest tests/
pytest tests/test_config_loader.py -v
pytest tests/ --cov=src --cov-report=html

# Run single test method
pytest tests/test_config_loader.py::TestConfigLoader::test_load_valid_config -v
```

### Running Examples
```bash
# Run usage examples (requires API keys)
python examples/usage_examples.py

# Launch web UI for configuration
python run_web_ui.py

# Launch hierarchical agents web UI (original version)
python run_hierarchical_ui.py

# Launch hierarchical agents web UI (API version - complete feature parity)
python run_hierarchical_ui_api.py

# Launch API server
python run_api_server.py

# Test specific agent configuration
python -c "
from src.core.configurable_agent import ConfigurableAgent
agent = ConfigurableAgent('configs/examples/research_agent.yml')
print(agent.run('test query'))
"
```

## Architecture Overview

This is a **configuration-driven multi-agent system** supporting both single ReAct agents and hierarchical agent teams. All behavior is defined through YAML files with two main architectural patterns:

### Single Agent Architecture (ReAct Pattern)

**Configuration-First Design**: Agent behavior (LLM, prompts, tools, memory) defined in YAML. Uses LangGraph's optimized `create_react_agent()` for reasoning loops.

**Component Initialization Flow**:
1. `ConfigurableAgent` loads YAML → validates with Pydantic models  
2. `_setup_llm()` → creates LLM instance (OpenAI/Anthropic/Google/Groq)
3. `_setup_tools()` → registers built-in and custom tools via `ToolRegistry`
4. `_setup_memory()` → initializes `MemoryManager` with LangMem if enabled
5. `_setup_graph()` → uses `create_react_agent()` with LLM and tools

**ReAct Pattern**: Reasoning → Acting → Observation → Final Answer cycle. More efficient than custom graph construction.

### Hierarchical Agent Architecture (Team Pattern)

**Three-Tier Structure**: Coordinator → Supervisors → Workers with intelligent task routing and cross-team communication.

**Advanced Routing**: Keyword-based, LLM-based, rule-based, capability-based, workload-based, and performance-based routing strategies.

**Dynamic Management**: Runtime addition/removal of agents and teams with real-time performance monitoring.

### Core Components

**src/core/configurable_agent.py** - Main single agent orchestrator with ReAct pattern implementation

**src/core/config_loader.py** - Pydantic models for YAML validation and environment variable resolution

**src/hierarchical/hierarchical_agent.py** - Main hierarchical team coordinator with multi-tier management

**src/hierarchical/supervisor.py** - Team supervisor agents with task delegation capabilities

**src/hierarchical/worker_agent.py** - Specialized worker agents with specific capabilities

**src/memory/memory_manager.py** - LangMem integration (semantic/episodic/procedural memory) with retention policies

**src/tools/tool_registry.py** - Built-in tools (web_search, calculator, file_reader, file_writer, code_executor) and custom tool registration

**src/optimization/prompt_optimizer.py** - A/B testing framework with automatic prompt evolution

### Configuration Patterns

**Single Agent Configuration**:
```yaml
agent: {name, description, version}
llm: {provider, model, parameters}
prompts: {system_prompt with variables}
tools: {built_in list, custom definitions}
memory: {semantic/episodic/procedural config}
react: {max_iterations, recursion_limit}
```

**Hierarchical Team Configuration**:
```yaml
coordinator: {routing_strategy, communication_config}
teams: {supervisor definitions with specializations}
workers: {individual agent configurations}
performance: {monitoring, alerts, analytics}
```

### Web UI Integration

**Single Agent UI** (`run_web_ui.py`): Form-based configuration with real-time YAML preview, template loading, and agent testing

**Hierarchical UI** (`run_hierarchical_ui.py`): Team management interface with performance dashboards and routing visualization

**API-Based Hierarchical UI** (`run_hierarchical_ui_api.py`): Modern web interface that communicates with the FastAPI backend for better scalability and separation of concerns

### FastAPI Backend

**API Server** (`run_api_server.py`): RESTful API server exposing hierarchical agent capabilities
- Team management endpoints (CRUD operations)
- Configuration validation and template management
- Agent library search and compatibility checking
- Task execution with real-time status tracking
- Comprehensive error handling and logging

**Key API Endpoints:**
- `/api/v1/teams/` - Team management
- `/api/v1/configs/` - Configuration operations
- `/api/v1/agents/` - Agent library access
- `/api/v1/executions/` - Task execution management

### Testing Architecture

**Comprehensive Test Runner** (`run_tests.py`): 
- Unit tests for individual components
- Integration tests for full agent workflows  
- Lint tests for code quality
- Quick smoke tests for basic functionality

**Test Patterns**:
- Mock API keys via environment variables
- Temporary YAML files for configuration testing
- Pydantic validation edge case testing
- Tool registry custom tool testing
- Memory manager multi-type testing

### Common Debugging

**Agent Initialization Issues**:
1. Check API key environment variables are set
2. Validate YAML against Pydantic models  
3. Verify custom tool import paths
4. Enable `debug_mode: true` for detailed logging

**Hierarchical Team Issues**:
1. Check coordinator routing configuration
2. Verify team and worker connectivity
3. Monitor performance dashboard for bottlenecks
4. Review task delegation logs