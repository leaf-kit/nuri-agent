# 강좌 06: 게이트웨이와 멀티플랫폼

> **이 강좌에서 배우는 것**
>
> - GatewayRunner가 단일 프로세스에서 다중 플랫폼을 서빙하는 구조를 이해한다
> - 플랫폼 어댑터의 공통 인터페이스와 각 플랫폼의 특성을 파악한다
> - 메시지가 수신되어 에이전트 응답이 전달되기까지의 전체 경로를 추적한다
> - CLI와 게이트웨이 간 슬래시 명령어 공유 메커니즘을 학습한다
> - Telegram 봇 구축의 실전 과정을 단계별로 익힌다
> - v0.7.0의 프로덕션 안정성 개선 사항을 살펴본다

---

## 1. 게이트웨이 아키텍처

### GatewayRunner의 역할

`GatewayRunner`는 Hermes Agent의 게이트웨이 프로세스 전체를 관리하는 중앙 컨트롤러다. 단일 프로세스 내에서 여러 메시징 플랫폼 어댑터를 동시에 실행한다.

```
게이트웨이 아키텍처 개요:

+------------------------------------------------------------------+
|                      GatewayRunner                                |
|                                                                  |
|  +------------------+  +------------------+  +------------------+|
|  | TelegramAdapter  |  | DiscordAdapter   |  | SlackAdapter     ||
|  | (polling/webhook)|  | (websocket)      |  | (websocket)      ||
|  +--------+---------+  +--------+---------+  +--------+---------+|
|           |                      |                     |         |
|           +----------------------+---------------------+         |
|                                  |                               |
|                          +-------v--------+                      |
|                          | SessionStore   |                      |
|                          | (세션 관리)     |                      |
|                          +-------+--------+                      |
|                                  |                               |
|                          +-------v--------+                      |
|                          | AIAgent        |                      |
|                          | (에이전트 실행) |                      |
|                          +-------+--------+                      |
|                                  |                               |
|                          +-------v--------+                      |
|                          | DeliveryRouter |                      |
|                          | (응답 라우팅)   |                      |
|                          +----------------+                      |
+------------------------------------------------------------------+
```

### 초기화 체인

`gateway/run.py`의 시작 과정은 엄격한 순서를 따른다:

```
초기화 순서:

1. SSL 인증서 자동 탐지
   _ensure_ssl_certs()
   ├── 환경변수 SSL_CERT_FILE 확인
   ├── Python 내장 경로 확인
   ├── certifi 패키지 시도
   └── OS별 일반 경로 탐색 (8개 후보)

2. 환경변수 로드
   load_hermes_dotenv()
   └── ~/.hermes/.env + 프로젝트 .env

3. config.yaml 브리징
   ├── terminal.* → TERMINAL_* 환경변수
   ├── auxiliary.* → AUXILIARY_* 환경변수
   ├── agent.max_turns → HERMES_MAX_ITERATIONS
   ├── timezone → HERMES_TIMEZONE
   └── security.redact_secrets → HERMES_REDACT_SECRETS

4. GatewayRunner 생성
   ├── 프리필 메시지 로드
   ├── 에페메럴 시스템 프롬프트 로드
   ├── 추론 설정 로드
   ├── 프로바이더 라우팅 설정
   ├── SessionStore 생성
   ├── DeliveryRouter 생성
   ├── SessionDB 초기화
   ├── PairingStore 생성
   └── HookRegistry 생성

5. 어댑터 시작
   ├── _create_adapter(Platform.TELEGRAM)
   ├── _create_adapter(Platform.DISCORD)
   ├── _create_adapter(Platform.SLACK)
   └── ...각 플랫폼별 connect()
```

### SSL 인증서 자동 탐지

```python
def _ensure_ssl_certs() -> None:
    """NixOS 등 비표준 시스템을 위한 SSL 인증서 자동 탐지."""
    if "SSL_CERT_FILE" in os.environ:
        return

    # 1. Python 내장 경로
    paths = ssl.get_default_verify_paths()

    # 2. certifi 패키지
    try:
        import certifi
        os.environ["SSL_CERT_FILE"] = certifi.where()
        return
    except ImportError:
        pass

    # 3. 8개 OS별 후보 경로
    for candidate in (
        "/etc/ssl/certs/ca-certificates.crt",          # Debian/Ubuntu
        "/etc/pki/tls/certs/ca-bundle.crt",            # RHEL/CentOS 7
        "/etc/ssl/cert.pem",                            # Alpine / macOS
        "/opt/homebrew/etc/openssl@1.1/cert.pem",       # macOS Homebrew ARM
        ...
    ):
        if os.path.exists(candidate):
            os.environ["SSL_CERT_FILE"] = candidate
            return
```

**왜 이렇게 만들었는가?** NixOS, Alpine, 일부 Docker 이미지에서는 Python이 CA 인증서를 찾지 못해 HTTPS 연결이 실패한다. Discord, Telegram 등의 API는 모두 HTTPS이므로, 게이트웨이 시작 전에 반드시 인증서 경로를 확보해야 한다. 이 함수는 모든 HTTP 라이브러리 import 전에 실행된다.

### config.yaml 브리징

config.yaml의 구조화된 설정을 환경변수로 변환하는 과정:

```python
_terminal_env_map = {
    "backend": "TERMINAL_ENV",
    "cwd": "TERMINAL_CWD",
    "timeout": "TERMINAL_TIMEOUT",
    "docker_image": "TERMINAL_DOCKER_IMAGE",
    "ssh_host": "TERMINAL_SSH_HOST",
    ...
}
for _cfg_key, _env_var in _terminal_env_map.items():
    if _cfg_key in _terminal_cfg:
        os.environ[_env_var] = str(_terminal_cfg[_cfg_key])
```

**왜 이렇게 만들었는가?** Hermes Agent의 내부 모듈들은 `os.getenv()`로 설정을 읽는다. config.yaml은 사용자가 설정을 한 곳에서 관리하는 "단일 진실의 원천(single source of truth)"이다. 브리징 레이어가 두 세계를 연결한다. `.env`의 값이 이미 존재하면 config.yaml이 덮어쓰지 않는다(`.env` 우선).

---

## 2. 플랫폼 어댑터 패턴

### 공통 인터페이스

모든 어댑터는 `BasePlatformAdapter`를 상속한다:

```python
# gateway/platforms/base.py (개념적 구조)
class BasePlatformAdapter:
    # 필수 메서드
    def connect(self) -> bool: ...
    def disconnect(self): ...
    def send(self, chat_id, text, ...) -> SendResult: ...
    def send_typing(self, chat_id): ...
    def send_image(self, chat_id, image_url, caption) -> SendResult: ...
    def get_chat_info(self, chat_id) -> dict: ...

    # 선택적 메서드 (기본 스텁 제공)
    def send_document(self, chat_id, path, caption): ...
    def send_voice(self, chat_id, path): ...
    def send_video(self, chat_id, path, caption): ...
    def send_animation(self, chat_id, path, caption): ...

    # 공통 헬퍼
    def build_source(self, ...) -> SessionSource: ...
    def handle_message(self, event: MessageEvent): ...
```

### 각 플랫폼별 특성과 제약

```
지원 플랫폼 현황 (20+ 어댑터):

+---------------+----------------+------------------+------------------+
| 플랫폼        | 연결 방식      | 메시지 제한       | 특이사항          |
+===============+================+==================+==================+
| Telegram      | Polling/       | 4096자            | Bot API, 리치    |
|               | Webhook        |                  | 미디어 지원       |
+---------------+----------------+------------------+------------------+
| Discord       | WebSocket      | 2000자            | 슬래시 커맨드,   |
|               | (Gateway)      |                  | 임베드 지원       |
+---------------+----------------+------------------+------------------+
| Slack         | WebSocket      | 40000자           | Block Kit,       |
|               | (Socket Mode)  |                  | 스레드 지원       |
+---------------+----------------+------------------+------------------+
| WhatsApp      | Bridge         | ~65000자          | E2E 암호화,      |
|               | (whatsmeow)    |                  | LID/JID 변환     |
+---------------+----------------+------------------+------------------+
| Signal        | Bridge         | ~2000자           | E2E 암호화,      |
|               | (signal-cli)   |                  | UUID 기반        |
+---------------+----------------+------------------+------------------+
| Email         | IMAP/SMTP      | 무제한            | 스레드 보존,     |
|               |                |                  | 첨부파일 지원    |
+---------------+----------------+------------------+------------------+
| Matrix        | HTTP API       | 무제한            | 분산 프로토콜,   |
|               |                |                  | E2E 암호화 옵션  |
+---------------+----------------+------------------+------------------+
| DingTalk      | WebSocket      | 플랫폼 제한       | 기업 메신저      |
+---------------+----------------+------------------+------------------+
| Feishu        | WebSocket      | 플랫폼 제한       | Lark (바이트댄스)|
+---------------+----------------+------------------+------------------+
| WeCom         | HTTP Callback  | 플랫폼 제한       | 기업용 WeChat    |
+---------------+----------------+------------------+------------------+
| Mattermost    | WebSocket      | 16383자           | 오픈소스 Slack   |
+---------------+----------------+------------------+------------------+
| SMS           | Twilio API     | ~1600자           | 문자 전용        |
+---------------+----------------+------------------+------------------+
| Webhook       | HTTP POST      | 무제한            | 범용 통합        |
+---------------+----------------+------------------+------------------+
| Home Assistant| REST API       | 무제한            | IoT 통합         |
+---------------+----------------+------------------+------------------+
| API Server    | REST API       | 무제한            | 프로그래밍 접근  |
+---------------+----------------+------------------+------------------+
```

### 어댑터가 따라야 하는 핵심 패턴

`ADDING_A_PLATFORM.md`에 정의된 16가지 통합 포인트:

```
새 플랫폼 추가 시 체크리스트 (16단계):

 1. [Core]     gateway/platforms/<platform>.py  -- 어댑터 구현
 2. [Config]   gateway/config.py               -- Platform enum 추가
 3. [Factory]  gateway/run.py                  -- _create_adapter() 추가
 4. [Auth]     gateway/run.py                  -- 인가 맵 등록
 5. [Session]  gateway/session.py              -- 세션 소스 필드
 6. [Prompt]   agent/prompt_builder.py         -- PLATFORM_HINTS 등록
 7. [Toolset]  toolsets.py                     -- 도구셋 등록
 8. [Cron]     cron/scheduler.py               -- 크론 배달 등록
 9. [Send]     tools/send_message_tool.py      -- 메시지 전송 도구
10. [Schema]   tools/cronjob_tools.py          -- 크론잡 스키마
11. [Dir]      gateway/channel_directory.py    -- 채널 디렉토리
12. [Status]   hermes_cli/status.py            -- 상태 표시
13. [Wizard]   hermes_cli/gateway.py           -- 설정 마법사
14. [Redact]   agent/redact.py                 -- 식별자 마스킹
15. [Docs]     README.md, website/docs/...     -- 문서화
16. [Tests]    tests/gateway/test_<platform>.py -- 테스트
```

**왜 이렇게 만들었는가?** 단순히 어댑터 하나를 만드는 것으로는 완전한 통합이 되지 않는다. 크론 배달이 안 되거나, 상태 표시에 빠지거나, 인가가 적용되지 않는 등의 문제가 발생한다. 16개 통합 포인트를 명시함으로써 "빠뜨린 것"을 체계적으로 방지한다.

---

## 3. 메시지 라우팅과 세션 관리

### 메시지 수신부터 응답 전달까지

```
메시지 라우팅 전체 경로:

[사용자] --메시지--> [플랫폼 API]
                         |
                         v
               [PlatformAdapter]
               handle_message(event)
                         |
                         v
               [GatewayRunner]
               +--------------------+
               | 1. 인가 확인        |
               |    _is_user_authorized()
               | 2. 세션 키 생성     |
               |    build_session_key()
               | 3. 중복 실행 방지   |
               |    _AGENT_PENDING_SENTINEL
               | 4. 에이전트 캐시    |
               |    _agent_cache     |
               | 5. 에이전트 실행    |
               |    AIAgent.run()    |
               +--------------------+
                         |
                         v
               [DeliveryRouter]
               +--------------------+
               | 미디어 추출         |
               | 메시지 분할         |
               | 타이핑 표시         |
               +--------------------+
                         |
                         v
               [PlatformAdapter]
               send(chat_id, text)
                         |
                         v
               [플랫폼 API] --응답--> [사용자]
```

### 레이스 컨디션 방지: AGENT_PENDING_SENTINEL

```python
_AGENT_PENDING_SENTINEL = object()
```

사용자가 빠르게 메시지를 연속 전송하면, 같은 세션에서 두 에이전트가 동시에 실행될 수 있다. `_AGENT_PENDING_SENTINEL`은 에이전트 생성 **전에** 즉시 슬롯을 점유하여 이를 방지한다:

```
레이스 컨디션 방지 시퀀스:

  메시지1 수신 ─┬─ running_agents[key] = SENTINEL  (즉시)
                │  ... await agent 생성 ...
                │  running_agents[key] = agent
                │
  메시지2 수신 ─┴─ running_agents[key] 확인
                   → SENTINEL 발견 → 큐에 대기
```

**왜 이렇게 만들었는가?** `await` 키워드 사이의 비동기 갭에서 두 번째 메시지가 "에이전트 미실행" 상태를 보고 새 에이전트를 시작할 수 있다. 센티넬 값으로 이 갭을 메운다.

### SessionStore의 역할

```python
self.session_store = SessionStore(
    self.config.sessions_dir,
    self.config,
    has_active_processes_fn=lambda key:
        process_registry.has_active_for_session(key),
)
```

SessionStore는:
- 세션 키 → 세션 메타데이터 매핑 관리
- 활성 프로세스 확인 (세션 리셋 시 안전성 보장)
- 세션별 메시지 히스토리 유지
- 컨텍스트 정보(플랫폼, 사용자 ID, 채팅 ID) 관리

### 에이전트 캐시

```python
# Key: session_key, Value: (AIAgent, config_signature_str)
self._agent_cache: Dict[str, tuple] = {}
```

동일 세션의 연속 메시지에 대해 AIAgent 인스턴스를 캐시한다.

**왜 이렇게 만들었는가?** 캐시 없이 매 메시지마다 새 AIAgent를 생성하면:
1. 시스템 프롬프트(메모리 포함)를 매번 재조립
2. Anthropic 프롬프트 캐싱의 접두사 캐시가 무효화
3. 캐시 미스로 인한 비용 ~10배 증가

캐시된 에이전트는 동일한 시스템 프롬프트 접두사를 유지하므로 캐시 적중률이 극대화된다.

---

## 4. 슬래시 명령어 통합

### CLI와 게이트웨이 간 명령어 공유

Hermes Agent의 슬래시 명령어(`/model`, `/compress`, `/reset` 등)는 CLI와 게이트웨이 양쪽에서 동작한다. `CommandDef` 구조체로 명령어의 실행 환경을 분기한다:

```
명령어 실행 분기:

  [사용자 입력: "/model gpt-4"]
           |
           v
  게이트웨이에서 수신?
           |yes               |no (CLI)
           v                  v
  gateway_only 명령?      cli_only 명령?
  (예: /pair)             (예: /gateway)
           |yes    |no          |yes    |no
           v       v            v       v
  게이트웨이   양쪽에서      CLI에서   양쪽에서
  에서만 실행  실행 가능     만 실행   실행 가능
```

### 비가용 스킬 안내

사용자가 비활성화되거나 미설치된 스킬을 명령어로 호출하면, 안내 메시지를 제공한다:

```python
def _check_unavailable_skill(command_name: str) -> str | None:
    # 비활성화된 스킬
    if name in disabled:
        return (
            f"The **{command_name}** skill is installed but disabled.\n"
            f"Enable it with: `hermes skills config`"
        )
    # 미설치 옵션 스킬
    if name in optional_skills:
        return (
            f"The **{command_name}** skill is available but not installed.\n"
            f"Install it with: `hermes skills install {install_path}`"
        )
```

---

## 5. 크론 스케줄러

### 예약 작업의 플랫폼 전달

크론 작업이 실행된 결과를 특정 플랫폼의 특정 채팅으로 전달하는 구조:

```
크론 작업 실행 흐름:

  [cron/scheduler.py]
  cronjob(action="create",
          deliver="telegram",
          chat_id="12345",
          schedule="0 9 * * *",
          task="오늘의 뉴스 요약")
           |
           v
  [스케줄 트리거: 매일 09:00]
           |
           v
  [AIAgent 실행]
  "오늘의 뉴스 요약" 작업 수행
           |
           v
  [_deliver_result()]
  platform_map = {
      "telegram": Platform.TELEGRAM,
      "discord": Platform.DISCORD,
      "slack": Platform.SLACK,
      "whatsapp": Platform.WHATSAPP,
      "signal": Platform.SIGNAL,
      ...
  }
           |
           v
  [해당 플랫폼 어댑터]
  send(chat_id="12345", text=결과)
```

크론 작업은 "cron" 플랫폼 힌트를 받아 자율적으로 실행된다:

```python
PLATFORM_HINTS["cron"] = (
    "You are running as a scheduled cron job. There is no user present -- you "
    "cannot ask questions, request clarification, or wait for follow-up. Execute "
    "the task fully and autonomously..."
)
```

---

## 6. Telegram 봇 구축 실습

### Step 1: BotFather로 봇 생성

```
1. Telegram에서 @BotFather 대화 시작
2. /newbot 명령 전송
3. 봇 이름과 username 설정
4. API 토큰 수령 (예: 123456:ABC-DEF1234...)
```

### Step 2: 환경변수 설정

```bash
# ~/.hermes/.env에 추가
TELEGRAM_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# 허용할 사용자 ID (선택사항, 보안 권장)
TELEGRAM_ALLOWED_USERS=your_user_id

# 또는 모든 사용자 허용 (주의: 공개 봇이 됨)
# TELEGRAM_ALLOW_ALL_USERS=true
```

### Step 3: config.yaml 설정

```yaml
# ~/.hermes/config.yaml
model:
  default: anthropic/claude-sonnet-4-20250514

terminal:
  backend: local

# Telegram 특화 설정 (선택)
platforms:
  telegram:
    enabled: true
```

### Step 4: 게이트웨이 시작

```bash
# 방법 1: CLI에서 시작
hermes --gateway

# 방법 2: 직접 실행
python -m gateway.run
```

### Step 5: 디버깅

```bash
# 로그 확인
tail -f ~/.hermes/logs/gateway.log

# 연결 상태 확인
hermes status

# 테스트 메시지 전송
# Telegram에서 봇에게 "Hello" 전송
```

### Step 6: 인가 확인

```python
# gateway/run.py의 인가 구조
platform_env_map = {
    Platform.TELEGRAM: "TELEGRAM_ALLOWED_USERS",
    Platform.DISCORD: "DISCORD_ALLOWED_USERS",
    Platform.SLACK: "SLACK_ALLOWED_USERS",
    ...
}
platform_allow_all_map = {
    Platform.TELEGRAM: "TELEGRAM_ALLOW_ALL_USERS",
    Platform.DISCORD: "DISCORD_ALLOW_ALL_USERS",
    ...
}
```

`TELEGRAM_ALLOWED_USERS`에 사용자 ID를 쉼표로 구분하여 나열하면, 해당 사용자만 봇과 대화할 수 있다. 설정하지 않으면 모든 메시지가 차단된다(기본 보안).

### WhatsApp 특수 사항: LID/JID 변환

WhatsApp은 전화번호 기반 JID(Jabber ID)와 LID(Linked ID)를 혼용한다:

```python
def _normalize_whatsapp_identifier(value: str) -> str:
    """WhatsApp JID/LID를 안정적인 숫자 식별자로 정규화."""
    return (
        str(value or "")
        .strip()
        .replace("+", "", 1)     # + 제거
        .split(":", 1)[0]        # LID 구분자 제거
        .split("@", 1)[0]        # JID 도메인 제거
    )

def _expand_whatsapp_auth_aliases(identifier: str) -> set:
    """WhatsApp 전화번호/LID 별칭을 매핑 파일로 해소."""
    # lid-mapping-{number}.json 파일 체인 탐색
    # 같은 사용자의 여러 식별자를 연결
```

---

## 7. 게이트웨이 강화 (v0.7.0)

### 레이스 컨디션 수정

v0.7.0에서 수정된 핵심 레이스 컨디션:

```
문제: 비동기 갭에서 중복 에이전트 생성

  [수정 전]
  메시지1 → check running_agents → 없음 → await create_agent → 등록
  메시지2 → check running_agents → 없음 (아직 생성 중!) → 중복 생성!

  [수정 후]
  메시지1 → running_agents[key] = SENTINEL → await create_agent → 교체
  메시지2 → check running_agents → SENTINEL 발견 → 큐에 대기
```

### 승인 라우팅

위험한 명령어 실행 시 사용자 승인을 요청하는 메커니즘:

```python
# 게이트웨이 시작 시 자동 활성화
os.environ["HERMES_EXEC_ASK"] = "1"

# 승인 대기 중인 세션 추적
self._pending_approvals: Dict[str, Dict[str, Any]] = {}
```

CLI에서는 터미널에서 직접 승인하지만, 게이트웨이에서는 메시징 플랫폼을 통해 승인/거부를 받는다.

### 플러드 제어

빠르게 연속 메시지를 보내는 사용자에 대한 보호:

```
플러드 제어 흐름:

  [메시지 연속 수신]
       |
       v
  에이전트 이미 실행 중?
       |yes                |no
       v                   v
  메시지를 큐에 저장     정상 처리
  _pending_messages[key]
       |
       v
  에이전트 완료 후
  큐에서 다음 메시지 꺼내기
  _dequeue_pending_text()
```

미디어 전용 메시지(캡션 없는 사진)도 올바르게 처리:

```python
def _build_media_placeholder(event) -> str:
    """미디어 전용 이벤트의 텍스트 플레이스홀더 생성."""
    for url in media_urls:
        if mtype.startswith("image/"):
            parts.append(f"[User sent an image: {url}]")
        elif mtype.startswith("audio/"):
            parts.append(f"[User sent audio: {url}]")
        else:
            parts.append(f"[User sent a file: {url}]")
```

### 실패한 플랫폼의 백그라운드 재연결

```python
# 연결 실패한 플랫폼 추적
self._failed_platforms: Dict[Platform, Dict[str, Any]] = {}
# 구조: {"config": platform_config, "attempts": int, "next_retry": float}
```

지수 백오프 + 지터로 자동 재연결을 시도한다. 게이트웨이 전체가 아닌 개별 플랫폼만 재시작되므로, Discord가 다운되어도 Telegram은 계속 동작한다.

### 모델 폴백

```python
# 주 모델이 rate-limited일 때 자동 폴백
self._effective_model: Optional[str] = None
self._effective_provider: Optional[str] = None

# 세션별 모델 오버라이드 (/model 명령)
self._session_model_overrides: Dict[str, Dict[str, str]] = {}
```

주 모델이 속도 제한에 걸리면 설정된 폴백 모델로 자동 전환하고, 주 모델이 복구되면 다시 돌아온다.

---

## 핵심 정리

1. **단일 프로세스 다중 플랫폼**: GatewayRunner가 하나의 프로세스에서 Telegram, Discord, Slack, WhatsApp 등을 동시에 서빙한다

2. **16가지 통합 포인트**: 새 플랫폼을 추가하려면 어댑터뿐 아니라 인가, 프롬프트 힌트, 도구셋, 크론, 문서 등 16개 지점을 모두 업데이트해야 한다

3. **초기화 순서 엄수**: SSL -> .env -> config.yaml 브리징 -> GatewayRunner 생성 -> 어댑터 시작. 특히 SSL 설정은 모든 HTTP 라이브러리 import 전에 완료해야 한다

4. **AGENT_PENDING_SENTINEL**: 비동기 갭의 레이스 컨디션을 방지하는 센티넬 패턴. 에이전트 생성 전에 슬롯을 즉시 점유한다

5. **에이전트 캐시**: 세션별 AIAgent를 캐시하여 프롬프트 캐싱 적중률을 극대화하고 비용을 ~10배 절감한다

6. **config.yaml 브리징**: 구조화된 YAML 설정을 환경변수로 변환하여 기존 `os.getenv()` 기반 코드와 호환성을 유지한다

7. **플랫폼 독립적 복원력**: 개별 플랫폼 장애가 다른 플랫폼에 영향을 주지 않으며, 지수 백오프로 자동 재연결한다
