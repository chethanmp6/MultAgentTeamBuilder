"""
Interactive Team Composition Interface with Drag-and-Drop functionality
"""
import streamlit as st
from typing import Dict, Any, List, Optional, Set
import json
from datetime import datetime

from .enhanced_agent_library import EnhancedAgentLibrary
from .agent_role_classifier import AgentRole, AgentCapability
from .real_time_validator import RealTimeValidator
from ..config.dynamic_template_generator import DynamicTemplateGenerator, TeamMember, Team


class TeamCompositionInterface:
    """Interactive interface for composing hierarchical teams."""
    
    def __init__(self, agent_library: Optional[EnhancedAgentLibrary] = None):
        self.agent_library = agent_library or EnhancedAgentLibrary()
        self.template_generator = DynamicTemplateGenerator(self.agent_library)
        self.validator = RealTimeValidator(self.agent_library, self.template_generator)
        
        # Add CSS to fix white text issues in the team composition interface
        st.markdown("""
        <style>
        /* Fix white text in team composition interface */
        .stMarkdown div[style*="background-color: #f8f9ff"] h5,
        .stMarkdown div[style*="background-color: #f8f9ff"] p {
            color: #000000 !important;
        }
        
        /* Fix text in coordinator drop zone */
        div[style*="border: 2px dashed #007bff"] h5,
        div[style*="border: 2px dashed #007bff"] p {
            color: #000000 !important;
        }
        
        /* Fix text in coordinator cards */
        div[style*="border: 2px solid #28a745"] h5,
        div[style*="border: 2px solid #28a745"] p,
        div[style*="border: 2px solid #28a745"] small,
        div[style*="border: 2px solid #28a745"] strong {
            color: #000000 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Initialize session state
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state for team composition."""
        if 'team_composition' not in st.session_state:
            st.session_state.team_composition = {
                'coordinator': None,
                'teams': {},
                'next_team_id': 1
            }
        
        if 'selected_agents' not in st.session_state:
            st.session_state.selected_agents = set()
        
        if 'current_team_config' not in st.session_state:
            st.session_state.current_team_config = None
    
    def render_team_builder(self):
        """Render the main team builder interface."""
        st.subheader("🏗️ Interactive Team Builder")
        
        # Team builder layout
        col1, col2 = st.columns([1, 2])
        
        with col1:
            self._render_agent_palette()
        
        with col2:
            self._render_team_canvas()
        
        # Action buttons
        self._render_action_buttons()
    
    def _render_agent_palette(self):
        """Render the agent palette for selection."""
        st.markdown("### 🎨 Agent Palette")
        
        # Search and filter options
        search_query = st.text_input("🔍 Search Agents", placeholder="Search by name, capability, or role...")
        
        # Role filter
        role_filter = st.selectbox(
            "Filter by Role",
            options=["All"] + [role.value.title() for role in AgentRole]
        )
        
        # Capability filter
        all_capabilities = set()
        for metadata in self.agent_library.agents.values():
            all_capabilities.update([cap.value for cap in metadata.capabilities])
        
        capability_filter = st.selectbox(
            "Filter by Capability",
            options=["All"] + sorted(list(all_capabilities))
        )
        
        # Get filtered agents
        filtered_agents = self._get_filtered_agents(search_query, role_filter, capability_filter)
        
        # Group agents by role
        agents_by_role = {
            "Coordinators": {},
            "Supervisors": {},
            "Workers": {},
            "Specialists": {}
        }
        
        for agent_id, metadata in filtered_agents.items():
            role_name = metadata.primary_role.value.title() + "s"
            if role_name in agents_by_role:
                agents_by_role[role_name][agent_id] = metadata
        
        # Render agent groups
        for role_group, agents in agents_by_role.items():
            if agents:
                with st.expander(f"📋 {role_group} ({len(agents)})", expanded=True):
                    self._render_agent_cards(agents, role_group.lower())
    
    def _get_filtered_agents(self, search_query: str, role_filter: str, capability_filter: str) -> Dict[str, Any]:
        """Get agents filtered by search and filter criteria."""
        agents = self.agent_library.get_all_agents()
        
        # Apply search filter
        if search_query:
            agents = self.agent_library.search_agents(search_query)
        
        # Apply role filter
        if role_filter != "All":
            role_enum = AgentRole(role_filter.lower())
            agents = {
                agent_id: metadata for agent_id, metadata in agents.items()
                if metadata.primary_role == role_enum or role_enum in metadata.secondary_roles
            }
        
        # Apply capability filter
        if capability_filter != "All":
            capability_enum = AgentCapability(capability_filter.lower())
            agents = {
                agent_id: metadata for agent_id, metadata in agents.items()
                if capability_enum in metadata.capabilities
            }
        
        return agents
    
    def _render_agent_cards(self, agents: Dict[str, Any], role_group: str):
        """Render agent cards with selection functionality."""
        for agent_id, metadata in agents.items():
            # Create unique key for this agent card
            card_key = f"agent_card_{agent_id}_{role_group}"
            
            # Agent card container
            card_container = st.container()
            
            with card_container:
                # Create columns for card layout
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Agent info
                    st.markdown(f"""
                    **🤖 {metadata.name}**  
                    *{metadata.description[:100]}{'...' if len(metadata.description) > 100 else ''}*
                    
                    **Capabilities:** {', '.join([cap.value for cap in metadata.capabilities][:3])}{'...' if len(metadata.capabilities) > 3 else ''}
                    
                    **Role:** {metadata.primary_role.value.title()}
                    {'🎯 Can Coordinate' if metadata.can_coordinate else ''}
                    {'👥 Can Supervise' if metadata.can_supervise else ''}
                    """)
                
                with col2:
                    # Action buttons
                    is_selected = agent_id in st.session_state.selected_agents
                    
                    if st.button(
                        "✅ Selected" if is_selected else "➕ Select",
                        key=f"select_{card_key}",
                        type="secondary" if is_selected else "primary",
                        disabled=is_selected
                    ):
                        self._select_agent(agent_id)
                        st.rerun()
                    
                    # Quick add buttons
                    if metadata.can_coordinate:
                        if st.button("👑 As Coordinator", key=f"coord_{card_key}"):
                            self._add_as_coordinator(agent_id)
                            st.rerun()
                    
                    if metadata.can_supervise:
                        if st.button("👥 As Supervisor", key=f"super_{card_key}"):
                            self._add_as_supervisor(agent_id)
                            st.rerun()
    
    def _render_team_canvas(self):
        """Render the main team composition canvas."""
        st.markdown("### 🎯 Team Canvas")
        
        # Team basic info
        team_info_col1, team_info_col2 = st.columns(2)
        
        with team_info_col1:
            team_name = st.text_input("Team Name", value="My Hierarchical Team")
        
        with team_info_col2:
            team_description = st.text_area("Team Description", height=100)
        
        # Coordinator section
        self._render_coordinator_section()
        
        # Teams section
        self._render_teams_section()
        
        # Real-time validation and preview
        self._render_validation_panel()
        
        # Team composition summary
        self._render_composition_summary()
        
        # Store team configuration
        self._update_team_config(team_name, team_description)
    
    def _render_coordinator_section(self):
        """Render the coordinator section."""
        st.markdown("#### 👑 Team Coordinator")
        
        coordinator = st.session_state.team_composition['coordinator']
        
        if coordinator:
            # Display current coordinator
            coordinator_metadata = self.agent_library.get_agent_info_summary(coordinator)
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div style="border: 2px solid #28a745; border-radius: 8px; padding: 1rem; background-color: #e8f5e8;">
                    <h5>🎯 {coordinator_metadata['name']}</h5>
                    <p><small>{coordinator_metadata['description']}</small></p>
                    <p><strong>Capabilities:</strong> {', '.join(coordinator_metadata['capabilities'][:4])}</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                if st.button("🗑️ Remove", key="remove_coordinator"):
                    st.session_state.team_composition['coordinator'] = None
                    st.rerun()
        else:
            # Show drop zone for coordinator
            st.markdown("""
            <div style="border: 2px dashed #007bff; border-radius: 8px; padding: 2rem; text-align: center; background-color: #f8f9ff;">
                <h5>👑 Drop Coordinator Here</h5>
                <p>Select a coordinator from the agent palette</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Quick coordinator selection
            coordinators = self.agent_library.get_coordinators()
            if coordinators:
                coordinator_options = ["Select a coordinator..."] + [
                    f"{metadata.name} ({agent_id})" for agent_id, metadata in coordinators.items()
                ]
                
                selected_coordinator = st.selectbox(
                    "Quick Coordinator Selection",
                    options=coordinator_options,
                    key="quick_coordinator_select"
                )
                
                if selected_coordinator != "Select a coordinator...":
                    agent_id = selected_coordinator.split(" (")[-1].rstrip(")")
                    if st.button("Add as Coordinator", key="quick_add_coordinator"):
                        self._add_as_coordinator(agent_id)
                        st.rerun()
    
    def _render_teams_section(self):
        """Render the teams section."""
        st.markdown("#### 👥 Teams")
        
        teams = st.session_state.team_composition['teams']
        
        # Add new team button
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("➕ Add Team", key="add_new_team"):
                self._add_new_team()
                st.rerun()
        
        # Render existing teams
        for team_id, team_data in teams.items():
            self._render_team_card(team_id, team_data)
    
    def _render_team_card(self, team_id: str, team_data: Dict[str, Any]):
        """Render an individual team card."""
        with st.expander(f"👥 {team_data['name']}", expanded=True):
            # Team info
            col1, col2 = st.columns([2, 1])
            
            with col1:
                team_data['name'] = st.text_input(
                    "Team Name", 
                    value=team_data['name'], 
                    key=f"team_name_{team_id}"
                )
                team_data['description'] = st.text_area(
                    "Description", 
                    value=team_data.get('description', ''),
                    key=f"team_desc_{team_id}",
                    height=80
                )
            
            with col2:
                if st.button("🗑️ Remove Team", key=f"remove_team_{team_id}"):
                    del st.session_state.team_composition['teams'][team_id]
                    st.rerun()
            
            # Supervisor section
            st.markdown("**👤 Supervisor**")
            supervisor = team_data.get('supervisor')
            
            if supervisor:
                supervisor_metadata = self.agent_library.get_agent_info_summary(supervisor)
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style="border: 1px solid #007bff; border-radius: 6px; padding: 0.5rem; background-color: #f0f8ff;">
                        <strong>👤 {supervisor_metadata['name']}</strong><br>
                        <small>{supervisor_metadata['description'][:80]}...</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("🗑️", key=f"remove_supervisor_{team_id}"):
                        team_data['supervisor'] = None
                        st.rerun()
            else:
                # Quick supervisor selection
                supervisors = self.agent_library.get_supervisors()
                supervisor_options = ["Select supervisor..."] + [
                    f"{metadata.name} ({agent_id})" for agent_id, metadata in supervisors.items()
                ]
                
                selected_supervisor = st.selectbox(
                    "Select Supervisor",
                    options=supervisor_options,
                    key=f"supervisor_select_{team_id}"
                )
                
                if selected_supervisor != "Select supervisor...":
                    agent_id = selected_supervisor.split(" (")[-1].rstrip(")")
                    if st.button("Add Supervisor", key=f"add_supervisor_{team_id}"):
                        team_data['supervisor'] = agent_id
                        st.rerun()
            
            # Workers section
            st.markdown("**🤖 Workers**")
            workers = team_data.get('workers', [])
            
            # Display current workers
            for i, worker_id in enumerate(workers):
                worker_metadata = self.agent_library.get_agent_info_summary(worker_id)
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.markdown(f"""
                    <div style="border: 1px solid #6c757d; border-radius: 4px; padding: 0.5rem; margin: 0.25rem 0;">
                        <strong>🤖 {worker_metadata['name']}</strong><br>
                        <small>{worker_metadata['description'][:60]}...</small>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("🗑️", key=f"remove_worker_{team_id}_{i}"):
                        workers.remove(worker_id)
                        team_data['workers'] = workers
                        st.rerun()
            
            # Add worker section
            workers_pool = self.agent_library.get_workers()
            available_workers = {
                agent_id: metadata for agent_id, metadata in workers_pool.items()
                if agent_id not in workers
            }
            
            if available_workers:
                worker_options = ["Select worker..."] + [
                    f"{metadata.name} ({agent_id})" for agent_id, metadata in available_workers.items()
                ]
                
                selected_worker = st.selectbox(
                    "Add Worker",
                    options=worker_options,
                    key=f"worker_select_{team_id}"
                )
                
                if selected_worker != "Select worker...":
                    agent_id = selected_worker.split(" (")[-1].rstrip(")")
                    if st.button("Add Worker", key=f"add_worker_{team_id}"):
                        workers.append(agent_id)
                        team_data['workers'] = workers
                        st.rerun()
    
    def _render_validation_panel(self):
        """Render real-time validation panel."""
        st.markdown("#### ✅ Real-time Validation")
        
        composition = st.session_state.team_composition
        
        # Perform validation
        validation = self.validator.validate_composition_live(composition)
        
        # Display status
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            status_color = {
                "valid": "🟢",
                "warning": "🟡", 
                "invalid": "🔴"
            }.get(validation["status"], "⚪")
            st.markdown(f"**Status:** {status_color} {validation['status'].title()}")
        
        with col2:
            completeness = validation.get("completeness", 0.0)
            st.metric("Completeness", f"{completeness:.1%}")
        
        with col3:
            # Live YAML preview toggle
            if st.button("🔄 Update Preview", key="update_preview"):
                # Force update preview
                pass
        
        # Display validation messages
        if validation["errors"]:
            st.error("**Errors:**")
            for error in validation["errors"]:
                st.error(f"• {error}")
        
        if validation["warnings"]:
            st.warning("**Warnings:**")
            for warning in validation["warnings"]:
                st.warning(f"• {warning}")
        
        if validation["suggestions"]:
            st.info("**Suggestions:**")
            for suggestion in validation["suggestions"]:
                st.info(f"• {suggestion}")
        
        # Team metrics
        metrics = self.validator.calculate_team_metrics(composition)
        
        if metrics["total_agents"] > 0:
            with st.expander("📊 Team Metrics", expanded=False):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Agents", metrics["total_agents"])
                with col2:
                    st.metric("Capabilities", f"{metrics['capabilities_coverage']:.1%}")
                with col3:
                    st.metric("Avg Compatibility", f"{metrics['avg_compatibility']:.2f}")
                with col4:
                    st.metric("Balance Score", f"{metrics['team_balance_score']:.2f}")
        
        # Live YAML preview
        team_name = st.session_state.get('current_team_name', 'Dynamic Team')
        team_description = st.session_state.get('current_team_description', 'Dynamically created team')
        
        yaml_preview = self.validator.generate_live_preview(composition, team_name, team_description)
        
        if yaml_preview:
            with st.expander("📄 Live YAML Preview", expanded=False):
                st.code(yaml_preview, language='yaml')
                
                # Download button for preview
                st.download_button(
                    label="📥 Download Preview",
                    data=yaml_preview,
                    file_name=f"team_preview_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yml",
                    mime="text/yaml",
                    key="download_preview"
                )
        
        # Completion suggestions
        suggestions = self.validator.get_completion_suggestions(composition)
        if suggestions and completeness < 0.8:
            with st.expander("💡 Completion Suggestions", expanded=True):
                for suggestion in suggestions[:3]:  # Show top 3 suggestions
                    priority_color = {
                        "high": "🔴",
                        "medium": "🟡",
                        "low": "🟢"
                    }.get(suggestion.get("priority", "medium"), "⚪")
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"{priority_color} {suggestion['message']}")
                    with col2:
                        if st.button("Apply", key=f"apply_{suggestion['agent_id']}_{suggestion['type']}"):
                            self._apply_suggestion(suggestion)
                            st.rerun()

    def _apply_suggestion(self, suggestion: Dict[str, Any]):
        """Apply a completion suggestion."""
        suggestion_type = suggestion.get("type")
        agent_id = suggestion.get("agent_id")
        
        if suggestion_type == "coordinator":
            st.session_state.team_composition['coordinator'] = agent_id
        elif suggestion_type == "team":
            self._add_as_supervisor(agent_id)
        elif suggestion_type == "worker":
            team_id = suggestion.get("team_id")
            if team_id in st.session_state.team_composition['teams']:
                workers = st.session_state.team_composition['teams'][team_id].get('workers', [])
                workers.append(agent_id)
                st.session_state.team_composition['teams'][team_id]['workers'] = workers
        
        st.success("Suggestion applied!")

    def _render_composition_summary(self):
        """Render team composition summary."""
        st.markdown("#### 📊 Team Summary")
        
        composition = st.session_state.team_composition
        
        # Statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            coordinator_count = 1 if composition['coordinator'] else 0
            st.metric("Coordinator", coordinator_count)
        
        with col2:
            teams_count = len(composition['teams'])
            st.metric("Teams", teams_count)
        
        with col3:
            supervisors_count = sum(1 for team in composition['teams'].values() if team.get('supervisor'))
            st.metric("Supervisors", supervisors_count)
        
        with col4:
            workers_count = sum(len(team.get('workers', [])) for team in composition['teams'].values())
            st.metric("Workers", workers_count)
        
        # Capability coverage
        all_capabilities = set()
        if composition['coordinator']:
            coordinator_metadata = self.agent_library.get_agent_info_summary(composition['coordinator'])
            all_capabilities.update(coordinator_metadata['capabilities'])
        
        for team in composition['teams'].values():
            if team.get('supervisor'):
                supervisor_metadata = self.agent_library.get_agent_info_summary(team['supervisor'])
                all_capabilities.update(supervisor_metadata['capabilities'])
            
            for worker_id in team.get('workers', []):
                worker_metadata = self.agent_library.get_agent_info_summary(worker_id)
                all_capabilities.update(worker_metadata['capabilities'])
        
        if all_capabilities:
            st.markdown("**🎯 Team Capabilities:**")
            st.markdown(f"{', '.join(sorted(all_capabilities))}")
    
    def _render_action_buttons(self):
        """Render action buttons for the team builder."""
        st.markdown("### 🎛️ Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("💾 Generate Template", type="primary"):
                self._generate_template()
        
        with col2:
            if st.button("✅ Validate Team"):
                self._validate_team()
        
        with col3:
            if st.button("🧪 Test Configuration"):
                self._test_configuration()
        
        with col4:
            if st.button("🔄 Clear All"):
                self._clear_composition()
                st.rerun()
    
    def _select_agent(self, agent_id: str):
        """Select an agent."""
        st.session_state.selected_agents.add(agent_id)
    
    def _add_as_coordinator(self, agent_id: str):
        """Add agent as coordinator."""
        st.session_state.team_composition['coordinator'] = agent_id
        st.success(f"Added {self.agent_library.agents[agent_id].name} as coordinator")
    
    def _add_as_supervisor(self, agent_id: str):
        """Add agent as supervisor to a new team."""
        team_id = str(st.session_state.team_composition['next_team_id'])
        st.session_state.team_composition['teams'][team_id] = {
            'name': f'Team {team_id}',
            'description': '',
            'supervisor': agent_id,
            'workers': []
        }
        st.session_state.team_composition['next_team_id'] += 1
        st.success(f"Created new team with {self.agent_library.agents[agent_id].name} as supervisor")
    
    def _add_new_team(self):
        """Add a new empty team."""
        team_id = str(st.session_state.team_composition['next_team_id'])
        st.session_state.team_composition['teams'][team_id] = {
            'name': f'Team {team_id}',
            'description': '',
            'supervisor': None,
            'workers': []
        }
        st.session_state.team_composition['next_team_id'] += 1
    
    def _update_team_config(self, team_name: str, team_description: str):
        """Update the current team configuration."""
        composition = st.session_state.team_composition
        
        # Store current team name and description for validation
        st.session_state.current_team_name = team_name
        st.session_state.current_team_description = team_description
        
        if composition['coordinator'] and composition['teams']:
            # Build teams data for template generator
            teams_data = []
            for team_id, team_data in composition['teams'].items():
                if team_data.get('supervisor'):
                    teams_data.append({
                        'name': team_data['name'],
                        'description': team_data.get('description', ''),
                        'supervisor_id': team_data['supervisor'],
                        'worker_ids': team_data.get('workers', []),
                        'specialization': 'general',
                        'max_workers': 10
                    })
            
            if teams_data:
                try:
                    team_config = self.template_generator.create_team_config(
                        team_name=team_name,
                        team_description=team_description,
                        coordinator_id=composition['coordinator'],
                        teams_data=teams_data
                    )
                    st.session_state.current_team_config = team_config
                except Exception as e:
                    st.error(f"Error creating team configuration: {e}")
    
    def _generate_template(self):
        """Generate and display the YAML template."""
        if st.session_state.current_team_config:
            try:
                yaml_content = self.template_generator.generate_yaml_config(st.session_state.current_team_config)
                
                st.success("✅ Template generated successfully!")
                
                # Display YAML preview
                with st.expander("📄 YAML Preview", expanded=True):
                    st.code(yaml_content, language='yaml')
                
                # Download button
                st.download_button(
                    label="📥 Download Template",
                    data=yaml_content,
                    file_name=f"{st.session_state.current_team_config.name.replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yml",
                    mime="text/yaml"
                )
                
            except Exception as e:
                st.error(f"Error generating template: {e}")
        else:
            st.warning("Please complete your team composition first")
    
    def _validate_team(self):
        """Validate the current team composition."""
        if st.session_state.current_team_config:
            validation = self.template_generator.validate_template(st.session_state.current_team_config)
            
            if validation['valid']:
                st.success("✅ Team composition is valid!")
            else:
                st.error("❌ Team composition has issues:")
                for error in validation['errors']:
                    st.error(f"• {error}")
            
            if validation['warnings']:
                st.warning("⚠️ Warnings:")
                for warning in validation['warnings']:
                    st.warning(f"• {warning}")
            
            if validation['suggestions']:
                st.info("💡 Suggestions:")
                for suggestion in validation['suggestions']:
                    st.info(f"• {suggestion}")
        else:
            st.warning("Please complete your team composition first")
    
    def _test_configuration(self):
        """Test the current configuration."""
        if st.session_state.current_team_config:
            st.info("🧪 Configuration testing feature would be implemented here")
            # This would integrate with the actual hierarchical team testing functionality
        else:
            st.warning("Please complete your team composition first")
    
    def _clear_composition(self):
        """Clear the current team composition."""
        st.session_state.team_composition = {
            'coordinator': None,
            'teams': {},
            'next_team_id': 1
        }
        st.session_state.selected_agents = set()
        st.session_state.current_team_config = None
        st.success("🔄 Team composition cleared")