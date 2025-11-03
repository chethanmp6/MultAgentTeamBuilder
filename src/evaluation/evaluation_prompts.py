"""
Evaluation Prompts - Structured prompts for LLM-as-judge evaluation
Adapted from open_deep_research methodology for hierarchical agent teams
"""

from typing import Dict, Any
from .common import EvaluationDimension


class EvaluationPrompts:
    """Collection of evaluation prompts for different dimensions"""
    
    def get_dimension_prompt(self, dimension: EvaluationDimension, context: Dict[str, Any]) -> Dict[str, str]:
        """Get evaluation prompt for a specific dimension"""
        
        prompt_map = {
            EvaluationDimension.TASK_COMPLETION: self._task_completion_prompt,
            EvaluationDimension.COLLABORATION_EFFECTIVENESS: self._collaboration_effectiveness_prompt,
            EvaluationDimension.RESOURCE_UTILIZATION: self._resource_utilization_prompt,
            EvaluationDimension.RESPONSE_COHERENCE: self._response_coherence_prompt,
            EvaluationDimension.SCALABILITY_PERFORMANCE: self._scalability_performance_prompt,
            EvaluationDimension.ERROR_HANDLING: self._error_handling_prompt
        }
        
        return prompt_map[dimension](context)
    
    def _task_completion_prompt(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Prompt for evaluating task completion quality"""
        return {
            "system": """You are an expert evaluator of hierarchical agent team performance. 
Your task is to evaluate how well a team completes assigned tasks.

Evaluation Criteria (1-5 scale):
5 - Exceptional: Tasks completed perfectly with additional insights
4 - Good: Tasks completed well with minor improvements possible  
3 - Satisfactory: Tasks completed adequately, meets basic requirements
2 - Poor: Tasks partially completed with significant issues
1 - Failure: Tasks not completed or major failures

Consider:
- Accuracy of responses
- Completeness of task fulfillment
- Quality of outputs
- Adherence to requirements

Respond in JSON format:
{
  "score": <1-5 integer>,
  "reasoning": "<detailed explanation>",
  "suggestions": ["<improvement suggestion 1>", "<suggestion 2>"]
}""",
            
            "human": f"""Evaluate the task completion performance of this hierarchical agent team:

Team Configuration:
- Name: {context['team_config']['name']}
- Teams: {context['team_config']['teams_count']}
- Workers: {context['team_config']['workers_count']}

Test Results Summary:
- Success Rate: {context['success_rate']:.1%}
- Average Execution Time: {context['avg_execution_time']:.1f}s

Detailed Test Results:
{self._format_test_results(context['test_results'])}

Evaluate the team's task completion performance and provide a score from 1-5 with detailed reasoning and improvement suggestions."""
        }
    
    def _collaboration_effectiveness_prompt(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Prompt for evaluating collaboration effectiveness"""
        return {
            "system": """You are an expert evaluator of hierarchical agent team collaboration.
Your task is to evaluate how effectively team members work together.

Evaluation Criteria (1-5 scale):
5 - Exceptional: Seamless coordination, optimal task distribution, excellent communication
4 - Good: Effective coordination with minor coordination issues
3 - Satisfactory: Adequate collaboration, some coordination gaps
2 - Poor: Significant coordination problems, inefficient task distribution
1 - Failure: Poor collaboration, major coordination failures

Consider:
- Coordination between supervisor and workers
- Task distribution efficiency
- Information sharing quality
- Conflict resolution capability
- Overall team synergy

Respond in JSON format:
{
  "score": <1-5 integer>,
  "reasoning": "<detailed explanation>", 
  "suggestions": ["<improvement suggestion 1>", "<suggestion 2>"]
}""",
            
            "human": f"""Evaluate the collaboration effectiveness of this hierarchical agent team:

Team Configuration:
- Name: {context['team_config']['name']}
- Teams: {context['team_config']['teams_count']}
- Workers: {context['team_config']['workers_count']}

Test Results Summary:
- Success Rate: {context['success_rate']:.1%}
- Average Execution Time: {context['avg_execution_time']:.1f}s

Complex Workflow Results:
{self._format_test_results([r for r in context['test_results'] if 'workflow' in r.get('scenario', '').lower()])}

Evaluate how well the team members collaborate and coordinate their efforts."""
        }
    
    def _resource_utilization_prompt(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Prompt for evaluating resource utilization"""
        return {
            "system": """You are an expert evaluator of hierarchical agent team resource utilization.
Your task is to evaluate how efficiently the team uses computational and time resources.

Evaluation Criteria (1-5 scale):
5 - Exceptional: Optimal resource usage, minimal waste, excellent efficiency
4 - Good: Efficient resource usage with minor optimizations possible
3 - Satisfactory: Adequate resource usage, some inefficiencies present
2 - Poor: Significant resource waste, inefficient processes
1 - Failure: Very poor resource utilization, major inefficiencies

Consider:
- Execution time efficiency
- Computational resource usage
- Task distribution optimization
- Parallel processing effectiveness
- Overall system efficiency

Respond in JSON format:
{
  "score": <1-5 integer>,
  "reasoning": "<detailed explanation>",
  "suggestions": ["<improvement suggestion 1>", "<suggestion 2>"]
}""",
            
            "human": f"""Evaluate the resource utilization of this hierarchical agent team:

Team Configuration:
- Name: {context['team_config']['name']}
- Teams: {context['team_config']['teams_count']}
- Workers: {context['team_config']['workers_count']}

Performance Metrics:
- Success Rate: {context['success_rate']:.1%}
- Average Execution Time: {context['avg_execution_time']:.1f}s

Test Results:
{self._format_test_results(context['test_results'])}

Evaluate how efficiently the team utilizes resources (time, computation, etc.)."""
        }
    
    def _response_coherence_prompt(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Prompt for evaluating response coherence"""
        return {
            "system": """You are an expert evaluator of hierarchical agent team response quality.
Your task is to evaluate the coherence, clarity, and quality of team responses.

Evaluation Criteria (1-5 scale):
5 - Exceptional: Highly coherent, clear, well-structured, insightful responses
4 - Good: Coherent and clear responses with minor issues
3 - Satisfactory: Adequate coherence, understandable responses
2 - Poor: Some coherence issues, unclear or confusing responses
1 - Failure: Incoherent, unclear, or nonsensical responses

Consider:
- Logical flow and structure
- Clarity of communication
- Consistency across responses
- Relevance to questions asked
- Overall response quality

Respond in JSON format:
{
  "score": <1-5 integer>,
  "reasoning": "<detailed explanation>",
  "suggestions": ["<improvement suggestion 1>", "<suggestion 2>"]
}""",
            
            "human": f"""Evaluate the response coherence of this hierarchical agent team:

Team Configuration:
- Name: {context['team_config']['name']}
- Teams: {context['team_config']['teams_count']}
- Workers: {context['team_config']['workers_count']}

Sample Responses:
{self._format_sample_responses(context['test_results'])}

Evaluate the coherence, clarity, and overall quality of the team's responses."""
        }
    
    def _scalability_performance_prompt(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Prompt for evaluating scalability performance"""
        return {
            "system": """You are an expert evaluator of hierarchical agent team scalability.
Your task is to evaluate how well the team handles increased workload and complexity.

Evaluation Criteria (1-5 scale):
5 - Exceptional: Excellent scalability, handles load increases gracefully
4 - Good: Good scalability with minor performance degradation under load
3 - Satisfactory: Adequate scalability, noticeable but manageable performance impact
2 - Poor: Poor scalability, significant performance degradation under load
1 - Failure: Very poor scalability, fails under increased load

Consider:
- Performance under concurrent tasks
- Handling of complex workflows
- Resource scaling efficiency
- Response time consistency
- System stability under load

Respond in JSON format:
{
  "score": <1-5 integer>,
  "reasoning": "<detailed explanation>",
  "suggestions": ["<improvement suggestion 1>", "<suggestion 2>"]
}""",
            
            "human": f"""Evaluate the scalability performance of this hierarchical agent team:

Team Configuration:
- Name: {context['team_config']['name']}
- Teams: {context['team_config']['teams_count']}
- Workers: {context['team_config']['workers_count']}

Load Test Results:
{self._format_test_results([r for r in context['test_results'] if 'load' in r.get('scenario', '').lower()])}

Performance Metrics:
- Success Rate: {context['success_rate']:.1%}
- Average Execution Time: {context['avg_execution_time']:.1f}s

Evaluate how well the team scales with increased workload and complexity."""
        }
    
    def _error_handling_prompt(self, context: Dict[str, Any]) -> Dict[str, str]:
        """Prompt for evaluating error handling"""
        return {
            "system": """You are an expert evaluator of hierarchical agent team error handling.
Your task is to evaluate how well the team handles errors, edge cases, and unexpected situations.

Evaluation Criteria (1-5 scale):
5 - Exceptional: Excellent error handling, graceful recovery, helpful error messages
4 - Good: Good error handling with minor improvements possible
3 - Satisfactory: Adequate error handling, basic recovery mechanisms
2 - Poor: Poor error handling, limited recovery capabilities
1 - Failure: Very poor error handling, system fails ungracefully

Consider:
- Graceful handling of edge cases
- Error recovery mechanisms
- Quality of error messages
- System stability during errors
- Robustness against unexpected inputs

Respond in JSON format:
{
  "score": <1-5 integer>,
  "reasoning": "<detailed explanation>",
  "suggestions": ["<improvement suggestion 1>", "<suggestion 2>"]
}""",
            
            "human": f"""Evaluate the error handling of this hierarchical agent team:

Team Configuration:
- Name: {context['team_config']['name']}
- Teams: {context['team_config']['teams_count']}
- Workers: {context['team_config']['workers_count']}

Edge Case Test Results:
{self._format_test_results([r for r in context['test_results'] if 'edge' in r.get('scenario', '').lower()])}

Error Statistics:
- Tests with Errors: {len([r for r in context['test_results'] if r.get('error')])}
- Success Rate: {context['success_rate']:.1%}

Evaluate how well the team handles errors, edge cases, and unexpected situations."""
        }
    
    def _format_test_results(self, test_results: list) -> str:
        """Format test results for prompt inclusion"""
        if not test_results:
            return "No relevant test results available."
        
        formatted = []
        for i, result in enumerate(test_results[:5]):  # Limit to first 5 results
            status = "✅ Success" if result['success'] else "❌ Failed"
            error_info = f" (Error: {result['error']})" if result.get('error') else ""
            
            formatted.append(f"""
Test {i+1}: {result['scenario']}
Status: {status}{error_info}
Execution Time: {result['execution_time']:.1f}s
Response: {result['response'][:200]}{'...' if len(result['response']) > 200 else ''}
""")
        
        if len(test_results) > 5:
            formatted.append(f"\n... and {len(test_results) - 5} more test results")
        
        return "\n".join(formatted)
    
    def _format_sample_responses(self, test_results: list) -> str:
        """Format sample responses for coherence evaluation"""
        if not test_results:
            return "No responses available."
        
        formatted = []
        for i, result in enumerate(test_results[:3]):  # Limit to first 3 responses
            formatted.append(f"""
Response {i+1} (from {result['scenario']}):
{result['response'][:400]}{'...' if len(result['response']) > 400 else ''}
""")
        
        return "\n".join(formatted)
    
    def get_comparative_prompt(self, team_a: str, team_b: str, 
                             results_a: Dict[str, Any], 
                             results_b: Dict[str, Any]) -> Dict[str, str]:
        """Get prompt for comparative evaluation of two teams"""
        return {
            "system": """You are an expert evaluator comparing two hierarchical agent teams.
Your task is to determine which team performs better overall.

Compare the teams across these dimensions:
- Task completion quality
- Collaboration effectiveness  
- Resource utilization
- Response coherence
- Scalability performance
- Error handling

Provide a structured comparison and declare a winner.

Respond in JSON format:
{
  "winner": "<team_a_name or team_b_name>",
  "reasoning": "<detailed comparison explanation>",
  "dimension_analysis": {
    "task_completion": "<which team is better and why>",
    "collaboration": "<which team is better and why>",
    "resource_utilization": "<which team is better and why>",
    "response_coherence": "<which team is better and why>",
    "scalability": "<which team is better and why>",
    "error_handling": "<which team is better and why>"
  },
  "recommendations": {
    "<team_a_name>": ["<improvement for team A>"],
    "<team_b_name>": ["<improvement for team B>"]
  }
}""",
            
            "human": f"""Compare these two hierarchical agent teams:

TEAM A: {team_a}
Overall Score: {results_a.get('overall_score', 0):.2f}
Dimension Scores: {results_a.get('dimension_scores', {})}
Success Rate: {results_a.get('success_rate', 0):.1%}
Avg Response Time: {results_a.get('avg_time', 0):.1f}s

TEAM B: {team_b}
Overall Score: {results_b.get('overall_score', 0):.2f}
Dimension Scores: {results_b.get('dimension_scores', {})}
Success Rate: {results_b.get('success_rate', 0):.1%}
Avg Response Time: {results_b.get('avg_time', 0):.1f}s

Compare these teams and determine which performs better overall."""
        }