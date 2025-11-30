from typing import Any, Dict, List, Tuple, Type

from crewai.flow.flow import Flow
from pydantic import BaseModel

from app.api.crud_client.models.task_read import TaskRead
from app.services.flow.flow_builder import create_flow_from_tasks
from app.services.flow.dependency_graph import (
    build_flow_dependency_graph,
    infer_initial_inputs,
)
from app.services.flow.flow_utils import validate_value_type
from config import agents_config, tasks_config


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
    
    def validate_inputs(self, inputs: Dict[str, Any], tasks: List["TaskRead"]) -> None:
        """
        Validate that input values match their expected types from the state schema
        and that all required inputs are provided.
        
        Args:
            inputs: Dictionary of input field names to values
            tasks: List of TaskRead objects to build dependency graph from
            
        Raises:
            ValueError: If any input type doesn't match the expected type, if required
                       inputs are missing, or if required inputs are None
        """
        graph = build_flow_dependency_graph(tasks)
        required_inputs = infer_initial_inputs(graph, tasks)
        required_field_names = set(required_inputs["all"])
        
        if required_field_names:
            provided_field_names = set(inputs.keys()) if inputs else set()
            missing_fields = required_field_names - provided_field_names
            if missing_fields:
                raise ValueError(
                    f"Missing required input fields: {sorted(missing_fields)}"
                )
        
        for field_name, value in inputs.items():
            field_spec = graph.state_field_specs.get(field_name)
            if not field_spec:
                raise ValueError(
                    f"Unknown input field '{field_name}'. "
                    f"Field must be defined in state.fields in tasks.yaml."
                )
            
            expected_type_str = field_spec.get("type", "string")
            
            if value is None:
                if field_name in required_field_names:
                    raise ValueError(
                        f"Required input field '{field_name}' cannot be None"
                    )
                continue
            
            try:
                validate_value_type(value, expected_type_str, field_name)
            except ValueError as e:
                raise ValueError(
                    f"Type validation failed for input field '{field_name}': {str(e)}"
                ) from e
