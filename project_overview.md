# Project Overview: Multi-Agent AI Marketing Campaign Platform

## 1. Executive Summary

### Project Purpose

This platform is a full-stack application that automates marketing campaign creation and execution through multi-agent AI workflows. The system enables users to design, execute, and manage complex marketing campaigns using AI agents that perform research, content strategy, scheduling, and content generation tasks autonomously.

### Value Proposition

- **Automated Campaign Creation**: Transform high-level campaign themes into complete marketing strategies and execution schedules
- **Multi-Agent Intelligence**: Leverage specialized AI agents (researchers, strategists, schedulers, copywriters) working in coordinated workflows
- **Visual Flow Builder**: Intuitive drag-and-drop interface for designing campaign task flows
- **Intelligent Retry & Recovery**: Retry failed tasks while preserving successful upstream work
- **Real-Time Monitoring**: Track task execution progress with granular status updates

### Target Use Case

The primary use case is **Instagram marketing campaign automation**. Users provide campaign parameters (theme, brand description, target audience, dates), and the system orchestrates multiple AI agents to:

1. Conduct market research on competitors and trends
2. Develop comprehensive content strategies
3. Generate detailed social media posting schedules
4. Create copywriting and visual assets
5. Produce final deliverables (Word documents, Excel schedules, rendered images)

---

## 2. System Architecture

### High-Level Architecture

The system follows a **three-tier microservices architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                      │
│              User Interface & Flow Builder                  │
└────────────┬───────────────────────────────┬───────────────┘
             │                               │
             │ User Operations               │ Crew Operations
             ▼                               ▼
┌──────────────────────────┐    ┌────────────────────────────┐
│   CRUD Service (FastAPI) │    │  Crew Service (FastAPI)    │
│  • Data Persistence      │    │  • Flow Orchestration     │
│  • Queue Management      │◄───┤  • Input Validation       │
│  • Authentication        │    │  • Retry/Cancel Logic      │
│  • Artifact Storage      │    └────────────┬───────────────┘
└────────────┬─────────────┘                 │
             │                               │
             │ Internal APIs                 │ Flow Building
             │                               │
             ▼                               ▼
┌─────────────────────────────────────────────────────────────┐
│              Worker Process (Background Jobs)               │
│  • Queue Polling                                           │
│  • Process-Per-Job Execution                               │
│  • Heartbeat Management                                    │
│  • Status Updates                                          │
└─────────────────────────────────────────────────────────────┘
```

### External Dependencies

- **AWS Cognito**: User authentication and authorization
- **PostgreSQL (Supabase)**: Primary database for crews, tasks, runs, and queue
- **AWS S3**: Artifact storage (Word docs, Excel files, images)
- **OpenAI API**: LLM models for agent reasoning and guardrail validation
- **Bright Data**: Web scraping and search capabilities
- **Playwright**: Browser automation for Instagram and web scraping
- **Orshot API**: Template rendering for visual content

### Communication Patterns

1. **Frontend ↔ CRUD Service**: User-facing operations (CRUD on crews, viewing runs)
2. **Frontend ↔ Crew Service**: Crew orchestration (kickoff, required inputs, cancellation)
3. **Crew Service ↔ CRUD Service**: Internal APIs (creating runs, queue operations)
4. **Worker ↔ CRUD Service**: Queue management (claim, heartbeat, status updates)
5. **Worker ↔ Crew Service**: Flow building (dynamic flow generation)
6. **All Services → S3**: Artifact uploads and presigned URL generation

---

## 3. Core Components & Services

### 3.1 Frontend (Next.js)

**Purpose**: User interface for managing crews, designing flows, and viewing execution results.

**Key Features**:

- **Studio Dashboard**: Overview of all crews with create/edit/delete operations
- **Visual Flow Builder**: Drag-and-drop interface using React Flow for designing task workflows
- **Dynamic Form Generation**: Automatically generates input forms based on required inputs from flow dependencies
- **Run History**: View past crew runs with detailed task status and outputs
- **Real-Time Status Updates**: Monitor running crew executions with task-level progress

**Technologies**:

- Next.js 14+ (App Router)
- React 18+
- TypeScript
- Tailwind CSS
- React Query (TanStack Query) for data fetching
- AWS Amplify for Cognito integration

**Key Components**:

- `StudioPage`: Main dashboard listing all crews
- `CrewPage`: Visual flow builder and crew editor
- `KickoffForm`: Dynamic form generator for required inputs
- `CrewRunsHistory`: Historical view of crew run executions
- `RunDetails`: Detailed view of a single crew run with task statuses

### 3.2 CRUD Service (FastAPI)

**Purpose**: Data persistence, queue management, and user authentication.

**Key Responsibilities**:

1. **Crew & Task Management**

   - CRUD operations for crews and nested tasks
   - Ownership validation (users can only access their own crews)
   - Task ordering and persistence

2. **User Authentication**

   - Cognito JWT token validation via JWKS
   - User synchronization (creates local user records from Cognito tokens)
   - Token extraction from Authorization header or cookies

3. **Queue Management**

   - Job queue for crew run execution
   - Lease-based job claiming (prevents duplicate processing)
   - Heartbeat mechanism for extending leases
   - Status tracking (QUEUED → CLAIMED → COMPLETED/FAILED/CANCELLED)

4. **Crew Run Persistence**

   - Stores crew run metadata (inputs, task snapshots)
   - Tracks execution outputs and task states
   - Manages retry relationships between runs

5. **Artifact Storage**

   - Base64 file upload handling
   - S3 integration for persistent storage
   - Presigned URL generation for secure artifact retrieval

6. **Internal API Surface**
   - Locked-down endpoints for worker communication
   - Requires `INTERNAL_CREW_API_KEY` for authentication
   - Endpoints for queue operations, crew run creation, status updates

**Technologies**:

- FastAPI
- SQLAlchemy (async) with PostgreSQL
- Alembic for database migrations
- boto3 for S3 operations
- PyJWT for Cognito token validation

**Key Endpoints**:

- `/crew/*`: Crew CRUD operations (user-facing)
- `/task/*`: Task management (user-facing)
- `/crew-run/*`: Crew run history (user-facing)
- `/artifact/*`: Artifact upload/retrieval (user-facing)
- `/internal/*`: Worker communication (internal only)

### 3.3 Crew Service (FastAPI + CrewAI)

**Purpose**: AI agent orchestration, dynamic flow building, and crew run execution coordination.

**Key Responsibilities**:

1. **Dynamic Flow Building**

   - Parses YAML configuration files (`tasks.yaml`, `agents.yaml`)
   - Constructs dependency graphs from task read/write specifications
   - Infers required inputs based on flow dependencies
   - Generates typed FlowState Pydantic models at runtime
   - Creates CrewAI Flow subclasses dynamically

2. **Input Validation**

   - Validates user inputs against flow state schema
   - Supports custom types (Pydantic models, IntEnums)
   - Type checking for primitives, lists, nested objects
   - Provides detailed error messages for invalid inputs

3. **Crew Run Kickoff**

   - Validates crew ownership
   - Validates input types before queueing
   - Creates crew run metadata with task snapshots
   - Delegates to CRUD service for queue enqueueing

4. **Retry & Cancellation Logic**
   - Retry service for creating retry runs from completed tasks
   - Task filtering (retry task + downstream only)
   - Upstream output extraction and merging
   - Cancellation request handling

**Technologies**:

- FastAPI
- CrewAI for multi-agent orchestration
- OpenAI GPT models (for agents and guardrail validation)
- Pydantic for type validation
- YAML parsing for configuration

**Key Endpoints**:

- `GET /crew/{crew_id}/required-inputs`: Returns required input fields and types
- `POST /crew/kickoff`: Initiates a crew run
- `POST /crew/crew-run/{crew_run_id}/cancel`: Cancels a running crew run
- `POST /crew/crew-run/{crew_run_id}/retry`: Creates a retry run

**Key Modules**:

- `flow_service.py`: Main orchestration façade
- `flow_builder.py`: Dynamic flow class generation
- `dependency_graph.py`: Dependency analysis and input inference
- `agent_factory.py`: CrewAI agent instantiation
- `guardrails.py`: Output validation (structured output + LLM judge)

### 3.4 Worker Process

**Purpose**: Background job execution engine that processes queued crew runs.

**Key Responsibilities**:

1. **Queue Polling**

   - Continuously polls CRUD service queue for available jobs
   - Respects concurrency limits (default: 3 concurrent jobs)
   - Handles network failures with retry logic

2. **Process Management**

   - Spawns isolated OS process per job (`process-per-job` model)
   - Tracks running processes in registry
   - Cleans up completed processes automatically

3. **Job Execution**

   - Fetches crew run data from CRUD service
   - Detects retry scenarios and prepares retry execution
   - Builds dynamic flow from task definitions
   - Executes CrewAI flow with task status tracking
   - Updates queue status on completion/failure/cancellation

4. **Heartbeat Management**

   - Background thread sends periodic heartbeats to extend lease
   - Detects cancellation requests from heartbeat responses
   - Implements exponential backoff for network failures

5. **Cancellation Handling**
   - Monitors cancellation events during execution
   - Gracefully terminates flow execution on cancellation
   - Updates queue status to CANCELLED

**Architecture**: Process-per-job model

- Each job runs in its own OS process (complete isolation)
- Heartbeat runs in background thread within each process
- Main execution thread monitors cancellation events
- Process exits cleanly on completion, failure, or cancellation

**Technologies**:

- Python multiprocessing (spawn context)
- Threading for heartbeat loops
- Synchronous HTTP client for CRUD communication
- CrewAI for flow execution

---

## 4. Main Features

### 4.1 Crew Management

Users can create, edit, and delete crews through the Studio interface:

- **Create Crew**: Define crew name and description
- **Visual Flow Builder**: Drag-and-drop task nodes to design workflow
- **Task Configuration**: Each task references predefined task types from YAML configuration
- **Task Ordering**: Tasks are executed sequentially based on visual flow order
- **Save & Load**: Crew definitions persist in database with task relationships

**Flow Builder Features**:

- React Flow-based visual editor
- Custom node types for different task categories
- Edge connections define execution order
- Real-time validation of task dependencies

### 4.2 Dynamic Flow Execution

The system builds executable flows dynamically from YAML configuration:

- **YAML-Driven Configuration**: Tasks, agents, and state schema defined in YAML files
- **Automatic Input Validation**: System infers required inputs from task dependencies
- **Multi-Agent Workflows**: Different agents execute different tasks (researcher, strategist, scheduler, copywriter)
- **Task Dependency Resolution**: System ensures tasks receive required data from upstream tasks
- **Type Safety**: Pydantic models ensure type correctness throughout execution

**Flow Building Process**:

1. Parse YAML configuration files
2. Build dependency graph from task read/write specifications
3. Infer required inputs (context fields + unwritten data fields)
4. Generate FlowState Pydantic model with only needed fields
5. Create CrewAI Flow subclass with sequential task steps
6. Wire agents and tools based on task assignments

### 4.3 Crew Run Lifecycle

Complete lifecycle of a crew run execution:

1. **Kickoff**: User provides required inputs via dynamic form
2. **Validation**: System validates input types and required fields
3. **Queue Enqueueing**: CRUD service creates crew run record and enqueues job
4. **Job Claiming**: Worker polls queue and claims available job
5. **Flow Building**: Worker builds dynamic flow from task definitions
6. **Execution**: CrewAI executes tasks sequentially
7. **Status Tracking**: Each task updates status (QUEUED → RUNNING → COMPLETED/FAILED)
8. **Output Storage**: Task outputs stored in crew run output
9. **Completion**: Queue status updated to COMPLETED

**Status States**:

- `QUEUED`: Job waiting in queue
- `CLAIMED`: Worker has claimed job and is executing
- `RUNNING`: Flow execution in progress (task-level status)
- `COMPLETED`: All tasks completed successfully
- `FAILED`: Task execution failed
- `CANCELLED`: User or system cancelled execution

### 4.4 Retry Mechanism

Users can retry from any completed task in a crew run:

- **Retry Point Selection**: Choose any completed task as retry starting point
- **Task Filtering**: System filters to retry task + all downstream tasks
- **Upstream Preservation**: Outputs from upstream (completed) tasks are preserved
- **Feedback Integration**: User provides feedback that is prepended to retry task description
- **Clean Execution**: Only retry and downstream tasks execute, reducing cost and time

**Retry Flow**:

1. User selects completed task and provides feedback
2. System creates new crew run with retry metadata
3. Upstream tasks marked as COMPLETED in new run
4. Retry task and downstream tasks reset to QUEUED
5. Worker extracts upstream outputs and merges with original inputs
6. Retry task description modified to include feedback
7. Only retry + downstream tasks execute

### 4.5 Cancellation

Users can cancel queued or running crew runs:

- **Queued Cancellation**: Immediate status update to CANCELLED
- **Running Cancellation**: Worker detects cancellation via heartbeat
- **Graceful Shutdown**: Worker process exits cleanly, updating status
- **Status Cleanup**: Queue entry marked as CANCELLED

**Cancellation Flow**:

1. User initiates cancellation via API
2. CRUD service sets `cancel_requested` flag (for CLAIMED jobs) or updates status (for QUEUED jobs)
3. Worker heartbeat detects cancellation request
4. Heartbeat thread sets cancellation event
5. Main execution thread checks event and exits process
6. Queue status updated to CANCELLED

### 4.6 Artifact Management

System stores and retrieves files generated during execution:

- **File Upload**: Agents can upload files (Word docs, Excel files, images) via tools
- **S3 Storage**: Files stored in AWS S3 with organized paths
- **Presigned URLs**: Secure, time-limited URLs for artifact retrieval
- **Artifact Linking**: Artifacts linked to crew runs for easy access

**Supported Artifact Types**:

- `TEXT`: Markdown reports, text documents
- `DOCUMENT`: Word documents (.docx)
- `SPREADSHEET`: Excel files (.xlsx)
- `IMAGE`: Generated or scraped images
- `OTHER`: Miscellaneous file types

---

## 5. Key Scenarios & Workflows

### Scenario 1: Creating and Executing a Marketing Campaign

**Goal**: User wants to create a complete Instagram marketing campaign from a high-level theme.

**Steps**:

1. **User Authentication**

   - User logs in via AWS Cognito
   - Frontend receives JWT token
   - Token stored in context and sent with API requests

2. **Crew Creation**

   - User navigates to Studio dashboard
   - Clicks "Add Crew" to create new crew
   - Enters crew name and description

3. **Flow Design**

   - User opens crew in visual flow builder
   - Drags task nodes: `marketing_research` → `content_strategy` → `social_media_schedule`
   - Connects tasks to define execution order
   - Saves crew (tasks persisted to CRUD service)

4. **Input Collection**

   - User clicks "Kickoff" button
   - Frontend calls `GET /crew/{crew_id}/required-inputs`
   - System analyzes task dependencies and returns required fields:
     - `theme` (string, required)
     - `brand_description` (string, required)
     - `target_audience_description` (string, required)
     - `start_date` (date, required)
     - `end_date` (date, required)
   - Frontend generates dynamic form based on field types

5. **Input Submission**

   - User fills out form with campaign details
   - Frontend calls `POST /crew/kickoff` with inputs
   - Crew Service validates input types
   - Crew Service calls CRUD internal API to create crew run
   - CRUD service creates crew run record and enqueues job
   - Response returns crew run with QUEUED status

6. **Job Execution**

   - Worker polls queue and claims job
   - Worker fetches crew run data from CRUD service
   - Worker builds dynamic flow:
     - Creates dependency graph
     - Generates FlowState model
     - Instantiates CrewAI agents
     - Creates Flow subclass with task steps
   - Worker executes flow

7. **Task Execution**

   - **Task 1: Marketing Research**

     - Status: QUEUED → RUNNING
     - Agent: `market_researcher`
     - Tools used: `search_internet`, `search_instagram`, `open_pages`
     - Output: `MarketingResearch` object stored in flow state
     - Status: RUNNING → COMPLETED

   - **Task 2: Content Strategy**

     - Status: QUEUED → RUNNING
     - Agent: `content_strategist`
     - Reads: `marketing_research` (from Task 1)
     - Tools used: `calculate_num_weeks`, `verify_sum_equals_expected`
     - Output: `ContentStrategy` object
     - Status: RUNNING → COMPLETED

   - **Task 3: Social Media Schedule**
     - Status: QUEUED → RUNNING
     - Agent: `scheduler`
     - Reads: `content_strategy` (from Task 2)
     - Tools used: `generate_social_media_schedule`, `html_table_to_excel`
     - Output: `SocialMediaSchedule` object + Excel file artifact
     - Status: RUNNING → COMPLETED

8. **Completion**

   - All tasks completed
   - Worker updates queue status to COMPLETED
   - Crew run output contains all task states and outputs
   - Artifacts (Word docs, Excel files) stored in S3

9. **Result Viewing**
   - User navigates to crew run history
   - Views task execution timeline
   - Downloads artifacts (presigned URLs)
   - Reviews generated content strategy and schedule

**Duration**: Typically 5-15 minutes depending on task complexity and LLM response times.

### Scenario 2: Retrying a Failed Task

**Goal**: User wants to retry a task that produced unsatisfactory results, without re-running successful upstream tasks.

**Steps**:

1. **Problem Identification**

   - User views completed crew run
   - Identifies that `content_strategy` task needs improvement
   - Upstream task (`marketing_research`) was successful

2. **Retry Initiation**

   - User selects `content_strategy` task in run details
   - Clicks "Retry from this task"
   - Provides feedback: "Focus more on video content and user-generated content"

3. **Retry Run Creation**

   - Frontend calls `POST /crew/crew-run/{crew_run_id}/retry`
   - Crew Service's `RetryService`:
     - Validates retry task is COMPLETED
     - Partitions tasks: upstream (preserve) vs. retry+downstream (reset)
     - Creates new crew run with retry metadata
     - Copies upstream task outputs to new run
     - Resets retry and downstream tasks to QUEUED

4. **Retry Execution Preparation**

   - Worker detects retry run (has `retry_feedback` in metadata)
   - `RetryExecutor` prepares execution:
     - Filters tasks: only `content_strategy` + `social_media_schedule`
     - Extracts outputs from `marketing_research` task
     - Merges upstream outputs with original inputs
     - Modifies `content_strategy` task description to include feedback

5. **Flow Building**

   - Worker builds flow with filtered tasks only
   - Flow state includes upstream `marketing_research` output
   - Retry task description includes user feedback

6. **Execution**

   - **Task 1: Content Strategy (Retry)**

     - Agent receives feedback in task description
     - Reads: `marketing_research` (from upstream, preserved)
     - Generates improved content strategy with video/UGC focus
     - Status: COMPLETED

   - **Task 2: Social Media Schedule**
     - Reads: `content_strategy` (from retry task)
     - Generates schedule based on improved strategy
     - Status: COMPLETED

7. **Completion**
   - New crew run completed
   - User compares original vs. retry results
   - Upstream work preserved, only retry+downstream re-executed

**Benefits**: Saves time and cost by not re-running successful upstream tasks.

### Scenario 3: Cancelling a Running Crew Run

**Goal**: User wants to stop a crew run that is taking too long or is no longer needed.

**Steps**:

1. **Cancellation Request**

   - User clicks "Cancel" button on running crew run
   - Frontend calls `POST /crew/crew-run/{crew_run_id}/cancel`
   - Crew Service forwards to CRUD service internal API

2. **Queue Status Update**

   - CRUD service checks queue status:
     - If QUEUED: Immediately updates status to CANCELLED
     - If CLAIMED: Sets `cancel_requested` flag (status remains CLAIMED)

3. **Cancellation Detection**

   - Worker process has claimed job and is executing
   - Heartbeat thread sends periodic heartbeat to CRUD service
   - CRUD service returns `cancel_requested: true` in heartbeat response
   - Heartbeat thread detects cancellation

4. **Process Termination**

   - Heartbeat thread sets `cancellation_event`
   - Main execution thread checks event:
     - If before flow execution: Exits early, updates status to CANCELLED
     - If during flow execution: Monitors event every second
     - When detected: Updates queue status, stops heartbeat, exits process

5. **Cleanup**
   - Worker process exits using `os._exit(0)` (terminates all threads)
   - Flow execution thread terminated immediately
   - Queue status updated to CANCELLED
   - Worker detects completed process in next poll cycle

**Result**: Crew run marked as CANCELLED, no further execution occurs.

---

## 6. How It Works - Technical Deep Dive

### 6.1 Authentication Flow

**Frontend Authentication**:

1. User authenticates via AWS Cognito (OAuth/OIDC)
2. Cognito returns JWT tokens (ID token, access token, refresh token)
3. Frontend stores tokens in Amplify Auth context
4. Frontend extracts ID token for API requests

**Backend Token Validation**:

1. Request arrives with `Authorization: Bearer <token>` header or cookie
2. CRUD service extracts token via `get_token_from_request` dependency
3. `AuthService` validates token:
   - Fetches JWKS from Cognito (cached for 1 hour)
   - Verifies token signature using JWKS
   - Validates audience (`COGNITO_APP_CLIENT_ID`)
   - Validates issuer (Cognito User Pool URL)
   - Extracts user claims (`sub`, `email`, `name`, etc.)
4. User record synced/created in local database
5. User object attached to request context

**Internal API Authentication**:

- Worker uses `INTERNAL_CREW_API_KEY` (shared secret)
- Sent via `X-Internal-Api-Key` header or Bearer token
- CRUD service validates against configured secret

### 6.2 Dynamic Flow Building

**Configuration Parsing**:

- `tasks.yaml`: Defines tasks, state fields, read/write specifications
- `agents.yaml`: Defines agent roles, goals, backstories, tool assignments
- `tools_spec.yaml`: Documents available tools and their parameters

**Dependency Graph Construction**:

1. `build_flow_dependency_graph()` analyzes:
   - State field specifications (types, field_kind: context/data)
   - Task read specifications (which fields each task reads, cardinality)
   - Task write specifications (which fields each task writes, mode: replace/append)
2. Creates `FlowDependencyGraph` with:
   - `state_field_specs`: All state fields
   - `task_read_specs`: Per-task read declarations
   - `task_write_specs`: Per-task write declarations
   - `field_readers`: Reverse lookup (which tasks read each field)
   - `field_writers`: Reverse lookup (which tasks write each field)

**Required Input Inference**:

1. `infer_initial_inputs()` determines required inputs:
   - **Context fields**: All context fields read by any selected task
   - **Data fields**: Data fields that are required but not written by any selected task
2. Returns `{field_name: type_str}` dictionary

**FlowState Model Generation**:

1. `build_flow_state_model()` creates Pydantic model:
   - Includes metadata fields (`flow_id`, `run_id`, `crew_run_id`)
   - Includes only fields touched by selected tasks
   - Maps YAML types to Python types:
     - `string` → `str`
     - `date` → `str` (ISO format)
     - `list[Type]` → `List[Type]`
     - Custom types → Registered Pydantic models
2. Uses `pydantic.create_model()` to synthesize class dynamically

**Flow Class Generation**:

1. `build_dynamic_flow_class()` creates CrewAI Flow subclass:
   - `@start` method: `initialize_flow()` - Sets state from inputs
   - `@listen` methods: One per task - `step_task_{key}()`
2. Each task step:
   - Reads required fields from `self.state`
   - Interpolates task description with state values
   - Updates task status to RUNNING
   - Executes CrewAI task with guardrails
   - Writes outputs to `self.state`
   - Updates task status to COMPLETED/FAILED

**Agent & Tool Wiring**:

1. `build_crewai_agents()` instantiates agents from `agents.yaml`
2. Each agent assigned tools from `TOOL_MAP` registry
3. Agents share LLM from `llm_registry.general_llm`

### 6.3 Queue & Worker System

**Queue Entry Creation**:

1. CRUD service creates `CrewRunQueue` entry:
   - `crew_run_id`: Links to crew run record
   - `status`: QUEUED
   - `lease_token`: Generated UUID for lease management
   - `lease_expires_at`: Current time + visibility timeout

**Job Claiming**:

1. Worker polls `POST /internal/queue/claim`
2. CRUD service atomically:
   - Finds oldest QUEUED job
   - Updates status to CLAIMED
   - Sets `lease_expires_at` to now + visibility timeout
   - Returns job metadata (crew_run_id, queue_id, lease_token)
3. Worker spawns new OS process with job metadata

**Lease Management**:

1. Heartbeat thread runs in background (within worker process)
2. Every `HEARTBEAT_INTERVAL_SECONDS`:
   - Calls `POST /internal/queue/{queue_id}/heartbeat`
   - Sends `lease_token` and `visibility_timeout_seconds`
   - CRUD service extends `lease_expires_at`
   - Response includes `cancel_requested` flag
3. If heartbeat fails (network error):
   - Retries with exponential backoff (up to 3 retries)
   - If all retries fail, process continues (lease may expire)

**Process Isolation**:

- Each job runs in separate OS process (multiprocessing spawn context)
- Processes share no memory or state
- Each process creates own HTTP client
- Process crashes don't affect worker or other jobs

**Status Updates**:

- Worker process updates queue status via `PUT /internal/queue/{queue_id}/status`
- Requires `lease_token` (ensures only claiming process can update)
- Final status: COMPLETED, FAILED, or CANCELLED

### 6.4 Task Execution Flow

**Task Status Lifecycle**:

1. **QUEUED**: Task waiting to execute (initial state)
2. **RUNNING**: Task execution started
   - Status updated before CrewAI task execution
   - Task inputs serialized and stored
3. **COMPLETED**: Task execution succeeded
   - Status updated after successful execution
   - Task outputs serialized and stored
   - Completion timestamp recorded
4. **FAILED**: Task execution failed
   - Status updated on exception
   - Error details stored
   - Execution stops (downstream tasks remain QUEUED)

**Status Tracking Implementation**:

- `TaskStatusService` handles status updates
- Uses synchronous CRUD client (compatible with multiprocessing)
- Updates via `PUT /internal/crew-run/{crew_run_id}/task/{task_key}/status`
- Serializes Pydantic models to JSON-compatible dicts

**Guardrail Validation**:
Each task has guardrail chain:

1. **Structured Output Guardrail** (if task writes custom Pydantic type):

   - Validates output matches expected model schema
   - Re-validates using Pydantic `model_validate()`
   - Replaces `result.pydantic` with validated model

2. **LLM Judge Guardrail** (always runs):
   - Sends task description, expected output, and raw response to judge LLM
   - Judge responds with `GuardrailResponseFormat`:
     - `is_valid`: Boolean
     - `reason`: Explanation if invalid
   - If invalid, CrewAI retries task (up to max retries)

**State Updates**:

- Task outputs written to `self.state` based on write specifications
- Write modes:
  - `replace`: Overwrites field value
  - `append`: Appends to list field
- State persisted to crew run output after flow completion

**Error Handling**:

- Exceptions caught in task step function
- Task status set to FAILED
- Error details stored in task state
- Flow execution stops (remaining tasks stay QUEUED)
- Queue status updated to FAILED

### 6.5 Data Flow

**Frontend → CRUD Service**:

- User operations: `GET /crew`, `POST /crew`, `PUT /crew`, `DELETE /crew/{id}`
- Task management: `PUT /task/{crew_id}/save`
- Run history: `GET /crew-run/{crew_run_id}`
- Artifacts: `POST /artifact/{crew_run_id}`, `GET /artifact/{artifact_id}`

**Frontend → Crew Service**:

- Required inputs: `GET /crew/{crew_id}/required-inputs`
- Kickoff: `POST /crew/kickoff`
- Cancellation: `POST /crew/crew-run/{crew_run_id}/cancel`
- Retry: `POST /crew/crew-run/{crew_run_id}/retry`

**Crew Service → CRUD Service (Internal)**:

- Create crew run: `POST /internal/crew-run/create`
- Get crew: `GET /internal/crew/{crew_id}`
- Get crew run: `GET /internal/crew-run/{crew_run_id}`

**Worker → CRUD Service (Internal)**:

- Claim job: `POST /internal/queue/claim`
- Heartbeat: `POST /internal/queue/{queue_id}/heartbeat`
- Update status: `PUT /internal/queue/{queue_id}/status`
- Update crew run output: `PUT /internal/crew-run/{crew_run_id}/output`
- Update task status: `PUT /internal/crew-run/{crew_run_id}/task/{task_key}/status`
- Create artifact: `POST /internal/artifact/{crew_run_id}`

**All Services → S3**:

- Artifact upload: `boto3.client('s3').put_object()`
- Presigned URL: `boto3.client('s3').generate_presigned_url()`
- Path structure: `artifacts/{user_id}/{crew_run_id}/{file_name}`

---

## 7. Technology Stack Summary

### Frontend

- **Framework**: Next.js 14+ (App Router)
- **UI Library**: React 18+
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React Query (TanStack Query)
- **Flow Builder**: React Flow
- **Authentication**: AWS Amplify (Cognito integration)
- **API Client**: Generated from OpenAPI specs (`openapi-ts`)

### Backend Services

- **Framework**: FastAPI
- **Language**: Python 3.11+
- **Async Runtime**: Uvicorn
- **Package Management**: uv

### CRUD Service

- **ORM**: SQLAlchemy (async)
- **Database**: PostgreSQL (Supabase)
- **Migrations**: Alembic
- **Storage**: AWS S3 (boto3)
- **Authentication**: PyJWT, JWKS validation

### Crew Service

- **AI Framework**: CrewAI
- **LLM Provider**: OpenAI (GPT-4, GPT-4-turbo)
- **Browser Automation**: Playwright
- **Web Scraping**: Bright Data API
- **Document Processing**: Pandoc (Markdown → Word)
- **Template Rendering**: Orshot API
- **Image Generation**: OpenAI DALL-E, Google Imagen

### Infrastructure

- **Cloud Provider**: AWS
- **Compute**: EC2 (Auto Scaling Groups)
- **Container Registry**: Amazon ECR
- **Load Balancing**: Application Load Balancer
- **Frontend Hosting**: AWS Amplify
- **Database**: Supabase (PostgreSQL)
- **Storage**: S3
- **Authentication**: AWS Cognito
- **Infrastructure as Code**: Terraform
- **CI/CD**: GitHub Actions

### Development Tools

- **API Client Generation**: `openapi-python-client`, `openapi-ts`
- **Testing**: pytest (backend), Jest (frontend, planned)
- **Linting**: ruff (Python), ESLint (TypeScript)
- **Local Development**: Docker Compose

---

## 8. Configuration & Customization

### YAML-Based Configuration

The system is highly configurable through YAML files without code changes:

**`tasks.yaml`**:

- **State Fields**: Define flow state schema
  - Field types (string, date, list[Type], custom models)
  - Field kind (context: user-provided, data: task-generated)
  - Required flags, placeholders for UI
- **Tasks**: Define executable tasks
  - Task key, name, description
  - Agent assignment
  - Read specifications (which fields, cardinality)
  - Write specifications (which fields, mode)
  - Output file paths

**`agents.yaml`**:

- Agent definitions:
  - Role, goal, backstory (prompts for LLM)
  - Tool assignments (list of tool names)
- Agents are instantiated as CrewAI Agent objects

**`tools_spec.yaml`**:

- Documents available tools
- Parameter specifications
- Usage examples
- Tools are registered in `TOOL_MAP` in code

### Custom Type System

**Registered Custom Types**:

- `MarketingResearch`: Research report structure
- `ContentStrategy`: Content strategy with phases
- `SocialMediaSchedule`: Posting schedule
- `AllowedTemplateId`: Enum for template IDs
- `OrshotSchemaField`: Template field configuration

**Adding New Custom Types**:

1. Define Pydantic model in `app/models/models.py`
2. Register in `CUSTOM_TYPE_REGISTRY`
3. Use in `tasks.yaml` state fields
4. System automatically validates and handles type

### Tool Registration

**Available Tools**:

- `search_internet`: Google search via Bright Data
- `search_instagram`: Instagram post search
- `open_pages`: Web page scraping
- `open_instagram_posts`: Instagram post content extraction
- `markdown_to_word_doc`: Markdown to Word conversion
- `html_table_to_excel`: HTML table to Excel conversion
- `generate_social_media_schedule`: Schedule generation
- `generate_copywriting_for_schedule`: Copywriting generation
- `generate_image`: Image generation (DALL-E)
- `generate_imagen`: Image generation (Imagen)
- `orshot_render`: Template rendering
- `calculate_num_weeks`: Date calculation
- `verify_sum_equals_expected`: Validation utility

**Adding New Tools**:

1. Implement tool function in `app/lib/tools/`
2. Register in `TOOL_MAP` in `flow_utils.py`
3. Document in `tools_spec.yaml`
4. Assign to agents in `agents.yaml`

### Flow State Schema Definition

State fields are defined in `tasks.yaml` under `state.fields`:

```yaml
state:
  fields:
    theme:
      type: string
      field_kind: context
      required: true
    marketing_research:
      type: MarketingResearch
      field_kind: data
      required: false
```

- **Context fields**: Always user-provided inputs
- **Data fields**: May be produced by tasks or provided by user
- System infers required inputs based on task dependencies

---

## Related Documentation

For deeper technical details, see:

- [Worker Architecture and Lifecycle](worker.md) - Detailed worker implementation
- [Dynamic Flow Building](dynamic_flow.md) - Flow construction process
- [Configuration Guide](configuration.md) - YAML configuration structure
- [Custom Type Handling](custom_types.md) - Type system documentation
- [Crew Run Cancellation](crewrun_cancellation.md) - Cancellation mechanism
- [Crew Run Retry Flow](crew_run_retry.md) - Retry implementation
- [Required Inputs](required_inputs.md) - Input inference and validation
- [Guardrail Pipeline](dynamic_flow_guardrails.md) - Output validation

---

## Conclusion

This platform provides a powerful, flexible system for automating marketing campaign creation through multi-agent AI workflows. The architecture emphasizes:

- **Separation of Concerns**: Clear boundaries between frontend, data persistence, and AI orchestration
- **Dynamic Configuration**: YAML-driven flows enable changes without code deployment
- **Reliability**: Queue-based execution, retry mechanisms, and graceful cancellation
- **Observability**: Real-time status tracking at task and run levels
- **Scalability**: Process-per-job model enables concurrent execution

The system is designed to grow with new agents, tasks, and tools while maintaining type safety and validation throughout the execution pipeline.
