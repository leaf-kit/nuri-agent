# Hermes Agent 기여 가이드

Hermes Agent에 기여해 주셔서 감사합니다! 이 가이드에서는 개발 환경 설정, 아키텍처 이해, 무엇을 만들지 결정하는 방법, 그리고 PR을 병합하는 과정까지 모든 내용을 다룹니다.

---

## 기여 우선순위

기여는 다음 순서로 중요하게 다룹니다:

1. **버그 수정** — 충돌, 잘못된 동작, 데이터 손실. 항상 최우선입니다.
2. **크로스 플랫폼 호환성** — Windows, macOS, 다양한 Linux 배포판, 다양한 터미널 에뮬레이터. Hermes가 어디서든 동작하기를 원합니다.
3. **보안 강화** — 셸 인젝션, 프롬프트 인젝션, 경로 탐색, 권한 상승. [보안](#보안-고려사항)을 참조하세요.
4. **성능 및 안정성** — 재시도 로직, 오류 처리, 점진적 기능 저하.
5. **새로운 스킬** — 단, 범용적으로 유용한 것만. [스킬로 만들어야 할까, 도구로 만들어야 할까?](#스킬로-만들어야-할까-도구로-만들어야-할까)를 참조하세요.
6. **새로운 도구** — 거의 필요하지 않습니다. 대부분의 기능은 스킬로 구현해야 합니다. 아래를 참조하세요.
7. **문서화** — 수정, 명확화, 새로운 예제.

---

## 스킬로 만들어야 할까, 도구로 만들어야 할까?

새로운 기여자들이 가장 많이 하는 질문입니다. 답은 거의 항상 **스킬**입니다.

### 스킬로 만들어야 할 때:

- 해당 기능을 지침 + 셸 명령어 + 기존 도구로 표현할 수 있을 때
- 에이전트가 `terminal`이나 `web_extract`를 통해 호출할 수 있는 외부 CLI나 API를 래핑할 때
- 에이전트 하네스에 통합된 커스텀 Python 연동이나 API 키 관리가 필요하지 않을 때
- 예시: arXiv 검색, Git 워크플로우, Docker 관리, PDF 처리, CLI 도구를 통한 이메일

### 도구로 만들어야 할 때:

- 에이전트 하네스가 관리하는 API 키, 인증 흐름, 또는 다중 컴포넌트 설정과의 엔드투엔드 통합이 필요할 때
- LLM 해석에 의한 "최선의 노력"이 아닌, 매번 정확하게 실행되어야 하는 커스텀 처리 로직이 필요할 때
- 터미널을 통해 전달할 수 없는 바이너리 데이터, 스트리밍, 또는 실시간 이벤트를 처리할 때
- 예시: 브라우저 자동화(Browserbase 세션 관리), TTS(오디오 인코딩 + 플랫폼 전달), 비전 분석(base64 이미지 처리)

### 스킬을 번들로 포함해야 할까?

번들 스킬(`skills/`)은 모든 Hermes 설치에 포함됩니다. **대부분의 사용자에게 폭넓게 유용한** 것이어야 합니다:

- 문서 처리, 웹 리서치, 일반적인 개발 워크플로우, 시스템 관리
- 다양한 사용자가 정기적으로 사용하는 것

스킬이 공식적이고 유용하지만 보편적으로 필요하지 않은 경우(예: 유료 서비스 통합, 무거운 의존성), **`optional-skills/`** 에 넣으세요 — 저장소에는 포함되지만 기본적으로 활성화되지 않습니다. 사용자는 `hermes skills browse`("official" 라벨)로 발견하고 `hermes skills install`(서드파티 경고 없이, 내장 신뢰)로 설치할 수 있습니다.

스킬이 전문적이거나, 커뮤니티 기여이거나, 틈새 분야인 경우 **Skills Hub**에 더 적합합니다 — 스킬 레지스트리에 업로드하고 [Nous Research Discord](https://discord.gg/NousResearch)에서 공유하세요. 사용자는 `hermes skills install`로 설치할 수 있습니다.

---

## 개발 환경 설정

### 사전 요구사항

| 요구사항 | 비고 |
|----------|------|
| **Git** | `--recurse-submodules` 지원 필요 |
| **Python 3.11+** | 없으면 uv가 자동 설치 |
| **uv** | 빠른 Python 패키지 관리자 ([설치](https://docs.astral.sh/uv/)) |
| **Node.js 18+** | 선택 사항 — 브라우저 도구 및 WhatsApp 브릿지에 필요 |

### 클론 및 설치

```bash
git clone --recurse-submodules https://github.com/NousResearch/hermes-agent.git
cd hermes-agent

# Python 3.11로 가상환경 생성
uv venv venv --python 3.11
export VIRTUAL_ENV="$(pwd)/venv"

# 모든 extras 포함 설치 (메시징, cron, CLI 메뉴, 개발 도구)
uv pip install -e ".[all,dev]"

# 선택 사항: RL 학습 서브모듈
# git submodule update --init tinker-atropos && uv pip install -e "./tinker-atropos"

# 선택 사항: 브라우저 도구
npm install
```

### 개발을 위한 설정

```bash
mkdir -p ~/.hermes/{cron,sessions,logs,memories,skills}
cp cli-config.yaml.example ~/.hermes/config.yaml
touch ~/.hermes/.env

# 최소한 LLM 제공자 키를 추가하세요:
echo 'OPENROUTER_API_KEY=sk-or-v1-your-key' >> ~/.hermes/.env
```

### 실행

```bash
# 전역 접근을 위한 심볼릭 링크 생성
mkdir -p ~/.local/bin
ln -sf "$(pwd)/venv/bin/hermes" ~/.local/bin/hermes

# 확인
hermes doctor
hermes chat -q "Hello"
```

### 테스트 실행

```bash
pytest tests/ -v
```

---

## 프로젝트 구조

```
hermes-agent/
├── run_agent.py              # AIAgent 클래스 — 핵심 대화 루프, 도구 디스패치, 세션 영속성
├── cli.py                    # HermesCLI 클래스 — 대화형 TUI, prompt_toolkit 통합
├── model_tools.py            # 도구 오케스트레이션 (tools/registry.py 위의 얇은 레이어)
├── toolsets.py               # 도구 그룹화 및 프리셋 (hermes-cli, hermes-telegram 등)
├── hermes_state.py           # FTS5 전문 검색 기능이 있는 SQLite 세션 데이터베이스, 세션 제목
├── batch_runner.py           # 궤적 생성을 위한 병렬 배치 처리
│
├── agent/                    # 에이전트 내부 모듈 (추출된 모듈)
│   ├── prompt_builder.py         # 시스템 프롬프트 조립 (정체성, 스킬, 컨텍스트 파일, 메모리)
│   ├── context_compressor.py     # 컨텍스트 한도 근접 시 자동 요약
│   ├── auxiliary_client.py       # 보조 OpenAI 클라이언트 해석 (요약, 비전)
│   ├── display.py                # KawaiiSpinner, 도구 진행 상태 포매팅
│   ├── model_metadata.py         # 모델 컨텍스트 길이, 토큰 추정
│   └── trajectory.py             # 궤적 저장 헬퍼
│
├── hermes_cli/               # CLI 명령어 구현
│   ├── main.py                   # 진입점, 인자 파싱, 명령어 디스패치
│   ├── config.py                 # 설정 관리, 마이그레이션, 환경 변수 정의
│   ├── setup.py                  # 대화형 설정 마법사
│   ├── auth.py                   # 제공자 해석, OAuth, Nous Portal
│   ├── models.py                 # OpenRouter 모델 선택 목록
│   ├── banner.py                 # 환영 배너, ASCII 아트
│   ├── commands.py               # 중앙 슬래시 명령어 레지스트리 (CommandDef), 자동완성, 게이트웨이 헬퍼
│   ├── callbacks.py              # 대화형 콜백 (확인, sudo, 승인)
│   ├── doctor.py                 # 진단
│   ├── skills_hub.py             # Skills Hub CLI + /skills 슬래시 명령어
│   └── skin_engine.py            # 스킨/테마 엔진 — 데이터 기반 CLI 시각적 커스터마이징
│
├── tools/                    # 도구 구현 (자체 등록 방식)
│   ├── registry.py               # 중앙 도구 레지스트리 (스키마, 핸들러, 디스패치)
│   ├── approval.py               # 위험 명령어 탐지 + 세션별 승인
│   ├── terminal_tool.py          # 터미널 오케스트레이션 (sudo, 환경 생명주기, 백엔드)
│   ├── file_operations.py        # read_file, write_file, search, patch 등
│   ├── web_tools.py              # web_search, web_extract (Parallel/Firecrawl + Gemini 요약)
│   ├── vision_tools.py           # 멀티모달 모델을 통한 이미지 분석
│   ├── delegate_tool.py          # 서브에이전트 생성 및 병렬 작업 실행
│   ├── code_execution_tool.py    # RPC 도구 접근이 가능한 샌드박스 Python
│   ├── session_search_tool.py    # FTS5 + 요약으로 과거 대화 검색
│   ├── cronjob_tools.py          # 예약 작업 관리
│   ├── skill_tools.py            # 스킬 검색, 로드, 관리
│   └── environments/             # 터미널 실행 백엔드
│       ├── base.py                   # BaseEnvironment ABC
│       ├── local.py, docker.py, ssh.py, singularity.py, modal.py, daytona.py
│
├── gateway/                  # 메시징 게이트웨이
│   ├── run.py                    # GatewayRunner — 플랫폼 생명주기, 메시지 라우팅, cron
│   ├── config.py                 # 플랫폼 설정 해석
│   ├── session.py                # 세션 스토어, 컨텍스트 프롬프트, 리셋 정책
│   └── platforms/                # 플랫폼 어댑터
│       ├── telegram.py, discord_adapter.py, slack.py, whatsapp.py
│
├── scripts/                  # 설치 및 브릿지 스크립트
│   ├── install.sh                # Linux/macOS 설치 스크립트
│   ├── install.ps1               # Windows PowerShell 설치 스크립트
│   └── whatsapp-bridge/          # Node.js WhatsApp 브릿지 (Baileys)
│
├── skills/                   # 번들 스킬 (설치 시 ~/.hermes/skills/에 복사)
├── optional-skills/          # 공식 선택 스킬 (허브에서 검색 가능, 기본 비활성화)
├── environments/             # RL 학습 환경 (Atropos 통합)
├── tests/                    # 테스트 모음
├── website/                  # 문서 사이트 (hermes-agent.nousresearch.com)
│
├── cli-config.yaml.example   # 설정 예제 (설치 시 ~/.hermes/config.yaml에 복사)
└── AGENTS.md                 # AI 코딩 어시스턴트를 위한 개발 가이드
```

### 사용자 설정 (`~/.hermes/`에 저장)

| 경로 | 용도 |
|------|------|
| `~/.hermes/config.yaml` | 설정 (모델, 터미널, 도구셋, 압축 등) |
| `~/.hermes/.env` | API 키 및 비밀 정보 |
| `~/.hermes/auth.json` | OAuth 자격 증명 (Nous Portal) |
| `~/.hermes/skills/` | 모든 활성 스킬 (번들 + 허브 설치 + 에이전트 생성) |
| `~/.hermes/memories/` | 영구 메모리 (MEMORY.md, USER.md) |
| `~/.hermes/state.db` | SQLite 세션 데이터베이스 |
| `~/.hermes/sessions/` | JSON 세션 로그 |
| `~/.hermes/cron/` | 예약 작업 데이터 |
| `~/.hermes/whatsapp/session/` | WhatsApp 브릿지 자격 증명 |

---

## 아키텍처 개요

### 핵심 루프

```
사용자 메시지 → AIAgent._run_agent_loop()
  ├── 시스템 프롬프트 구성 (prompt_builder.py)
  ├── API kwargs 구성 (모델, 메시지, 도구, 추론 설정)
  ├── LLM 호출 (OpenAI 호환 API)
  ├── 응답에 tool_calls가 있는 경우:
  │     ├── 레지스트리 디스패치를 통해 각 도구 실행
  │     ├── 도구 결과를 대화에 추가
  │     └── LLM 호출로 다시 루프
  ├── 텍스트 응답인 경우:
  │     ├── 세션을 DB에 영속화
  │     └── final_response 반환
  └── 토큰 한도 근접 시 컨텍스트 압축
```

### 주요 설계 패턴

- **자체 등록 도구**: 각 도구 파일은 임포트 시 `registry.register()`를 호출합니다. `model_tools.py`가 모든 도구 모듈을 임포트하여 탐색을 트리거합니다.
- **도구셋 그룹화**: 도구는 도구셋(`web`, `terminal`, `file`, `browser` 등)으로 그룹화되며 플랫폼별로 활성화/비활성화할 수 있습니다.
- **세션 영속성**: 모든 대화는 전문 검색과 고유 세션 제목이 포함된 SQLite(`hermes_state.py`)에 저장됩니다. JSON 로그는 `~/.hermes/sessions/`에 저장됩니다.
- **임시 주입**: 시스템 프롬프트와 프리필 메시지는 API 호출 시점에 주입되며, 데이터베이스나 로그에 영속화되지 않습니다.
- **제공자 추상화**: 에이전트는 모든 OpenAI 호환 API와 동작합니다. 제공자 해석은 초기화 시 수행됩니다 (Nous Portal OAuth, OpenRouter API 키, 또는 커스텀 엔드포인트).
- **제공자 라우팅**: OpenRouter 사용 시 config.yaml의 `provider_routing`이 제공자 선택을 제어합니다 (처리량/지연/가격별 정렬, 특정 제공자 허용/무시, 데이터 보존 정책). 이는 API 요청에서 `extra_body.provider`로 주입됩니다.

---

## 코드 스타일

- **PEP 8** 준수 (실용적인 예외 허용 — 엄격한 줄 길이 제한은 적용하지 않음)
- **주석**: 비자명한 의도, 트레이드오프, API 특이 사항을 설명할 때만 작성. 코드가 하는 일을 나열하지 마세요 — `# increment counter`는 아무 도움이 되지 않습니다
- **오류 처리**: 특정 예외를 잡으세요. `logger.warning()`/`logger.error()`로 기록하되 — 예상치 못한 오류에는 `exc_info=True`를 사용하여 스택 트레이스가 로그에 나타나도록 하세요
- **크로스 플랫폼**: 절대로 Unix를 가정하지 마세요. [크로스 플랫폼 호환성](#크로스-플랫폼-호환성)을 참조하세요

---

## 새 도구 추가

도구를 작성하기 전에 먼저 확인하세요: [이것은 스킬로 만들어야 하지 않을까?](#스킬로-만들어야-할까-도구로-만들어야-할까)

도구는 중앙 레지스트리에 자체 등록됩니다. 각 도구 파일은 스키마, 핸들러, 등록을 함께 포함합니다:

```python
"""my_tool — 이 도구가 하는 일에 대한 간략한 설명."""

import json
from tools.registry import registry


def my_tool(param1: str, param2: int = 10, **kwargs) -> str:
    """핸들러. 문자열 결과(주로 JSON)를 반환합니다."""
    result = do_work(param1, param2)
    return json.dumps(result)


MY_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "my_tool",
        "description": "What this tool does and when the agent should use it.",
        "parameters": {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "What param1 is"},
                "param2": {"type": "integer", "description": "What param2 is", "default": 10},
            },
            "required": ["param1"],
        },
    },
}


def _check_requirements() -> bool:
    """이 도구의 의존성이 사용 가능한지 확인합니다."""
    return True


registry.register(
    name="my_tool",
    toolset="my_toolset",
    schema=MY_TOOL_SCHEMA,
    handler=lambda args, **kw: my_tool(**args, **kw),
    check_fn=_check_requirements,
)
```

그런 다음 `model_tools.py`의 `_modules` 리스트에 임포트를 추가하세요:

```python
_modules = [
    # ... 기존 모듈 ...
    "tools.my_tool",
]
```

새로운 도구셋인 경우 `toolsets.py`와 관련 플랫폼 프리셋에도 추가하세요.

---

## 스킬 추가

번들 스킬은 `skills/`에 카테고리별로 정리됩니다. 공식 선택 스킬은 `optional-skills/`에서 동일한 구조를 사용합니다:

```
skills/
├── research/
│   └── arxiv/
│       ├── SKILL.md              # 필수: 주요 지침
│       └── scripts/              # 선택: 헬퍼 스크립트
│           └── search_arxiv.py
├── productivity/
│   └── ocr-and-documents/
│       ├── SKILL.md
│       ├── scripts/
│       └── references/
└── ...
```

### SKILL.md 형식

```markdown
---
name: my-skill
description: 간략한 설명 (스킬 검색 결과에 표시됨)
version: 1.0.0
author: Your Name
license: MIT
platforms: [macos, linux]          # 선택 — 특정 OS 플랫폼으로 제한
                                   #   유효값: macos, linux, windows
                                   #   생략하면 모든 플랫폼에서 로드 (기본값)
required_environment_variables:    # 선택 — 로드 시 보안 설정 메타데이터
  - name: MY_API_KEY
    prompt: API key
    help: Where to get it
    required_for: full functionality
prerequisites:                     # 선택 — 레거시 런타임 요구사항
  env_vars: [MY_API_KEY]           #   필수 환경 변수의 하위 호환 별칭
  commands: [curl, jq]             #   안내 목적; 스킬을 숨기지 않음
metadata:
  hermes:
    tags: [Category, Subcategory, Keywords]
    related_skills: [other-skill-name]
    fallback_for_toolsets: [web]       # 선택 — 도구셋 사용 불가 시에만 표시
    requires_toolsets: [terminal]      # 선택 — 도구셋 사용 가능 시에만 표시
---

# 스킬 제목

간략한 소개.

## 사용 시점
트리거 조건 — 에이전트가 이 스킬을 언제 로드해야 하는가?

## 빠른 참조
일반적인 명령어 또는 API 호출 표.

## 절차
에이전트가 따르는 단계별 지침.

## 주의사항
알려진 실패 사례와 대처 방법.

## 검증
정상 동작 여부를 확인하는 방법.
```

### 플랫폼별 스킬

스킬은 `platforms` 프론트매터 필드를 통해 지원하는 OS 플랫폼을 선언할 수 있습니다. 이 필드가 있는 스킬은 호환되지 않는 플랫폼에서 시스템 프롬프트, `skills_list()`, 슬래시 명령어에서 자동으로 숨겨집니다.

```yaml
platforms: [macos]            # macOS 전용 (예: iMessage, Apple 미리 알림)
platforms: [macos, linux]     # macOS 및 Linux
platforms: [windows]          # Windows 전용
```

필드를 생략하거나 비워두면 모든 플랫폼에서 스킬이 로드됩니다 (하위 호환). `skills/apple/`에서 macOS 전용 스킬 예제를 참조하세요.

### 조건부 스킬 활성화

스킬은 현재 세션에서 사용 가능한 도구와 도구셋에 따라 시스템 프롬프트에 나타나는 시점을 제어하는 조건을 선언할 수 있습니다. 이는 주로 **대체 스킬** — 기본 도구가 사용 불가능할 때만 표시되어야 하는 대안에 사용됩니다.

`metadata.hermes` 아래에 네 가지 필드가 지원됩니다:

```yaml
metadata:
  hermes:
    fallback_for_toolsets: [web]      # 이 도구셋이 사용 불가능할 때만 표시
    requires_toolsets: [terminal]     # 이 도구셋이 사용 가능할 때만 표시
    fallback_for_tools: [web_search]  # 이 특정 도구가 사용 불가능할 때만 표시
    requires_tools: [terminal]        # 이 특정 도구가 사용 가능할 때만 표시
```

**의미:**
- `fallback_for_*`: 해당 스킬은 백업입니다. 나열된 도구/도구셋이 사용 가능하면 **숨겨지고**, 사용 불가능하면 **표시됩니다**. 프리미엄 도구의 무료 대안에 사용하세요.
- `requires_*`: 해당 스킬은 특정 도구가 있어야 동작합니다. 나열된 도구/도구셋이 사용 불가능하면 **숨겨집니다**. 특정 기능에 의존하는 스킬에 사용하세요 (예: 터미널 접근이 필요한 스킬).
- 둘 다 지정된 경우, 두 조건이 모두 충족되어야 스킬이 나타납니다.
- 둘 다 지정되지 않은 경우, 스킬은 항상 표시됩니다 (하위 호환).

**예시:**

```yaml
# DuckDuckGo 검색 — Firecrawl (web 도구셋)이 사용 불가능할 때 표시
metadata:
  hermes:
    fallback_for_toolsets: [web]

# 스마트 홈 스킬 — 터미널이 사용 가능할 때만 유용
metadata:
  hermes:
    requires_toolsets: [terminal]

# 로컬 브라우저 대체 — Browserbase가 사용 불가능할 때 표시
metadata:
  hermes:
    fallback_for_toolsets: [browser]
```

필터링은 `agent/prompt_builder.py`에서 프롬프트 빌드 시점에 수행됩니다. `build_skills_system_prompt()` 함수가 에이전트로부터 사용 가능한 도구와 도구셋 세트를 받아 `_skill_should_show()`로 각 스킬의 조건을 평가합니다.

### 스킬 설정 메타데이터

스킬은 `required_environment_variables` 프론트매터 필드를 통해 로드 시 보안 설정 메타데이터를 선언할 수 있습니다. 값이 누락되어도 스킬이 검색에서 숨겨지지 않으며, 스킬이 실제로 로드될 때 CLI 전용 보안 프롬프트가 트리거됩니다.

```yaml
required_environment_variables:
  - name: TENOR_API_KEY
    prompt: Tenor API key
    help: Get a key from https://developers.google.com/tenor
    required_for: full functionality
```

사용자는 설정을 건너뛰고 스킬을 계속 로드할 수 있습니다. Hermes는 메타데이터(`stored_as`, `skipped`, `validated`)만 모델에 노출하며, 실제 비밀 값은 절대 노출하지 않습니다.

레거시 `prerequisites.env_vars`는 계속 지원되며 새 표현으로 정규화됩니다.

```yaml
prerequisites:
  env_vars: [TENOR_API_KEY]       # required_environment_variables의 레거시 별칭
  commands: [curl, jq]            # 안내 목적 CLI 검사
```

게이트웨이 및 메시징 세션은 인밴드로 비밀 정보를 수집하지 않으며, 사용자에게 `hermes setup`을 실행하거나 `~/.hermes/.env`를 로컬에서 업데이트하도록 안내합니다.

**필수 환경 변수를 선언해야 할 때:**
- 스킬이 로드 시 안전하게 수집되어야 하는 API 키나 토큰을 사용할 때
- 사용자가 설정을 건너뛰어도 스킬이 유용하지만, 기능이 점진적으로 저하될 수 있을 때

**명령어 사전 요구사항을 선언해야 할 때:**
- 스킬이 설치되지 않았을 수 있는 CLI 도구에 의존할 때 (예: `himalaya`, `openhue`, `ddgs`)
- 명령어 검사는 안내로 취급하며, 검색 시점에 숨기지 않음

예제는 `skills/gifs/gif-search/`와 `skills/email/himalaya/`를 참조하세요.

### 스킬 가이드라인

- **절대적으로 필요한 경우가 아니면 외부 의존성을 사용하지 마세요.** 표준 라이브러리 Python, curl, 기존 Hermes 도구(`web_extract`, `terminal`, `read_file`)를 선호하세요.
- **점진적 공개.** 가장 일반적인 워크플로우를 먼저 배치하세요. 엣지 케이스와 고급 사용법은 하단에 놓으세요.
- **헬퍼 스크립트를 포함하세요** — XML/JSON 파싱이나 복잡한 로직에 사용. LLM이 매번 인라인으로 파서를 작성하도록 기대하지 마세요.
- **테스트하세요.** `hermes --toolsets skills -q "Use the X skill to do Y"`를 실행하고 에이전트가 지침을 올바르게 따르는지 확인하세요.

---

## 스킨 / 테마 추가

Hermes는 데이터 기반 스킨 시스템을 사용합니다 — 새 스킨을 추가하는 데 코드 변경이 필요하지 않습니다.

**방법 A: 사용자 스킨 (YAML 파일)**

`~/.hermes/skins/<name>.yaml`을 생성하세요:

```yaml
name: mytheme
description: Short description of the theme

colors:
  banner_border: "#HEX"     # 패널 테두리 색상
  banner_title: "#HEX"      # 패널 제목 색상
  banner_accent: "#HEX"     # 섹션 헤더 색상
  banner_dim: "#HEX"        # 흐린/어두운 텍스트 색상
  banner_text: "#HEX"       # 본문 텍스트 색상
  response_border: "#HEX"   # 응답 박스 테두리

spinner:
  waiting_faces: ["(⚔)", "(⛨)"]
  thinking_faces: ["(⚔)", "(⌁)"]
  thinking_verbs: ["forging", "plotting"]
  wings:                     # 선택 — 좌우 장식
    - ["⟪⚔", "⚔⟫"]

branding:
  agent_name: "My Agent"
  welcome: "Welcome message"
  response_label: " ⚔ Agent "
  prompt_symbol: "⚔ ❯ "

tool_prefix: "╎"             # 도구 출력 줄 접두사
```

모든 필드는 선택 사항입니다 — 누락된 값은 기본 스킨에서 상속됩니다.

**방법 B: 내장 스킨**

`hermes_cli/skin_engine.py`의 `_BUILTIN_SKINS` 딕셔너리에 추가하세요. 위와 동일한 스키마를 Python 딕셔너리로 사용하세요. 내장 스킨은 패키지와 함께 배포되며 항상 사용 가능합니다.

**활성화:**
- CLI: `/skin mytheme` 또는 config.yaml에서 `display.skin: mytheme` 설정
- 설정: `display: { skin: mytheme }`

전체 스키마와 기존 스킨 예제는 `hermes_cli/skin_engine.py`를 참조하세요.

---

## 크로스 플랫폼 호환성

Hermes는 Linux, macOS, Windows에서 실행됩니다. OS와 관련된 코드를 작성할 때:

### 핵심 규칙

1. **`termios`와 `fcntl`은 Unix 전용입니다.** 항상 `ImportError`와 `NotImplementedError`를 모두 잡으세요:
   ```python
   try:
       from simple_term_menu import TerminalMenu
       menu = TerminalMenu(options)
       idx = menu.show()
   except (ImportError, NotImplementedError):
       # 대체: Windows를 위한 번호 메뉴
       for i, opt in enumerate(options):
           print(f"  {i+1}. {opt}")
       idx = int(input("Choice: ")) - 1
   ```

2. **파일 인코딩.** Windows에서 `.env` 파일을 `cp1252`로 저장할 수 있습니다. 항상 인코딩 오류를 처리하세요:
   ```python
   try:
       load_dotenv(env_path)
   except UnicodeDecodeError:
       load_dotenv(env_path, encoding="latin-1")
   ```

3. **프로세스 관리.** `os.setsid()`, `os.killpg()`, 시그널 처리는 Windows에서 다릅니다. 플랫폼 검사를 사용하세요:
   ```python
   import platform
   if platform.system() != "Windows":
       kwargs["preexec_fn"] = os.setsid
   ```

4. **경로 구분자.** `/`를 이용한 문자열 결합 대신 `pathlib.Path`를 사용하세요.

5. **설치 스크립트의 셸 명령어.** `scripts/install.sh`를 변경한 경우, `scripts/install.ps1`에도 동일한 변경이 필요한지 확인하세요.

---

## 보안 고려사항

Hermes는 터미널 접근 권한이 있습니다. 보안이 중요합니다.

### 기존 보호 장치

| 계층 | 구현 |
|------|------|
| **Sudo 비밀번호 파이핑** | 셸 인젝션 방지를 위해 `shlex.quote()` 사용 |
| **위험 명령어 탐지** | `tools/approval.py`의 정규식 패턴과 사용자 승인 흐름 |
| **Cron 프롬프트 인젝션** | `tools/cronjob_tools.py`의 스캐너가 지침 오버라이드 패턴 차단 |
| **쓰기 거부 목록** | 보호된 경로(`~/.ssh/authorized_keys`, `/etc/shadow`)를 심볼릭 링크 우회 방지를 위해 `os.path.realpath()`로 해석 |
| **스킬 가드** | 허브에서 설치된 스킬을 위한 보안 스캐너(`tools/skills_guard.py`) |
| **코드 실행 샌드박스** | `execute_code` 자식 프로세스는 환경에서 API 키가 제거된 상태로 실행 |
| **컨테이너 보안 강화** | Docker: 모든 권한 제거, 권한 상승 불가, PID 제한, 크기 제한된 tmpfs |

### 보안에 민감한 코드를 기여할 때

- 사용자 입력을 셸 명령어에 삽입할 때 **항상 `shlex.quote()`를 사용하세요**
- 경로 기반 접근 제어 검사 전에 `os.path.realpath()`로 **심볼릭 링크를 해석하세요**
- **비밀 정보를 로그에 남기지 마세요.** API 키, 토큰, 비밀번호는 절대로 로그 출력에 나타나서는 안 됩니다
- 단일 실패가 에이전트 루프를 중단시키지 않도록 도구 실행 주위에서 **광범위한 예외를 잡으세요**
- 변경 사항이 파일 경로, 프로세스 관리, 셸 명령어에 관련된 경우 **모든 플랫폼에서 테스트하세요**

PR이 보안에 영향을 미치는 경우, 설명에 명시적으로 기재하세요.

---

## Pull Request 프로세스

### 브랜치 이름 규칙

```
fix/description        # 버그 수정
feat/description       # 새 기능
docs/description       # 문서
test/description       # 테스트
refactor/description   # 코드 구조 개선
```

### 제출 전 확인사항

1. **테스트 실행**: `pytest tests/ -v`
2. **수동 테스트**: `hermes`를 실행하고 변경한 코드 경로를 직접 확인
3. **크로스 플랫폼 영향 확인**: 파일 I/O, 프로세스 관리, 터미널 처리에 관련된 경우 Windows와 macOS를 고려
4. **PR을 집중적으로 유지**: PR 하나에 논리적 변경 하나. 버그 수정과 리팩터링과 새 기능을 섞지 마세요.

### PR 설명

다음을 포함하세요:
- **무엇**이 변경되었고 **왜** 변경했는지
- **테스트 방법** (버그의 재현 단계, 기능의 사용 예제)
- **테스트한 플랫폼**
- 관련 이슈 참조

### 커밋 메시지

[Conventional Commits](https://www.conventionalcommits.org/)를 사용합니다:

```
<type>(<scope>): <description>
```

| 타입 | 용도 |
|------|------|
| `fix` | 버그 수정 |
| `feat` | 새 기능 |
| `docs` | 문서 |
| `test` | 테스트 |
| `refactor` | 코드 구조 개선 (동작 변경 없음) |
| `chore` | 빌드, CI, 의존성 업데이트 |

스코프: `cli`, `gateway`, `tools`, `skills`, `agent`, `install`, `whatsapp`, `security` 등.

예시:
```
fix(cli): prevent crash in save_config_value when model is a string
feat(gateway): add WhatsApp multi-user session isolation
fix(security): prevent shell injection in sudo password piping
test(tools): add unit tests for file_operations
```

---

## 이슈 보고

- [GitHub Issues](https://github.com/NousResearch/hermes-agent/issues)를 사용하세요
- 포함할 정보: OS, Python 버전, Hermes 버전(`hermes version`), 전체 오류 트레이스백
- 재현 단계를 포함하세요
- 중복 이슈를 만들기 전에 기존 이슈를 확인하세요
- 보안 취약점은 비공개로 보고해 주세요

---

## 커뮤니티

- **Discord**: [discord.gg/NousResearch](https://discord.gg/NousResearch) — 질문, 프로젝트 공유, 스킬 공유를 위한 공간
- **GitHub Discussions**: 설계 제안 및 아키텍처 논의
- **Skills Hub**: 전문 스킬을 레지스트리에 업로드하고 커뮤니티와 공유하세요

---

## 라이선스

기여함으로써, 귀하의 기여물이 [MIT 라이선스](LICENSE)에 따라 라이선스됨에 동의합니다.
