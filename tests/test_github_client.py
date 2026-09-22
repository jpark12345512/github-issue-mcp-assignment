from __future__ import annotations

import httpx
import pytest

from github_issue_mcp.github_client import GitHubClient, GitHubClientError


@pytest.mark.anyio
async def test_list_issues_filters_pull_requests() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/repos/octocat/demo/issues"
        assert request.headers["authorization"] == "Bearer test-token"
        return httpx.Response(
            200,
            json=[
                {
                    "number": 1,
                    "title": "A real issue",
                    "state": "open",
                    "html_url": "https://github.com/octocat/demo/issues/1",
                    "labels": [{"name": "bug"}],
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-02T00:00:00Z",
                },
                {
                    "number": 2,
                    "title": "A pull request",
                    "pull_request": {"url": "https://api.github.com/pulls/2"},
                },
            ],
        )

    transport = httpx.MockTransport(handler)
    async with GitHubClient("test-token", transport=transport) as client:
        issues = await client.list_issues(owner="octocat", repo="demo", state="open", limit=10)

    assert [issue["number"] for issue in issues] == [1]
    assert issues[0]["labels"] == ["bug"]


@pytest.mark.anyio
async def test_error_response_does_not_disclose_token_or_body() -> None:
    secret = "github_pat_SUPER_SECRET_VALUE"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": f"Bad credentials: {secret}"})

    transport = httpx.MockTransport(handler)
    async with GitHubClient(secret, transport=transport) as client:
        with pytest.raises(GitHubClientError) as error:
            await client.list_issues(owner="octocat", repo="demo", state="open", limit=10)

    public_error = str(error.value)
    assert secret not in public_error
    assert "Bad credentials" not in public_error
    assert public_error == "GitHub authentication failed. Check GITHUB_TOKEN in .env."

