# API Quick Start Guide

## 🚀 Get Started in 5 Minutes

This guide will help you get up and running with the Hierarchical Agent System API quickly.

## Prerequisites

- Python 3.8+
- API keys for at least one LLM provider (OpenAI, Anthropic, Google, or Groq)
- Basic understanding of REST APIs

## Step 1: Setup and Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-org/hierarchical-agents.git
   cd hierarchical-agents
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env and add your API keys
   ```

4. **Start the API server:**
   ```bash
   python run_api_server.py
   ```

5. **Verify the server is running:**
   ```bash
   curl http://localhost:8000/health
   ```

## Step 2: Your First Team

### Create a Simple Research Team

```bash
curl -X POST http://localhost:8000/api/v1/teams/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Quick Research Team",
    "description": "A simple team for research tasks",
    "config_data": {
      "team": {
        "name": "Quick Research Team",
        "description": "A simple team for research tasks",
        "version": "1.0.0",
        "type": "hierarchical"
      },
      "coordinator": {
        "name": "Research Coordinator",
        "description": "Routes research tasks to appropriate teams",
        "llm": {
          "provider": "openai",
          "model": "gpt-4o-mini",
          "temperature": 0.3,
          "api_key_env": "OPENAI_API_KEY"
        },
        "prompts": {
          "system_prompt": {
            "template": "You are a coordinator that routes tasks to the most appropriate team member based on their capabilities."
          },
          "decision_prompt": {
            "template": "Route this task: {user_input}"
          }
        }
      },
      "teams": [
        {
          "name": "Research Team",
          "description": "Team specialized in web research",
          "supervisor": {
            "name": "Research Supervisor",
            "description": "Supervises research tasks",
            "config_file": "configs/examples/research_supervisor.yml"
          },
          "workers": [
            {
              "name": "Web Researcher",
              "role": "worker", 
              "description": "Performs web research tasks",
              "capabilities": ["web_search", "information_gathering"],
              "config_file": "configs/examples/web_browser_agent.yml"
            }
          ]
        }
      ]
    }
  }'
```

**Expected Response:**
```json
{
  "team_id": "team_abc123",
  "name": "Quick Research Team",
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Step 3: Execute Your First Task

```bash
curl -X POST http://localhost:8000/api/v1/executions/team_abc123/execute \
  -H "Content-Type: application/json" \
  -d '{
    "input_text": "Research the latest trends in artificial intelligence for 2024",
    "parameters": {
      "format": "bullet_points",
      "target_audience": "business executives"
    },
    "timeout_seconds": 120
  }'
```

**Expected Response:**
```json
{
  "execution_id": "exec_xyz789",
  "team_id": "team_abc123", 
  "status": "running",
  "started_at": "2024-01-15T10:30:00Z"
}
```

## Step 4: Check Results

```bash
curl http://localhost:8000/api/v1/executions/exec_xyz789
```

**When completed, you'll get:**
```json
{
  "execution_id": "exec_xyz789",
  "status": "completed",
  "result": {
    "success": true,
    "output": "# AI Trends 2024\n\n• Generative AI integration in business processes\n• Advanced multimodal AI systems\n• AI governance and regulation developments\n..."
  }
}
```

## Common Use Cases

### 1. Content Creation Team

```bash
curl -X POST http://localhost:8000/api/v1/teams/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Content Creation Team",
    "config": {
      "coordinator": {
        "routing_strategy": "capability_based"
      },
      "teams": [
        {
          "name": "Research Team",
          "supervisor": {
            "name": "Research Lead"
          },
          "workers": [
            {"name": "Researcher", "capabilities": ["research", "fact_checking"]}
          ]
        },
        {
          "name": "Writing Team", 
          "supervisor": {
            "name": "Writing Lead"
          },
          "workers": [
            {"name": "Content Writer", "capabilities": ["writing", "editing"]}
          ]
        }
      ]
    }
  }'
```

### 2. Customer Support Team

```bash
curl -X POST http://localhost:8000/api/v1/teams/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Customer Support Team",
    "config": {
      "coordinator": {
        "routing_strategy": "capability_based"
      },
      "teams": [
        {
          "name": "Technical Support",
          "supervisor": {"name": "Tech Lead"},
          "workers": [
            {"name": "Technical Specialist", "capabilities": ["technical_support", "troubleshooting"]}
          ]
        },
        {
          "name": "General Support",
          "supervisor": {"name": "Support Lead"},
          "workers": [
            {"name": "Support Agent", "capabilities": ["customer_service", "general_inquiry"]}
          ]
        }
      ]
    }
  }'
```

## Using Templates

### List Available Templates

```bash
curl http://localhost:8000/api/v1/configs/templates
```

### Create Team from Template

```bash
# First, get template details
curl http://localhost:8000/api/v1/configs/templates/research_pipeline

# Then create team with the template config
curl -X POST http://localhost:8000/api/v1/teams/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Research Team",
    "config": {
      // ... paste template config here
    }
  }'
```

## Agent Discovery

### Search for Agents

```bash
# Find research-capable agents
curl -X POST http://localhost:8000/api/v1/agents/search \
  -H "Content-Type: application/json" \
  -d '{
    "capabilities": ["research", "analysis"],
    "limit": 10
  }'

# Find agents by role
curl "http://localhost:8000/api/v1/agents/?role=worker&limit=20"
```

### Get Team Suggestions

```bash
curl -X POST http://localhost:8000/api/v1/agents/suggest-team \
  -H "Content-Type: application/json" \
  -d '{
    "requirements": {
      "domain": "research",
      "team_size": 5,
      "required_capabilities": ["research", "analysis", "writing"]
    }
  }'
```

## Configuration Validation

### Validate Before Creating

```bash
curl -X POST http://localhost:8000/api/v1/configs/validate \
  -H "Content-Type: application/json" \
  -d '{
    "config": {
      // ... your team config
    },
    "validation_level": "strict",
    "optimize": true
  }'
```

## Python SDK Example

For easier integration, use the Python SDK:

```python
import asyncio
from hierarchical_agents import HierarchicalAgentClient

async def main():
    # Initialize client
    client = HierarchicalAgentClient("http://localhost:8000")
    
    # Create a team
    team = await client.teams.create({
        "name": "SDK Test Team",
        "config": {
            "coordinator": {"routing_strategy": "capability_based"},
            "teams": [{
                "name": "Test Team",
                "supervisor": {"name": "Test Supervisor"},
                "workers": [{
                    "name": "Test Worker",
                    "capabilities": ["general"]
                }]
            }]
        }
    })
    
    print(f"Created team: {team.team_id}")
    
    # Execute a task
    execution = await client.executions.execute(
        team_id=team.team_id,
        task="Explain quantum computing in simple terms"
    )
    
    print(f"Execution ID: {execution.execution_id}")
    
    # Wait for completion
    result = await client.executions.wait_for_completion(execution.execution_id)
    print(f"Result: {result.output}")

# Run the example
asyncio.run(main())
```

## Monitoring and Debugging

### Check Team Status

```bash
curl http://localhost:8000/api/v1/teams/team_abc123/status
```

### View Execution Logs

```bash
curl http://localhost:8000/api/v1/executions/exec_xyz789/logs
```

### List All Executions

```bash
curl "http://localhost:8000/api/v1/executions/?team_id=team_abc123&limit=10"
```

## Error Handling

### Common Error Responses

```bash
# 400 Bad Request
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid team configuration",
    "details": {"field": "workers", "issue": "At least one worker required"}
  }
}

# 404 Not Found  
{
  "error": {
    "code": "TEAM_NOT_FOUND",
    "message": "Team with ID 'team_abc123' not found"
  }
}

# 429 Rate Limited
{
  "error": {
    "code": "RATE_LIMITED", 
    "message": "Too many requests. Please try again later.",
    "retry_after": 60
  }
}
```

### Handling Errors in Python

```python
import requests

try:
    response = requests.post("http://localhost:8000/api/v1/teams/", json=team_config)
    response.raise_for_status()
    team = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 400:
        error_detail = e.response.json()["error"]
        print(f"Validation error: {error_detail['message']}")
    elif e.response.status_code == 429:
        print("Rate limited. Please wait and retry.")
    else:
        print(f"API error: {e}")
```

## Best Practices

### 1. Team Design
- **Start simple**: Begin with basic configurations and gradually add complexity
- **Capability focus**: Design teams around specific capabilities rather than generic roles
- **Clear prompts**: Write specific, clear prompts for coordinators and supervisors

### 2. Task Execution
- **Set timeouts**: Always specify reasonable timeout values
- **Context matters**: Provide rich context for better results
- **Monitor progress**: Use the status endpoint to track long-running tasks

### 3. Performance
- **Reuse teams**: Create teams once and reuse them for multiple tasks
- **Batch operations**: Group related tasks when possible
- **Cache results**: Implement caching for frequently used configurations

### 4. Error Handling
- **Implement retries**: Add exponential backoff for transient failures
- **Validate configs**: Always validate configurations before deployment
- **Monitor logs**: Regularly check execution logs for issues

## Next Steps

1. **Explore the Web UI**: Launch `python run_hierarchical_ui_api.py` for a graphical interface
2. **Read the full documentation**: Check out `API_DOCUMENTATION.md` for comprehensive details
3. **Join the community**: Connect with other developers using the system
4. **Contribute**: Help improve the system by contributing to the open-source project

## Support

- **Documentation**: Full API docs at http://localhost:8000/docs
- **GitHub Issues**: Report bugs and request features
- **Community Discord**: Get help from other developers
- **Email Support**: contact@hierarchical-agents.com

## Quick Reference

### Essential Endpoints
```
POST /api/v1/teams/                    # Create team
GET  /api/v1/teams/{id}               # Get team details
POST /api/v1/executions/{id}/execute  # Execute task
GET  /api/v1/executions/{id}          # Get results
POST /api/v1/agents/search            # Find agents
POST /api/v1/configs/validate         # Validate config
```

### Environment Variables
```bash
API_HOST=0.0.0.0
API_PORT=8000
OPENAI_API_KEY=your-key
ANTHROPIC_API_KEY=your-key
```

### Health Check
```bash
curl http://localhost:8000/health
```

Happy building! 🚀