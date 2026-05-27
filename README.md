# Crew AI Engineering Team

This is a production-oriented CrewAI example that turns a bounded software
specification into reviewed Python artifacts and verifies the final backend in
an isolated container.

The dependency range is intentionally limited to the validated CrewAI `0.108.x`
API because artifact persistence behavior is part of the security boundary.

## What Is Different

- It uses a valid installable `src/crew_ai_engg_team` package and matching CLI entry point.
- Requirements prompts prohibit silently adding authentication, storage, or integrations.
- Code artifacts pass an AST syntax guardrail before CrewAI writes them to disk.
- Repair tasks overwrite the canonical backend and frontend files that are subsequently used.
- Generated tests use Python's standard-library `unittest`.
- After generation, the CLI deterministically executes final tests through
  `verify_final_artifacts` inside Docker with no network, a read-only artifact
  mount, dropped capabilities, and resource limits.

## Prerequisites

- Python 3.10 through 3.12
- Docker running when the final verification task executes
- An LLM provider supported by CrewAI

The default model is `gpt-4o-mini`; set `OPENAI_API_KEY` in `.env` or
override the model with `CREW_LLM_MODEL`, for example:

```bash
export CREW_LLM_MODEL=ollama/qwen2.5-coder:7b
```

Specialized local agents and request timeout can be configured independently:

```bash
export FRONTEND_LLM_MODEL=ollama/gemma3:12b
export REVIEWER_LLM_MODEL=ollama/llama3:8b
export CREW_LLM_TIMEOUT_SECONDS=180
```

Docker is intentionally required only when final generated code is tested. The
crew can be imported and initialized without a Docker daemon.

## Install And Run

```bash
cd 3_crew/community_contributions/crew_ai_engg_team
uv sync
uv run run_crew
```

For local development tests:

```bash
uv sync --extra dev
uv run pytest
```

## Output

A run writes these artifacts under `output/`:

- `requirements.md` and `design.md`
- `{module_name}.py` and `app.py`, containing the final repaired source files
- `review.md`
- `test_{module_name}.py`
- `verification.md`
- `crew_run.json`

## Safety Boundary

The syntax guardrail confirms that saved code parses as Python; it is not a
security scanner. The safety control is that generated tests and imported
generated backend code execute only inside the constrained Docker container,
and verification failure causes the CLI command to fail.
Do not run files from `output/` directly on a host that contains secrets.
