"""Performance benchmarks for ai-rules install command."""

import pytest

from click.testing import CliRunner

from ai_rules.cli import install


@pytest.mark.performance
class TestInstallPerformance:
    """Benchmarks for install command using pytest-benchmark."""

    def test_install_dry_run(self, benchmark):
        """Benchmark ai-rules install --dry-run execution time."""
        runner = CliRunner()

        result = benchmark(runner.invoke, install, ["--dry-run"])

        assert result.exit_code == 0

    def test_install_dry_run_with_rebuild_cache(self, benchmark):
        """Benchmark install with cache rebuild."""
        runner = CliRunner()

        result = benchmark(runner.invoke, install, ["--dry-run", "--rebuild-cache"])

        assert result.exit_code == 0
