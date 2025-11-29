# Required Inputs - Frontend Integration Guide

This document explains how to integrate with the `/crew/{crew_id}/required-inputs` endpoint in your frontend application.

## API Endpoint

**Endpoint**: `GET /crew/{crew_id}/required-inputs`

**Authentication**: Requires a valid bearer token or Cognito cookie in the Authorization header.

**Response**: Returns a `RequiredInputsResponse` containing an array of `RequiredInputField` objects.

## Response Contract

The endpoint returns the following payload structure:

```jsonc
{
  "fields": [
    {
      "field_name": "theme",
      "field_kind": "context",
      "required": true,
      "placeholder": "Enter your campaign theme",
      "type_info": {
        "type": "string",
        "is_list": false,
        "is_enum": false,
        "is_custom_model": false
      }
    },
    {
      "field_name": "templateId",
      "field_kind": "context",
      "required": true,
      "placeholder": "Select template IDs",
      "type_info": {
        "type": "AllowedTemplateId",
        "is_list": true,
        "inner_type": "AllowedTemplateId",
        "is_enum": true,
        "enum_values": [1201]
      }
    },
    {
      "field_name": "orshot_schema",
      "field_kind": "context",
      "required": true,
      "placeholder": "Configure Orshot schema fields",
      "type_info": {
        "type": "OrshotSchemaField",
        "is_list": true,
        "inner_type": "OrshotSchemaField",
        "is_custom_model": true,
        "model_schema": {
          "title": "OrshotSchemaField",
          "properties": {
            "field": { "type": "string" },
            "dataType": { "$ref": "#/$defs/OrshotDataType" },
            "description": { "type": "string" }
          },
          "required": ["field", "dataType", "description"]
        }
      }
    },
    {
      "field_name": "marketing_research",
      "field_kind": "data",
      "required": false,
      "placeholder": "Provide marketing research data",
      "type_info": {
        "type": "MarketingResearch",
        "is_custom_model": true,
        "model_schema": {
          "title": "MarketingResearch",
          "properties": {
            "content": { "type": "string" },
            "metadata": { "type": "object", "nullable": true }
          },
          "required": ["content"]
        }
      }
    }
  ]
}
```

### Field Properties

- **`field_name`** (string, required): The name of the field. Use this exact name when POSTing to `/crew/kickoff`.
- **`field_kind`** (string, required): Either `"context"` or `"data"`.
- **`required`** (boolean, default: `true`): Whether this field should be marked as required in the UI. **Note**: This is a UI hint only. Backend validation uses task dependencies to determine actual requirements.
- **`placeholder`** (string | null, optional): Placeholder text to display in form inputs.
- **`type_info`** (object, required): Type information for rendering the appropriate form control.

### Type Information (`type_info`)

The `type_info` object always includes:

- **`type`** (string): The base type name (e.g., `"string"`, `"MarketingResearch"`, `"AllowedTemplateId"`).
- **`is_list`** (boolean): Whether this is a list type. Always present (even when `false`).
- **`is_enum`** (boolean): Whether this is an enum type. Always present (even when `false`).
- **`is_custom_model`** (boolean): Whether this is a custom Pydantic model. Always present (even when `false`).

Conditionally included fields:

- **`inner_type`** (string): Present when `is_list` is `true`. The type of list elements.
- **`enum_values`** (array): Present when `is_enum` is `true`. Array of valid enum values.
- **`model_schema`** (object): Present when `is_custom_model` is `true` and a schema is available. JSON schema for the custom model.

## Type Safety with Generated Types

### Generating TypeScript Types

The `/schemas` endpoint ensures custom types appear in the OpenAPI schema. Use `openapi-ts` to generate TypeScript types:

```bash
openapi-ts --input http://localhost:8000/openapi.json --output ./types
```

This generates TypeScript types for all models including:

- `RequiredInputsResponse`
- `RequiredInputField`
- `FieldTypeInfo`
- Custom types like `MarketingResearch`, `ContentStrategy`, etc.

### Using Generated Types

```typescript
import { RequiredInputsResponse, RequiredInputField } from "./types";

async function fetchRequiredInputs(
  crewId: string
): Promise<RequiredInputsResponse> {
  const response = await fetch(`/crew/${crewId}/required-inputs`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error(`Failed to fetch required inputs: ${response.statusText}`);
  }

  return response.json();
}
```

### Using Types for Crew Kickoff

The generated TypeScript types from the OpenAPI schema include the request and response models for `/crew/kickoff`. These types correspond to the Pydantic models defined in the crew service (`CrewRunCreateRequest` and `CrewRun`).

**Request Type**: `CrewRunCreateRequest`

- `crew_id: string` (UUID)
- `inputs?: Record<string, any>` - A dictionary where keys match `field_name` from the required inputs response

**Response Type**: `CrewRun`

- `id: string` (UUID) - The created crew run ID
- `crew_id: string` (UUID) - The crew ID

The `inputs` object structure matches the field names returned by `/required-inputs`. The backend validates these inputs against the flow dependency graph before creating the crew run in the CRUD service.

**Example with Type Safety**:

```typescript
import { CrewRunCreateRequest, CrewRun } from "./types";

async function kickoffCrewRun(
  crewId: string,
  inputs: Record<string, any>
): Promise<CrewRun> {
  const request: CrewRunCreateRequest = {
    crew_id: crewId,
    inputs: inputs, // Use exact field_name values from required-inputs
  };

  const response = await fetch("/crew/kickoff", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to start crew run");
  }

  return response.json() as CrewRun;
}
```

**Note**: The database schemas in the CRUD service (`schemas.py`) define the SQLAlchemy models for persistence. The API types you use in the frontend are generated from the **crew service's** OpenAPI schema, which exposes the Pydantic models (`CrewRunCreateRequest`, `CrewRun`) used for API communication. The crew service handles the translation between these API models and the CRUD service's database models internally.

## Form Rendering Guidelines

### 1. Fetch Required Inputs

Call the endpoint whenever the crew selection changes so the form stays in sync with the active tasks:

```typescript
useEffect(() => {
  if (crewId) {
    fetchRequiredInputs(crewId).then(setFormFields).catch(handleError);
  }
}, [crewId]);
```

### 2. Render Form Controls

For each field, check `type_info` properties to determine the appropriate input:

```typescript
function renderField(field: RequiredInputField) {
  const { field_name, type_info, required, placeholder } = field;

  // Enum fields: render dropdown
  if (type_info.is_enum && type_info.enum_values) {
    return (
      <select name={field_name} required={required} placeholder={placeholder}>
        {type_info.enum_values.map((value) => (
          <option key={value} value={value}>
            {value}
          </option>
        ))}
      </select>
    );
  }

  // Custom models: use JSON schema form builder
  if (type_info.is_custom_model && type_info.model_schema) {
    return (
      <JsonSchemaForm
        schema={type_info.model_schema}
        name={field_name}
        required={required}
        placeholder={placeholder}
      />
    );
  }

  // List types: render repeatable form
  if (type_info.is_list) {
    return (
      <RepeatableForm
        name={field_name}
        elementType={type_info.inner_type}
        required={required}
        placeholder={placeholder}
      />
    );
  }

  // Basic types: render appropriate input
  switch (type_info.type) {
    case "string":
      return (
        <input
          type="text"
          name={field_name}
          required={required}
          placeholder={placeholder}
        />
      );
    case "date":
      return (
        <input
          type="date"
          name={field_name}
          required={required}
          placeholder={placeholder}
        />
      );
    case "int":
    case "float":
      return (
        <input
          type="number"
          name={field_name}
          required={required}
          placeholder={placeholder}
        />
      );
    case "bool":
      return <input type="checkbox" name={field_name} />;
    default:
      return (
        <textarea
          name={field_name}
          required={required}
          placeholder={placeholder}
        />
      );
  }
}
```

### 3. Complete Example

```typescript
import { RequiredInputsResponse, RequiredInputField } from "./types";
import Form from "@rjsf/core";

async function renderCrewInputForm(crewId: string) {
  // Fetch required inputs
  const response = await fetch(`/crew/${crewId}/required-inputs`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const data: RequiredInputsResponse = await response.json();

  return (
    <form onSubmit={handleSubmit}>
      {data.fields.map((field) => renderField(field))}
      <button type="submit">Start Crew Run</button>
    </form>
  );
}
```

## Integration with `/crew/kickoff`

After collecting form data, POST it to `/crew/kickoff` using the generated types:

```typescript
import { CrewRunCreateRequest, CrewRun } from "./types";

async function startCrewRun(
  crewId: string,
  inputs: Record<string, any>
): Promise<CrewRun> {
  const request: CrewRunCreateRequest = {
    crew_id: crewId,
    inputs: inputs, // Use the exact field names from required-inputs response
  };

  const response = await fetch("/crew/kickoff", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to start crew run");
  }

  return response.json() as CrewRun; // Returns CrewRun with id and crew_id
}
```

**Important**: Use the exact `field_name` values returned by `/required-inputs` when constructing the `inputs` object. The backend validates field names and types based on the dependency graph.

## Relationship to CRUD Service Schemas

The `/required-inputs` endpoint is part of the **crew service** (this service). It returns field definitions for form rendering.

The **CRUD service** (`/Users/michaelong/Projects/cs464 project/FSD/backend/crud_service`) manages:

- Crew definitions (stored in `crews` table)
- Task definitions (stored in `tasks` table)
- Crew runs (stored in `crew_runs` table with `run_metadata` JSONB field)

When you POST to `/crew/kickoff`:

1. The crew service validates inputs using the dependency graph
2. Creates a `CrewRun` record in the CRUD service
3. Stores the inputs in `crew_run.run_metadata.inputs` (JSONB field)

The CRUD service schemas (`app/schemas/schemas.py`) define the database structure, while the crew service's `/required-inputs` endpoint provides the dynamic form schema based on the crew's tasks.

## Best Practices

1. **Always use generated types**: Use `openapi-ts` to generate TypeScript types for type safety
2. **Preserve field names**: Use exact `field_name` values when POSTing to `/crew/kickoff`
3. **Handle optional fields**: Check `required` flag for UI hints, but remember backend validation is authoritative
4. **Use model_schema for custom types**: Feed `model_schema` to JSON schema form builders like `@rjsf/core`
5. **Validate on frontend**: Use the `type_info` to validate inputs before submission, but backend validation is the source of truth

## Related Documentation

- [Required Inputs - Backend Logic](./required_inputs_backend.md) - How required inputs are determined
- [Dynamic Flow](./dynamic_flow.md) - How flows are built from tasks
