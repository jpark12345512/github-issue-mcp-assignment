"""Small, typed wrapper around the GitHub Issues REST API."""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Any, Self

import httpx

logger = logging.getLogger(__name__)

GITHUB_API_BASE = "https://api.github.com"


class GitHubClientError(RuntimeError):
    """A deliberately sanitized error that is safe to return to an MCP client."""


class GitHubClient:
    """Async GitHub client with least-privilege token authentication."""

    def __init__(
        self,
        token: str,
        *,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        # Endpoint shapes and recommended headers follow GitHub's official REST docs:
        # https://docs.github.com/en/rest/issues/issues
        self._client = httpx.AsyncClient(
            base_url=GITHUB_API_BASE,
            headers={
                "Accept": "application/vnd.github+json",
                "Authorization": f"Bearer {token}",
                "User-Agent": "github-issue-mcp/1.0",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=httpx.Timeout(15.0),
            transport=transport,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self._client.aclose()

    async def _request(self, method: str, endpoint: str, **kwargs: Any) -> Any:
        try:
            response = await self._client.request(method, endpoint, **kwargs)
        except httpx.TimeoutException as exc:
            logger.warning("GitHub request timed out; exception_type=%s", type(exc).__name__)
            raise GitHubClientError("GitHub did not respond in time. Try again later.") from None
        except httpx.RequestError as exc:
            logger.warning("GitHub request failed; exception_type=%s", type(exc).__name__)
            raise GitHubClientError(
                "Could not connect to GitHub. Check the network and try again."
            ) from None

        if response.is_error:
            # Do not return response bodies, request headers, tokens, or tracebacks to the model.
            logger.warning("GitHub returned an error; status=%s", response.status_code)
            public_messages = {
                401: "GitHub authentication failed. Check GITHUB_TOKEN in .env.",
                403: "GitHub denied the request. Check token permissions or GitHub rate limits.",
                404: "Repository not found or the token does not have access.",
                422: "GitHub rejected the supplied issue data.",
                429: "GitHub rate limit exceeded. Try again later.",
            }
            message = public_messages.get(response.status_code)
            if message is None and response.status_code >= 500:
                message = "GitHub is temporarily unavailable. Try again later."
            if message is None:
                message = "GitHub could not complete the request."
            raise GitHubClientError(message)

        try:
            return response.json()
        except ValueError:
            logger.warning("GitHub returned non-JSON success response")
            raise GitHubClientError("GitHub returned an unexpected response.") from None

    async def list_issues(
        self,
        *,
        owner: str,
        repo: str,
        state: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        payload = await self._request(
            "GET",
            f"/repos/{owner}/{repo}/issues",
            params={"state": state, "per_page": limit, "sort": "updated", "direction": "desc"},
        )
        if not isinstance(payload, list):
            raise GitHubClientError("GitHub returned an unexpected issue list.")

        # GitHub's issues endpoint also returns pull requests; omit those here.
        issues = []
        for item in payload:
            if not isinstance(item, dict) or "pull_request" in item:
                continue
            issues.append(
                {
                    "number": item.get("number"),
                    "title": item.get("title"),
                    "state": item.get("state"),
                    "url": item.get("html_url"),
                    "labels": [
                        label.get("name")
                        for label in item.get("labels", [])
                        if isinstance(label, dict) and label.get("name")
                    ],
                    "created_at": item.get("created_at"),
                    "updated_at": item.get("updated_at"),
                }
            )
        return issues

    async def create_issue(
        self,
        *,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: list[str],
    ) -> dict[str, Any]:
        payload = await self._request(
            "POST",
            f"/repos/{owner}/{repo}/issues",
            json={"title": title, "body": body, "labels": labels},
        )
        if not isinstance(payload, dict):
            raise GitHubClientError("GitHub returned an unexpected create-issue response.")
        return {
            "number": payload.get("number"),
            "title": payload.get("title"),
            "state": payload.get("state"),
            "url": payload.get("html_url"),
        }
