# 강좌 10: 확장과 커스터마이징

> **이 강좌에서 배우는 것**
>
> - 스킨 엔진으로 CLI의 시각적 외관을 데이터 주도 방식으로 커스터마이징하는 방법
> - 프로필 시스템으로 완전히 격리된 다중 Hermes 인스턴스를 운영하는 원리
> - MCP (Model Context Protocol)를 통한 외부 도구 확장과 에디터 통합
> - Atropos RL 훈련 환경으로 차세대 도구 호출 모델을 훈련하는 파이프라인
> - 크론 스케줄러로 예약 작업을 자동화하는 방법
> - AIAgent를 라이브러리로 임포트하여 자체 프로젝트에 활용하는 패턴

---

## 1. 스킨 엔진

### 데이터 주도 시각적 커스터마이징

`hermes_cli/skin_engine.py`는 코드 변경 없이 CLI의 시각적 외관을 완전히 바꿀 수 있는 데이터 주도 스킨 시스템이다.

**왜 이렇게 만들었는가?** CLI 도구에서 시각적 커스터마이징은 보통 하드코딩된 색상 상수를 수정해야 한다. Hermes는 스킨을 YAML 데이터로 분리하여, 사용자가 Python 코드를 한 줄도 수정하지 않고 전체 외관을 바꿀 수 있게 했다. 이는 커뮤니티 스킨 공유를 가능하게 하는 설계이다.

### SkinConfig 데이터클래스

```python
@dataclass
class SkinConfig:
    name: str
    description: str = ""
    colors: Dict[str, str] = field(default_factory=dict)
    spinner: Dict[str, Any] = field(default_factory=dict)
    branding: Dict[str, str] = field(default_factory=dict)
    tool_prefix: str = "┊"
    tool_emojis: Dict[str, str] = field(default_factory=dict)
    banner_logo: str = ""     # Rich 마크업 ASCII 아트 로고
    banner_hero: str = ""     # Rich 마크업 히어로 아트
```

스킨이 커스터마이징하는 요소:

```
+-------------------------------------------------------+
|  banner_logo   (ASCII 아트 로고)                        |
|  banner_hero   (캐릭터 아트)                            |
+-------------------------------------------------------+
|  colors.banner_border  |  패널 테두리 색상              |
|  colors.banner_title   |  패널 제목 텍스트 색상          |
|  colors.banner_accent  |  섹션 헤더 색상                |
|  colors.banner_text    |  본문 텍스트 색상               |
+-------------------------------------------------------+
|  branding.agent_name   |  "Hermes Agent"               |
|  branding.welcome      |  시작 메시지                    |
|  branding.goodbye      |  종료 메시지                    |
|  branding.prompt_symbol|  입력 프롬프트 기호 "❯ "        |
+-------------------------------------------------------+
|  spinner.waiting_faces |  API 대기 중 표정 ["(^_^)", ...]|
|  spinner.thinking_verbs|  사고 중 동사 ["plotting", ...]  |
|  spinner.wings         |  스피너 장식 [["⟪⚔", "⚔⟫"]]   |
+-------------------------------------------------------+
|  tool_prefix           |  도구 출력 줄 접두사 "┊"         |
|  tool_emojis           |  도구별 이모지 오버라이드         |
+-------------------------------------------------------+
```

### 내장 스킨

Hermes는 7개 이상의 내장 스킨을 제공한다:

| 스킨 | 테마 | 프롬프트 | 특징 |
|------|------|---------|------|
| **default** | 금색 카와이 | `❯` | 클래식 Hermes, 따뜻한 골드 톤 |
| **ares** | 진홍/청동 전쟁신 | `⚔ ❯` | 커스텀 스피너 날개, 전투 동사 |
| **mono** | 그레이스케일 | `❯` | 클린한 흑백, 최소주의 |
| **slate** | 쿨 블루 | `❯` | 개발자 중심, 차분한 색상 |
| **poseidon** | 딥 블루/해류 | `Ψ ❯` | 바다 테마 스피너 |
| **sisyphus** | 회색/인내 | `◉ ❯` | 시지프스 바위 모티프 |
| **charizard** | 화산/불꽃 | `✦ ❯` | 불꽃 테마 ASCII 아트 |

### 스킨 로딩 메커니즘

```python
def _build_skin_config(data: Dict[str, Any]) -> SkinConfig:
    """YAML 또는 내장 dict로부터 SkinConfig를 빌드."""
    # 핵심: default 스킨을 베이스로 사용하여 누락된 값을 채움
    default = _BUILTIN_SKINS["default"]
    colors = dict(default.get("colors", {}))
    colors.update(data.get("colors", {}))      # 사용자 값이 기본값을 오버라이드
    spinner = dict(default.get("spinner", {}))
    spinner.update(data.get("spinner", {}))
    branding = dict(default.get("branding", {}))
    branding.update(data.get("branding", {}))
    return SkinConfig(name=data.get("name", "unknown"), colors=colors, ...)
```

**왜 이렇게 만들었는가?** default 스킨을 베이스로 사용하는 상속 패턴 덕분에, 사용자 YAML에서 변경하고 싶은 필드만 지정하면 된다. 나머지는 자동으로 default에서 상속된다.

### 사용자 YAML 스킨 작성법

`~/.hermes/skins/` 디렉토리에 YAML 파일을 만들면 된다:

```yaml
# ~/.hermes/skins/cyberpunk.yaml
name: cyberpunk
description: "네온 사이버펑크 테마"

colors:
  banner_border: "#FF00FF"
  banner_title: "#00FFFF"
  banner_accent: "#FF1493"
  banner_text: "#E0E0E0"
  ui_accent: "#00FFFF"
  prompt: "#00FF00"
  response_border: "#FF00FF"

spinner:
  waiting_faces: ["(>_<)", "(O_O)", "(@_@)"]
  thinking_verbs:
    - "hacking the mainframe"
    - "jacking into the net"
    - "compiling neural code"

branding:
  agent_name: "Cyberpunk Agent"
  prompt_symbol: ">> "
  goodbye: "Flatline. ☠"
```

### 런타임 전환

```bash
# CLI에서 스킨 전환
/skin ares          # 내장 ares 스킨으로 전환
/skin cyberpunk     # 사용자 cyberpunk 스킨으로 전환
/skin default       # 기본 스킨으로 복귀

# config.yaml에서 영구 설정
# display:
#   skin: "ares"
```

```python
# 프로그래밍 방식 전환
from hermes_cli.skin_engine import get_active_skin, set_active_skin

set_active_skin("ares")
skin = get_active_skin()
print(skin.get_branding("agent_name"))  # "Ares Agent"
print(skin.get_color("banner_title"))   # "#C7A96B"
```

---

## 2. 프로필 시스템

### 다중 인스턴스 지원의 설계 원리

Hermes 프로필은 완전히 격리된 다중 인스턴스를 지원한다. 각 프로필은 자체 `HERMES_HOME` 디렉토리를 가지며, 설정, API 키, 메모리, 세션, 스킬, 게이트웨이가 모두 분리된다.

```
~/.hermes/                    # default 프로필
  ├── config.yaml
  ├── .env
  ├── auth.json
  ├── sessions/
  ├── memories/
  └── skills/

~/.hermes/profiles/coder/     # "coder" 프로필
  ├── config.yaml             # 별도 모델/프로바이더 설정
  ├── .env                    # 별도 API 키
  ├── auth.json
  ├── sessions/               # 별도 세션 히스토리
  ├── memories/               # 별도 메모리
  └── skills/                 # 별도 스킬

~/.hermes/profiles/devops/    # "devops" 프로필
  └── ...
```

### _apply_profile_override()의 동작

`hermes_cli/main.py`의 `_apply_profile_override()`는 Hermes 시작의 가장 첫 단계에서 실행된다:

```python
def _apply_profile_override() -> None:
    """모듈 임포트 전에 --profile/-p를 파싱하고 HERMES_HOME을 설정."""
    argv = sys.argv[1:]
    profile_name = None

    # 1. 명시적 -p / --profile 플래그 확인
    for i, arg in enumerate(argv):
        if arg in ("--profile", "-p") and i + 1 < len(argv):
            profile_name = argv[i + 1]
            break
        elif arg.startswith("--profile="):
            profile_name = arg.split("=", 1)[1]
            break

    # 2. 플래그 없으면 ~/.hermes/active_profile 확인
    if profile_name is None:
        active_path = Path.home() / ".hermes" / "active_profile"
        if active_path.exists():
            name = active_path.read_text().strip()
            if name and name != "default":
                profile_name = name

    # 3. 프로필을 찾았으면 HERMES_HOME 환경변수 설정
    if profile_name is not None:
        from hermes_cli.profiles import resolve_profile_env
        hermes_home = resolve_profile_env(profile_name)
        os.environ["HERMES_HOME"] = hermes_home
```

**왜 이렇게 만들었는가?** `HERMES_HOME` 환경변수를 모듈 임포트 **전에** 설정하는 것이 핵심이다. 이후 모든 모듈이 `get_hermes_home()`을 호출할 때 이미 올바른 프로필 경로가 반환된다. argparse보다 먼저 실행되어야 하므로 수동 argv 파싱을 사용한다.

### get_hermes_home() vs display_hermes_home()

```python
# hermes_constants.py

def get_hermes_home() -> Path:
    """코드용 -- 실제 Path 객체 반환"""
    return Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))

def display_hermes_home() -> str:
    """사용자 표시용 -- ~/로 시작하는 읽기 쉬운 문자열"""
    home = get_hermes_home()
    try:
        return "~/" + str(home.relative_to(Path.home()))
    except ValueError:
        return str(home)  # 홈 디렉토리 외부 경로

# 결과 예시:
# default:  "~/.hermes"
# profile:  "~/.hermes/profiles/coder"
# custom:   "/opt/hermes-custom"
```

### 프로필 안전 코드 작성 규칙

1. **절대로** `Path.home() / ".hermes"`를 하드코딩하지 않는다. 항상 `get_hermes_home()` 사용
2. 사용자 표시 문자열에는 `display_hermes_home()` 사용
3. 모듈 수준 상수에서 `get_hermes_home()` 캐싱은 안전 -- `_apply_profile_override()` 이후에 임포트됨
4. 테스트에서 `Path.home()` 모킹 시 `HERMES_HOME` 환경변수도 함께 설정

```python
# 올바른 예
config_path = get_hermes_home() / "config.yaml"

# 잘못된 예 (프로필이 무시됨!)
config_path = Path.home() / ".hermes" / "config.yaml"
```

### 하위 디렉토리 호환성

```python
def get_hermes_dir(new_subpath: str, old_name: str) -> Path:
    """하위 디렉토리의 이전/현재 경로 호환."""
    home = get_hermes_home()
    old_path = home / old_name
    if old_path.exists():
        return old_path           # 기존 설치: 이전 경로 유지
    return home / new_subpath     # 신규 설치: 새 경로 사용
```

**왜 이렇게 만들었는가?** 기존 사용자의 데이터를 마이그레이션 없이 보존하면서, 신규 사용자에게는 정리된 디렉토리 구조를 제공한다.

---

## 3. MCP (Model Context Protocol) 통합

### MCP 서버 연결 구조

MCP는 에이전트에 외부 도구를 연결하는 표준 프로토콜이다. Hermes는 MCP 서버를 연결하여 도구셋을 동적으로 확장할 수 있다.

```
+------------------+     MCP Protocol     +------------------+
|                  | <==================> |                  |
|  Hermes Agent    |   도구 목록 조회       |  MCP Server      |
|                  |   도구 호출 요청       |  (외부 프로세스)   |
|  - tool registry |   결과 반환           |  - 커스텀 도구    |
|  - agent loop    |                      |  - DB 접근       |
|                  |                      |  - API 연동      |
+------------------+                      +------------------+
```

### ACP를 통한 에디터 통합

ACP (Agent Control Protocol)는 에디터와 Hermes를 연결하는 프로토콜이다:

```
에디터 통합 아키텍처
=====================

  VS Code / Zed / JetBrains
       |
    ACP Protocol (acp://copilot)
       |
       v
  Hermes Agent (copilot-acp 프로바이더)
       |
    OpenAI-compatible API
       |
       v
  추론 서버 (GitHub Models / 기타)
```

`auth.py`에 정의된 ACP 프로바이더:

```python
"copilot-acp": ProviderConfig(
    id="copilot-acp",
    name="GitHub Copilot ACP",
    auth_type="external_process",
    inference_base_url="acp://copilot",
    base_url_env_var="COPILOT_ACP_BASE_URL",
),
```

---

## 4. RL 훈련 환경

### Atropos 통합

`environments/hermes_base_env.py`의 `HermesAgentBaseEnv`는 Hermes를 RL (Reinforcement Learning) 훈련 파이프라인에 연결하는 추상 베이스 클래스이다.

```
Atropos RL 훈련 파이프라인
===========================

  데이터셋           Hermes Agent          보상 함수
     |                   |                    |
     v                   v                    v
  get_next_item()   에이전트 루프 실행     compute_reward()
     |               (도구 호출 포함)         |
     v                   |                    v
  format_prompt()       결과 궤적            점수화
     |                   |                    |
     +----->  배치로 묶어 ScoredDataGroup 구성  <-----+
                         |
                         v
                  vLLM / ManagedServer
                  (모델 파라미터 업데이트)
```

### HermesAgentBaseEnv 구조

```python
class HermesAgentBaseEnv(BaseEnv):
    """
    서브클래스가 구현해야 하는 메서드:
        setup()           -- 데이터셋 로드, 상태 초기화
        get_next_item()   -- 다음 데이터 항목 반환
        format_prompt()   -- 데이터 항목을 사용자 메시지로 변환
        compute_reward()  -- 궤적 점수화 (ToolContext 접근 가능)
        evaluate()        -- 주기적 평가
    """
```

### 2단계 운영 모드

1. **Phase 1**: OpenAI 서버 모드 -- 기존 API로 궤적 생성
2. **Phase 2**: vLLM ManagedServer 모드 -- 자체 모델 서빙 및 파라미터 업데이트

### 궤적 압축

대화가 길어지면 궤적도 길어진다. Hermes의 컨텍스트 압축기가 궤적을 요약하여 훈련 데이터의 효율성을 높인다:

```python
# config.yaml
compression:
  enabled: true
  threshold: 0.50       # 컨텍스트 50% 사용 시 압축 시작
  target_ratio: 0.20    # 압축 후 20%로 축소
  protect_last_n: 20    # 최근 20개 메시지는 보존
```

**왜 이렇게 만들었는가?** RL 훈련에서 긴 궤적은 GPU 메모리와 학습 효율 모두에 부정적이다. 도구 호출의 핵심 패턴은 보존하면서 반복적인 출력을 압축하는 것이 Hermes RL 환경의 차별점이다.

---

## 5. 크론 스케줄러 확장

### 예약 작업 정의

`cron/scheduler.py`는 파일 기반 크론 시스템으로, 게이트웨이에서 60초마다 실행된다:

```
크론 실행 흐름
==============

  게이트웨이 백그라운드 스레드 (60초 간격)
       |
       v
  tick() 함수
       |
       v
  ~/.hermes/cron/ 디렉토리 스캔
       |
       v
  due 작업 확인 (croniter로 스케줄 평가)
       |
       v
  에이전트 루프 실행 (작업별 독립 세션)
       |
       v
  결과를 플랫폼으로 전달 (telegram, discord, slack 등)
```

### 전달 플랫폼

```python
_KNOWN_DELIVERY_PLATFORMS = frozenset({
    "telegram", "discord", "slack", "whatsapp", "signal",
    "matrix", "mattermost", "homeassistant", "dingtalk", "feishu",
    "wecom", "sms", "email", "webhook",
})
```

### 크론 작업 정의 예시

```yaml
# ~/.hermes/cron/daily-report.yaml
name: daily-report
schedule: "0 9 * * *"          # 매일 오전 9시
prompt: "오늘의 GitHub 이슈 요약을 생성해주세요."
platform: telegram              # 결과 전달 대상
max_turns: 30                   # 작업당 최대 턴 수
```

### 자연어 스케줄링

Hermes CLI에서 `/cron` 명령으로 자연어 스케줄을 등록할 수 있다:

```
/cron 매일 아침 9시에 이메일 요약 보내줘
/cron 매주 월요일 팀 슬랙에 주간 보고 생성
```

### 잠금 메커니즘

```python
# 파일 기반 잠금으로 중복 실행 방지
# ~/.hermes/cron/.tick.lock
# Unix: fcntl.flock(), Windows: msvcrt.locking()
```

**왜 이렇게 만들었는가?** 여러 프로세스(CLI + 게이트웨이)가 동시에 크론을 트리거할 수 있다. 파일 잠금으로 "정확히 한 번" 실행을 보장한다.

---

## 6. 커스텀 도구 개발 종합 실습

### 도구 개발 워크플로우

```
아이디어 -> 스키마 정의 -> 핸들러 구현 -> 테스트 -> PR 제출

  1. 도구 아이디어 구상
     "날씨 정보를 가져오는 weather 도구를 만들자"

  2. tools/ 디렉토리에 핸들러 작성
     tools/weather_tool.py

  3. JSON 스키마 정의 (함수 호출 인터페이스)
     {
       "name": "get_weather",
       "description": "도시의 현재 날씨 정보 조회",
       "parameters": {
         "type": "object",
         "properties": {
           "city": {"type": "string", "description": "도시 이름"}
         },
         "required": ["city"]
       }
     }

  4. 핸들러 함수 구현 (반드시 JSON 문자열 반환)
     def handle_get_weather(args):
         city = args.get("city")
         # API 호출 로직
         return json.dumps({"city": city, "temp": 22, "condition": "맑음"})

  5. 도구 레지스트리에 등록

  6. 테스트
     pytest tests/tools/test_weather_tool.py

  7. PR 제출
```

### 도구 핸들러 규칙

- 모든 핸들러는 **JSON 문자열을 반환**해야 한다
- 상태 파일은 `get_hermes_home()` 기반 경로에 저장 (프로필 안전)
- 도구 스키마에 파일 경로가 있으면 `display_hermes_home()` 사용

---

## 7. Hermes를 자체 프로젝트에 활용하기

### AIAgent를 라이브러리로 임포트

Hermes의 `AIAgent` 클래스는 독립적으로 임포트하여 사용할 수 있다:

```python
from agent.ai_agent import AIAgent

# 에이전트 초기화
agent = AIAgent(
    model="anthropic/claude-sonnet-4",
    api_key="sk-ant-...",
    base_url="https://api.anthropic.com",
    system_prompt="당신은 코드 리뷰 전문가입니다.",
    tools=["terminal", "read_file", "write_file"],
    max_turns=30,
)

# 단일 질의
response = agent.chat("이 PR의 코드를 리뷰해주세요.")
```

### 임베디드 에이전트 패턴

자체 애플리케이션에 Hermes를 임베딩:

```python
# 웹 서버 내 에이전트
from fastapi import FastAPI
from agent.ai_agent import AIAgent

app = FastAPI()
agent = AIAgent(model="...", api_key="...")

@app.post("/ask")
async def ask(question: str):
    response = agent.chat(question)
    return {"answer": response}
```

### 배치 처리 패턴

여러 작업을 순차적으로 처리:

```python
tasks = [
    "파일 A의 버그를 수정해주세요",
    "테스트 커버리지를 80% 이상으로 올려주세요",
    "README를 업데이트해주세요",
]

for task in tasks:
    agent = AIAgent(model="...", api_key="...")
    result = agent.chat(task)
    print(f"완료: {task[:30]}... -> {result[:100]}")
```

### 게이트웨이 모드 (API 서버)

Hermes 게이트웨이는 메시징 플랫폼과 연결되는 상시 실행 서버이다:

```
게이트웨이 아키텍처
===================

  Telegram ──┐
  Discord ───┤
  Slack ─────┤──> 게이트웨이 서버 ──> AIAgent ──> 추론 API
  WhatsApp ──┤      (run.py)
  Matrix ────┘
       |
       v
  크론 스케줄러 (60초 간격)
```

```bash
# 게이트웨이 실행
hermes gateway

# 환경변수로 플랫폼 설정
export TELEGRAM_BOT_TOKEN="..."
export DISCORD_BOT_TOKEN="..."
```

### 위임 (Delegation) 패턴

부모 에이전트가 자식 에이전트에게 하위 작업을 위임:

```yaml
# config.yaml
delegation:
  model: "google/gemini-3-flash-preview"  # 자식은 저렴한 모델 사용
  provider: "openrouter"
  max_iterations: 50                       # 자식별 독립 예산
```

```
부모 에이전트 (Claude Sonnet 4)
       |
  delegate_task("CSS 스타일 수정")
       |
       v
  자식 에이전트 (Gemini Flash)   <- 저렴한 모델, 독립 예산
       |
    작업 완료 후 결과 반환
       |
       v
  부모가 결과를 통합
```

**왜 이렇게 만들었는가?** 복잡한 작업에서 모든 하위 작업을 비싼 모델로 처리할 필요는 없다. CSS 수정이나 파일 복사 같은 단순 작업은 저렴한 모델에 위임하고, 아키텍처 결정은 고성능 모델이 담당하는 비용 최적화 패턴이다.

---

## 핵심 정리

| 개념 | 핵심 내용 |
|------|----------|
| **스킨 엔진** | YAML 데이터로 CLI 외관 완전 커스터마이징, default 상속 패턴, `/skin` 런타임 전환 |
| **프로필 시스템** | `_apply_profile_override()`가 임포트 전에 `HERMES_HOME` 설정, 완전 격리된 다중 인스턴스 |
| **MCP 통합** | 표준 프로토콜로 외부 도구 연결, ACP로 에디터 통합 |
| **RL 훈련** | `HermesAgentBaseEnv`가 Atropos 연결, 2단계 모드 (API/vLLM), 궤적 압축 |
| **크론 스케줄러** | 파일 기반, 60초 간격 tick, 14개 전달 플랫폼, 파일 잠금으로 중복 방지 |
| **라이브러리 활용** | `AIAgent` 직접 임포트, 임베디드/배치/API 서버 패턴, 위임으로 비용 최적화 |
| **프로필 안전** | `get_hermes_home()` 필수 사용, `Path.home() / ".hermes"` 절대 금지 |
| **도구 개발** | JSON 문자열 반환 필수, 스키마 정의 -> 핸들러 구현 -> 레지스트리 등록 |
