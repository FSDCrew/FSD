"""Agent factory utilities."""

from __future__ import annotations

from typing import Dict

from crewai import Agent as CrewAIAgent

from config import agents_config
from .flow_utils import tool_resolver
from .llm_registry import general_llm


def build_crewai_agents() -> Dict[str, CrewAIAgent]:
    """Build CrewAI Agent instances from agent config in config.py."""

    agents: Dict[str, CrewAIAgent] = {}

    for agent_key, agent_config in agents_config.items():
        tools = tool_resolver.resolve(agent_config)

        agents[agent_key] = CrewAIAgent(
            role=agent_config.get("role", ""),
            goal=agent_config.get("goal", ""),
            backstory=agent_config.get("backstory", ""),
            tools=tools or None,
            verbose=True,
            llm=general_llm,
            # reasoning=True,
            # max_reasoning_attempts=5
        )

    return agents

