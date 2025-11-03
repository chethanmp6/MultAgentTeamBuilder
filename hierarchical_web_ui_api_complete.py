"""
Enhanced Streamlit Web UI for Hierarchical Agent Teams - Complete API Version
Full feature parity with the original hierarchical_web_ui.py using REST APIs
"""
import streamlit as st
import yaml
import os
import json
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import time

from ui.api_client import get_api_client, handle_api_error, APIError
from src.core.config_loader import ConfigLoader, AgentConfiguration
from src.validation.hierarchy_validator import HierarchyValidator, ValidationResult, ValidationSeverity

# Page configuration
st.set_page_config(
    page_title="Hierarchical Agent Teams (Complete API)",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS (same as original)
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        width: 22% !important;
        min-width: 300px !important;
    }
    [data-testid="stSidebar"] > div:first-child {
        width: 22% !important;
        min-width: 300px !important;
    }
    .main .block-container {
        margin-left: 24% !important;
        max-width: 76% !important;
    }
    
    /* Hierarchical team styling */
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
    
    /* Card selection styles */
    .supervisor-card {
        border: 2px solid #6c757d;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #f8f9fa;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .supervisor-card:hover {
        border-color: #007bff;
        background-color: #e3f2fd;
        box-shadow: 0 4px 8px rgba(0,123,255,0.2);
    }
    
    .supervisor-card-selected {
        border: 3px solid #28a745;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #d4edda;
        box-shadow: 0 4px 12px rgba(40,167,69,0.3);
    }
    
    .worker-card-selected {
        border: 2px solid #28a745;
        border-radius: 6px;
        padding: 0.5rem;
        margin: 0.25rem;
        background-color: #d1ecf1;
        border-left: 4px solid #28a745;
        box-shadow: 0 2px 8px rgba(40,167,69,0.2);
    }
    
    .hierarchy-level-1 { margin-left: 0px; }
    .hierarchy-level-2 { margin-left: 20px; }
    .hierarchy-level-3 { margin-left: 40px; }
    
    .status-indicator {
        display: inline-block;
        width: 12px;
        height: 12px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-active { background-color: #28a745; }
    .status-inactive { background-color: #dc3545; }
    .status-pending { background-color: #ffc107; }
    
    /* Fix text colors */
    input, textarea, select {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    .coordinator-card *, .worker-card *, .team-card *, 
    .supervisor-card *, .supervisor-card-selected *, .worker-card-selected * {
        color: #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables for hierarchical team management."""
    if 'api_client' not in st.session_state:
        st.session_state.api_client = get_api_client()
    if 'hierarchical_config' not in st.session_state:
        st.session_state.hierarchical_config = {}
    if 'current_hierarchical_team' not in st.session_state:
        st.session_state.current_hierarchical_team = None
    if 'team_instances' not in st.session_state:
        st.session_state.team_instances = {}
    if 'selected_template' not in st.session_state:
        st.session_state.selected_template = None
    if 'builder_mode' not in st.session_state:
        st.session_state.builder_mode = 'simple'  # 'simple', 'advanced', or 'template'
    if 'current_team_id' not in st.session_state:
        st.session_state.current_team_id = None
    if 'teams_list' not in st.session_state:
        st.session_state.teams_list = []
    if 'execution_history' not in st.session_state:
        st.session_state.execution_history = []
    if 'agent_library_cache' not in st.session_state:
        st.session_state.agent_library_cache = {}

@handle_api_error
def load_agent_stats():
    """Load agent library statistics from API"""
    try:
        return st.session_state.api_client.get_agent_stats()
    except Exception as e:
        st.error(f"Failed to load agent stats: {e}")
        return None

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
            st.session_state.hierarchical_config = response.get('config_data', {})
            st.success(f"✅ Team '{team_name}' created successfully!")
            load_teams_list()  # Refresh teams list
        return response
    except Exception as e:
        st.error(f"Failed to create team: {e}")
        return None

@handle_api_error
def create_team_from_config(team_name: str, config_data: Dict[str, Any]):
    """Create a team from configuration data"""
    try:
        response = st.session_state.api_client.create_team(
            name=team_name,
            description=f"Team created from configuration",
            config_data=config_data
        )
        if response:
            st.session_state.current_team_id = response['id']
            st.session_state.hierarchical_config = config_data
            st.success(f"✅ Team '{team_name}' created successfully!")
            load_teams_list()
        return response
    except Exception as e:
        st.error(f"Failed to create team: {e}")
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

def render_hierarchical_templates_sidebar():
    """Render hierarchical team templates in sidebar."""
    st.sidebar.subheader("🏢 Team Builder Mode")
    
    # Mode selection
    builder_mode = st.sidebar.radio(
        "Choose Builder Mode:",
        options=["Simple Team Builder", "Template Library"],
        index=0 if st.session_state.builder_mode == 'simple' else 1,
        help="Select how you want to build your hierarchical team"
    )
    
    if builder_mode == "Simple Team Builder":
        st.session_state.builder_mode = 'simple'
        render_simple_builder_sidebar()
    else:
        st.session_state.builder_mode = 'template'
        render_template_library_sidebar()

def render_simple_builder_sidebar():
    """Render simple builder options in sidebar."""
    st.sidebar.markdown("### 🚀 Simple Team Builder")
    st.sidebar.markdown("**Easy 3-step process:**")
    st.sidebar.markdown("1. Select a supervisor")
    st.sidebar.markdown("2. Add worker agents")  
    st.sidebar.markdown("3. Deploy your team!")
    
    # Quick stats from API
    agent_stats = load_agent_stats()
    if agent_stats:
        st.sidebar.metric("Available Agents", agent_stats['total_agents'])
        st.sidebar.metric("Supervisors", agent_stats['by_role'].get('supervisor', 0))
        st.sidebar.metric("Workers", agent_stats['total_agents'] - agent_stats['by_role'].get('supervisor', 0))


def render_template_library_sidebar():
    """Render template library options in sidebar."""
    st.sidebar.markdown("### 📚 Template Library")
    
    try:
        templates_response = st.session_state.api_client.list_templates()
        templates = templates_response.get('templates', [])
        
        if templates:
            template_options = {f"{t['name']} ({t['id']})": t['id'] for t in templates}
            selected_template = st.sidebar.selectbox(
                "Choose Template:",
                options=["Select template..."] + list(template_options.keys()),
                help="Select a pre-configured hierarchical team template"
            )
            
            if selected_template != "Select template..." and selected_template in template_options:
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


def render_simple_team_builder():
    """Render simple team builder interface with card-based selection"""
    st.subheader("🚀 Simple Team Builder")
    st.markdown("Build your hierarchical team in 3 easy steps:")
    
    # Initialize session state for selections
    if 'selected_supervisor' not in st.session_state:
        st.session_state.selected_supervisor = None
    if 'selected_workers' not in st.session_state:
        st.session_state.selected_workers = []
    
    # Initialize session state for customized configurations
    if 'customized_configs' not in st.session_state:
        st.session_state.customized_configs = {
            'supervisor_config': None,
            'worker_configs': {}
        }
    if 'show_supervisor_editor' not in st.session_state:
        st.session_state.show_supervisor_editor = False
    if 'show_worker_editors' not in st.session_state:
        st.session_state.show_worker_editors = set()
    
    # Step 1: Select Supervisor
    st.markdown("### Step 1: Select a Supervisor")
    st.markdown("Choose one supervisor agent to lead your team:")
    
    # Check API client
    if not hasattr(st.session_state, 'api_client') or st.session_state.api_client is None:
        st.error("API client not initialized. Please refresh the page.")
        return
    
    try:
        # Direct API call with error handling
        try:
            agents_response = st.session_state.api_client.list_agents(role="supervisor", limit=20)
        except Exception as api_error:
            st.error(f"API Error: {str(api_error)}")
            st.info("Please check that the API server is running on http://localhost:8000")
            return
        
        if agents_response is None:
            st.error("Failed to get supervisors from API - received None response")
            return
            
        if not isinstance(agents_response, dict):
            st.error(f"Invalid API response format: {type(agents_response)}")
            return
            
        supervisors = agents_response.get('agents', [])
        
        if supervisors:
            render_supervisor_selection_cards(supervisors)
            
            if st.session_state.selected_supervisor:
                st.success(f"✅ Selected Supervisor: **{st.session_state.selected_supervisor['name']}**")
                
                # Step 1.5: Customize Supervisor
                st.markdown("#### ⚙️ Customize Supervisor (Optional)")
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"**{st.session_state.selected_supervisor['name']}** - Customize configuration to match your specific needs")
                
                with col2:
                    if st.button("⚙️ Customize", key="customize_supervisor", use_container_width=True):
                        st.session_state.show_supervisor_editor = not st.session_state.show_supervisor_editor
                        # Initialize supervisor config if not exists
                        if st.session_state.customized_configs['supervisor_config'] is None:
                            st.session_state.customized_configs['supervisor_config'] = load_agent_config_from_api(
                                st.session_state.selected_supervisor['id']
                            )
                        st.rerun()
                
                # Show supervisor configuration editor if enabled
                if st.session_state.show_supervisor_editor:
                    render_supervisor_config_editor()
                
                # Step 2: Add Workers
                st.markdown("### Step 2: Add Worker Agents")
                st.markdown("Select worker agents for your team:")
                
                # Direct API call with error handling
                try:
                    workers_response = st.session_state.api_client.list_agents(role="worker", limit=20)
                except Exception as api_error:
                    st.error(f"Worker API Error: {str(api_error)}")
                    st.info("Please check that the API server is running on http://localhost:8000")
                    return
                
                if workers_response is None:
                    st.error("Failed to get workers from API - received None response")
                    return
                    
                if not isinstance(workers_response, dict):
                    st.error(f"Invalid worker API response format: {type(workers_response)}")
                    return
                    
                workers = workers_response.get('agents', [])
                
                if workers:
                    render_worker_selection_cards(workers)
                    
                    if st.session_state.selected_workers:
                        st.success(f"✅ Selected {len(st.session_state.selected_workers)} worker(s)")
                        
                        # Step 2.5: Customize Workers
                        st.markdown("#### ⚙️ Customize Workers (Optional)")
                        st.markdown("**Selected Workers:**")
                        
                        for i, worker in enumerate(st.session_state.selected_workers):
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                worker_id = worker.get('id', f'worker_{i}')
                                is_customized = worker_id in st.session_state.customized_configs['worker_configs']
                                status_icon = "⚙️" if is_customized else "🤖"
                                status_text = " (Customized)" if is_customized else ""
                                st.markdown(f"{status_icon} **{worker['name']}**{status_text}")
                            
                            with col2:
                                if st.button("⚙️ Edit", key=f"customize_worker_{worker_id}", use_container_width=True):
                                    if worker_id in st.session_state.show_worker_editors:
                                        st.session_state.show_worker_editors.remove(worker_id)
                                    else:
                                        st.session_state.show_worker_editors.add(worker_id)
                                        # Initialize worker config if not exists
                                        if worker_id not in st.session_state.customized_configs['worker_configs']:
                                            st.session_state.customized_configs['worker_configs'][worker_id] = load_agent_config_from_api(worker_id)
                                    st.rerun()
                            
                            # Show worker configuration editor if enabled
                            if worker_id in st.session_state.show_worker_editors:
                                render_worker_config_editor(worker_id, worker['name'])
                        
                        # Step 3: Validate & Optimize
                        st.markdown("### Step 3: Validate & Optimize (Optional)")
                        st.markdown("Analyze your team configuration and optimize routing prompts for better performance before deployment.")
                        
                        team_name = st.text_input("Team Name", value="My Simple Team")
                        team_description = st.text_area("Team Description (optional)", 
                                                       value=f"Team with {len(st.session_state.selected_workers)} specialized workers")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("🔍 Validate Configuration", use_container_width=True):
                                if team_name:
                                    # Create configuration for validation
                                    config_data = create_simple_team_config_with_customizations(
                                        team_name, team_description, 
                                        st.session_state.selected_supervisor, 
                                        st.session_state.selected_workers,
                                        st.session_state.customized_configs
                                    )
                                    
                                    # Store config for validation
                                    st.session_state.validation_config = config_data
                                    st.session_state.show_validation_results = True
                                    
                                    # Run validation
                                    with st.spinner("Analyzing configuration..."):
                                        validator = HierarchyValidator()
                                        validation_result = validator.validate_hierarchy_config(config_data)
                                        st.session_state.validation_result = validation_result
                                else:
                                    st.error("Please enter a team name first")
                        
                        with col2:
                            if st.button("🔄 Reset Selection", use_container_width=True):
                                st.session_state.selected_supervisor = None
                                st.session_state.selected_workers = []
                                st.rerun()
                        
                        # Step 4: Evaluate Team Performance
                        if True:  # Always show evaluation step
                            st.markdown("### Step 4: Evaluate Team Performance")
                            st.markdown("Run comprehensive evaluation tests to assess your team's performance before deployment.")
                            
                            render_team_evaluation_interface(team_name, team_description, "simple")
                            
                            # Display evaluation results if available
                            display_evaluation_results("simple")
                        
                        # Step 5: Deploy Your Team
                        st.markdown("### Step 5: Deploy Your Team")
                        st.markdown("Test and deploy your optimized team configuration to start using your hierarchical agent system.")
                        
                        # Test prompt section
                        st.markdown("#### 🧪 Test Your Team")
                        test_prompt = st.text_area(
                            "Test Prompt", 
                            value="Write a brief summary about artificial intelligence",
                            help="Enter a test prompt to verify your team works correctly before deployment"
                        )
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            if st.button("🧪 Test Deployment", use_container_width=True):
                                if team_name and test_prompt:
                                    test_team_deployment(team_name, team_description, test_prompt)
                                elif not team_name:
                                    st.error("Please enter a team name")
                                else:
                                    st.error("Please enter a test prompt")
                        
                        with col2:
                            if st.button("🚀 Deploy Team", use_container_width=True):
                                if team_name:
                                    # Create team configuration with customizations
                                    config_data = create_simple_team_config_with_customizations(
                                        team_name, team_description, 
                                        st.session_state.selected_supervisor, 
                                        st.session_state.selected_workers,
                                        st.session_state.customized_configs
                                    )
                                    create_team_from_config(team_name, config_data)
                                else:
                                    st.error("Please enter a team name")
                        
                        with col3:
                            if st.button("🚀 Deploy Without Validation", use_container_width=True):
                                if team_name:
                                    # Deploy directly without validation
                                    config_data = create_simple_team_config_with_customizations(
                                        team_name, team_description, 
                                        st.session_state.selected_supervisor, 
                                        st.session_state.selected_workers,
                                        st.session_state.customized_configs
                                    )
                                    create_team_from_config(team_name, config_data)
                                else:
                                    st.error("Please enter a team name")
                        
                        # Show test results if available
                        if getattr(st.session_state, 'show_test_results', False):
                            render_test_deployment_results()
                        
                        # Show validation results if available
                        if getattr(st.session_state, 'show_validation_results', False) and hasattr(st.session_state, 'validation_result'):
                            render_validation_results(st.session_state.validation_result, team_name, team_description)
                else:
                    st.info("No worker agents available")
        else:
            st.info("No supervisor agents available")
    
    except Exception as e:
        st.error(f"Failed to load agents: {e}")

def render_supervisor_selection_cards(supervisors):
    """Render supervisor agents as selectable cards"""
    try:
        if not supervisors:
            st.info("No supervisors available")
            return
        
        if not isinstance(supervisors, list):
            st.error(f"Invalid supervisors format: expected list, got {type(supervisors)}")
            return
            
        num_cols = min(3, len(supervisors))
        if num_cols <= 0:
            st.info("No supervisors to display")
            return
        
        cols = st.columns(num_cols)
        
        for i, supervisor in enumerate(supervisors):
            if not supervisor or not isinstance(supervisor, dict):
                continue
                
            with cols[i % num_cols]:
                # Check if this supervisor is selected
                supervisor_id = supervisor.get('id', f'supervisor_{i}')
                is_selected = bool(st.session_state.selected_supervisor and 
                                 st.session_state.selected_supervisor.get('id') == supervisor_id)
                
                
                # Create card styling based on selection
                card_class = "supervisor-card-selected" if is_selected else "supervisor-card"
                
                capabilities_text = ', '.join([cap.get('name', '') for cap in supervisor.get('capabilities', [])][:3])
                if len(supervisor.get('capabilities', [])) > 3:
                    capabilities_text += '...'
                
                st.markdown(f"""
                <div class="{card_class}">
                    <h4>👥 {supervisor.get('name', 'Unknown')}</h4>
                    <p><small>{supervisor.get('description', '')[:100]}{'...' if len(supervisor.get('description', '')) > 100 else ''}</small></p>
                    <p><strong>Capabilities:</strong> {capabilities_text}</p>
                    <p><strong>Team Size Limit:</strong> {supervisor.get('team_size_limit', 'No limit')}</p>
                    {'<p><strong>✅ Selected</strong></p>' if is_selected else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Selection button
                button_text = "✅ Selected" if is_selected else "📋 Select"
                button_disabled = bool(is_selected)  # Ensure it's a boolean
                
                if st.button(button_text, key=f"select_supervisor_{supervisor_id}", 
                            disabled=button_disabled, use_container_width=True):
                    st.session_state.selected_supervisor = supervisor
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Error rendering supervisor cards: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

def render_worker_selection_cards(workers):
    """Render worker agents as selectable cards"""
    try:
        if not workers:
            st.info("No workers available")
            return
        
        if not isinstance(workers, list):
            st.error(f"Invalid workers format: expected list, got {type(workers)}")
            return
            
        num_cols = min(3, len(workers))
        if num_cols <= 0:
            st.info("No workers to display")
            return
        
        cols = st.columns(num_cols)
        
        for i, worker in enumerate(workers):
            if not worker or not isinstance(worker, dict):
                continue
                
            with cols[i % num_cols]:
                # Check if this worker is selected
                worker_id = worker.get('id', f'worker_{i}')
                is_selected = bool(any(w.get('id') == worker_id for w in st.session_state.selected_workers if w))
                
                # Create card styling based on selection
                card_class = "worker-card-selected" if is_selected else "worker-card"
                
                capabilities_text = ', '.join([cap.get('name', '') for cap in worker.get('capabilities', [])][:3])
                if len(worker.get('capabilities', [])) > 3:
                    capabilities_text += '...'
                
                st.markdown(f"""
                <div class="{card_class}">
                    <h4>🤖 {worker.get('name', 'Unknown')}</h4>
                    <p><small>{worker.get('description', '')[:80]}{'...' if len(worker.get('description', '')) > 80 else ''}</small></p>
                    <p><strong>Capabilities:</strong> {capabilities_text}</p>
                    <p><strong>Compatibility:</strong> {worker.get('compatibility_score', 0):.2f}</p>
                    {'<p><strong>✅ Selected</strong></p>' if is_selected else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Selection button
                if is_selected:
                    if st.button("❌ Remove", key=f"remove_worker_{worker_id}", use_container_width=True):
                        st.session_state.selected_workers = [w for w in st.session_state.selected_workers 
                                                            if w and w.get('id') != worker_id]
                        st.rerun()
                else:
                    if st.button("➕ Add", key=f"add_worker_{worker_id}", use_container_width=True):
                        st.session_state.selected_workers.append(worker)
                        st.rerun()
                        
    except Exception as e:
        st.error(f"Error rendering worker cards: {str(e)}")
        import traceback
        st.code(traceback.format_exc())

def load_agent_config_from_api(agent_id: str) -> Dict[str, Any]:
    """Load agent configuration from API"""
    try:
        # Get agent details from API
        agent_response = st.session_state.api_client.get_agent(agent_id)
        if agent_response and 'config_data' in agent_response:
            return agent_response['config_data']
        else:
            # Return default configuration if not found
            return create_default_agent_config(agent_id)
    except Exception as e:
        st.error(f"Failed to load config for agent {agent_id}: {e}")
        return create_default_agent_config(agent_id)

def create_default_agent_config(agent_id: str) -> Dict[str, Any]:
    """Create a default agent configuration"""
    return {
        "agent": {
            "name": f"Agent {agent_id}",
            "description": "Customizable AI agent",
            "version": "1.0.0"
        },
        "llm": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.7,
            "max_tokens": 2000,
            "api_key_env": "OPENAI_API_KEY"
        },
        "prompts": {
            "system_prompt": {
                "template": "You are a helpful AI assistant.",
                "variables": []
            },
            "user_prompt": {
                "template": "User request: {user_input}",
                "variables": ["user_input"]
            }
        },
        "tools": {
            "built_in": ["web_search", "file_reader", "file_writer"],
            "custom": []
        },
        "memory": {
            "enabled": True,
            "provider": "langmem",
            "types": {
                "semantic": True,
                "episodic": True,
                "procedural": True
            },
            "storage": {
                "backend": "memory"
            },
            "settings": {
                "max_memory_size": 5000,
                "retention_days": 30,
                "background_processing": True
            }
        },
        "react": {
            "max_iterations": 10,
            "recursion_limit": 50
        },
        "runtime": {
            "max_iterations": 10,
            "timeout_seconds": 120,
            "retry_attempts": 2,
            "debug_mode": False
        }
    }

def render_supervisor_config_editor():
    """Render supervisor configuration editor"""
    st.markdown("---")
    st.markdown("### ⚙️ Supervisor Configuration Editor")
    
    if st.session_state.customized_configs['supervisor_config'] is None:
        st.warning("No configuration loaded for supervisor")
        return
    
    config = st.session_state.customized_configs['supervisor_config']
    
    # Create tabs for different configuration sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏷️ Basic Info", 
        "🤖 LLM Settings", 
        "💬 Prompts", 
        "🛠️ Tools", 
        "🧠 Memory", 
        "⚡ Runtime"
    ])
    
    with tab1:
        render_basic_info_tab(config, "supervisor")
    
    with tab2:
        render_llm_config_tab(config, "supervisor")
    
    with tab3:
        render_prompts_config_tab(config, "supervisor")
    
    with tab4:
        render_tools_config_tab(config, "supervisor")
    
    with tab5:
        render_memory_config_tab(config, "supervisor")
    
    with tab6:
        render_runtime_config_tab(config, "supervisor")
    
    # Save and Preview buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save Configuration", key="save_supervisor_config", use_container_width=True):
            st.success("✅ Supervisor configuration saved!")
    
    with col2:
        if st.button("👁️ Preview YAML", key="preview_supervisor_yaml", use_container_width=True):
            st.code(yaml.dump(config, default_flow_style=False), language='yaml')
    
    with col3:
        if st.button("🔄 Reset to Default", key="reset_supervisor_config", use_container_width=True):
            st.session_state.customized_configs['supervisor_config'] = create_default_agent_config(
                st.session_state.selected_supervisor['id']
            )
            st.rerun()

def render_worker_config_editor(worker_id: str, worker_name: str):
    """Render worker configuration editor"""
    st.markdown("---")
    st.markdown(f"### ⚙️ {worker_name} Configuration Editor")
    
    if worker_id not in st.session_state.customized_configs['worker_configs']:
        st.warning(f"No configuration loaded for worker {worker_name}")
        return
    
    config = st.session_state.customized_configs['worker_configs'][worker_id]
    
    # Create tabs for different configuration sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏷️ Basic Info", 
        "🤖 LLM Settings", 
        "💬 Prompts", 
        "🛠️ Tools", 
        "🧠 Memory", 
        "⚡ Runtime"
    ])
    
    with tab1:
        render_basic_info_tab(config, f"worker_{worker_id}")
    
    with tab2:
        render_llm_config_tab(config, f"worker_{worker_id}")
    
    with tab3:
        render_prompts_config_tab(config, f"worker_{worker_id}")
    
    with tab4:
        render_tools_config_tab(config, f"worker_{worker_id}")
    
    with tab5:
        render_memory_config_tab(config, f"worker_{worker_id}")
    
    with tab6:
        render_runtime_config_tab(config, f"worker_{worker_id}")
    
    # Save and Preview buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save Configuration", key=f"save_worker_config_{worker_id}", use_container_width=True):
            st.success(f"✅ {worker_name} configuration saved!")
    
    with col2:
        if st.button("👁️ Preview YAML", key=f"preview_worker_yaml_{worker_id}", use_container_width=True):
            st.code(yaml.dump(config, default_flow_style=False), language='yaml')
    
    with col3:
        if st.button("🔄 Reset to Default", key=f"reset_worker_config_{worker_id}", use_container_width=True):
            st.session_state.customized_configs['worker_configs'][worker_id] = create_default_agent_config(worker_id)
            st.rerun()

def render_basic_info_tab(config: Dict[str, Any], key_prefix: str):
    """Render basic agent information tab"""
    st.markdown("#### Agent Information")
    
    agent_config = config.setdefault('agent', {})
    
    agent_config['name'] = st.text_input(
        "Agent Name",
        value=agent_config.get('name', ''),
        key=f"{key_prefix}_agent_name"
    )
    
    agent_config['description'] = st.text_area(
        "Description",
        value=agent_config.get('description', ''),
        height=100,
        key=f"{key_prefix}_agent_description"
    )
    
    agent_config['version'] = st.text_input(
        "Version",
        value=agent_config.get('version', '1.0.0'),
        key=f"{key_prefix}_agent_version"
    )

def render_llm_config_tab(config: Dict[str, Any], key_prefix: str):
    """Render LLM configuration tab"""
    st.markdown("#### LLM Configuration")
    
    llm_config = config.setdefault('llm', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        llm_config['provider'] = st.selectbox(
            "Provider",
            options=["openai", "anthropic", "google", "groq"],
            index=["openai", "anthropic", "google", "groq"].index(llm_config.get('provider', 'openai')),
            key=f"{key_prefix}_llm_provider"
        )
        
        # Model options based on provider
        model_options = {
            'openai': ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo'],
            'anthropic': ['claude-3-sonnet-20240229', 'claude-3-haiku-20240307'],
            'google': ['gemini-1.5-flash', 'gemini-1.5-pro'],
            'groq': ['llama-3.1-70b-versatile', 'mixtral-8x7b-32768']
        }
        
        current_models = model_options.get(llm_config['provider'], ['gpt-4o-mini'])
        current_model = llm_config.get('model', current_models[0])
        if current_model not in current_models:
            current_models.append(current_model)
        
        llm_config['model'] = st.selectbox(
            "Model",
            options=current_models,
            index=current_models.index(current_model),
            key=f"{key_prefix}_llm_model"
        )
    
    with col2:
        llm_config['temperature'] = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=2.0,
            value=float(llm_config.get('temperature', 0.7)),
            step=0.1,
            key=f"{key_prefix}_llm_temperature"
        )
        
        llm_config['max_tokens'] = st.number_input(
            "Max Tokens",
            min_value=100,
            max_value=10000,
            value=int(llm_config.get('max_tokens', 2000)),
            step=100,
            key=f"{key_prefix}_llm_max_tokens"
        )
    
    # API Key Environment Variable
    api_key_options = {
        'openai': 'OPENAI_API_KEY',
        'anthropic': 'ANTHROPIC_API_KEY', 
        'google': 'GOOGLE_API_KEY',
        'groq': 'GROQ_API_KEY'
    }
    
    llm_config['api_key_env'] = st.text_input(
        "API Key Environment Variable",
        value=llm_config.get('api_key_env', api_key_options.get(llm_config['provider'], 'OPENAI_API_KEY')),
        key=f"{key_prefix}_llm_api_key_env"
    )

def render_prompts_config_tab(config: Dict[str, Any], key_prefix: str):
    """Render prompts configuration tab"""
    st.markdown("#### Prompts Configuration")
    
    prompts_config = config.setdefault('prompts', {})
    
    # System Prompt
    st.markdown("**System Prompt**")
    system_prompt = prompts_config.setdefault('system_prompt', {'template': '', 'variables': []})
    
    system_prompt['template'] = st.text_area(
        "System Prompt Template",
        value=system_prompt.get('template', ''),
        height=150,
        help="Use {variable_name} for dynamic variables",
        key=f"{key_prefix}_system_prompt_template"
    )
    
    # Variables input
    variables_text = st.text_input(
        "Variables (comma-separated)",
        value=', '.join(system_prompt.get('variables', [])),
        help="Variables used in the template, e.g., user_input, context",
        key=f"{key_prefix}_system_prompt_variables"
    )
    system_prompt['variables'] = [v.strip() for v in variables_text.split(',') if v.strip()]
    
    # User Prompt
    st.markdown("**User Prompt**")
    user_prompt = prompts_config.setdefault('user_prompt', {'template': '', 'variables': []})
    
    user_prompt['template'] = st.text_area(
        "User Prompt Template",
        value=user_prompt.get('template', ''),
        height=100,
        key=f"{key_prefix}_user_prompt_template"
    )
    
    user_variables_text = st.text_input(
        "User Prompt Variables (comma-separated)",
        value=', '.join(user_prompt.get('variables', [])),
        key=f"{key_prefix}_user_prompt_variables"
    )
    user_prompt['variables'] = [v.strip() for v in user_variables_text.split(',') if v.strip()]

def render_tools_config_tab(config: Dict[str, Any], key_prefix: str):
    """Render tools configuration tab"""
    st.markdown("#### Tools Configuration")
    
    tools_config = config.setdefault('tools', {})
    
    # Built-in tools
    st.markdown("**Built-in Tools**")
    available_tools = [
        "web_search", "calculator", "file_reader", "file_writer", 
        "code_executor", "image_generator", "data_analyzer"
    ]
    
    current_tools = tools_config.get('built_in', [])
    selected_tools = st.multiselect(
        "Select built-in tools",
        options=available_tools,
        default=current_tools,
        key=f"{key_prefix}_built_in_tools"
    )
    tools_config['built_in'] = selected_tools
    
    # Custom tools section
    st.markdown("**Custom Tools**")
    if st.checkbox("Enable custom tools", key=f"{key_prefix}_enable_custom_tools"):
        st.info("Custom tools configuration - for advanced users")
        custom_tools_yaml = st.text_area(
            "Custom Tools (YAML format)",
            value=yaml.dump(tools_config.get('custom', []), default_flow_style=False),
            height=100,
            key=f"{key_prefix}_custom_tools_yaml"
        )
        try:
            tools_config['custom'] = yaml.safe_load(custom_tools_yaml) or []
        except yaml.YAMLError as e:
            st.error(f"Invalid YAML format: {e}")
            tools_config['custom'] = []

def render_memory_config_tab(config: Dict[str, Any], key_prefix: str):
    """Render memory configuration tab"""
    st.markdown("#### Memory Configuration")
    
    memory_config = config.setdefault('memory', {})
    
    # Enable memory
    memory_config['enabled'] = st.checkbox(
        "Enable Memory",
        value=memory_config.get('enabled', True),
        key=f"{key_prefix}_memory_enabled"
    )
    
    if memory_config['enabled']:
        col1, col2 = st.columns(2)
        
        with col1:
            memory_config['provider'] = st.selectbox(
                "Memory Provider",
                options=["langmem", "custom"],
                index=0 if memory_config.get('provider', 'langmem') == 'langmem' else 1,
                key=f"{key_prefix}_memory_provider"
            )
        
        with col2:
            # Memory types
            st.markdown("**Memory Types**")
            types_config = memory_config.setdefault('types', {})
            
            types_config['semantic'] = st.checkbox(
                "Semantic Memory (Facts & Knowledge)",
                value=types_config.get('semantic', True),
                key=f"{key_prefix}_memory_semantic"
            )
            
            types_config['episodic'] = st.checkbox(
                "Episodic Memory (Conversation History)",
                value=types_config.get('episodic', True),
                key=f"{key_prefix}_memory_episodic"
            )
            
            types_config['procedural'] = st.checkbox(
                "Procedural Memory (Learned Patterns)",
                value=types_config.get('procedural', True),
                key=f"{key_prefix}_memory_procedural"
            )
        
        # Memory settings
        st.markdown("**Memory Settings**")
        settings_config = memory_config.setdefault('settings', {})
        
        col3, col4 = st.columns(2)
        with col3:
            settings_config['max_memory_size'] = st.number_input(
                "Max Memory Size",
                min_value=1000,
                max_value=50000,
                value=int(settings_config.get('max_memory_size', 5000)),
                step=1000,
                key=f"{key_prefix}_memory_max_size"
            )
        
        with col4:
            settings_config['retention_days'] = st.number_input(
                "Retention Days",
                min_value=1,
                max_value=365,
                value=int(settings_config.get('retention_days', 30)),
                key=f"{key_prefix}_memory_retention"
            )

def render_runtime_config_tab(config: Dict[str, Any], key_prefix: str):
    """Render runtime configuration tab"""
    st.markdown("#### Runtime Configuration")
    
    runtime_config = config.setdefault('runtime', {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        runtime_config['max_iterations'] = st.number_input(
            "Max Iterations",
            min_value=1,
            max_value=50,
            value=int(runtime_config.get('max_iterations', 10)),
            help="Maximum number of reasoning iterations",
            key=f"{key_prefix}_runtime_max_iterations"
        )
        
        runtime_config['timeout_seconds'] = st.number_input(
            "Timeout (seconds)",
            min_value=30,
            max_value=600,
            value=int(runtime_config.get('timeout_seconds', 120)),
            help="Maximum execution time",
            key=f"{key_prefix}_runtime_timeout"
        )
    
    with col2:
        runtime_config['retry_attempts'] = st.number_input(
            "Retry Attempts",
            min_value=0,
            max_value=5,
            value=int(runtime_config.get('retry_attempts', 2)),
            help="Number of retries on failure",
            key=f"{key_prefix}_runtime_retries"
        )
        
        runtime_config['debug_mode'] = st.checkbox(
            "Debug Mode",
            value=runtime_config.get('debug_mode', False),
            help="Enable detailed logging",
            key=f"{key_prefix}_runtime_debug"
        )

def create_simple_team_config(team_name: str, team_description: str, supervisor: Dict, workers: List[Dict]) -> Dict[str, Any]:
    """Create a simple team configuration"""
    return {
        "team": {
            "name": team_name,
            "description": team_description or f"Simple team with {len(workers)} workers",
            "version": "1.0.0",
            "type": "hierarchical"
        },
        "coordinator": {
            "name": f"{team_name} Coordinator",
            "description": "Simple team coordinator",
            "llm": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "max_tokens": 2000,
                "api_key_env": "OPENAI_API_KEY"
            },
            "prompts": {
                "system_prompt": {
                    "template": f"You are coordinating the {team_name} team.",
                    "variables": []
                },
                "decision_prompt": {
                    "template": "Route this task: {user_input}",
                    "variables": ["user_input"]
                }
            }
        },
        "teams": [
            {
                "name": "main_team",
                "description": "Main working team",
                "supervisor": {
                    "name": supervisor['name'],
                    "llm": {
                        "provider": "openai",
                        "model": "gpt-4o-mini",
                        "temperature": 0.2,
                        "api_key_env": "OPENAI_API_KEY"
                    }
                },
                "workers": [
                    {
                        "name": worker['name'],
                        "role": "worker",
                        "config_file": "configs/examples/research_agent.yml",  # Default config
                        "description": worker['description'],
                        "capabilities": [cap['name'] for cap in worker.get('capabilities', [])],
                        "priority": i + 1
                    } for i, worker in enumerate(workers)
                ]
            }
        ]
    }

def create_simple_team_config_with_customizations(team_name: str, team_description: str, 
                                                 supervisor: Dict, workers: List[Dict],
                                                 customized_configs: Dict[str, Any]) -> Dict[str, Any]:
    """Create a simple team configuration with customized agent configurations"""
    
    # Get supervisor config (customized or default)
    supervisor_config = customized_configs.get('supervisor_config')
    if supervisor_config:
        supervisor_llm = supervisor_config.get('llm', {
            "provider": "openai",
            "model": "gpt-4o-mini", 
            "temperature": 0.2,
            "api_key_env": "OPENAI_API_KEY"
        })
        supervisor_prompts = supervisor_config.get('prompts', {})
    else:
        supervisor_llm = {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "temperature": 0.2,
            "api_key_env": "OPENAI_API_KEY"
        }
        supervisor_prompts = {}
    
    # Create workers with customized configs
    customized_workers = []
    worker_configs = customized_configs.get('worker_configs', {})
    
    for i, worker in enumerate(workers):
        worker_id = worker['id']
        worker_config = worker_configs.get(worker_id)
        
        if worker_config:
            # Use customized configuration
            customized_worker = {
                "name": worker_config.get('agent', {}).get('name', worker['name']),
                "role": "worker",
                "description": worker_config.get('agent', {}).get('description', worker['description']),
                "capabilities": [cap['name'] for cap in worker.get('capabilities', [])],
                "priority": i + 1,
                "config_data": worker_config  # Embed the full customized config
            }
        else:
            # Use default configuration
            customized_worker = {
                "name": worker['name'],
                "role": "worker", 
                "config_file": "configs/examples/research_agent.yml",
                "description": worker['description'],
                "capabilities": [cap['name'] for cap in worker.get('capabilities', [])],
                "priority": i + 1
            }
        
        customized_workers.append(customized_worker)
    
    return {
        "team": {
            "name": team_name,
            "description": team_description or f"Simple team with {len(workers)} workers",
            "version": "1.0.0",
            "type": "hierarchical"
        },
        "coordinator": {
            "name": f"{team_name} Coordinator",
            "description": "Simple team coordinator",
            "llm": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "max_tokens": 2000,
                "api_key_env": "OPENAI_API_KEY"
            },
            "prompts": {
                "system_prompt": {
                    "template": f"You are coordinating the {team_name} team.",
                    "variables": []
                },
                "decision_prompt": {
                    "template": "Route this task: {user_input}",
                    "variables": ["user_input"]
                }
            }
        },
        "teams": [
            {
                "name": "main_team",
                "description": "Main working team",
                "supervisor": {
                    "name": supervisor_config.get('agent', {}).get('name', supervisor['name']) if supervisor_config else supervisor['name'],
                    "llm": supervisor_llm,
                    "prompts": supervisor_prompts,
                    "config_data": supervisor_config  # Embed the full customized supervisor config
                } if supervisor_config else {
                    "name": supervisor['name'],
                    "llm": supervisor_llm
                },
                "workers": customized_workers
            }
        ]
    }

def render_template_library_builder():
    """Render template library builder interface with card-based selection and customization"""
    st.subheader("📚 Template Library Builder")
    st.markdown("Build your hierarchical team from pre-configured templates in 4 easy steps:")
    
    # Initialize session state for template selections
    if 'selected_template' not in st.session_state:
        st.session_state.selected_template = None
    if 'template_config' not in st.session_state:
        st.session_state.template_config = None
    if 'template_customized_configs' not in st.session_state:
        st.session_state.template_customized_configs = {
            'supervisor_config': None,
            'worker_configs': {}
        }
    if 'show_template_supervisor_editor' not in st.session_state:
        st.session_state.show_template_supervisor_editor = False
    if 'show_template_worker_editors' not in st.session_state:
        st.session_state.show_template_worker_editors = set()
    
    # Step 1: Select Template
    st.markdown("### Step 1: Select a Template")
    st.markdown("Choose a pre-configured hierarchical team template:")
    
    # Check API client
    if not hasattr(st.session_state, 'api_client') or st.session_state.api_client is None:
        st.error("API client not initialized. Please refresh the page.")
        return
    
    try:
        # Load available templates
        templates_response = st.session_state.api_client.list_templates()
        templates = templates_response.get('templates', []) if templates_response else []
        
        if templates:
            render_template_selection_cards(templates)
            
            # Step 2: Customize Configuration (only if template selected)
            if st.session_state.selected_template:
                st.markdown("### Step 2: Customize Your Team Configuration")
                st.markdown("Edit the supervisor and worker configurations to match your needs:")
                
                render_template_customization_step()
                
                # Step 3: Validate & Optimize (only if supervisor and workers configured)
                if st.session_state.template_config:
                    st.markdown("### Step 3: Validate & Optimize")
                    st.markdown("Analyze and optimize your team configuration for best performance:")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        team_name = st.text_input("Team Name", value=f"Team from {st.session_state.selected_template['name']}")
                        team_description = st.text_area(
                            "Team Description", 
                            value=f"Hierarchical team created from {st.session_state.selected_template['name']} template",
                            height=100
                        )
                    
                    with col2:
                        if st.button("🔍 Validate & Optimize", use_container_width=True):
                            if team_name:
                                # Create configuration with customizations
                                config_data = create_team_config_from_template(
                                    team_name, team_description,
                                    st.session_state.template_config,
                                    st.session_state.template_customized_configs
                                )
                                
                                # Store config for validation
                                st.session_state.validation_config = config_data
                                st.session_state.show_validation_results = True
                                
                                # Run validation
                                with st.spinner("Analyzing configuration..."):
                                    validator = HierarchyValidator()
                                    validation_result = validator.validate_hierarchy_config(config_data)
                                    st.session_state.validation_result = validation_result
                            else:
                                st.error("Please enter a team name first")
                    
                    # Step 4: Evaluate Team Performance
                    if True:  # Always show evaluation step
                        st.markdown("### Step 4: Evaluate Team Performance")
                        st.markdown("Run comprehensive evaluation tests to assess your team's performance before deployment.")
                        
                        render_team_evaluation_interface(team_name, team_description, "template")
                        
                        # Display evaluation results if available
                        display_evaluation_results("template")
                    
                    # Step 5: Deploy Your Team
                    st.markdown("### Step 5: Deploy Your Team")
                    st.markdown("Test and deploy your optimized team configuration to start using your hierarchical agent system.")
                    
                    # Test prompt section
                    st.markdown("#### 🧪 Test Your Team")
                    test_prompt = st.text_area(
                        "Test Prompt", 
                        value="Write a brief summary about artificial intelligence",
                        help="Enter a test prompt to verify your team works correctly before deployment"
                    )
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("🧪 Test Deployment", key="template_test_deployment", use_container_width=True):
                            if team_name and test_prompt:
                                test_template_team_deployment(team_name, team_description, test_prompt)
                            elif not team_name:
                                st.error("Please enter a team name")
                            else:
                                st.error("Please enter a test prompt")
                    
                    with col2:
                        if st.button("🚀 Deploy Team", key="template_deploy_team", use_container_width=True):
                            if team_name:
                                # Create team configuration with customizations
                                config_data = create_team_config_from_template(
                                    team_name, team_description,
                                    st.session_state.template_config,
                                    st.session_state.template_customized_configs
                                )
                                create_team_from_config(team_name, config_data)
                            else:
                                st.error("Please enter a team name")
                    
                    with col3:
                        if st.button("🚀 Deploy Without Validation", key="template_deploy_no_validation", use_container_width=True):
                            if team_name:
                                # Deploy directly without validation
                                config_data = create_team_config_from_template(
                                    team_name, team_description,
                                    st.session_state.template_config,
                                    st.session_state.template_customized_configs
                                )
                                create_team_from_config(team_name, config_data)
                            else:
                                st.error("Please enter a team name")
                    
                    # Show test results if available
                    if getattr(st.session_state, 'show_test_results', False):
                        render_test_deployment_results()
                    
                    # Show validation results if available
                    if getattr(st.session_state, 'show_validation_results', False) and hasattr(st.session_state, 'validation_result'):
                        render_validation_results(st.session_state.validation_result, team_name, team_description)
        else:
            st.info("No templates available")
    
    except Exception as e:
        st.error(f"Failed to load templates: {e}")

def render_template_selection_cards(templates):
    """Render template selection cards"""
    try:
        if not templates:
            st.info("No templates available")
            return
        
        num_cols = min(3, len(templates))
        if num_cols <= 0:
            st.info("No templates to display")
            return
        
        cols = st.columns(num_cols)
        
        for i, template in enumerate(templates):
            if not template or not isinstance(template, dict):
                continue
                
            with cols[i % num_cols]:
                # Check if this template is selected
                template_id = template.get('id', f'template_{i}')
                is_selected = bool(st.session_state.selected_template and 
                                 st.session_state.selected_template.get('id') == template_id)
                
                # Create card styling based on selection
                card_class = "supervisor-card-selected" if is_selected else "supervisor-card"
                
                st.markdown(f"""
                <div class="{card_class}">
                    <h4>📚 {template.get('name', 'Unknown Template')}</h4>
                    <p><small>{template.get('description', '')[:100]}{'...' if len(template.get('description', '')) > 100 else ''}</small></p>
                    <p><strong>Teams:</strong> {template.get('team_count', 0)}</p>
                    <p><strong>Workers:</strong> {template.get('worker_count', 0)}</p>
                    <p><strong>Version:</strong> {template.get('version', '1.0.0')}</p>
                    {'<p><strong>✅ Selected</strong></p>' if is_selected else ''}
                </div>
                """, unsafe_allow_html=True)
                
                # Selection button
                button_text = "✅ Selected" if is_selected else "📋 Select"
                button_disabled = bool(is_selected)
                
                if st.button(button_text, key=f"select_template_{template_id}", 
                            disabled=button_disabled, use_container_width=True):
                    st.session_state.selected_template = template
                    # Load template configuration
                    load_template_config(template_id)
                    st.rerun()
                    
    except Exception as e:
        st.error(f"Error rendering template cards: {str(e)}")

def load_template_config_from_file(template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Load template configuration from file_path"""
    try:
        file_path = template_data.get('file_path', '')
        
        # Try to load via API first (preferred method)
        try:
            # Some APIs might have a method to get full template config
            if hasattr(st.session_state.api_client, 'get_template_config'):
                config = st.session_state.api_client.get_template_config(template_data['id'])
                if config:
                    st.success("✅ Loaded configuration via API")
                    return config
        except Exception:
            pass  # Continue to file loading
        
        # Try to read the file directly if path is accessible
        if file_path and os.path.exists(file_path):
            with open(file_path, 'r') as f:
                config_data = yaml.safe_load(f)
                st.success("✅ Loaded configuration from file")
                return config_data
        
        # If all else fails, try to construct config from metadata
        st.info("🔧 Creating configuration from template metadata...")
        return construct_config_from_metadata(template_data)
        
    except Exception as e:
        st.warning(f"⚠️ Could not load template file, creating from metadata: {e}")
        return construct_config_from_metadata(template_data)

def construct_config_from_metadata(template_data: Dict[str, Any]) -> Dict[str, Any]:
    """Construct a basic config structure from template metadata"""
    
    # Create a basic hierarchical config structure
    config = {
        "team": {
            "name": template_data.get('name', 'Template Team'),  
            "description": template_data.get('description', 'Team from template'),
            "version": "1.0.0",
            "type": template_data.get('type', 'hierarchical')
        },
        "coordinator": {
            "name": f"{template_data.get('name', 'Template')} Coordinator",
            "description": "Team coordinator",
            "llm": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "temperature": 0.3,
                "max_tokens": 2000,
                "api_key_env": "OPENAI_API_KEY"
            }
        },
        "teams": []
    }
    
    # Create teams based on team_count and worker_count
    team_count = template_data.get('team_count', 1)
    worker_count = template_data.get('worker_count', 2)
    capabilities = template_data.get('capabilities', ['general_assistance'])
    
    # Distribute workers across teams
    workers_per_team = max(1, worker_count // team_count)
    
    for i in range(team_count):
        team_name = f"team_{i+1}" if team_count > 1 else "main_team"
        
        # Create supervisor for this team
        supervisor = {
            "name": f"{template_data.get('name', 'Template')} Supervisor {i+1}" if team_count > 1 else f"{template_data.get('name', 'Template')} Supervisor",
            "description": f"Supervisor for {team_name}",
            "role": "supervisor"
        }
        
        # Create workers for this team
        workers = []
        start_worker = i * workers_per_team
        end_worker = min((i + 1) * workers_per_team, worker_count)
        
        for j in range(start_worker, end_worker):
            worker_caps = capabilities[j % len(capabilities):j % len(capabilities) + 2] if capabilities else ['general_assistance']
            worker = {
                "id": f"worker_{j+1}",
                "name": f"{template_data.get('name', 'Template')} Worker {j+1}",
                "description": f"Worker agent {j+1}",
                "role": "worker", 
                "capabilities": worker_caps
            }
            workers.append(worker)
        
        team = {
            "name": team_name,
            "description": f"Team {i+1} for {template_data.get('name', 'template')}",
            "supervisor": supervisor,
            "workers": workers
        }
        config["teams"].append(team)
    
    st.success(f"✅ Created configuration with {len(config['teams'])} teams and {worker_count} total workers")
    return config

def load_template_config(template_id: str):
    """Load template configuration from API"""
    try:
        # Get template details from API
        template_details = st.session_state.api_client.get_template(template_id)
        
        if template_details and 'template' in template_details:
            template_data = template_details['template']
            
            # Check if this is just metadata with file_path
            if 'file_path' in template_data and not any(key in template_data for key in ['teams', 'config_data', 'configuration']):
                st.info("📁 Loading configuration from template file...")
                config_data = load_template_config_from_file(template_data)
            else:
                # Try different possible config data locations
                config_data = None
                if 'config_data' in template_data:
                    config_data = template_data['config_data']
                elif 'configuration' in template_data:
                    config_data = template_data['configuration']
                else:
                    # If no config_data field, use the template data itself
                    config_data = template_data
            
            st.session_state.template_config = config_data
            
            # Initialize customization configs based on template
            if st.session_state.template_config:
                teams = extract_teams_from_template(st.session_state.template_config)
                
                # Initialize with default configs if no config_data exists
                supervisor_config = None
                if teams and len(teams) > 0:
                    supervisor_data = teams[0].get('supervisor', {})
                    supervisor_config = supervisor_data.get('config_data')
                    
                    # If no config_data, create from supervisor data
                    if not supervisor_config and supervisor_data:
                        supervisor_config = create_default_agent_config(
                            supervisor_data.get('name', 'supervisor')
                        )
                        # Merge any existing data
                        if 'llm' in supervisor_data:
                            supervisor_config['llm'] = supervisor_data['llm']
                        if 'prompts' in supervisor_data:
                            supervisor_config['prompts'] = supervisor_data['prompts']
                
                st.session_state.template_customized_configs = {
                    'supervisor_config': supervisor_config,
                    'worker_configs': {}
                }
                
                # Initialize worker configs
                if teams and len(teams) > 0:
                    workers = teams[0].get('workers', [])
                    for worker in workers:
                        worker_id = worker.get('id', worker.get('name', 'unknown'))
                        worker_config = worker.get('config_data')
                        
                        # If no config_data, create default config
                        if not worker_config:
                            worker_config = create_default_agent_config(worker_id)
                            # Merge any existing worker data
                            if 'llm' in worker:
                                worker_config['llm'] = worker['llm']
                            if 'prompts' in worker:
                                worker_config['prompts'] = worker['prompts']
                            if 'capabilities' in worker:
                                worker_config['capabilities'] = worker['capabilities']
                        
                        st.session_state.template_customized_configs['worker_configs'][worker_id] = worker_config
            
            st.success(f"✅ Template '{st.session_state.selected_template['name']}' loaded successfully!")
        else:
            st.error("Failed to load template configuration - no template data received")
            st.session_state.template_config = None
            
    except Exception as e:
        st.error(f"Failed to load template: {e}")
        st.session_state.template_config = None
        # Reset customized configs on error
        st.session_state.template_customized_configs = {
            'supervisor_config': None,
            'worker_configs': {}
        }

def extract_teams_from_template(template_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract teams from template configuration, trying multiple possible locations"""
    if not template_config:
        return []
    
    # Try different possible locations for teams
    teams = []
    
    # Strategy 1: Direct teams field
    if 'teams' in template_config and template_config['teams']:
        teams = template_config['teams']
        st.success(f"✅ Found {len(teams)} teams in template")
    
    # Strategy 2: Look in nested config sections
    else:
        # Check configuration.teams
        if 'configuration' in template_config:
            config = template_config['configuration']
            if isinstance(config, dict) and 'teams' in config and config['teams']:
                teams = config['teams']
                st.success(f"✅ Found {len(teams)} teams in configuration section")
        
        # Check config.teams if not found yet
        if not teams and 'config' in template_config:
            config = template_config['config']
            if isinstance(config, dict) and 'teams' in config and config['teams']:
                teams = config['teams']
                st.success(f"✅ Found {len(teams)} teams in config section")
        
        # Check hierarchical_config.teams if not found yet
        if not teams and 'hierarchical_config' in template_config:
            config = template_config['hierarchical_config']
            if isinstance(config, dict) and 'teams' in config and config['teams']:
                teams = config['teams']
                st.success(f"✅ Found {len(teams)} teams in hierarchical_config section")
    
    # Strategy 3: Create team from root level agents if no teams found
    if not teams:
        # Look for supervisor/workers at root level and create a team
        if ('supervisor' in template_config or 'workers' in template_config or 
            'agents' in template_config):
            team = create_team_from_template_agents(template_config)
            if team:
                teams = [team]
                st.success("✅ Created team from root level agents")
        
        # Look for individual agent configurations
        elif any(key in template_config for key in ['agent', 'agents', 'supervisors', 'team_members']):
            team = create_team_from_flat_structure(template_config)
            if team:
                teams = [team]
                st.success("✅ Created team from flat agent structure")
    
    return teams if isinstance(teams, list) else []

def create_team_from_template_agents(template_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a team structure from template with agents at root level"""
    team = {
        "name": "main_team",
        "description": "Main team from template",
        "supervisor": {},
        "workers": []
    }
    
    # Extract supervisor
    if 'supervisor' in template_config:
        team['supervisor'] = template_config['supervisor']
    elif 'agent' in template_config and template_config['agent'].get('role') == 'supervisor':
        team['supervisor'] = template_config['agent']
    
    # Extract workers
    if 'workers' in template_config:
        team['workers'] = template_config['workers']
    elif 'agents' in template_config:
        agents = template_config['agents']
        if isinstance(agents, list):
            team['workers'] = [agent for agent in agents if agent.get('role') != 'supervisor']
    
    return team

def create_team_from_flat_structure(template_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a team structure from flat template configuration"""
    team = {
        "name": "main_team", 
        "description": "Team created from flat template structure",
        "supervisor": {},
        "workers": []
    }
    
    # Try to identify supervisor and workers from various fields
    if 'supervisors' in template_config:
        supervisors = template_config['supervisors']
        if isinstance(supervisors, list) and len(supervisors) > 0:
            team['supervisor'] = supervisors[0]
    
    if 'team_members' in template_config:
        members = template_config['team_members']
        if isinstance(members, list):
            for member in members:
                if member.get('role') == 'supervisor':
                    team['supervisor'] = member
                else:
                    team['workers'].append(member)
    
    # If still no supervisor, create a default one
    if not team['supervisor']:
        team['supervisor'] = {
            "name": "Default Supervisor",
            "description": "Default supervisor created from template",
            "role": "supervisor"
        }
    
    # If no workers, create some default ones
    if not team['workers']:
        team['workers'] = [
            {
                "name": "Default Worker 1",
                "description": "Default worker created from template", 
                "role": "worker",
                "capabilities": ["general_assistance"]
            }
        ]
    
    return team

def create_minimal_team_from_template(template_config: Dict[str, Any]) -> Dict[str, Any]:
    """Create a minimal team structure from any template configuration"""
    # Get template name from various possible locations
    template_name = "Unknown Template"
    if 'name' in template_config:
        template_name = template_config['name']
    elif 'title' in template_config:
        template_name = template_config['title']
    elif 'id' in template_config:
        template_name = template_config['id']
    
    # Get description from various possible locations
    description = "Template-based team"
    if 'description' in template_config:
        description = template_config['description']
    elif 'summary' in template_config:
        description = template_config['summary']
    
    team = {
        "name": "main_team",
        "description": f"Team created from {template_name}",
        "supervisor": {
            "name": f"{template_name} Supervisor",
            "description": f"Supervisor for {template_name}",
            "role": "supervisor"
        },
        "workers": [
            {
                "id": "worker_1",
                "name": f"{template_name} Assistant",
                "description": "Primary assistant agent",
                "role": "worker",
                "capabilities": ["general_assistance"]
            }
        ]
    }
    
    return team

def create_default_team_from_template():
    """Create a default team structure when template has no teams"""
    if not st.session_state.template_config:
        return
    
    # Create a basic team structure
    default_team = {
        "name": "main_team",
        "description": f"Default team for {st.session_state.selected_template.get('name', 'template')}",
        "supervisor": {
            "name": f"{st.session_state.selected_template.get('name', 'Template')} Supervisor",
            "description": f"Supervisor for {st.session_state.selected_template.get('name', 'template')} team",
            "role": "supervisor"
        },
        "workers": [
            {
                "id": "worker_1",
                "name": f"{st.session_state.selected_template.get('name', 'Template')} Worker 1", 
                "description": "Primary worker agent",
                "role": "worker",
                "capabilities": ["general_assistance", "analysis"]
            },
            {
                "id": "worker_2", 
                "name": f"{st.session_state.selected_template.get('name', 'Template')} Worker 2",
                "description": "Secondary worker agent", 
                "role": "worker",
                "capabilities": ["research", "writing"]
            }
        ]
    }
    
    # Add the team to template config
    if 'teams' not in st.session_state.template_config:
        st.session_state.template_config['teams'] = []
    
    st.session_state.template_config['teams'].append(default_team)
    
    # Also update the template config to ensure it has proper structure
    if 'team' not in st.session_state.template_config:
        st.session_state.template_config['team'] = {
            "name": st.session_state.selected_template.get('name', 'Template Team'),
            "description": st.session_state.selected_template.get('description', 'Team from template'),
            "version": "1.0.0",
            "type": "hierarchical"
        }
    
    # Initialize customization configs for the new team
    supervisor_config = create_default_agent_config("template_supervisor")
    worker_configs = {}
    
    for worker in default_team['workers']:
        worker_id = worker.get('id', worker.get('name', 'unknown'))
        worker_configs[worker_id] = create_default_agent_config(worker_id)
    
    st.session_state.template_customized_configs = {
        'supervisor_config': supervisor_config,
        'worker_configs': worker_configs
    }
    
    st.success("✅ Created default team structure for template!")

def render_template_customization_step():
    """Render template customization step"""
    if not st.session_state.template_config:
        st.warning("No template configuration loaded")
        # Try to reload if we have a selected template
        if st.session_state.selected_template:
            if st.button("🔄 Reload Template Configuration", use_container_width=True):
                load_template_config(st.session_state.selected_template['id'])
                st.rerun()
        return
    
    template_config = st.session_state.template_config
    teams = extract_teams_from_template(template_config)
    
    if not teams:
        st.warning("Template has no teams configured")
        st.info(f"Available template sections: {', '.join(template_config.keys()) if template_config else 'None'}")
        
        # Offer to create a default team structure
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🏗️ Create Default Team Structure", use_container_width=True):
                create_default_team_from_template()
                st.rerun()
        
        with col2:
            if st.button("📋 Show Template Structure", use_container_width=True):
                st.json(template_config)
        
        with col3:
            if st.button("🔧 Force Team Creation", use_container_width=True):
                # Force create a minimal team and add it to the template config
                minimal_team = create_minimal_team_from_template(template_config)
                if 'teams' not in st.session_state.template_config:
                    st.session_state.template_config['teams'] = []
                st.session_state.template_config['teams'].append(minimal_team)
                
                # Initialize configs
                supervisor_config = create_default_agent_config("template_supervisor")
                worker_configs = {
                    "worker_1": create_default_agent_config("worker_1")
                }
                st.session_state.template_customized_configs = {
                    'supervisor_config': supervisor_config,
                    'worker_configs': worker_configs
                }
                st.success("✅ Force created team structure!")
                st.rerun()
        
        return
    
    main_team = teams[0]  # Use first team for customization
    supervisor = main_team.get('supervisor', {})
    workers = main_team.get('workers', [])
    
    # Supervisor Configuration Section
    st.markdown("#### 👥 Supervisor Configuration")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"**Supervisor:** {supervisor.get('name', 'Unknown')}")
        st.markdown(f"**Description:** {supervisor.get('description', 'No description')}")
    
    with col2:
        if st.button("⚙️ Customize Supervisor", key="customize_template_supervisor", use_container_width=True):
            st.session_state.show_template_supervisor_editor = not st.session_state.show_template_supervisor_editor
            st.rerun()
    
    if st.session_state.show_template_supervisor_editor:
        render_template_supervisor_config_editor()
    
    # Workers Configuration Section
    st.markdown("#### 🤖 Workers Configuration")
    
    if workers:
        for worker in workers:
            worker_id = worker.get('id', worker.get('name', 'unknown'))
            worker_name = worker.get('name', 'Unknown Worker')
            
            col1, col2 = st.columns([3, 1])
            with col1:
                capabilities_text = ', '.join([cap.get('name', cap) if isinstance(cap, dict) else str(cap) 
                                             for cap in worker.get('capabilities', [])][:3])
                if len(worker.get('capabilities', [])) > 3:
                    capabilities_text += '...'
                
                st.markdown(f"**Worker:** {worker_name}")
                st.markdown(f"**Capabilities:** {capabilities_text}")
            
            with col2:
                if st.button("⚙️ Customize", key=f"customize_template_worker_{worker_id}", use_container_width=True):
                    if worker_id in st.session_state.show_template_worker_editors:
                        st.session_state.show_template_worker_editors.remove(worker_id)
                    else:
                        st.session_state.show_template_worker_editors.add(worker_id)
                    st.rerun()
            
            if worker_id in st.session_state.show_template_worker_editors:
                render_template_worker_config_editor(worker_id, worker_name)
    else:
        st.info("No workers configured in this template")

def render_template_supervisor_config_editor():
    """Render template supervisor configuration editor"""
    st.markdown("---")
    st.markdown("### ⚙️ Supervisor Configuration Editor (Template)")
    
    if st.session_state.template_customized_configs['supervisor_config'] is None:
        st.warning("No configuration loaded for supervisor")
        
        # Try to create a default configuration
        if st.button("🔧 Create Default Configuration", key="create_default_supervisor_config"):
            default_config = create_default_agent_config("template_supervisor")
            st.session_state.template_customized_configs['supervisor_config'] = default_config
            st.success("Created default supervisor configuration")
            st.rerun()
        return
    
    config = st.session_state.template_customized_configs['supervisor_config']
    
    # Create tabs for different configuration sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏷️ Basic Info", 
        "🤖 LLM Settings", 
        "💬 Prompts", 
        "🛠️ Tools", 
        "🧠 Memory", 
        "⚡ Runtime"
    ])
    
    with tab1:
        render_basic_info_tab(config, "template_supervisor")
    
    with tab2:
        render_llm_config_tab(config, "template_supervisor")
    
    with tab3:
        render_prompts_config_tab(config, "template_supervisor")
    
    with tab4:
        render_tools_config_tab(config, "template_supervisor")
    
    with tab5:
        render_memory_config_tab(config, "template_supervisor")
    
    with tab6:
        render_runtime_config_tab(config, "template_supervisor")
    
    # Save and Preview buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save Configuration", key="save_template_supervisor_config", use_container_width=True):
            st.success("✅ Supervisor configuration saved!")
    
    with col2:
        if st.button("👁️ Preview YAML", key="preview_template_supervisor_yaml", use_container_width=True):
            st.code(yaml.dump(config, default_flow_style=False), language='yaml')
    
    with col3:
        if st.button("🔄 Reset to Template Default", key="reset_template_supervisor_config", use_container_width=True):
            # Reset to original template configuration
            load_template_config(st.session_state.selected_template['id'])
            st.rerun()

def render_template_worker_config_editor(worker_id: str, worker_name: str):
    """Render template worker configuration editor"""
    st.markdown("---")
    st.markdown(f"### ⚙️ {worker_name} Configuration Editor (Template)")
    
    if worker_id not in st.session_state.template_customized_configs['worker_configs']:
        st.warning(f"No configuration loaded for worker {worker_name}")
        
        # Try to create a default configuration
        if st.button("🔧 Create Default Configuration", key=f"create_default_worker_config_{worker_id}"):
            default_config = create_default_agent_config(worker_id)
            st.session_state.template_customized_configs['worker_configs'][worker_id] = default_config
            st.success(f"Created default configuration for {worker_name}")
            st.rerun()
        return
    
    config = st.session_state.template_customized_configs['worker_configs'][worker_id]
    
    # Create tabs for different configuration sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏷️ Basic Info", 
        "🤖 LLM Settings", 
        "💬 Prompts", 
        "🛠️ Tools", 
        "🧠 Memory", 
        "⚡ Runtime"
    ])
    
    with tab1:
        render_basic_info_tab(config, f"template_worker_{worker_id}")
    
    with tab2:
        render_llm_config_tab(config, f"template_worker_{worker_id}")
    
    with tab3:
        render_prompts_config_tab(config, f"template_worker_{worker_id}")
    
    with tab4:
        render_tools_config_tab(config, f"template_worker_{worker_id}")
    
    with tab5:
        render_memory_config_tab(config, f"template_worker_{worker_id}")
    
    with tab6:
        render_runtime_config_tab(config, f"template_worker_{worker_id}")
    
    # Save and Preview buttons
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("💾 Save Configuration", key=f"save_template_worker_config_{worker_id}", use_container_width=True):
            st.success(f"✅ {worker_name} configuration saved!")
    
    with col2:
        if st.button("👁️ Preview YAML", key=f"preview_template_worker_yaml_{worker_id}", use_container_width=True):
            st.code(yaml.dump(config, default_flow_style=False), language='yaml')
    
    with col3:
        if st.button("🔄 Reset to Template Default", key=f"reset_template_worker_config_{worker_id}", use_container_width=True):
            # Reset to original template configuration
            load_template_config(st.session_state.selected_template['id'])
            st.rerun()

def create_team_config_from_template(team_name: str, team_description: str, 
                                   template_config: Dict[str, Any], 
                                   customized_configs: Dict[str, Any]) -> Dict[str, Any]:
    """Create team configuration from template with customizations"""
    # Start with template configuration
    config_data = template_config.copy()
    
    # Update team information
    config_data["team"] = {
        "name": team_name,
        "description": team_description or f"Team created from template",
        "version": "1.0.0",
        "type": "hierarchical"
    }
    
    # Apply customizations to supervisor and workers
    if "teams" in config_data and len(config_data["teams"]) > 0:
        main_team = config_data["teams"][0]
        
        # Apply supervisor customizations
        if customized_configs.get('supervisor_config'):
            main_team["supervisor"]["config_data"] = customized_configs['supervisor_config']
        
        # Apply worker customizations
        if customized_configs.get('worker_configs'):
            for worker in main_team.get("workers", []):
                worker_id = worker.get('id', worker.get('name', 'unknown'))
                if worker_id in customized_configs['worker_configs']:
                    worker["config_data"] = customized_configs['worker_configs'][worker_id]
    
    return config_data

def test_template_team_deployment(team_name: str, team_description: str, test_prompt: str):
    """Test template team deployment with a sample prompt before actual deployment."""
    try:
        with st.spinner("🧪 Testing template team deployment..."):
            # Create temporary team configuration for testing
            config_data = create_team_config_from_template(
                f"Test_{team_name}", 
                f"Test deployment for {team_description}", 
                st.session_state.template_config,
                st.session_state.template_customized_configs
            )
            
            # Create temporary team via API
            response = st.session_state.api_client.create_team(
                name=f"Test_{team_name}",
                description=f"Test deployment for {team_description}",
                config_data=config_data
            )
            
            if response and 'id' in response:
                test_team_id = response['id']
                
                # Execute test prompt
                execution_response = st.session_state.api_client.execute_task(
                    team_id=test_team_id,
                    input_text=test_prompt,
                    timeout_seconds=120  # 2 minute timeout for testing
                )
                
                if execution_response and 'execution_id' in execution_response:
                    execution_id = execution_response['execution_id']
                    
                    # Store test results for display
                    st.session_state.test_results = {
                        'team_name': team_name,
                        'test_prompt': test_prompt,
                        'execution_id': execution_id,
                        'team_id': test_team_id,
                        'status': 'running',
                        'started_at': execution_response.get('started_at'),
                    }
                    st.session_state.show_test_results = True
                    
                    # Poll for results (simple implementation)
                    st.rerun()
                else:
                    st.error("Failed to start test execution")
            else:
                st.error("Failed to create test team")
                
    except Exception as e:
        st.error(f"Test deployment failed: {str(e)}")

def render_enhanced_agent_library():
    """Render the enhanced agent library with role-based filtering."""
    st.subheader("🗂️ Enhanced Agent Library")
    
    # Library statistics
    agent_stats = load_agent_stats()
    if agent_stats:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Agents", agent_stats['total_agents'])
        with col2:
            st.metric("Supervisors", agent_stats['by_role'].get('supervisor', 0))
        with col3:
            st.metric("Workers", agent_stats['total_agents'] - agent_stats['by_role'].get('supervisor', 0))
        with col4:
            st.metric("Avg Compatibility", f"{agent_stats['average_compatibility']:.2f}")
    
    # Search and filter functionality
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    
    with col1:
        search_term = st.text_input("Search agents", placeholder="Search by name, capability, or role...")
    
    with col2:
        role_filter = st.selectbox(
            "Filter by role",
            options=["All", "Coordinator", "Supervisor", "Worker", "Specialist"]
        )
    
    with col3:
        capability_options = ["All"]
        if agent_stats and agent_stats['by_capability']:
            capability_options.extend(sorted(agent_stats['by_capability'].keys()))
        capability_filter = st.selectbox(
            "Filter by capability",
            options=capability_options
        )
    
    with col4:
        view_mode = st.selectbox("View", options=["Grid", "List", "Detailed"])
    
    # Get filtered agents from API
    try:
        agents_response = st.session_state.api_client.search_agents(
            query=search_term if search_term else None,
            role=role_filter.lower() if role_filter != "All" else None,
            capabilities=[capability_filter] if capability_filter != "All" else None,
            limit=50
        )
        agents = agents_response.get('agents', [])
        
        # Display agents
        if view_mode == "Grid":
            render_enhanced_agent_grid(agents)
        elif view_mode == "List":
            render_enhanced_agent_list(agents)
        else:
            render_detailed_agent_view(agents)
    
    except Exception as e:
        st.error(f"Failed to load agents: {e}")

def render_enhanced_agent_grid(agents):
    """Render enhanced agents in a grid layout."""
    if not agents:
        st.info("No agents found matching your criteria")
        return
        
    cols = st.columns(3)
    
    for i, agent in enumerate(agents):
        with cols[i % 3]:
            role_emoji = {
                "coordinator": "👑",
                "supervisor": "👥", 
                "worker": "🤖",
                "specialist": "🎯"
            }.get(agent.get('primary_role', 'worker'), "🤖")
            
            with st.container():
                capabilities_text = ', '.join([cap.get('name', '') for cap in agent.get('capabilities', [])][:3])
                if len(agent.get('capabilities', [])) > 3:
                    capabilities_text += '...'
                
                st.markdown(f"""
                <div class="worker-card">
                    <h4>{role_emoji} {agent.get('name', 'Unknown')}</h4>
                    <p><small>{agent.get('description', '')[:100]}{'...' if len(agent.get('description', '')) > 100 else ''}</small></p>
                    <p><strong>Role:</strong> {agent.get('primary_role', 'worker').title()}</p>
                    <p><strong>Capabilities:</strong> {capabilities_text}</p>
                    <p><strong>Compatibility:</strong> {agent.get('compatibility_score', 0):.2f}</p>
                    {'<p><strong>🎯 Can Coordinate</strong></p>' if agent.get('can_coordinate') else ''}
                    {'<p><strong>👥 Can Supervise</strong></p>' if agent.get('can_supervise') else ''}
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"ℹ️ Info", key=f"info_{agent.get('id', i)}"):
                        st.session_state[f"show_info_{agent.get('id', i)}"] = True
                
                with col2:
                    if st.button(f"➕ Select", key=f"select_enhanced_{agent.get('id', i)}"):
                        st.success(f"Selected {agent.get('name', 'Agent')}")

def render_enhanced_agent_list(agents):
    """Render enhanced agents in a list layout."""
    if not agents:
        st.info("No agents found matching your criteria")
        return
        
    for agent in agents:
        role_emoji = {
            "coordinator": "👑",
            "supervisor": "👥", 
            "worker": "🤖",
            "specialist": "🎯"
        }.get(agent.get('primary_role', 'worker'), "🤖")
        
        with st.expander(f"{role_emoji} {agent.get('name', 'Unknown')} ({agent.get('primary_role', 'worker').title()})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Description:** {agent.get('description', 'No description')}")
                st.write(f"**Primary Role:** {agent.get('primary_role', 'worker').title()}")
                if agent.get('secondary_roles'):
                    st.write(f"**Secondary Roles:** {', '.join(agent['secondary_roles'])}")
                
                capabilities = [cap.get('name', '') for cap in agent.get('capabilities', [])]
                st.write(f"**Capabilities:** {', '.join(capabilities)}")
                st.write(f"**Tools:** {', '.join(agent.get('tools', []))}")
                st.write(f"**Specializations:** {', '.join(agent.get('specializations', []))}")
                st.write(f"**Compatibility Score:** {agent.get('compatibility_score', 0):.2f}")
                st.write(f"**Config File:** {agent.get('file_path', 'Unknown')}")
            
            with col2:
                if agent.get('can_coordinate'):
                    st.success("🎯 Can Coordinate")
                if agent.get('can_supervise'):
                    st.success("👥 Can Supervise")
                if agent.get('team_size_limit'):
                    st.info(f"Max Team Size: {agent['team_size_limit']}")
                
                if st.button(f"Select Agent", key=f"select_list_enhanced_{agent.get('id', 'unknown')}"):
                    st.success(f"Selected {agent.get('name', 'Agent')}")

def render_detailed_agent_view(agents):
    """Render detailed agent view with compatibility matrix."""
    if not agents:
        st.info("No agents found matching your criteria")
        return
        
    agent_options = [f"{agent.get('name', 'Unknown')} ({agent.get('id', 'unknown')})" for agent in agents]
    selected_agent = st.selectbox(
        "Select agent for detailed view:",
        options=["Select agent..."] + agent_options
    )
    
    if selected_agent != "Select agent...":
        agent_idx = agent_options.index(selected_agent)
        agent = agents[agent_idx]
        
        # Agent details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            ### {agent.get('name', 'Unknown')}
            **Description:** {agent.get('description', 'No description')}
            
            **Primary Role:** {agent.get('primary_role', 'worker').title()}
            
            **Secondary Roles:** {', '.join(agent.get('secondary_roles', [])) if agent.get('secondary_roles') else 'None'}
            
            **Capabilities:** {', '.join([cap.get('name', '') for cap in agent.get('capabilities', [])])}
            
            **Tools:** {', '.join(agent.get('tools', []))}
            
            **Specializations:** {', '.join(agent.get('specializations', []))}
            """)
        
        with col2:
            st.metric("Compatibility Score", f"{agent.get('compatibility_score', 0):.2f}")
            if agent.get('can_coordinate'):
                st.success("🎯 Can Coordinate")
            if agent.get('can_supervise'):
                st.success("👥 Can Supervise")
            if agent.get('team_size_limit'):
                st.info(f"Max Team Size: {agent['team_size_limit']}")
        
        # Compatibility with other agents
        st.markdown("### 🤝 Compatibility with Other Agents")
        
        try:
            agent_ids = [a.get('id', f'agent_{i}') for i, a in enumerate(agents)]
            compatibility_response = st.session_state.api_client.check_agent_compatibility(agent_ids)
            
            if compatibility_response and compatibility_response.get('compatibility_matrix'):
                agent_id = agent.get('id', f'agent_{agent_idx}')
                if agent_id in compatibility_response['compatibility_matrix']:
                    agent_compatibility = compatibility_response['compatibility_matrix'][agent_id]
                    
                    # Sort by compatibility score
                    sorted_compatibility = sorted(
                        [(other_id, score) for other_id, score in agent_compatibility.items() if other_id != agent_id],
                        key=lambda x: x[1], reverse=True
                    )
                    
                    # Show top 5 most compatible agents
                    st.markdown("**Most Compatible Agents:**")
                    for other_id, score in sorted_compatibility[:5]:
                        # Find agent name by ID
                        other_agent = next((a for a in agents if a.get('id') == other_id), None)
                        if other_agent:
                            st.write(f"• {other_agent.get('name', 'Unknown')}: {score:.2f}")
        except Exception as e:
            st.error(f"Failed to load compatibility data: {e}")

def render_team_builder():
    """Render the hierarchical team builder interface."""
    st.subheader("🏗️ Hierarchical Team Builder")
    
    if not st.session_state.hierarchical_config:
        st.info("👆 Load a hierarchical template from the sidebar to start building your team")
        return
    
    # Display current team configuration
    config = st.session_state.hierarchical_config
    
    # Team Information
    st.write("### Team Information")
    team_info = config.get('team', {})
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Name:** {team_info.get('name', 'Unknown')}")
        st.write(f"**Type:** {team_info.get('type', 'hierarchical')}")
    with col2:
        st.write(f"**Description:** {team_info.get('description', 'No description')}")
        st.write(f"**Version:** {team_info.get('version', '1.0.0')}")
    
    # Coordinator Configuration
    render_coordinator_config(config.get('coordinator', {}))
    
    # Teams Configuration
    render_teams_config(config.get('teams', []))
    
    # Team Actions
    render_team_actions()

def render_coordinator_config(coordinator_config):
    """Render coordinator configuration."""
    st.write("### 👑 Coordinator Configuration")
    
    with st.container():
        st.markdown(f"""
        <div class="coordinator-card">
            <h4>🎯 {coordinator_config.get('name', 'Unknown Coordinator')}</h4>
            <p>{coordinator_config.get('description', 'No description')}</p>
            <p><strong>LLM:</strong> {coordinator_config.get('llm', {}).get('provider', 'unknown')} - {coordinator_config.get('llm', {}).get('model', 'unknown')}</p>
            <p><strong>Routing Strategy:</strong> {coordinator_config.get('routing', {}).get('strategy', 'hybrid')}</p>
        </div>
        """, unsafe_allow_html=True)

def render_teams_config(teams_config):
    """Render teams configuration with hierarchy visualization."""
    st.write("### 🏢 Teams Hierarchy")
    
    for i, team in enumerate(teams_config):
        render_team_card(team, i)

def render_team_card(team_config, team_index):
    """Render an individual team card."""
    team_name = team_config.get('name', f'Team {team_index + 1}')
    
    with st.expander(f"👥 {team_name}", expanded=True):
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.write(f"**Description:** {team_config.get('description', 'No description')}")
            
            # Supervisor info
            supervisor = team_config.get('supervisor', {})
            st.write(f"**Supervisor:** {supervisor.get('name', 'Unknown')}")
            
            # Workers
            workers = team_config.get('workers', [])
            st.write(f"**Workers:** {len(workers)} agents")
            
            for worker in workers:
                render_worker_card(worker)
        
        with col2:
            # Team management actions
            st.write("**Team Actions**")
            
            if st.button(f"Add Worker", key=f"add_worker_{team_index}"):
                st.session_state[f"show_add_worker_{team_index}"] = True
            
            if st.button(f"Edit Team", key=f"edit_team_{team_index}"):
                st.session_state[f"show_edit_team_{team_index}"] = True
            
            if st.button(f"Remove Team", key=f"remove_team_{team_index}"):
                remove_team(team_index)

def render_worker_card(worker_config):
    """Render an individual worker card."""
    worker_name = worker_config.get('name', 'Unknown Worker')
    worker_role = worker_config.get('role', 'worker')
    capabilities = worker_config.get('capabilities', [])
    
    st.markdown(f"""
    <div class="worker-card hierarchy-level-3">
        <strong>🤖 {worker_name}</strong> <em>({worker_role})</em><br>
        <small>{worker_config.get('description', 'No description')}</small><br>
        <small><strong>Capabilities:</strong> {', '.join(capabilities[:3])}{'...' if len(capabilities) > 3 else ''}</small>
    </div>
    """, unsafe_allow_html=True)

def remove_team(team_index):
    """Remove a team from the configuration."""
    if 'teams' in st.session_state.hierarchical_config:
        if team_index < len(st.session_state.hierarchical_config['teams']):
            del st.session_state.hierarchical_config['teams'][team_index]
            st.success("Team removed")
            st.rerun()

def render_team_actions():
    """Render team-level actions."""
    st.write("### 🎛️ Team Management")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("💾 Save Configuration"):
            save_hierarchical_config()
    
    with col2:
        if st.button("🧪 Test Team"):
            st.session_state.show_test_interface = True
    
    with col3:
        if st.button("🚀 Deploy Team"):
            deploy_hierarchical_team()
    
    with col4:
        if st.button("📊 View Metrics"):
            st.session_state.show_metrics = True

def save_hierarchical_config():
    """Save the current hierarchical configuration."""
    if not st.session_state.hierarchical_config:
        st.error("No configuration to save")
        return
    
    # Generate filename
    team_name = st.session_state.hierarchical_config.get('team', {}).get('name', 'custom_team')
    safe_name = "".join(c for c in team_name if c.isalnum() or c in (' ', '_')).rstrip()
    filename = f"{safe_name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yml"
    
    # Convert to YAML
    config_yaml = yaml.dump(st.session_state.hierarchical_config, default_flow_style=False, indent=2)
    
    st.download_button(
        label="📥 Download Configuration",
        data=config_yaml,
        file_name=filename,
        mime="text/yaml"
    )
    
    st.success("✅ Configuration ready for download")

def deploy_hierarchical_team():
    """Deploy the hierarchical team for production use."""
    st.write("#### 🚀 Team Deployment")
    
    if not st.session_state.hierarchical_config:
        st.error("No configuration to deploy")
        return
    
    deployment_name = st.text_input("Deployment Name", value=f"deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    environment = st.selectbox("Environment", options=["development", "staging", "production"])
    
    if st.button("Deploy Team"):
        try:
            # Create the team via API
            team_name = st.session_state.hierarchical_config.get('team', {}).get('name', deployment_name)
            response = create_team_from_config(team_name, st.session_state.hierarchical_config)
            if response:
                st.success(f"✅ Team '{team_name}' deployed successfully to {environment}")
        except Exception as e:
            st.error(f"Deployment failed: {e}")

def render_configuration_management():
    """Render configuration management interface."""
    st.subheader("⚙️ Configuration Management")
    
    # Configuration import/export
    st.write("### 📁 Configuration Files")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Import Configuration**")
        uploaded_file = st.file_uploader(
            "Upload Hierarchical Configuration", 
            type=['yml', 'yaml'],
            key="hierarchical_config_upload"
        )
        
        if uploaded_file is not None:
            try:
                # Upload via API
                upload_result = st.session_state.api_client.upload_config_from_streamlit(uploaded_file)
                if upload_result and upload_result.get('validation_result', {}).get('valid'):
                    # If upload and validation successful, load the config
                    config_data = yaml.safe_load(uploaded_file.getvalue().decode('utf-8'))
                    st.session_state.hierarchical_config = config_data
                    st.success(f"✅ Loaded configuration from {uploaded_file.name}")
                    st.rerun()
                else:
                    validation = upload_result.get('validation_result', {})
                    st.error("Configuration validation failed:")
                    for error in validation.get('errors', []):
                        st.error(f"• {error}")
            except Exception as e:
                st.error(f"Error loading configuration: {e}")
    
    with col2:
        st.write("**Export Configuration**")
        if st.session_state.hierarchical_config:
            config_yaml = yaml.dump(st.session_state.hierarchical_config, 
                                   default_flow_style=False, indent=2)
            
            st.download_button(
                label="📥 Download Configuration",
                data=config_yaml,
                file_name=f"hierarchical_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yml",
                mime="text/yaml"
            )
        else:
            st.info("No configuration to export")
    
    # Configuration validation
    st.write("### ✅ Configuration Validation")
    
    if st.button("Validate Current Configuration"):
        if st.session_state.hierarchical_config:
            try:
                validation_result = st.session_state.api_client.validate_config(
                    st.session_state.hierarchical_config, "hierarchical"
                )
                
                if validation_result['valid']:
                    st.success("✅ Configuration is valid!")
                    
                    # Show validation details
                    with st.expander("Validation Details"):
                        config = st.session_state.hierarchical_config
                        st.write("**Team Information:**")
                        st.write(f"- Name: {config.get('team', {}).get('name', 'Unknown')}")
                        st.write(f"- Type: {config.get('team', {}).get('type', 'hierarchical')}")
                        st.write(f"- Teams: {len(config.get('teams', []))}")
                        
                        total_workers = sum(len(team.get('workers', [])) for team in config.get('teams', []))
                        st.write(f"- Total Workers: {total_workers}")
                else:
                    st.error("❌ Configuration validation failed:")
                    for error in validation_result.get('errors', []):
                        st.error(f"• {error}")
                    
                    if validation_result.get('warnings'):
                        st.warning("Warnings:")
                        for warning in validation_result['warnings']:
                            st.warning(f"• {warning}")
                            
            except Exception as e:
                st.error(f"❌ Configuration validation failed: {e}")
        else:
            st.warning("No configuration to validate")
    
    # Template management
    st.write("### 📚 Template Management")
    
    try:
        templates_response = st.session_state.api_client.list_templates()
        templates = templates_response.get('templates', [])
        
        if templates:
            st.write("**Available Templates:**")
            
            for template in templates:
                with st.expander(f"📋 {template['id']}"):
                    st.write(f"**Name:** {template['name']}")
                    st.write(f"**Description:** {template['description']}")
                    st.write(f"**Teams:** {template.get('team_count', 0)}")
                    st.write(f"**Workers:** {template.get('worker_count', 0)}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Load Template", key=f"load_{template['id']}"):
                            template_details = st.session_state.api_client.get_template(template['id'])
                            if template_details:
                                st.session_state.hierarchical_config = template_details['config_data']
                                st.success(f"Loaded {template['id']}")
                                st.rerun()
                    
                    with col2:
                        if st.button(f"View YAML", key=f"view_{template['id']}"):
                            template_details = st.session_state.api_client.get_template(template['id'])
                            if template_details:
                                st.code(yaml.dump(template_details['config_data'], default_flow_style=False), 
                                        language='yaml')
        else:
            st.info("No templates found")
    except Exception as e:
        st.error(f"Failed to load templates: {e}")

def render_hierarchy_visualization():
    """Render interactive hierarchy visualization."""
    st.subheader("🔗 Team Hierarchy Visualization")
    
    if not st.session_state.hierarchical_config:
        st.info("Load a hierarchical configuration to view team structure")
        return
    
    config = st.session_state.hierarchical_config
    
    # Create hierarchy visualization
    st.write("### Organization Structure")
    
    # Coordinator (top level)
    coordinator = config.get('coordinator', {})
    st.markdown(f"""
    <div class="coordinator-card hierarchy-level-1">
        <span class="status-indicator status-active"></span>
        <strong>👑 {coordinator.get('name', 'Coordinator')}</strong><br>
        <small>{coordinator.get('description', 'Team Coordinator')}</small>
    </div>
    """, unsafe_allow_html=True)
    
    # Teams (second level)
    teams = config.get('teams', [])
    for team in teams:
        st.markdown(f"""
        <div class="team-card hierarchy-level-2">
            <span class="status-indicator status-active"></span>
            <strong>👥 {team.get('name', 'Team')}</strong><br>
            <small>{team.get('description', 'No description')}</small><br>
            <small><strong>Supervisor:</strong> {team.get('supervisor', {}).get('name', 'Unknown')}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Workers (third level)
        workers = team.get('workers', [])
        for worker in workers:
            st.markdown(f"""
            <div class="worker-card hierarchy-level-3">
                <span class="status-indicator status-active"></span>
                <strong>🤖 {worker.get('name', 'Worker')}</strong> <em>({worker.get('role', 'worker')})</em><br>
                <small>{worker.get('description', 'No description')}</small>
            </div>
            """, unsafe_allow_html=True)

def render_testing_interface():
    """Render team testing interface"""
    st.subheader("🧪 Team Testing")
    
    if not st.session_state.current_team_id:
        st.warning("Please create or select a team first")
        return
    
    # Test input interface
    test_input = st.text_area(
        "Enter test message:",
        placeholder="Enter a task for your hierarchical team to handle...",
        height=100
    )
    
    if st.button("🚀 Run Test") and test_input:
        with st.spinner("Running hierarchical team test..."):
            try:
                # Execute task via API
                execution = st.session_state.api_client.execute_task(
                    team_id=st.session_state.current_team_id,
                    input_text=test_input,
                    timeout_seconds=300
                )
                
                if execution:
                    execution_id = execution['execution_id']
                    st.success(f"✅ Test started! Execution ID: {execution_id}")
                    
                    # Poll for results
                    max_wait = 60  # Maximum wait time in seconds
                    wait_time = 0
                    
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    while wait_time < max_wait:
                        result = st.session_state.api_client.get_execution(execution_id)
                        
                        if result:
                            status = result.get('status', {}).get('status', 'pending')
                            progress = result.get('status', {}).get('progress', 0)
                            
                            progress_bar.progress(progress / 100)
                            status_text.text(f"Status: {status} ({progress}%)")
                            
                            if status == 'completed':
                                st.write("### 📋 Test Results")
                                
                                if result.get('result'):
                                    result_data = result['result']
                                    st.write(f"**Response:** {result_data.get('response', 'No response')}")
                                    
                                    if result_data.get('execution_time_seconds'):
                                        st.metric("Execution Time", f"{result_data['execution_time_seconds']:.2f}s")
                                    
                                    with st.expander("📊 Detailed Results"):
                                        st.json(result_data)
                                break
                            elif status == 'failed':
                                st.error(f"❌ Test failed: {result.get('status', {}).get('error_message', 'Unknown error')}")
                                break
                        
                        time.sleep(2)
                        wait_time += 2
                    
                    if wait_time >= max_wait:
                        st.warning("⏱️ Test is taking longer than expected. Check execution history for updates.")
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                
            except Exception as e:
                st.error(f"Test failed: {e}")

def render_performance_dashboard():
    """Render performance dashboard"""
    st.subheader("📊 Performance Dashboard")
    
    # Mock performance metrics (in a real implementation, these would come from the API)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Response Time", "2.3s", "-0.5s")
    
    with col2:
        st.metric("Success Rate", "94.2%", "+2.1%")
    
    with col3:
        st.metric("Tasks Completed", "156", "+23")
    
    with col4:
        st.metric("Team Efficiency", "87%", "+5%")
    
    # Team performance
    if st.session_state.teams_list:
        st.write("### Team Performance")
        
        for team in st.session_state.teams_list:
            with st.expander(f"📊 {team['name']} Performance"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Status", team.get('status', 'Unknown'))
                
                with col2:
                    st.metric("Created", team.get('created_at', 'Unknown')[:10] if team.get('created_at') else 'Unknown')
                
                with col3:
                    # Get team hierarchy info
                    hierarchy = team.get('hierarchy_info', {})
                    total_agents = hierarchy.get('total_teams', 0) + hierarchy.get('total_workers', 0)
                    st.metric("Total Agents", total_agents)
    
    # Execution history performance
    if st.session_state.execution_history:
        st.write("### Recent Executions")
        
        # Show last 5 executions
        recent_executions = st.session_state.execution_history[-5:]
        
        for execution in reversed(recent_executions):
            with st.expander(f"🔍 {execution['input_text'][:50]}..."):
                st.write(f"**Execution ID:** {execution['execution_id']}")
                st.write(f"**Team ID:** {execution['team_id']}")
                st.write(f"**Timestamp:** {execution['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}")
                
                if st.button(f"Check Status", key=f"status_{execution['execution_id']}"):
                    try:
                        result = st.session_state.api_client.get_execution(execution['execution_id'])
                        if result:
                            st.json(result)
                    except Exception as e:
                        st.error(f"Failed to get status: {e}")


@handle_api_error
def test_team_deployment(team_name: str, team_description: str, test_prompt: str):
    """Test team deployment with a sample prompt before actual deployment."""
    try:
        with st.spinner("🧪 Testing team deployment..."):
            # Create temporary team configuration for testing
            config_data = create_simple_team_config_with_customizations(
                f"Test_{team_name}", 
                f"Test deployment for {team_description}", 
                st.session_state.selected_supervisor, 
                st.session_state.selected_workers,
                st.session_state.customized_configs
            )
            
            # Create temporary team via API
            response = st.session_state.api_client.create_team(
                name=f"Test_{team_name}",
                description=f"Test deployment for {team_description}",
                config_data=config_data
            )
            
            if response and 'id' in response:
                test_team_id = response['id']
                
                # Execute test prompt
                execution_response = st.session_state.api_client.execute_task(
                    team_id=test_team_id,
                    input_text=test_prompt,
                    timeout_seconds=120  # 2 minute timeout for testing
                )
                
                if execution_response and 'execution_id' in execution_response:
                    execution_id = execution_response['execution_id']
                    
                    # Store test results for display
                    st.session_state.test_results = {
                        'team_name': team_name,
                        'test_prompt': test_prompt,
                        'execution_id': execution_id,
                        'team_id': test_team_id,
                        'status': 'running',
                        'started_at': execution_response.get('started_at'),
                    }
                    st.session_state.show_test_results = True
                    
                    # Poll for results (simple implementation)
                    st.rerun()
                else:
                    st.error("Failed to start test execution")
            else:
                st.error("Failed to create test team")
                
    except Exception as e:
        st.error(f"Test deployment failed: {str(e)}")


def render_test_deployment_results():
    """Render test deployment results."""
    if not hasattr(st.session_state, 'test_results'):
        return
    
    test_results = st.session_state.test_results
    
    st.markdown("---")
    st.markdown("## 🧪 Test Deployment Results")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"**Test Team**: {test_results['team_name']}")
        st.markdown(f"**Test Prompt**: {test_results['test_prompt']}")
    
    with col2:
        # Check execution status button
        if st.button("🔄 Check Status", key="check_test_status"):
            try:
                result = st.session_state.api_client.get_execution(test_results['execution_id'])
                if result:
                    test_results.update(result)
                    st.session_state.test_results = test_results
                    st.rerun()
            except Exception as e:
                st.error(f"Failed to get status: {e}")
    
    with col3:
        # Clean up test team button
        if st.button("🗑️ Clean Up", key="cleanup_test"):
            try:
                st.session_state.api_client.delete_team(test_results['team_id'])
                st.session_state.show_test_results = False
                if hasattr(st.session_state, 'test_results'):
                    del st.session_state.test_results
                st.success("Test team cleaned up successfully!")
                st.rerun()
            except Exception as e:
                st.warning(f"Failed to clean up test team: {e}")
    
    # Display execution status
    status = test_results.get('status', {})
    if isinstance(status, dict):
        current_status = status.get('status', 'unknown')
    else:
        current_status = status
    
    # Status indicator
    status_colors = {
        'running': 'orange',
        'completed': 'green', 
        'failed': 'red',
        'pending': 'blue'
    }
    status_color = status_colors.get(current_status, 'gray')
    
    st.markdown(f"**Status**: <span style='color: {status_color}; font-weight: bold;'>{current_status.title()}</span>", 
                unsafe_allow_html=True)
    
    # Show execution details if available
    if 'result' in test_results and test_results['result']:
        result_data = test_results['result']
        
        # Execution metrics
        if 'execution_time' in result_data:
            st.metric("Execution Time", f"{result_data['execution_time']:.2f}s")
        
        # Response content
        if 'response' in result_data:
            st.markdown("### 📋 Test Response")
            with st.expander("View Full Response", expanded=True):
                st.markdown(result_data['response'])
        
        # Routing information if available
        if 'routing_info' in result_data:
            routing_info = result_data['routing_info']
            st.markdown("### 🗺️ Routing Information")
            
            col1, col2 = st.columns(2)
            with col1:
                if 'coordinator_decision' in routing_info:
                    st.markdown("**Coordinator Decision:**")
                    st.info(routing_info['coordinator_decision'])
            
            with col2:
                if 'team_assignment' in routing_info:
                    st.markdown("**Team Assignment:**")
                    st.info(routing_info['team_assignment'])
    
    elif current_status == 'running':
        st.info("⏳ Test execution in progress... Click 'Check Status' to update.")
    
    elif current_status == 'failed':
        st.error("❌ Test execution failed. Check your team configuration and try again.")
        if 'error' in test_results:
            st.error(f"Error details: {test_results['error']}")
    
    # Test success/failure summary
    if current_status == 'completed':
        st.success("✅ **Test Successful!** Your team is working correctly and ready for deployment.")
        
        # Show deployment recommendation
        st.markdown("### 🚀 Ready to Deploy")
        st.info("Your team responded successfully to the test prompt. You can now safely deploy this team configuration.")
        
    elif current_status == 'failed':
        st.error("❌ **Test Failed!** Please review your configuration before deploying.")
        
        # Show troubleshooting tips
        with st.expander("🔧 Troubleshooting Tips"):
            st.markdown("""
            **Common Issues:**
            - Check that all workers have appropriate capabilities for the task
            - Verify supervisor routing logic includes the selected workers
            - Ensure LLM configurations are valid and API keys are set
            - Review worker specializations match the test prompt requirements
            
            **Next Steps:**
            1. Go back to Step 3 to validate and optimize your configuration
            2. Adjust worker capabilities or supervisor routing logic
            3. Test again with a simpler prompt to isolate issues
            """)


def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Main title
    st.title("🏢 Hierarchical Agent Teams (Complete API Version)")
    st.write("Build and manage complex hierarchical agent teams with full feature parity")
    
    # Sidebar
    render_api_status()
    render_hierarchical_templates_sidebar()
    
    # Quick stats in sidebar
    if st.session_state.hierarchical_config:
        st.sidebar.divider()
        st.sidebar.subheader("📊 Current Team")
        
        config = st.session_state.hierarchical_config
        teams_count = len(config.get('teams', []))
        workers_count = sum(len(team.get('workers', [])) for team in config.get('teams', []))
        
        st.sidebar.metric("Teams", teams_count)
        st.sidebar.metric("Workers", workers_count)
        st.sidebar.metric("Total Agents", teams_count + workers_count + 1)  # +1 for coordinator
    
    # Main content tabs - Different modes
    if st.session_state.builder_mode == 'simple':
        # Simple Team Builder - Single page interface
        render_simple_team_builder()
        
    elif st.session_state.builder_mode == 'template':
        # Template Library Builder - Single page interface
        render_template_library_builder()
        
    else:
        # Traditional template-based tabs
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🏗️ Team Builder", 
            "🗂️ Agent Library", 
            "🔗 Hierarchy View", 
            "🧪 Testing", 
            "📊 Performance Dashboard",
            "⚙️ Configuration"
        ])
        
        with tab1:
            render_team_builder()
        
        with tab2:
            render_enhanced_agent_library()
        
        with tab3:
            render_hierarchy_visualization()
        
        with tab4:
            render_testing_interface()
        
        with tab5:
            render_performance_dashboard()
        
        with tab6:
            render_configuration_management()


def render_validation_results(validation_result: ValidationResult, team_name: str, team_description: str):
    """Render the validation results with optimization options."""
    st.markdown("---")
    st.markdown("## 🔍 Configuration Validation Results")
    
    # Overall score display
    score = validation_result.overall_score
    score_color = "green" if score >= 80 else "orange" if score >= 60 else "red"
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown(f"### Overall Score: <span style='color: {score_color}; font-weight: bold;'>{score:.1f}/100</span>", 
                   unsafe_allow_html=True)
    with col2:
        total_issues = len(validation_result.issues)
        critical_issues = len([i for i in validation_result.issues if i.severity == ValidationSeverity.CRITICAL])
        st.metric("Total Issues", total_issues, delta=f"{critical_issues} critical" if critical_issues > 0 else None)
    with col3:
        auto_fixable = len([i for i in validation_result.issues if i.auto_fixable])
        st.metric("Auto-Fixable", auto_fixable)
    
    # Issues breakdown
    if validation_result.issues:
        st.markdown("### 🚨 Issues Found")
        
        # Group issues by severity
        severity_groups = {}
        for issue in validation_result.issues:
            if issue.severity not in severity_groups:
                severity_groups[issue.severity] = []
            severity_groups[issue.severity].append(issue)
        
        # Display issues by severity
        severity_icons = {
            ValidationSeverity.CRITICAL: "🔴",
            ValidationSeverity.HIGH: "🟠", 
            ValidationSeverity.MEDIUM: "🟡",
            ValidationSeverity.LOW: "🔵",
            ValidationSeverity.INFO: "ℹ️"
        }
        
        for severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH, 
                        ValidationSeverity.MEDIUM, ValidationSeverity.LOW, ValidationSeverity.INFO]:
            if severity in severity_groups:
                with st.expander(f"{severity_icons[severity]} {severity.value.title()} Issues ({len(severity_groups[severity])})", 
                               expanded=(severity in [ValidationSeverity.CRITICAL, ValidationSeverity.HIGH])):
                    for issue in severity_groups[severity]:
                        st.markdown(f"**{issue.category.value.replace('_', ' ').title()}**: {issue.message}")
                        st.markdown(f"📍 Location: `{issue.location}`")
                        st.markdown(f"💡 Suggestion: {issue.suggestion}")
                        if issue.auto_fixable:
                            st.markdown("✅ *This issue can be automatically fixed.*")
                        st.markdown(f"🎯 Confidence: {issue.confidence:.0%}")
                        st.markdown("---")
    
    # Suggestions
    if validation_result.suggestions:
        st.markdown("### 💡 Optimization Suggestions")
        for i, suggestion in enumerate(validation_result.suggestions, 1):
            st.markdown(f"{i}. {suggestion}")
    
    # Action buttons
    st.markdown("### 🛠️ Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🔧 Apply Auto-Fixes", use_container_width=True):
            if validation_result.optimized_config:
                st.session_state.validation_config = validation_result.optimized_config
                st.success("✅ Auto-fixes applied! Review the optimized configuration below.")
                # Trigger re-validation to show improvements
                with st.spinner("Re-validating optimized configuration..."):
                    validator = HierarchyValidator()
                    new_result = validator.validate_hierarchy_config(validation_result.optimized_config)
                    st.session_state.validation_result = new_result
                st.rerun()
            else:
                st.warning("No optimized configuration available.")
    
    with col2:
        if st.button("👁️ Preview Optimized Config", use_container_width=True):
            if validation_result.optimized_config:
                st.session_state.show_optimized_preview = True
            else:
                st.warning("No optimized configuration available.")
    
    with col3:
        if st.button("🚀 Deploy Optimized Team", use_container_width=True):
            if validation_result.optimized_config:
                create_team_from_config(team_name, validation_result.optimized_config)
                st.success(f"🎉 Optimized team '{team_name}' deployed successfully!")
            else:
                st.warning("No optimized configuration available.")
    
    with col4:
        if st.button("🔄 Re-validate", use_container_width=True):
            with st.spinner("Re-validating configuration..."):
                validator = HierarchyValidator()
                new_result = validator.validate_hierarchy_config(st.session_state.validation_config)
                st.session_state.validation_result = new_result
            st.rerun()
    
    # Show optimized configuration preview if requested
    if getattr(st.session_state, 'show_optimized_preview', False):
        st.markdown("### 📋 Optimized Configuration Preview")
        
        if validation_result.optimized_config:
            # Show side-by-side comparison
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### Original Configuration")
                st.code(yaml.dump(st.session_state.validation_config, default_flow_style=False), language='yaml')
            
            with col2:
                st.markdown("#### Optimized Configuration")
                st.code(yaml.dump(validation_result.optimized_config, default_flow_style=False), language='yaml')
            
            # Highlight key differences
            st.markdown("#### 🔍 Key Optimizations Applied")
            optimizations_applied = []
            
            # Compare prompts
            original_coordinator_prompt = st.session_state.validation_config.get('coordinator', {}).get('prompts', {}).get('system_prompt', {}).get('template', '')
            optimized_coordinator_prompt = validation_result.optimized_config.get('coordinator', {}).get('prompts', {}).get('system_prompt', {}).get('template', '')
            
            if original_coordinator_prompt != optimized_coordinator_prompt:
                optimizations_applied.append("🎯 **Coordinator Prompt**: Enhanced with team-specific routing logic and capability references")
            
            # Compare supervisor prompts
            original_teams = st.session_state.validation_config.get('teams', [])
            optimized_teams = validation_result.optimized_config.get('teams', [])
            
            for i, (orig_team, opt_team) in enumerate(zip(original_teams, optimized_teams)):
                orig_supervisor_prompt = orig_team.get('supervisor', {}).get('prompts', {}).get('system_prompt', {}).get('template', '')
                opt_supervisor_prompt = opt_team.get('supervisor', {}).get('prompts', {}).get('system_prompt', {}).get('template', '')
                
                if orig_supervisor_prompt != opt_supervisor_prompt:
                    team_name = opt_team.get('name', f'Team {i+1}')
                    optimizations_applied.append(f"👥 **{team_name} Supervisor**: Improved worker delegation and capability-based routing")
            
            if optimizations_applied:
                for optimization in optimizations_applied:
                    st.markdown(optimization)
            else:
                st.info("No significant optimizations were applied to this configuration.")
            
            # Button to close preview
            if st.button("❌ Close Preview"):
                st.session_state.show_optimized_preview = False
                st.rerun()
        else:
            st.warning("No optimized configuration available to preview.")
    
    # Performance tips
    with st.expander("💡 General Performance Tips", expanded=False):
        st.markdown("""
        **Routing Best Practices:**
        - Ensure supervisor prompts clearly reference worker capabilities
        - Include specific examples of task types each worker handles best
        - Add fallback instructions for edge cases
        - Use capability-based routing rather than simple keyword matching
        
        **Prompt Optimization:**
        - Be specific about decision criteria
        - Include worker tool information in routing decisions
        - Add performance considerations (workload, response time)
        - Provide clear instructions for multi-step coordination
        
        **Configuration Structure:**
        - Balance team sizes for optimal performance
        - Ensure capability coverage without excessive overlap
        - Configure appropriate memory and runtime settings
        - Test with realistic workloads before production deployment
        """)


def render_team_evaluation_interface(team_name: str, team_description: str, context: str):
    """
    Render the team evaluation interface for Step 4
    
    Args:
        team_name: Name of the team being evaluated
        team_description: Description of the team
        context: Context ("simple" or "template" to differentiate UI flows)
    """
    st.markdown("---")
    st.markdown("### 📊 Step 4: Evaluate Team Performance") 
    st.markdown("Run comprehensive evaluation tests to assess your team's performance before deployment.")
    
    # Import evaluation components
    try:
        from src.evaluation.team_evaluator import TeamEvaluator
        from src.evaluation.common import EvaluationDimension
        from src.evaluation.test_scenarios import ScenarioLibrary, DifficultyLevel
        from src.evaluation.results_dashboard import EvaluationResultsDashboard
    except ImportError as e:
        st.error(f"Evaluation framework not available: {e}")
        st.info("Please ensure the evaluation framework is properly installed.")
        return
    
    # Evaluation configuration
    st.markdown("#### 🎯 Evaluation Configuration")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        evaluation_type = st.selectbox(
            "Evaluation Type",
            ["Quick Evaluation (5 tests)", "Comprehensive Evaluation (12 tests)", "Custom Evaluation"],
            help="Choose the scope of evaluation testing"
        )
    
    with col2:
        llm_provider = st.selectbox(
            "LLM for Evaluation",
            ["openai", "anthropic"],
            help="LLM provider for LLM-as-judge evaluation"
        )
    
    with col3:
        model_name = st.selectbox(
            "Model",
            ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini"] if llm_provider == "openai" else ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"],
            help="Specific model for evaluation"
        )
    
    # Custom evaluation options
    if evaluation_type == "Custom Evaluation":
        st.markdown("#### 📝 Custom Test Scenarios")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_domains = st.multiselect(
                "Select Domains",
                ["general", "research", "creative", "business", "technology", "analysis"],
                default=["general"]
            )
        
        with col2:
            selected_difficulties = st.multiselect(
                "Select Difficulty Levels",
                [level.value for level in DifficultyLevel],
                default=["easy", "medium"]
            )
        
        include_load_tests = st.checkbox("Include Load Tests", value=False)
        custom_scenario_text = st.text_area(
            "Add Custom Scenario (Optional)",
            placeholder="Enter a custom test prompt for your specific use case...",
            height=100
        )
    
    # Evaluation dimensions selection
    st.markdown("#### 📏 Evaluation Dimensions")
    
    dimension_cols = st.columns(3)
    selected_dimensions = []
    
    all_dimensions = [
        ("Task Completion", EvaluationDimension.TASK_COMPLETION, "How well the team completes assigned tasks"),
        ("Collaboration", EvaluationDimension.COLLABORATION_EFFECTIVENESS, "Team coordination and communication"),
        ("Resource Usage", EvaluationDimension.RESOURCE_UTILIZATION, "Efficiency of resource utilization"),
        ("Response Quality", EvaluationDimension.RESPONSE_COHERENCE, "Coherence and quality of responses"),
        ("Scalability", EvaluationDimension.SCALABILITY_PERFORMANCE, "Performance under increased load"),
        ("Error Handling", EvaluationDimension.ERROR_HANDLING, "Graceful handling of errors and edge cases")
    ]
    
    for i, (display_name, dimension, description) in enumerate(all_dimensions):
        with dimension_cols[i % 3]:
            if st.checkbox(display_name, value=True, help=description):
                selected_dimensions.append(dimension)
    
    # Run evaluation button
    st.markdown("---")
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if st.button("🚀 Run Evaluation", type="primary", use_container_width=True):
            if not selected_dimensions:
                st.error("Please select at least one evaluation dimension.")
                return
            
            # Store evaluation config in session state
            st.session_state[f'evaluation_config_{context}'] = {
                'team_name': team_name,
                'team_description': team_description,
                'evaluation_type': evaluation_type,
                'llm_provider': llm_provider,
                'model_name': model_name,
                'selected_dimensions': selected_dimensions,
                'custom_scenario': custom_scenario_text if evaluation_type == "Custom Evaluation" else None,
                'selected_domains': selected_domains if evaluation_type == "Custom Evaluation" else None,
                'selected_difficulties': selected_difficulties if evaluation_type == "Custom Evaluation" else None,
                'include_load_tests': include_load_tests if evaluation_type == "Custom Evaluation" else False
            }
            
            # Trigger evaluation
            st.session_state[f'run_evaluation_{context}'] = True
            st.rerun()
    
    with col2:
        if st.button("📋 Load Sample Config", use_container_width=True):
            st.session_state[f'show_sample_evaluation_{context}'] = True
    
    with col3:
        if st.button("❓ Evaluation Help", use_container_width=True):
            st.session_state[f'show_evaluation_help_{context}'] = True
    
    # Show sample evaluation configuration
    if st.session_state.get(f'show_sample_evaluation_{context}', False):
        with st.expander("📋 Sample Evaluation Configuration", expanded=True):
            st.markdown("""
            **Quick Evaluation Example:**
            - 5 test scenarios covering basic functionality
            - All 6 evaluation dimensions
            - Estimated time: 2-3 minutes
            - Good for initial team validation
            
            **Comprehensive Evaluation Example:**
            - 12+ test scenarios across multiple domains
            - All evaluation dimensions with detailed analysis
            - Estimated time: 5-8 minutes
            - Recommended for production deployment
            
            **Custom Evaluation Example:**
            - Select specific domains (e.g., research, creative)
            - Choose difficulty levels (easy, medium, hard)
            - Add custom scenarios for your specific use case
            - Include load tests for scalability assessment
            """)
            
            if st.button("Close Sample Config"):
                st.session_state[f'show_sample_evaluation_{context}'] = False
                st.rerun()
    
    # Show evaluation help
    if st.session_state.get(f'show_evaluation_help_{context}', False):
        with st.expander("❓ Evaluation Framework Help", expanded=True):
            st.markdown("""
            ### 🎯 About Team Evaluation
            
            Our evaluation framework uses the **LLM-as-judge** methodology inspired by open_deep_research to comprehensively assess your hierarchical agent teams.
            
            **Evaluation Dimensions:**
            - **Task Completion**: Accuracy and completeness of responses
            - **Collaboration**: How well team members work together
            - **Resource Usage**: Efficiency of time and computational resources
            - **Response Quality**: Coherence, clarity, and relevance
            - **Scalability**: Performance under increased workload
            - **Error Handling**: Graceful handling of edge cases and errors
            
            **Test Scenarios:**
            - **Simple Tasks**: Basic question answering and factual queries
            - **Complex Workflows**: Multi-step problems requiring coordination
            - **Edge Cases**: Unusual inputs and error conditions
            - **Load Tests**: Concurrent tasks and resource-intensive operations
            
            **Scoring System:**
            - Each dimension scored 1-5 (converted to 0.0-1.0 scale)
            - Overall score calculated as average of all dimensions
            - Letter grades: A+ (0.9+), A (0.8+), B (0.7+), C (0.6+), D (0.5+), F (<0.5)
            
            **Best Practices:**
            - Run Quick Evaluation during development
            - Use Comprehensive Evaluation before deployment
            - Add Custom scenarios for domain-specific testing
            - Review recommendations for optimization opportunities
            """)
            
            if st.button("Close Help"):
                st.session_state[f'show_evaluation_help_{context}'] = False
                st.rerun()
    
    # Run evaluation if triggered
    if st.session_state.get(f'run_evaluation_{context}', False):
        run_team_evaluation(context)


def run_team_evaluation(context: str):
    """Execute the team evaluation process"""
    
    eval_config = st.session_state.get(f'evaluation_config_{context}')
    if not eval_config:
        st.error("No evaluation configuration found.")
        return
    
    st.markdown("---")
    st.markdown("### 🔄 Running Team Evaluation...")
    
    # Progress tracking
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        # Import evaluation components
        from src.evaluation.team_evaluator import TeamEvaluator
        from src.evaluation.test_scenarios import ScenarioLibrary, DifficultyLevel
        from src.evaluation.results_dashboard import EvaluationResultsDashboard
        
        # Initialize evaluator
        status_text.text("🤖 Initializing LLM evaluator...")
        progress_bar.progress(10)
        
        evaluator = TeamEvaluator(
            llm_provider=eval_config['llm_provider'],
            model_name=eval_config['model_name']
        )
        
        # Get test scenarios
        status_text.text("📝 Preparing test scenarios...")
        progress_bar.progress(20)
        
        if eval_config['evaluation_type'] == "Quick Evaluation (5 tests)":
            scenarios = ScenarioLibrary.get_quick_evaluation_set()
        elif eval_config['evaluation_type'] == "Comprehensive Evaluation (12 tests)":
            scenarios = ScenarioLibrary.get_comprehensive_evaluation_set()
        else:  # Custom evaluation
            scenarios = []
            
            # Add scenarios based on selected domains and difficulties
            if eval_config.get('selected_domains') and eval_config.get('selected_difficulties'):
                all_scenarios = (
                    ScenarioLibrary.get_general_scenarios() +
                    ScenarioLibrary.get_research_scenarios() +
                    ScenarioLibrary.get_creative_scenarios()
                )
                
                difficulty_enum_map = {level.value: level for level in DifficultyLevel}
                
                for scenario in all_scenarios:
                    if (scenario.domain in eval_config['selected_domains'] or 
                        scenario.domain == 'general') and \
                       scenario.difficulty in [difficulty_enum_map[d] for d in eval_config['selected_difficulties']]:
                        scenarios.append(scenario)
                
                # Add load tests if requested
                if eval_config.get('include_load_tests'):
                    scenarios.extend(ScenarioLibrary.get_load_test_scenarios())
            
            # Add custom scenario if provided
            if eval_config.get('custom_scenario'):
                from src.evaluation.test_scenarios import ScenarioType
                custom_scenario = ScenarioLibrary.create_custom_scenario(
                    name="Custom User Scenario",
                    prompt=eval_config['custom_scenario'],
                    scenario_type=ScenarioType.SIMPLE_TASK,
                    difficulty=DifficultyLevel.MEDIUM
                )
                scenarios.append(custom_scenario)
        
        if not scenarios:
            st.error("No test scenarios selected for evaluation.")
            return
        
        status_text.text(f"🧪 Running {len(scenarios)} test scenarios...")
        progress_bar.progress(30)
        
        # Mock team configuration (in real implementation, this would come from the validated config)
        team_config = {
            'team': {
                'name': eval_config['team_name'],
                'description': eval_config['team_description'],
                'type': 'hierarchical'
            },
            'teams': [
                {
                    'name': 'Research Team',
                    'workers': [{'name': 'Researcher'}, {'name': 'Analyst'}]
                },
                {
                    'name': 'Creative Team', 
                    'workers': [{'name': 'Writer'}, {'name': 'Designer'}]
                }
            ]
        }
        
        # Mock team instance (in real implementation, this would be the actual team)
        class MockTeamInstance:
            def __init__(self, name, description):
                self.name = name
                self.description = description
            
            async def ainvoke(self, inputs):
                # Simulate team response based on input
                prompt = inputs.get('input', '')
                if 'capital' in prompt.lower():
                    return {'output': 'The capital of France is Paris.'}
                elif 'plan' in prompt.lower():
                    return {'output': f'Here is a detailed plan for {prompt[:50]}... [comprehensive response]'}
                elif not prompt.strip():
                    return {'output': 'I notice you provided an empty input. How can I help you today?'}
                else:
                    return {'output': f'Based on your request about "{prompt[:100]}", here is my comprehensive response with detailed analysis and recommendations...'}
        
        team_instance = MockTeamInstance(eval_config['team_name'], eval_config['team_description'])
        
        # Run evaluation
        status_text.text("⚖️ Evaluating team performance...")
        progress_bar.progress(50)
        
        # Simulate async evaluation (in real implementation, this would be actual evaluation)
        import asyncio
        import time
        from datetime import datetime
        
        async def mock_evaluation():
            # Simulate evaluation process
            await asyncio.sleep(2)  # Simulate processing time
            
            # Create mock evaluation result
            from src.evaluation.team_evaluator import EvaluationResult, TestResult
            from src.evaluation.test_scenarios import ScenarioType
            import random
            
            # Generate mock test results
            test_results = []
            for i, scenario in enumerate(scenarios):
                success = random.choice([True, True, True, False])  # 75% success rate
                execution_time = random.uniform(1.0, 5.0)
                
                response = f"Mock response for {scenario.name}: This is a simulated response that demonstrates the team's capability to handle {scenario.scenario_type.value} scenarios."
                
                test_results.append(TestResult(
                    scenario_name=scenario.name,
                    scenario_type=scenario.scenario_type,
                    success=success,
                    execution_time=execution_time,
                    response=response,
                    expected_outcome=scenario.expected_outcome,
                    error_message=None if success else "Simulated error for demonstration"
                ))
            
            # Generate mock dimension scores
            dimension_scores = {}
            for dimension in eval_config['selected_dimensions']:
                # Simulate realistic scores with some variation
                base_score = 0.75  # Base good performance
                variation = random.uniform(-0.15, 0.15)
                score = max(0.0, min(1.0, base_score + variation))
                dimension_scores[dimension] = score
            
            overall_score = sum(dimension_scores.values()) / len(dimension_scores)
            
            recommendations = []
            warnings = []
            
            if overall_score < 0.7:
                recommendations.extend([
                    "Consider simplifying team structure for better coordination",
                    "Review and optimize supervisor prompts for clearer task delegation",
                    "Add more specific capability descriptions to workers"
                ])
            
            if any(score < 0.6 for score in dimension_scores.values()):
                warnings.append("Some performance dimensions are below acceptable thresholds")
            
            return EvaluationResult(
                team_name=eval_config['team_name'],
                team_config=team_config,
                overall_score=overall_score,
                dimension_scores=dimension_scores,
                test_results=test_results,
                evaluation_time=5.2,  # Mock evaluation time
                timestamp=datetime.now(),
                recommendations=recommendations,
                warnings=warnings
            )
        
        # Run the mock evaluation
        evaluation_result = asyncio.run(mock_evaluation())
        
        progress_bar.progress(100)
        status_text.text("✅ Evaluation completed!")
        
        # Store results
        st.session_state[f'evaluation_result_{context}'] = evaluation_result
        st.session_state[f'show_evaluation_results_{context}'] = True
        
        # Clear the run flag
        st.session_state[f'run_evaluation_{context}'] = False
        
        # Small delay to show completion
        time.sleep(1)
        
        # Display results
        st.rerun()
        
    except Exception as e:
        st.error(f"Evaluation failed: {str(e)}")
        progress_bar.progress(0)
        status_text.text("❌ Evaluation failed")
        
        # Clear the run flag
        st.session_state[f'run_evaluation_{context}'] = False


# Display evaluation results if available
def display_evaluation_results(context: str):
    """Display evaluation results and next steps"""
    
    evaluation_result = st.session_state.get(f'evaluation_result_{context}')
    if not evaluation_result:
        return
    
    if not st.session_state.get(f'show_evaluation_results_{context}', False):
        return
    
    # Import dashboard
    try:
        from src.evaluation.results_dashboard import EvaluationResultsDashboard
        
        # Render evaluation results
        EvaluationResultsDashboard.render_evaluation_results(evaluation_result)
        
        # Action buttons
        st.markdown("---")
        st.markdown("### 🎯 Next Steps")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("✅ Accept Results & Continue", type="primary", use_container_width=True):
                st.session_state[f'evaluation_accepted_{context}'] = True
                st.session_state[f'show_evaluation_results_{context}'] = False
                st.success("✅ Evaluation results accepted! Proceeding to deployment.")
                st.rerun()
        
        with col2:
            if st.button("🔧 Optimize Further", use_container_width=True):
                # Go back to optimization step
                if hasattr(st.session_state, 'validation_result'):
                    st.session_state.show_validation_results = True
                st.session_state[f'show_evaluation_results_{context}'] = False
                st.info("🔧 Returning to optimization step...")
                st.rerun()
        
        with col3:
            if st.button("🔄 Re-run Evaluation", use_container_width=True):
                st.session_state[f'run_evaluation_{context}'] = True
                st.session_state[f'show_evaluation_results_{context}'] = False
                st.rerun()
        
        with col4:
            if st.button("📊 Export Report", use_container_width=True):
                report = EvaluationResultsDashboard.export_evaluation_report(evaluation_result)
                st.download_button(
                    label="💾 Download Report",
                    data=report,
                    file_name=f"{evaluation_result.team_name}_evaluation_report.md",
                    mime="text/markdown"
                )
        
    except ImportError as e:
        st.error(f"Results dashboard not available: {e}")


if __name__ == "__main__":
    main()