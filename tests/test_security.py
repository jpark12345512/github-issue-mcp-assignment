from __future__ import annotations

import pytest

from github_issue_mcp.security import (
    InputValidationError,
    RateLimitExceeded,
    SlidingWindowRateLimiter,
    validate_repository,
    validate_title,
)


@pytest.mark.parametrize(
    "malicious_repo",
    ["../../etc/passwd", "owner/repo", "repo\nX-Injected: yes", ".."],
)
def test_repository_injection_attempts_are_blocked(malicious_repo: str) -> None:
    with pytest.raises(InputValidationError):
        validate_repository(malicious_repo)


def test_title_header_injection_attempt_is_blocked() -> None:
    with pytest.raises(InputValidationError):
        validate_title("Bug title\r\nX-Injected: yes")


def test_rate_limit_exploit_is_blocked() -> None:
    now = 100.0
    limiter = SlidingWindowRateLimiter(
        max_calls=3,
        window_seconds=60,
        clock=lambda: now,
    )

    limiter.check("tool")
    limiter.check("tool")
    limiter.check("tool")

    with pytest.raises(RateLimitExceeded) as error:
        limiter.check("tool")
    assert error.value.retry_after_seconds == 60


def test_rate_limit_window_reopens() -> None:
    times = iter([100.0, 101.0, 161.0])
    limiter = SlidingWindowRateLimiter(
        max_calls=2,
        window_seconds=60,
        clock=lambda: next(times),
    )
    limiter.check("tool")
    limiter.check("tool")
    limiter.check("tool")

