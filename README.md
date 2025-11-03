# Hierarchical Agent Teams - API-Based Architecture

A powerful, scalable system for creating **hierarchical AI agent teams** using LangGraph's ReAct pattern, with integrated memory management via LangMem, dynamic prompt optimization, and **FastAPI-based REST architecture** for production-ready deployments.

## 🚀 Features

### 🏢 Hierarchical Agent Teams (Primary Focus)
- **Three-tier Architecture**: Coordinator → Supervisors → Workers
- **Intelligent Routing**: Advanced algorithms for optimal task delegation
- **Dynamic Team Management**: Add/remove agents and teams at runtime
- **Cross-team Communication**: Enable collaboration between teams
- **Performance Monitoring**: Real-time metrics and analytics
- **Configuration-driven**: All behavior defined through YAML configs

### 🔥 API-First Architecture (Recommended)
- **FastAPI Backend**: Production-ready REST APIs with automatic documentation
- **Scalable Design**: Multi-process architecture (API server + UI)
- **External Integration**: Full REST API access for other applications
- **Real-time Tracking**: Status monitoring for long-running tasks
- **Comprehensive Error Handling**: HTTP status codes and detailed error messages
- **API Documentation**: Automatic Swagger UI and ReDoc generation

### 🧠 Advanced Routing Strategies
- **Keyword-based**: Route by matching task keywords to agent capabilities
- **LLM-based**: Use language models for intelligent routing decisions
- **Rule-based**: Route using predefined business rules
- **Capability-based**: Match tasks to agent specializations
- **Workload-based**: Balance load across available agents
- **Performance-based**: Route to highest-performing agents
- **Hybrid**: Combine multiple strategies for optimal results

### 🛠️ Core System Features
- **YAML Configuration**: Complete agent configuration through YAML files
- **LLM Flexibility**: Support for OpenAI, Anthropic, Google Gemini, Groq, and other providers
- **ReAct Agent Pattern**: Uses LangGraph's optimized ReAct (Reasoning + Acting) agents
- **Memory Integration**: LangMem integration for semantic, episodic, and procedural memory
- **Prompt Optimization**: Dynamic prompt improvement with A/B testing
- **Tool Registry**: Built-in and custom tool management
- **Template System**: Reusable agent templates for different use cases

## 🚀 Quick Start (API-Based - Recommended)

### Step 1: Setup

```bash
# Automated setup (recommended)
python3 setup.py
```

This will:
- Create a virtual environment
- Install all dependencies
- Set up the `.env` file
- Test the installation

**Or manual setup:**
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp env.example .env
# Edit .env file and add your API keys
```

**Required environment variables:**
```bash
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
GROQ_API_KEY=your-groq-api-key-here
```

### Step 2: Start the FastAPI Server

```bash
python run_api_server.py
```

The API server will start on http://localhost:8000 with:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Step 3: Start the Web UI

```bash
# In a separate terminal, launch the API-based web interface (Complete version)
python run_hierarchical_ui_api.py
# Or directly with streamlit (Complete version)
streamlit run hierarchical_web_ui_api_complete.py
```

The web interface will be available at: http://localhost:8501

**Note**: The launcher automatically starts the complete version (`hierarchical_web_ui_api_complete.py`) which includes all advanced features.

## 🎯 Basic Usage

### Creating Hierarchical Teams via API

```python
from ui.api_client import get_api_client

# Get the API client
client = get_api_client()

# Create a team from template
team = client.create_team(
    name="My Research Team",
    description="Team for research tasks",
    template_id="research_pipeline_team"
)

print(f"Created team: {team['name']} with ID: {team['id']}")

# Execute a task
execution = client.execute_task(
    team_id=team['id'],
    input_text="Research the latest developments in quantum computing",
    timeout_seconds=300
)

print(f"Started execution: {execution['execution_id']}")

# Get execution results
result = client.get_execution(execution['execution_id'])
print(f"Status: {result['status']['status']}")
if result['result']:
    print(f"Response: {result['result']['response']}")
```

### Using HTTP Requests Directly

```python
import httpx

client = httpx.Client(base_url="http://localhost:8000")

# List available templates
templates = client.get("/api/v1/configs/templates").json()
print(f"Available templates: {len(templates['templates'])}")

# Create team from template
team_data = {
    "name": "My API Team",
    "description": "Team created via API",
    "template_id": "research_pipeline_team"
}
team = client.post("/api/v1/teams/", json=team_data).json()

# Execute task
task_data = {
    "input_text": "Analyze the current state of AI research",
    "timeout_seconds": 300
}
execution = client.post(f"/api/v1/executions/{team['id']}/execute", json=task_data).json()

# Get results
result = client.get(f"/api/v1/executions/{execution['execution_id']}").json()
```

## 🚀 Simple Team Builder (Featured in Complete UI)

The **Simple Team Builder** is the flagship feature of the complete web interface, providing a step-by-step wizard for creating hierarchical agent teams:

### 📋 **4-Step Process**

1. **Step 1: Select Supervisor** - Choose from available supervisor agents
2. **Step 2: Add Workers** - Select and configure worker agents with specific capabilities
3. **Step 3: Validate & Optimize** - AI-powered configuration validation and prompt optimization
4. **Step 4: Deploy Your Team** - Test deployment and final team creation

### 🧪 **Test Deployment Feature**

- **Pre-deployment Testing**: Test your team with custom prompts before production deployment
- **Real-time Monitoring**: Track test execution status and performance metrics
- **Detailed Results**: View team responses, routing decisions, and execution analytics
- **Troubleshooting**: Built-in guidance for common configuration issues
- **Safe Testing**: Temporary test teams automatically cleaned up after testing

### ✨ **Key Benefits**

- **No Configuration Required**: Visual interface eliminates YAML complexity
- **Intelligent Validation**: AI-powered optimization of routing prompts and team structure
- **Risk-Free Testing**: Verify team functionality before deployment
- **Performance Insights**: Understand how your team processes and routes tasks

## 🖥️ Web Interface Features

### 🆕 API-Based Web UI (Primary Interface)

The system provides two API-based Streamlit interfaces:

#### 🚀 **Complete Version** (Default - `hierarchical_web_ui_api_complete.py`)
**Launched by**: `python run_hierarchical_ui_api.py`

**Full-Featured Interface** with all capabilities:

- **🚀 Simple Team Builder**: Step-by-step wizard for creating hierarchical teams
- **🧪 Test Deployment**: Test teams before production deployment
- **🔍 Configuration Validation**: AI-powered validation and optimization
- **🎯 Multi-Tab Interface**: Organized tabs for team management, configuration, execution tracking
- **📝 Visual Configuration**: Form-based configuration with validation and help text
- **💾 File Operations**: Load example configs, upload/download YAML files
- **🔍 Live Preview**: Real-time YAML preview with validation
- **🚀 Quick Templates**: One-click loading of pre-configured team templates
- **🏗️ Team Builder**: Visual hierarchical team builder with drag-and-drop
- **📊 Performance Dashboard**: Real-time metrics and analytics
- **🗂️ Enhanced Agent Library**: Advanced search, filtering, and compatibility checking

#### 📋 **Basic Version** (Optional - `hierarchical_web_ui_api.py`)
**Launched by**: `streamlit run hierarchical_web_ui_api.py`

**Lightweight Interface** for simple use cases:
- **🏗️ Basic Team Management**: Create and manage teams from templates
- **🚀 Task Execution**: Execute tasks on deployed teams
- **📈 Execution History**: View past executions and results
- **🗂️ Agent Library**: Browse available agents
- **⚡ Minimal Resource Usage**: Faster startup and lower resource requirements

#### 🔥 **Shared API-Based Features** (Both Versions):
- **🔌 API Integration**: All operations go through REST APIs
- **📈 Execution Tracking**: Real-time status tracking for long-running tasks
- **🔄 Enhanced Error Handling**: Comprehensive error messages and recovery
- **🌐 External Access**: APIs can be consumed by other applications
- **📊 Server-side Monitoring**: Enhanced metrics and logging
- **🔒 Scalable Architecture**: Multi-process design for production use

## 🚀 API Reference

The FastAPI backend exposes comprehensive hierarchical agent capabilities:

### Key API Endpoints

- **`/api/v1/teams/`** - Team management (CRUD operations)
- **`/api/v1/configs/`** - Configuration operations and templates
- **`/api/v1/agents/`** - Agent library access and search
- **`/api/v1/executions/`** - Task execution management and tracking

### Configuration via API

```python
# Validate a configuration
config_data = {
    "team": {"name": "Test Team", "type": "hierarchical"},
    "coordinator": {...},  # Your config
    "teams": [...]
}

validation = client.validate_config(config_data, "hierarchical")
if validation['valid']:
    print("Configuration is valid!")
else:
    print(f"Errors: {validation['errors']}")

# Upload configuration file
with open("my_config.yml", "rb") as f:
    upload_result = client.upload_config(f.read(), "my_config.yml")
    print(f"Upload successful: {upload_result['file_id']}")
```

### Agent Library Operations

```python
# Search agents by capability
agents = client.search_agents(
    capabilities=["web_search", "research"],
    role="worker",
    limit=10
)

print(f"Found {len(agents['agents'])} matching agents")

# Get team suggestions
suggestions = client.get_team_suggestions(
    task_description="Research and write a comprehensive report on AI ethics"
)

for suggestion in suggestions['suggestions']:
    print(f"Suggested team: {suggestion['reasoning']}")
```

## 📁 Hierarchical Team Configuration

### Team Configuration Structure

```yaml
# Team Information
team:
  name: "Your Team Name"
  description: "Team description"
  version: "1.0.0"
  type: "hierarchical"

# Top-level Coordinator
coordinator:
  name: "Team Coordinator"
  description: "Coordinates between teams"
  llm:
    provider: "openai"
    model: "gpt-4o-mini"
    temperature: 0.3
    max_tokens: 2000
    api_key_env: "OPENAI_API_KEY"
  
  routing:
    strategy: "hybrid"  # keyword_based, llm_based, rule_based, hybrid
    fallback_team: "default_team"
    confidence_threshold: 0.8

# Teams Configuration
teams:
  - name: "specialist_team"
    description: "Team description"
    
    supervisor:
      name: "Team Supervisor"
      llm:
        provider: "openai"
        model: "gpt-4o-mini"
        temperature: 0.2
      routing:
        strategy: "capability_based"
        fallback_worker: "default_worker"
    
    workers:
      - name: "specialist_worker"
        role: "specialist"
        config_file: "configs/examples/specialist_agent.yml"
        description: "Specialized worker agent"
        capabilities: 
          - "specialized_task"
          - "domain_expertise"
        priority: 1

# Memory Configuration (Hierarchical)
memory:
  enabled: true
  provider: "langmem"
  levels:
    coordinator:
      enabled: true
      types: {semantic: true, episodic: true, procedural: true}
    team:
      enabled: true
      shared_across_workers: true
    worker:
      enabled: true
      individual: false

# Coordination Settings
coordination:
  cross_team_communication: true
  team_dependencies: 
    - "team_b depends on team_a"
  task_flow:
    type: "pipeline"  # sequential, parallel, conditional, pipeline
    max_parallel_tasks: 3
    timeout_per_task: 300

# Performance Monitoring
performance:
  monitoring:
    enabled: true
    metrics:
      - "response_time"
      - "task_success_rate"
      - "worker_utilization"
      - "decision_accuracy"
```

## 📚 Pre-built Team Templates

### 🔬 Research Pipeline Team
- **Flow**: Browser Agent → Research Analyst → Writer Agent
- **Use case**: Comprehensive research with web search, analysis, and content creation
- **Configuration**: `configs/examples/hierarchical/research_pipeline_team.yml`

### 💻 Development Team
- **Flow**: Requirements → Development → QA
- **Use case**: Software development with analysis, coding, and testing
- **Configuration**: `configs/examples/hierarchical/development_team.yml`

### 🎧 Customer Service Team
- **Flow**: Triage → Specialist → Escalation
- **Use case**: Customer support with routing and escalation handling
- **Configuration**: `configs/examples/hierarchical/customer_service_team.yml`

### ✍️ Content Creation Team
- **Flow**: Research → Writing → Editorial
- **Use case**: Content creation with research, writing, and editing
- **Configuration**: `configs/examples/hierarchical/content_creation_team.yml`

## 🛠️ Advanced Features

### Enhanced Routing for Hierarchical Teams

```python
from src.hierarchical.enhanced_routing import EnhancedRoutingEngine, RoutingStrategy, AgentCapability

# Create routing engine
routing_engine = EnhancedRoutingEngine(
    llm=your_llm,
    default_strategy=RoutingStrategy.HYBRID
)

# Register agents
web_agent = AgentCapability(
    agent_id="web_searcher",
    capabilities=["web_search", "information_gathering"],
    specialization_keywords=["search", "web", "internet"],
    priority=1
)
routing_engine.register_agent(web_agent)

# Route a task
decision = routing_engine.route_task(
    task_description="Find information about AI developments",
    available_agents=["web_searcher", "analyst", "writer"],
    strategy=RoutingStrategy.HYBRID
)

print(f"Selected agent: {decision.target}")
print(f"Confidence: {decision.confidence}")
print(f"Reasoning: {decision.reasoning}")
```

### Optimization and Feedback

```python
from src.optimization.prompt_optimizer import OptimizationMetric

# Record feedback for optimization
team.prompt_optimizer.record_feedback(
    prompt_type="system_prompt",
    variant_id="variant_1",
    metrics={
        OptimizationMetric.USER_SATISFACTION: 0.9,
        OptimizationMetric.ACCURACY: 0.85
    }
)

# Run optimization
optimized_prompts = team.prompt_optimizer.optimize_prompts()
```

## 🔄 Task Flow Types

### Sequential Flow
Tasks are processed one after another through the team hierarchy.

```yaml
coordination:
  task_flow:
    type: "sequential"
    timeout_per_task: 300
```

### Parallel Flow
Multiple tasks can be processed simultaneously across teams.

```yaml
coordination:
  task_flow:
    type: "parallel"
    max_parallel_tasks: 5
```

### Pipeline Flow
Tasks flow through teams in a predefined pipeline sequence.

```yaml
coordination:
  task_flow:
    type: "pipeline"
    max_parallel_tasks: 3
```

### Conditional Flow
Task routing depends on specific conditions and results.

```yaml
coordination:
  task_flow:
    type: "conditional"
    timeout_per_task: 300
```

## 🎯 Use Cases

### Research & Analysis
- **Academic Research**: Multi-step research with web search, analysis, and report generation
- **Market Research**: Comprehensive market analysis with data gathering and insights
- **Competitive Intelligence**: Automated competitor analysis and reporting

### Software Development
- **Full-stack Development**: Requirements analysis, development, and testing
- **Code Review**: Automated code analysis, review, and improvement suggestions
- **DevOps**: Deployment, monitoring, and maintenance workflows

### Content Creation
- **Content Marketing**: Research, writing, editing, and SEO optimization
- **Technical Documentation**: API documentation, user guides, and tutorials
- **Social Media**: Content creation, scheduling, and engagement analysis

### Customer Support
- **Multi-tier Support**: Triage, specialized support, and escalation handling
- **Help Desk**: Automated ticket routing and resolution
- **Customer Success**: Proactive customer engagement and support

## 📊 Performance Monitoring

### Key Metrics Tracked
- **Response Time**: Average time for task completion
- **Success Rate**: Percentage of successfully completed tasks
- **Agent Utilization**: Workload distribution across agents
- **Routing Accuracy**: Effectiveness of routing decisions
- **Team Coordination**: Cross-team collaboration efficiency

### Dashboard Features
- Real-time charts and visualizations
- Agent performance comparison
- Team analytics with workload distribution
- Alert system with configurable thresholds
- Historical trend analysis
- Detailed performance reports

## 🧪 Testing

```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py --unit      # Unit tests only
python run_tests.py --integration  # Integration tests only
python run_tests.py --lint      # Code quality checks
python run_tests.py --quick     # Quick smoke test

# With coverage report
python run_tests.py --unit --coverage

# For detailed output
python run_tests.py --all --verbose
```

## 🏗️ Architecture

```
src/
├── hierarchical/
│   ├── hierarchical_agent.py    # Hierarchical team management
│   ├── enhanced_routing.py      # Advanced routing algorithms
│   ├── enhanced_supervisor.py   # Supervisor agent implementation
│   ├── supervisor.py            # Basic supervisor functionality
│   ├── team_coordinator.py      # Team coordination logic
│   └── worker_agent.py          # Worker agent implementation
├── memory/
│   └── memory_manager.py        # LangMem integration
├── optimization/
│   ├── prompt_optimizer.py      # Prompt optimization
│   └── feedback_collector.py    # Feedback collection
├── tools/
│   └── tool_registry.py         # Tool management
├── monitoring/
│   └── performance_dashboard.py # Performance monitoring
└── validation/
    └── hierarchy_validator.py   # Configuration validation

api/
├── server.py                    # FastAPI application
├── routes/                      # API endpoints
├── services/                    # Business logic
├── models/                      # Pydantic models
└── middleware/                  # Error handling

ui/
├── api_client.py                        # Python API client
├── hierarchical_web_ui_api.py           # Basic Streamlit UI
└── hierarchical_web_ui_api_complete.py  # Complete Streamlit UI (Default)
```

## 🚨 Troubleshooting

### Common Issues

#### API Server Won't Start
```bash
# Check if port 8000 is in use
lsof -i :8000  # On Unix/Linux/macOS
netstat -ano | findstr :8000  # On Windows

# Try different port
API_PORT=8001 python run_api_server.py
```

#### UI Can't Connect to API
```bash
# Check API server is running
curl http://localhost:8000/health

# Verify API base URL
echo $API_BASE_URL

# Test with different base URL
API_BASE_URL=http://localhost:8001 python run_hierarchical_ui_api.py
```

#### Switching Between UI Versions
```bash
# Use Complete UI (Default - includes Simple Team Builder)
python run_hierarchical_ui_api.py
# or directly
streamlit run hierarchical_web_ui_api_complete.py

# Use Basic UI (Lightweight version)
streamlit run hierarchical_web_ui_api.py
```

#### Configuration Validation Errors
```bash
# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('your_config.yml'))"

# Validate via API
curl -X POST "http://localhost:8000/api/v1/configs/validate" \
     -H "Content-Type: application/json" \
     -d @your_config.json
```

#### API Key Issues
```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $ANTHROPIC_API_KEY

# Verify API server has access
curl http://localhost:8000/health
```

## 🤝 Contributing

We welcome contributions to hierarchical agent teams! Please feel free to:

- Submit bug reports and feature requests
- Contribute new team templates
- Improve routing algorithms
- Enhance the API and web UI
- Add new monitoring capabilities

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

## 📞 Support

For issues and questions:
- Check the [examples](configs/examples/hierarchical/) directory
- Review the [test files](tests/) for usage patterns
- Create an issue on GitHub
- Check the API documentation at http://localhost:8000/docs

## 🔮 Roadmap

### Completed ✅
- [x] Hierarchical agent teams with advanced coordination
- [x] **FastAPI backend with comprehensive REST APIs**
- [x] **API-based Streamlit UI with full feature parity**
- [x] Advanced routing algorithms and strategies
- [x] Performance monitoring dashboard
- [x] Memory management integration
- [x] Configuration validation and optimization
- [x] **Real-time execution tracking**
- [x] **Comprehensive API documentation**

### Planned 🚧
- [ ] WebSocket support for real-time updates
- [ ] API authentication and authorization
- [ ] Database persistence (PostgreSQL/MongoDB)
- [ ] Additional LLM provider support (Ollama, Cohere)
- [ ] Advanced memory backends (vector databases)
- [ ] Auto-scaling and load balancing
- [ ] Integration hub and template marketplace
- [ ] Advanced analytics and ML-powered insights
- [ ] Plugin system for custom components
- [ ] Docker containerization
- [ ] Kubernetes deployment templates

---

**Built with ❤️ for the AI agent community**

Build powerful hierarchical agent teams with intelligent coordination, advanced routing, and comprehensive monitoring. Start building your configurable hierarchical agent systems today with our **production-ready API architecture**!

## 🔗 Quick Links

- **Start API Server**: `python run_api_server.py`
- **Start Web UI**: `python run_hierarchical_ui_api.py`
- **API Documentation**: http://localhost:8000/docs
- **Web Interface**: http://localhost:8501
- **Health Check**: http://localhost:8000/health