from __future__ import annotations

import pytest
from mcp import Client

from github_issue_mcp.server import mcp, reset_rate_limits


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(autouse=True)
def _reset_rate_limits() -> None:
    reset_rate_limits()


@pytest.mark.anyio
async def test_create_issue_defaults_to_non_mutating_preview() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool(
            "create_repository_issue",
            {
                "owner": "octocat",
                "repo": "demo",
                "title": "Login button is unresponsive",
                "body": "Steps to reproduce:\n1. Open login\n2. Click the button",
                "labels": ["bug"],
            },
        )

    assert result.is_error is False
    assert result.structured_content is not None
    assert result.structured_content["status"] == "preview"
    assert result.structured_content["issue"]["repository"] == "octocat/demo"


@pytest.mark.anyio
async def test_injection_is_reported_as_tool_error() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.call_tool(
            "create_repository_issue",
            {
                "owner": "octocat",
                "repo": "../../etc/passwd",
                "title": "Malicious input",
            },
        )

    assert result.is_error is True
    assert "Invalid input" in result.content[0].text


@pytest.mark.anyio
async def test_triage_prompt_contains_safe_workflow() -> None:
    async with Client(mcp, raise_exceptions=True) as client:
        result = await client.get_prompt(
            "triage_bug_report",
            {
                "owner": "octocat",
                "repo": "demo",
                "report": "The login button does nothing after it is clicked.",
            },
        )

    rendered = result.messages[0].content.text
    assert "confirm=false" in rendered
    assert "explicit confirmation" in rendered
    assert "untrusted report data" in rendered

