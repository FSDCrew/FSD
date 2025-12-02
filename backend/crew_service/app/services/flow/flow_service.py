from enum import Enum, IntEnum
from typing import Any, Dict, List, Tuple, Type

from config import agents_config, tasks_config
from crewai.flow.flow import Flow
from pydantic import BaseModel

from app.models.models import CUSTOM_TYPE_REGISTRY, FieldTypeInfo, RequiredInputField, RequiredInputsResponse, TaskInfo
from app.services.flow.flow_builder import create_flow_from_tasks
from app.services.flow.dependency_graph import (
    build_flow_dependency_graph,
    infer_initial_inputs,
)
from app.services.flow.flow_builder import create_flow_from_tasks
from app.services.flow.flow_utils import validate_value_type


class FlowService:
    """Service for managing flow execution operations."""
    
    def __init__(self):
        """Initialize FlowService with configs from config.py."""
        self.tasks_config = tasks_config
        self.agents_config = agents_config
    
    def _parse_type_string(self, type_str: str) -> FieldTypeInfo:
        """
        Parse a type string from YAML into structured FieldTypeInfo.
        
        Handles:
        - Basic types: "string", "int", "float", "bool", "date"
        - Lists: "list[string]", "list[OrshotSchemaField]", "list[AllowedTemplateId]"
        - Custom models: "MarketingResearchReport", "ContentStrategy", etc.
        - Enums: "AllowedTemplateId", "OrshotDataType"
        - Unknown types: treated as Dict[str, Any]
        """
        original_type_str = type_str
        is_list = False
        inner_type_str = None
        
        if type_str.startswith("list[") or type_str.startswith("List["):
            is_list = True
            inner_type_str = type_str[5:-1].strip()
            type_str = inner_type_str
        
        if type_str in CUSTOM_TYPE_REGISTRY:
            type_class = CUSTOM_TYPE_REGISTRY[type_str]
            
            if issubclass(type_class, (Enum, IntEnum)):
                enum_values = [member.value for member in type_class]
                
                return FieldTypeInfo(
                    type=type_str,
                    is_list=is_list,
                    inner_type=inner_type_str if is_list else None,
                    is_enum=True,
                    enum_values=enum_values,
                    is_custom_model=False,
                )
            
            elif issubclass(type_class, BaseModel):
                try:
                    model_schema = type_class.model_json_schema()
                    # Resolve $ref references in array items to provide explicit type info
                    model_schema = self._resolve_refs_in_schema(model_schema)
                except Exception:
                    model_schema = None
                
                return FieldTypeInfo(
                    type=type_str,
                    is_list=is_list,
                    inner_type=inner_type_str if is_list else None,
                    is_enum=False,
                    enum_values=None,
                    is_custom_model=True,
                    model_schema=model_schema,
                )
        
        basic_types = {"string", "int", "float", "bool", "date"}
        if type_str.lower() in basic_types:
            return FieldTypeInfo(
                type=type_str.lower(),
                is_list=is_list,
                inner_type=inner_type_str.lower() if is_list and inner_type_str else None,
                is_enum=False,
                enum_values=None,
                is_custom_model=False,
            )
        
        return FieldTypeInfo(
            type=original_type_str,
            is_list=is_list,
            inner_type=inner_type_str if is_list else None,
            is_enum=False,
            enum_values=None,
            is_custom_model=True,
            model_schema=None,
        )

    def _resolve_refs_in_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve $ref references in JSON schema, especially for array items.
        This helps the frontend understand nested types without needing to resolve $refs.
        """
        if not isinstance(schema, dict):
            return schema
        
        resolved = schema.copy()
        
        # Resolve $defs references
        defs = resolved.get("$defs", {})
        
        # Process properties to resolve array item $refs
        if "properties" in resolved:
            properties = resolved["properties"].copy()
            for prop_name, prop_schema in properties.items():
                if isinstance(prop_schema, dict):
                    # If it's an array with $ref in items, resolve it
                    if prop_schema.get("type") == "array" and "items" in prop_schema:
                        items = prop_schema["items"]
                        if isinstance(items, dict) and "$ref" in items:
                            ref_path = items["$ref"]
                            # Extract type name from #/$defs/TypeName
                            if ref_path.startswith("#/$defs/"):
                                ref_type_name = ref_path.replace("#/$defs/", "")
                                if ref_type_name in defs:
                                    # Replace $ref with actual schema and add type info
                                    items_resolved = defs[ref_type_name].copy()
                                    # Add explicit type name for frontend
                                    items_resolved["_type_name"] = ref_type_name
                                    properties[prop_name] = {
                                        **prop_schema,
                                        "items": items_resolved
                                    }
                                    # Skip recursive call for this property since we've already resolved it
                                    continue
                    # Recursively resolve nested schemas
                    properties[prop_name] = self._resolve_refs_in_schema(prop_schema)
            resolved["properties"] = properties
        
        return resolved
    
    def get_required_inputs(self, task_reads: List["TaskInfo"]) -> RequiredInputsResponse:
        """
        Get required inputs for a list of tasks with structured type information.
        
        Args:
            task_reads: List of TaskRead objects from CrudClient
            
        Returns:
            RequiredInputsResponse with structured field type information
        """
        # Build dependency graph to access state_field_specs for type information
        graph = build_flow_dependency_graph(task_reads)
        
        # Get required inputs
        required_inputs = infer_initial_inputs(graph, task_reads)
        
        fields: List[RequiredInputField] = []
        for field_name in required_inputs["all"]:
            field_spec = graph.state_field_specs.get(field_name)
            if not field_spec:
                continue
            
            type_str = field_spec.get("type", "string")
            field_kind = field_spec.get("field_kind", "data")
            required = field_spec.get("required", True)
            placeholder = field_spec.get("placeholder")
            
            type_info = self._parse_type_string(type_str)
            
            fields.append(RequiredInputField(
                field_name=field_name,
                type_info=type_info,
                field_kind=field_kind,
                required=required,
                placeholder=placeholder,
            ))
        
        return RequiredInputsResponse(
            fields=fields,
        )
    
    def build_flow(
        self, 
        task_reads: List["TaskInfo"]
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
    
    def validate_inputs(self, inputs: Dict[str, Any], tasks: List["TaskInfo"]) -> None:
        """
        Validate that input values match their expected types from the state schema
        and that all required inputs are provided.
        
        Args:
            inputs: Dictionary of input field names to values
            tasks: List of TaskInfo objects to build dependency graph from
            
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
