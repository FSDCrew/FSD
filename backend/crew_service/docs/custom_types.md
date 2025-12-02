# Custom Type Handling

This document explains how Crew Service handles custom types in flow state fields, from type resolution during flow construction to runtime validation of user inputs.

## Overview

Custom types allow the flow system to work with rich, structured data beyond simple primitives (`string`, `int`, `bool`, etc.). Custom types are registered in `CUSTOM_TYPE_REGISTRY` (`app/models/models.py`) and can be:

- **Pydantic BaseModel classes** – Structured data models with validation (e.g., `MarketingResearch`, `ContentStrategy`)
- **IntEnum classes** – Integer enumeration types (e.g., `AllowedTemplateId`)

Custom types declared in YAML (`app/config/tasks.yaml`) are resolved to Python types during flow construction and validated at runtime when users provide input values.

## Type Registry

The `CUSTOM_TYPE_REGISTRY` is a dictionary mapping type name strings (as they appear in YAML) to their corresponding Python classes:

```182:196:app/models/models.py
CUSTOM_TYPE_REGISTRY: Dict[str, Type[BaseModel] | Type[IntEnum]] = {
    # Orshot
    "AllowedTemplateId": AllowedTemplateId,
    "OrshotSchemaField": OrshotSchemaField,
    
    # Content Strategy
    "ContentStrategy": ContentStrategy,
    "StrategyPhase": StrategyPhase,
    
    # Marketing
    "MarketingResearch": MarketingResearch,
    
    # Social Media
    "SocialMediaSchedule": SocialMediaSchedule,
}
```

Currently registered types include:

- **`AllowedTemplateId`** (IntEnum) – Orshot template identifiers
- **`OrshotSchemaField`** (BaseModel) – Orshot template field configuration
- **`ContentStrategy`** (BaseModel) – Complete content strategy with phases and settings
- **`StrategyPhase`** (BaseModel) – Individual strategy phase definition
- **`MarketingResearch`** (BaseModel) – Marketing research report data
- **`SocialMediaSchedule`** (BaseModel) – Social media posting schedule

## Type Resolution

`flow_utils.resolve_python_type` maps YAML type strings to Python types used in the dynamically generated `FlowState` Pydantic model:

```58:96:app/services/flow/flow_utils.py
def resolve_python_type(field_type: str) -> Type:
    """
    Map a YAML type string into a Python type usable in a Pydantic model.
    
    Supports:
    - Simple types: "string", "int", "float", "bool", "date"
    - Lists: "list[str]", "list[int]", "list[MarketingResearch]", etc.
    - Custom types: "MarketingResearch", "ContentStrategy", "SocialMediaSchedule" (registered models)
    - Unknown custom types: "DiscoveryDataset", etc. (treated as Dict[str, Any])
    """
    base_type_mapping: Dict[str, Type] = {
        "string": str,
        "date": str,  # stored as ISO string
        "int": int,
        "float": float,
        "bool": bool,
    }

    if field_type.startswith("list[") or field_type.startswith("List["):
        # Extract inner type from list[InnerType] or List[InnerType]
        inner_type_str = field_type[5:-1].strip()
        inner_type = resolve_python_type(inner_type_str)
        
        return List[inner_type]
    
    # Handle array syntax: Type[] (e.g., "DiscoveryDataset[]")
    if field_type.endswith("[]"):
        inner_type_str = field_type[:-2].strip()
        inner_type = resolve_python_type(inner_type_str)
        return List[inner_type]

    if field_type.lower() in base_type_mapping:
        return base_type_mapping[field_type.lower()]
    
    if field_type in CUSTOM_TYPE_REGISTRY:
        return CUSTOM_TYPE_REGISTRY[field_type]
    
    # Unknown custom types (like DiscoveryDataset) are treated as Dict[str, Any]
    return Dict[str, Any]
```

### Resolution Logic

1. **List types** – Recursively resolves the inner type (`list[MarketingResearch]` → `List[MarketingResearch]`)
2. **Base types** – Maps to Python primitives (`"string"` → `str`)
3. **Registered custom types** – Returns the class from `CUSTOM_TYPE_REGISTRY`
4. **Unknown custom types** – Falls back to `Dict[str, Any]` to allow new types without code changes

## Value Validation

`flow_utils.validate_value_type` enforces that user-provided values match the expected type schema. This function is called during input validation before flow execution.

### Validation Flow

The validation process follows this order:

1. **List validation** – Checks if the value is a list and recursively validates each item
2. **Date validation** – Validates ISO8601 date string format
3. **Custom type validation** – Handles registered custom types with multiple acceptance patterns
4. **Unknown custom type fallback** – Validates as `Dict[str, Any]` for unregistered types
5. **Primitive type validation** – Standard `isinstance` checks for base types

### Custom Type Validation Cases

When a type is found in `CUSTOM_TYPE_REGISTRY`, the validator handles four distinct cases:

#### Case 1: Already an Instance

If the value is already an instance of the expected model class (BaseModel or IntEnum), validation passes immediately:

```187:189:app/services/flow/flow_utils.py
        # Case 1: Value is already an instance of the model class (BaseModel or IntEnum)
        if isinstance(value, model_class):
            return  # Already valid, no validation needed
```

**Example:**
```python
research = MarketingResearch(content="# Report", metadata={})
validate_value_type(research, "MarketingResearch", "research")  # ✓ Passes
```

#### Case 2: Dictionary Input (Most Common)

For dictionary values, the validator attempts to parse them into the expected model:

**For BaseModel types:**
```192:199:app/services/flow/flow_utils.py
        # Case 2: Value is a dict - needs to be validated/parsed
        if isinstance(value, dict):
            if issubclass(model_class, BaseModel):
                try:
                    model_class.model_validate(value)
                except Exception as e:
                    raise ValueError(
                        f"Invalid {expected_type_str} for field '{field_name}': {str(e)}"
                    ) from e
```

**For IntEnum types:**
```200:207:app/services/flow/flow_utils.py
            elif issubclass(model_class, IntEnum):
                try:
                    enum_value = value.get("value", value)
                    model_class(enum_value)
                except (ValueError, KeyError, TypeError) as e:
                    raise ValueError(
                        f"Invalid {expected_type_str} for field '{field_name}': {str(e)}"
                    ) from e
```

**Examples:**
```python
# BaseModel from dict
validate_value_type(
    {"content": "# Report", "metadata": None},
    "MarketingResearch",
    "research"
)  # ✓ Passes

# IntEnum from dict (supports {"value": 1201} or just 1201)
validate_value_type({"value": 1201}, "AllowedTemplateId", "template_id")  # ✓ Passes
validate_value_type(1201, "AllowedTemplateId", "template_id")  # Handled by Case 3
```

#### Case 3: IntEnum with Integer Value

For IntEnum types, integer values are accepted directly:

```214:228:app/services/flow/flow_utils.py
        # Case 3: IntEnum with int value (not dict, not already enum instance)
        if issubclass(model_class, IntEnum):
            try:
                if isinstance(value, int):
                    model_class(value)  # Validate it's a valid enum value
                else:
                    raise ValueError(
                        f"Expected {expected_type_str} (int, dict, or {expected_type_str} instance) "
                        f"for field '{field_name}', but got {type(value).__name__}"
                    )
            except ValueError as e:
                raise ValueError(
                    f"Invalid {expected_type_str} for field '{field_name}': {str(e)}"
                ) from e
            return
```

**Example:**
```python
validate_value_type(1201, "AllowedTemplateId", "template_id")  # ✓ Passes
validate_value_type(9999, "AllowedTemplateId", "template_id")  # ✗ Raises ValueError (invalid enum value)
```

#### Case 4: BaseModel Non-Dict Input

If a BaseModel type is expected but the value is neither a dict nor an instance, validation fails:

```230:235:app/services/flow/flow_utils.py
        # Case 4: BaseModel but value is not dict and not instance
        if issubclass(model_class, BaseModel):
            raise ValueError(
                f"Expected {expected_type_str} (dict or {expected_type_str} instance) "
                f"for field '{field_name}', but got {type(value).__name__}"
            )
```

**Example:**
```python
validate_value_type("not a dict", "MarketingResearch", "research")  # ✗ Raises ValueError
```

### List Handling

Custom types can be used in lists. The validator recursively validates each list item:

```134:149:app/services/flow/flow_utils.py
    if expected_type_str.startswith("list[") or expected_type_str.startswith("List["):
        if not isinstance(value, list):
            raise ValueError(
                f"Expected list type for field '{field_name}', but got {type(value).__name__}"
            )
        
        inner_type_str = expected_type_str[5:-1].strip()
        
        for i, item in enumerate(value):
            try:
                validate_value_type(item, inner_type_str, f"{field_name}[{i}]")
            except ValueError as e:
                raise ValueError(
                    f"Invalid item at index {i} in list field '{field_name}': {str(e)}"
                ) from e
        return
```

**Example:**
```python
validate_value_type(
    [
        {"content": "# Report 1"},
        {"content": "# Report 2", "metadata": {"source": "api"}}
    ],
    "list[MarketingResearch]",
    "research_list"
)  # ✓ Passes - each dict is validated as MarketingResearch
```

The validator also supports array syntax (`Type[]`):

```151:165:app/services/flow/flow_utils.py
    if expected_type_str.endswith("[]"):
        if not isinstance(value, list):
            raise ValueError(
                f"Expected list type for field '{field_name}', but got {type(value).__name__}"
            )
        
        inner_type_str = expected_type_str[:-2].strip()
        for i, item in enumerate(value):
            try:
                validate_value_type(item, inner_type_str, f"{field_name}[{i}]")
            except ValueError as e:
                raise ValueError(
                    f"Invalid item at index {i} in list field '{field_name}': {str(e)}"
                ) from e
        return
```

### Unknown Custom Types

Types not found in `CUSTOM_TYPE_REGISTRY` are treated as `Dict[str, Any]`:

```242:248:app/services/flow/flow_utils.py
    # Handle Dict[str, Any] (for unknown custom types like DiscoveryDataset)
    if expected_python_type == dict:
        if not isinstance(value, dict):
            raise ValueError(
                f"Expected dict type for field '{field_name}', but got {type(value).__name__}"
            )
        return
```

This allows new custom types to be used in YAML without requiring code changes. The system accepts any dictionary structure, deferring validation to downstream consumers.

**Example:**
```python
# DiscoveryDataset is not in CUSTOM_TYPE_REGISTRY
validate_value_type(
    {"data": [1, 2, 3], "source": "api"},
    "DiscoveryDataset",
    "dataset"
)  # ✓ Passes - validated as Dict[str, Any]
```

## Usage in Flow Construction

During flow construction (`flow_builder.build_flow_state_model`), custom types are resolved to create the `FlowState` Pydantic model:

1. The dependency graph identifies which state fields are needed
2. `resolve_python_type` maps each field's YAML type string to a Python type
3. Registered custom types become their actual classes; unknown types become `Dict[str, Any]`
4. The FlowState model is synthesized with proper typing

At runtime, when users provide inputs:

1. `FlowService.validate_inputs` calls `validate_value_type` for each required field
2. Custom types are validated according to the cases described above
3. Invalid values raise `ValueError` with descriptive messages
4. Valid inputs proceed to flow execution

## Adding New Custom Types

To add a new custom type:

1. **Define the model** in `app/models/models.py`:
   ```python
   class MyCustomType(BaseModel):
       field1: str
       field2: int
   ```

2. **Register it** in `CUSTOM_TYPE_REGISTRY`:
   ```python
   CUSTOM_TYPE_REGISTRY = {
       # ... existing types ...
       "MyCustomType": MyCustomType,
   }
   ```

3. **Use it in YAML** (`app/config/tasks.yaml`):
   ```yaml
   state_fields:
     my_field:
       type: MyCustomType  # or list[MyCustomType]
       field_kind: data
   ```

4. **Validation works automatically** – The system will accept:
   - Instances of `MyCustomType`
   - Dictionaries that can be parsed into `MyCustomType` via `model_validate`

For IntEnum types, follow the same pattern but use `IntEnum` as the base class.

## Error Messages

Validation errors include the field name and expected type for debugging:

- `"Expected list type for field 'research', but got str"`
- `"Invalid MarketingResearch for field 'research': content field required"`
- `"Invalid item at index 2 in list field 'research_list': Expected dict type for field 'research_list[2]', but got str"`
- `"Invalid AllowedTemplateId for field 'template_id': 9999 is not a valid AllowedTemplateId"`

These messages help users understand what structure is expected and where validation failed.

