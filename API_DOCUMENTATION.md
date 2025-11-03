# Hierarchical Agent System API Documentation

## Overview

The Hierarchical Agent System API provides comprehensive REST endpoints for managing hierarchical agent teams, configurations, and task executions. Built with FastAPI, it offers automatic OpenAPI documentation, type validation, and high-performance async operations.

## Table of Contents

- [Getting Started](#getting-started)
- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [Teams Management](#teams-management)
  - [Agent Library](#agent-library)
  - [Configuration Management](#configuration-management)
  - [Task Execution](#task-execution)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)
- [SDK Usage](#sdk-usage)

## Getting Started

### Base URL
```
http://localhost:8000
```

### Quick Start
1. Start the API server:
   ```bash
   python run_api_server.py
   ```

2. Access interactive documentation:
   - **Swagger UI**: http://localhost:8000/docs
   - **ReDoc**: http://localhost:8000/redoc

3. Check API health:
   ```bash
   curl http://localhost:8000/health
   ```

### Environment Setup
Required environment variables:
```bash
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000

# LLM API Keys (at least one required)
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key
GROQ_API_KEY=your-groq-key
```

## Authentication

Currently, the API operates without authentication for development purposes. In production deployments:

- **API Keys**: Include `X-API-Key` header
- **JWT Tokens**: Include `Authorization: Bearer <token>` header
- **Rate Limiting**: Applied per API key/IP address

## API Endpoints

### Teams Management

#### Create Team
```http
POST /api/v1/teams/
```

Create a new hierarchical agent team.

**Request Body:**
```json
{
  "name": "Research Team",
  "description": "Specialized research and analysis team",
  "config_data": {
    "team": {
      "name": "Research Team",
      "description": "Specialized research and analysis team",
      "version": "1.0.0",
      "type": "hierarchical"
    },
    "coordinator": {
      "name": "Research Coordinator",
      "description": "Coordinates research tasks across specialized teams",
      "llm": {
        "provider": "openai",
        "model": "gpt-4o-mini",
        "temperature": 0.3,
        "api_key_env": "OPENAI_API_KEY"
      },
      "prompts": {
        "system_prompt": {
          "template": "You are a coordinator managing specialized research teams..."
        },
        "decision_prompt": {
          "template": "Route this research task: {user_input}"
        }
      }
    },
    "teams": [
      {
        "name": "Research Team",
        "description": "Team specialized in research and analysis",
        "supervisor": {
          "name": "Research Supervisor",
          "description": "Supervises research workers",
          "config_file": "configs/examples/research_supervisor.yml"
        },
        "workers": [
          {
            "name": "Senior Researcher",
            "role": "worker",
            "description": "Expert in research and analysis",
            "capabilities": ["research", "analysis"],
            "config_file": "configs/examples/web_browser_agent.yml"
          }
        ]
      }
    ]
  }
}
```

**Response:**
```json
{
  "team_id": "team_123",
  "name": "Research Team", 
  "description": "Specialized research and analysis team",
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "config": { ... },
  "performance_metrics": {
    "total_executions": 0,
    "success_rate": 0.0,
    "avg_response_time": 0.0
  }
}
```

#### List Teams
```http
GET /api/v1/teams/?limit=10&offset=0
```

**Query Parameters:**
- `limit` (int, optional): Maximum number of teams to return (default: 100)
- `offset` (int, optional): Number of teams to skip (default: 0)

**Response:**
```json
{
  "teams": [
    {
      "team_id": "team_123",
      "name": "Research Team",
      "description": "Specialized research and analysis team",
      "status": "active",
      "created_at": "2024-01-15T10:30:00Z",
      "performance_metrics": {
        "total_executions": 42,
        "success_rate": 0.95,
        "avg_response_time": 2.3
      }
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}
```

#### Get Team Details
```http
GET /api/v1/teams/{team_id}
```

#### Update Team
```http
PUT /api/v1/teams/{team_id}
```

#### Delete Team
```http
DELETE /api/v1/teams/{team_id}
```

#### Get Team Status
```http
GET /api/v1/teams/{team_id}/status
```

### Agent Library

#### Search Agents
```http
POST /api/v1/agents/search
```

Search available agents by role, capabilities, or domain.

**Request Body:**
```json
{
  "query": "research",
  "role": "worker",
  "capabilities": ["research", "analysis"],
  "domain": "academic",
  "limit": 20,
  "offset": 0
}
```

**Response:**
```json
{
  "agents": [
    {
      "id": "agent_456",
      "name": "Senior Researcher",
      "description": "Expert in academic research and data analysis",
      "primary_role": "worker",
      "secondary_roles": ["analyst"],
      "capabilities": [
        {
          "name": "research",
          "description": "Academic and web research",
          "proficiency": 0.9
        }
      ],
      "tools": ["web_search", "calculator", "file_reader"],
      "specializations": ["academic", "scientific"],
      "compatibility_score": 0.87,
      "file_path": "configs/agents/senior_researcher.yml"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

#### List All Agents
```http
GET /api/v1/agents/?role=worker&limit=50
```

#### Get Agent Details
```http
GET /api/v1/agents/{agent_id}
```

#### Check Agent Compatibility
```http
POST /api/v1/agents/compatibility
```

**Request Body:**
```json
{
  "agent_ids": ["agent_456", "agent_789", "agent_101"],
  "team_context": "research_team"
}
```

**Response:**
```json
{
  "compatibility_matrix": {
    "agent_456": {
      "agent_789": 0.85,
      "agent_101": 0.72
    },
    "agent_789": {
      "agent_456": 0.85,
      "agent_101": 0.68
    }
  },
  "recommendations": [
    "agent_456 and agent_789 have high compatibility for research tasks",
    "Consider pairing agent_456 with agent_101 for diverse perspectives"
  ]
}
```

#### Get Agent Statistics
```http
GET /api/v1/agents/stats
```

#### Suggest Team Composition
```http
POST /api/v1/agents/suggest-team
```

### Configuration Management

#### Validate Configuration
```http
POST /api/v1/configs/validate
```

Validate a hierarchical team configuration.

**Request Body:**
```json
{
  "config": {
    "coordinator": { ... },
    "teams": [ ... ]
  },
  "validation_level": "strict"
}
```

**Response:**
```json
{
  "valid": true,
  "validation_result": {
    "overall_score": 0.92,
    "issues": [],
    "warnings": [
      "Consider adding memory configuration for better performance"
    ],
    "recommendations": [
      "Add more diverse capabilities to research team",
      "Configure retry logic for supervisor agents"
    ],
    "optimized_config": { ... }
  }
}
```

#### Upload Configuration File
```http
POST /api/v1/configs/upload
```

#### List Templates
```http
GET /api/v1/configs/templates
```

**Response:**
```json
{
  "templates": [
    {
      "id": "template_123",
      "name": "Research Pipeline Team",
      "description": "Complete research workflow with coordinator and specialized teams",
      "category": "research",
      "difficulty": "intermediate",
      "file_path": "configs/examples/hierarchical/research_pipeline_team.yml",
      "created_at": "2024-01-15T10:30:00Z",
      "usage_count": 42,
      "rating": 4.7
    }
  ],
  "total": 1
}
```

#### Get Template Details
```http
GET /api/v1/configs/templates/{template_id}
```

#### Export Configuration
```http
POST /api/v1/configs/export
```

### Task Execution

#### Execute Task
```http
POST /api/v1/executions/{team_id}/execute
```

Execute a task using a hierarchical team.

**Request Body:**
```json
{
  "input_text": "Research the latest developments in quantum computing and provide a comprehensive report",
  "parameters": {
    "priority": "high",
    "deadline": "2024-01-20T17:00:00Z",
    "format": "detailed_report"
  },
  "timeout_seconds": 300
}
```

**Response:**
```json
{
  "execution_id": "exec_789",
  "team_id": "team_123",
  "status": "running",
  "started_at": "2024-01-15T10:30:00Z",
  "estimated_completion": "2024-01-15T10:35:00Z",
  "progress": {
    "percentage": 25,
    "current_step": "Research phase",
    "steps_completed": 1,
    "total_steps": 4
  }
}
```

#### Get Execution Status
```http
GET /api/v1/executions/{execution_id}
```

**Response:**
```json
{
  "execution_id": "exec_789",
  "team_id": "team_123",
  "status": "completed",
  "started_at": "2024-01-15T10:30:00Z",
  "completed_at": "2024-01-15T10:34:30Z",
  "duration_seconds": 270,
  "result": {
    "success": true,
    "output": "# Quantum Computing Developments Report\\n\\n## Executive Summary\\n...",
    "metadata": {
      "tokens_used": 1250,
      "agents_involved": ["coordinator", "research_supervisor", "senior_researcher"],
      "cost_estimate": "$0.025"
    }
  },
  "performance_metrics": {
    "response_time": 2.3,
    "accuracy_score": 0.94,
    "team_coordination_score": 0.87
  }
}
```

#### List Executions
```http
GET /api/v1/executions/?team_id=team_123&status=completed&limit=20
```

#### Cancel Execution
```http
POST /api/v1/executions/{execution_id}/cancel
```

#### Get Execution Logs
```http
GET /api/v1/executions/{execution_id}/logs
```

## Data Models

### Core Models

#### TeamConfiguration
```typescript
interface TeamConfiguration {
  coordinator: {
    routing_strategy: "capability_based" | "llm_based" | "rule_based";
    prompts: {
      system_prompt: {
        template: string;
        variables?: Record<string, any>;
      };
    };
    llm?: {
      provider: "openai" | "anthropic" | "google" | "groq";
      model: string;
      temperature?: number;
    };
  };
  teams: Array<{
    name: string;
    supervisor: {
      name: string;
      prompts: {
        system_prompt: {
          template: string;
          variables?: Record<string, any>;
        };
      };
      llm?: LLMConfig;
    };
    workers: Array<{
      name: string;
      capabilities: string[];
      tools: string[];
      specializations?: string[];
      config_file?: string;
      config_data?: WorkerConfig;
    }>;
  }>;
  performance?: {
    monitoring_enabled: boolean;
    alerts?: Array<AlertConfig>;
  };
}
```

#### Agent
```typescript
interface Agent {
  id: string;
  name: string;
  description: string;
  primary_role: "coordinator" | "supervisor" | "worker" | "specialist";
  secondary_roles?: string[];
  capabilities: Array<{
    name: string;
    description: string;
    proficiency: number; // 0.0 to 1.0
  }>;
  tools: string[];
  specializations: string[];
  compatibility_score?: number;
  file_path: string;
  can_coordinate?: boolean;
  can_supervise?: boolean;
  team_size_limit?: number;
}
```

#### ExecutionResult
```typescript
interface ExecutionResult {
  execution_id: string;
  team_id: string;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  started_at: string; // ISO 8601
  completed_at?: string;
  duration_seconds?: number;
  result?: {
    success: boolean;
    output: string;
    metadata: {
      tokens_used: number;
      agents_involved: string[];
      cost_estimate: string;
    };
  };
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  performance_metrics: {
    response_time: number;
    accuracy_score: number;
    team_coordination_score: number;
  };
}
```

## Error Handling

The API uses standard HTTP status codes and provides detailed error information:

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Configuration validation failed",
    "details": {
      "field": "teams[0].workers",
      "issue": "At least one worker is required per team"
    },
    "timestamp": "2024-01-15T10:30:00Z",
    "request_id": "req_123"
  }
}
```

### Common Error Codes
- `400 BAD_REQUEST`: Invalid request data
- `401 UNAUTHORIZED`: Authentication required
- `403 FORBIDDEN`: Insufficient permissions
- `404 NOT_FOUND`: Resource not found
- `409 CONFLICT`: Resource conflict (e.g., duplicate team name)
- `422 VALIDATION_ERROR`: Request data validation failed
- `429 RATE_LIMITED`: Too many requests
- `500 INTERNAL_ERROR`: Server error
- `503 SERVICE_UNAVAILABLE`: Service temporarily unavailable

## Rate Limiting

API endpoints are rate-limited to ensure fair usage:

- **Default**: 100 requests per minute per IP
- **Authenticated**: 1000 requests per minute per API key
- **Execution endpoints**: 10 concurrent executions per team

Rate limit headers:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1705328400
```

## Examples

### Complete Team Creation and Execution Workflow

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# 1. Create a team
team_config = {
    "name": "Content Creation Team",
    "description": "Team specialized in content research and writing",
    "config": {
        "coordinator": {
            "routing_strategy": "capability_based",
            "prompts": {
                "system_prompt": {
                    "template": "You coordinate between research and writing teams..."
                }
            }
        },
        "teams": [
            {
                "name": "Research Team",
                "supervisor": {
                    "name": "Research Supervisor",
                    "prompts": {
                        "system_prompt": {
                            "template": "You manage research tasks..."
                        }
                    }
                },
                "workers": [
                    {
                        "name": "Web Researcher",
                        "capabilities": ["web_search", "data_analysis"],
                        "tools": ["web_search", "calculator"]
                    }
                ]
            }
        ]
    }
}

response = requests.post(f"{BASE_URL}/api/v1/teams/", json=team_config)
team = response.json()
team_id = team["team_id"]

print(f"Created team: {team_id}")

# 2. Execute a task
task_request = {
    "task": "Research and write a comprehensive article about renewable energy trends in 2024",
    "context": {
        "target_audience": "general public",
        "word_count": 1500,
        "tone": "informative yet engaging"
    },
    "execution_options": {
        "timeout_seconds": 600,
        "max_retries": 2
    }
}

response = requests.post(f"{BASE_URL}/api/v1/executions/{team_id}/execute", json=task_request)
execution = response.json()
execution_id = execution["execution_id"]

print(f"Started execution: {execution_id}")

# 3. Monitor execution status
import time

while True:
    response = requests.get(f"{BASE_URL}/api/v1/executions/{execution_id}")
    execution_status = response.json()
    
    status = execution_status["status"]
    print(f"Status: {status}")
    
    if status in ["completed", "failed", "cancelled"]:
        break
    
    time.sleep(5)

# 4. Get results
if execution_status["status"] == "completed":
    result = execution_status["result"]
    print("Task completed successfully!")
    print(f"Output: {result['output'][:200]}...")
    print(f"Performance: {execution_status['performance_metrics']}")
else:
    print(f"Task failed: {execution_status.get('error', {}).get('message')}")
```

### Agent Search and Team Suggestion

```python
# Search for research-capable agents
search_request = {
    "query": "research analysis",
    "capabilities": ["research", "data_analysis"],
    "limit": 10
}

response = requests.post(f"{BASE_URL}/api/v1/agents/search", json=search_request)
agents = response.json()["agents"]

print(f"Found {len(agents)} matching agents")

# Get team composition suggestions
suggestion_request = {
    "requirements": {
        "domain": "research",
        "team_size": 5,
        "required_capabilities": ["research", "analysis", "writing"],
        "budget_level": "standard"
    }
}

response = requests.post(f"{BASE_URL}/api/v1/agents/suggest-team", json=suggestion_request)
suggestions = response.json()

print("Suggested team composition:")
for suggestion in suggestions["suggestions"]:
    print(f"- {suggestion['role']}: {suggestion['agent_name']}")
```

## SDK Usage

For production applications, consider using the official Python SDK:

```bash
pip install hierarchical-agents-sdk
```

```python
from hierarchical_agents import HierarchicalAgentClient

# Initialize client
client = HierarchicalAgentClient(
    base_url="http://localhost:8000",
    api_key="your-api-key"  # for production
)

# Create team from template
team = await client.teams.create_from_template(
    template_id="research_pipeline",
    name="My Research Team",
    customizations={
        "llm_provider": "openai",
        "model": "gpt-4o"
    }
)

# Execute task with streaming
async for update in client.executions.execute_streaming(
    team_id=team.team_id,
    task="Analyze market trends in renewable energy"
):
    print(f"Progress: {update.progress}% - {update.status}")

# Get final result
result = await client.executions.get_result(update.execution_id)
print(result.output)
```

## Support and Resources

- **API Documentation**: http://localhost:8000/docs
- **GitHub Repository**: https://github.com/your-org/hierarchical-agents
- **Issue Tracker**: https://github.com/your-org/hierarchical-agents/issues
- **Community Discord**: https://discord.gg/hierarchical-agents
- **Email Support**: support@hierarchical-agents.com

## Changelog

### v1.0.0 (2024-01-15)
- Initial API release
- Core team management endpoints
- Agent library and search functionality
- Configuration validation and templates
- Task execution with real-time monitoring
- Comprehensive error handling and rate limiting