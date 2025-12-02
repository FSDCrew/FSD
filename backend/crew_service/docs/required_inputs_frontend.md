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
    },
    {
      "field_name": "content_strategy",
      "type_info": {
        "type": "ContentStrategy",
        "is_list": false,
        "is_enum": false,
        "is_custom_model": true,
        "model_schema": {
          "$defs": {
            "StrategyPhase": {
              "additionalProperties": false,
              "description": "Non-date-specific strategic phase definition.\nThe scheduler will later map these phases to calendar weeks.",
              "properties": {
                "name": {
                  "description": "Phase name, e.g., 'Awareness', 'Engagement', etc.",
                  "title": "Name",
                  "type": "string"
                },
                "duration_in_weeks": {
                  "description": "How long the phase should run, without calendar dates.",
                  "title": "Duration In Weeks",
                  "type": "integer"
                },
                "themes": {
                  "description": "Core themes emphasized in this phase.",
                  "items": {
                    "type": "string"
                  },
                  "title": "Themes",
                  "type": "array"
                },
                "objectives": {
                  "description": "Strategic objectives for the phase.",
                  "items": {
                    "type": "string"
                  },
                  "title": "Objectives",
                  "type": "array"
                },
                "recommended_content_types": {
                  "description": "Content formats recommended here (e.g., posts, reels, stories).",
                  "items": {
                    "type": "string"
                  },
                  "title": "Recommended Content Types",
                  "type": "array"
                },
                "posting_cadence": {
                  "additionalProperties": {
                    "type": "integer"
                  },
                  "description": "Cadence expressed as counts, e.g., {'posts_per_week': 3, 'stories_per_week': 2}",
                  "title": "Posting Cadence",
                  "type": "object"
                },
                "messaging_guidelines": {
                  "anyOf": [
                    {
                      "items": {
                        "type": "string"
                      },
                      "type": "array"
                    },
                    {
                      "type": "null"
                    }
                  ],
                  "default": null,
                  "description": "Tone & message guidelines specific to this phase.",
                  "title": "Messaging Guidelines"
                }
              },
              "required": [
                "name",
                "duration_in_weeks",
                "themes",
                "objectives",
                "recommended_content_types",
                "posting_cadence"
              ],
              "title": "StrategyPhase",
              "type": "object"
            }
          },
          "description": "Complete content strategy output.\n\n- `content`: Human-readable markdown summary\n- `global_settings`: Tone, voice, brand alignment, audience considerations\n- `phases`: Structured, agent-parsable strategy blocks (no dates!)\n- `metadata`: Version, timestamps, etc.",
          "example": {
            "content": "# Content Strategy\n\n## Executive Summary\nHigh-level strategy...",
            "global_settings": {
              "content_pillars": ["Education", "Brand Story", "Engagement"],
              "tone": "Friendly, confident, aspirational",
              "voice": "Conversational but informative"
            },
            "phases": [
              {
                "duration_in_weeks": 2,
                "messaging_guidelines": [
                  "Highlight core value",
                  "Use simple, clear language"
                ],
                "name": "Awareness",
                "objectives": ["Build recognition", "Warm up audience"],
                "posting_cadence": {
                  "posts_per_week": 3,
                  "stories_per_week": 2
                },
                "recommended_content_types": ["posts", "reels", "stories"],
                "themes": ["Brand Intro", "Problem Awareness"]
              }
            ]
          },
          "properties": {
            "content": {
              "description": "Full content strategy rendered as markdown",
              "title": "Content",
              "type": "string"
            },
            "global_settings": {
              "additionalProperties": true,
              "description": "High-level settings: tone, voice, brand alignment, messaging principles, content pillars",
              "title": "Global Settings",
              "type": "object"
            },
            "phases": {
              "description": "List of strategic phases that define themes, cadence, and objectives without assigning dates",
              "items": {
                "$ref": "#/$defs/StrategyPhase"
              },
              "title": "Phases",
              "type": "array"
            }
          },
          "required": ["content", "global_settings", "phases"],
          "title": "ContentStrategy",
          "type": "object"
        }
      },
      "field_kind": "data",
      "required": false,
      "placeholder": "Provide content strategy"
    }
  ]
}
```

### Field Properties

- **`field_name`** (string, required): The name of the field. Use this exact name when POSTing to `/crew/kickoff`.
- **`field_kind`** (string, required): Either `"context"` or `"data"`. **Note**: Currently, this field is provided by the API but is not used in form rendering logic.
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

**Note on `$ref` resolution**: The backend automatically resolves `$ref` references in array items within custom model schemas. For example, if `ContentStrategy.phases` is a list of `StrategyPhase` objects, the `phases.items` field will contain the full `StrategyPhase` schema instead of a `$ref` reference. This makes it easier for frontend form builders to render nested forms without needing to resolve references manually. Non-array `$ref` references may still appear in the schema and should be resolved using the `$defs` section.

**Note on inline object definitions**: In addition to `$ref` references, the schema may also contain inline object definitions (i.e., `type: "object"` with a `properties` field). Your form rendering logic should handle both patterns:

- `items.$ref` → resolve using `$defs`
- `items.type === "object" && items.properties` → use the inline definition directly

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

**Type Safety Note**: The generated `FieldTypeInfo` type is defined as `{ [key: string]: unknown; }`, which means properties like `is_list`, `is_enum`, `model_schema`, etc. are accessed without strict typing. You'll need to cast or assert types when accessing these properties, or use type guards to ensure type safety at runtime.

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

### 2. Initialize Form Data

After fetching required inputs, initialize form data with appropriate default values based on field types:

```typescript
function initializeFormData(fields: RequiredInputField[]): Record<string, any> {
  const initialData: Record<string, any> = {};

  fields.forEach((field) => {
    const typeInfo = field.type_info as any;

    if (typeInfo.is_list) {
      // Initialize lists (custom models, enums, or primitives) with empty array
      initialData[field.field_name] = [];
    } else if (typeInfo.is_custom_model && typeInfo.model_schema) {
      // Initialize custom models with empty object
      initialData[field.field_name] = {};
    } else if (typeInfo.type === "boolean" || typeInfo.type === "bool") {
      // Initialize booleans with false
      initialData[field.field_name] = false;
    } else {
      // Initialize strings, numbers, and other types with empty string
      initialData[field.field_name] = "";
    }
  });

  return initialData;
}
```

### 3. Render Form Controls

For each field, check `type_info` properties to determine the appropriate input. The rendering order should be:

1. **Check if it's a list** (`is_list === true`)
   - If `is_custom_model` → render list of custom model forms
   - If `is_enum` → render multi-select enum buttons
   - Otherwise → render repeatable primitive inputs
2. **Check if it's an enum** (`is_enum === true`)
   - Render single-select dropdown
3. **Check if it's a custom model** (`is_custom_model === true`)
   - Render nested form based on `model_schema`
4. **Otherwise** → render basic type input (string, number, boolean, date)

Here's a comprehensive example:

```typescript
function renderField(
  field: RequiredInputField,
  value: any,
  onChange: (value: any) => void
) {
  const { field_name, type_info, required, placeholder } = field;
  const typeInfo = type_info as any;

  // 1. Check if it's a list first
  if (typeInfo.is_list) {
    // List of custom models
    if (typeInfo.is_custom_model && typeInfo.model_schema) {
      return renderCustomModelList(field, typeInfo, value || [], onChange);
    }
    // List of enums
    if (typeInfo.is_enum && typeInfo.enum_values) {
      return renderEnumList(field, typeInfo, value || [], onChange);
    }
    // List of primitives
    return renderPrimitiveList(field, typeInfo, value || [], onChange);
  }

  // 2. Check if it's an enum
  if (typeInfo.is_enum && typeInfo.enum_values) {
    return renderEnumSelect(field, typeInfo, value, onChange);
  }

  // 3. Check if it's a custom model
  if (typeInfo.is_custom_model && typeInfo.model_schema) {
    return renderCustomModel(field, typeInfo, value || {}, onChange);
  }

  // 4. Basic types
  return renderBasicInput(field, typeInfo, value, onChange);
}
```

### 4. Handle Nullable Arrays

Some array fields may be nullable (using `anyOf` with `null`). Check for this pattern in nested model properties:

```typescript
function isNullableArray(propSchema: any): boolean {
  if (!propSchema.anyOf) return false;
  const arraySchema = propSchema.anyOf.find((s: any) => s.type === "array");
  const nullSchema = propSchema.anyOf.find((s: any) => s.type === "null");
  return !!(arraySchema && nullSchema);
}

function renderNullableArray(
  propName: string,
  propSchema: any,
  value: any,
  onChange: (value: any) => void
) {
  const arraySchema = propSchema.anyOf.find((s: any) => s.type === "array");
  const isNull = value === null || value === undefined;
  const arrayValue = isNull ? [] : value || [];

  return (
    <div>
      <label>
        <input
          type="checkbox"
          checked={!isNull}
          onChange={(e) => {
            onChange(e.target.checked ? [] : null);
          }}
        />
        Enable {propName}
      </label>
      {!isNull &&
        // Render array items based on arraySchema.items
        // Check for $ref or inline object definition
        renderArrayItems(propName, arraySchema, arrayValue, onChange)}
    </div>
  );
}
```

### 5. Handle Dynamic Objects (additionalProperties)

Some object fields may have `additionalProperties` set to `true` or a type definition, indicating they accept dynamic key-value pairs:

```typescript
function renderDynamicObject(
  propName: string,
  propSchema: any,
  value: Record<string, any>,
  onChange: (value: Record<string, any>) => void
) {
  const objValue = value || {};
  const valueType = propSchema.additionalProperties?.type || "string";

  return (
    <div>
      <label>{propName}</label>
      {Object.entries(objValue).map(([key, val], index) => (
        <div key={index}>
          <input
            placeholder="Key"
            value={key}
            onChange={(e) => {
              const newObj = { ...objValue };
              delete newObj[key];
              if (e.target.value) {
                newObj[e.target.value] = val;
              }
              onChange(newObj);
            }}
          />
          <input
            type={
              valueType === "integer" || valueType === "number"
                ? "number"
                : "text"
            }
            placeholder="Value"
            value={val}
            onChange={(e) => {
              const newObj = { ...objValue };
              newObj[key] =
                valueType === "integer" || valueType === "number"
                  ? Number(e.target.value)
                  : e.target.value;
              onChange(newObj);
            }}
          />
          <button
            onClick={() => {
              const newObj = { ...objValue };
              delete newObj[key];
              onChange(newObj);
            }}
          >
            Remove
          </button>
        </div>
      ))}
      <button
        onClick={() => {
          onChange({ ...objValue, new_key: "" });
        }}
      >
        Add Key-Value Pair
      </button>
    </div>
  );
}
```

### 6. Handle Nested Custom Models

When rendering custom models, you may encounter nested custom models within arrays. Handle both `$ref` references and inline object definitions:

```typescript
function renderNestedCustomModelList(
  propName: string,
  propSchema: any,
  value: any[],
  onChange: (value: any[]) => void,
  defs?: Record<string, any>
) {
  const itemsSchema = propSchema.items;
  let modelSchema: any = null;

  // Check for $ref (reference to a model in $defs)
  if (itemsSchema.$ref) {
    const refName = itemsSchema.$ref.replace("#/$defs/", "");
    modelSchema = defs?.[refName];
  }
  // Check for inline object definition
  else if (itemsSchema.type === "object" && itemsSchema.properties) {
    modelSchema = itemsSchema;
  }

  if (!modelSchema || !modelSchema.properties) {
    return null;
  }

  const listValue = Array.isArray(value) ? value : [];
  const requiredProps = modelSchema.required || [];
  const properties = modelSchema.properties || {};

  return (
    <div>
      {listValue.map((item, index) => (
        <div key={index}>
          <h4>Item {index + 1}</h4>
          {Object.entries(properties).map(
            ([nestedPropName, nestedPropSchema]: [string, any]) => {
              // Recursively render nested properties
              return renderModelProperty(
                nestedPropName,
                nestedPropSchema,
                item[nestedPropName],
                (newValue) => {
                  const newList = [...listValue];
                  newList[index] = {
                    ...newList[index],
                    [nestedPropName]: newValue,
                  };
                  onChange(newList);
                },
                requiredProps.includes(nestedPropName),
                defs
              );
            }
          )}
          <button
            onClick={() => {
              onChange(listValue.filter((_, i) => i !== index));
            }}
          >
            Remove
          </button>
        </div>
      ))}
      <button
        onClick={() => {
          onChange([...listValue, createEmptyItem(properties)]);
        }}
      >
        Add Item
      </button>
    </div>
  );
}
```

### 7. Complete Example

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

## Form Submission and Data Filtering

Before submitting form data to `/crew/kickoff`, you should filter out empty values to avoid sending unnecessary data:

```typescript
function filterFormData(formData: Record<string, any>): Record<string, any> {
  const submitData: Record<string, any> = {};

  for (const [key, value] of Object.entries(formData)) {
    if (Array.isArray(value)) {
      // Filter out empty objects/items from lists
      const filtered = value.filter((item) => {
        if (typeof item === "object" && item !== null) {
          // For objects, check if at least one property has a value
          return Object.values(item).some((v) => {
            if (typeof v === "string") return v.trim() !== "";
            if (typeof v === "boolean") return true;
            return v !== null && v !== undefined;
          });
        }
        // For primitives, check if not empty
        if (typeof item === "string") return item.trim() !== "";
        return item !== null && item !== undefined;
      });
      if (filtered.length > 0) {
        submitData[key] = filtered;
      }
    } else if (typeof value === "object" && value !== null) {
      // For single custom models, check if at least one property has a value
      const hasValue = Object.values(value).some((v) => {
        if (typeof v === "string") return v.trim() !== "";
        if (typeof v === "boolean") return true;
        return v !== null && v !== undefined;
      });
      if (hasValue) {
        submitData[key] = value;
      }
    } else {
      // For primitives, include if not empty
      if (value !== "" && value !== null && value !== undefined) {
        submitData[key] = value;
      }
    }
  }

  return submitData;
}
```

**Validation**: Before submission, validate that all required fields are filled:

```typescript
function validateRequiredFields(
  fields: RequiredInputField[],
  formData: Record<string, any>
): string[] {
  const missingFields: string[] = [];

  fields.forEach((field) => {
    if (!field.required) return;

    const value = formData[field.field_name];
    const typeInfo = field.type_info as any;

    // Check for empty arrays
    if (Array.isArray(value)) {
      if (value.length === 0) {
        missingFields.push(field.field_name);
      }
      return;
    }

    // Check for empty objects (custom models)
    if (
      typeInfo.is_custom_model &&
      typeof value === "object" &&
      value !== null
    ) {
      const hasValue = Object.values(value).some((v: any) => {
        if (typeof v === "string") return v.trim() !== "";
        if (typeof v === "boolean") return true;
        return v !== null && v !== undefined;
      });
      if (!hasValue) {
        missingFields.push(field.field_name);
      }
      return;
    }

    // Check for empty strings, null, undefined
    if (!value || (typeof value === "string" && value.trim() === "")) {
      missingFields.push(field.field_name);
    }
  });

  return missingFields;
}
```

## Integration with `/crew/kickoff`

After collecting and filtering form data, POST it to `/crew/kickoff` using the generated types:

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

1. **Always use generated types**: Use `openapi-ts` to generate TypeScript types for type safety. Note that `FieldTypeInfo` is loosely typed (`{ [key: string]: unknown; }`), so you may need type assertions or type guards when accessing properties.

2. **Preserve field names**: Use exact `field_name` values when POSTing to `/crew/kickoff`. The backend validates field names against the dependency graph.

3. **Initialize form data properly**: Set appropriate default values based on field types (empty arrays for lists, empty objects for custom models, `false` for booleans, empty strings for numbers/strings).

4. **Handle nullable arrays**: Check for `anyOf` patterns with `null` type when rendering nested model properties. Provide a checkbox or toggle to enable/disable nullable arrays.

5. **Filter empty values before submission**: Remove empty arrays, empty objects, and empty strings from form data before sending to `/crew/kickoff` to keep payloads clean.

6. **Support both $ref and inline definitions**: When rendering nested custom models, handle both `$ref` references (resolve via `$defs`) and inline object definitions (`type: "object"` with `properties`).

7. **Render fields in correct order**: Check `is_list` first, then `is_enum`, then `is_custom_model`, then basic types. This ensures proper rendering priority.

8. **Handle dynamic objects**: For objects with `additionalProperties`, provide a key-value pair editor that allows users to add/remove custom properties.

9. **Validate on frontend**: Use the `type_info` and `required` flag to validate inputs before submission, but remember that backend validation is the source of truth.

10. **Note on field_kind**: The `field_kind` property is provided by the API but is not currently used in form rendering. It may be used for future UI categorization or filtering features.

## Related Documentation

- [Required Inputs - Backend Logic](./required_inputs_backend.md) - How required inputs are determined
- [Dynamic Flow](./dynamic_flow.md) - How flows are built from tasks
