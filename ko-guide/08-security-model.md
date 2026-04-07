# 강좌 08: 보안 모델과 방어 체계

> **이 강좌에서 배우는 것**
>
> - AI 에이전트가 터미널 접근을 가질 때의 고유한 보안 위협
> - `approval.py`의 위험 명령어 감지 정규식 패턴과 승인 흐름
> - 프롬프트 인젝션 방어: 컨텍스트 파일 스캔과 스킬 가드
> - 비밀 유출 차단: 환경변수 블로킹, 출력 검열, 보호 디렉토리
> - 파일 시스템 쓰기 금지 목록과 심링크 공격 방지
> - Docker 컨테이너의 보안 하드닝 설정
> - 코드 실행 샌드박스의 격리 메커니즘
> - 크론 잡 인젝션 방어와 보안 체크리스트

---

## 1. Hermes의 보안 위협 모델

Hermes는 일반적인 웹 애플리케이션과 근본적으로 다른 보안 위협에 노출된다. LLM이 터미널, 파일 시스템, 웹 브라우저에 직접 접근할 수 있기 때문이다.

```
┌─────────────────────────────────────────────────────────┐
│                    위협 벡터 맵                           │
│                                                         │
│  ┌──────────────┐    ┌──────────────┐    ┌────────────┐ │
│  │ 사용자 입력   │    │ 웹 콘텐츠     │    │ 컨텍스트    │ │
│  │ (직접 요청)   │    │ (크롤링 결과)  │    │ 파일       │ │
│  └──────┬───────┘    └──────┬───────┘    └─────┬──────┘ │
│         │                   │                  │        │
│         ▼                   ▼                  ▼        │
│  ┌──────────────────────────────────────────────────┐   │
│  │              LLM (추론 엔진)                      │   │
│  │  프롬프트 인젝션에 의해 의도와 다른 행동 가능       │   │
│  └────────┬─────────────┬──────────────┬────────────┘   │
│           │             │              │                │
│     ┌─────▼─────┐ ┌────▼────┐  ┌──────▼──────┐        │
│     │ 터미널     │ │ 파일    │  │ 웹 브라우저  │        │
│     │ (rm -rf)  │ │ (쓰기)  │  │ (비밀 유출)  │        │
│     └───────────┘ └─────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────┘
```

Hermes가 방어하는 네 가지 핵심 위협:

| 위협 | 설명 | 공격 예시 |
|------|------|----------|
| **Shell Injection** | 위험한 셸 명령 실행 | `rm -rf /`, `dd if=/dev/zero of=/dev/sda` |
| **Prompt Injection** | 외부 텍스트가 LLM의 지시를 오버라이드 | 웹 페이지에 `ignore previous instructions` 삽입 |
| **비밀 유출** | API 키, 토큰이 LLM 응답이나 외부로 유출 | 스크립트가 `.env`를 읽어 출력 |
| **권한 상승** | 에이전트가 시스템 수준 권한을 획득 | `chmod 777`, `chown root`, `sudoers` 수정 |

---

## 2. 명령어 승인 시스템

`tools/approval.py`는 Hermes 보안의 첫 번째 방어선이다. 모든 터미널 명령은 실행 전에 이 모듈을 통과한다.

### 2.1 위험 명령어 감지 패턴

`DANGEROUS_PATTERNS` 리스트에 정의된 30+개의 정규식 패턴:

```python
DANGEROUS_PATTERNS = [
    # 파일 시스템 파괴
    (r'\brm\s+(-[^\s]*\s+)*/',          "delete in root path"),
    (r'\brm\s+-[^\s]*r',                "recursive delete"),
    (r'\bfind\b.*-exec\s+(/\S*/)?rm\b', "find -exec rm"),
    (r'\bfind\b.*-delete\b',            "find -delete"),
    (r'\bxargs\s+.*\brm\b',            "xargs with rm"),

    # 권한 조작
    (r'\bchmod\s+(-[^\s]*\s+)*(777|666|o\+[rwx]*w|a\+[rwx]*w)\b',
                                         "world/other-writable permissions"),
    (r'\bchown\s+(-[^\s]*)?R\s+root',   "recursive chown to root"),

    # 디스크/파일시스템
    (r'\bmkfs\b',                        "format filesystem"),
    (r'\bdd\s+.*if=',                    "disk copy"),
    (r'>\s*/dev/sd',                     "write to block device"),

    # SQL 파괴
    (r'\bDROP\s+(TABLE|DATABASE)\b',     "SQL DROP"),
    (r'\bDELETE\s+FROM\b(?!.*\bWHERE\b)', "SQL DELETE without WHERE"),
    (r'\bTRUNCATE\s+(TABLE)?\s*\w',      "SQL TRUNCATE"),

    # 원격 코드 실행
    (r'\b(curl|wget)\b.*\|\s*(ba)?sh\b', "pipe remote content to shell"),
    (r'\b(bash|sh|zsh|ksh)\s+-[^\s]*c(\s+|$)', "shell command via -c/-lc flag"),
    (r'\b(python[23]?|perl|ruby|node)\s+-[ec]\s+', "script execution via -e/-c flag"),

    # 시스템 서비스
    (r'\bsystemctl\s+(stop|disable|mask)\b', "stop/disable system service"),
    (r'\bkill\s+-9\s+-1\b',             "kill all processes"),

    # 자기 방어
    (r'\b(pkill|killall)\b.*\b(hermes|gateway|cli\.py)\b',
                                         "kill hermes/gateway process"),
    # fork bomb
    (r':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:', "fork bomb"),
]
```

**왜 이렇게 만들었는가?** 정규식 기반 패턴 매칭은 false positive가 있을 수 있지만, false negative(위험한 명령을 놓치는 것)보다 낫다. `python -c "print('hello')"`가 잡히는 것은 불편하지만, `python -c "import os; os.system('rm -rf /')"` 를 놓치는 것은 재앙이다.

### 2.2 명령 정규화 (우회 방지)

패턴 매칭 전에 명령을 정규화하여 우회를 방지한다:

```python
def _normalize_command_for_detection(command: str) -> str:
    from tools.ansi_strip import strip_ansi
    command = strip_ansi(command)          # ANSI 이스케이프 시퀀스 제거
    command = command.replace('\x00', '')   # 널 바이트 제거
    command = unicodedata.normalize('NFKC', command)  # 유니코드 정규화
    return command
```

이 정규화는 세 가지 우회 시도를 차단한다:
- **ANSI 이스케이프**: `\x1b[31mrm -rf /\x1b[0m`으로 패턴을 숨기는 시도
- **널 바이트**: `r\x00m -rf /`로 `rm`패턴을 깨뜨리는 시도
- **유니코드 전각 문자**: `ｒｍ -rf /` (fullwidth Latin)으로 우회하는 시도

### 2.3 승인 흐름

```
명령 실행 요청
      │
      ▼
 컨테이너 환경?  ──예──► 자동 승인 (컨테이너가 보안 경계)
      │ 아니오
      ▼
 YOLO 모드?  ────예──► 자동 승인 (사용자가 명시적으로 비활성화)
      │ 아니오
      ▼
 패턴 매칭
      │
  위험하지 않음 ──────► 자동 승인
      │ 위험함
      ▼
 이미 승인됨?  ──예──► 자동 승인 (세션/영구 허용 목록)
      │ 아니오
      ▼
 Smart 모드?  ──예──► 보조 LLM이 위험도 평가
      │ 아니오          │
      │            APPROVE ──► 자동 승인
      │            DENY ────► 차단
      │            ESCALATE ─┐
      ▼                      │
 사용자에게 프롬프트 ◄────────┘
      │
      ├─ [o]nce: 이번 한 번만 허용
      ├─ [s]ession: 이 세션 동안 허용
      ├─ [a]lways: 영구 허용 목록에 추가
      └─ [d]eny: 차단 ("Do NOT retry" 메시지)
```

### 2.4 Smart Approval (보조 LLM)

`approvals.mode: smart` 설정 시, 패턴에 잡힌 명령을 보조 LLM이 한 번 더 검토한다:

```python
def _smart_approve(command: str, description: str) -> str:
    prompt = f"""You are a security reviewer for an AI coding agent.
Command: {command}
Flagged reason: {description}

Rules:
- APPROVE if the command is clearly safe
- DENY if genuinely dangerous
- ESCALATE if uncertain

Respond with exactly one word: APPROVE, DENY, or ESCALATE"""
```

**왜 이렇게 만들었는가?** `python -c "print('hello')"` 같은 false positive를 자동으로 걸러내기 위함이다. 보조 LLM은 맥락을 이해하므로, 정규식보다 더 정확한 판단이 가능하다. 불확실하면 `ESCALATE`하여 사용자에게 넘긴다.

### 2.5 세션별 승인 상태 관리

```python
_lock = threading.Lock()                    # 스레드 안전성
_session_approved: dict[str, set] = {}      # 세션별 허용 패턴
_permanent_approved: set = set()            # 영구 허용 패턴 (config.yaml 저장)

# 게이트웨이: contextvars로 세션 키 격리
_approval_session_key: contextvars.ContextVar[str] = contextvars.ContextVar(
    "approval_session_key", default=""
)
```

게이트웨이 환경에서는 여러 사용자 세션이 동시에 실행된다. `contextvars.ContextVar`를 사용하여 세션 A의 승인이 세션 B에 영향을 주지 않도록 격리한다.

---

## 3. 프롬프트 인젝션 방어

### 3.1 컨텍스트 파일 스캔

`agent/prompt_builder.py`는 `.hermes.md`, `HERMES.md`, `.cursorrules` 같은 컨텍스트 파일을 시스템 프롬프트에 주입하기 전에 스캔한다:

```python
_CONTEXT_THREAT_PATTERNS = [
    (r'ignore\s+(previous|all|above|prior)\s+instructions', "prompt_injection"),
    (r'do\s+not\s+tell\s+the\s+user',                      "deception_hide"),
    (r'system\s+prompt\s+override',                         "sys_prompt_override"),
    (r'disregard\s+(your|all|any)\s+(instructions|rules|guidelines)',
                                                            "disregard_rules"),
    (r'act\s+as\s+(if|though)\s+you\s+(have\s+no|don\'t\s+have)\s+'
     r'(restrictions|limits|rules)',                        "bypass_restrictions"),
    (r'<!--[^>]*(?:ignore|override|system|secret|hidden)[^>]*-->',
                                                            "html_comment_injection"),
    (r'<\s*div\s+style\s*=\s*["\'].*display\s*:\s*none',   "hidden_div"),
    (r'translate\s+.*\s+into\s+.*\s+and\s+(execute|run|eval)',
                                                            "translate_execute"),
    (r'curl\s+[^\n]*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)',
                                                            "exfil_curl"),
    (r'cat\s+[^\n]*(\.env|credentials|\.netrc|\.pgpass)',   "read_secrets"),
]
```

발견 시 해당 파일의 내용 전체가 차단 메시지로 대체된다:

```python
if findings:
    return f"[BLOCKED: {filename} contained potential prompt injection ({', '.join(findings)}). Content not loaded.]"
```

### 3.2 보이지 않는 유니코드 문자 탐지

```python
_CONTEXT_INVISIBLE_CHARS = {
    '\u200b',  # zero-width space
    '\u200c',  # zero-width non-joiner
    '\u200d',  # zero-width joiner
    '\u2060',  # word joiner
    '\ufeff',  # byte order mark
    '\u202a',  # left-to-right embedding
    '\u202b',  # right-to-left embedding
    '\u202c',  # pop directional formatting
    '\u202d',  # left-to-right override
    '\u202e',  # right-to-left override
}
```

**왜 이렇게 만들었는가?** 공격자가 보이지 않는 유니코드 문자를 프로젝트의 `.hermes.md`에 삽입하면, 사람의 눈에는 정상으로 보이지만 LLM은 숨겨진 지시를 읽게 된다. RTL override(`\u202e`)는 텍스트 방향을 뒤집어 코드 리뷰에서도 발견하기 어려운 공격을 만든다.

### 3.3 스킬 가드 (Skills Guard)

`tools/skills_guard.py`는 외부 스킬 설치 전 정적 분석을 수행한다:

```python
THREAT_PATTERNS = [
    # 비밀 유출: curl/wget로 API 키 전송
    (r'curl\s+[^\n]*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)',
     "env_exfil_curl", "critical", "exfiltration", ...),

    # 비밀 파일 접근
    (r'\$HOME/\.ssh|\~/\.ssh', "ssh_dir_access", "high", "exfiltration", ...),
    (r'\$HOME/\.hermes/\.env', "hermes_env_access", "critical", "exfiltration", ...),
    (r'cat\s+[^\n]*(\.env|credentials|\.netrc)', "read_secrets_file", "critical", ...),

    # DNS 유출
    (r'\b(dig|nslookup|host)\s+[^\n]*\$', "dns_exfil", "critical", "exfiltration", ...),

    # 마크다운 이미지를 통한 유출
    (r'!\[.*\]\(https?://[^\)]*\$\{?', "md_image_exfil", "high", "exfiltration", ...),
]
```

신뢰 수준에 따른 설치 정책:

```
                     safe        caution     dangerous
  builtin:          allow       allow       allow
  trusted:          allow       allow       block
  community:        allow       block       block
  agent-created:    allow       allow       ask
```

**왜 이렇게 만들었는가?** `openai/skills`나 `anthropics/skills` 같은 신뢰된 저장소의 스킬은 `caution` 수준까지 허용하지만, 커뮤니티 스킬은 어떤 발견이든 차단한다. 이는 NPM의 `npm audit` 모델과 유사한 접근이다.

---

## 4. 비밀 유출 차단

### 4.1 환경변수 블로킹

`tools/environments/local.py`의 `_build_provider_env_blocklist()`는 프로바이더 레지스트리에서 자동으로 차단 목록을 구축한다:

```python
# 프로바이더 레지스트리에서 자동 수집
from hermes_cli.auth import PROVIDER_REGISTRY
for pconfig in PROVIDER_REGISTRY.values():
    blocked.update(pconfig.api_key_env_vars)  # 각 프로바이더의 API 키 변수

# 수동 추가 (레지스트리에 없는 것들)
blocked.update({
    "OPENAI_API_KEY", "ANTHROPIC_API_KEY", "OPENROUTER_API_KEY",
    "GOOGLE_API_KEY", "DEEPSEEK_API_KEY", "MISTRAL_API_KEY",
    "GROQ_API_KEY", "TOGETHER_API_KEY", "XAI_API_KEY",
    # 메시징 플랫폼
    "TELEGRAM_HOME_CHANNEL", "DISCORD_HOME_CHANNEL",
    "SLACK_HOME_CHANNEL", ...
    # 원격 샌드박스
    "MODAL_TOKEN_ID", "MODAL_TOKEN_SECRET", "DAYTONA_API_KEY",
})
```

총 40+개의 환경변수가 서브프로세스에 전달되지 않는다.

**왜 이렇게 만들었는가?** 새로운 프로바이더가 추가되면 레지스트리에 등록하는 것만으로 자동 차단된다. 수동 목록 관리의 "잊어버림" 위험을 제거한다.

### 4.2 출력 검열 (redact)

```python
from agent.redact import redact_sensitive_text

# execute_code의 stdout/stderr 검열
stdout_text = redact_sensitive_text(stdout_text)
stderr_text = redact_sensitive_text(stderr_text)
```

환경변수를 차단해도 스크립트가 디스크에서 비밀을 읽을 수 있으므로, 출력 단계에서도 검열한다. 이것이 심층 방어(defense in depth)의 핵심이다:

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│ 1차 방어     │     │ 2차 방어     │     │ 3차 방어     │
│ 환경변수     │────►│ 파일 시스템  │────►│ 출력 검열    │
│ 블로킹       │     │ 쓰기 금지    │     │ (redact)    │
└─────────────┘     └─────────────┘     └─────────────┘
   API 키가            .env 쓰기가          유출된 비밀이
   env에서 제거         차단됨               출력에서 마스킹
```

### 4.3 보호 디렉토리

다음 디렉토리 내의 파일들은 쓰기가 차단된다:

```python
WRITE_DENIED_PREFIXES = [
    "~/.ssh",        # SSH 키, known_hosts
    "~/.aws",        # AWS 자격증명
    "~/.gnupg",      # GPG 키링
    "~/.kube",       # Kubernetes 설정
    "~/.docker",     # Docker 레지스트리 인증
    "~/.azure",      # Azure CLI 인증
    "~/.config/gh",  # GitHub CLI 토큰
    "/etc/sudoers.d",# sudo 권한
    "/etc/systemd",  # systemd 서비스 설정
]
```

---

## 5. 파일 시스템 보호

### 5.1 쓰기 금지 목록

`tools/file_operations.py`에 정의된 절대 쓰기 금지 파일들:

```python
WRITE_DENIED_PATHS = {
    os.path.realpath(p) for p in [
        "~/.ssh/authorized_keys",  # SSH 인증 키
        "~/.ssh/id_rsa",           # SSH 개인 키
        "~/.ssh/id_ed25519",       # SSH ED25519 키
        "~/.ssh/config",           # SSH 설정
        "~/.hermes/.env",          # Hermes 비밀 파일
        "~/.bashrc",               # 셸 시작 스크립트
        "~/.zshrc",                # Zsh 시작 스크립트
        "~/.profile",              # 로그인 프로필
        "~/.netrc",                # 네트워크 자격증명
        "~/.pgpass",               # PostgreSQL 비밀번호
        "~/.npmrc",                # NPM 인증
        "~/.pypirc",               # PyPI 인증
        "/etc/sudoers",            # sudo 권한 설정
        "/etc/passwd",             # 사용자 계정
        "/etc/shadow",             # 해시된 비밀번호
    ]
}
```

### 5.2 심링크 공격 방지

모든 경로에 `os.path.realpath()`를 적용하여 심링크 해석(symlink resolution)을 수행한다:

```python
WRITE_DENIED_PATHS = {
    os.path.realpath(p) for p in [...]  # realpath: 심링크를 따라간 실제 경로
}
```

**공격 시나리오:**
```
공격자가 프로젝트에 심링크 생성:
  ./innocent.txt -> ~/.ssh/authorized_keys

에이전트가 write_file("./innocent.txt", "ssh-rsa AAAA...")를 시도
  → realpath 해석: ./innocent.txt → ~/.ssh/authorized_keys
  → WRITE_DENIED_PATHS에 포함 → 차단!
```

스킬 디렉토리 마운트에서도 같은 방어가 적용된다. `credential_files.py`의 `_safe_skills_path()`는:

```python
def _safe_skills_path(skills_dir: Path) -> str:
    symlinks = [p for p in skills_dir.rglob("*") if p.is_symlink()]
    if not symlinks:
        return str(skills_dir)  # 심링크 없으면 원본 사용

    # 심링크 발견 시: 정규 파일만 복사한 안전한 사본 생성
    safe_dir = Path(tempfile.mkdtemp(prefix="hermes-skills-safe-"))
    for item in skills_dir.rglob("*"):
        if item.is_symlink():
            continue  # 심링크는 무시
        # 일반 파일만 복사
```

자격증명 파일 등록에서도 경로 탈출(path traversal)을 방지한다:

```python
def register_credential_file(relative_path: str, ...):
    if os.path.isabs(relative_path):
        return False  # 절대 경로 거부

    resolved = host_path.resolve()
    resolved.relative_to(hermes_home_resolved)  # HERMES_HOME 밖이면 ValueError
```

---

## 6. 컨테이너 격리

### 6.1 Docker 보안 하드닝

`tools/environments/docker.py`에 정의된 보안 플래그:

```python
_SECURITY_ARGS = [
    "--cap-drop", "ALL",                        # 모든 Linux 능력 제거
    "--cap-add", "DAC_OVERRIDE",                # bind mount 쓰기용
    "--cap-add", "CHOWN",                       # 패키지 관리자용
    "--cap-add", "FOWNER",                      # 파일 소유권 변경용
    "--security-opt", "no-new-privileges",      # 권한 상승 차단
    "--pids-limit", "256",                      # PID 수 제한 (fork bomb 방지)
    "--tmpfs", "/tmp:rw,nosuid,size=512m",      # tmp: SUID 차단, 512MB 제한
    "--tmpfs", "/var/tmp:rw,noexec,nosuid,size=256m",  # 실행 금지
    "--tmpfs", "/run:rw,noexec,nosuid,size=64m",       # 실행 금지
]
```

각 설정의 의미:

```
┌──────────────────────────────────────────────────────────────┐
│                  Docker 보안 계층                              │
│                                                              │
│  cap-drop ALL + cap-add 3개                                  │
│  ├─ NET_RAW 없음: raw socket 생성 불가 (ARP 스푸핑 방지)      │
│  ├─ SYS_ADMIN 없음: mount, cgroup 조작 불가                   │
│  ├─ NET_ADMIN 없음: 네트워크 인터페이스 조작 불가              │
│  └─ DAC_OVERRIDE + CHOWN + FOWNER만 허용                      │
│                                                              │
│  no-new-privileges                                           │
│  └─ setuid/setgid 바이너리가 권한을 상승시킬 수 없음          │
│                                                              │
│  pids-limit 256                                              │
│  └─ fork bomb이 256개 프로세스에서 멈춤                       │
│                                                              │
│  tmpfs 크기 제한                                              │
│  ├─ /tmp: 512MB (빌드 아티팩트용, nosuid)                     │
│  ├─ /var/tmp: 256MB (noexec, nosuid)                         │
│  └─ /run: 64MB (noexec, nosuid)                              │
└──────────────────────────────────────────────────────────────┘
```

**왜 이렇게 만들었는가?** 컨테이너 안에서는 `approval.py`의 명령어 승인이 건너뛰어진다(`env_type in ("docker", "singularity", "modal", "daytona")` 조건). 대신 컨테이너 자체가 보안 경계 역할을 한다. 에이전트가 `rm -rf /`를 실행해도 컨테이너만 파괴되고, 호스트 시스템은 안전하다.

### 6.2 비영속 모드의 tmpfs

영속 저장이 비활성화된 경우:

```python
writable_args.extend([
    "--tmpfs", "/workspace:rw,exec,size=10g",  # 작업 공간
    "--tmpfs", "/home:rw,exec,size=1g",        # 홈 디렉토리
    "--tmpfs", "/root:rw,exec,size=1g",        # 루트 홈
])
```

세션 종료 시 모든 데이터가 사라진다. 민감한 작업에 적합하다.

---

## 7. 코드 실행 샌드박스

`execute_code` 도구는 LLM이 작성한 Python 스크립트를 실행한다. 보안 관점에서 세 가지 방어층이 있다:

### 7.1 환경변수 필터링

로컬 백엔드에서 자식 프로세스 생성 시:

```python
def _sanitize_subprocess_env(base_env, extra_env=None):
    sanitized = {}
    for key, value in base_env.items():
        if key not in _HERMES_PROVIDER_ENV_BLOCKLIST:
            sanitized[key] = value
    return sanitized
```

### 7.2 도구 허용 목록

RPC 서버는 7개 도구만 허용한다:

```python
SANDBOX_ALLOWED_TOOLS = frozenset([
    "web_search", "web_extract",
    "read_file", "write_file", "search_files", "patch",
    "terminal",
])
```

`delegate_task`, `memory`, `clarify`, `send_message`, `execute_code` 자체는 사용 불가.

### 7.3 터미널 파라미터 차단

```python
_TERMINAL_BLOCKED_PARAMS = {"background", "check_interval", "pty"}
```

샌드박스 스크립트에서 백그라운드 프로세스 실행이나 PTY 할당을 차단한다.

### 7.4 도구 호출 제한

```python
DEFAULT_MAX_TOOL_CALLS = 50

if tool_call_counter[0] >= max_tool_calls:
    resp = {"error": f"Tool call limit reached ({max_tool_calls})."}
```

스크립트가 무한 루프로 도구를 호출하는 것을 방지한다.

### 7.5 출력 크기 제한

```python
MAX_STDOUT_BYTES = 50_000    # 50 KB
MAX_STDERR_BYTES = 10_000    # 10 KB
```

대량 출력으로 LLM의 컨텍스트 윈도우를 가득 채우는 것을 방지한다.

---

## 8. 크론 잡 인젝션 방어

`tools/cronjob_tools.py`는 예약 작업의 프롬프트를 별도로 스캔한다. 크론 잡은 사용자 없이 자동 실행되므로, 인젝션이 성공하면 장시간 탐지되지 않을 수 있다.

```python
_CRON_THREAT_PATTERNS = [
    (r'ignore\s+(?:\w+\s+)*(?:previous|all|above|prior)\s+'
     r'(?:\w+\s+)*instructions',                 "prompt_injection"),
    (r'do\s+not\s+tell\s+the\s+user',           "deception_hide"),
    (r'system\s+prompt\s+override',              "sys_prompt_override"),
    (r'disregard\s+(your|all|any)\s+(instructions|rules|guidelines)',
                                                  "disregard_rules"),
    (r'curl\s+[^\n]*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)',
                                                  "exfil_curl"),
    (r'cat\s+[^\n]*(\.env|credentials|\.netrc|\.pgpass)',
                                                  "read_secrets"),
    (r'authorized_keys',                          "ssh_backdoor"),
    (r'/etc/sudoers|visudo',                      "sudoers_mod"),
    (r'rm\s+-rf\s+/',                            "destructive_root_rm"),
]
```

컨텍스트 파일 스캔과 동일하게 보이지 않는 유니코드 문자도 탐지한다:

```python
_CRON_INVISIBLE_CHARS = {
    '\u200b', '\u200c', '\u200d', '\u2060', '\ufeff',
    '\u202a', '\u202b', '\u202c', '\u202d', '\u202e',
}
```

**왜 이렇게 만들었는가?** 크론 잡의 프롬프트는 한번 등록되면 반복적으로 실행된다. 공격자가 `create_cron_job`의 `prompt` 필드에 인젝션을 삽입하면, 매 실행마다 비밀이 유출될 수 있다. 특히 `authorized_keys` 패턴은 SSH 백도어 설치를 탐지한다.

---

## 9. 보안 체크리스트

### 기여자를 위한 보안 코딩 가이드라인

**새로운 도구 추가 시:**

- [ ] 도구가 파일을 쓰는가? `WRITE_DENIED_PATHS`와 `WRITE_DENIED_PREFIXES` 검사를 추가하라
- [ ] 도구가 셸 명령을 실행하는가? `check_all_command_guards()`를 거치는지 확인하라
- [ ] 도구의 출력이 LLM에 전달되는가? `redact_sensitive_text()`로 검열하라
- [ ] 도구가 외부 입력을 받는가? 프롬프트 인젝션 패턴을 스캔하라
- [ ] 도구가 서브에이전트에서 사용 가능해야 하는가? `DELEGATE_BLOCKED_TOOLS` 목록을 검토하라

**새로운 프로바이더 추가 시:**

- [ ] API 키 환경변수를 `PROVIDER_REGISTRY`에 등록하라 (자동 블로킹)
- [ ] 수동 블로킹 목록에도 fallback으로 추가하라

**컨텍스트 파일 처리 시:**

- [ ] `_scan_context_content()`를 반드시 거쳐야 한다
- [ ] 보이지 않는 유니코드 문자를 확인하라
- [ ] HTML 주석이나 hidden div를 통한 인젝션을 차단하라

**크론 잡 관련:**

- [ ] 프롬프트에 `_scan_cron_prompt()`를 적용하라
- [ ] 크론 잡이 새 세션에서 실행되므로, 전체 도구 접근이 가능함을 인지하라

**컨테이너 환경:**

- [ ] 커스텀 Docker 이미지를 사용하는 경우, `_SECURITY_ARGS`가 적용되는지 확인하라
- [ ] bind mount 경로가 민감한 호스트 디렉토리를 노출하지 않는지 검증하라
- [ ] 스킬 디렉토리 마운트 시 심링크가 없는지 확인하라 (`_safe_skills_path()`)

---

## 핵심 정리

1. **Hermes의 보안은 심층 방어(defense in depth) 전략을 따른다.** 하나의 방어층이 실패해도, 다음 층이 잡아낸다. 환경변수 블로킹 -> 파일 쓰기 금지 -> 출력 검열의 3중 방어가 대표적이다.

2. **`approval.py`의 30+개 정규식 패턴**이 위험 명령을 감지하고, ANSI/유니코드 정규화로 우회를 방지한다. Smart Approval 모드에서는 보조 LLM이 false positive를 자동 걸러낸다.

3. **프롬프트 인젝션은 세 곳에서 방어된다**: 컨텍스트 파일 스캔(prompt_builder.py), 스킬 가드(skills_guard.py), 크론 프롬프트 스캔(cronjob_tools.py). 10개의 위협 패턴과 10개의 보이지 않는 유니코드 문자를 탐지한다.

4. **비밀 유출은 입출력 양쪽에서 차단된다.** 입력: 환경변수 블로킹(40+개). 출력: `redact_sensitive_text()` 검열. 저장소: 보호 디렉토리(`.ssh`, `.aws`, `.docker` 등) 쓰기 금지.

5. **파일 시스템 보호는 `os.path.realpath()`로 심링크 공격을 방지**하고, `WRITE_DENIED_PATHS`로 민감 파일을 보호한다. 스킬 마운트 시 심링크를 포함한 디렉토리는 안전한 사본으로 대체된다.

6. **Docker 컨테이너는 `cap-drop ALL`, `no-new-privileges`, `pids-limit 256`, `tmpfs` 크기 제한**으로 하드닝된다. 컨테이너 안에서는 명령어 승인이 건너뛰어지는 대신, 컨테이너 자체가 보안 경계이다.

7. **`execute_code` 샌드박스는 7개 도구만 허용**, 도구 호출 50회 제한, stdout 50KB 제한, 터미널 백그라운드 실행 차단으로 제한된다.

8. **크론 잡은 별도의 인젝션 스캐너**를 가진다. 사용자 없이 자동 실행되므로, `authorized_keys` 백도어나 `sudoers` 조작 같은 지속성(persistence) 공격을 특별히 탐지한다.

9. **보안은 기여자의 책임이기도 하다.** 새 도구 추가 시 쓰기 금지 검사, 출력 검열, 프롬프트 스캔을 반드시 포함해야 한다.
