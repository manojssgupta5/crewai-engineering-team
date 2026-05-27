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
    python_code_guardrail, 
    review_output_guardrail
)

from crew_ai_engg_team.tools.sandboxed_test_runner import (
    SandboxedTestRunner,
)

from crew_ai_engg_team.guardrails import (
    GuardedPythonTask,
    python_code_guardrail,
    review_output_guardrail,
)

test_runner_tool = SandboxedTestRunner()
    
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
    def reviewer(self) -> Agent:
        return Agent(config=self.agents_config['reviewer'], reasoning=True)

    @agent
    def fix_review_engineer(self) -> Agent:
        return Agent(config=self.agents_config['fix_review_engineer'], reasoning=True)

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
            guardrail=python_code_guardrail,
            max_retries=2,
        )

    @task
    def frontend_task(self) -> Task:
        return GuardedPythonTask(
            config=self.tasks_config["frontend_task"],
            guardrail=python_code_guardrail,
            max_retries=2,
        )

    @task
    def review_task(self) -> Task:
        return Task(
            config=self.tasks_config["review_task"],
            guardrail=review_output_guardrail,
            max_retries=2,
        )

    @task
    def backend_repair_task(self) -> Task:
        return GuardedPythonTask(
            config=self.tasks_config["backend_repair_task"],
            guardrail=python_code_guardrail,
            max_retries=2,
        )

    @task
    def frontend_repair_task(self) -> Task:
        return GuardedPythonTask(
            config=self.tasks_config["frontend_repair_task"],
            guardrail=python_code_guardrail,
            max_retries=2,
        )

    @task
    def test_task(self) -> Task:
        return GuardedPythonTask(
            config=self.tasks_config["test_task"],
            guardrail=python_code_guardrail,
            max_retries=2,
        )
    
    @task
    def test_execution_task(self) -> Task:
        return Task(
            config=self.tasks_config["test_execution_task"],
            max_retries=2,
        )
    
    @task
    def test_fix_task(self) -> Task:
        return GuardedPythonTask(
            config=self.tasks_config["test_fix_task"],
            guardrail=python_code_guardrail,
            max_retries=2,
        )
    
    @task
    def test_execution_task_rerun(self) -> Task:
        return Task(
            config=self.tasks_config["test_execution_task_rerun"],
            max_retries=2,
        )

    def _build_tasks(self):
        tasks = []

        requirements_file = Path("output/requirements.md")
        design_file = Path("output/design.md")
        backend_code = Path("output/account_manager.py")
        frontend_code = Path("output/app.py")
        test_account_manager = Path("output/test_account_manager.py")

        if not requirements_file.exists():
            tasks.append(self.requirements_task())

        if not design_file.exists():
            tasks.append(self.design_task())

        if not backend_code.exists():
            tasks.append(self.backend_task())

        if not frontend_code.exists():
            tasks.append(self.frontend_task())

        if not test_account_manager.exists():
            tasks.append(self.test_task())

        tasks.extend(
            [
                # self.requirements_task(),
                # self.design_task(),
                # self.backend_task(),
                # self.frontend_task(),
                self.review_task(),
                self.backend_repair_task(),
                self.frontend_repair_task(),
                #self.test_task(),
                self.test_execution_task(),
                self.test_fix_task(),
                self.test_execution_task_rerun(),
            ]
        )
        return tasks

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
