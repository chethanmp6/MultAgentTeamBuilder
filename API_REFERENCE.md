# API Reference - Hierarchical Agent System

## Endpoint Reference

### Teams API (`/api/v1/teams`)

#### `POST /api/v1/teams/`
Create a new hierarchical agent team.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `name` | string | Yes | Unique team name |
| `description` | string | No | Team description |
| `config` | TeamConfiguration | Yes | Team configuration object |

**Request Schema:**
```json
{
  "type": "object",
  "required": ["name", "config"],
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "pattern": "^[a-zA-Z0-9_\\s-]+$"
    },
    "description": {
      "type": "string",
      "maxLength": 500
    },
    "config": {
      "$ref": "#/definitions/TeamConfiguration"
    }
  }
}
```

**Response Codes:**
- `201`: Team created successfully
- `400`: Invalid configuration
- `409`: Team name already exists
- `422`: Validation error

---

#### `GET /api/v1/teams/`
List all teams with pagination.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `limit` | integer | 100 | Max results per page (1-1000) |
| `offset` | integer | 0 | Number of results to skip |
| `status` | string | - | Filter by status (active, inactive, error) |
| `search` | string | - | Search in team names and descriptions |

**Response Schema:**
```json
{
  "type": "object",
  "properties": {
    "teams": {
      "type": "array",
      "items": {"$ref": "#/definitions/TeamSummary"}
    },
    "total": {"type": "integer"},
    "limit": {"type": "integer"},
    "offset": {"type": "integer"}
  }
}
```

---

#### `GET /api/v1/teams/{team_id}`
Get detailed information about a specific team.

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `team_id` | string | Yes | Unique team identifier |

**Response Codes:**
- `200`: Team details retrieved
- `404`: Team not found

---

#### `PUT /api/v1/teams/{team_id}`
Update an existing team configuration.

**Request Body:** Same as POST `/teams/` but all fields optional

**Response Codes:**
- `200`: Team updated successfully
- `400`: Invalid configuration
- `404`: Team not found
- `409`: Configuration conflict

---

#### `DELETE /api/v1/teams/{team_id}`
Delete a team and stop all active executions.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `force` | boolean | false | Force delete even with active executions |

**Response Codes:**
- `200`: Team deleted successfully
- `400`: Team has active executions (use force=true)
- `404`: Team not found

---

#### `GET /api/v1/teams/{team_id}/status`
Get real-time team status and health metrics.

**Response Schema:**
```json
{
  "type": "object",
  "properties": {
    "team_id": {"type": "string"},
    "status": {"type": "string", "enum": ["active", "inactive", "error", "maintenance"]},
    "health_score": {"type": "number", "minimum": 0, "maximum": 1},
    "active_executions": {"type": "integer"},
    "last_execution": {"type": "string", "format": "date-time"},
    "performance_metrics": {
      "type": "object",
      "properties": {
        "total_executions": {"type": "integer"},
        "success_rate": {"type": "number"},
        "avg_response_time": {"type": "number"},
        "avg_cost_per_execution": {"type": "number"}
      }
    },
    "resource_usage": {
      "type": "object", 
      "properties": {
        "cpu_usage": {"type": "number"},
        "memory_usage": {"type": "number"},
        "token_usage_24h": {"type": "integer"}
      }
    }
  }
}
```

### Agents API (`/api/v1/agents`)

#### `POST /api/v1/agents/search`
Search for agents based on criteria.

**Request Schema:**
```json
{
  "type": "object",
  "properties": {
    "query": {"type": "string", "maxLength": 200},
    "role": {"type": "string", "enum": ["coordinator", "supervisor", "worker", "specialist"]},
    "capabilities": {"type": "array", "items": {"type": "string"}},
    "tools": {"type": "array", "items": {"type": "string"}},
    "domain": {"type": "string"},
    "min_compatibility": {"type": "number", "minimum": 0, "maximum": 1},
    "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 20},
    "offset": {"type": "integer", "minimum": 0, "default": 0}
  }
}
```

**Example Requests:**
```bash
# Search by capability
curl -X POST http://localhost:8000/api/v1/agents/search \
  -H "Content-Type: application/json" \
  -d '{"capabilities": ["research", "analysis"], "limit": 10}'

# Search by role and domain  
curl -X POST http://localhost:8000/api/v1/agents/search \
  -H "Content-Type: application/json" \
  -d '{"role": "worker", "domain": "research", "min_compatibility": 0.8}'
```

---

#### `GET /api/v1/agents/`
List all available agents.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `role` | string | - | Filter by agent role |
| `capability` | string | - | Filter by specific capability |
| `limit` | integer | 50 | Max results (1-200) |
| `offset` | integer | 0 | Pagination offset |

---

#### `GET /api/v1/agents/{agent_id}`
Get detailed agent information.

**Response includes:**
- Full agent configuration
- Capability proficiency scores
- Usage statistics
- Compatibility ratings
- Performance metrics

---

#### `POST /api/v1/agents/compatibility`
Check compatibility between multiple agents.

**Request Schema:**
```json
{
  "type": "object",
  "required": ["agent_ids"],
  "properties": {
    "agent_ids": {
      "type": "array",
      "items": {"type": "string"},
      "minItems": 2,
      "maxItems": 20
    },
    "team_context": {"type": "string"},
    "include_suggestions": {"type": "boolean", "default": true}
  }
}
```

**Response Schema:**
```json
{
  "type": "object",
  "properties": {
    "compatibility_matrix": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "additionalProperties": {"type": "number"}
      }
    },
    "overall_compatibility": {"type": "number"},
    "recommendations": {"type": "array", "items": {"type": "string"}},
    "warnings": {"type": "array", "items": {"type": "string"}}
  }
}
```

---

#### `GET /api/v1/agents/stats`
Get agent library statistics.

**Response Schema:**
```json
{
  "type": "object", 
  "properties": {
    "total_agents": {"type": "integer"},
    "by_role": {
      "type": "object",
      "properties": {
        "coordinator": {"type": "integer"},
        "supervisor": {"type": "integer"},
        "worker": {"type": "integer"},
        "specialist": {"type": "integer"}
      }
    },
    "by_domain": {"type": "object"},
    "top_capabilities": {"type": "array", "items": {"type": "string"}},
    "avg_compatibility": {"type": "number"}
  }
}
```

---

#### `POST /api/v1/agents/suggest-team`
Get team composition suggestions based on requirements.

**Request Schema:**
```json
{
  "type": "object",
  "required": ["requirements"],
  "properties": {
    "requirements": {
      "type": "object",
      "properties": {
        "domain": {"type": "string"},
        "task_type": {"type": "string"},
        "team_size": {"type": "integer", "minimum": 2, "maximum": 20},
        "required_capabilities": {"type": "array", "items": {"type": "string"}},
        "optional_capabilities": {"type": "array", "items": {"type": "string"}},
        "budget_level": {"type": "string", "enum": ["low", "standard", "high"]},
        "performance_priority": {"type": "string", "enum": ["speed", "accuracy", "cost"]}
      }
    }
  }
}
```

**Response includes:**
- Multiple team composition options
- Capability coverage analysis
- Cost estimates
- Performance predictions

### Configurations API (`/api/v1/configs`)

#### `POST /api/v1/configs/validate`
Validate a hierarchical team configuration.

**Request Schema:**
```json
{
  "type": "object",
  "required": ["config"],
  "properties": {
    "config": {"$ref": "#/definitions/TeamConfiguration"},
    "validation_level": {
      "type": "string", 
      "enum": ["basic", "standard", "strict"],
      "default": "standard"
    },
    "optimize": {"type": "boolean", "default": false}
  }
}
```

**Validation Levels:**
- **basic**: Syntax and required fields only
- **standard**: Include capability and tool validation
- **strict**: Full compatibility and optimization analysis

**Response Schema:**
```json
{
  "type": "object",
  "properties": {
    "valid": {"type": "boolean"},
    "validation_result": {
      "type": "object",
      "properties": {
        "overall_score": {"type": "number"},
        "issues": {"type": "array", "items": {"$ref": "#/definitions/ValidationIssue"}},
        "warnings": {"type": "array", "items": {"type": "string"}},
        "recommendations": {"type": "array", "items": {"type": "string"}},
        "optimized_config": {"$ref": "#/definitions/TeamConfiguration"}
      }
    }
  }
}
```

---

#### `POST /api/v1/configs/upload`
Upload and parse configuration files.

**Form Data:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file` | file | Yes | YAML/JSON configuration file |
| `validate` | boolean | No | Auto-validate after upload |

**Supported Formats:**
- YAML (.yml, .yaml)
- JSON (.json)

**Response includes:**
- Parsed configuration
- Validation results (if requested)
- File metadata

---

#### `GET /api/v1/configs/templates`
List available configuration templates.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `category` | string | - | Template category filter |
| `difficulty` | string | - | Difficulty level filter |
| `search` | string | - | Search in names/descriptions |
| `sort` | string | "name" | Sort by: name, popularity, rating |

**Response Schema:**
```json
{
  "type": "object",
  "properties": {
    "templates": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {"type": "string"},
          "name": {"type": "string"},
          "description": {"type": "string"},
          "category": {"type": "string"},
          "difficulty": {"type": "string", "enum": ["beginner", "intermediate", "advanced"]},
          "tags": {"type": "array", "items": {"type": "string"}},
          "usage_count": {"type": "integer"},
          "rating": {"type": "number"},
          "created_at": {"type": "string", "format": "date-time"},
          "file_path": {"type": "string"}
        }
      }
    },
    "total": {"type": "integer"}
  }
}
```

---

#### `GET /api/v1/configs/templates/{template_id}`
Get detailed template information and configuration.

**Response includes:**
- Complete template configuration
- Usage examples
- Customization options
- Prerequisites and dependencies

---

#### `POST /api/v1/configs/export`
Export team configuration in various formats.

**Request Schema:**
```json
{
  "type": "object",
  "required": ["team_id", "format"],
  "properties": {
    "team_id": {"type": "string"},
    "format": {"type": "string", "enum": ["yaml", "json", "docker", "terraform"]},
    "include_metadata": {"type": "boolean", "default": true},
    "anonymize": {"type": "boolean", "default": false}
  }
}
```

**Supported Export Formats:**
- **yaml**: YAML configuration file
- **json**: JSON configuration file  
- **docker**: Docker Compose with services
- **terraform**: Terraform deployment configuration

### Executions API (`/api/v1/executions`)

#### `POST /api/v1/executions/{team_id}/execute`
Execute a task using a hierarchical team.

**Request Schema:**
```json
{
  "type": "object",
  "required": ["task"],
  "properties": {
    "task": {"type": "string", "minLength": 1, "maxLength": 10000},
    "context": {
      "type": "object",
      "properties": {
        "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
        "deadline": {"type": "string", "format": "date-time"},
        "format": {"type": "string"},
        "audience": {"type": "string"},
        "constraints": {"type": "array", "items": {"type": "string"}}
      }
    },
    "execution_options": {
      "type": "object",
      "properties": {
        "timeout_seconds": {"type": "integer", "minimum": 10, "maximum": 3600},
        "max_retries": {"type": "integer", "minimum": 0, "maximum": 5},
        "stream_response": {"type": "boolean", "default": false},
        "save_intermediate": {"type": "boolean", "default": false}
      }
    }
  }
}
```

**Response Codes:**
- `202`: Execution started successfully (async)
- `400`: Invalid task or options
- `404`: Team not found
- `409`: Team busy with maximum concurrent executions
- `413`: Task too large

---

#### `GET /api/v1/executions/{execution_id}`
Get execution status and results.

**Response Schema:**
```json
{
  "type": "object",
  "properties": {
    "execution_id": {"type": "string"},
    "team_id": {"type": "string"},
    "status": {"type": "string", "enum": ["pending", "running", "completed", "failed", "cancelled"]},
    "started_at": {"type": "string", "format": "date-time"},
    "completed_at": {"type": "string", "format": "date-time"},
    "duration_seconds": {"type": "number"},
    "progress": {
      "type": "object",
      "properties": {
        "percentage": {"type": "number", "minimum": 0, "maximum": 100},
        "current_step": {"type": "string"},
        "steps_completed": {"type": "integer"},
        "total_steps": {"type": "integer"},
        "eta_seconds": {"type": "number"}
      }
    },
    "result": {
      "type": "object",
      "properties": {
        "success": {"type": "boolean"},
        "output": {"type": "string"},
        "intermediate_outputs": {"type": "array"},
        "metadata": {
          "type": "object",
          "properties": {
            "tokens_used": {"type": "integer"},
            "agents_involved": {"type": "array", "items": {"type": "string"}},
            "cost_estimate": {"type": "string"},
            "execution_path": {"type": "array"}
          }
        }
      }
    },
    "error": {
      "type": "object",
      "properties": {
        "code": {"type": "string"},
        "message": {"type": "string"},
        "details": {},
        "recovery_suggestions": {"type": "array", "items": {"type": "string"}}
      }
    },
    "performance_metrics": {
      "type": "object",
      "properties": {
        "response_time": {"type": "number"},
        "accuracy_score": {"type": "number"},
        "team_coordination_score": {"type": "number"},
        "resource_efficiency": {"type": "number"}
      }
    }
  }
}
```

---

#### `GET /api/v1/executions/`
List executions with filtering and pagination.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `team_id` | string | - | Filter by team |
| `status` | string | - | Filter by status |
| `start_date` | string | - | Filter executions after date (ISO 8601) |
| `end_date` | string | - | Filter executions before date |
| `limit` | integer | 50 | Max results (1-500) |
| `offset` | integer | 0 | Pagination offset |
| `sort` | string | "-started_at" | Sort field (+/- for asc/desc) |

**Sort Options:**
- `started_at`: Execution start time
- `duration`: Execution duration
- `cost`: Execution cost
- `success_rate`: Team success rate

---

#### `POST /api/v1/executions/{execution_id}/cancel`
Cancel a running execution.

**Request Schema:**
```json
{
  "type": "object",
  "properties": {
    "reason": {"type": "string", "maxLength": 200},
    "force": {"type": "boolean", "default": false}
  }
}
```

**Response Codes:**
- `200`: Execution cancelled successfully
- `400`: Execution cannot be cancelled (already completed)
- `404`: Execution not found

---

#### `GET /api/v1/executions/{execution_id}/logs`
Get detailed execution logs.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `level` | string | "info" | Log level filter (debug, info, warn, error) |
| `agent` | string | - | Filter logs by agent |
| `limit` | integer | 1000 | Max log entries |
| `format` | string | "json" | Response format (json, text) |

**Response Schema:**
```json
{
  "type": "object",
  "properties": {
    "execution_id": {"type": "string"},
    "logs": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "timestamp": {"type": "string", "format": "date-time"},
          "level": {"type": "string"},
          "agent": {"type": "string"},
          "message": {"type": "string"},
          "metadata": {}
        }
      }
    },
    "total_entries": {"type": "integer"}
  }
}
```

---

#### `GET /api/v1/executions/{execution_id}/stream`
Stream execution progress (Server-Sent Events).

**Headers:**
```
Accept: text/event-stream
Cache-Control: no-cache
```

**Event Types:**
- `progress`: Progress updates
- `output`: Partial outputs
- `completed`: Final result
- `error`: Error events

**Example Events:**
```
event: progress
data: {"percentage": 25, "current_step": "Research phase"}

event: output  
data: {"partial_result": "Based on initial research..."}

event: completed
data: {"success": true, "final_output": "Complete report..."}
```

## Data Type Definitions

### TeamConfiguration
```json
{
  "type": "object",
  "required": ["coordinator", "teams"],
  "properties": {
    "coordinator": {"$ref": "#/definitions/CoordinatorConfig"},
    "teams": {
      "type": "array",
      "items": {"$ref": "#/definitions/TeamConfig"},
      "minItems": 1
    },
    "performance": {"$ref": "#/definitions/PerformanceConfig"}
  }
}
```

### CoordinatorConfig  
```json
{
  "type": "object",
  "required": ["routing_strategy"],
  "properties": {
    "routing_strategy": {
      "type": "string",
      "enum": ["capability_based", "llm_based", "rule_based", "performance_based", "workload_based"]
    },
    "prompts": {"$ref": "#/definitions/PromptConfig"},
    "llm": {"$ref": "#/definitions/LLMConfig"},
    "memory": {"$ref": "#/definitions/MemoryConfig"}
  }
}
```

### TeamConfig
```json
{
  "type": "object", 
  "required": ["name", "supervisor", "workers"],
  "properties": {
    "name": {"type": "string"},
    "supervisor": {"$ref": "#/definitions/SupervisorConfig"},
    "workers": {
      "type": "array",
      "items": {"$ref": "#/definitions/WorkerConfig"},
      "minItems": 1
    }
  }
}
```

### LLMConfig
```json
{
  "type": "object",
  "required": ["provider", "model"],
  "properties": {
    "provider": {"type": "string", "enum": ["openai", "anthropic", "google", "groq"]},
    "model": {"type": "string"},
    "temperature": {"type": "number", "minimum": 0, "maximum": 2},
    "max_tokens": {"type": "integer", "minimum": 1},
    "timeout": {"type": "integer", "minimum": 1}
  }
}
```

### ValidationIssue
```json
{
  "type": "object",
  "properties": {
    "severity": {"type": "string", "enum": ["error", "warning", "info"]},
    "code": {"type": "string"},
    "message": {"type": "string"},
    "path": {"type": "string"},
    "suggestion": {"type": "string"}
  }
}
```

## HTTP Status Codes

| Code | Description | Usage |
|------|-------------|-------|
| 200 | OK | Successful GET, PUT, DELETE |
| 201 | Created | Successful POST creation |
| 202 | Accepted | Async operation started |
| 204 | No Content | Successful DELETE with no body |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Access denied |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Resource conflict |
| 422 | Unprocessable Entity | Validation failed |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |
| 502 | Bad Gateway | Upstream service error |
| 503 | Service Unavailable | Service temporarily down |

## Request/Response Headers

### Common Request Headers
```http
Content-Type: application/json
Accept: application/json
X-API-Key: your-api-key
X-Request-ID: unique-request-id
User-Agent: your-client/1.0
```

### Common Response Headers
```http
Content-Type: application/json
X-Request-ID: unique-request-id
X-Response-Time: 123ms
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1705328400
```

## Webhooks

Configure webhooks to receive real-time notifications:

### Webhook Events
- `team.created`
- `team.updated` 
- `team.deleted`
- `execution.started`
- `execution.completed`
- `execution.failed`

### Webhook Payload Example
```json
{
  "event": "execution.completed",
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "execution_id": "exec_789",
    "team_id": "team_123",
    "status": "completed",
    "duration_seconds": 45.2,
    "success": true
  }
}
```

### Webhook Configuration
```bash
curl -X POST http://localhost:8000/api/v1/webhooks \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://your-app.com/webhooks/hierarchical-agents",
    "events": ["execution.completed", "execution.failed"],
    "secret": "your-webhook-secret"
  }'
```