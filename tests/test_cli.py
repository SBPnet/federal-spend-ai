"""CLI smoke tests."""

from unittest.mock import patch

from click.testing import CliRunner

from federalspendai.cli import cli


def test_cli_ingest_dry_run():
    runner = CliRunner()
    result = runner.invoke(cli, ["ingest", "--dry-run", "--datasets", "awards"])
    assert result.exit_code == 0
    assert "dry-run" in result.output or "Would" in result.output


def test_cli_analyze_requires_input():
    runner = CliRunner()
    result = runner.invoke(cli, ["analyze"])
    assert result.exit_code == 1
    assert "reference-number" in result.output or "text" in result.output


def test_cli_analyze_text_json():
    runner = CliRunner()
    with patch("federalspendai.tools.nlp.analyze_contract_text") as mock_analyze:
        mock_analyze.return_value = {
            "_meta": {},
            "data": {
                "summary": "test",
                "model": "spacy",
                "entities": [],
                "risk_flags": [{"code": "X", "message": "m", "severity": "info"}],
            },
        }
        result = runner.invoke(cli, ["analyze", "--text", "sole source contract", "--json"])
    assert result.exit_code == 0
    assert "summary" in result.output


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "ingest" in result.output
