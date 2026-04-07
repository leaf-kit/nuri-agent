# 가격 정확도 아키텍처

날짜: 2026-03-16

## 목표

Hermes는 사용자의 실제 청구 경로에 대한 공식 소스로 뒷받침되는 경우에만 달러 비용을 표시해야 합니다.

이 설계는 다음에 있는 현재의 정적, 휴리스틱 가격 책정 흐름을 대체합니다:

- `run_agent.py`
- `agent/usage_pricing.py`
- `agent/insights.py`
- `cli.py`

새로운 제공자 인식 가격 시스템은 다음을 수행합니다:

- 캐시 청구를 올바르게 처리
- `actual` vs `estimated` vs `included` vs `unknown` 구분
- 제공자가 권위 있는 청구 데이터를 노출할 때 사후 비용 조정
- 직접 제공자, OpenRouter, 구독, 기업 가격, 커스텀 엔드포인트 지원

## 현재 설계의 문제점

현재 Hermes 동작에는 네 가지 구조적 문제가 있습니다:

1. `prompt_tokens`와 `completion_tokens`만 저장하는데, 이는 캐시 읽기와 캐시 쓰기를 별도로 청구하는 제공자에게 불충분합니다.
2. 정적 모델 가격 테이블과 퍼지 휴리스틱을 사용하여 현재 공식 가격과 차이가 발생할 수 있습니다.
3. 공개 API 목록 가격이 사용자의 실제 청구 경로와 일치한다고 가정합니다.
4. 실시간 추정치와 조정된 청구 비용 간의 구분이 없습니다.

## 설계 원칙

1. 가격 책정 전에 사용량을 정규화합니다.
2. 캐시된 토큰을 일반 입력 비용에 절대 합산하지 않습니다.
3. 확실성을 명시적으로 추적합니다.
4. 청구 경로를 모델 아이덴티티의 일부로 취급합니다.
5. 스크래핑된 문서보다 공식 기계 판독 가능 소스를 선호합니다.
6. 가능한 경우 사후 제공자 비용 API를 사용합니다.
7. 정밀도를 만들어내기보다 `n/a`를 표시합니다.

## 상위 수준 아키텍처

새 시스템은 네 개의 계층으로 구성됩니다:

1. `usage_normalization`
   원시 제공자 사용량을 정규 사용량 레코드로 변환합니다.
2. `pricing_source_resolution`
   청구 경로, 진실의 소스, 적용 가능한 가격 소스를 결정합니다.
3. `cost_estimation_and_reconciliation`
   가능한 경우 즉시 추정치를 생성한 다음, 나중에 실제 청구 비용으로 대체하거나 주석을 달아줍니다.
4. `presentation`
   `/usage`, `/insights`, 상태 바가 확실성 메타데이터와 함께 비용을 표시합니다.

## 정규 사용량 레코드

모든 제공자 경로가 가격 계산 전에 매핑되는 정규 사용량 모델을 추가합니다.

제안 구조:

```python
@dataclass
class CanonicalUsage:
    provider: str
    billing_provider: str
    model: str
    billing_route: str

    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    reasoning_tokens: int = 0
    request_count: int = 1

    raw_usage: dict[str, Any] | None = None
    raw_usage_fields: dict[str, str] | None = None
    computed_fields: set[str] | None = None

    provider_request_id: str | None = None
    provider_generation_id: str | None = None
    provider_response_id: str | None = None
```

규칙:

- `input_tokens`는 캐시되지 않은 입력만을 의미합니다.
- `cache_read_tokens`와 `cache_write_tokens`는 절대 `input_tokens`에 합산되지 않습니다.
- `output_tokens`는 캐시 메트릭을 제외합니다.
- `reasoning_tokens`는 제공자가 공식적으로 별도 청구하지 않는 한 텔레메트리입니다.

이것은 `opencode`에서 사용되는 정규화 패턴과 동일하며, 출처 및 조정 ID가 확장되었습니다.

## 제공자 정규화 규칙

### OpenAI Direct

소스 사용량 필드:

- `prompt_tokens`
- `completion_tokens`
- `prompt_tokens_details.cached_tokens`

정규화:

- `cache_read_tokens = cached_tokens`
- `input_tokens = prompt_tokens - cached_tokens`
- `cache_write_tokens = 0` (OpenAI가 해당 경로에서 노출하지 않는 한)
- `output_tokens = completion_tokens`

### Anthropic Direct

소스 사용량 필드:

- `input_tokens`
- `output_tokens`
- `cache_read_input_tokens`
- `cache_creation_input_tokens`

정규화:

- `input_tokens = input_tokens`
- `output_tokens = output_tokens`
- `cache_read_tokens = cache_read_input_tokens`
- `cache_write_tokens = cache_creation_input_tokens`

### OpenRouter

추정 시점의 사용량 정규화는 가능한 경우 기본 제공자와 동일한 규칙으로 응답 사용량 페이로드를 사용해야 합니다.

조정 시점의 레코드는 다음도 저장해야 합니다:

- OpenRouter generation id
- 가능한 경우 네이티브 토큰 필드
- `total_cost`
- `cache_discount`
- `upstream_inference_cost`
- `is_byok`

### Gemini / Vertex

가능한 경우 공식 Gemini 또는 Vertex 사용량 필드를 사용합니다.

캐시된 콘텐츠 토큰이 노출되는 경우:

- `cache_read_tokens`에 매핑

경로가 캐시 생성 메트릭을 노출하지 않는 경우:

- `cache_write_tokens = 0` 저장
- 나중의 확장을 위해 원시 사용량 페이로드 보존

### DeepSeek 및 기타 직접 제공자

공식적으로 노출된 필드만 정규화합니다.

제공자가 캐시 버킷을 노출하지 않는 경우:

- 제공자가 도출 방법을 명시적으로 문서화하지 않는 한 추론하지 않음

### 구독 / 포함 비용 경로

이들도 정규 사용량 모델을 사용합니다.

토큰은 정상적으로 추적됩니다. 비용은 사용량 존재 여부가 아니라 청구 모드에 따라 달라집니다.

## 청구 경로 모델

Hermes는 `model`만으로 가격을 키하는 것을 중단해야 합니다.

청구 경로 디스크립터를 도입합니다:

```python
@dataclass
class BillingRoute:
    provider: str
    base_url: str | None
    model: str
    billing_mode: str
    organization_hint: str | None = None
```

`billing_mode` 값:

- `official_cost_api`
- `official_generation_api`
- `official_models_api`
- `official_docs_snapshot`
- `subscription_included`
- `user_override`
- `custom_contract`
- `unknown`

예시:

- Costs API에 접근 가능한 OpenAI 직접 API: `official_cost_api`
- Usage & Cost API에 접근 가능한 Anthropic 직접 API: `official_cost_api`
- 조정 전 OpenRouter 요청: `official_models_api`
- generation 조회 후 OpenRouter 요청: `official_generation_api`
- GitHub Copilot 스타일 구독 경로: `subscription_included`
- 로컬 OpenAI 호환 서버: `unknown`
- 설정된 요금의 기업 계약: `custom_contract`

## 비용 상태 모델

표시되는 모든 비용에는 다음이 있어야 합니다:

```python
@dataclass
class CostResult:
    amount_usd: Decimal | None
    status: Literal["actual", "estimated", "included", "unknown"]
    source: Literal[
        "provider_cost_api",
        "provider_generation_api",
        "provider_models_api",
        "official_docs_snapshot",
        "user_override",
        "custom_contract",
        "none",
    ]
    label: str
    fetched_at: datetime | None
    pricing_version: str | None
    notes: list[str]
```

표시 규칙:

- `actual`: 달러 금액을 최종 값으로 표시
- `estimated`: 달러 금액을 추정 라벨과 함께 표시
- `included`: UX 선택에 따라 `included` 또는 `$0.00 (included)` 표시
- `unknown`: `n/a` 표시

## 공식 소스 계층

다음 순서로 비용을 해결합니다:

1. 요청 수준 또는 계정 수준의 공식 청구 비용
2. 공식 기계 판독 가능 모델 가격
3. 공식 문서 스냅샷
4. 사용자 재정의 또는 커스텀 계약
5. 알 수 없음

시스템은 현재 청구 경로에 대해 더 높은 신뢰도의 소스가 존재하는 경우 절대 더 낮은 수준으로 건너뛰어서는 안 됩니다.

## 제공자별 진실 규칙

### OpenAI Direct

선호 진실:

1. 조정된 지출을 위한 Costs API
2. 실시간 추정을 위한 공식 가격 페이지

### Anthropic Direct

선호 진실:

1. 조정된 지출을 위한 Usage & Cost API
2. 실시간 추정을 위한 공식 가격 문서

### OpenRouter

선호 진실:

1. 조정된 `total_cost`를 위한 `GET /api/v1/generation`
2. 실시간 추정을 위한 `GET /api/v1/models` 가격

OpenRouter 청구의 진실 소스로 기본 제공자의 공개 가격을 사용하지 마십시오.

### Gemini / Vertex

선호 진실:

1. 해당 경로에서 사용 가능한 경우 조정된 지출을 위한 공식 청구 내보내기 또는 청구 API
2. 추정을 위한 공식 가격 문서

### DeepSeek

선호 진실:

1. 향후 사용 가능해질 경우 공식 기계 판독 가능 비용 소스
2. 현재는 공식 가격 문서 스냅샷

### 구독 포함 경로

선호 진실:

1. 모델을 구독에 포함된 것으로 표시하는 명시적 경로 설정

API 목록 가격 추정이 아닌 `included`를 표시해야 합니다.

### 커스텀 엔드포인트 / 로컬 모델

선호 진실:

1. 사용자 재정의
2. 커스텀 계약 설정
3. 알 수 없음

기본적으로 `unknown`으로 표시해야 합니다.

## 가격 카탈로그

현재 `MODEL_PRICING` dict를 더 풍부한 가격 카탈로그로 교체합니다.

제안 레코드:

```python
@dataclass
class PricingEntry:
    provider: str
    route_pattern: str
    model_pattern: str

    input_cost_per_million: Decimal | None = None
    output_cost_per_million: Decimal | None = None
    cache_read_cost_per_million: Decimal | None = None
    cache_write_cost_per_million: Decimal | None = None
    request_cost: Decimal | None = None
    image_cost: Decimal | None = None

    source: str = "official_docs_snapshot"
    source_url: str | None = None
    fetched_at: datetime | None = None
    pricing_version: str | None = None
```

카탈로그는 경로를 인식해야 합니다:

- `openai:gpt-5`
- `anthropic:claude-opus-4-6`
- `openrouter:anthropic/claude-opus-4.6`
- `copilot:gpt-4o`

이를 통해 직접 제공자 청구와 중개자 청구를 혼동하지 않습니다.

## 가격 동기화 아키텍처

수동으로 유지되는 단일 하드코딩 테이블 대신 가격 동기화 서브시스템을 도입합니다.

제안 모듈:

- `agent/pricing/catalog.py`
- `agent/pricing/sources.py`
- `agent/pricing/sync.py`
- `agent/pricing/reconcile.py`
- `agent/pricing/types.py`

### 동기화 소스

- OpenRouter models API
- API가 없는 경우 공식 제공자 문서 스냅샷
- 설정에서의 사용자 재정의

### 동기화 출력

가격 항목을 다음과 함께 로컬에 캐시합니다:

- 소스 URL
- 가져오기 타임스탬프
- 버전/해시
- 신뢰도/소스 유형

### 동기화 빈도

- 시작 시 캐시 워밍
- 소스에 따라 6~24시간마다 백그라운드 새로고침
- 수동 `hermes pricing sync`

## 조정 아키텍처

실시간 요청은 초기에 추정치만 생성할 수 있습니다. Hermes는 제공자가 실제 청구 비용을 노출할 때 나중에 조정해야 합니다.

제안 흐름:

1. 에이전트 호출 완료.
2. Hermes가 정규 사용량과 조정 ID를 저장.
3. Hermes가 가격 소스가 있는 경우 즉시 추정치를 계산.
4. 조정 워커가 지원되는 경우 실제 비용을 가져옴.
5. 세션 및 메시지 레코드가 `actual` 비용으로 업데이트됨.

다음과 같이 실행할 수 있습니다:

- 저렴한 조회의 경우 인라인
- 지연된 제공자 회계의 경우 비동기적

## 영속성 변경

세션 저장소는 집계된 prompt/completion 합계만 저장하는 것을 중단해야 합니다.

사용량과 비용 확실성 모두에 대한 필드를 추가합니다:

- `input_tokens`
- `output_tokens`
- `cache_read_tokens`
- `cache_write_tokens`
- `reasoning_tokens`
- `estimated_cost_usd`
- `actual_cost_usd`
- `cost_status`
- `cost_source`
- `pricing_version`
- `billing_provider`
- `billing_mode`

스키마 확장이 하나의 PR에 너무 큰 경우 새로운 가격 이벤트 테이블을 추가합니다:

```text
session_cost_events
  id
  session_id
  request_id
  provider
  model
  billing_mode
  input_tokens
  output_tokens
  cache_read_tokens
  cache_write_tokens
  estimated_cost_usd
  actual_cost_usd
  cost_status
  cost_source
  pricing_version
  created_at
  updated_at
```

## Hermes 접점

### `run_agent.py`

현재 역할:

- 원시 제공자 사용량 파싱
- 세션 토큰 카운터 업데이트

새 역할:

- `CanonicalUsage` 빌드
- 정규 카운터 업데이트
- 조정 ID 저장
- 가격 서브시스템에 사용량 이벤트 발행

### `agent/usage_pricing.py`

현재 역할:

- 정적 조회 테이블
- 직접 비용 산술

새 역할:

- 가격 카탈로그 파사드로 이동 또는 교체
- 퍼지 모델 패밀리 휴리스틱 없음
- 청구 경로 컨텍스트 없이 직접 가격 책정 없음

### `cli.py`

현재 역할:

- prompt/completion 합계에서 직접 세션 비용 계산

새 역할:

- `CostResult` 표시
- 상태 배지 표시:
  - `actual`
  - `estimated`
  - `included`
  - `n/a`

### `agent/insights.py`

현재 역할:

- 정적 가격에서 과거 추정치 재계산

새 역할:

- 저장된 가격 이벤트 집계
- 추정보다 실제 비용 선호
- 조정을 사용할 수 없는 경우에만 추정치 표시

## UX 규칙

### 상태 바

다음 중 하나를 표시합니다:

- `$1.42`
- `~$1.42`
- `included`
- `cost n/a`

여기서:

- `$1.42`는 `actual`을 의미
- `~$1.42`는 `estimated`를 의미
- `included`는 구독 기반 또는 명시적 무비용 경로를 의미
- `cost n/a`는 알 수 없음을 의미

### `/usage`

표시 항목:

- 토큰 버킷
- 추정 비용
- 가능한 경우 실제 비용
- 비용 상태
- 가격 소스

### `/insights`

집계 항목:

- 실제 비용 합계
- 추정 전용 합계
- 비용 미확인 세션 수
- 포함 비용 세션 수

## 설정 및 재정의

설정에 사용자 설정 가능한 가격 재정의를 추가합니다:

```yaml
pricing:
  mode: hybrid
  sync_on_startup: true
  sync_interval_hours: 12
  overrides:
    - provider: openrouter
      model: anthropic/claude-opus-4.6
      billing_mode: custom_contract
      input_cost_per_million: 4.25
      output_cost_per_million: 22.0
      cache_read_cost_per_million: 0.5
      cache_write_cost_per_million: 6.0
  included_routes:
    - provider: copilot
      model: "*"
    - provider: codex-subscription
      model: "*"
```

재정의는 일치하는 청구 경로에 대해 카탈로그 기본값보다 우선해야 합니다.

## 롤아웃 계획

### 1단계

- 정규 사용량 모델 추가
- `run_agent.py`에서 캐시 토큰 버킷 분리
- 캐시가 부풀린 프롬프트 합계에 대한 가격 책정 중단
- 개선된 백엔드 수학으로 현재 UI 유지

### 2단계

- 경로 인식 가격 카탈로그 추가
- OpenRouter models API 동기화 통합
- `estimated` vs `included` vs `unknown` 추가

### 3단계

- OpenRouter generation 비용 조정 추가
- 실제 비용 영속성 추가
- `/insights`를 실제 비용 선호로 업데이트

### 4단계

- 직접 OpenAI 및 Anthropic 조정 경로 추가
- 사용자 재정의 및 계약 가격 추가
- 가격 동기화 CLI 명령 추가

## 테스트 전략

다음에 대한 테스트 추가:

- OpenAI 캐시 토큰 차감
- Anthropic 캐시 읽기/쓰기 분리
- OpenRouter 추정 vs 실제 조정
- 구독 기반 모델의 `included` 표시
- 커스텀 엔드포인트의 `n/a` 표시
- 재정의 우선순위
- 오래된 카탈로그 폴백 동작

휴리스틱 가격을 가정하는 현재 테스트는 경로 인식 기대값으로 대체해야 합니다.

## 비목표

- 공식 소스 또는 사용자 재정의 없이 정확한 기업 청구 재구성
- 캐시 버킷 데이터가 없는 이전 세션에 대한 완벽한 과거 비용 역채움
- 요청 시점에 임의의 제공자 웹 페이지 스크래핑

## 권장 사항

기존 `MODEL_PRICING` dict를 확장하지 마십시오.

그 방식은 제품 요구 사항을 충족할 수 없습니다. Hermes는 대신 다음으로 마이그레이션해야 합니다:

- 정규 사용량 정규화
- 경로 인식 가격 소스
- 추정 후 조정 비용 생명주기
- UI에서 명시적 확실성 상태

이것이 "Hermes 가격은 가능한 경우 공식 소스로 뒷받침되며, 그렇지 않으면 명확히 라벨링됩니다"라는 진술을 방어 가능하게 만드는 최소 아키텍처입니다.
