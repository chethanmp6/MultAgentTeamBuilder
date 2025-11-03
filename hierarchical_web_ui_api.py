"""
Enhanced Streamlit Web UI for Hierarchical Agent Teams - API Version
Uses REST APIs instead of direct function calls
"""
import streamlit as st
import yaml
import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path

from ui.api_client import get_api_client, handle_api_error, APIError

# Page configuration
st.set_page_config(
    page_title="Hierarchical Agent Teams (API)",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS (keeping the same styling)
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        width: 22% !important;
        min-width: 300px !important;
    }
    .team-card {
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
    }
    .worker-card {
        border: 1px solid #ccc;
        border-radius: 6px;
        padding: 0.5rem;
        margin: 0.25rem;
        background-color: #ffffff;
        border-left: 4px solid #007bff;
    }
    .coordinator-card {
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #e8f5e8;
    }
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    .status-active { background-color: #28a745; }
    .status-inactive { background-color: #dc3545; }
    input, textarea, select {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'api_client' not in st.session_state:
        st.session_state.api_client = get_api_client()
    if 'current_team_id' not in st.session_state:
        st.session_state.current_team_id = None
    if 'teams_list' not in st.session_state:
        st.session_state.teams_list = []
    if 'execution_history' not in st.session_state:
        st.session_state.execution_history = []

@handle_api_error
def load_teams_list():
    """Load teams from API"""
    try:
        response = st.session_state.api_client.list_teams()
        st.session_state.teams_list = response.get('teams', [])
        return response
    except Exception as e:
        st.error(f"Failed to load teams: {e}")
        return None

@handle_api_error
def create_team_from_template(template_id: str, team_name: str):
    """Create a team from template using API"""
    try:
        response = st.session_state.api_client.create_team(
            name=team_name,
            description=f"Team created from template: {template_id}",
            template_id=template_id
        )
        if response:
            st.session_state.current_team_id = response['id']
            st.success(f"✅ Team '{team_name}' created successfully!")
            load_teams_list()  # Refresh teams list
        return response
    except Exception as e:
        st.error(f"Failed to create team: {e}")
        return None

@handle_api_error
def execute_team_task(team_id: str, input_text: str):
    """Execute a task on a team using API"""
    try:
        response = st.session_state.api_client.execute_task(
            team_id=team_id,
            input_text=input_text
        )
        if response:
            execution_id = response['execution_id']
            st.session_state.execution_history.append({
                'execution_id': execution_id,
                'team_id': team_id,
                'input_text': input_text,
                'timestamp': datetime.now()
            })
        return response
    except Exception as e:
        st.error(f"Failed to execute task: {e}")
        return None

@handle_api_error
def get_execution_result(execution_id: str):
    """Get execution results using API"""
    try:
        return st.session_state.api_client.get_execution(execution_id)
    except Exception as e:
        st.error(f"Failed to get execution result: {e}")
        return None

def render_api_status():
    """Render API connection status"""
    st.sidebar.subheader("🔌 API Status")
    
    try:
        health = st.session_state.api_client.health_check()
        if health:
            st.sidebar.success("✅ API Connected")
            st.sidebar.metric("Active Teams", health.get('teams_count', 0))
            st.sidebar.metric("Active Executions", health.get('active_executions', 0))
        else:
            st.sidebar.error("❌ API Unavailable")
    except Exception as e:
        st.sidebar.error("❌ API Connection Failed")
        st.sidebar.caption(f"Error: {str(e)}")

def render_template_selector():
    """Render template selection in sidebar"""
    st.sidebar.subheader("📚 Templates")
    
    try:
        templates_response = st.session_state.api_client.list_templates()
        templates = templates_response.get('templates', [])
        
        if templates:
            template_options = {f"{t['name']} ({t['id']})": t['id'] for t in templates}
            selected_template = st.sidebar.selectbox(
                "Choose Template:",
                options=["Select template..."] + list(template_options.keys())
            )
            
            if selected_template != "Select template...":
                template_id = template_options[selected_template]
                
                # Show template details
                template_details = st.session_state.api_client.get_template(template_id)
                if template_details:
                    template_info = template_details['template']
                    st.sidebar.caption(f"📝 {template_info['description']}")
                    st.sidebar.caption(f"Teams: {template_info.get('team_count', 0)}")
                    st.sidebar.caption(f"Workers: {template_info.get('worker_count', 0)}")
                
                # Team creation form
                with st.sidebar.form(f"create_team_{template_id}"):
                    team_name = st.text_input("Team Name", value=f"Team from {template_id}")
                    if st.form_submit_button("🚀 Create Team"):
                        if team_name:
                            create_team_from_template(template_id, team_name)
                        else:
                            st.error("Please enter a team name")
        else:
            st.sidebar.info("No templates available")
    
    except Exception as e:
        st.sidebar.error(f"Failed to load templates: {e}")

def render_teams_management():
    """Render teams management interface"""
    st.subheader("🏢 Team Management")
    
    # Load teams
    load_teams_list()
    
    if st.session_state.teams_list:
        # Team selection
        team_options = {f"{team['name']} ({team['id']})": team['id'] for team in st.session_state.teams_list}
        selected_team = st.selectbox(
            "Select Team:",
            options=["Select team..."] + list(team_options.keys())
        )
        
        if selected_team != "Select team...":
            team_id = team_options[selected_team]
            st.session_state.current_team_id = team_id
            
            # Get team details
            try:
                team_details = st.session_state.api_client.get_team(team_id)
                if team_details:
                    render_team_details(team_details)
            except Exception as e:
                st.error(f"Failed to load team details: {e}")
    else:
        st.info("No teams available. Create a team from a template using the sidebar.")

def render_team_details(team_details: Dict[str, Any]):
    """Render detailed team information"""
    st.write("### Team Information")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Team Name", team_details['name'])
    with col2:
        st.metric("Status", team_details['status'])
    with col3:
        st.metric("Created", team_details['created_at'][:10])
    
    # Hierarchy information
    if team_details.get('hierarchy_info'):
        hierarchy = team_details['hierarchy_info']
        
        st.write("### Team Hierarchy")
        
        # Coordinator
        coordinator = hierarchy.get('coordinator', {})
        st.markdown(f"""
        <div class="coordinator-card">
            <span class="status-indicator status-active"></span>
            <strong>👑 {coordinator.get('name', 'Coordinator')}</strong><br>
            <small>Team Coordinator</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Teams
        teams = hierarchy.get('teams', {})
        for team_name, team_info in teams.items():
            st.markdown(f"""
            <div class="team-card">
                <span class="status-indicator status-active"></span>
                <strong>👥 {team_name}</strong><br>
                <small>Supervisor: {team_info.get('supervisor_name', 'Unknown')}</small><br>
                <small>Workers: {team_info.get('worker_count', 0)}</small>
            </div>
            """, unsafe_allow_html=True)
            
            # Workers
            for worker in team_info.get('workers', []):
                st.markdown(f"""
                <div class="worker-card" style="margin-left: 20px;">
                    <span class="status-indicator status-active"></span>
                    <strong>🤖 {worker.get('name', 'Worker')}</strong> <em>({worker.get('role', 'worker')})</em><br>
                    <small>{worker.get('description', 'No description')}</small>
                </div>
                """, unsafe_allow_html=True)

def render_task_execution():
    """Render task execution interface"""
    st.subheader("🚀 Task Execution")
    
    if not st.session_state.current_team_id:
        st.warning("Please select a team first")
        return
    
    # Task input
    with st.form("task_execution"):
        task_input = st.text_area(
            "Enter your task:",
            placeholder="Describe the task you want the hierarchical team to handle...",
            height=100
        )
        
        col1, col2 = st.columns([3, 1])
        with col1:
            execute_button = st.form_submit_button("🚀 Execute Task", use_container_width=True)
        with col2:
            if st.form_submit_button("🗑️ Clear History"):
                st.session_state.execution_history = []
                st.rerun()
    
    if execute_button and task_input:
        with st.spinner("Executing task..."):
            response = execute_team_task(st.session_state.current_team_id, task_input)
            
            if response:
                execution_id = response['execution_id']
                st.success(f"✅ Task submitted! Execution ID: {execution_id}")
                
                # Poll for results
                with st.spinner("Waiting for results..."):
                    import time
                    max_wait = 60  # Maximum wait time in seconds
                    wait_time = 0
                    
                    while wait_time < max_wait:
                        result = get_execution_result(execution_id)
                        if result and result.get('status', {}).get('status') == 'completed':
                            st.write("### 📋 Execution Results")
                            
                            if result.get('result'):
                                result_data = result['result']
                                st.write(f"**Response:** {result_data.get('response', 'No response')}")
                                
                                if result_data.get('execution_time_seconds'):
                                    st.metric("Execution Time", f"{result_data['execution_time_seconds']:.2f}s")
                                
                                with st.expander("📊 Detailed Results"):
                                    st.json(result_data)
                            break
                        elif result and result.get('status', {}).get('status') == 'failed':
                            st.error(f"❌ Execution failed: {result.get('status', {}).get('error_message', 'Unknown error')}")
                            break
                        
                        time.sleep(2)
                        wait_time += 2
                    
                    if wait_time >= max_wait:
                        st.warning("⏱️ Execution is taking longer than expected. Check execution history for updates.")

def render_execution_history():
    """Render execution history"""
    st.subheader("📈 Execution History")
    
    if st.session_state.execution_history:
        for i, execution in enumerate(reversed(st.session_state.execution_history[-10:])):  # Show last 10
            with st.expander(f"Execution {i+1}: {execution['input_text'][:50]}..."):
                st.write(f"**Execution ID:** {execution['execution_id']}")
                st.write(f"**Team ID:** {execution['team_id']}")
                st.write(f"**Input:** {execution['input_text']}")
                st.write(f"**Timestamp:** {execution['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                if st.button(f"🔍 Check Status", key=f"check_{execution['execution_id']}"):
                    result = get_execution_result(execution['execution_id'])
                    if result:
                        st.json(result)
    else:
        st.info("No execution history available")

def render_agent_library():
    """Render agent library interface"""
    st.subheader("🗂️ Agent Library")
    
    try:
        # Search form
        col1, col2 = st.columns([3, 1])
        with col1:
            search_query = st.text_input("Search agents", placeholder="Search by name, capability, or role...")
        with col2:
            search_button = st.button("🔍 Search")
        
        # Load agents
        if search_button or not search_query:
            agents_response = st.session_state.api_client.list_agents(
                query=search_query if search_query else None,
                limit=20
            )
            
            if agents_response and agents_response.get('agents'):
                agents = agents_response['agents']
                
                st.write(f"Found {len(agents)} agents")
                
                # Display agents in grid
                cols = st.columns(3)
                for i, agent in enumerate(agents):
                    with cols[i % 3]:
                        st.markdown(f"""
                        <div class="worker-card">
                            <h4>{agent['name']}</h4>
                            <p><small>{agent['description'][:100]}{'...' if len(agent['description']) > 100 else ''}</small></p>
                            <p><strong>Role:</strong> {agent['primary_role']}</p>
                            <p><strong>Capabilities:</strong> {len(agent.get('capabilities', []))}</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.info("No agents found")
    
    except Exception as e:
        st.error(f"Failed to load agent library: {e}")

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Main title
    st.title("🏢 Hierarchical Agent Teams (API Version)")
    st.write("Build and manage complex hierarchical agent teams using REST APIs")
    
    # Sidebar
    render_api_status()
    render_template_selector()
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🏗️ Team Management", 
        "🚀 Task Execution",
        "📈 Execution History",
        "🗂️ Agent Library"
    ])
    
    with tab1:
        render_teams_management()
    
    with tab2:
        render_task_execution()
    
    with tab3:
        render_execution_history()
    
    with tab4:
        render_agent_library()

if __name__ == "__main__":
    main()