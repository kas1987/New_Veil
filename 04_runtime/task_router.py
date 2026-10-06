"""Task router — routes tasks to appropriate agents based on role and Veil state."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TaskType(Enum):
    CHAT = "chat"
    AGENT_HANDOFF = "agent_handoff"
    AGENT_COMM = "agent_comm"
    DREAM = "dream"
    DISTRICT_UNLOCK = "district_unlock"
    MEMORY_WRITE = "memory_write"
    MEMORY_READ = "memory_read"
    ALIGNMENT_CHECK = "alignment_check"
    CANON_QUERY = "canon_query"
    VOICE_PIPELINE = "voice_pipeline"


class AgentRole(Enum):
    MIRA = "mira"
    SOLENNE = "solenne"
    VAEL = "vael"
    ARCHIVIST = "archivist"
    LOREKEEPER = "lorekeeper"
    SENTINEL = "sentinel"
    AUDITOR = "auditor"
    CHAINBREAKER = "chainbreaker"
    CARTOGRAPHER = "cartographer"
    WHISPERTECH = "whispertech"


# Route mapping: task type → default agent
DEFAULT_ROUTES = {
    TaskType.CHAT: AgentRole.MIRA,
    TaskType.AGENT_HANDOFF: AgentRole.MIRA,
    TaskType.AGENT_COMM: AgentRole.MIRA,
    TaskType.DREAM: AgentRole.LOREKEEPER,
    TaskType.DISTRICT_UNLOCK: AgentRole.CARTOGRAPHER,
    TaskType.MEMORY_WRITE: AgentRole.AUDITOR,
    TaskType.MEMORY_READ: AgentRole.AUDITOR,
    TaskType.ALIGNMENT_CHECK: AgentRole.SENTINEL,
    TaskType.CANON_QUERY: AgentRole.LOREKEEPER,
    TaskType.VOICE_PIPELINE: AgentRole.WHISPERTECH,
}


@dataclass
class RoutedTask:
    task_type: TaskType
    target_agent: AgentRole
    payload: dict
    veil_state: str = "calm"
    priority: int = 5  # 1=highest, 10=lowest


def route_task(
    task_type: TaskType,
    payload: dict,
    veil_state: str = "calm",
    override_agent: AgentRole | None = None,
) -> RoutedTask:
    """Route a task to the appropriate agent.

    Args:
        task_type: The type of task
        payload: Task data
        veil_state: Current Veil state (affects priority)
        override_agent: Force route to a specific agent

    Returns:
        RoutedTask with target agent and priority
    """
    agent = override_agent or DEFAULT_ROUTES.get(task_type, AgentRole.MIRA)
    priority = _calculate_priority(task_type, veil_state)

    return RoutedTask(
        task_type=task_type,
        target_agent=agent,
        payload=payload,
        veil_state=veil_state,
        priority=priority,
    )


def _calculate_priority(task_type: TaskType, veil_state: str) -> int:
    """Calculate task priority based on type and Veil state.

    Lower number = higher priority.
    """
    base = 5

    # Alignment and dream tasks are higher priority during quasar
    if veil_state == "quasar_active":
        if task_type in (TaskType.ALIGNMENT_CHECK, TaskType.DREAM, TaskType.CANON_QUERY):
            base = 2

    # Memory writes are higher priority during storm/quasar
    if veil_state in ("storm", "quasar_active"):
        if task_type == TaskType.MEMORY_WRITE:
            base = 3

    # Voice and chat are lower priority during storm
    if veil_state == "storm":
        if task_type in (TaskType.VOICE_PIPELINE, TaskType.CHAT):
            base = 7

    return base
