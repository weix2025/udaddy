# Project: Daddy - Next-generation AI-driven Secure Computing Platform

This document is a comprehensive plan and design memorandum for building a next-generation computing platform centered on "Versioned Digital Assets," driven by AI dialogue, and pursuing ultimate performance and security. It fully documents the project's evolution, design decisions, final architecture, and future implementation roadmap.

## 1. Design Direction & Core Philosophy

- **AI-First**: The application's core interaction interface is AI dialogue. Users issue commands via natural language, and the system understands the intent to execute corresponding workflows.
- **Versioned Digital Assets**: Discarding the traditional concept of "tasks," the system's core is the versionable "Workspace." Every modification or execution is a reference to or creation of an asset version, similar to a Git commit, ensuring traceability, reproducibility, and security.
- **Unique Identifiers**: All user-visible entities in the system (users, workflows, workspaces, etc.) use prefixed nanoids as unique identifiers (e.g., `usr_xxxx`, `wflw_xxxx`), ensuring global uniqueness, security, and readability of IDs.
- **Performance & Security First**: The backend architecture prioritizes high-concurrency performance and memory safety, with the final technology choice leaning towards the Rust language.
- **Decoupled & Cross-Platform**: The frontend is built with KMP (Kotlin Multiplatform), allowing one codebase to serve Android, iOS, Desktop, and Web in the future. The backend provides a pure API, completely decoupled from the frontend.

## 2. Monorepo Project Structure

This is a Kotlin Multiplatform project. The code is organized into several modules:

- `/composeApp`: Contains code shared across Compose Multiplatform applications (Android, iOS, Desktop, Web).
  - `commonMain` is for code common to all targets.
  - Platform-specific folders (`androidMain`, `iosMain`, etc.) are for platform-specific Kotlin code.
- `/iosApp`: The Xcode project entry point for the iOS application.
- `/server`: A Ktor-based backend server application. It can provide API services to client applications and access the shared logic in the `/shared` module.
- `/shared`: Contains core business logic shared across all targets (Android, iOS, Desktop, Web, Server). Data models, business rules, and network layer definitions should be placed here.

## 3. Final Architecture & Data Model

### Architecture Diagram & Data Flow

```
+-------------+      +----------------+      +----------------------+
|             | (1)  |                | (2)  |                      |
|   Frontend  |----->| API Gateway    |----->|  Message Queue       |
| (KMP App)   |      | (Rust/Python)  |      |  (e.g., Redis)       |
|             |      |                |      |                      |
+-------------+      +----------------+      +----------------------+
      ^     |                                          |
      | (5) |                                          | (3. Task)
      |     | (WebSocket)                              V
      |     |                                +----------------------+
      |     |                                |                      |
      +-----|--------------------------------| Compute Worker(s)    |
            |                                | (Rust)               |
            | (4. Result)                    | - WASM Runtime       |
            +------------------------------->| - Data Processing    |
                                             +----------------------+
```

**Data Flow:**

1.  **Request Initiation**: The KMP frontend application sends an operation request via HTTPS to the API Gateway (e.g., "start version v1.1.0 of workflow wflw_XyZ123Ab").
2.  **Task Enqueueing**: After user authentication and request validation, the API Gateway does not execute the task directly. It serializes the task into a JSON message containing `workspace_nanoid` and input parameters, pushes it to the Redis task queue, and immediately returns a task ID to the frontend.
3.  **Task Execution**: An independent cluster of Rust Compute Workers listens to the task queue. Upon receiving a task, it loads the corresponding Workspace data from the database, sets up the WASM runtime environment, and executes the computation.
4.  **Result Write-back**: After task completion, the Worker writes the result (success or failure, output data, logs, etc.) back to the database, updating the task's status.
5.  **Status Synchronization**: The frontend can receive real-time task status updates via a WebSocket connection or by polling the API Gateway with the task ID, enabling real-time updates for the monitoring interface.

### Core Data Model (Database Schema)

```sql
-- User Table: The top-level entity, the ultimate owner of all assets.
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    -- Public-facing, secure, prefixed unique ID.
    nanoid VARCHAR(255) UNIQUE NOT NULL, -- e.g., 'usr_A1b2C3d4'
    name VARCHAR(255),
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Workflow Template Table: A logical container for a user-created workflow, does not contain executable logic itself.
CREATE TABLE workflows (
    id SERIAL PRIMARY KEY,
    -- The workflow's own unique ID.
    nanoid VARCHAR(255) UNIQUE NOT NULL, -- e.g., 'wflw_XyZ123Ab'
    -- Foreign key to the user who owns this workflow, ensuring clear data ownership.
    owner_nanoid VARCHAR(255) NOT NULL REFERENCES users(nanoid) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Workspace/Version Snapshot Table: The core of the core, a specific, immutable version implementation of a workflow.
CREATE TABLE workspaces (
    id SERIAL PRIMARY KEY,
    -- The workspace's own unique ID, representing a specific execution or version.
    nanoid VARCHAR(255) UNIQUE NOT NULL, -- e.g., 'wspc_pQ9r8s7T'
    -- Foreign key to the logical workflow this workspace belongs to.
    workflow_nanoid VARCHAR(255) NOT NULL REFERENCES workflows(nanoid) ON DELETE CASCADE,
    -- Version tag defined by the user, can be a semantic version, branch name, or any meaningful string.
    version_tag VARCHAR(255) NOT NULL, -- e.g., 'v1.1.0', 'main', 'feat-new-model'
    -- Using PostgreSQL's efficient JSONB type to store all metadata and logic definitions for this workspace version.
    -- e.g., {"dag": {"nodes": [...], "edges": [...]}, "params": {...}, "wasm_asset_id": "..."}
    data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    -- Composite unique constraint to ensure version tags are unique within the same workflow, preventing version conflicts.
    UNIQUE (workflow_nanoid, version_tag)
);
```

## 4. How to Build and Run

You can use Gradle to build and run each part of this project.

-   **Web (Wasm)**: Start a local development server.
    ```bash
    ./gradlew :composeApp:wasmJsBrowserDevelopmentRun
    ```
-   **Desktop**: Run the desktop application on your current OS.
    ```bash
    ./gradlew :composeApp:desktopRun
    ```
-   **Server**: Start the backend Ktor server.
    ```bash
    ./gradlew :server:run
    ```
-   **Android**: Open the project in Android Studio, select `composeApp` as the run configuration, and run it.
-   **iOS**: On a macOS machine with Xcode, open `iosApp/iosApp.xcodeproj` and run from Xcode.

## 5. Implementation Roadmap

### Conceptually Done
- [x] Product direction confirmed: The final product form and core interaction (AI dialogue-driven) are confirmed.
- [x] Data model confirmed: The core three-layer data model (User, Workflow, Workspace) is designed.
- [x] ID strategy confirmed: The strategy of using prefixed nanoids as unique IDs globally is established.
- [x] Architecture pattern confirmed: The "compute offloading" high-performance hybrid architecture is selected.
- [x] Core technology stack confirmed: The decision to use Rust as the core computing layer is made.

### To-Do Implementation
- [ ] **Project Initialization (Monorepo Setup)**:
    - [ ] Create a monorepo structure containing the KMP frontend and Rust backend (API + Worker).
    - [ ] Configure shared build scripts, code formatters (`rustfmt`, `ktlint`), and a CI/CD pipeline.
- [ ] **Database Layer (Rust)**:
    - [ ] Use `sqlx` (for compile-time checked safety) to define the data access layer in the Rust project.
    - [ ] Use `sqlx-cli` to initialize and manage database migration scripts.
- [ ] **Rust Worker Development (Compute Core)**:
    - [ ] Implement robust logic to consume tasks from Redis.
    - [ ] Integrate the `wasmtime` or `wasmer` library to load, instantiate, and call WASM modules, including resource limiting (memory, CPU time).
    - [ ] Implement logic to write back task results (success/failure/logs).
- [ ] **API Service Development (Rust/Python)**:
    - [ ] Implement JWT-based user authentication and authorization middleware.
    - [ ] Implement full CRUD APIs for `users`, `workflows`, and `workspaces`.
    - [ ] Implement the "start workflow" API, whose core logic is to validate parameters and publish a task to Redis.
    - [ ] (Future) Implement the AI dialogue API.
- [ ] **KMP Frontend Development**:
    - [ ] Connect to the real backend API, replacing the `MockRepository`.
    - [ ] Implement the bottom navigation bar and the UI framework for the 4 core screens.
    - [ ] Implement the AI dialogue interface.
    - [ ] Implement the n8n-style visual workflow real-time monitoring interface.
