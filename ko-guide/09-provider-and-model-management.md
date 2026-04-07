# 강좌 09: 프로바이더와 모델 관리

> **이 강좌에서 배우는 것**
>
> - Hermes가 20개 이상의 추론 프로바이더를 단일 인터페이스로 추상화하는 방법
> - 자격 증명이 해석되는 정확한 우선순위 체인 (환경변수 -> config.yaml -> OAuth)
> - 동일 프로바이더에 여러 API 키를 풀링하여 장애 복원력을 높이는 v0.7.0 자격 증명 풀
> - models.dev 레지스트리를 활용한 자동 컨텍스트 길이 감지
> - 프로바이더 장애 시 자동 폴백 전략과 429 레이트 리밋 처리
> - OpenRouter 라우팅 최적화와 Anthropic 프롬프트 캐싱 비용 절감

---

## 1. 멀티 프로바이더 아키텍처

Hermes Agent의 핵심 설계 원칙 중 하나는 **프로바이더 독립성**이다. 모든 추론 프로바이더를 OpenAI 호환 Chat Completions API로 추상화하여, 사용자가 프로바이더를 바꿔도 에이전트 코드는 변경할 필요가 없다.

### 프로바이더 레지스트리

`hermes_cli/auth.py`의 `PROVIDER_REGISTRY`가 모든 프로바이더를 정의한다:

```python
@dataclass
class ProviderConfig:
    id: str
    name: str
    auth_type: str  # "oauth_device_code", "oauth_external", "api_key"
    portal_base_url: str = ""
    inference_base_url: str = ""
    client_id: str = ""
    scope: str = ""
    api_key_env_vars: tuple = ()      # 환경변수 검색 순서
    base_url_env_var: str = ""        # 베이스 URL 오버라이드용 환경변수
```

**왜 이렇게 만들었는가?** `ProviderConfig`를 데이터클래스로 정의한 이유는 새 프로바이더를 추가할 때 코드 로직을 수정하지 않고 레지스트리에 항목만 추가하면 되기 때문이다. 인증 방식(`auth_type`)을 필드로 분리하여 OAuth와 API 키 프로바이더를 동일한 구조로 처리한다.

### 지원 프로바이더 목록과 특성

```
+-------------------+------------------+---------------------------+
| 프로바이더         | 인증 방식         | 특성                       |
+-------------------+------------------+---------------------------+
| Nous Portal       | OAuth PKCE       | 자체 추론 서버, 에이전트 키 발급 |
| OpenAI Codex      | OAuth External   | ChatGPT 백엔드 API 활용    |
| GitHub Copilot    | API Key / gh CLI | GH 토큰 자동 탐지          |
| Copilot ACP       | External Process | 에디터 통합용 ACP 프로토콜    |
| Gemini            | API Key          | Google AI Studio          |
| Z.AI / GLM        | API Key          | 다중 엔드포인트 자동 탐지     |
| Kimi / Moonshot   | API Key          | sk-kimi- 접두사 자동 라우팅  |
| MiniMax           | API Key          | Anthropic 호환 API 표면    |
| Anthropic         | API Key          | 네이티브 프롬프트 캐싱 지원   |
| DeepSeek          | API Key          | 코딩 특화 모델              |
| Alibaba DashScope | API Key          | 글로벌/중국 엔드포인트       |
| Hugging Face      | API Key (HF_TOKEN)| 라우터 기반 모델 접근       |
| AI Gateway        | API Key          | Vercel AI Gateway         |
| OpenCode Zen/Go   | API Key          | GLM/Kimi/MiniMax 통합     |
| Kilo Code         | API Key          | 게이트웨이 기반             |
+-------------------+------------------+---------------------------+
```

### Z.AI 엔드포인트 자동 탐지

Z.AI는 과금 플랜(일반/코딩)과 리전(글로벌/중국)에 따라 4개의 엔드포인트가 있다. Hermes는 설정 시 자동으로 모든 엔드포인트를 프로브하여 작동하는 것을 선택한다:

```python
ZAI_ENDPOINTS = [
    ("global",        "https://api.z.ai/api/paas/v4",             "glm-5",   "Global"),
    ("cn",            "https://open.bigmodel.cn/api/paas/v4",      "glm-5",   "China"),
    ("coding-global", "https://api.z.ai/api/coding/paas/v4",       "glm-4.7", "Global (Coding)"),
    ("coding-cn",     "https://open.bigmodel.cn/api/coding/paas/v4","glm-4.7", "China (Coding)"),
]
```

**왜 이렇게 만들었는가?** 사용자가 어떤 Z.AI 플랜을 가지고 있는지 모르기 때문에, 설정 시 프로브를 수행하여 "Insufficient balance" 오류를 미리 방지한다. 이는 중국 개발자를 위한 사용자 경험 최적화이다.

---

## 2. 자격 증명 해석 체인

`resolve_provider()` 함수는 어떤 프로바이더를 사용할지 결정하는 중앙 허브다. 해석은 명확한 우선순위 체인을 따른다:

```
자격 증명 해석 순서
====================

  [1] 명시적 API 키/URL (--api-key, --base-url CLI 플래그)
       |
       v
  [2] 환경변수 (OPENROUTER_API_KEY, ANTHROPIC_API_KEY 등)
       |
       v
  [3] config.yaml의 providers 섹션
       |
       v
  [4] OAuth 토큰 (auth.json에 저장된 Nous Portal / Codex 토큰)
       |
       v
  [5] 자격 증명 풀 (auth.json의 credential_pool)
       |
       v
  [6] 플레이스홀더 감지 및 거부
```

### 플레이스홀더 감지

Hermes는 설정 파일에서 실수로 남긴 플레이스홀더 값을 자동으로 감지한다:

```python
_PLACEHOLDER_SECRET_VALUES = {
    "*", "**", "***", "changeme", "your_api_key",
    "your-api-key", "placeholder", "example", "dummy", "null", "none",
}

def has_usable_secret(value: Any, *, min_length: int = 4) -> bool:
    if not isinstance(value, str):
        return False
    cleaned = value.strip()
    if len(cleaned) < min_length:
        return False
    if cleaned.lower() in _PLACEHOLDER_SECRET_VALUES:
        return False
    return True
```

**왜 이렇게 만들었는가?** 튜토리얼을 따라 하다 `your_api_key`를 그대로 두는 실수가 매우 빈번하다. 4자 미만의 문자열도 거부하여 빈 문자열이나 단순 오타가 API 호출로 이어지지 않게 한다.

### Nous Portal OAuth PKCE 흐름

Nous Portal은 Device Code + PKCE 방식의 OAuth를 사용한다:

```
사용자              Hermes CLI            Nous Portal
  |                    |                      |
  |  hermes model      |                      |
  |------------------->|                      |
  |                    |  POST /device/code   |
  |                    |--------------------->|
  |                    |  device_code,        |
  |                    |  user_code,          |
  |                    |  verification_uri    |
  |                    |<---------------------|
  |  브라우저 열림      |                      |
  |<-------------------|                      |
  |  코드 입력 & 승인   |                      |
  |------------------------------------------>|
  |                    |  POST /token         |
  |                    |  (device_code +      |
  |                    |   code_verifier)     |
  |                    |--------------------->|
  |                    |  access_token,       |
  |                    |  refresh_token       |
  |                    |<---------------------|
  |                    |                      |
  |                    |  POST /mint-key      |
  |                    |  (access_token)      |
  |                    |--------------------->|
  |                    |  agent_key (30분 TTL) |
  |                    |<---------------------|
```

핵심 상수:
- `DEFAULT_AGENT_KEY_MIN_TTL_SECONDS = 1800` (30분) -- 에이전트 키 최소 유효 시간
- `ACCESS_TOKEN_REFRESH_SKEW_SECONDS = 120` -- 만료 2분 전에 갱신 시작
- `DEVICE_AUTH_POLL_INTERVAL_CAP_SECONDS = 1` -- 디바이스 코드 폴링 최대 간격

### 인증 상태 저장소

모든 인증 상태는 `~/.hermes/auth.json`에 저장되며, 크로스 프로세스 파일 잠금으로 보호된다:

```python
@contextmanager
def _auth_store_lock(timeout_seconds=AUTH_LOCK_TIMEOUT_SECONDS):
    """크로스 프로세스 어드바이저리 잠금. 재진입 가능."""
    # Unix: fcntl.flock(), Windows: msvcrt.locking()
    # 재진입: 같은 스레드가 이미 잠금을 보유하면 바로 진행
```

---

## 3. 자격 증명 풀 (v0.7.0)

`agent/credential_pool.py`의 `CredentialPool`은 동일 프로바이더에 여러 API 키를 등록하고 자동으로 로테이션하는 시스템이다.

### 풀 전략

```python
STRATEGY_FILL_FIRST  = "fill_first"    # 첫 번째 키를 우선 사용 (기본값)
STRATEGY_ROUND_ROBIN = "round_robin"   # 순환 사용
STRATEGY_RANDOM      = "random"        # 무작위 선택
STRATEGY_LEAST_USED  = "least_used"    # 사용 횟수가 적은 키 우선
```

### PooledCredential 구조

```python
@dataclass
class PooledCredential:
    provider: str
    id: str                              # 고유 식별자 (6자 hex)
    label: str                           # 표시 이름 (이메일 등)
    auth_type: str                       # "oauth" | "api_key"
    priority: int                        # 선택 우선순위
    access_token: str                    # API 키 또는 액세스 토큰
    request_count: int = 0               # 누적 요청 수 (least_used용)
    last_status: Optional[str] = None    # "ok" | "exhausted"
    last_error_code: Optional[int] = None # 마지막 HTTP 에러 코드
```

### 자동 교체 흐름

```
API 요청 실패 (401/402/429)
         |
         v
mark_exhausted_and_rotate()
         |
    +----+----+
    |         |
  429       401/402
    |         |
    v         v
 1시간      24시간
 쿨다운     쿨다운
    |         |
    +----+----+
         |
         v
다음 가용 자격 증명 선택
(전략에 따라 fill_first/round_robin/random/least_used)
         |
         v
가용 키가 없으면 -> 폴백 프로바이더로 전환
```

```python
# 쿨다운 상수
EXHAUSTED_TTL_429_SECONDS = 60 * 60          # 429: 1시간 (레이트 리밋은 빨리 리셋)
EXHAUSTED_TTL_DEFAULT_SECONDS = 24 * 60 * 60 # 402 등: 24시간 (과금 문제는 오래 걸림)
```

### 스레드 안전성

`CredentialPool`은 내부적으로 `threading.Lock`을 사용하여 모든 상태 변경이 스레드 안전하다:

```python
class CredentialPool:
    def __init__(self, provider, entries):
        self._entries = sorted(entries, key=lambda e: e.priority)
        self._lock = threading.Lock()   # 모든 선택/갱신은 잠금 하에 수행

    def select(self):
        with self._lock:
            return self._select_unlocked()

    def mark_used(self, entry_id=None):
        with self._lock:
            # request_count 증가
```

**왜 이렇게 만들었는가?** 게이트웨이 모드에서는 여러 메시징 플랫폼의 요청이 동시에 들어올 수 있다. 스레드 안전한 풀 관리 없이는 동일 키를 동시에 소진시키거나 레이스 컨디션이 발생한다.

---

## 4. 모델 메타데이터와 컨텍스트 길이

### model_metadata.py의 역할

`agent/model_metadata.py`는 모델 이름으로부터 컨텍스트 길이, 토큰 추정치 등을 가져오는 유틸리티 모듈이다.

```
모델 메타데이터 해석 순서
=========================

  [1] models.dev 레지스트리 (4000+ 모델, 109+ 프로바이더)
       |  실패 시
       v
  [2] OpenRouter 라이브 API (/models 엔드포인트)
       |  실패 시
       v
  [3] 내장 DEFAULT_CONTEXT_LENGTHS (패턴 매칭)
       |  실패 시
       v
  [4] 컨텍스트 프로브 (128K -> 64K -> 32K -> 16K -> 8K 단계적 축소)
       |  실패 시
       v
  [5] 기본값: 128,000 토큰
```

### models.dev 레지스트리

`agent/models_dev.py`가 models.dev 통합을 담당한다:

```python
@dataclass
class ModelInfo:
    id: str
    name: str
    family: str
    provider_id: str
    reasoning: bool = False          # 추론 능력
    tool_call: bool = False          # 도구 호출 지원
    attachment: bool = False         # 이미지/파일 첨부 (비전)
    context_window: int = 0          # 컨텍스트 윈도우 크기
    max_output: int = 0              # 최대 출력 토큰
    cost_input: float = 0.0          # 입력 비용 ($/M 토큰)
    cost_output: float = 0.0         # 출력 비용 ($/M 토큰)
    cost_cache_read: Optional[float] = None   # 캐시 읽기 비용
    cost_cache_write: Optional[float] = None  # 캐시 쓰기 비용
```

데이터 해석 순서 (오프라인 우선):
1. 번들된 스냅샷 (패키지에 포함)
2. 디스크 캐시 (`~/.hermes/models_dev_cache.json`)
3. 네트워크 fetch (`https://models.dev/api.json`)
4. 백그라운드 60분 주기 갱신

### 프로바이더 접두사 스트리핑

모델 이름에서 프로바이더 접두사를 지능적으로 분리한다:

```python
# "local:my-model"    -> "my-model"      (프로바이더 접두사 제거)
# "qwen3.5:27b"       -> "qwen3.5:27b"   (Ollama 태그는 보존)
# "deepseek:latest"   -> "deepseek:latest" (Ollama 태그는 보존)
```

**왜 이렇게 만들었는가?** Ollama 생태계에서는 `model:tag` 형식이 일반적이다 (예: `llama3:70b`). 프로바이더 접두사와 Ollama 태그를 정규식 패턴(`\d+\.?\d*b|latest|stable|q\d`)으로 구별한다.

---

## 5. 폴백 전략

### 프로바이더 실패 시 자동 전환

`config.yaml`의 `fallback_providers` 리스트로 폴백 체인을 정의한다:

```yaml
# config.yaml
providers:
  openrouter:
    api_key: "sk-or-..."
fallback_providers:
  - anthropic
  - gemini
```

```
요청 흐름 (폴백 포함)
======================

  OpenRouter (primary)
       |
    실패 (429/500/502)
       |
       v
  Anthropic (fallback #1)
       |
    실패
       |
       v
  Gemini (fallback #2)
       |
    성공 -> 응답 반환
       |
  다음 턴에서 primary 복원 시도
```

### per-turn primary 복원

폴백이 발생한 후, **매 턴마다** primary 프로바이더를 먼저 시도한다. 이렇게 하면 일시적 장애 후 자동으로 원래 프로바이더로 돌아온다.

### 429 레이트 리밋 처리

Anthropic 프로바이더에서 200K 컨텍스트 리밋 에러가 발생하면 자동으로 컨텍스트를 축소한다:

```
Anthropic 429 처리 흐름
========================

  API 호출 (200K 컨텍스트)
       |
    429 "context_length_exceeded"
       |
       v
  컨텍스트를 200,000 토큰 이하로 자동 축소
       |
       v
  재시도
```

---

## 6. OpenRouter 라우팅

OpenRouter를 사용할 때 `provider_routing` 설정으로 어떤 백엔드 프로바이더가 요청을 처리할지 제어할 수 있다.

### 설정 옵션

```yaml
provider_routing:
  # 정렬 전략
  sort: "throughput"    # "price" (기본) | "throughput" | "latency"

  # 특정 프로바이더만 허용
  only: ["anthropic", "google"]

  # 특정 프로바이더 제외
  ignore: ["deepinfra", "fireworks"]

  # 프로바이더 순서 지정 (기본 로드 밸런싱 무시)
  order: ["anthropic", "google", "together"]

  # 요청의 모든 파라미터를 지원하는 프로바이더만 사용
  require_parameters: true

  # 데이터 보존 정책: 데이터 저장 가능성이 있는 프로바이더 제외
  data_collection: "deny"
```

이 설정은 OpenAI API 호출의 `extra_body.provider` 필드로 주입된다.

**왜 이렇게 만들었는가?** OpenRouter는 동일 모델을 여러 백엔드 프로바이더에서 제공한다. 기업 환경에서는 데이터 보존 정책(`data_collection: "deny"`)이 중요하고, 실시간 서비스에서는 `sort: "latency"`가 필수적이다. 모델 이름에 `:nitro`를 붙이면 throughput 정렬의 축약형이 된다.

---

## 7. 프롬프트 캐싱 비용 최적화

### Anthropic 프롬프트 캐싱의 원리

Anthropic API는 시스템 프롬프트와 메시지의 앞부분을 캐시하여, 후속 요청에서 캐시된 토큰의 비용을 대폭 절감한다.

```
캐시 비용 구조
===============

  일반 입력:     $3.00 / M 토큰 (Claude Sonnet 4.6 기준)
  캐시 쓰기:     $3.75 / M 토큰 (25% 할증)
  캐시 읽기:     $0.30 / M 토큰 (90% 할인!)

  => 10턴 대화에서 시스템 프롬프트(~5K 토큰)가 매번 캐시 히트하면:
     일반: 5K x 10 x $3.00 = $0.15
     캐시: 5K x $3.75 + 5K x 9 x $0.30 = $0.032
     절감: ~79%
```

### Hermes의 캐시 보호 전략

Hermes는 캐시 무효화를 방지하기 위해 여러 정책을 적용한다:

1. **시스템 프롬프트 안정성**: 시스템 프롬프트는 대화 중 변경되지 않도록 설계
2. **스킬 명령어는 user 메시지로 주입**: 시스템 프롬프트를 변경하면 캐시가 깨지므로, 스킬 슬래시 명령어는 user 메시지로 주입한다
3. **에펨럴 주입**: prefill 메시지와 시스템 지시는 API 호출 시점에 주입되며, 세션/로그/궤적에 저장되지 않는다
4. **OpenRouter role:tool에서 cache_control 건너뛰기**: OpenRouter 경유 시 tool 메시지의 `cache_control` 마커를 제거하여 호환성 문제를 방지한다

**왜 이렇게 만들었는가?** 캐시가 깨지면 비용이 급증한다. 특히 긴 대화에서 시스템 프롬프트가 매번 전액 과금되면 비용이 10배 이상 증가할 수 있다. Hermes의 AGENTS.md에 "Prompt Caching Must Not Break"라는 정책이 명시되어 있을 정도로 중요한 설계 원칙이다.

---

## 8. 설정 실습

### config.yaml 기본 설정

```yaml
# ~/.hermes/config.yaml

# 모델 설정
model: "anthropic/claude-sonnet-4"

# 프로바이더 설정
providers:
  openrouter:
    api_key: ""          # .env 파일이나 환경변수 권장
    base_url: "https://openrouter.ai/api/v1"

# 폴백 프로바이더
fallback_providers:
  - anthropic
  - gemini

# 자격 증명 풀 전략 (프로바이더별)
credential_pool_strategies:
  openrouter: "least_used"
  anthropic: "fill_first"
```

### .env 파일 설정

```bash
# ~/.hermes/.env

# OpenRouter (가장 많은 모델 지원)
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxx

# Anthropic (직접 연결, 프롬프트 캐싱 최적)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxx

# Google AI Studio
GOOGLE_API_KEY=AIzaSyxxxxxxxxxx

# Z.AI / GLM (중국 모델)
GLM_API_KEY=xxxxxxxxxxxx

# Kimi / Moonshot
KIMI_API_KEY=sk-kimi-xxxxxxxxxxxx

# DeepSeek
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxx

# Hugging Face
HF_TOKEN=hf_xxxxxxxxxxxx
```

### 프로바이더별 빠른 설정 가이드

#### OpenRouter (범용, 권장)

```bash
# 1. https://openrouter.ai/keys 에서 API 키 발급
# 2. 환경변수 설정
export OPENROUTER_API_KEY="sk-or-v1-..."

# 3. Hermes 실행
hermes
```

#### Anthropic (직접 연결)

```bash
# 1. https://console.anthropic.com/account/keys 에서 키 발급
export ANTHROPIC_API_KEY="sk-ant-..."

# 2. 프로바이더 지정 실행
hermes --provider anthropic
```

#### Nous Portal (OAuth)

```bash
# 1. OAuth 흐름 시작
hermes model
# 2. 브라우저에서 Nous Portal 로그인
# 3. 표시된 코드 입력
# 자동으로 에이전트 키 발급 및 갱신
```

#### Z.AI / GLM

```bash
# 1. https://bigmodel.cn 에서 API 키 발급
export GLM_API_KEY="your-key"

# 2. 엔드포인트 자동 탐지됨 (글로벌/중국/코딩 플랜)
hermes --provider zai
```

#### Kimi / Moonshot

```bash
# platform.kimi.ai 키 (sk-kimi- 접두사)
export KIMI_API_KEY="sk-kimi-..."
# -> 자동으로 api.kimi.com/coding/v1 으로 라우팅

# platform.moonshot.ai 키 (레거시)
export KIMI_API_KEY="sk-..."
# -> 자동으로 api.moonshot.ai/v1 으로 라우팅
```

#### 커스텀 프로바이더 (Ollama, vLLM 등)

```yaml
# config.yaml
custom_providers:
  - name: "local-ollama"
    base_url: "http://localhost:11434/v1"
    api_key: "ollama"   # Ollama는 아무 값이나 가능
    model: "llama3:70b"
```

### 여러 API 키 풀 설정

```bash
# hermes auth 명령으로 키를 풀에 추가
hermes auth add openrouter --key "sk-or-v1-key1"
hermes auth add openrouter --key "sk-or-v1-key2"
hermes auth add openrouter --key "sk-or-v1-key3"

# config.yaml에서 전략 설정
# credential_pool_strategies:
#   openrouter: "least_used"
```

### 디렉토리 구조

```
~/.hermes/
  ├── config.yaml          # 메인 설정
  ├── .env                 # API 키 (0600 권한)
  ├── auth.json            # OAuth 토큰 + 자격 증명 풀
  ├── auth.json.lock       # 크로스 프로세스 잠금
  └── models_dev_cache.json # models.dev 캐시
```

---

## 핵심 정리

| 개념 | 핵심 내용 |
|------|----------|
| **프로바이더 추상화** | `ProviderConfig` 데이터클래스로 20+ 프로바이더를 통일된 인터페이스로 관리 |
| **해석 체인** | 명시적 플래그 > 환경변수 > config.yaml > OAuth > 자격 증명 풀 |
| **자격 증명 풀** | 동일 프로바이더에 여러 키 등록, 4가지 로테이션 전략, 401/429 자동 교체 |
| **모델 메타데이터** | models.dev (오프라인 우선) -> OpenRouter -> 내장 테이블 -> 프로브 |
| **폴백** | `fallback_providers` 체인, per-turn primary 복원, 429 자동 컨텍스트 축소 |
| **OpenRouter 라우팅** | sort/only/ignore/order/data_collection으로 백엔드 제어 |
| **프롬프트 캐싱** | 시스템 프롬프트 안정성 유지, 스킬은 user 메시지로 주입, 캐시 읽기 90% 할인 |
| **보안** | .env는 0600 권한, auth.json은 파일 잠금, 플레이스홀더 자동 감지 |
