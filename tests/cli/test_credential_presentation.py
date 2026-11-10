"""Credentials remain private in configuration and diagnostics."""

import logging
from io import StringIO

from typer.testing import CliRunner

from openfatture.cli.commands import config
from openfatture.platform.logging import SensitiveLogFilter, register_sensitive_values


def test_config_set_does_not_echo_credential(tmp_path, monkeypatch):
    key = "synthetic-secret-for-cli-test"
    monkeypatch.setenv("OPENFATTURE_CONFIG_DIR", str(tmp_path))
    result = CliRunner().invoke(config.app, ["set", "ai_api_key", key])
    assert result.exit_code == 0, result.stdout
    assert key not in result.stdout
    assert (
        not (tmp_path / "config.toml").exists() or key not in (tmp_path / "config.toml").read_text()
    )
    assert key in (tmp_path / "credentials.toml").read_text()


def test_standard_logging_masks_credentials_and_exception_text():
    key = "synthetic-secret-for-diagnostic-test"
    register_sensitive_values(key)
    output = StringIO()
    logger = logging.getLogger("credential-test")
    handler = logging.StreamHandler(output)
    handler.addFilter(SensitiveLogFilter())
    logger.addHandler(handler)
    logger.propagate = False
    try:
        try:
            raise ValueError(key)
        except ValueError:
            logger.error("Failed: %s", {"parameters": {"api_key": key}}, exc_info=True)
        assert key not in output.getvalue()
        assert "REDACTED" in output.getvalue()
    finally:
        logger.removeHandler(handler)
        logger.propagate = True


def test_json_output_is_not_wrapped_or_interpreted_as_markup():
    import json

    from rich.console import Console

    from openfatture.ai.domain.response import AgentResponse
    from openfatture.cli.formatters.utils import render_response

    output = StringIO()
    response = AgentResponse(content="[bold]literal[/bold] " + "long-text" * 100)
    render_response(response, "json", Console(file=output, width=20), show_metrics=False)
    parsed = json.loads(output.getvalue())
    assert parsed["content"] == response.content
