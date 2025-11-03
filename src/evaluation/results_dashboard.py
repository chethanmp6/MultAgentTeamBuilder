"""
Evaluation Results Dashboard - Visualization and analysis of team evaluation results
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from typing import Dict, List, Any
import pandas as pd
from datetime import datetime

from .team_evaluator import EvaluationResult
from .common import EvaluationDimension


class EvaluationResultsDashboard:
    """Dashboard for displaying evaluation results"""
    
    @staticmethod
    def render_evaluation_results(evaluation: EvaluationResult):
        """Render complete evaluation results"""
        st.markdown("---")
        st.markdown("## 📊 Team Evaluation Results")
        
        # Overall score and grade
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Overall Score",
                value=f"{evaluation.overall_score:.2f}",
                delta=f"Grade: {evaluation.grade}"
            )
        
        with col2:
            st.metric(
                label="Test Success Rate",
                value=f"{len([r for r in evaluation.test_results if r.success])}/{len(evaluation.test_results)}",
                delta=f"{(len([r for r in evaluation.test_results if r.success]) / len(evaluation.test_results) * 100):.1f}%" if evaluation.test_results else "0%"
            )
        
        with col3:
            avg_time = sum(r.execution_time for r in evaluation.test_results) / len(evaluation.test_results) if evaluation.test_results else 0
            st.metric(
                label="Avg Response Time",
                value=f"{avg_time:.1f}s"
            )
        
        with col4:
            st.metric(
                label="Evaluation Time",
                value=f"{evaluation.evaluation_time:.1f}s"
            )
        
        # Dimension scores visualization
        EvaluationResultsDashboard._render_dimension_scores(evaluation)
        
        # Test results summary
        EvaluationResultsDashboard._render_test_results(evaluation.test_results)
        
        # Recommendations and warnings
        EvaluationResultsDashboard._render_recommendations_warnings(evaluation)
        
        # Detailed analysis
        with st.expander("📈 Detailed Analysis", expanded=False):
            EvaluationResultsDashboard._render_detailed_analysis(evaluation)
    
    @staticmethod
    def _render_dimension_scores(evaluation: EvaluationResult):
        """Render dimension scores with radar chart"""
        st.markdown("### 🎯 Performance by Dimension")
        
        # Prepare data for radar chart
        dimensions = list(evaluation.dimension_scores.keys())
        scores = list(evaluation.dimension_scores.values())
        
        # Create radar chart
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=scores,
            theta=[dim.value.replace('_', ' ').title() for dim in dimensions],
            fill='toself',
            name=evaluation.team_name,
            line_color='rgb(0, 123, 255)'
        ))
        
        fig.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 1]
                )),
            showlegend=True,
            title="Team Performance Radar Chart",
            height=400
        )
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("**Dimension Scores:**")
            for dimension, score in evaluation.dimension_scores.items():
                color = "green" if score >= 0.8 else "orange" if score >= 0.6 else "red"
                st.markdown(f"**{dimension.value.replace('_', ' ').title()}:** "
                          f"<span style='color: {color}'>{score:.2f}</span>", 
                          unsafe_allow_html=True)
    
    @staticmethod
    def _render_test_results(test_results: List[Any]):
        """Render test results summary"""
        st.markdown("### 🧪 Test Results Summary")
        
        if not test_results:
            st.info("No test results available")
            return
        
        # Create summary DataFrame
        results_data = []
        for result in test_results:
            results_data.append({
                'Scenario': result.scenario_name,
                'Type': result.scenario_type.value,
                'Status': '✅ Pass' if result.success else '❌ Fail',
                'Time (s)': f"{result.execution_time:.1f}",
                'Error': result.error_message if result.error_message else '-'
            })
        
        df = pd.DataFrame(results_data)
        st.dataframe(df, use_container_width=True)
        
        # Success rate by scenario type
        type_stats = {}
        for result in test_results:
            scenario_type = result.scenario_type.value
            if scenario_type not in type_stats:
                type_stats[scenario_type] = {'success': 0, 'total': 0}
            type_stats[scenario_type]['total'] += 1
            if result.success:
                type_stats[scenario_type]['success'] += 1
        
        # Visualization of success rates by type
        if len(type_stats) > 1:
            types = list(type_stats.keys())
            success_rates = [type_stats[t]['success'] / type_stats[t]['total'] * 100 for t in types]
            
            fig = px.bar(
                x=types,
                y=success_rates,
                title="Success Rate by Scenario Type",
                labels={'x': 'Scenario Type', 'y': 'Success Rate (%)'}
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def _render_recommendations_warnings(evaluation: EvaluationResult):
        """Render recommendations and warnings"""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 💡 Recommendations")
            if evaluation.recommendations:
                for i, rec in enumerate(evaluation.recommendations, 1):
                    st.markdown(f"{i}. {rec}")
            else:
                st.success("No specific recommendations - team performing well!")
        
        with col2:
            st.markdown("### ⚠️ Warnings")
            if evaluation.warnings:
                for warning in evaluation.warnings:
                    st.warning(warning)
            else:
                st.success("No warnings - team appears stable!")
    
    @staticmethod
    def _render_detailed_analysis(evaluation: EvaluationResult):
        """Render detailed analysis"""
        
        # Performance trends
        if evaluation.test_results:
            st.markdown("#### ⏱️ Response Time Analysis")
            
            times_data = []
            for i, result in enumerate(evaluation.test_results):
                times_data.append({
                    'Test': i + 1,
                    'Scenario': result.scenario_name,
                    'Time': result.execution_time,
                    'Success': result.success
                })
            
            df_times = pd.DataFrame(times_data)
            
            fig = px.scatter(
                df_times,
                x='Test',
                y='Time',
                color='Success',
                hover_data=['Scenario'],
                title="Response Times by Test",
                labels={'Time': 'Response Time (s)'}
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Team configuration details
        st.markdown("#### 🏗️ Team Configuration")
        config_details = {
            'Team Name': evaluation.team_config.get('team', {}).get('name', 'Unknown'),
            'Team Type': evaluation.team_config.get('team', {}).get('type', 'Unknown'),
            'Number of Teams': len(evaluation.team_config.get('teams', [])),
            'Total Workers': sum(len(team.get('workers', [])) for team in evaluation.team_config.get('teams', [])),
            'Evaluation Timestamp': evaluation.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        for key, value in config_details.items():
            st.markdown(f"**{key}:** {value}")
    
    @staticmethod
    def render_comparative_results(evaluations: List[EvaluationResult]):
        """Render comparative analysis of multiple evaluations"""
        st.markdown("---")
        st.markdown("## 🏆 Comparative Team Analysis")
        
        if len(evaluations) < 2:
            st.warning("Need at least 2 evaluations for comparison")
            return
        
        # Overall scores comparison
        team_names = [e.team_name for e in evaluations]
        overall_scores = [e.overall_score for e in evaluations]
        
        fig = px.bar(
            x=team_names,
            y=overall_scores,
            title="Overall Score Comparison",
            labels={'x': 'Team', 'y': 'Overall Score'},
            color=overall_scores,
            color_continuous_scale='RdYlGn'
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Dimension comparison
        st.markdown("### 📊 Dimension-by-Dimension Comparison")
        
        # Prepare data for dimension comparison
        comparison_data = []
        for evaluation in evaluations:
            for dimension, score in evaluation.dimension_scores.items():
                comparison_data.append({
                    'Team': evaluation.team_name,
                    'Dimension': dimension.value.replace('_', ' ').title(),
                    'Score': score
                })
        
        df_comparison = pd.DataFrame(comparison_data)
        
        fig = px.bar(
            df_comparison,
            x='Dimension',
            y='Score',
            color='Team',
            barmode='group',
            title="Dimension Scores Comparison"
        )
        fig.update_layout(height=500, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)
        
        # Performance summary table
        st.markdown("### 📋 Performance Summary")
        summary_data = []
        for evaluation in evaluations:
            success_rate = len([r for r in evaluation.test_results if r.success]) / len(evaluation.test_results) if evaluation.test_results else 0
            avg_time = sum(r.execution_time for r in evaluation.test_results) / len(evaluation.test_results) if evaluation.test_results else 0
            
            summary_data.append({
                'Team': evaluation.team_name,
                'Overall Score': f"{evaluation.overall_score:.3f}",
                'Grade': evaluation.grade,
                'Success Rate': f"{success_rate:.1%}",
                'Avg Response Time': f"{avg_time:.1f}s",
                'Test Count': len(evaluation.test_results)
            })
        
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True)
        
        # Winner declaration
        best_team = max(evaluations, key=lambda x: x.overall_score)
        st.success(f"🏆 **Winner:** {best_team.team_name} with a score of {best_team.overall_score:.3f}")
    
    @staticmethod
    def render_evaluation_history(evaluations: List[EvaluationResult]):
        """Render evaluation history and trends"""
        st.markdown("### 📈 Evaluation History")
        
        if len(evaluations) < 2:
            st.info("Need multiple evaluations to show trends")
            return
        
        # Sort by timestamp
        evaluations_sorted = sorted(evaluations, key=lambda x: x.timestamp)
        
        # Create trend chart
        history_data = []
        for evaluation in evaluations_sorted:
            history_data.append({
                'Timestamp': evaluation.timestamp,
                'Team': evaluation.team_name,
                'Overall Score': evaluation.overall_score,
                'Grade': evaluation.grade
            })
        
        df_history = pd.DataFrame(history_data)
        
        fig = px.line(
            df_history,
            x='Timestamp',
            y='Overall Score',
            color='Team',
            title="Team Performance Over Time",
            markers=True
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    @staticmethod
    def export_evaluation_report(evaluation: EvaluationResult) -> str:
        """Generate exportable evaluation report"""
        report = f"""
# Team Evaluation Report

## Team: {evaluation.team_name}
**Evaluation Date:** {evaluation.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Overall Score:** {evaluation.overall_score:.3f} ({evaluation.grade})

## Performance Summary
- **Test Success Rate:** {len([r for r in evaluation.test_results if r.success])}/{len(evaluation.test_results)} ({(len([r for r in evaluation.test_results if r.success]) / len(evaluation.test_results) * 100):.1f}%)
- **Average Response Time:** {sum(r.execution_time for r in evaluation.test_results) / len(evaluation.test_results):.1f}s
- **Evaluation Duration:** {evaluation.evaluation_time:.1f}s

## Dimension Scores
"""
        
        for dimension, score in evaluation.dimension_scores.items():
            report += f"- **{dimension.value.replace('_', ' ').title()}:** {score:.3f}\n"
        
        report += "\n## Test Results\n"
        for i, result in enumerate(evaluation.test_results, 1):
            status = "✅ PASS" if result.success else "❌ FAIL"
            report += f"{i}. **{result.scenario_name}** - {status} ({result.execution_time:.1f}s)\n"
            if result.error_message:
                report += f"   Error: {result.error_message}\n"
        
        if evaluation.recommendations:
            report += "\n## Recommendations\n"
            for i, rec in enumerate(evaluation.recommendations, 1):
                report += f"{i}. {rec}\n"
        
        if evaluation.warnings:
            report += "\n## Warnings\n"
            for i, warning in enumerate(evaluation.warnings, 1):
                report += f"{i}. {warning}\n"
        
        return report