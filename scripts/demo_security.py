"""Offline demonstration of the two required security best practices."""

from github_issue_mcp.security import (
    InputValidationError,
    RateLimitExceeded,
    SlidingWindowRateLimiter,
    validate_repository,
)


def demonstrate_input_sanitization() -> None:
    malicious_repo = "../../etc/passwd"
    print("[Exploit 1] Attempting path traversal through the repo argument")
    print(f"Input: {malicious_repo!r}")
    try:
        validate_repository(malicious_repo)
    except InputValidationError as exc:
        print(f"BLOCKED: {exc}")
    else:
        raise AssertionError("The malicious repository input was not blocked.")


def demonstrate_rate_limiting() -> None:
    print("\n[Exploit 2] Sending four calls into a three-call window")
    limiter = SlidingWindowRateLimiter(max_calls=3, window_seconds=60)
    for call_number in range(1, 5):
        try:
            limiter.check("demo_tool")
        except RateLimitExceeded as exc:
            print(f"Call {call_number}: BLOCKED ({exc})")
        else:
            print(f"Call {call_number}: allowed")


if __name__ == "__main__":
    demonstrate_input_sanitization()
    demonstrate_rate_limiting()

