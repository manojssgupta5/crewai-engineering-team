"""Command-line entry point for the engineering crew."""
import re
import warnings
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

from crew import EngineeringTeam
from tools import verify_final_artifacts

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

DEFAULT_REQUIREMENTS = """
Build a simple account management system for a trading simulation platform.

Functional requirements:
- Users can create an account and deposit funds.
- Users can withdraw funds, unless doing so would make their cash balance negative.
- Users can buy shares, unless they lack sufficient cash.
- Users can sell shares, unless they lack sufficient holdings.
- The system reports current cash, holdings, transaction history, portfolio value,
  and profit or loss measured against total deposited funds.

Technical constraints:
- Provide get_share_price(symbol: str) -> float and a deterministic implementation
  returning fixed prices for AAPL, TSLA, and GOOGL.
- Produce one self-contained backend Python module and a small optional Gradio demo.
- Do not introduce credentials, authentication, databases, or network access unless
  they are explicitly requested.
""".strip()


def build_inputs(
    requirements: str = DEFAULT_REQUIREMENTS,
    module_name: str = "account_manager",
    class_name: str = "AccountManager",
) -> dict[str, str]:
    """Validate user-controlled identifiers and form CrewAI inputs."""
    if not requirements.strip():
        raise ValueError("requirements must not be empty")
    if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", module_name):
        raise ValueError("module_name must be a valid Python module identifier")
    if not re.fullmatch(r"[A-Z][A-Za-z0-9_]*", class_name):
        raise ValueError("class_name must be a PascalCase Python class identifier")
    return {
        "requirements": requirements.strip(),
        "module_name": module_name,
        "class_name": class_name,
    }


def run() -> None:
    """Generate, review, repair, and verify the sample application."""
    Path("output").mkdir(parents=True, exist_ok=True)
    result = EngineeringTeam().crew().kickoff(inputs=build_inputs())
    verification = verify_final_artifacts()
    Path("output/verification.md").write_text(
        f"# Final Verification\n\n```\n{verification}\n```\n",
        encoding="utf-8",
    )
    if not verification.startswith("PASSED:"):
        raise RuntimeError(verification)
    print(result.raw)
    print(verification)

if __name__ == "__main__":
    run()
