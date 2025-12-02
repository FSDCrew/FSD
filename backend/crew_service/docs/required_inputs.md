# Required Inputs Documentation

This documentation explains how the `/crew/{crew_id}/required-inputs` endpoint works and how to integrate with it.

## Documentation Overview

The required inputs functionality is documented in two separate guides:

1. **[Required Inputs - Backend Logic](./required_inputs_backend.md)**

   - How required inputs are determined using dependency graphs
   - Backend validation logic
   - Flow state creation process
   - Understanding the `infer_initial_inputs` algorithm

2. **[Required Inputs - Frontend Integration Guide](./required_inputs_frontend.md)**
   - API endpoint details and response contract
   - TypeScript type generation with `openapi-ts`
   - Form rendering guidelines and examples
   - Integration with `/crew/kickoff` endpoint
   - Relationship to CRUD service schemas

## Quick Start

For frontend developers, start with the [Frontend Integration Guide](./required_inputs_frontend.md).

For backend developers or those wanting to understand the logic, see the [Backend Logic documentation](./required_inputs_backend.md).

## Endpoint

**`GET /crew/{crew_id}/required-inputs`**

Returns a list of fields that must be provided before starting a crew run, along with type information and UI metadata for rendering dynamic forms.

## Related Documentation

- [Dynamic Flow](./dynamic_flow.md) - How flows are built from tasks
- [Configuration](./configuration.md) - YAML configuration structure
