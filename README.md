# GitHub Issue MCP Server

A local Python MCP server in the **Development Workflow** domain. It connects an MCP host such as Claude Desktop to the GitHub Issues REST API.

The server exposes:

1. `list_repository_issues` — list recently updated issues while excluding pull requests.
2. `create_repository_issue` — preview an issue by default and create it only when `confirm=true`.
3. `triage_bug_report` — a reusable prompt that checks for duplicates, prepares a preview, and asks for confirmation before creation.

## Rubric mapping

| Requirement | Implementation |
|---|---|
| Python virtual environment | Managed by `uv` in `.venv` |
| Authentication | Fine-grained GitHub personal access token in a local `.env` file |
| Secret management | `.env` is loaded from a `pathlib.Path` and excluded by `.gitignore` |
| Two tools and a prompt | Implemented in `src/github_issue_mcp/server.py` |
| Best practice 1 | Input sanitization with strict repository-coordinate validation and bounded text inputs |
| Best practice 2 | Thread-safe process-local sliding-window rate limiting |
| Exploit demonstrations | `scripts/demo_security.py` and `tests/test_security.py` |
| Error disclosure | API bodies, authorization headers, tokens, and tracebacks are not returned to tool callers |
| Claude Desktop config | macOS/Linux and Windows JSON examples are included |

The Canvas-only table, architecture diagram, and reflection are intentionally not stored in this repository, as required by the assignment.

## Prerequisites

- Python 3.11 or newer
- `uv`
- Git
- Claude Desktop
- A private GitHub repository in which Issues are enabled

Install `uv` if necessary:

macOS/Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Restart the terminal after installation.

## 1. Install the project

Open this folder in VS Code, then open **Terminal → New Terminal**.

```bash
uv sync --dev
```

This creates `.venv`, installs the server dependencies, installs the test tools, and uses `uv.lock` for repeatable versions.

If the VS Code Python extension does not select the environment automatically:

1. Open the Command Palette.
2. Run **Python: Select Interpreter**.
3. Select `.venv/bin/python` on macOS/Linux or `.venv\Scripts\python.exe` on Windows.

The required `requirements.txt` is also included. A non-`uv` installation can use:

```bash
python -m venv .venv
```

macOS/Linux activation:

```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
```

Windows PowerShell activation:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

## 2. Create a least-privilege GitHub token

Use a **fine-grained personal access token**, not a classic token when possible.

1. In GitHub, open your profile menu and select **Settings**.
2. Select **Developer settings**.
3. Select **Personal access tokens → Fine-grained tokens**.
4. Select **Generate new token**.
5. Give it a short expiration and a descriptive name such as `github-issue-mcp-class`.
6. Under **Repository access**, choose **Only select repositories**.
7. Select only the private repository used for this assignment.
8. Under **Repository permissions**, set **Issues** to **Read and write**. Metadata read access is added automatically.
9. Generate and immediately copy the token. GitHub displays it only once.

GitHub documents that listing repository issues requires Issues read permission and creating an issue requires Issues write permission.

## 3. Configure the secret

Create `.env` from the safe example.

macOS/Linux:

```bash
cp .env.example .env
chmod 600 .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Open `.env` and replace only the placeholder value:

```dotenv
GITHUB_TOKEN=github_pat_your_real_token_here
RATE_LIMIT_MAX_CALLS=5
RATE_LIMIT_WINDOW_SECONDS=60
```

Do not put the token in a source file, Claude Desktop JSON file, command, screenshot, commit, or submitted report. The server uses `pathlib.Path` to find the project-local `.env`, so it does not depend on the working directory or a system environment variable.

Verify that Git will ignore the file:

```bash
git check-ignore .env
```

Expected output:

```text
.env
```

## 4. Run quality and exploit checks

Run the complete test suite:

```bash
uv run pytest -v
```

Run style checks:

```bash
uv run ruff check .
```

Run the offline exploit demonstration:

```bash
uv run python scripts/demo_security.py
```

Expected result:

```text
[Exploit 1] Attempting path traversal through the repo argument
Input: '../../etc/passwd'
BLOCKED: repo must be 1-100 letters, digits, dots, underscores, or hyphens; paths are not allowed.

[Exploit 2] Sending four calls into a three-call window
Call 1: allowed
Call 2: allowed
Call 3: allowed
Call 4: BLOCKED (Rate limit exceeded. Retry in 60 seconds.)
```

## 5. Test with MCP Inspector

Start the official MCP Inspector:

```bash
uv run mcp dev src/github_issue_mcp/server.py
```

Open the local URL printed in the terminal.

### Test `list_repository_issues`

Use:

- `owner`: your GitHub username or organization
- `repo`: the repository name only
- `state`: `open`
- `limit`: `5`

The result should have `status: "ok"` and an `issues` list.

### Test safe issue preview

Call `create_repository_issue` with:

- your owner and repository
- `title`: `MCP assignment demo issue`
- `body`: `Created during the MCP server demo.`
- `labels`: `[]`
- `confirm`: `false`

The result should have `status: "preview"`. Check GitHub: no issue should exist.

After reviewing the preview, call it once with `confirm: true`. The result should have `status: "created"` and a GitHub URL.

### Test the prompt

Open the Inspector's Prompts section and render `triage_bug_report` with a short bug report. Confirm that its workflow:

- searches for duplicates;
- creates a non-mutating preview first;
- requires explicit confirmation before writing.

Stop the Inspector with `Ctrl+C`.

## 6. Verify the stdio server

Run:

```bash
uv run github-issue-mcp
```

The command should remain running without printing normal output. This is expected: a stdio MCP server waits for a host to send JSON-RPC messages. Stop it with `Ctrl+C`.

Never add `print()` calls to the server. Standard output carries the MCP protocol. Application logging uses standard error instead.

## 7. Configure Claude Desktop

First obtain absolute paths.

macOS/Linux:

```bash
which uv
pwd
```

Windows PowerShell:

```powershell
(Get-Command uv).Source
(Get-Location).Path
```

Open the Claude Desktop configuration file:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

Use `claude_desktop_config.example.json` for macOS or `claude_desktop_config.windows.example.json` for Windows. Replace both placeholders with the exact absolute paths printed above.

macOS example:

```json
{
  "mcpServers": {
    "github-issue-mcp": {
      "command": "/Users/YOUR_NAME/.local/bin/uv",
      "args": [
        "--directory",
        "/Users/YOUR_NAME/Projects/github-issue-mcp",
        "run",
        "--frozen",
        "github-issue-mcp"
      ]
    }
  }
}
```

Windows JSON paths must use doubled backslashes:

```json
{
  "mcpServers": {
    "github-issue-mcp": {
      "command": "C:\\Users\\YOUR_NAME\\.local\\bin\\uv.exe",
      "args": [
        "--directory",
        "C:\\Users\\YOUR_NAME\\Projects\\github-issue-mcp",
        "run",
        "--frozen",
        "github-issue-mcp"
      ]
    }
  }
}
```

If the existing file already contains other servers, add only the `github-issue-mcp` entry inside its existing `mcpServers` object. Do not create a second `mcpServers` key.

Fully quit Claude Desktop, including its menu-bar or system-tray process, and reopen it. Confirm that `list_repository_issues` and `create_repository_issue` are available.

Suggested Claude test message:

```text
Use list_repository_issues to show the five most recently updated open issues in OWNER/REPO.
```

Suggested safe-write test:

```text
Prepare an issue titled "Claude Desktop MCP demo" in OWNER/REPO with body "Preview test". Show me the preview but do not create it.
```

Claude should request tool approval. The returned status must be `preview`, and GitHub must remain unchanged.

## 8. Demonstrate the two required defenses

### Input sanitization exploit

In MCP Inspector, call either tool with this repository value:

```text
../../etc/passwd
```

Expected: the tool returns an error beginning with `Invalid input`. No GitHub request is sent. The repository and owner are inserted into a URL path only after strict allow-list validation.

### Rate-limit exploit

For a quick live demonstration, temporarily use these values in `.env`:

```dotenv
RATE_LIMIT_MAX_CALLS=3
RATE_LIMIT_WINDOW_SECONDS=60
```

Restart the Inspector or Claude Desktop, because limits are loaded at process start. Call `create_repository_issue` four times with `confirm=false`. The first three calls return previews and create nothing. The fourth returns a rate-limit error with a retry time.

Restore the default values after the demonstration if desired.

## 9. Create and submit the private GitHub repository

Before the first commit, replace `YOUR NAME` in `pyproject.toml` and `LICENSE`.

```bash
git init
git add .
git status
```

Carefully verify that `.env` is **not** listed. Then commit:

```bash
git commit -m "Build secure GitHub issue MCP server"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_PRIVATE_REPOSITORY.git
git push -u origin main
```

On GitHub, confirm the repository is private and invite the instructor and TA under **Settings → Collaborators** using the addresses specified in the assignment.

## Security design

### Input sanitization

- Owner and repository names use allow-list regular expressions.
- Path separators, path traversal, control characters, and `.git` suffixes are rejected.
- Titles, bodies, labels, list sizes, and label counts have explicit bounds.
- User text is serialized as JSON by `httpx`; it is never interpolated into a shell command or SQL statement.

### Rate limiting

- A thread-safe sliding window is maintained independently for each tool.
- Defaults are five calls per 60 seconds.
- Rejected calls receive an actionable retry time.
- The limiter is process-local and resets when the server restarts. A shared datastore such as Redis would be needed for multiple server processes.

### Additional error-disclosure protection

- The GitHub response body is never copied into a tool error.
- Authorization headers and tokens are never logged.
- Expected failures become short `ToolError` messages.
- Unexpected failures reveal only a generic error and exception type in local logs.

## Project structure

```text
github-issue-mcp/
├── src/github_issue_mcp/
│   ├── config.py          # pathlib + .env configuration
│   ├── github_client.py   # GitHub REST client and safe API errors
│   ├── security.py        # validation and sliding-window limiter
│   └── server.py          # two MCP tools, prompt, stdio entry point
├── tests/                 # functional and exploit tests
├── scripts/
│   └── demo_security.py   # offline exploit demonstration
├── .env.example
├── claude_desktop_config.example.json
├── claude_desktop_config.windows.example.json
├── pyproject.toml
├── requirements.txt
└── README.md
```

## Troubleshooting

### `GitHub authentication is not configured`

Confirm that the file is named exactly `.env`, is in the project root, and contains a real `GITHUB_TOKEN` value rather than the placeholder.

### `Repository not found or the token does not have access`

Check owner/repository spelling, the token's selected repository, and that the token is approved if an organization requires approval.

### Server does not appear in Claude Desktop

1. Run `uv run github-issue-mcp` first; it should wait silently.
2. Confirm that both paths in the JSON are absolute.
3. Validate the JSON syntax.
4. Fully quit and reopen Claude Desktop.
5. Inspect `mcp-server-GitHub Issue Assistant.log` or the similarly named server log in:
   - macOS: `~/Library/Logs/Claude`
   - Windows: `%APPDATA%\Claude\logs`

### Tool suddenly returns a local rate-limit error

Wait for the configured window or restart the server during development. Do not use restart as a production bypass; this limiter is intentionally documented as process-local.

## Code attribution and references

The implementation is original except for the conventional SDK registration and startup pattern noted in source comments. References consulted:

- [MCP Python SDK v2: first server](https://py.sdk.modelcontextprotocol.io/get-started/first-steps/)
- [MCP Python SDK v2: prompts](https://py.sdk.modelcontextprotocol.io/servers/prompts/)
- [MCP Python SDK v2: testing](https://py.sdk.modelcontextprotocol.io/get-started/testing/)
- [MCP Python SDK v2: error handling](https://py.sdk.modelcontextprotocol.io/servers/handling-errors/)
- [GitHub REST API: issues](https://docs.github.com/en/rest/issues/issues)
- [GitHub: managing fine-grained personal access tokens](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)

