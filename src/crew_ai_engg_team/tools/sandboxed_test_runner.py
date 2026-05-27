"""Execute final generated tests inside a constrained Docker container."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class SandboxedTestInput(BaseModel):
    """The verifier can only request the fixed, predefined validation action."""

    confirmation: str = Field(
        default="run",
        description="Use the literal value 'run' to validate final generated artifacts.",
    )


def build_docker_command(output_dir: Path, image: str) -> list[str]:
    """Build the restricted test command for generated artifacts."""
    return [
        "docker",
        "run",
        "--rm",
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--pids-limit",
        "128",
        "--memory",
        "256m",
        "--cpus",
        "1",
        "--tmpfs",
        "/tmp:rw,noexec,nosuid,size=32m",
        "-e",
        "PYTHONDONTWRITEBYTECODE=1",
        "-v",
        f"{output_dir}:/workspace:ro",
        "-w",
        "/workspace",
        image,
        "python",
        "-m",
        "unittest",
        "discover",
        "-s",
        "/workspace",
        "-p",
        "test_*.py",
        "-v",
    ]


class SandboxedTestRunner(BaseTool):
    """Run generated unit tests without executing model output on the host."""

    name: str = "verify_final_artifacts"
    description: str = (
        "Runs all final unittest files against final artifacts in an isolated, "
        "network-disabled Docker container. Call once with confirmation='run'."
    )
    args_schema: type[BaseModel] = SandboxedTestInput

    def _run(self, confirmation: str = "run") -> str:
        if confirmation != "run":
            return "ERROR: confirmation must be 'run'"

        output_dir = Path("output").resolve()
        if not output_dir.is_dir():
            return "ERROR: output directory does not exist"
        if not any(output_dir.glob("test_*.py")):
            return "ERROR: no generated unittest file found in output"

        image = os.getenv("CREW_TEST_IMAGE", "python:3.12-slim")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:/@-]{0,127}", image):
            return "ERROR: CREW_TEST_IMAGE contains unsupported characters"

        command = build_docker_command(output_dir, image)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=180,
                check=False,
            )
        except FileNotFoundError:
            return "ERROR: Docker is required to verify generated code safely"
        except subprocess.TimeoutExpired:
            return "FAILED: isolated tests exceeded the 180 second timeout"

        output = (result.stdout + result.stderr).strip()
        if len(output) > 6000:
            output = "...[truncated]\n" + output[-6000:]
        status = "PASSED" if result.returncode == 0 else "FAILED"
        return f"{status}: isolated final-artifact verification\n{output}"


def verify_final_artifacts() -> str:
    """Deterministically execute final verification outside model control."""
    return SandboxedTestRunner()._run("run")
