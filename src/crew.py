"""Crew definition for generating and validating a small Python application."""
import os
from pathlib import Path

from crewai import Agent, Crew, Process, Task

from crewai.project import (
    CrewBase,
    agent,
    crew,
    task
)

from tools.guardrails import (
    GuardedPythonTask,  
    make_python_guardrail,
    _FORBIDDEN_TEST_IMPORTS
)

from tools.sandboxed_test_runner import (
    SandboxedTestRunner,
)

test_runner_tool = SandboxedTestRunner()

_FENCE = {".py": "python", ".md": "markdown", ".txt": ""}

def _inject_file(task: Task, path: Path, label: str) -> Task:
    """Append an existing artifact's content to a task description """
    if not path.exists():
        return task
    fence = _FENCE.get(path.suffix, "")
    safe = path.read_text().replace("{", "{{").replace("}", "}}")
    task.description += (
        "\n\n### Existing " + label + " — read carefully before making changes:\n"
        "```" + fence + "\n" + safe + "\n```"
    )
    return task

def _inject_files(task: Task, *pairs: tuple) -> Task:
    """Convenience wrapper to inject multiple files into one task."""
    for path, label in pairs:
        _inject_file(task, path, label)
    return task


@CrewBase
class EngineeringTeam:
    """Generate, review, repair, and safely verify software artifacts."""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    #-------------------------Agents List-------------------------#
    @agent
    def product_manager(self) -> Agent:
        return Agent(config=self.agents_config['product_manager'], reasoning=True)

    @agent
    def engineering_lead(self) -> Agent:
        return Agent(config=self.agents_config['engineering_lead'], reasoning=True)

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(config=self.agents_config['backend_engineer'], reasoning=True)

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(config=self.agents_config['frontend_engineer'], reasoning=True)

    @agent
    def test_engineer(self) -> Agent:
        return Agent(config=self.agents_config['test_engineer'], reasoning=True)

    @agent
    def bug_fix_engineer(self) -> Agent:
        return Agent(config=self.agents_config['bug_fix_engineer'], reasoning=True)


    #-------------------------Tasks List-------------------------#
    @task
    def requirements_task(self) -> Task:
        return Task(config=self.tasks_config["requirements_task"])

    @task
    def design_task(self) -> Task:
        return Task(config=self.tasks_config["design_task"])

    @task
    def backend_task(self) -> Task:
        return GuardedPythonTask(
            config=self.tasks_config["backend_task"],
            guardrail=make_python_guardrail(self._class_name),
            max_retries=3,
        )

    @task
    def frontend_task(self) -> Task:
        return GuardedPythonTask(
            config=self.tasks_config["frontend_task"],
            guardrail=make_python_guardrail(),
            max_retries=3,
        )

    @task
    def test_task(self) -> Task:
        return GuardedPythonTask(
            config=self.tasks_config["test_task"],
            guardrail=make_python_guardrail(
                forbid_imports=_FORBIDDEN_TEST_IMPORTS
            ),
        max_retries=2,
    )

    @task
    def test_execution_task(self) -> Task:
        return Task(
            config=self.tasks_config["test_execution_task"],
            tools=[test_runner_tool],
            max_retries=2,
        )

    @task
    def test_fix_task(self) -> Task:
        return GuardedPythonTask(
            config=self.tasks_config["test_fix_task"],
            guardrail=make_python_guardrail(self._class_name),
            max_retries=3,
        )

    @task
    def test_execution_task_rerun(self) -> Task:
        return Task(
            config=self.tasks_config["test_execution_task_rerun"],
            tools=[test_runner_tool],
            max_retries=2,
        )

    #--------------------BuildTasks--------------------#
    def _build_tasks(self):
        tasks = []

        # All output artifact paths in one place
        requirements_file = Path("output/requirements.md")
        design_file = Path("output/design.md")
        backend_code = Path("output/account_manager.py")
        frontend_code = Path("output/app.py")
        test_file = Path("output/test_account_manager.py")
        test_failures_file = Path("output/test_failures.txt")

        if not requirements_file.exists():   
            tasks.append(self.requirements_task())

        if not design_file.exists():
            design = self.design_task()
            _inject_files(
                design,
                (requirements_file, "requirements.md"),
            )
            tasks.append(design)

        if not backend_code.exists():
            backend = self.backend_task()
            _inject_files(
                backend,
                (design_file, "design.md")
            )
            tasks.append(backend)

        if not frontend_code.exists():
            frontend = self.frontend_task()
            _inject_files(
                frontend,
                (design_file, "design.md")
            )
            tasks.append(frontend)

        if not test_file.exists():
            test = self.test_task()
            _inject_files(
                test,
                (design_file, "design.md"),
                (frontend_code, "app.py"),
                (backend_code, "account_manager.py"),
            )
            tasks.append(test)

        if not test_failures_file.exists():
            test_execution_task = self.test_execution_task()
            _inject_files(
                test_execution_task,
                (frontend_code, "app.py"),
                (backend_code, "account_manager.py"),
                (test_file, "test_account_manager.py"),
            )
        tasks.append(test_execution_task)

        test_fix = self.test_fix_task()
        _inject_files(
            test_fix,
            (test_failures_file, "test_failures.txt"),
            (frontend_code, "app.py"),
            (backend_code, "account_manager.py"),
            (test_file, "test_account_manager.py"),    
        )
        tasks.append(test_fix)

        tasks.append(self.test_execution_task_rerun())
        
        return tasks

    #--------------------Crew--------------------#
    @crew
    def crew(self) -> Crew:
        """Create the sequential engineering pipeline."""
        Path("output").mkdir(parents=True, exist_ok=True)
        return Crew(
            agents=self.agents,
            tasks=self._build_tasks(),
            process=Process.sequential,
            verbose=True,
            output_log_file="output/crew_run.json",
        )
