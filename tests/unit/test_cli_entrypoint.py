import os
import subprocess
import sys

from pathlib import Path

import pytest

from click.testing import CliRunner


@pytest.mark.unit
def test_entrypoint_uses_canonical_completion_var() -> None:
    """Both aliases use _AI_AGENT_RULES_COMPLETE for bash completion."""
    from ai_rules.cli import main

    runner = CliRunner(env={"_AI_AGENT_RULES_COMPLETE": "bash_source"})

    result = runner.invoke(
        main, [], standalone_mode=False, complete_var="_AI_AGENT_RULES_COMPLETE"
    )
    assert result.exit_code == 0
    assert "_AI_AGENT_RULES_COMPLETE" in result.output

    result_without = runner.invoke(main, [])
    assert result_without.exit_code != 0
    assert "_AI_AGENT_RULES_COMPLETE" not in result_without.output


@pytest.mark.unit
def test_cli_package_supports_module_execution() -> None:
    repo_root = Path(__file__).parents[2]
    src_path = repo_root / "src"
    existing_pythonpath = os.environ.get("PYTHONPATH")
    pythonpath = (
        str(src_path)
        if not existing_pythonpath
        else os.pathsep.join([str(src_path), existing_pythonpath])
    )

    result = subprocess.run(
        [sys.executable, "-m", "ai_rules.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
        env={**os.environ, "PYTHONPATH": pythonpath},
        timeout=10,
    )

    assert result.returncode == 0
    assert "Usage:" in result.stdout
    assert "install" in result.stdout
