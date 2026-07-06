"""CLI smoke tests."""

from click.testing import CliRunner

from federalspendai.cli import cli


def test_cli_ingest_dry_run():
    runner = CliRunner()
    result = runner.invoke(cli, ["ingest", "--dry-run", "--datasets", "awards"])
    assert result.exit_code == 0
    assert "dry-run" in result.output or "Would" in result.output


def test_cli_analyze_stub():
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze"])
    assert result.exit_code == 0


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "ingest" in result.output
