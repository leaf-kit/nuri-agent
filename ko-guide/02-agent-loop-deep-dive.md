# 강좌 02: 에이전트 루프 심층 분석

> **이 강좌에서 배우는 것**
>
> - `AIAgent` 클래스의 초기화 매개변수가 왜 그렇게 많은지
> - `run_conversation()` 내부의 while 루프가 정확히 어떻게 동작하는지
> - `IterationBudget`이 단순 카운터가 아닌 객체인 이유
> - `chat()`과 `run_conversation()`의 차이와 사용 시나리오
> - API 오류, 도구 실패, 컨텍스트 초과 시 복원 전략
> - 컨텍스트 압축 5단계 알고리즘의 동작 원리
> - 에이전트 루프 디버깅 실전 팁

---

## 1. AIAgent 클래스 해부

`run_agent.py`의 `AIAgent.__init__()`은 **40개 이상의 매개변수**를 받는다. 이것은 설계 실수가 아니라 의도된 선택이다.

### 매개변수 범주별 분류

```
AIAgent.__init__() 매개변수 분류:

[연결/인증]
  base_url, api_key, provider, api_mode
  acp_command, acp_args                    # ACP(Agent Communication Protocol) 지원

[모델 동작]
  model, max_tokens, reasoning_config
  prefill_messages                          # few-shot 프라이밍

[실행 제어]
  max_iterations, tool_delay
  iteration_budget                          # 외부에서 주입 가능 (서브에이전트)

[도구 필터링]
  enabled_toolsets, disabled_toolsets

[출력/로깅]
  save_trajectories, verbose_logging, quiet_mode
  log_prefix_chars, log_prefix

[콜백 (플랫폼 추상화)]
  tool_progress_callback, tool_start_callback, tool_complete_callback
  thinking_callback, reasoning_callback
  clarify_callback, step_callback
  stream_delta_callback, tool_gen_callback, status_callback

[세션 관리]
  session_id, session_db, parent_session_id
  platform, pass_session_id, persist_session

[OpenRouter 라우팅]
  providers_allowed, providers_ignored, providers_order
  provider_sort, provider_require_parameters, provider_data_collection

[고급 기능]
  skip_context_files, skip_memory
  fallback_model, credential_pool
  checkpoints_enabled, checkpoint_max_snapshots
  ephemeral_system_prompt
```

**왜 이렇게 많은 옵션이 있는가?**

Hermes Agent는 **4가지 다른 런타임 환경**에서 동일한 `AIAgent`를 사용한다:

1. **CLI 인터랙티브 모드**: `clarify_callback` 필요, `quiet_mode=True`, TUI 콜백 세트 전체
2. **Gateway 메시지 핸들러**: 메시지마다 새 인스턴스, `session_db` 필수, `platform` 지정
3. **배치 러너**: `skip_context_files=True`, `save_trajectories=True`, `quiet_mode=True`
4. **RL 환경**: `iteration_budget` 외부 주입, 궤적 저장 최적화

하나의 클래스로 통합한 이유는 **에이전트 로직의 단일 소스(single source of truth)**를 유지하기 위해서다. 서브클래스나 래퍼로 분리하면 버그 수정이 분산된다.

### 초기화 시 핵심 동작

```python
def __init__(self, ...):
    # 1. stdio 안전 래핑 (broken pipe 방어)
    _install_safe_stdio()

    # 2. API 모드 자동 감지
    # provider가 "anthropic"이면 -> anthropic_messages
    # URL에 "chatgpt.com/backend-api/codex" 포함 -> codex_responses
    # 직접 OpenAI URL이면 -> codex_responses (Responses API)
    # 그 외 -> chat_completions

    # 3. LLM 클라이언트 초기화 (OpenAI SDK 또는 Anthropic SDK)
    # 4. 도구 정의 로드 (get_tool_definitions)
    # 5. 프롬프트 캐싱 자동 활성화 (Claude + OpenRouter)
    # 6. 세션 DB 등록
    # 7. TodoStore, MemoryStore 초기화
    # 8. 메모리 provider 플러그인 로드
    # 9. ContextCompressor 초기화
    # 10. CheckpointManager 초기화
```

---

## 2. 대화 루프 상세 흐름

`run_conversation()`은 Hermes Agent의 심장이다. 약 2,300줄에 달하는 이 메서드의 핵심 구조를 의사코드로 분석한다.

### 전체 구조 (의사 코드)

```python
def run_conversation(self, user_message, system_message, conversation_history, ...):
    # ═══ Phase 1: 사전 준비 ═══
    self._restore_primary_runtime()               # 이전 턴 fallback 상태 복원
    user_message = _sanitize_surrogates(...)       # 서러게이트 문자 정리
    iteration_budget = IterationBudget(max_iterations)  # 반복 예산 초기화

    messages = list(conversation_history or [])
    _strip_budget_warnings_from_history(messages)  # 이전 턴의 예산 경고 제거
    self._hydrate_todo_store(conversation_history) # Gateway용: 히스토리에서 todo 복원

    messages.append({"role": "user", "content": user_message})

    # ═══ Phase 2: 시스템 프롬프트 ═══
    if self._cached_system_prompt is None:
        if session_db에_저장된_프롬프트_있음:
            self._cached_system_prompt = stored_prompt  # 캐시 히트 보존
        else:
            self._cached_system_prompt = self._build_system_prompt()

    # ═══ Phase 3: 사전 압축 (preflight) ═══
    if compression_enabled and 메시지가_충분히_많음:
        preflight_tokens = estimate_request_tokens_rough(messages, system, tools)
        if preflight_tokens >= threshold:
            for _ in range(3):  # 최대 3회 반복 압축
                messages = self._compress_context(messages, ...)
                if 토큰_충분히_줄었음: break

    # ═══ Phase 4: 플러그인 사전 호출 ═══
    plugin_context = invoke_hook("pre_llm_call", ...)
    ext_memory_cache = memory_manager.prefetch_all(user_message)

    # ═══ Phase 5: 메인 루프 ═══
    while api_call_count < max_iterations and budget.remaining > 0:

        if self._interrupt_requested: break        # 인터럽트 확인
        if not budget.consume(): break             # 예산 소비

        # --- API 메시지 준비 ---
        api_messages = []
        for msg in messages:
            api_msg = msg.copy()
            # 현재 턴 사용자 메시지에 외부 메모리 + 플러그인 컨텍스트 주입
            # reasoning 필드 -> reasoning_content 변환
            # strict API용 필드 정리
            api_messages.append(api_msg)

        # 시스템 프롬프트 + ephemeral 프롬프트 결합
        api_messages = [system_msg] + prefill_messages + api_messages
        api_messages = apply_anthropic_cache_control(api_messages)
        api_messages = self._sanitize_api_messages(api_messages)

        # --- API 호출 (스트리밍) ---
        response = self._interruptible_streaming_api_call(api_kwargs)

        # --- 응답 검증 ---
        if response가_비정상:
            retry_count += 1
            if 재시도_초과: self._try_activate_fallback() or return 실패
            continue

        # --- 응답 처리 ---
        assistant_message = 응답에서_메시지_추출()
        messages.append(assistant_message)

        # --- 컨텍스트 압축 확인 ---
        if compressor.should_compress(usage.prompt_tokens):
            messages = self._compress_context(messages, ...)

        # --- 도구 호출 처리 ---
        tool_calls = assistant_message.get("tool_calls")
        if not tool_calls:
            final_response = assistant_message["content"]
            break  # ★ 루프 탈출: LLM이 도구 없이 응답 완료

        # --- 도구 실행 ---
        for tool_call in tool_calls:
            if tool_call.name in AGENT_LOOP_TOOLS:
                result = self._handle_agent_tool(tool_call)   # memory, todo 등
            else:
                result = handle_function_call(tool_call.name, tool_call.args)
            messages.append({"role": "tool", "content": result, ...})

        # --- 예산 압박 경고 주입 ---
        if budget.used / budget.max_total >= 0.7:
            마지막_도구_결과에_경고_삽입()

        continue  # while 루프 상단으로

    # ═══ Phase 6: 후처리 ═══
    self._persist_session(messages, conversation_history)  # SQLite 플러시
    if save_trajectories: _save_trajectory_to_file(...)    # JSONL 저장
    return {"messages": messages, "final_response": ..., "api_calls": ..., "completed": True}
```

### 루프 탈출 조건 (5가지)

| 조건 | 코드 위치 | 결과 |
|------|-----------|------|
| LLM이 `tool_calls` 없이 응답 | `if not tool_calls: break` | 정상 완료 |
| `IterationBudget` 소진 | `while` 조건 + `budget.consume()` | 강제 종료, 경고 |
| 인터럽트 요청 | `if self._interrupt_requested: break` | 즉시 중단 |
| API 재시도 모두 실패 | `retry_count >= max_retries` | 에러 반환 |
| `finish_reason == "length"` | 별도 처리 | 이어쓰기 시도 후 종료 |

---

## 3. IterationBudget 메커니즘

### 왜 단순 카운터가 아닌 Budget 객체인가?

```python
class IterationBudget:
    def __init__(self, max_total: int):
        self.max_total = max_total
        self._used = 0
        self._lock = threading.Lock()  # ★ 스레드 안전성

    def consume(self) -> bool:
        """하나 소비. 허용되면 True 반환."""
        with self._lock:
            if self._used >= self.max_total:
                return False
            self._used += 1
            return True

    def refund(self) -> None:
        """execute_code 턴은 예산에서 환불."""
        with self._lock:
            if self._used > 0:
                self._used -= 1
```

**세 가지 설계 이유**:

1. **스레드 안전성**: `delegate_task` 도구로 서브에이전트가 `ThreadPoolExecutor`에서 병렬 실행된다. `threading.Lock()`이 없으면 경합 조건으로 예산 초과가 발생한다.

2. **환불(refund) 메커니즘**: `execute_code` 도구는 프로그래밍 방식으로 다른 도구를 호출한다. 이 "메타 도구" 호출은 예산을 소비하면 안 된다 (사용자의 의도가 아닌 프로그래밍적 도구 사용). `refund()`로 해결한다.

3. **서브에이전트 독립성**: 각 서브에이전트(`delegate_task`)는 **자신만의** `IterationBudget`을 가진다. 부모 에이전트의 `max_iterations=90`과 독립적으로, 서브에이전트는 `delegation.max_iterations=50`으로 제한된다.

```
부모 에이전트 (max_iterations=90)
   ├── 반복 1-5: 직접 도구 호출
   ├── 반복 6: delegate_task 호출 ──> 서브에이전트 A (별도 Budget, max=50)
   │                                     └── 반복 1-25: 서브에이전트 작업
   ├── 반복 7: delegate_task 호출 ──> 서브에이전트 B (별도 Budget, max=50)
   │                                     └── 반복 1-30: 서브에이전트 작업
   └── 반복 8-15: 결과 종합
   총 반복: 부모 15 + 서브A 25 + 서브B 30 = 70 (부모 한도 90 이내)
```

### 예산 압박 경고

예산 소비율이 임계값을 넘으면 LLM에 경고를 주입한다:

```python
self._budget_caution_threshold = 0.7   # 70%: "정리를 시작하세요"
self._budget_warning_threshold = 0.9   # 90%: "지금 당장 응답하세요"
```

경고는 **마지막 도구 결과의 JSON에** 삽입된다 (별도 메시지가 아님). 이렇게 하면 메시지 구조를 깨뜨리지 않고, 프롬프트 캐시도 무효화하지 않는다.

---

## 4. chat() vs run_conversation()

두 인터페이스의 관계는 단순하다:

```python
def chat(self, message: str, stream_callback=None) -> str:
    """단순 인터페이스: 문자열 입력 -> 문자열 출력"""
    result = self.run_conversation(message, stream_callback=stream_callback)
    return result["final_response"]

def run_conversation(self, user_message, system_message=None,
                     conversation_history=None, task_id=None,
                     stream_callback=None, persist_user_message=None) -> Dict:
    """완전한 인터페이스: 전체 대화 상태 제어"""
    # ... 2,300줄의 루프 로직
    return {
        "messages": messages,
        "final_response": content,
        "api_calls": api_call_count,
        "completed": True/False,
        "error": None or "...",
    }
```

| 기능 | `chat()` | `run_conversation()` |
|------|----------|---------------------|
| 반환 타입 | `str` | `Dict` |
| 대화 이력 제어 | 불가 | `conversation_history` 매개변수 |
| 시스템 프롬프트 오버라이드 | 불가 | `system_message` 매개변수 |
| 태스크 격리 | 자동 | `task_id` 수동 지정 가능 |
| 에러 정보 접근 | 불가 (빈 문자열) | `result["error"]`, `result["completed"]` |
| 사용 시나리오 | 스크립트, 간단한 호출 | CLI, Gateway, 배치 러너, RL 환경 |

**실전 가이드**: `chat()`은 프로토타이핑에만 사용하라. 프로덕션에서는 항상 `run_conversation()`을 사용하여 에러 처리와 대화 상태를 완전히 제어해야 한다.

---

## 5. 오류 처리와 복원력

Hermes Agent의 오류 처리는 **7가지 계층**으로 구성된다.

### 계층 1: API 연결 오류 (재시도)

```python
while retry_count < max_retries:  # 기본 3회
    try:
        response = self._interruptible_streaming_api_call(api_kwargs)
    except (APIConnectionError, APITimeoutError, InternalServerError):
        retry_count += 1
        wait_time = min(5 * (2 ** (retry_count - 1)), 120)  # 5s, 10s, 20s, ...120s
        # 중간에 인터럽트 확인하며 대기
```

### 계층 2: 비정상 응답 (fallback 체인)

```
응답이 None/빈 choices -> fallback 모델로 전환
          |
          v
    _fallback_chain: [
        {"provider": "anthropic", "model": "claude-sonnet-4-20250514"},
        {"provider": "openai", "model": "gpt-4o"},
    ]
```

`_try_activate_fallback()`이 체인의 다음 provider로 전환한다. 다음 턴 시작 시 `_restore_primary_runtime()`으로 원래 provider 복원을 시도한다.

### 계층 3: Rate Limiting (429)

429 응답 시 `Retry-After` 헤더를 존중하고, 지수 백오프를 적용한다. 한 번 429를 받으면 즉시 fallback으로 전환을 시도한다.

### 계층 4: 컨텍스트 길이 초과 (자동 압축)

```python
except BadRequestError as e:
    if "context_length" in str(e) or "maximum context" in str(e):
        # 에러 메시지에서 실제 한도 파싱
        detected_limit = parse_context_limit_from_error(str(e))
        if detected_limit:
            save_context_length(model, detected_limit)  # 캐시에 저장
            compressor.context_length = detected_limit

        # 즉시 압축 후 재시도
        messages = self._compress_context(messages, ...)
        restart_with_compressed_messages = True
        break  # retry 루프를 탈출하고 while 루프 상단으로
```

**왜 이렇게 만들었는가?** 모델의 실제 컨텍스트 길이는 공식 문서와 다를 수 있다 (provider별 오버헤드, 시스템 토큰 예약). 에러에서 실제 한도를 파싱하여 `model_metadata` 캐시에 저장하면, 다음 세션부터는 사전에 정확히 압축할 수 있다.

### 계층 5: 도구 실행 실패

```python
# tools/registry.py dispatch()
try:
    return entry.handler(args, **kwargs)
except Exception as e:
    return json.dumps({"error": f"Tool execution failed: {type(e).__name__}: {e}"})
```

모든 도구 실행 오류는 **JSON 에러 문자열로 래핑**되어 LLM에게 반환된다. LLM은 이 에러를 보고 다른 접근법을 시도하거나 사용자에게 보고할 수 있다. 에이전트 루프 자체는 중단되지 않는다.

### 계층 6: 잘못된 도구 호출 (자동 복구)

LLM이 존재하지 않는 도구를 호출하거나, JSON 인자가 깨져 있으면:

```python
# 도구 이름 유효성 검사
if function_name not in self.valid_tool_names:
    # 퍼지 매칭으로 가장 유사한 도구 제안
    suggestion = fuzzy_match(function_name, self.valid_tool_names)
    result = f'{{"error": "Unknown tool: {function_name}. Did you mean: {suggestion}?"}}'

# JSON 파싱 실패
except json.JSONDecodeError:
    self._invalid_json_retries += 1
    result = '{"error": "Invalid JSON in tool arguments. Please retry with valid JSON."}'
```

### 계층 7: stdio 안전 래핑

```python
class _SafeWriter:
    """broken pipe에서 crash를 방지하는 투명 래퍼"""
    def write(self, data):
        try:
            return self._inner.write(data)
        except (OSError, ValueError):
            return len(data)  # 조용히 무시
```

systemd 서비스, Docker 컨테이너, 서브에이전트 스레드에서 stdout이 닫힐 수 있다. `print()` 호출로 에이전트가 crash하면 안 되므로, 모든 쓰기를 `_SafeWriter`로 보호한다.

---

## 6. 컨텍스트 압축 트리거

### 언제 압축이 시작되는가?

두 가지 트리거가 있다:

```
트리거 1: API 응답 후 (사후 압축)
    compressor.update_from_response(usage)
    if compressor.should_compress(usage.prompt_tokens):
        messages = self._compress_context(messages, ...)

트리거 2: run_conversation 시작 시 (사전 압축 - preflight)
    preflight_tokens = estimate_request_tokens_rough(messages, system, tools)
    if preflight_tokens >= compressor.threshold_tokens:
        messages = self._compress_context(messages, ...)  # 최대 3회 반복
```

임계값은 `compression.threshold` 설정으로 조절한다 (기본값 0.50 = 컨텍스트 길이의 50%).

### 압축 알고리즘 5단계

`agent/context_compressor.py`의 `ContextCompressor` 클래스가 실행하는 5단계:

```
Step 1: 오래된 도구 결과 정리 (LLM 호출 없음, 무비용)
   ┌──────────────────────────────────────────────┐
   │ 보호된 tail 영역 밖의 도구 결과 중            │
   │ 200자 이상인 것을 플레이스홀더로 교체:         │
   │ "[Old tool output cleared to save context space]" │
   └──────────────────────────────────────────────┘
   
Step 2: head 보호 (처음 N개 메시지)
   ┌──────────────────────────────────────────────┐
   │ protect_first_n (기본 3)개 메시지를 보존      │
   │ = system prompt + 첫 사용자 메시지 + 첫 응답  │
   │ 이유: 대화의 원래 맥락/목표를 유지             │
   └──────────────────────────────────────────────┘

Step 3: tail 보호 (토큰 예산 기반)
   ┌──────────────────────────────────────────────┐
   │ tail_token_budget (threshold * target_ratio)  │
   │ 만큼의 최근 메시지를 보존                     │
   │ 주의: 메시지 개수가 아닌 토큰 예산 기반!       │
   │ 이유: 긴 도구 결과 1개 vs 짧은 메시지 20개의   │
   │       실질적 정보량이 다르기 때문               │
   └──────────────────────────────────────────────┘

Step 4: 중간 영역 요약 (LLM 호출)
   ┌──────────────────────────────────────────────┐
   │ head와 tail 사이의 "중간 턴"을 구조화된       │
   │ 프롬프트로 LLM에 보내 요약 생성:              │
   │                                               │
   │  ## Goal                                      │
   │  ## Constraints & Preferences                 │
   │  ## Progress (Done / In Progress / Blocked)   │
   │  ## Key Decisions                             │
   │  ## Relevant Files                            │
   │  ## Next Steps                                │
   │  ## Critical Context                          │
   │                                               │
   │ 요약 토큰 예산 = 압축 내용의 20% (최소 2K,     │
   │ 최대 컨텍스트 길이의 5%, 절대상한 12K)         │
   └──────────────────────────────────────────────┘

Step 5: 반복 요약 업데이트 (2차 이후 압축)
   ┌──────────────────────────────────────────────┐
   │ _previous_summary가 있으면 "처음부터 요약"    │
   │ 대신 "기존 요약 업데이트" 프롬프트 사용:       │
   │                                               │
   │ "PREVIOUS SUMMARY: ..."                       │
   │ "NEW TURNS TO INCORPORATE: ..."               │
   │ "PRESERVE existing, ADD new, MOVE completed"  │
   │                                               │
   │ 이유: 반복 압축 시 정보 손실 최소화            │
   │ (3차 압축이면 1차+2차 요약이 누적 보존)        │
   └──────────────────────────────────────────────┘
```

### 압축 결과의 메시지 구조

```python
# 압축 전
messages = [system, user1, asst1, tool1, user2, asst2, tool2, ..., user10, asst10]
#           ^head^                    ^중간 (요약됨)^                 ^tail^

# 압축 후
messages = [
    system,
    user1, asst1,                              # head 보존
    {"role": "user", "content": "[CONTEXT COMPACTION] 이전 대화 요약..."}, # 요약
    user8, asst8, tool8, user9, asst9, tool9,  # tail 보존
    user10, asst10,
]
```

### 요약 실패 시 fallback

LLM 요약 호출이 실패하면 (`_generate_summary()` returns None):
- 중간 턴을 요약 없이 **그냥 삭제**한다
- 600초 쿨다운 타이머를 설정하여 반복 실패를 방지한다
- 이유: 요약 없는 삭제가 컨텍스트 초과 에러보다 낫다

---

## 7. 실전 팁: 에이전트 루프 디버깅

### 로그 확인 방법

```bash
# 에이전트 로그 (모든 INFO+ 메시지)
tail -f ~/.hermes/logs/agent.log

# 에러 로그 (WARNING+ 메시지만)
tail -f ~/.hermes/logs/errors.log

# API 요청 덤프 (디버깅용)
export HERMES_DUMP_REQUESTS=1
# -> 각 API 요청의 전체 페이로드가 로그에 기록됨
```

### verbose 모드 활성화

```bash
hermes --verbose "질문"
# 또는 코드에서
agent = AIAgent(verbose_logging=True)
```

verbose 모드에서 확인할 수 있는 것:
- 각 API 호출의 메시지 수, 토큰 수, 도구 수
- 응답 모델명, usage 정보
- 도구 호출 인자와 결과 미리보기 (log_prefix_chars로 길이 조절)

### max_iterations 조정

```yaml
# ~/.hermes/config.yaml
agent:
  max_iterations: 50      # 기본 90, 줄이면 비용 절약
  
delegation:
  max_iterations: 30      # 서브에이전트 한도 (기본 50)
```

**가이드라인**:
- 간단한 질의응답: 5-10이면 충분
- 코드 작성/수정: 20-40
- 복잡한 연구 작업: 50-90
- RL 훈련용 데이터 생성: 30-50 (너무 길면 궤적 품질 저하)

### 무한 루프 방지

LLM이 같은 도구를 반복 호출하는 패턴을 감지하는 내장 보호가 있다:

```python
# file_tools.py의 연속 읽기 감지
_READ_SEARCH_TOOLS = {"read_file", "search_files"}
# 연속 n회 이상 read/search만 하면 경고 메시지 삽입
```

추가 방어:
- `_invalid_tool_retries` 카운터: 같은 잘못된 도구 호출이 반복되면 강제 종료
- `_empty_content_retries`: 빈 응답 반복 시 fallback 전환
- `_incomplete_scratchpad_retries`: 불완전한 `<think>` 태그 반복 시 자동 수정

### 디버깅 체크리스트

문제 발생 시 확인 순서:

```
1. ~/.hermes/logs/errors.log 확인
   -> API 에러? 도구 실행 에러? 인증 문제?

2. session DB에서 마지막 세션 확인
   sqlite3 ~/.hermes/state.db "SELECT * FROM sessions ORDER BY started_at DESC LIMIT 5"

3. 세션 메시지 확인
   sqlite3 ~/.hermes/state.db "SELECT role, substr(content,1,100) FROM messages
   WHERE session_id='...' ORDER BY timestamp"

4. HERMES_DUMP_REQUESTS=1로 API 페이로드 확인

5. 도구 가용성 확인
   python -c "from model_tools import check_tool_availability; print(check_tool_availability())"
```

---

## 핵심 정리

| 항목 | 요약 |
|------|------|
| **AIAgent 매개변수가 많은 이유** | 4가지 런타임(CLI, Gateway, Batch, RL)에서 단일 클래스 재사용 |
| **루프 핵심 구조** | `while budget.remaining > 0` -> API 호출 -> 도구 실행 -> 반복 또는 종료 |
| **루프 탈출 조건** | 도구 없는 응답, 예산 소진, 인터럽트, API 실패, length 초과 |
| **IterationBudget** | 스레드 안전, refund 지원, 서브에이전트 독립 예산 |
| **chat() vs run_conversation()** | 단순 래퍼 vs 완전 제어. 프로덕션에서는 항상 `run_conversation()` |
| **오류 처리 7계층** | API 재시도 -> fallback 체인 -> 429 처리 -> 컨텍스트 압축 -> 도구 에러 래핑 -> 퍼지 매칭 -> stdio 보호 |
| **압축 5단계** | 오래된 도구 정리 -> head 보호 -> tail 보호(토큰 기반) -> 중간 요약 -> 반복 업데이트 |
| **디버깅 핵심** | `~/.hermes/logs/`, `HERMES_DUMP_REQUESTS=1`, `state.db` SQLite 조회 |

다음 강좌에서는 도구 시스템의 레지스트리 패턴, 도구세트, 비동기 브릿징을 완전 해부한다.
