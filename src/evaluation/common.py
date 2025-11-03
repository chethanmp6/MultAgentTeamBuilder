"""
Common types and enums for the evaluation framework
"""

from enum import Enum


class EvaluationDimension(Enum):
    """Evaluation dimensions adapted for hierarchical teams"""
    TASK_COMPLETION = "task_completion"
    COLLABORATION_EFFECTIVENESS = "collaboration_effectiveness" 
    RESOURCE_UTILIZATION = "resource_utilization"
    RESPONSE_COHERENCE = "response_coherence"
    SCALABILITY_PERFORMANCE = "scalability_performance"
    ERROR_HANDLING = "error_handling"


class EvaluationSeverity(Enum):
    """Severity levels for evaluation findings"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"