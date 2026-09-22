# GitHub Issue MCP 과제 따라하기

이 문서는 완성된 프로젝트를 내려받은 뒤 VS Code, GitHub, MCP Inspector, Claude Desktop 순서로 직접 실행하는 절차입니다. 명령은 한 줄씩 실행하고, 각 단계의 확인 결과를 본 다음 다음 단계로 이동하세요.

## 최종 결과

완료하면 다음 기능을 시연할 수 있습니다.

- Claude Desktop이 로컬 Python MCP 서버를 실행합니다.
- `list_repository_issues`가 GitHub 이슈를 조회합니다.
- `create_repository_issue`가 기본적으로 미리보기만 반환합니다.
- `confirm=true`일 때만 이슈를 실제 생성합니다.
- `triage_bug_report` 프롬프트가 중복 검색 → 초안 → 확인 → 생성 순서를 안내합니다.
- 경로 조작 입력이 차단됩니다.
- 설정된 횟수를 초과한 호출이 차단됩니다.

## 0단계: 필요한 프로그램 확인

다음 프로그램이 필요합니다.

1. VS Code
2. Git
3. Claude Desktop
4. GitHub 계정
5. `uv`

VS Code를 열고 **Terminal → New Terminal**을 선택한 뒤 확인합니다.

```bash
git --version
uv --version
```

`uv`를 찾을 수 없으면 설치합니다.

macOS/Linux:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

설치 후 VS Code와 터미널을 완전히 닫았다가 다시 엽니다.

## 1단계: 폴더 열기

1. 프로젝트 ZIP 압축을 풉니다.
2. VS Code에서 **File → Open Folder**를 선택합니다.
3. 압축을 푼 `github-issue-mcp` 폴더를 선택합니다.
4. VS Code에서 **Terminal → New Terminal**을 선택합니다.
5. 터미널 위치가 프로젝트 루트인지 확인합니다.

macOS/Linux:

```bash
pwd
ls
```

Windows PowerShell:

```powershell
(Get-Location).Path
Get-ChildItem
```

출력에 `README.md`, `pyproject.toml`, `requirements.txt`, `src`, `tests`가 보여야 합니다.

## 2단계: 가상환경과 패키지 설치

다음을 실행합니다.

```bash
uv sync --dev
```

완료되면 `.venv` 가상환경과 `uv.lock`의 고정 버전에 맞는 패키지가 준비됩니다.

VS Code 왼쪽 아래의 Python 버전을 선택하거나 Command Palette에서 **Python: Select Interpreter**를 실행합니다.

- macOS/Linux: `.venv/bin/python`
- Windows: `.venv\Scripts\python.exe`

확인 명령:

```bash
uv run python --version
uv run python -c "import mcp; print('MCP import OK')"
```

## 3단계: 과제용 비공개 GitHub 저장소 만들기

1. GitHub에서 오른쪽 위 `+` → **New repository**를 선택합니다.
2. 이름을 예를 들어 `github-issue-mcp-assignment`로 정합니다.
3. 반드시 **Private**를 선택합니다.
4. README, `.gitignore`, license 자동 생성은 선택하지 않습니다. 로컬 프로젝트에 이미 있습니다.
5. **Create repository**를 선택합니다.
6. 생성된 저장소의 HTTPS URL을 메모합니다.
7. 저장소의 **Settings → General → Features**에서 Issues가 활성화되어 있는지 확인합니다.

## 4단계: GitHub 토큰 만들기

토큰은 이 MCP 서버가 실제 GitHub API를 호출할 때 쓰는 인증 정보입니다.

1. GitHub 오른쪽 위 프로필 사진 → **Settings**를 선택합니다.
2. 왼쪽 아래 **Developer settings**를 선택합니다.
3. **Personal access tokens → Fine-grained tokens**를 선택합니다.
4. **Generate new token**을 선택합니다.
5. Token name에 `github-issue-mcp-class` 같은 이름을 입력합니다.
6. Expiration은 과제 마감 뒤의 짧은 기간으로 설정합니다.
7. Resource owner에 본인 계정을 선택합니다.
8. Repository access에서 **Only select repositories**를 선택합니다.
9. 방금 만든 과제 저장소 하나만 선택합니다.
10. Repository permissions에서 **Issues: Read and write**를 선택합니다.
11. **Generate token**을 누릅니다.
12. 나타난 토큰을 즉시 복사합니다. 이 값을 채팅이나 스크린샷에 넣지 마세요.

## 5단계: `.env`에 토큰 저장

VS Code 터미널에서 실행합니다.

macOS/Linux:

```bash
cp .env.example .env
chmod 600 .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

VS Code 탐색기에서 `.env`를 열고 다음처럼 편집합니다.

```dotenv
GITHUB_TOKEN=여기에_복사한_실제_토큰
RATE_LIMIT_MAX_CALLS=5
RATE_LIMIT_WINDOW_SECONDS=60
```

따옴표를 추가할 필요는 없습니다. 파일을 저장합니다.

비밀 파일이 Git에서 제외되는지 확인합니다.

```bash
git check-ignore .env
```

`.env`가 출력되어야 합니다. 아무것도 출력되지 않으면 커밋하지 말고 `.gitignore`부터 확인하세요.

## 6단계: 테스트 실행

전체 테스트:

```bash
uv run pytest -v
```

예상 결과의 핵심은 모든 테스트가 `PASSED`이고 마지막에 실패가 없는 것입니다.

코드 스타일 검사:

```bash
uv run ruff check .
```

예상 결과:

```text
All checks passed!
```

## 7단계: 두 공격 차단 시연

다음 명령은 GitHub 토큰이나 네트워크를 사용하지 않습니다.

```bash
uv run python scripts/demo_security.py
```

첫 번째 시연은 `../../etc/passwd`를 저장소 이름으로 넣는 경로 조작 공격입니다. `/`가 허용 목록에 없으므로 API 요청 전에 차단됩니다.

두 번째 시연은 60초 동안 최대 세 번만 허용된 작업을 네 번 호출합니다. 네 번째 호출이 `BLOCKED`로 나와야 합니다.

발표할 때는 다음처럼 설명하면 됩니다.

> 첫 번째 방어는 사용자 입력을 그대로 URL 경로에 넣지 않고 허용 문자와 길이를 먼저 검증합니다. 두 번째 방어는 도구별 호출 시간을 기록하는 sliding-window rate limiter로 과도한 요청을 막습니다.

## 8단계: MCP Inspector에서 기능 확인

실행:

```bash
uv run mcp dev src/github_issue_mcp/server.py
```

터미널에 표시된 로컬 주소를 브라우저에서 엽니다. Inspector 연결 화면이 나오면 서버에 연결합니다.

### 이슈 조회 도구

Tools에서 `list_repository_issues`를 선택합니다.

- owner: 본인의 GitHub 사용자 이름
- repo: 과제 저장소 이름만 입력
- state: `open`
- limit: `5`

실행 결과에 다음이 있으면 정상입니다.

- `status`: `ok`
- `repository`: `사용자명/저장소명`
- `issues`: 목록

처음에는 이슈가 없어서 빈 목록이어도 정상입니다.

### 안전한 미리보기

Tools에서 `create_repository_issue`를 선택합니다.

- owner: 본인의 사용자 이름
- repo: 과제 저장소 이름
- title: `MCP assignment demo issue`
- body: `Created during the MCP server demo.`
- labels: 빈 배열 `[]`
- confirm: `false`

결과의 `status`가 `preview`여야 합니다. GitHub 저장소를 새로고침해도 이슈가 만들어지지 않아야 합니다.

같은 값을 사용해 `confirm`만 `true`로 바꾸어 한 번 실행합니다. `status`가 `created`이고 URL이 반환되어야 합니다. GitHub Issues 탭에서 이슈가 실제 생성됐는지 확인합니다.

### 프롬프트

Prompts에서 `triage_bug_report`를 선택합니다.

- owner와 repo를 입력합니다.
- report에 `로그인 버튼을 클릭해도 아무 반응이 없다` 같은 내용을 입력합니다.

렌더링 결과에 다음 절차가 포함되어야 합니다.

1. 기존 이슈 검색
2. 중복 여부 판단
3. `confirm=false` 미리보기
4. 사용자 확인
5. 확인 뒤 `confirm=true` 생성

완료 후 터미널에서 `Ctrl+C`를 누릅니다.

## 9단계: Claude Desktop 설정에 필요한 경로 확인

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

두 결과를 메모합니다.

## 10단계: Claude Desktop 설정

Claude Desktop을 한 번 이상 실행한 상태여야 설정 폴더가 존재합니다.

설정 파일 위치:

- macOS: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Windows: `%APPDATA%\Claude\claude_desktop_config.json`

### macOS에서 설정 파일 열기

```bash
code ~/Library/Application\ Support/Claude/claude_desktop_config.json
```

### Windows PowerShell에서 설정 파일 열기

```powershell
code $env:APPDATA\Claude\claude_desktop_config.json
```

파일이 비어 있거나 없으면 다음 구조를 붙여 넣습니다. 플레이스홀더 두 곳을 9단계에서 확인한 실제 절대 경로로 교체합니다.

```json
{
  "mcpServers": {
    "github-issue-mcp": {
      "command": "/실제/절대/경로/uv",
      "args": [
        "--directory",
        "/실제/절대/경로/github-issue-mcp",
        "run",
        "--frozen",
        "github-issue-mcp"
      ]
    }
  }
}
```

Windows JSON에서는 `C:\Users\...`처럼 역슬래시를 두 번 써야 합니다. 저장소에 운영체제별 예제 파일이 있습니다.

기존 `mcpServers` 안에 다른 서버가 있으면 전체를 덮어쓰지 말고 `github-issue-mcp` 항목만 추가합니다. JSON 항목 사이의 쉼표도 확인하세요.

Claude Desktop 창만 닫지 말고 메뉴바 또는 시스템 트레이에서도 완전히 종료한 뒤 다시 실행합니다.

## 11단계: Claude Desktop에서 시연

새 대화에서 다음과 같이 요청합니다. `OWNER/REPO`는 실제 값으로 바꿉니다.

```text
list_repository_issues 도구를 사용해서 OWNER/REPO의 최근 open issue 5개를 보여줘.
```

Claude가 도구 실행 허용을 요청하면 내용을 확인하고 허용합니다.

쓰기 안전장치 시연:

```text
OWNER/REPO에 제목이 "Claude Desktop MCP demo"이고 본문이 "Preview test"인 이슈를 준비해줘. 아직 생성하지 말고 미리보기만 보여줘.
```

`preview` 결과와 함께 GitHub에는 아무 변화가 없는지 확인합니다. 그다음 실제 생성 여부를 묻는 Claude에게 승인하면 `confirm=true` 호출과 GitHub URL을 확인합니다.

## 12단계: Inspector에서 exploit 실시간 시연

### 입력 검증

도구의 repo에 다음 값을 넣습니다.

```text
../../etc/passwd
```

`Invalid input` 오류가 반환되어야 합니다.

### 호출 제한

`.env`에서 다음처럼 바꿉니다.

```dotenv
RATE_LIMIT_MAX_CALLS=3
RATE_LIMIT_WINDOW_SECONDS=60
```

서버를 다시 시작한 후 `create_repository_issue`를 `confirm=false`로 네 번 호출합니다. 처음 세 번은 미리보기, 네 번째는 `Local rate limit exceeded`가 되어야 합니다. `confirm=false`라 GitHub 이슈는 생성되지 않습니다.

## 13단계: 코드에서 반드시 설명할 수 있어야 하는 부분

- `config.py`: `pathlib.Path`로 프로젝트의 `.env`를 찾고 토큰을 읽습니다.
- `security.py`: 허용 목록 입력 검증과 sliding-window rate limiter가 있습니다.
- `github_client.py`: `Authorization: Bearer` 헤더로 GitHub REST API를 호출하고 민감한 오류 본문을 숨깁니다.
- `server.py`: 두 도구와 하나의 프롬프트를 MCP에 등록합니다.
- `confirm=False`: 쓰기 도구의 기본 동작을 미리보기로 만듭니다.
- `ToolError`: 모델이 수정하거나 사용자에게 설명할 수 있는 안전한 오류를 반환합니다.
- `mcp.run()`: Claude Desktop이 자식 프로세스로 실행하는 stdio 서버를 시작합니다.
- 서버 코드에 `print()`를 쓰지 않는 이유: stdout은 MCP JSON-RPC 통신에 사용되기 때문입니다.

## 14단계: 본인 정보와 코드 확인

다음 파일의 `YOUR NAME`을 본인 이름으로 바꿉니다.

- `pyproject.toml`
- `LICENSE`

README 전체와 소스 코드를 읽고 각 함수의 역할을 설명할 수 있는지 확인합니다. AI가 만든 내용을 이해하지 않은 채 제출하지 마세요.

## 15단계: Git 커밋과 push

```bash
git init
git add .
git status
```

`git status`에 `.env`가 없어야 합니다. 보이면 즉시 중단하고 `.gitignore`를 확인합니다.

```bash
git commit -m "Build secure GitHub issue MCP server"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
git push -u origin main
```

GitHub 저장소의 **Settings → Collaborators**에서 교수자와 TA에게 접근 권한을 부여합니다. 과제 안내에 TA 주소가 아직 정해지지 않았다면 공지를 확인해 나중에 추가합니다.

## 16단계: Canvas 자료 제출

저장소 밖에 제공된 Canvas 초안에서 다음을 본인 값과 실제 경험으로 수정합니다.

1. 표의 GitHub 링크
2. 아키텍처 다이어그램
3. 실제로 겪은 어려움
4. 도구 추상화 결정을 내린 이유
5. 한계와 개선 방향

Canvas 자료는 GitHub 저장소에 올리지 마세요.

## 발표 직전 체크리스트

- [ ] `.env`가 Git에 포함되지 않았다.
- [ ] 토큰은 선택한 저장소 하나에만 접근한다.
- [ ] `uv run pytest -v`가 통과한다.
- [ ] `uv run ruff check .`가 통과한다.
- [ ] Inspector에서 두 도구와 프롬프트가 보인다.
- [ ] Claude Desktop에서 서버가 연결된다.
- [ ] `confirm=false`가 GitHub를 변경하지 않는다.
- [ ] 잘못된 repo 입력이 차단된다.
- [ ] 네 번째 연속 호출이 차단된다.
- [ ] 저장소가 private이고 교수자/TA가 접근할 수 있다.
- [ ] Canvas 문서는 저장소 밖에서 제출한다.

