# Hermes Agent - 개발 가이드

AI 코딩 어시스턴트 및 hermes-agent 코드베이스에서 작업하는 개발자를 위한 안내서입니다.

## 개발 환경

```bash
source venv/bin/activate  # Python 실행 전 반드시 활성화
```

## 프로젝트 구조

```
hermes-agent/
├── run_agent.py          # AIAgent 클래스 — 핵심 대화 루프
├── model_tools.py        # 도구 오케스트레이션, _discover_tools(), handle_function_call()
├── toolsets.py           # 도구세트 정의, _HERMES_CORE_TOOLS 목록
├── cli.py                # HermesCLI 클래스 — 대화형 CLI 오케스트레이터
├── hermes_state.py       # SessionDB — SQLite 세션 저장소 (FTS5 검색)
├── agent/                # 에이전트 내부 모듈
│   ├── prompt_builder.py     # 시스템 프롬프트 조립
│   ├── context_compressor.py # 자동 컨텍스트 압축
│   ├── prompt_caching.py     # Anthropic 프롬프트 캐싱
│   ├── auxiliary_client.py   # 보조 LLM 클라이언트 (비전, 요약)
│   ├── model_metadata.py     # 모델 컨텍스트 길이, 토큰 추정
│   ├── models_dev.py         # models.dev 레지스트리 통합 (프로바이더 인식 컨텍스트)
│   ├── display.py            # KawaiiSpinner, 도구 미리보기 포맷팅
│   ├── skill_commands.py     # 스킬 슬래시 명령어 (CLI/게이트웨이 공유)
│   └── trajectory.py         # 궤적 저장 헬퍼
├── hermes_cli/           # CLI 하위 명령어 및 설정
│   ├── main.py           # 진입점 — 모든 `hermes` 하위 명령어
│   ├── config.py         # DEFAULT_CONFIG, OPTIONAL_ENV_VARS, 마이그레이션
│   ├── commands.py       # 슬래시 명령어 정의 + SlashCommandCompleter
│   ├── callbacks.py      # 터미널 콜백 (명확화, sudo, 승인)
│   ├── setup.py          # 대화형 설정 마법사
│   ├── skin_engine.py    # 스킨/테마 엔진 — CLI 시각적 커스터마이징
│   ├── skills_config.py  # `hermes skills` — 플랫폼별 스킬 활성화/비활성화
│   ├── tools_config.py   # `hermes tools` — 플랫폼별 도구 활성화/비활성화
│   ├── skills_hub.py     # `/skills` 슬래시 명령어 (검색, 탐색, 설치)
│   ├── models.py         # 모델 카탈로그, 프로바이더 모델 목록
│   ├── model_switch.py   # 공유 /model 전환 파이프라인 (CLI + 게이트웨이)
│   └── auth.py           # 프로바이더 자격 증명 해석
├── tools/                # 도구 구현 (파일당 하나의 도구)
│   ├── registry.py       # 중앙 도구 레지스트리 (스키마, 핸들러, 디스패치)
│   ├── approval.py       # 위험한 명령어 감지
│   ├── terminal_tool.py  # 터미널 오케스트레이션
│   ├── process_registry.py # 백그라운드 프로세스 관리
│   ├── file_tools.py     # 파일 읽기/쓰기/검색/패치
│   ├── web_tools.py      # 웹 검색/추출 (Parallel + Firecrawl)
│   ├── browser_tool.py   # Browserbase 브라우저 자동화
│   ├── code_execution_tool.py # execute_code 샌드박스
│   ├── delegate_tool.py  # 서브에이전트 위임
│   ├── mcp_tool.py       # MCP 클라이언트 (~1050줄)
│   └── environments/     # 터미널 백엔드 (local, docker, ssh, modal, daytona, singularity)
├── gateway/              # 메시징 플랫폼 게이트웨이
│   ├── run.py            # 메인 루프, 슬래시 명령어, 메시지 디스패치
│   ├── session.py        # SessionStore — 대화 영속화
│   └── platforms/        # 어댑터: telegram, discord, slack, whatsapp, homeassistant, signal
├── acp_adapter/          # ACP 서버 (VS Code / Zed / JetBrains 통합)
├── cron/                 # 스케줄러 (jobs.py, scheduler.py)
├── environments/         # RL 훈련 환경 (Atropos)
├── tests/                # Pytest 스위트 (~3000개 테스트)
└── batch_runner.py       # 병렬 배치 처리
```

**사용자 설정:** `~/.hermes/config.yaml` (설정), `~/.hermes/.env` (API 키)

## 파일 의존성 체인

```
tools/registry.py  (의존성 없음 — 모든 도구 파일에서 임포트)
       ↑
tools/*.py  (각각 임포트 시 registry.register() 호출)
       ↑
model_tools.py  (tools/registry 임포트 + 도구 발견 트리거)
       ↑
run_agent.py, cli.py, batch_runner.py, environments/
```

---

## AIAgent 클래스 (run_agent.py)

```python
class AIAgent:
    def __init__(self,
        model: str = "anthropic/claude-opus-4.6",
        max_iterations: int = 90,
        enabled_toolsets: list = None,
        disabled_toolsets: list = None,
        quiet_mode: bool = False,
        save_trajectories: bool = False,
        platform: str = None,           # "cli", "telegram" 등
        session_id: str = None,
        skip_context_files: bool = False,
        skip_memory: bool = False,
        # ... 추가로 provider, api_mode, callbacks, routing 매개변수
    ): ...

    def chat(self, message: str) -> str:
        """간단한 인터페이스 — 최종 응답 문자열을 반환합니다."""

    def run_conversation(self, user_message: str, system_message: str = None,
                         conversation_history: list = None, task_id: str = None) -> dict:
        """전체 인터페이스 — final_response + messages가 포함된 dict를 반환합니다."""
```

### 에이전트 루프

핵심 루프는 `run_conversation()` 내부에 있으며 — 완전히 동기식입니다:

```python
while api_call_count < self.max_iterations and self.iteration_budget.remaining > 0:
    response = client.chat.completions.create(model=model, messages=messages, tools=tool_schemas)
    if response.tool_calls:
        for tool_call in response.tool_calls:
            result = handle_function_call(tool_call.name, tool_call.args, task_id)
            messages.append(tool_result_message(result))
        api_call_count += 1
    else:
        return response.content
```

메시지는 OpenAI 형식을 따릅니다: `{"role": "system/user/assistant/tool", ...}`. 추론 내용은 `assistant_msg["reasoning"]`에 저장됩니다.

---

## CLI 아키텍처 (cli.py)

- 배너/패널에 **Rich**, 자동완성 입력에 **prompt_toolkit** 사용
- **KawaiiSpinner** (`agent/display.py`) — API 호출 시 애니메이션 이모지, 도구 결과를 위한 `┊` 활동 피드
- `cli.py`의 `load_cli_config()`가 하드코딩된 기본값 + 사용자 설정 YAML을 병합
- **스킨 엔진** (`hermes_cli/skin_engine.py`) — 데이터 주도 CLI 테마; 시작 시 `display.skin` 설정 키로 초기화; 스킨이 배너 색상, 스피너 이모지/동사/날개, 도구 접두사, 응답 상자, 브랜딩 텍스트를 커스터마이즈
- `process_command()`는 `HermesCLI`의 메서드 — 중앙 레지스트리의 `resolve_command()`로 확인된 정식 명령어 이름으로 디스패치
- 스킬 슬래시 명령어: `agent/skill_commands.py`가 `~/.hermes/skills/`를 스캔하여 프롬프트 캐싱을 보존하기 위해 **사용자 메시지**로 주입 (시스템 프롬프트가 아님)

### 슬래시 명령어 레지스트리 (`hermes_cli/commands.py`)

모든 슬래시 명령어는 `CommandDef` 객체의 중앙 `COMMAND_REGISTRY` 목록에 정의됩니다. 모든 하위 소비자가 이 레지스트리에서 자동으로 파생됩니다:

- **CLI** — `process_command()`가 `resolve_command()`로 별칭 확인 후 정식 이름으로 디스패치
- **게이트웨이** — 훅 발생을 위한 `GATEWAY_KNOWN_COMMANDS` frozenset, 디스패치를 위한 `resolve_command()`
- **게이트웨이 도움말** — `gateway_help_lines()`가 `/help` 출력 생성
- **Telegram** — `telegram_bot_commands()`가 BotCommand 메뉴 생성
- **Slack** — `slack_subcommand_map()`이 `/hermes` 하위 명령어 라우팅 생성
- **자동완성** — `COMMANDS` 플랫 딕셔너리가 `SlashCommandCompleter`에 전달
- **CLI 도움말** — `COMMANDS_BY_CATEGORY` 딕셔너리가 `show_help()`에 전달

### 슬래시 명령어 추가하기

1. `hermes_cli/commands.py`의 `COMMAND_REGISTRY`에 `CommandDef` 항목 추가:
```python
CommandDef("mycommand", "Description of what it does", "Session",
           aliases=("mc",), args_hint="[arg]"),
```
2. `cli.py`의 `HermesCLI.process_command()`에 핸들러 추가:
```python
elif canonical == "mycommand":
    self._handle_mycommand(cmd_original)
```
3. 게이트웨이에서도 사용 가능한 명령어라면, `gateway/run.py`에 핸들러 추가:
```python
if canonical == "mycommand":
    return await self._handle_mycommand(event)
```
4. 영속적 설정에는 `cli.py`의 `save_config_value()` 사용

**CommandDef 필드:**
- `name` — 슬래시 없는 정식 이름 (예: `"background"`)
- `description` — 사람이 읽을 수 있는 설명
- `category` — `"Session"`, `"Configuration"`, `"Tools & Skills"`, `"Info"`, `"Exit"` 중 하나
- `aliases` — 대체 이름 튜플 (예: `("bg",)`)
- `args_hint` — 도움말에 표시되는 인수 자리표시자 (예: `"<prompt>"`, `"[name]"`)
- `cli_only` — 대화형 CLI에서만 사용 가능
- `gateway_only` — 메시징 플랫폼에서만 사용 가능
- `gateway_config_gate` — 설정 도트 경로 (예: `"display.tool_progress_command"`); `cli_only` 명령어에 설정하면 설정값이 참일 때 게이트웨이에서 사용 가능. `GATEWAY_KNOWN_COMMANDS`는 항상 설정 게이트 명령어를 포함하여 게이트웨이가 디스패치 가능; 도움말/메뉴는 게이트가 열려있을 때만 표시.

**별칭 추가**는 기존 `CommandDef`의 `aliases` 튜플에만 추가하면 됩니다. 다른 파일 변경 불필요 — 디스패치, 도움말 텍스트, Telegram 메뉴, Slack 매핑, 자동완성이 모두 자동으로 업데이트됩니다.

---

## 새 도구 추가하기

**3개 파일**에 변경이 필요합니다:

**1. `tools/your_tool.py` 생성:**
```python
import json, os
from tools.registry import registry

def check_requirements() -> bool:
    return bool(os.getenv("EXAMPLE_API_KEY"))

def example_tool(param: str, task_id: str = None) -> str:
    return json.dumps({"success": True, "data": "..."})

registry.register(
    name="example_tool",
    toolset="example",
    schema={"name": "example_tool", "description": "...", "parameters": {...}},
    handler=lambda args, **kw: example_tool(param=args.get("param", ""), task_id=kw.get("task_id")),
    check_fn=check_requirements,
    requires_env=["EXAMPLE_API_KEY"],
)
```

**2. `model_tools.py`**의 `_discover_tools()` 목록에 임포트 추가.

**3. `toolsets.py`에 추가** — `_HERMES_CORE_TOOLS` (모든 플랫폼) 또는 새 도구세트.

레지스트리가 스키마 수집, 디스패치, 가용성 확인, 오류 래핑을 처리합니다. 모든 핸들러는 JSON 문자열을 반환해야 합니다.

**도구 스키마의 경로 참조**: 스키마 설명에 파일 경로가 언급되면 (예: 기본 출력 디렉토리), 프로필 인식을 위해 `display_hermes_home()`을 사용하세요. 스키마는 임포트 시점에 생성되며, 이는 `_apply_profile_override()`가 `HERMES_HOME`을 설정한 후입니다.

**상태 파일**: 도구가 영속적 상태(캐시, 로그, 체크포인트)를 저장하면, 기본 디렉토리에 `get_hermes_home()`을 사용하세요 — 절대 `Path.home() / ".hermes"`를 사용하지 마세요. 이렇게 하면 각 프로필이 고유한 상태를 갖게 됩니다.

**에이전트 수준 도구** (todo, memory): `handle_function_call()` 전에 `run_agent.py`가 가로챕니다. 패턴은 `todo_tool.py`를 참조하세요.

---

## 설정 추가하기

### config.yaml 옵션:
1. `hermes_cli/config.py`의 `DEFAULT_CONFIG`에 추가
2. `_config_version` (현재 5) 증가로 기존 사용자의 마이그레이션 트리거

### .env 변수:
1. `hermes_cli/config.py`의 `OPTIONAL_ENV_VARS`에 메타데이터와 함께 추가:
```python
"NEW_API_KEY": {
    "description": "용도 설명",
    "prompt": "표시 이름",
    "url": "https://...",
    "password": True,
    "category": "tool",  # provider, tool, messaging, setting
},
```

### 설정 로더 (두 개의 별도 시스템):

| 로더 | 사용처 | 위치 |
|------|--------|------|
| `load_cli_config()` | CLI 모드 | `cli.py` |
| `load_config()` | `hermes tools`, `hermes setup` | `hermes_cli/config.py` |
| 직접 YAML 로드 | 게이트웨이 | `gateway/run.py` |

---

## 스킨/테마 시스템

스킨 엔진(`hermes_cli/skin_engine.py`)은 데이터 주도 CLI 시각적 커스터마이징을 제공합니다. 스킨은 **순수 데이터** — 새 스킨을 추가하는 데 코드 변경이 필요 없습니다.

### 아키텍처

```
hermes_cli/skin_engine.py    # SkinConfig 데이터클래스, 내장 스킨, YAML 로더
~/.hermes/skins/*.yaml       # 사용자 설치 커스텀 스킨 (드롭인)
```

- `init_skin_from_config()` — CLI 시작 시 호출, 설정에서 `display.skin` 읽기
- `get_active_skin()` — 현재 스킨의 캐시된 `SkinConfig` 반환
- `set_active_skin(name)` — 런타임에 스킨 전환 (`/skin` 명령어에서 사용)
- `load_skin(name)` — 사용자 스킨 먼저, 그 다음 내장, 그 다음 기본으로 폴백
- 누락된 스킨 값은 `default` 스킨에서 자동 상속

### 스킨이 커스터마이즈하는 요소

| 요소 | 스킨 키 | 사용처 |
|------|---------|--------|
| 배너 패널 테두리 | `colors.banner_border` | `banner.py` |
| 배너 패널 제목 | `colors.banner_title` | `banner.py` |
| 배너 섹션 헤더 | `colors.banner_accent` | `banner.py` |
| 배너 흐린 텍스트 | `colors.banner_dim` | `banner.py` |
| 배너 본문 텍스트 | `colors.banner_text` | `banner.py` |
| 응답 상자 테두리 | `colors.response_border` | `cli.py` |
| 스피너 이모지 (대기) | `spinner.waiting_faces` | `display.py` |
| 스피너 이모지 (사고) | `spinner.thinking_faces` | `display.py` |
| 스피너 동사 | `spinner.thinking_verbs` | `display.py` |
| 스피너 날개 (선택사항) | `spinner.wings` | `display.py` |
| 도구 출력 접두사 | `tool_prefix` | `display.py` |
| 도구별 이모지 | `tool_emojis` | `display.py` → `get_tool_emoji()` |
| 에이전트 이름 | `branding.agent_name` | `banner.py`, `cli.py` |
| 환영 메시지 | `branding.welcome` | `cli.py` |
| 응답 상자 레이블 | `branding.response_label` | `cli.py` |
| 프롬프트 기호 | `branding.prompt_symbol` | `cli.py` |

### 내장 스킨

- `default` — 클래식 Hermes 골드/카와이 (현재 외관)
- `ares` — 크림슨/브론즈 전쟁의 신 테마, 커스텀 스피너 날개
- `mono` — 깔끔한 그레이스케일 모노크롬
- `slate` — 쿨 블루 개발자 중심 테마

### 내장 스킨 추가하기

`hermes_cli/skin_engine.py`의 `_BUILTIN_SKINS` 딕셔너리에 추가:

```python
"mytheme": {
    "name": "mytheme",
    "description": "Short description",
    "colors": { ... },
    "spinner": { ... },
    "branding": { ... },
    "tool_prefix": "┊",
},
```

### 사용자 스킨 (YAML)

`~/.hermes/skins/<name>.yaml` 생성:

```yaml
name: cyberpunk
description: Neon-soaked terminal theme

colors:
  banner_border: "#FF00FF"
  banner_title: "#00FFFF"
  banner_accent: "#FF1493"

spinner:
  thinking_verbs: ["jacking in", "decrypting", "uploading"]
  wings:
    - ["⟨⚡", "⚡⟩"]

branding:
  agent_name: "Cyber Agent"
  response_label: " ⚡ Cyber "

tool_prefix: "▏"
```

`/skin cyberpunk` 또는 config.yaml에서 `display.skin: cyberpunk`로 활성화.

---

## 중요 정책

### 프롬프트 캐싱을 깨뜨리면 안 됨

Hermes-Agent는 대화 전체에서 캐싱이 유효하게 유지되도록 보장합니다. **다음을 야기하는 변경을 구현하지 마세요:**
- 대화 중 과거 컨텍스트 변경
- 대화 중 도구세트 변경
- 대화 중 메모리 재로드 또는 시스템 프롬프트 재구축

캐시 파괴는 극적으로 높은 비용을 초래합니다. 컨텍스트를 변경하는 유일한 시점은 컨텍스트 압축 중입니다.

### 작업 디렉토리 동작
- **CLI**: 현재 디렉토리 사용 (`.` → `os.getcwd()`)
- **메시징**: `MESSAGING_CWD` 환경 변수 사용 (기본값: 홈 디렉토리)

### 백그라운드 프로세스 알림 (게이트웨이)

`terminal(background=true, check_interval=...)`이 사용되면, 게이트웨이가 사용자 채팅에 상태 업데이트를 푸시하는 워처를 실행합니다. config.yaml의 `display.background_process_notifications` (또는 `HERMES_BACKGROUND_NOTIFICATIONS` 환경 변수)로 상세도를 제어:

- `all` — 실행 중 출력 업데이트 + 최종 메시지 (기본값)
- `result` — 최종 완료 메시지만
- `error` — 종료 코드가 0이 아닐 때만 최종 메시지
- `off` — 워처 메시지 없음

---

## 프로필: 다중 인스턴스 지원

Hermes는 **프로필**을 지원합니다 — 각각 고유한 `HERMES_HOME` 디렉토리(설정, API 키, 메모리, 세션, 스킬, 게이트웨이 등)를 가진 완전히 격리된 여러 인스턴스.

핵심 메커니즘: `hermes_cli/main.py`의 `_apply_profile_override()`가 모듈 임포트 전에 `HERMES_HOME`을 설정합니다. `get_hermes_home()`에 대한 119개 이상의 참조가 모두 자동으로 활성 프로필로 범위가 지정됩니다.

### 프로필 안전 코드 규칙

1. **모든 HERMES_HOME 경로에 `get_hermes_home()` 사용.** `hermes_constants`에서 임포트.
   코드에서 상태를 읽거나 쓸 때 절대 `~/.hermes` 또는 `Path.home() / ".hermes"`를 하드코딩하지 마세요.
   ```python
   # 올바름
   from hermes_constants import get_hermes_home
   config_path = get_hermes_home() / "config.yaml"

   # 잘못됨 — 프로필을 깨뜨림
   config_path = Path.home() / ".hermes" / "config.yaml"
   ```

2. **사용자 대면 메시지에 `display_hermes_home()` 사용.** `hermes_constants`에서 임포트.
   기본의 경우 `~/.hermes`, 프로필의 경우 `~/.hermes/profiles/<name>`을 반환합니다.
   ```python
   # 올바름
   from hermes_constants import display_hermes_home
   print(f"Config saved to {display_hermes_home()}/config.yaml")

   # 잘못됨 — 프로필에서 잘못된 경로 표시
   print("Config saved to ~/.hermes/config.yaml")
   ```

3. **모듈 수준 상수는 괜찮음** — 임포트 시점에 `get_hermes_home()`을 캐시하며, 이는 `_apply_profile_override()`가 환경 변수를 설정한 후입니다. `Path.home() / ".hermes"`가 아닌 `get_hermes_home()`을 사용하세요.

4. **`Path.home()`을 모킹하는 테스트는 `HERMES_HOME`도 설정해야 함** — 코드가 이제 `Path.home() / ".hermes"`가 아닌 `get_hermes_home()` (환경 변수 읽기)을 사용하므로:
   ```python
   with patch.object(Path, "home", return_value=tmp_path), \
        patch.dict(os.environ, {"HERMES_HOME": str(tmp_path / ".hermes")}):
       ...
   ```

5. **게이트웨이 플랫폼 어댑터는 토큰 잠금을 사용해야 함** — 어댑터가 고유한 자격 증명(봇 토큰, API 키)으로 연결되는 경우, `connect()`/`start()` 메서드에서 `gateway.status`의 `acquire_scoped_lock()`을 호출하고 `disconnect()`/`stop()`에서 `release_scoped_lock()`을 호출하세요. 두 프로필이 같은 자격 증명을 사용하는 것을 방지합니다. 정식 패턴은 `gateway/platforms/telegram.py`를 참조하세요.

6. **프로필 작업은 HERMES_HOME이 아닌 HOME 기준** — `_get_profiles_root()`는 `get_hermes_home() / "profiles"`가 아닌 `Path.home() / ".hermes" / "profiles"`를 반환합니다. 이는 의도적입니다 — `hermes -p coder profile list`가 활성 프로필과 관계없이 모든 프로필을 볼 수 있게 합니다.

## 알려진 함정

### `~/.hermes` 경로를 하드코딩하지 마세요
코드 경로에는 `hermes_constants`의 `get_hermes_home()`을 사용하세요. 사용자 대면 print/log 메시지에는 `display_hermes_home()`을 사용하세요. `~/.hermes` 하드코딩은 프로필을 깨뜨립니다 — 각 프로필은 고유한 `HERMES_HOME` 디렉토리를 가집니다. 이것은 PR #3575에서 수정된 5개 버그의 원인이었습니다.

### `simple_term_menu`를 대화형 메뉴에 사용하지 마세요
tmux/iTerm2에서 렌더링 버그 — 스크롤 시 고스트. 대신 `curses` (stdlib)를 사용하세요. 패턴은 `hermes_cli/tools_config.py`를 참조하세요.

### 스피너/디스플레이 코드에서 `\033[K` (ANSI 줄 끝까지 지우기)를 사용하지 마세요
`prompt_toolkit`의 `patch_stdout` 하에서 리터럴 `?[K` 텍스트로 누출됩니다. 공백 패딩을 사용하세요: `f"\r{line}{' ' * pad}"`.

### `_last_resolved_tool_names`는 `model_tools.py`의 프로세스 전역 변수
`delegate_tool.py`의 `_run_single_child()`가 서브에이전트 실행 전후로 이 전역 변수를 저장하고 복원합니다. 이 전역 변수를 읽는 새 코드를 추가하면, 자식 에이전트 실행 중에 일시적으로 오래된 값일 수 있음에 유의하세요.

### 도구 스키마 설명에 교차 도구 참조를 하드코딩하지 마세요
도구 스키마 설명은 다른 도구세트의 도구를 이름으로 언급하면 안 됩니다 (예: `browser_navigate`가 "prefer web_search"라고 말하는 것). 해당 도구가 사용 불가능할 수 있으며(API 키 누락, 비활성화된 도구세트), 모델이 존재하지 않는 도구 호출을 할루시네이트하게 됩니다. 교차 참조가 필요하면, `model_tools.py`의 `get_tool_definitions()`에서 동적으로 추가하세요 — `browser_navigate` / `execute_code` 후처리 블록 패턴을 참조하세요.

### 테스트는 `~/.hermes/`에 쓰면 안 됨
`tests/conftest.py`의 `_isolate_hermes_home` autouse 픽스처가 `HERMES_HOME`을 임시 디렉토리로 리다이렉트합니다. 테스트에서 `~/.hermes/` 경로를 절대 하드코딩하지 마세요.

**프로필 테스트**: 프로필 기능을 테스트할 때는 `Path.home()`도 모킹하여 `_get_profiles_root()`와 `_get_default_hermes_home()`이 임시 디렉토리 내에서 해석되도록 하세요.
`tests/hermes_cli/test_profiles.py`의 패턴을 사용하세요:
```python
@pytest.fixture
def profile_env(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home
```

---

## 테스트

```bash
source venv/bin/activate
python -m pytest tests/ -q          # 전체 스위트 (~3000개 테스트, ~3분)
python -m pytest tests/test_model_tools.py -q   # 도구세트 해석
python -m pytest tests/test_cli_init.py -q       # CLI 설정 로딩
python -m pytest tests/gateway/ -q               # 게이트웨이 테스트
python -m pytest tests/tools/ -q                 # 도구 수준 테스트
```

변경사항을 푸시하기 전에 항상 전체 스위트를 실행하세요.
