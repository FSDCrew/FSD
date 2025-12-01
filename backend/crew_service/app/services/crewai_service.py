import logging
from typing import Dict, List

from crewai import Agent as CrewAIAgent, Crew, Task as CrewAITask
from app.api.crud_client.models.task_read import TaskInfo
from config import agents_config, tasks_config

logger = logging.getLogger(__name__)


class CrewAIService:
    """Service for building CrewAI crews from TaskRead objects."""
    
    def build_crew(self, tasks: List[TaskInfo]) -> Crew:
        """Build a CrewAI crew from TaskRead objects."""
        agent_keys_in_tasks = {task['agent_key'] for task in tasks if 'agent_key' in task and task['agent_key']}    
        crewai_agents = self._build_agents_map(agent_keys_in_tasks)
        crewai_tasks = self._build_tasks(tasks, crewai_agents)
        
        crew = Crew(
            tasks=crewai_tasks,
            verbose=True,
        )
        
        return crew

    def _build_agents_map(self, agent_keys: set[str]) -> Dict[str, CrewAIAgent]:
        """Build a dictionary mapping agent_key to Agent objects."""
        agents_map: Dict[str, CrewAIAgent] = {}
        for agent_key in agent_keys:
            agent = self._create_agent(agent_key)
            if agent:
                agents_map[agent_key] = agent
        return agents_map

    def _create_agent(self, agent_key: str) -> CrewAIAgent | None:
        """Create a CrewAI Agent from agent_key using agents_config."""
        agent_config = agents_config.get(agent_key)
        if not agent_config:
            logger.warning(f"Agent key '{agent_key}' not found in agents_config")
            return None
        
        agent = CrewAIAgent(
            role=agent_config.get('role', ''),
            goal=agent_config.get('goal', ''),
            backstory=agent_config.get('backstory', ''),
            verbose=True,
            allow_delegation=False
        )
        return agent

    def _build_tasks(self, tasks: List[TaskInfo], agents_map: Dict[str, CrewAIAgent]) -> List[CrewAITask]:
        """Build a list of CrewAI Task objects from TaskRead objects."""
        sorted_tasks = sorted(tasks, key=lambda t: t.order)
        crewai_tasks: List[CrewAITask] = []
        
        for task_read in sorted_tasks:
            agent_key = task_read['agent_key'] if 'agent_key' in task_read else None
            agent = agents_map.get(agent_key) if agent_key else None
            if not agent:
                logger.warning(f"Agent key '{agent_key}' not found in agents_map")
                continue
            
            task = self._create_task(task_read, agent)
            if task:
                crewai_tasks.append(task)
        
        return crewai_tasks

    def _create_task(self, task_read: TaskInfo, agent: CrewAIAgent) -> CrewAITask | None:
        """Create a CrewAI Task from TaskRead object using tasks_config."""
        task_config = tasks_config.get(task_read.key) if task_read.key else None
        if not task_config:
            logger.warning(f"Task key '{task_read.key}' not found in tasks")
            return None
        
        task = CrewAITask(
            description=task_config.get('description', ''),
            expected_output=task_config.get('expected_output', ''),
            agent=agent
        )
        return task

