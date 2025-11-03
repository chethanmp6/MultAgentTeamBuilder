"""
Enhanced Streamlit Web UI for Hierarchical Agent Teams
Extends the base web UI with comprehensive hierarchical team management
"""
import streamlit as st
import yaml
import os
import tempfile
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import asyncio
from datetime import datetime
import sys
import yaml

# Import project modules
from src.core.configurable_agent import ConfigurableAgent
from src.core.config_loader import ConfigLoader, AgentConfiguration
from src.core.hierarchical_config_loader import (
    HierarchicalConfigLoader, 
    HierarchicalAgentConfiguration,
    TeamConfig,
    WorkerConfig,
    CoordinatorConfig
)
from src.hierarchical.hierarchical_agent import HierarchicalAgentTeam
from src.tools.tool_registry import ToolRegistry
from src.monitoring.performance_dashboard import PerformanceDashboard

# Import new dynamic builder components
from src.ui.enhanced_agent_library import EnhancedAgentLibrary
from src.ui.team_composition_interface import TeamCompositionInterface
from src.ui.simple_team_builder import SimpleTeamBuilder
from src.config.dynamic_template_generator import DynamicTemplateGenerator

# Page configuration
st.set_page_config(
    page_title="Hierarchical Agent Teams",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS for hierarchical team visualization
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
    
    /* Drag and drop styling */
    .drop-zone {
        border: 2px dashed #007bff;
        border-radius: 8px;
        padding: 2rem;
    }
    
    /* Fix text area text color - ensure text is black and readable */
    .stTextArea textarea {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Fix text input text color */
    .stTextInput input {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Fix selectbox text color */
    .stSelectbox select {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Fix number input text color */
    .stNumberInput input {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Ensure all form elements have readable text */
    .stTextArea, .stTextInput, .stSelectbox, .stNumberInput {
        color: #000000 !important;
    }
    
    /* Fix any white text on white background issues */
    .stTextArea > div > div > textarea,
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stNumberInput > div > div > input {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Additional comprehensive text color fixes for all form elements */
    .stTextArea textarea,
    .stTextInput input,
    .stSelectbox select,
    .stNumberInput input,
    .stMultiselect select,
    .stSlider input {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Target form elements specifically */
    .stForm .stTextArea textarea,
    .stForm .stTextInput input,
    .stForm .stSelectbox select,
    .stForm .stNumberInput input,
    .stForm .stMultiselect select {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Target all input elements with more specific selectors */
    input[type="text"],
    input[type="number"],
    textarea,
    select {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Force text color for all Streamlit form widgets */
    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea,
    [data-testid="stSelectbox"] select,
    [data-testid="stNumberInput"] input,
    [data-testid="stMultiselect"] select {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Additional targeting for nested elements */
    .stTextArea > div > div > div > textarea,
    .stTextInput > div > div > div > input,
    .stSelectbox > div > div > div > select,
    .stNumberInput > div > div > div > input {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Fix ONLY the specific problematic text areas */
    .coordinator-card, .coordinator-card p, .coordinator-card h4,
    .worker-card, .worker-card p, .worker-card strong, .worker-card em, .worker-card small {
        color: #000000 !important;
    }
    
    /* Fix all text inside coordinator and worker cards */
    .coordinator-card *, .worker-card *, .team-card * {
        color: #000000 !important;
    }
    
    /* Fix specific text elements that might be white */
    .coordinator-card strong, .coordinator-card small,
    .team-card strong, .team-card small,
    .worker-card strong, .worker-card small, .worker-card em {
        color: #000000 !important;
    }
    
    /* Fix only text areas and inputs that are white on white */
    .stTextArea textarea,
    .stTextInput input,
    .stSelectbox select,
    .stNumberInput input,
    .stMultiselect select {
        color: #000000 !important;
        background-color: #ffffff !important;
    }
    
    /* Don't affect any other text elements */
    .stMarkdown, .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6,
    .stMarkdown strong, .stMarkdown em, .stMarkdown small, .stMarkdown span, .stMarkdown div {
        /* Let these keep their natural colors */
    }
        text-align: center;
        margin: 1rem 0;
        background-color: #f8f9ff;
    }
    
    .drop-zone:hover {
        background-color: #e6f3ff;
        border-color: #0056b3;
    }
</style>

<script>
function fixTextColors() {
    // Fix all textarea elements
    document.querySelectorAll('textarea').forEach(function(el) {
        el.style.color = '#000000';
        el.style.backgroundColor = '#ffffff';
    });
    
    // Fix all input elements
    document.querySelectorAll('input[type="text"], input[type="number"]').forEach(function(el) {
        el.style.color = '#000000';
        el.style.backgroundColor = '#ffffff';
    });
    
    // Fix all select elements
    document.querySelectorAll('select').forEach(function(el) {
        el.style.color = '#000000';
        el.style.backgroundColor = '#ffffff';
    });
    
    // Fix ONLY the specific problematic areas
    document.querySelectorAll('.coordinator-card, .coordinator-card p, .coordinator-card h4, .worker-card, .worker-card p, .worker-card strong, .worker-card em, .worker-card small').forEach(function(el) {
        if (el.style.color === 'white' || el.style.color === '#ffffff' || el.style.color === 'rgb(255, 255, 255)' || !el.style.color) {
            el.style.color = '#000000';
        }
    });
    
    // Fix all text inside coordinator, worker, and team cards
    document.querySelectorAll('.coordinator-card *, .worker-card *, .team-card *').forEach(function(el) {
        if (el.style.color === 'white' || el.style.color === '#ffffff' || el.style.color === 'rgb(255, 255, 255)' || !el.style.color) {
            el.style.color = '#000000';
        }
    });
    
    // Fix specific text elements that might be white
    document.querySelectorAll('.coordinator-card strong, .coordinator-card small, .team-card strong, .team-card small, .worker-card strong, .worker-card small, .worker-card em').forEach(function(el) {
        if (el.style.color === 'white' || el.style.color === '#ffffff' || el.style.color === 'rgb(255, 255, 255)' || !el.style.color) {
            el.style.color = '#000000';
        }
    });
    
    // Fix only form inputs that are white on white
    document.querySelectorAll('.stTextArea textarea, .stTextInput input, .stSelectbox select, .stNumberInput input, .stMultiselect select').forEach(function(el) {
        el.style.color = '#000000';
        el.style.backgroundColor = '#ffffff';
    });
}

// Run on page load
document.addEventListener('DOMContentLoaded', fixTextColors);

// Run periodically to catch dynamically added elements
setInterval(fixTextColors, 1000);
</script>
""", unsafe_allow_html=True)

# Initialize session state for hierarchical teams
def initialize_session_state():
    """Initialize session state variables for hierarchical team management."""
    if 'hierarchical_config' not in st.session_state:
        st.session_state.hierarchical_config = {}
    if 'current_hierarchical_team' not in st.session_state:
        st.session_state.current_hierarchical_team = None
    if 'team_instances' not in st.session_state:
        st.session_state.team_instances = {}
    if 'selected_template' not in st.session_state:
        st.session_state.selected_template = None
    if 'agent_library' not in st.session_state:
        st.session_state.agent_library = load_agent_library()
    if 'performance_dashboard' not in st.session_state:
        st.session_state.performance_dashboard = PerformanceDashboard()
    
    # Initialize new dynamic builder components
    if 'enhanced_agent_library' not in st.session_state:
        st.session_state.enhanced_agent_library = EnhancedAgentLibrary()
    if 'team_composition_interface' not in st.session_state:
        st.session_state.team_composition_interface = TeamCompositionInterface(st.session_state.enhanced_agent_library)
    if 'simple_team_builder' not in st.session_state:
        st.session_state.simple_team_builder = SimpleTeamBuilder(st.session_state.enhanced_agent_library)
    if 'dynamic_template_generator' not in st.session_state:
        st.session_state.dynamic_template_generator = DynamicTemplateGenerator(st.session_state.enhanced_agent_library)
    if 'builder_mode' not in st.session_state:
        st.session_state.builder_mode = 'simple'  # 'simple', 'advanced', or 'template'

def load_agent_library():
    """Load available agent configurations for the library."""
    library = {}
    configs_dir = Path("configs/examples")
    
    if configs_dir.exists():
        for config_file in configs_dir.glob("*.yml"):
            try:
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                    
                agent_info = config_data.get('agent', {})
                library[config_file.stem] = {
                    'name': agent_info.get('name', config_file.stem),
                    'description': agent_info.get('description', 'No description'),
                    'file_path': str(config_file),
                    'capabilities': extract_capabilities(config_data),
                    'tools': config_data.get('tools', {}).get('built_in', [])
                }
            except Exception as e:
                st.error(f"Error loading {config_file}: {e}")
    
    return library

def extract_capabilities(config_data):
    """Extract capabilities from agent configuration."""
    capabilities = []
    
    # Extract from tools
    tools = config_data.get('tools', {}).get('built_in', [])
    capabilities.extend(tools)
    
    # Extract from specialization if available
    specialization = config_data.get('specialization', {})
    if 'capabilities' in specialization:
        capabilities.extend(specialization['capabilities'])
        
    return list(set(capabilities))

def render_hierarchical_templates_sidebar():
    """Render hierarchical team templates in sidebar."""
    st.sidebar.subheader("🏢 Team Builder Mode")
    
    # Mode selection
    builder_mode = st.sidebar.radio(
        "Choose Builder Mode:",
        options=["Simple Team Builder", "Advanced Builder", "Template Library"],
        index=0 if st.session_state.builder_mode == 'simple' else (1 if st.session_state.builder_mode == 'advanced' else 2),
        help="Select how you want to build your hierarchical team"
    )
    
    if builder_mode == "Simple Team Builder":
        st.session_state.builder_mode = 'simple'
        render_simple_builder_sidebar()
    elif builder_mode == "Advanced Builder":
        st.session_state.builder_mode = 'advanced'
        render_advanced_builder_sidebar()
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
    
    # Quick stats
    library_stats = st.session_state.enhanced_agent_library.get_statistics()
    
    st.sidebar.metric("Available Agents", library_stats['total_agents'])
    st.sidebar.metric("Supervisors", library_stats['supervision_capable'])
    st.sidebar.metric("Workers", library_stats['total_agents'] - library_stats['supervision_capable'])

def render_advanced_builder_sidebar():
    """Render advanced builder options in sidebar."""
    st.sidebar.markdown("### 🎨 Advanced Team Builder")
    st.sidebar.markdown("Build complex multi-team hierarchies with coordinators and specialized teams.")
    
    # Quick stats
    library_stats = st.session_state.enhanced_agent_library.get_statistics()
    
    st.sidebar.metric("Available Agents", library_stats['total_agents'])
    st.sidebar.metric("Coordinators", library_stats['coordination_capable'])
    st.sidebar.metric("Supervisors", library_stats['supervision_capable'])
    
    # Task-based suggestions
    st.sidebar.markdown("### 💡 Quick Start")
    task_description = st.sidebar.text_area(
        "Describe your task:",
        placeholder="e.g., Research and write a comprehensive report on AI trends...",
        height=80
    )
    
    if st.sidebar.button("🚀 Generate Team Suggestions", use_container_width=True) and task_description:
        try:
            suggestions = st.session_state.enhanced_agent_library.get_team_suggestions(task_description)
            st.session_state.team_suggestions = suggestions
            st.sidebar.success("✅ Team suggestions generated!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error generating suggestions: {e}")
    
    # Auto-generate from task
    if st.sidebar.button("🎯 Auto-Generate Team", use_container_width=True) and task_description:
        try:
            team_config = st.session_state.dynamic_template_generator.generate_template_from_task(task_description)
            yaml_content = st.session_state.dynamic_template_generator.generate_yaml_config(team_config)
            st.session_state.hierarchical_config = yaml.safe_load(yaml_content)
            st.session_state.selected_template = "Auto-Generated"
            st.sidebar.success("✅ Team auto-generated!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error auto-generating team: {e}")

def render_dynamic_builder_sidebar():
    """Render dynamic builder options in sidebar."""
    st.sidebar.markdown("### 🎨 Dynamic Team Builder")
    st.sidebar.markdown("Build your team by selecting agents and defining relationships.")
    
    # Quick stats
    library_stats = st.session_state.enhanced_agent_library.get_statistics()
    
    st.sidebar.metric("Available Agents", library_stats['total_agents'])
    st.sidebar.metric("Coordinators", library_stats['coordination_capable'])
    st.sidebar.metric("Supervisors", library_stats['supervision_capable'])
    
    # Task-based suggestions
    st.sidebar.markdown("### 💡 Quick Start")
    task_description = st.sidebar.text_area(
        "Describe your task:",
        placeholder="e.g., Research and write a comprehensive report on AI trends...",
        height=80
    )
    
    if st.sidebar.button("🚀 Generate Team Suggestions", use_container_width=True) and task_description:
        try:
            suggestions = st.session_state.enhanced_agent_library.get_team_suggestions(task_description)
            st.session_state.team_suggestions = suggestions
            st.sidebar.success("✅ Team suggestions generated!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error generating suggestions: {e}")
    
    # Auto-generate from task
    if st.sidebar.button("🎯 Auto-Generate Team", use_container_width=True) and task_description:
        try:
            team_config = st.session_state.dynamic_template_generator.generate_template_from_task(task_description)
            yaml_content = st.session_state.dynamic_template_generator.generate_yaml_config(team_config)
            st.session_state.hierarchical_config = yaml.safe_load(yaml_content)
            st.session_state.selected_template = "Auto-Generated"
            st.sidebar.success("✅ Team auto-generated!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Error auto-generating team: {e}")

def render_template_library_sidebar():
    """Render template library options in sidebar."""
    st.sidebar.markdown("### 📚 Template Library")
    
    # Available hierarchical templates
    hierarchical_templates = {
        "🔬 Research Pipeline": {
            "file": "research_pipeline_team.yml",
            "description": "Browser → Analyst → Writer pipeline"
        },
        "💻 Development Team": {
            "file": "development_team.yml", 
            "description": "Requirements → Development → QA"
        },
        "🎧 Customer Service": {
            "file": "customer_service_team.yml",
            "description": "Triage → Specialist → Escalation"
        },
        "✍️ Content Creation": {
            "file": "content_creation_team.yml",
            "description": "Research → Writing → Editorial"
        }
    }
    
    # Template selection
    selected_template = st.sidebar.selectbox(
        "Choose Template:",
        options=["Select template..."] + list(hierarchical_templates.keys()),
        help="Select a pre-configured hierarchical team template"
    )
    
    if selected_template != "Select template..." and selected_template in hierarchical_templates:
        template_info = hierarchical_templates[selected_template]
        st.sidebar.caption(f"📝 {template_info['description']}")
        
        if st.sidebar.button("Load Hierarchical Template", use_container_width=True):
            template_path = Path(f"configs/examples/hierarchical/{template_info['file']}")
            if template_path.exists():
                try:
                    loader = HierarchicalConfigLoader()
                    config = loader.load_config(str(template_path))
                    st.session_state.hierarchical_config = config.model_dump()
                    st.session_state.selected_template = selected_template
                    st.sidebar.success("✅ Template loaded!")
                    st.rerun()
                except Exception as e:
                    st.sidebar.error(f"Error loading template: {e}")
            else:
                st.sidebar.error("Template file not found")

def render_enhanced_agent_library():
    """Render the enhanced agent library with role-based filtering."""
    st.subheader("🗂️ Enhanced Agent Library")
    
    # Library statistics
    library_stats = st.session_state.enhanced_agent_library.get_statistics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Agents", library_stats['total_agents'])
    with col2:
        st.metric("Coordinators", library_stats['coordination_capable'])
    with col3:
        st.metric("Supervisors", library_stats['supervision_capable'])
    with col4:
        st.metric("Avg Compatibility", f"{library_stats['average_compatibility']:.2f}")
    
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
        capability_filter = st.selectbox(
            "Filter by capability",
            options=["All"] + sorted(list(library_stats['capabilities'].keys()))
        )
    
    with col4:
        view_mode = st.selectbox("View", options=["Grid", "List", "Detailed"])
    
    # Get filtered agents
    if search_term:
        filtered_agents = st.session_state.enhanced_agent_library.search_agents(search_term)
    else:
        filtered_agents = st.session_state.enhanced_agent_library.get_all_agents()
    
    # Apply role filter
    if role_filter != "All":
        from src.ui.agent_role_classifier import AgentRole
        role_enum = AgentRole(role_filter.lower())
        filtered_agents = {
            agent_id: metadata for agent_id, metadata in filtered_agents.items()
            if metadata.primary_role == role_enum or role_enum in metadata.secondary_roles
        }
    
    # Apply capability filter
    if capability_filter != "All":
        from src.ui.agent_role_classifier import AgentCapability
        capability_enum = AgentCapability(capability_filter.lower())
        filtered_agents = {
            agent_id: metadata for agent_id, metadata in filtered_agents.items()
            if capability_enum in metadata.capabilities
        }
    
    # Display agents
    if view_mode == "Grid":
        render_enhanced_agent_grid(filtered_agents)
    elif view_mode == "List":
        render_enhanced_agent_list(filtered_agents)
    else:
        render_detailed_agent_view(filtered_agents)

def render_enhanced_agent_grid(agents):
    """Render enhanced agents in a grid layout."""
    cols = st.columns(3)
    
    for i, (agent_id, metadata) in enumerate(agents.items()):
        with cols[i % 3]:
            role_emoji = {
                "coordinator": "👑",
                "supervisor": "👥", 
                "worker": "🤖",
                "specialist": "🎯"
            }.get(metadata.primary_role.value, "🤖")
            
            with st.container():
                st.markdown(f"""
                <div class="worker-card">
                    <h4>{role_emoji} {metadata.name}</h4>
                    <p><small>{metadata.description[:100]}{'...' if len(metadata.description) > 100 else ''}</small></p>
                    <p><strong>Role:</strong> {metadata.primary_role.value.title()}</p>
                    <p><strong>Capabilities:</strong> {', '.join([cap.value for cap in metadata.capabilities][:3])}{'...' if len(metadata.capabilities) > 3 else ''}</p>
                    <p><strong>Compatibility:</strong> {metadata.compatibility_score:.2f}</p>
                    {'<p><strong>🎯 Can Coordinate</strong></p>' if metadata.can_coordinate else ''}
                    {'<p><strong>👥 Can Supervise</strong></p>' if metadata.can_supervise else ''}
                </div>
                """, unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"ℹ️ Info", key=f"info_{agent_id}"):
                        st.session_state[f"show_info_{agent_id}"] = True
                
                with col2:
                    if st.button(f"➕ Select", key=f"select_enhanced_{agent_id}"):
                        st.success(f"Selected {metadata.name}")

def render_enhanced_agent_list(agents):
    """Render enhanced agents in a list layout."""
    for agent_id, metadata in agents.items():
        role_emoji = {
            "coordinator": "👑",
            "supervisor": "👥", 
            "worker": "🤖",
            "specialist": "🎯"
        }.get(metadata.primary_role.value, "🤖")
        
        with st.expander(f"{role_emoji} {metadata.name} ({metadata.primary_role.value.title()})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Description:** {metadata.description}")
                st.write(f"**Primary Role:** {metadata.primary_role.value.title()}")
                if metadata.secondary_roles:
                    st.write(f"**Secondary Roles:** {', '.join([role.value.title() for role in metadata.secondary_roles])}")
                st.write(f"**Capabilities:** {', '.join([cap.value for cap in metadata.capabilities])}")
                st.write(f"**Tools:** {', '.join(metadata.tools)}")
                st.write(f"**Specializations:** {', '.join(metadata.specializations)}")
                st.write(f"**Compatibility Score:** {metadata.compatibility_score:.2f}")
                st.write(f"**Config File:** {metadata.file_path}")
            
            with col2:
                if metadata.can_coordinate:
                    st.success("🎯 Can Coordinate")
                if metadata.can_supervise:
                    st.success("👥 Can Supervise")
                if metadata.team_size_limit:
                    st.info(f"Max Team Size: {metadata.team_size_limit}")
                
                if st.button(f"Select Agent", key=f"select_list_enhanced_{agent_id}"):
                    st.success(f"Selected {metadata.name}")

def render_detailed_agent_view(agents):
    """Render detailed agent view with compatibility matrix."""
    selected_agent = st.selectbox(
        "Select agent for detailed view:",
        options=["Select agent..."] + [f"{metadata.name} ({agent_id})" for agent_id, metadata in agents.items()]
    )
    
    if selected_agent != "Select agent...":
        agent_id = selected_agent.split(" (")[-1].rstrip(")")
        metadata = agents[agent_id]
        
        # Agent details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown(f"""
            ### {metadata.name}
            **Description:** {metadata.description}
            
            **Primary Role:** {metadata.primary_role.value.title()}
            
            **Secondary Roles:** {', '.join([role.value.title() for role in metadata.secondary_roles]) if metadata.secondary_roles else 'None'}
            
            **Capabilities:** {', '.join([cap.value for cap in metadata.capabilities])}
            
            **Tools:** {', '.join(metadata.tools)}
            
            **Specializations:** {', '.join(metadata.specializations)}
            """)
        
        with col2:
            st.metric("Compatibility Score", f"{metadata.compatibility_score:.2f}")
            if metadata.can_coordinate:
                st.success("🎯 Can Coordinate")
            if metadata.can_supervise:
                st.success("👥 Can Supervise")
            if metadata.team_size_limit:
                st.info(f"Max Team Size: {metadata.team_size_limit}")
        
        # Compatibility with other agents
        st.markdown("### 🤝 Compatibility with Other Agents")
        
        compatibility_matrix = st.session_state.enhanced_agent_library.get_agent_compatibility_matrix()
        if agent_id in compatibility_matrix:
            agent_compatibility = compatibility_matrix[agent_id]
            # Sort by compatibility score
            sorted_compatibility = sorted(
                [(other_id, score) for other_id, score in agent_compatibility.items() if other_id != agent_id],
                key=lambda x: x[1], reverse=True
            )
            
            # Show top 5 most compatible agents
            st.markdown("**Most Compatible Agents:**")
            for other_id, score in sorted_compatibility[:5]:
                if other_id in agents:
                    other_metadata = agents[other_id]
                    st.write(f"• {other_metadata.name}: {score:.2f}")

def render_agent_library():
    """Render the agent library for selecting workers."""
    st.subheader("🗂️ Agent Library")
    
    # Search and filter functionality
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        search_term = st.text_input("Search agents", placeholder="Search by name or capability...")
    
    with col2:
        capability_filter = st.selectbox(
            "Filter by capability",
            options=["All"] + list(set(
                cap for agent in st.session_state.agent_library.values() 
                for cap in agent['capabilities']
            ))
        )
    
    with col3:
        view_mode = st.selectbox("View", options=["Grid", "List"])
    
    # Filter agents based on search and capability
    filtered_agents = {}
    for agent_id, agent in st.session_state.agent_library.items():
        match_search = not search_term or search_term.lower() in agent['name'].lower() or search_term.lower() in agent['description'].lower()
        match_capability = capability_filter == "All" or capability_filter in agent['capabilities']
        
        if match_search and match_capability:
            filtered_agents[agent_id] = agent
    
    # Display agents
    if view_mode == "Grid":
        render_agent_grid(filtered_agents)
    else:
        render_agent_list(filtered_agents)

def render_agent_grid(agents):
    """Render agents in a grid layout."""
    cols = st.columns(3)
    
    for i, (agent_id, agent) in enumerate(agents.items()):
        with cols[i % 3]:
            with st.container():
                st.markdown(f"""
                <div class="worker-card">
                    <h4>{agent['name']}</h4>
                    <p><small>{agent['description']}</small></p>
                    <p><strong>Capabilities:</strong> {', '.join(agent['capabilities'][:3])}{'...' if len(agent['capabilities']) > 3 else ''}</p>
                </div>
                """, unsafe_allow_html=True)
                
                if st.button(f"Select {agent['name']}", key=f"select_{agent_id}"):
                    st.session_state[f"selected_agent_{agent_id}"] = True
                    st.success(f"Selected {agent['name']}")

def render_agent_list(agents):
    """Render agents in a list layout."""
    for agent_id, agent in agents.items():
        with st.expander(f"📋 {agent['name']}"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Description:** {agent['description']}")
                st.write(f"**Capabilities:** {', '.join(agent['capabilities'])}")
                st.write(f"**Tools:** {', '.join(agent['tools'])}")
                st.write(f"**Config File:** {agent['file_path']}")
            
            with col2:
                if st.button(f"Select", key=f"select_list_{agent_id}"):
                    st.session_state[f"selected_agent_{agent_id}"] = True
                    st.success(f"Selected {agent['name']}")

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
                render_add_worker_dialog(team_index)
            
            if st.button(f"Edit Team", key=f"edit_team_{team_index}"):
                render_edit_team_dialog(team_index)
            
            if st.button(f"Remove Team", key=f"remove_team_{team_index}"):
                if st.confirm(f"Remove {team_name}?"):
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

def render_add_worker_dialog(team_index):
    """Render dialog for adding a new worker to a team."""
    st.write("#### Add New Worker")
    
    with st.form(f"add_worker_form_{team_index}"):
        col1, col2 = st.columns(2)
        
        with col1:
            worker_name = st.text_input("Worker Name")
            worker_role = st.text_input("Worker Role")
        
        with col2:
            # Agent selection from library
            available_agents = list(st.session_state.agent_library.keys())
            selected_agent = st.selectbox("Base Configuration", options=available_agents)
        
        worker_description = st.text_area("Description")
        
        capabilities = st.multiselect(
            "Capabilities",
            options=["web_search", "code_generation", "data_analysis", "writing", "research", "debugging"],
            default=st.session_state.agent_library.get(selected_agent, {}).get('capabilities', [])[:3]
        )
        
        if st.form_submit_button("Add Worker"):
            add_worker_to_team(team_index, {
                'name': worker_name,
                'role': worker_role,
                'config_file': st.session_state.agent_library[selected_agent]['file_path'],
                'description': worker_description,
                'capabilities': capabilities,
                'priority': 1
            })
            st.success(f"Added {worker_name} to team")
            st.rerun()

def add_worker_to_team(team_index, worker_config):
    """Add a worker to the specified team."""
    if 'teams' in st.session_state.hierarchical_config:
        if team_index < len(st.session_state.hierarchical_config['teams']):
            if 'workers' not in st.session_state.hierarchical_config['teams'][team_index]:
                st.session_state.hierarchical_config['teams'][team_index]['workers'] = []
            
            st.session_state.hierarchical_config['teams'][team_index]['workers'].append(worker_config)

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
            test_hierarchical_team()
    
    with col3:
        if st.button("🚀 Deploy Team"):
            deploy_hierarchical_team()
    
    with col4:
        if st.button("📊 View Metrics"):
            show_team_metrics()

def save_hierarchical_config():
    """Save the current hierarchical configuration."""
    if not st.session_state.hierarchical_config:
        st.error("No configuration to save")
        return
    
    # Generate filename
    team_name = st.session_state.hierarchical_config.get('team', {}).get('name', 'custom_team')
    safe_name = "".join(c for c in team_name if c.isalnum() or c in (' ', '_')).rstrip()
    filename = f"{safe_name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yml"
    
    # Create save directory
    save_dir = Path("configs/custom/hierarchical")
    save_dir.mkdir(parents=True, exist_ok=True)
    
    # Save configuration
    save_path = save_dir / filename
    try:
        with open(save_path, 'w') as f:
            yaml.dump(st.session_state.hierarchical_config, f, default_flow_style=False, indent=2)
        
        st.success(f"✅ Configuration saved to {save_path}")
        
        # Offer download
        with open(save_path, 'r') as f:
            st.download_button(
                label="📥 Download Configuration",
                data=f.read(),
                file_name=filename,
                mime="text/yaml"
            )
            
    except Exception as e:
        st.error(f"Error saving configuration: {e}")

def test_hierarchical_team():
    """Test the current hierarchical team configuration."""
    if not st.session_state.hierarchical_config:
        st.error("No configuration to test")
        return
    
    st.write("#### 🧪 Team Testing")
    
    # Save config to temporary file for testing
    try:
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            yaml.dump(st.session_state.hierarchical_config, f, default_flow_style=False)
            temp_config_path = f.name
        
        # Load and validate configuration
        loader = HierarchicalConfigLoader()
        config = loader.load_config(temp_config_path)
        
        st.success("✅ Configuration is valid!")
        
        # Test input interface
        test_input = st.text_area(
            "Enter test message:",
            placeholder="Enter a task for your hierarchical team to handle...",
            height=100
        )
        
        if st.button("🚀 Run Test") and test_input:
            with st.spinner("Running hierarchical team test..."):
                try:
                    # Create hierarchical team instance
                    team = HierarchicalAgentTeam(
                        name=config.team.name,
                        hierarchical_config=st.session_state.hierarchical_config
                    )
                    
                    # Add teams and workers based on configuration
                    for team_config in config.teams:
                        for worker_config in team_config.workers:
                            team.create_worker_from_config(
                                name=worker_config.name,
                                config_file=worker_config.config_file,
                                team_name=team_config.name
                            )
                    
                    # Run the test
                    result = team.run(test_input)
                    
                    st.write("#### 📋 Test Results")
                    st.write(f"**Response:** {result.get('response', 'No response')}")
                    
                    with st.expander("📊 Detailed Results"):
                        st.json(result)
                    
                except Exception as e:
                    st.error(f"Test failed: {e}")
        
        # Clean up temp file
        os.unlink(temp_config_path)
        
    except Exception as e:
        st.error(f"Error during testing: {e}")

def deploy_hierarchical_team():
    """Deploy the hierarchical team for production use."""
    st.write("#### 🚀 Team Deployment")
    
    if not st.session_state.hierarchical_config:
        st.error("No configuration to deploy")
        return
    
    deployment_name = st.text_input("Deployment Name", value=f"deployment_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
    environment = st.selectbox("Environment", options=["development", "staging", "production"])
    
    if st.button("Deploy Team"):
        # In a real implementation, this would deploy to your infrastructure
        st.success(f"✅ Team '{deployment_name}' deployed to {environment}")
        st.info("📝 Deployment details would be shown here in a production system")

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
                config_data = yaml.safe_load(uploaded_file.read())
                st.session_state.hierarchical_config = config_data
                st.success(f"✅ Loaded configuration from {uploaded_file.name}")
                st.rerun()
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
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                    yaml.dump(st.session_state.hierarchical_config, f, default_flow_style=False)
                    temp_path = f.name
                
                loader = HierarchicalConfigLoader()
                config = loader.load_config(temp_path)
                
                st.success("✅ Configuration is valid!")
                
                # Show validation details
                with st.expander("Validation Details"):
                    st.write("**Team Information:**")
                    st.write(f"- Name: {config.team.name}")
                    st.write(f"- Type: {config.team.type}")
                    st.write(f"- Teams: {len(config.teams)}")
                    
                    total_workers = sum(len(team.workers) for team in config.teams)
                    st.write(f"- Total Workers: {total_workers}")
                
                os.unlink(temp_path)
                
            except Exception as e:
                st.error(f"❌ Configuration validation failed: {e}")
        else:
            st.warning("No configuration to validate")
    
    # Template management
    st.write("### 📚 Template Management")
    
    # List available templates
    template_dir = Path("configs/examples/hierarchical")
    if template_dir.exists():
        available_templates = list(template_dir.glob("*.yml"))
        
        if available_templates:
            st.write("**Available Templates:**")
            
            for template_file in available_templates:
                with st.expander(f"📋 {template_file.stem}"):
                    try:
                        with open(template_file, 'r') as f:
                            template_data = yaml.safe_load(f)
                        
                        team_info = template_data.get('team', {})
                        st.write(f"**Name:** {team_info.get('name', 'Unknown')}")
                        st.write(f"**Description:** {team_info.get('description', 'No description')}")
                        st.write(f"**Teams:** {len(template_data.get('teams', []))}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"Load Template", key=f"load_{template_file.stem}"):
                                st.session_state.hierarchical_config = template_data
                                st.success(f"Loaded {template_file.stem}")
                                st.rerun()
                        
                        with col2:
                            if st.button(f"View YAML", key=f"view_{template_file.stem}"):
                                st.code(yaml.dump(template_data, default_flow_style=False), 
                                        language='yaml')
                    
                    except Exception as e:
                        st.error(f"Error loading template: {e}")
        else:
            st.info("No templates found in hierarchical directory")
    else:
        st.info("Template directory not found")
    
    # Configuration comparison
    st.write("### 🔍 Configuration Comparison")
    
    if st.session_state.hierarchical_config:
        comparison_file = st.file_uploader(
            "Upload configuration to compare", 
            type=['yml', 'yaml'],
            key="comparison_config"
        )
        
        if comparison_file is not None:
            try:
                comparison_config = yaml.safe_load(comparison_file.read())
                
                st.write("**Configuration Differences:**")
                
                # Simple comparison of key fields
                current_teams = len(st.session_state.hierarchical_config.get('teams', []))
                comparison_teams = len(comparison_config.get('teams', []))
                
                if current_teams != comparison_teams:
                    st.write(f"• Teams: Current ({current_teams}) vs Comparison ({comparison_teams})")
                
                current_coordinator = st.session_state.hierarchical_config.get('coordinator', {}).get('name', '')
                comparison_coordinator = comparison_config.get('coordinator', {}).get('name', '')
                
                if current_coordinator != comparison_coordinator:
                    st.write(f"• Coordinator: '{current_coordinator}' vs '{comparison_coordinator}'")
                
                # Could add more detailed comparison logic here
                
            except Exception as e:
                st.error(f"Error comparing configurations: {e}")

def show_team_metrics():
    """Show team performance metrics."""
    st.write("#### 📊 Team Performance Metrics")
    
    # Mock metrics for demonstration
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Response Time", "2.3s", "-0.5s")
    
    with col2:
        st.metric("Success Rate", "94.2%", "+2.1%")
    
    with col3:
        st.metric("Tasks Completed", "156", "+23")
    
    with col4:
        st.metric("Team Efficiency", "87%", "+5%")
    
    # Performance chart placeholder
    st.info("📈 Detailed performance charts would be shown here in a production system")

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

def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Main title
    st.title("🏢 Hierarchical Agent Teams")
    st.write("Build and manage complex hierarchical agent teams with specialized roles and coordination")
    
    # Sidebar
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
        st.session_state.simple_team_builder.render()
        
    elif st.session_state.builder_mode == 'advanced':
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🎨 Advanced Builder",
            "🗂️ Agent Library", 
            "🔗 Hierarchy View", 
            "🧪 Testing", 
            "📊 Performance Dashboard",
            "⚙️ Configuration"
        ])
        
        with tab1:
            st.session_state.team_composition_interface.render_team_builder()
        
        with tab2:
            render_enhanced_agent_library()
        
        with tab3:
            render_hierarchy_visualization()
        
        with tab4:
            if st.session_state.hierarchical_config or hasattr(st.session_state, 'current_team_config'):
                test_hierarchical_team()
            else:
                st.info("Build a team configuration to access testing features")
        
        with tab5:
            st.session_state.performance_dashboard.render_dashboard(
                st.session_state.current_hierarchical_team
            )
        
        with tab6:
            render_configuration_management()
    
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
            render_agent_library()
        
        with tab3:
            render_hierarchy_visualization()
        
        with tab4:
            if st.session_state.hierarchical_config:
                test_hierarchical_team()
            else:
                st.info("Load a hierarchical configuration to access testing features")
        
        with tab5:
            st.session_state.performance_dashboard.render_dashboard(
                st.session_state.current_hierarchical_team
            )
        
        with tab6:
            render_configuration_management()

if __name__ == "__main__":
    main()