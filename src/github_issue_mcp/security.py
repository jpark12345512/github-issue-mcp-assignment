"""Input validation and process-local rate limiting for MCP tools."""

from __future__ import annotations

import math
import re
import threading
import time
import unicodedata
from collections import defaultdict, deque
from collections.abc import Callable, Iterable


class InputValidationError(ValueError):
    """Raised when untrusted tool input violates the allow-list policy."""


class RateLimitExceeded(RuntimeError):
    """Raised when a tool exceeds its local sliding-window limit."""

    def __init__(self, retry_after_seconds: int) -> None:
        self.retry_after_seconds = retry_after_seconds
        super().__init__(f"Rate limit exceeded. Retry in {retry_after_seconds} seconds.")


_OWNER_PATTERN = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?")
_REPOSITORY_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,100}")


def _normalise(value: str) -> str:
    return unicodedata.normalize("NFKC", value).strip()


def _has_control_characters(value: str, *, allow_newline_and_tab: bool) -> bool:
    permitted = {"\n", "\t"} if allow_newline_and_tab else set()
    return any(
        character not in permitted and unicodedata.category(character) == "Cc"
        for character in value
    )


def validate_owner(owner: str) -> str:
    """Validate a GitHub user or organization name using a strict allow-list."""
    clean = _normalise(owner)
    if not _OWNER_PATTERN.fullmatch(clean) or "--" in clean:
        raise InputValidationError(
            "owner must be 1-39 letters, digits, or single hyphens and cannot start "
            "or end with a hyphen."
        )
    return clean


def validate_repository(repo: str) -> str:
    """Validate a repository slug and reject path separators/traversal."""
    clean = _normalise(repo)
    if clean in {".", ".."} or not _REPOSITORY_PATTERN.fullmatch(clean):
        raise InputValidationError(
            "repo must be 1-100 letters, digits, dots, underscores, or hyphens; "
            "paths are not allowed."
        )
    if clean.lower().endswith(".git"):
        raise InputValidationError("repo must not include the .git suffix.")
    return clean


def validate_title(title: str) -> str:
    """Validate and normalize an issue title."""
    clean = _normalise(title)
    if not 1 <= len(clean) <= 256:
        raise InputValidationError("title must contain 1-256 characters.")
    if _has_control_characters(clean, allow_newline_and_tab=False):
        raise InputValidationError("title cannot contain control characters or line breaks.")
    return clean


def validate_body(body: str, *, maximum_length: int = 20_000) -> str:
    """Validate free-form Markdown while retaining ordinary newlines and tabs."""
    clean = unicodedata.normalize("NFKC", body).strip()
    if len(clean) > maximum_length:
        raise InputValidationError(f"body must not exceed {maximum_length} characters.")
    if _has_control_characters(clean, allow_newline_and_tab=True):
        raise InputValidationError("body contains unsupported control characters.")
    return clean


def validate_labels(labels: Iterable[str] | None) -> list[str]:
    """Validate issue labels without changing their user-visible spelling."""
    if labels is None:
        return []
    clean_labels = []
    for label in labels:
        clean = _normalise(label)
        if not 1 <= len(clean) <= 50:
            raise InputValidationError("each label must contain 1-50 characters.")
        if _has_control_characters(clean, allow_newline_and_tab=False):
            raise InputValidationError("labels cannot contain control characters.")
        clean_labels.append(clean)
    if len(clean_labels) > 10:
        raise InputValidationError("no more than 10 labels may be supplied.")
    return clean_labels


def validate_limit(limit: int) -> int:
    """Keep list responses small enough for an LLM context window."""
    if not 1 <= limit <= 50:
        raise InputValidationError("limit must be between 1 and 50.")
    return limit


class SlidingWindowRateLimiter:
    """A thread-safe, in-memory sliding-window limiter keyed by tool name."""

    def __init__(
        self,
        *,
        max_calls: int,
        window_seconds: int,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if max_calls <= 0 or window_seconds <= 0:
            raise ValueError("max_calls and window_seconds must be positive.")
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._clock = clock
        self._calls: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str) -> None:
        """Record one call, or raise RateLimitExceeded if the window is full."""
        now = self._clock()
        cutoff = now - self.window_seconds
        with self._lock:
            calls = self._calls[key]
            while calls and calls[0] <= cutoff:
                calls.popleft()
            if len(calls) >= self.max_calls:
                retry_after = max(1, math.ceil(calls[0] + self.window_seconds - now))
                raise RateLimitExceeded(retry_after)
            calls.append(now)

    def reset(self) -> None:
        """Clear all windows. Used by isolated tests and local demonstrations."""
        with self._lock:
            self._calls.clear()
