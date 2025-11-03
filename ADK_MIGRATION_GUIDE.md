# Google ADK Migration Guide

This guide provides a comprehensive overview of migrating from LangChain/LangGraph to Google ADK (Agent Development Kit).

## Overview

The migration from LangChain/LangGraph to Google ADK involves:
- Replacing LangChain LLM integrations with Google ADK models
- Converting LangGraph ReAct agents to ADK workflow patterns
- Migrating LangChain tools to ADK tool format
- Updating memory management to use ADK memory systems
- Adapting hierarchical agent coordination to ADK patterns

## Migration Architecture

### Before (LangChain/LangGraph)
```
├── LangChain LLMs (OpenAI, Anthropic, etc.)
├── LangGraph ReAct Agents
├── LangChain Tools & BaseTool
├── LangChain Memory (LangMem)
└── Custom Message Types
```

### After (Google ADK)
```
├── ADK Models (Gemini-based)
├── ADK Agents with Workflows
├── ADK Tools & Functions
├── ADK Memory Management
└── ADK Message System
```

## Component Migration Map

| LangChain/LangGraph | Google ADK | Migration Notes |
|---------------------|------------|-----------------|
| `init_chat_model()` | `Model()` | Use ADK model factory |
| `create_react_agent()` | `Agent()` with workflow | Implement custom ReAct logic |
| `BaseMessage`, `HumanMessage` | `Message` | Use ADK message types |
| `BaseTool`, `@tool` | ADK Tools | Convert to ADK tool format |
| `BaseChatModel` | `Model` | Use ADK model interface |
| LangMem memory | ADK memory | Use ADK memory system |

## Installation and Setup

### 1. Install Google ADK

```bash
# Install ADK and dependencies
pip install -r requirements_adk.txt

# Or install manually
pip install google-adk google-generativeai google-cloud-aiplatform
```

### 2. Environment Configuration

Update your `.env` file:

```bash
# Google API Configuration
GOOGLE_API_KEY=your-google-api-key-here
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_LOCATION=us-central1

# Keep existing keys for gradual migration
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

### 3. Import ADK Components

```python
# Replace LangChain imports
from src.adk import (
    ADKConfigurableAgent,
    ADKHierarchicalAgentTeam,
    ADKToolRegistry,
    ADKMemoryManager
)
```

## Step-by-Step Migration

### Step 1: Single Agent Migration

#### Before (LangChain)
```python
from src.core.configurable_agent import ConfigurableAgent

agent = ConfigurableAgent('configs/examples/coding_assistant.yml')
result = agent.run("Write a Python function")
```

#### After (ADK)
```python
from src.adk.configurable_agent_adk import ADKConfigurableAgent

agent = ADKConfigurableAgent('configs/examples/coding_assistant.yml')
result = agent.run("Write a Python function")
```

### Step 2: Configuration Migration

The ADK config loader automatically converts LangChain configurations:

```yaml
# Original LangChain config
llm:
  provider: "openai"
  model: "gpt-4o-mini"
  api_key_env: "OPENAI_API_KEY"

# Automatically converted to ADK format
llm:
  provider: "google"
  model: "gemini-1.5-flash"
  api_key_env: "GOOGLE_API_KEY"
```

### Step 3: Tool Migration

#### Before (LangChain)
```python
from langchain_core.tools import tool

@tool
def web_search(query: str) -> str:
    return f"Search results for: {query}"
```

#### After (ADK)
```python
from src.adk.tool_registry_adk import ADKToolRegistry

registry = ADKToolRegistry()
registry.register_function_as_tool(
    name="web_search",
    func=web_search,
    description="Search the web for information"
)
```

### Step 4: Hierarchical Agent Migration

#### Before (LangChain)
```python
from src.hierarchical.hierarchical_agent import HierarchicalAgentTeam

team = HierarchicalAgentTeam(name="research_team")
team.add_worker(worker, "research_team")
```

#### After (ADK)
```python
from src.adk.hierarchical.hierarchical_agent_adk import ADKHierarchicalAgentTeam

team = ADKHierarchicalAgentTeam(name="research_team")
team.add_worker(worker, "research_team")
```

### Step 5: Memory Migration

#### Before (LangChain)
```python
from src.memory.memory_manager import MemoryManager

memory = MemoryManager(config.memory)
memory.store_interaction(messages, response)
```

#### After (ADK)
```python
from src.adk.memory_manager_adk import ADKMemoryManager

memory = ADKMemoryManager(config.memory)
memory.store_interaction(messages, response)
```

## Configuration Updates

### Model Mapping

| LangChain Model | ADK Model |
|-----------------|-----------|
| `gpt-4o-mini` | `gemini-1.5-flash` |
| `gpt-4` | `gemini-1.5-pro` |
| `claude-3-5-sonnet` | `gemini-1.5-pro` |
| `claude-3-haiku` | `gemini-1.5-flash` |

### Provider Mapping

| LangChain Provider | ADK Provider |
|-------------------|--------------|
| `openai` | `google` |
| `anthropic` | `google` |
| `gemini` | `google` |
| `groq` | `google` |

## API and Web UI Updates

### API Server Updates

The API server automatically supports both LangChain and ADK agents:

```python
# api/services/agent_service.py
def create_agent(config_data, framework="adk"):
    if framework == "adk":
        return ADKConfigurableAgent(config_data=config_data)
    else:
        return ConfigurableAgent(config_data=config_data)
```

### Web UI Updates

The web interface provides framework selection:

```python
# Web UI framework selector
framework = st.selectbox(
    "Agent Framework",
    ["Google ADK", "LangChain (Legacy)"],
    index=0  # Default to ADK
)
```

## Testing the Migration

### 1. Unit Tests

```bash
# Run ADK-specific tests
python -m pytest tests/test_adk/ -v

# Run migration validation tests
python tests/test_migration_validation.py
```

### 2. Integration Tests

```bash
# Test ADK agent functionality
python -c "
from src.adk import ADKConfigurableAgent
agent = ADKConfigurableAgent('configs/examples/web_browser_agent.yml')
print(agent.run('Test ADK integration'))
"
```

### 3. Hierarchical Team Tests

```bash
# Test ADK hierarchical teams
python -c "
from src.adk.hierarchical import ADKHierarchicalAgentTeam
team = ADKHierarchicalAgentTeam(name='test_team')
print(team.get_hierarchy_info())
"
```

## Migration Utilities

### Automatic Migration Script

```python
# migrate_to_adk.py
from src.adk.migration_utils import LangChainToADKMigrator

migrator = LangChainToADKMigrator()

# Migrate single agent
adk_agent = migrator.migrate_agent(langchain_agent)

# Migrate hierarchical team
adk_team = migrator.migrate_team(langchain_team)

# Generate migration report
report = migrator.generate_migration_report()
```

### Migration Validation

```python
# Validate migration completeness
from src.adk.validation import validate_migration

validation_result = validate_migration(
    original_agent=langchain_agent,
    migrated_agent=adk_agent
)

print(f"Migration successful: {validation_result['success']}")
print(f"Components migrated: {validation_result['components']}")
```

## Best Practices

### 1. Gradual Migration

- Start with single agents before hierarchical teams
- Test each component individually
- Keep LangChain components available during transition

### 2. Configuration Management

- Use ADK config loader for automatic conversion
- Validate configurations before deployment
- Maintain backward compatibility during migration

### 3. Performance Monitoring

- Compare ADK vs LangChain performance
- Monitor memory usage and response times
- Use ADK's built-in monitoring features

### 4. Error Handling

- Implement fallback mechanisms
- Log migration warnings and errors
- Provide clear error messages

## Troubleshooting

### Common Issues

#### 1. API Key Configuration
```bash
# Verify Google API key
echo $GOOGLE_API_KEY

# Test API connectivity
python -c "import google.generativeai as genai; genai.configure(api_key='$GOOGLE_API_KEY'); print('API key valid')"
```

#### 2. Model Compatibility
```python
# Check available models
from google.generativeai import list_models
for model in list_models():
    print(model.name)
```

#### 3. Tool Migration Issues
```python
# Validate tool conversion
from src.adk.tool_registry_adk import ADKToolRegistry
registry = ADKToolRegistry()
print(registry.get_migration_stats())
```

#### 4. Memory Migration
```python
# Check memory compatibility
from src.adk.memory_manager_adk import ADKMemoryManager
memory = ADKMemoryManager(config)
print(memory.get_adk_integration_info())
```

### Getting Help

1. Check ADK documentation: https://google.github.io/adk-docs/
2. Review migration logs for warnings and errors
3. Use validation utilities to verify migration
4. Test with simple examples before complex workflows

## Feature Comparison

| Feature | LangChain/LangGraph | Google ADK | Migration Status |
|---------|-------------------|------------|------------------|
| Single Agents | ✅ | ✅ | ✅ Complete |
| Hierarchical Teams | ✅ | ✅ | ✅ Complete |
| Tool System | ✅ | ✅ | ✅ Complete |
| Memory Management | ✅ | ✅ | ✅ Complete |
| ReAct Pattern | ✅ | ✅ | ✅ Complete |
| Multi-Provider LLMs | ✅ | 🔄 Google-focused | ⚠️ Partial |
| Web UI | ✅ | ✅ | ✅ Complete |
| API Server | ✅ | ✅ | ✅ Complete |

## Next Steps

1. **Install Dependencies**: Set up ADK environment
2. **Test Migration**: Start with simple single agents
3. **Validate Functionality**: Ensure all features work as expected
4. **Deploy Gradually**: Migrate production systems incrementally
5. **Monitor Performance**: Compare ADK vs LangChain metrics
6. **Optimize Configuration**: Fine-tune ADK-specific settings

## Support

For migration support:
- Review the ADK documentation
- Check migration logs and validation results
- Use the built-in migration utilities
- Test thoroughly before production deployment

The migration provides access to Google's latest AI capabilities while maintaining all existing functionality.