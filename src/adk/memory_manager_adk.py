"""
ADK-compatible memory management system.
Migrated from LangChain-based memory_manager.py to Google ADK.
"""
import json
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
import hashlib

# ADK imports (with fallback for development)
try:
    from google_adk.memory import SessionMemory, ConversationMemory
    from google_adk.core import Message
    ADK_AVAILABLE = True
except ImportError:
    # Fallback for development/testing
    print("Warning: Google ADK memory not available. Using mock implementations.")

    class SessionMemory:
        def __init__(self):
            self.data = {}

        def store(self, key: str, value: Any):
            self.data[key] = value

        def retrieve(self, key: str) -> Any:
            return self.data.get(key)

    class ConversationMemory:
        def __init__(self):
            self.messages = []

        def add_message(self, message):
            self.messages.append(message)

        def get_messages(self, limit: int = None):
            if limit:
                return self.messages[-limit:]
            return self.messages

    class Message:
        def __init__(self, content: str, role: str = "user"):
            self.content = content
            self.role = role

    ADK_AVAILABLE = False

from .config_loader_adk import ADKMemoryConfig


class ADKMemoryManager:
    """ADK-compatible memory management system."""

    def __init__(self, memory_config: ADKMemoryConfig):
        self.config = memory_config
        self.session_memory = None
        self.conversation_memory = None
        self.semantic_memory = {}
        self.episodic_memory = []
        self.procedural_memory = {}
        self.memory_store = {}

        # Initialize based on configuration
        self._initialize_memory_backend()

    def _initialize_memory_backend(self):
        """Initialize ADK memory backend based on configuration."""
        if not self.config.enabled:
            return

        if ADK_AVAILABLE:
            # Initialize ADK memory components
            if self.config.settings.session_management:
                self.session_memory = SessionMemory()

            if self.config.types.conversation:
                self.conversation_memory = ConversationMemory()
        else:
            # Fallback to mock implementations
            self.session_memory = SessionMemory()
            self.conversation_memory = ConversationMemory()

        # Initialize custom memory types
        if self.config.storage.backend == "memory":
            # In-memory storage (default)
            pass
        elif self.config.storage.backend == "vertex":
            # Initialize Vertex AI memory storage
            # This would integrate with Vertex AI memory services
            pass

    def store_interaction(self, messages: List[Union[Message, Dict]], response: Union[Message, Dict]):
        """
        Store an interaction in ADK memory.

        Args:
            messages: List of input messages
            response: Response message
        """
        if not self.config.enabled:
            return

        # Convert to ADK Message format if needed
        adk_messages = self._convert_to_adk_messages(messages)
        adk_response = self._convert_to_adk_message(response)

        # Store in conversation memory
        if self.conversation_memory and self.config.types.conversation:
            for msg in adk_messages:
                self.conversation_memory.add_message(msg)
            self.conversation_memory.add_message(adk_response)

        # Store interaction metadata
        interaction_id = self._generate_interaction_id(messages, response)
        timestamp = datetime.now()

        interaction = {
            "id": interaction_id,
            "timestamp": timestamp.isoformat(),
            "messages": [self._message_to_dict(msg) for msg in adk_messages],
            "response": self._message_to_dict(adk_response),
            "metadata": {}
        }

        # Store in episodic memory
        if self.config.types.episodic:
            self.episodic_memory.append(interaction)
            self._cleanup_old_episodes()

        # Extract semantic information
        if self.config.types.semantic:
            self._extract_semantic_info(adk_messages, adk_response)

        # Update procedural memory
        if self.config.types.procedural:
            self._update_procedural_memory(adk_messages, adk_response)

    def retrieve_memory(self, query: str, memory_type: str = "all") -> Dict[str, Any]:
        """
        Retrieve relevant memory based on query.

        Args:
            query: Search query
            memory_type: Type of memory to search ("all", "conversation", "semantic", "episodic", "procedural")

        Returns:
            Dictionary containing relevant memory items
        """
        if not self.config.enabled:
            return {}

        relevant_memory = {}

        # Retrieve conversation memory
        if memory_type in ["all", "conversation"] and self.config.types.conversation:
            relevant_memory["conversation"] = self._search_conversation_memory(query)

        # Retrieve semantic memory
        if memory_type in ["all", "semantic"] and self.config.types.semantic:
            relevant_memory["semantic"] = self._search_semantic_memory(query)

        # Retrieve episodic memory
        if memory_type in ["all", "episodic"] and self.config.types.episodic:
            relevant_memory["episodic"] = self._search_episodic_memory(query)

        # Retrieve procedural memory
        if memory_type in ["all", "procedural"] and self.config.types.procedural:
            relevant_memory["procedural"] = self._get_procedural_memory(query)

        return relevant_memory

    def get_relevant_context(self, query: str, max_items: int = 5) -> str:
        """Get relevant context as a formatted string for ADK agents."""
        memory = self.retrieve_memory(query)
        context_parts = []

        # Add conversation context
        if "conversation" in memory and memory["conversation"]:
            recent_messages = memory["conversation"][-max_items:]
            conversation_text = "; ".join([
                f"{msg.get('role', 'user')}: {msg.get('content', '')}"
                for msg in recent_messages
            ])
            context_parts.append(f"Recent conversation: {conversation_text}")

        # Add semantic context
        if "semantic" in memory and memory["semantic"]:
            facts = memory["semantic"][:max_items]
            context_parts.append("Relevant facts: " + "; ".join(facts))

        # Add episodic context
        if "episodic" in memory and memory["episodic"]:
            episodes = memory["episodic"][:max_items]
            episode_summaries = [ep.get("summary", "Previous interaction") for ep in episodes]
            context_parts.append("Previous interactions: " + "; ".join(episode_summaries))

        # Add procedural context
        if "procedural" in memory and memory["procedural"]:
            procedures = memory["procedural"]
            context_parts.append("Learned procedures: " + "; ".join(procedures.keys()))

        return " | ".join(context_parts) if context_parts else ""

    def store_session_data(self, key: str, value: Any):
        """Store data in session memory."""
        if self.session_memory and self.config.settings.session_management:
            self.session_memory.store(key, value)

    def retrieve_session_data(self, key: str) -> Any:
        """Retrieve data from session memory."""
        if self.session_memory and self.config.settings.session_management:
            return self.session_memory.retrieve(key)
        return None

    def _convert_to_adk_messages(self, messages: List[Union[Message, Dict]]) -> List[Message]:
        """Convert messages to ADK Message format."""
        adk_messages = []
        for msg in messages:
            adk_messages.append(self._convert_to_adk_message(msg))
        return adk_messages

    def _convert_to_adk_message(self, message: Union[Message, Dict]) -> Message:
        """Convert a single message to ADK Message format."""
        if ADK_AVAILABLE and isinstance(message, Message):
            return message

        # Handle dictionary format
        if isinstance(message, dict):
            content = message.get("content", str(message))
            role = message.get("role", "user")
        else:
            # Handle LangChain message objects
            content = getattr(message, "content", str(message))
            role = getattr(message, "type", "user").lower()
            if "human" in role:
                role = "user"
            elif "ai" in role:
                role = "assistant"

        return Message(content=content, role=role)

    def _search_conversation_memory(self, query: str) -> List[Dict[str, Any]]:
        """Search conversation memory for relevant messages."""
        if not self.conversation_memory:
            return []

        query_words = set(query.lower().split())
        relevant_messages = []

        messages = self.conversation_memory.get_messages(limit=50)  # Get recent messages
        for msg in messages:
            if hasattr(msg, 'content'):
                content = msg.content
            else:
                content = str(msg)

            message_words = set(content.lower().split())
            overlap = len(query_words.intersection(message_words))

            if overlap > 0:
                relevant_messages.append({
                    "content": content,
                    "role": getattr(msg, 'role', 'unknown'),
                    "relevance": overlap
                })

        # Sort by relevance and return top results
        relevant_messages.sort(key=lambda x: x["relevance"], reverse=True)
        return relevant_messages[:5]

    def _extract_semantic_info(self, messages: List[Message], response: Message):
        """Extract semantic information from interaction."""
        # Simple semantic extraction (enhanced version would use NLP)
        all_content = []
        for msg in messages:
            all_content.append(getattr(msg, 'content', str(msg)))
        all_content.append(getattr(response, 'content', str(response)))

        content = " ".join(all_content)

        # Look for facts patterns
        if "is" in content.lower():
            sentences = content.split(".")
            for sentence in sentences:
                if " is " in sentence.lower():
                    fact = sentence.strip()
                    fact_id = hashlib.md5(fact.encode()).hexdigest()[:8]
                    self.semantic_memory[fact_id] = {
                        "fact": fact,
                        "confidence": 0.8,
                        "timestamp": datetime.now().isoformat()
                    }

    def _search_semantic_memory(self, query: str) -> List[str]:
        """Search semantic memory for relevant facts."""
        query_words = set(query.lower().split())
        relevant_facts = []

        for fact_data in self.semantic_memory.values():
            fact_words = set(fact_data["fact"].lower().split())
            overlap = len(query_words.intersection(fact_words))
            if overlap > 0:
                relevant_facts.append((fact_data["fact"], overlap))

        # Sort by relevance and return top facts
        relevant_facts.sort(key=lambda x: x[1], reverse=True)
        return [fact[0] for fact in relevant_facts[:5]]

    def _search_episodic_memory(self, query: str) -> List[Dict[str, Any]]:
        """Search episodic memory for relevant interactions."""
        query_words = set(query.lower().split())
        relevant_episodes = []

        for episode in self.episodic_memory:
            # Search in all messages of the episode
            episode_text = " ".join([
                msg["content"] for msg in episode["messages"]
            ] + [episode["response"]["content"]])

            episode_words = set(episode_text.lower().split())
            overlap = len(query_words.intersection(episode_words))

            if overlap > 0:
                relevant_episodes.append((episode, overlap))

        # Sort by relevance and return top episodes
        relevant_episodes.sort(key=lambda x: x[1], reverse=True)
        return [ep[0] for ep in relevant_episodes[:3]]

    def _update_procedural_memory(self, messages: List[Message], response: Message):
        """Update procedural memory based on successful patterns."""
        response_content = getattr(response, 'content', str(response))

        if "successfully" in response_content.lower() or "completed" in response_content.lower():
            # Extract the pattern that led to success
            if messages:
                last_message = messages[-1]
                pattern = getattr(last_message, 'content', str(last_message))[:100]
                pattern_id = hashlib.md5(pattern.encode()).hexdigest()[:8]

                if pattern_id in self.procedural_memory:
                    self.procedural_memory[pattern_id]["success_count"] += 1
                else:
                    self.procedural_memory[pattern_id] = {
                        "pattern": pattern,
                        "success_count": 1,
                        "last_used": datetime.now().isoformat()
                    }

    def _get_procedural_memory(self, query: str) -> Dict[str, Any]:
        """Get relevant procedural memory."""
        # Return most successful patterns
        sorted_procedures = sorted(
            self.procedural_memory.items(),
            key=lambda x: x[1]["success_count"],
            reverse=True
        )

        return {
            proc_id: proc_data["pattern"]
            for proc_id, proc_data in sorted_procedures[:3]
        }

    def _cleanup_old_episodes(self):
        """Clean up old episodic memories based on retention policy."""
        if len(self.episodic_memory) > self.config.settings.max_memory_size:
            # Remove oldest episodes
            self.episodic_memory = self.episodic_memory[-self.config.settings.max_memory_size:]

        # Remove episodes older than retention period
        cutoff_date = datetime.now() - timedelta(days=self.config.settings.retention_days)
        self.episodic_memory = [
            episode for episode in self.episodic_memory
            if datetime.fromisoformat(episode["timestamp"]) > cutoff_date
        ]

    def _generate_interaction_id(self, messages: List, response) -> str:
        """Generate unique ID for interaction."""
        content = str(messages) + str(response) + str(datetime.now())
        return hashlib.md5(content.encode()).hexdigest()[:12]

    def _message_to_dict(self, message: Union[Message, Dict]) -> Dict[str, Any]:
        """Convert message to dictionary."""
        if isinstance(message, dict):
            return message

        return {
            "role": getattr(message, "role", "unknown"),
            "content": getattr(message, "content", str(message)),
            "timestamp": datetime.now().isoformat()
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get memory usage statistics."""
        return {
            "memory_enabled": self.config.enabled,
            "adk_available": ADK_AVAILABLE,
            "session_management": self.config.settings.session_management,
            "conversation_messages": len(self.conversation_memory.messages) if self.conversation_memory else 0,
            "semantic_facts": len(self.semantic_memory),
            "episodic_interactions": len(self.episodic_memory),
            "procedural_patterns": len(self.procedural_memory),
            "retention_days": self.config.settings.retention_days,
            "max_memory_size": self.config.settings.max_memory_size
        }

    def clear_memory(self):
        """Clear all memory."""
        self.semantic_memory.clear()
        self.episodic_memory.clear()
        self.procedural_memory.clear()
        self.memory_store.clear()

        if self.conversation_memory:
            self.conversation_memory.messages.clear()

        if self.session_memory:
            self.session_memory.data.clear()

    def export_history(self, format_type: str = "json") -> str:
        """Export memory history."""
        history = {
            "semantic_memory": self.semantic_memory,
            "episodic_memory": self.episodic_memory,
            "procedural_memory": self.procedural_memory,
            "conversation_messages": [
                self._message_to_dict(msg) for msg in self.conversation_memory.messages
            ] if self.conversation_memory else [],
            "export_timestamp": datetime.now().isoformat(),
            "adk_version": "1.0.0"
        }

        if format_type.lower() == "json":
            return json.dumps(history, indent=2)
        else:
            return str(history)

    def import_history(self, history_data: str, format_type: str = "json"):
        """Import memory history."""
        if format_type.lower() == "json":
            data = json.loads(history_data)
            self.semantic_memory = data.get("semantic_memory", {})
            self.episodic_memory = data.get("episodic_memory", [])
            self.procedural_memory = data.get("procedural_memory", {})

            # Import conversation messages if available
            if "conversation_messages" in data and self.conversation_memory:
                for msg_data in data["conversation_messages"]:
                    message = Message(
                        content=msg_data.get("content", ""),
                        role=msg_data.get("role", "user")
                    )
                    self.conversation_memory.add_message(message)

    def get_adk_integration_info(self) -> Dict[str, Any]:
        """Get information about ADK integration status."""
        return {
            "adk_available": ADK_AVAILABLE,
            "session_memory_active": self.session_memory is not None,
            "conversation_memory_active": self.conversation_memory is not None,
            "memory_types_enabled": {
                "conversation": self.config.types.conversation,
                "semantic": self.config.types.semantic,
                "episodic": self.config.types.episodic,
                "procedural": self.config.types.procedural
            },
            "session_management": self.config.settings.session_management
        }