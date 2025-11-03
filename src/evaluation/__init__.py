"""
Multi-Agent Team Evaluation Framework

This module provides comprehensive evaluation capabilities for hierarchical agent teams,
inspired by the open_deep_research evaluation methodology.
"""

from .team_evaluator import TeamEvaluator, EvaluationResult
from .test_scenarios import TestScenario, TestScenarioRunner, ScenarioType
from .evaluation_prompts import EvaluationPrompts
from .results_dashboard import EvaluationResultsDashboard
from .common import EvaluationDimension, EvaluationSeverity

__all__ = [
    'TeamEvaluator',
    'EvaluationResult', 
    'EvaluationDimension',
    'EvaluationSeverity',
    'TestScenario',
    'TestScenarioRunner',
    'ScenarioType',
    'EvaluationPrompts',
    'EvaluationResultsDashboard'
]