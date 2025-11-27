from typing import Any, Dict, List, Tuple, Type, TYPE_CHECKING

from pydantic import BaseModel
from crewai.flow.flow import Flow

from app.services.flow.flow_builder import (
    build_flow_dependency_graph,
    create_flow_from_tasks,
    infer_initial_inputs,
)
from config import tasks_config, agents_config

if TYPE_CHECKING:
    from app.api.crud_client.models.task_read import TaskRead


class FlowService:
    """Service for managing flow execution operations."""
    
    def __init__(self):
        """Initialize FlowService with configs from config.py."""
        self.tasks_config = tasks_config
        self.agents_config = agents_config
    
    def get_required_inputs(self, task_reads: List["TaskRead"]) -> Dict[str, str]:
        """
        Get required inputs for a list of tasks, mapping field_name -> type_string.
        
        Args:
            task_reads: List of TaskRead objects from CrudClient
            
        Returns:
            Dict mapping field_name to type_string (e.g., {"theme": "string", "start_date": "date"})
        """
        # Build dependency graph to access state_field_specs for type information
        graph = build_flow_dependency_graph(task_reads)
        
        # Get required inputs
        required_inputs = infer_initial_inputs(graph, task_reads)
        
        # Map field names to their types
        result: Dict[str, str] = {}
        for field_name in required_inputs["all"]:
            field_spec = graph.state_field_specs.get(field_name)
            result[field_name] = field_spec.get("type", "string") if field_spec else "string"
        
        return result
    
    def build_flow(
        self, 
        task_reads: List["TaskRead"]
    ) -> Tuple[Type[BaseModel], Type[Flow], Dict[str, List[str]]]:
        """
        Build Flow from TaskRead objects.
        
        Args:
            task_reads: List of TaskRead objects from CrudClient
            
        Returns:
            Tuple of (FlowStateModel, FlowClass, required_inputs)
        """
        return create_flow_from_tasks(incoming_tasks=task_reads)
    
    def execute_flow(
        self, 
        flow_class: Type[Flow], 
        inputs: Dict[str, Any]
    ) -> Any:
        """
        Execute a flow instance with given inputs.
        
        Args:
            flow_class: Flow class to instantiate and execute
            inputs: Dictionary of input values for the flow
            
        Returns:
            Flow execution result
        """
        flow = flow_class()
        return flow.kickoff(inputs=inputs)

