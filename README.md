
# AI Engineering Crew

A multi agent software engineering pipeline built with the CrewAI framework.  
The project takes a plain English requirement and turns it into a working Python application through a structured software delivery flow.

Instead of asking one LLM to generate everything in a single shot, this system splits the work into specialized engineering roles:

1. Product manager converts requirements into a PRD
2. Engineering lead creates API, state, and error design contracts
3. Backend engineers generate Python modules
4. Frontend engineer creates a lightweight Gradio UI
5. Test engineer generates deterministic unit tests
6. Debugging engineer fixes failing implementations
7. Sandboxed verifier runs final tests inside Docker

The system behaves more like a small engineering team than a single prompt.

---

# Project Goal

The goal of this project is to build a reliable AI driven software engineering workflow where every stage validates the next stage before code moves forward. The pipeline focuses on deterministic generation, strict contracts, safe execution, and automated repair loops. Instead of optimizing only for code generation speed, the system optimizes for correctness, traceability, and controlled outputs.

---

# Architecture Overview

```text
Requirements
    ↓
PRD Generation
    ↓
Design Contracts
    ├── API Contract
    ├── State Model
    └── Error Registry
    ↓
Backend Code Generation
    ├── exceptions.py
    ├── models.py
    └── account_manager.py
    ↓
Frontend Generation
    ↓
Unit Test Generation
    ↓
Sandboxed Docker Verification
    ↓
Automatic Bug Fixing
    ↓
Re Verification
```

---

# Core Design Philosophy

## 1. Small Specialized Agents

Each agent has a very narrow responsibility.

Example:

- Engineering lead never writes code
- Backend engineer never changes requirements
- Test engineer only validates behavior
- Debugging engineer applies minimal fixes

This reduces hallucination and scope creep.

Agent definitions are stored in:

- `agents.yaml`

---

# Agents Breakdown

## Product Manager

Responsible for converting raw requirements into a structured PRD.

Key rules:

- No invented features
- Every requirement mapped to acceptance criteria
- Explicit out of scope section

Configured with reasoning enabled.

---

## Engineering Lead

Creates structured design contracts.

Outputs:

- API contract table
- State model tables
- Error registry table

The design stage is intentionally strict because downstream code depends on exact schemas and exception names.

---

## Backend Engineer

Responsible for generating:

- `exceptions.py`
- `models.py`
- `{module_name}.py`

The core backend agent must:

- Validate before mutation
- Use exact exception types
- Avoid redefining models
- Follow design contracts exactly

---

## Frontend Engineer

Builds a lightweight Gradio application.

Important constraint:

All business logic must stay in the backend module.

Frontend only calls backend APIs.

---

## Test Engineer

Creates deterministic unit tests.

Interesting detail:

Expected values are derived from known stock prices:

- AAPL = 10.0
- TSLA = 15.0
- GOOGL = 20.0

This prevents flaky assertions.

---

## Bug Fix Engineer

Reads test failures and applies targeted fixes instead of rewriting the whole module.

This is important because large rewrites often break already passing behavior.

---

# Deep Dive Into Pipeline

## Phase 1: Requirements Engineering

Defined in `requirements_task`.

The raw prompt is transformed into a PRD with strict sections:

- Scope
- Functional requirements
- Technical constraints
- Out of scope
- Acceptance criteria

Interesting part:

The task explicitly prevents feature invention.

That single constraint matters a lot because later stages assume the PRD is the source of truth.

---

## Phase 2: Design Contracts

Three independent design artifacts are generated.

### API Design

Defines:

- Method signatures
- Parameters
- Return types
- Exceptions
- Preconditions
- Postconditions

This behaves almost like an interface contract.

### State Model

Defines internal state invariants.

Example:

- accounts dict
- holdings dict
- transaction history
- total deposited funds

This reduces ambiguity before implementation begins.

### Error Registry

One of the most important parts of the system.

It centralizes:

- Exception names
- Trigger conditions
- Exact error messages

Example rule:

```text
shares <= 0 and non integer shares must BOTH raise InvalidAmountError
```

This avoids inconsistent behavior across generated files.

---

# Dynamic Dependency Injection

One of the strongest parts of the architecture is `_inject_file()` inside `crew.py`.

The function reads generated artifacts and injects them into downstream prompts.

Example flow:

```text
requirements.md
    ↓
design_api.md
    ↓
backend_core_task
```

The backend engineer therefore receives:

- API design
- State design
- Error definitions
- Existing support files

This creates contextual continuity between stages.

Without this mechanism, each agent would operate in isolation.

---

# Guardrail System

Implemented in `guardrails.py`.

This is not just output validation.
It actively blocks malformed or unsafe artifacts.

## Syntax Validation

Generated code is parsed using Python AST:

```python
ast.parse(source)
```

This catches invalid Python before saving files.

---

## Structural Validation

Example:

The backend module must define:

```python
class AccountManager
```

If missing, generation fails and retries happen automatically.

---

## Forbidden Imports

Test files cannot import frameworks like:

- Flask
- FastAPI
- Requests
- Django

Reason:

Tests must stay deterministic and isolated.

---

# GuardedPythonTask

Custom task type:

```python
class GuardedPythonTask(Task)
```

Important behavior:

The validated transformed output gets persisted instead of raw LLM output.

That means markdown wrappers and formatting noise never leak into generated artifacts.

---

# Sandboxed Verification

Implemented in `sandboxed_test_runner.py`.

This is the most security aware part of the project.

Generated code is never executed directly on the host machine.

Instead, tests run inside a hardened Docker container.

---

# Docker Isolation Controls

The verifier applies multiple runtime restrictions:

```text
--network none
--read-only
--cap-drop ALL
--memory 256m
--cpus 1
```

What this protects against:

- Network access
- Filesystem mutation
- Privilege escalation
- Resource abuse

This is a strong design choice for AI generated code execution.

---

# Automatic Repair Loop

Pipeline sequence:

```text
Generate code
    ↓
Run tests
    ↓
Collect failures
    ↓
Inject traceback into bug fix task
    ↓
Patch implementation
    ↓
Re run tests
```

This creates a closed loop autonomous engineering workflow.

---

# Input Validation

`build_inputs()` in `main.py` validates:

- Requirements are non empty
- Module names are valid Python identifiers
- Class names follow PascalCase

Example:

```python
if not re.fullmatch(r"[A-Z][A-Za-z0-9_]*", class_name):
```

This prevents prompt injection through identifiers.

---

# Execution Flow

Main execution happens in:

```python
run()
```

Flow:

1. Build validated inputs
2. Initialize engineering crew
3. Run sequential pipeline
4. Verify generated artifacts
5. Persist verification report
6. Raise exception if verification fails

---

# Output Structure

Generated files are written into:

```text
output/
```

Typical artifacts:

```text
output/
├── requirements.md
├── design_api.md
├── design_state.md
├── design_errors.md
├── exceptions.py
├── models.py
├── account_manager.py
├── app.py
├── test_account_manager.py
├── test_results.txt
├── verification.md
└── crew_run.json
```

---

# Why This Project Is Interesting

Most AI coding demos stop at code generation.

This project goes much further:

- Structured engineering workflow
- Multi stage contract enforcement
- AST based validation
- Sandboxed execution
- Automated repair loop
- Deterministic testing
- Dependency aware prompt chaining

It combines ideas from:

- AI agents
- software architecture
- secure execution
- CI pipelines
- autonomous debugging systems

---

# Example Scenario

Suppose the generated backend incorrectly allows negative withdrawals.

What happens?

1. Test engineer creates failing test
2. Docker verifier detects failure
3. Traceback stored in `test_results.txt`
4. Bug fix engineer receives traceback
5. Minimal patch applied
6. Verification reruns automatically

This is very similar to a lightweight autonomous CI repair pipeline.

---

# Tech Stack

- Python
- CrewAI
- Docker
- Pydantic
- AST module
- Gradio
- dotenv

---

# How To Run

## Install Dependencies

```bash
pip install crewai python-dotenv pydantic gradio
```

Docker is also required.

---

## Run The Pipeline

```bash
python main.py
```

---

# Important Security Decisions

## No Network Access During Verification

Generated tests run with:

```text
--network none
```

Even if generated code attempts external communication, it fails.

---

## Read Only File System

Container mounts output directory as read only:

```text
/workspace:ro
```

Generated code cannot mutate artifacts during verification.

---

## Strict Resource Limits

The verifier prevents runaway execution using:

- CPU limits
- memory limits
- process count limits
- execution timeout

---

# Possible Future Enhancements

- Parallel task execution
- Retry strategy based on failure category
- Semantic diff patching
- Mutation testing
- Static type checking
- Coverage thresholds
- Multi language generation
- Human approval checkpoints
- Kubernetes sandbox execution
- Persistent execution history

---

# Key Learning From This Architecture

The biggest idea in this project is this: Reliable AI engineering systems are not built from stronger prompts alone.

They are built from:
- Constrained workflows
- Explicit contracts
- Verification loops
- Isolated execution
- Narrow responsibilities
- Well designed prompts combined with mature models and strong validation layers
- Continuous validation between stages instead of trusting a single generation step
- Clear PRD and design contracts because weak upstream design makes downstream correction expensive and unstable
- Structured repair loops that can detect and recover from failures automatically
- Deterministic testing instead of subjective output evaluation

One important learning from this architecture is that prompt quality alone is not enough. Even strong models can drift if requirements, API contracts, or state definitions are ambiguous. The earlier the pipeline loses alignment, the harder it becomes for downstream agents to recover cleanly.

This project demonstrates that reliable AI software systems behave more like engineering pipelines than chat interfaces. The real strength comes from combining good prompts, specialized agents, validation checkpoints, and controlled execution environments into a single coordinated workflow.
