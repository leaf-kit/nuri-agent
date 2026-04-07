# 강좌 07: 서브에이전트와 병렬 실행

> **이 강좌에서 배우는 것**
>
> - 왜 하나의 에이전트가 모든 작업을 처리하면 안 되는지 (컨텍스트 비용, 격리, 병렬성)
> - `delegate_task` 도구의 내부 구조와 매개변수
> - ThreadPoolExecutor 기반 최대 3개 동시 실행 메커니즘
> - 차단된 도구 목록(`DELEGATE_BLOCKED_TOOLS`)과 그 설계 이유
> - 깊이 제한(MAX_DEPTH=2)이 무한 위임을 막는 원리
> - `_last_resolved_tool_names` 전역 상태의 저장/복원 패턴
> - `execute_code` 샌드박스의 격리 구조와 RPC 통신
> - 서브에이전트를 효과적으로 사용하는 실전 패턴

---

## 1. 서브에이전트 위임이란

LLM 에이전트가 복잡한 작업을 수행할 때, 모든 것을 하나의 대화 컨텍스트 안에서 처리하면 세 가지 근본적인 문제가 발생한다.

**컨텍스트 비용 폭발**: 디버깅 과정에서 수십 개의 파일을 읽고, 터미널 출력을 분석하면 컨텍스트 윈도우가 빠르게 채워진다. 토큰이 늘어날수록 추론 비용은 O(n^2)에 가까워진다.

**격리 부재**: 한 작업의 중간 결과(예: 로그 100줄)가 다른 작업의 판단을 오염시킬 수 있다. 특히 웹 검색 결과에 포함된 프롬프트 인젝션이 전체 대화를 장악할 위험이 있다.

**순차 실행 병목**: 독립적인 세 가지 조사를 순서대로 수행하면 총 시간은 각각의 합이 된다. 병렬로 돌리면 가장 오래 걸리는 작업 하나의 시간만큼만 소요된다.

```
                          ┌───────────────────────────────────────┐
                          │         부모 에이전트 (Parent)          │
                          │  컨텍스트: 사용자 대화 + 위임 결과 요약   │
                          └────────┬───────────┬───────────┬──────┘
                                   │           │           │
                         delegate_task     delegate_task   delegate_task
                                   │           │           │
                          ┌────────▼──┐  ┌─────▼─────┐  ┌─▼──────────┐
                          │  자식 A   │  │  자식 B    │  │  자식 C    │
                          │ 독립 컨텍 │  │ 독립 컨텍  │  │ 독립 컨텍  │
                          │ 제한 도구 │  │ 제한 도구  │  │ 제한 도구  │
                          └───────────┘  └───────────┘  └────────────┘
                                   │           │           │
                              요약 반환     요약 반환     요약 반환
                                   │           │           │
                          ┌────────▼───────────▼───────────▼──────┐
                          │    부모: 세 결과 합산 → 사용자 응답      │
                          └───────────────────────────────────────┘
```

**왜 이렇게 만들었는가?** 부모의 컨텍스트에는 위임 호출과 최종 요약만 남는다. 자식의 중간 도구 호출, 추론 과정은 절대 부모 컨텍스트에 들어가지 않는다. 이것이 `delegate_tool.py` 모듈 독스트링의 핵심 설계 원칙이다:

> "The parent's context only sees the delegation call and the summary result,
> never the child's intermediate tool calls or reasoning."

---

## 2. delegate_task 도구 해부

### 2.1 함수 시그니처와 매개변수

```python
def delegate_task(
    goal: Optional[str] = None,         # 단일 모드: 자식이 달성할 목표
    context: Optional[str] = None,      # 배경 정보 (파일 경로, 에러 메시지 등)
    toolsets: Optional[List[str]] = None,# 자식에게 허용할 도구세트
    tasks: Optional[List[Dict]] = None, # 배치 모드: 최대 3개 병렬 작업
    max_iterations: Optional[int] = None,# 자식당 최대 도구 호출 턴 (기본 50)
    acp_command: Optional[str] = None,  # ACP 서브프로세스 오버라이드
    acp_args: Optional[List[str]] = None,
    parent_agent=None,                  # 내부 주입: 부모 에이전트 참조
) -> str:  # JSON 결과 반환
```

**두 가지 모드**가 있다:

| 모드 | 필수 매개변수 | 설명 |
|------|-------------|------|
| 단일(Single) | `goal` | 자식 1개 생성, 직접 실행 (스레드풀 오버헤드 없음) |
| 배치(Batch) | `tasks` 배열 | 최대 3개 자식 병렬 생성, `ThreadPoolExecutor`로 동시 실행 |

### 2.2 자식 에이전트의 격리 범위

각 자식 에이전트는 `_build_child_agent()` 함수에서 구성되며, 다음이 완전히 격리된다:

```python
child = AIAgent(
    # ... 자격 증명 상속 ...
    enabled_toolsets=child_toolsets,          # 제한된 도구세트
    quiet_mode=True,                         # 출력 억제
    ephemeral_system_prompt=child_prompt,    # 전용 시스템 프롬프트
    skip_context_files=True,                 # HERMES.md 등 미로드
    skip_memory=True,                        # MEMORY.md 미로드
    clarify_callback=None,                   # 사용자 질문 불가
    iteration_budget=None,                   # 독립 예산
)
child._delegate_depth = parent_depth + 1    # 깊이 추적
```

**왜 이렇게 만들었는가?** 자식은 "깨끗한 슬레이트(clean slate)"로 시작한다. 부모의 대화 이력, 메모리 파일, 컨텍스트 파일을 전혀 볼 수 없다. 필요한 정보는 반드시 `context` 매개변수로 명시적으로 전달해야 한다. 이 설계는 정보 유출을 방지하고, 자식이 부모의 잘못된 맥락에 영향받지 않도록 보장한다.

### 2.3 시스템 프롬프트 구성

```python
def _build_child_system_prompt(goal: str, context: Optional[str] = None) -> str:
    parts = [
        "You are a focused subagent working on a specific delegated task.",
        "",
        f"YOUR TASK:\n{goal}",
    ]
    if context and context.strip():
        parts.append(f"\nCONTEXT:\n{context}")
    parts.append(
        "\nComplete this task using the tools available to you. "
        "When finished, provide a clear, concise summary of: ..."
    )
```

자식의 시스템 프롬프트는 의도적으로 단순하다. "집중된 서브에이전트"라는 정체성만 부여하고, 목표와 컨텍스트를 직접 주입한다. Hermes의 기본 시스템 프롬프트(identity, platform hints, skills index)는 모두 건너뛴다.

---

## 3. 병렬 실행 메커니즘

### 3.1 ThreadPoolExecutor 기반 동시 실행

```python
MAX_CONCURRENT_CHILDREN = 3

if n_tasks == 1:
    # 단일 작업 -- 직접 실행 (스레드풀 오버헤드 없음)
    result = _run_single_child(0, task["goal"], child, parent_agent)
else:
    # 배치 -- 병렬 실행
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_CHILDREN) as executor:
        futures = {}
        for i, t, child in children:
            future = executor.submit(
                _run_single_child,
                task_index=i, goal=t["goal"],
                child=child, parent_agent=parent_agent,
            )
            futures[future] = i

        for future in as_completed(futures):
            entry = future.result()
            results.append(entry)
```

**왜 최대 3개인가?** API 호출 비용과 동시성의 균형이다. 각 자식은 독립적으로 LLM API를 호출하므로, 3개 이상이면 API rate limit에 걸릴 확률이 급증하고, 총 토큰 비용이 부모 혼자 처리할 때보다 오히려 높아질 수 있다.

### 3.2 진행 상황 콜백

자식 에이전트가 도구를 호출할 때마다, 부모의 CLI 스피너(또는 게이트웨이)에 실시간으로 표시된다:

```
  [1] ├─ 🔍 web_search  "Python asyncio best practices"
  [1] ├─ 💭 "결과를 분석하면..."
  [2] ├─ 📁 read_file  "src/main.py"
  ✓ [1/3] Research Python asyncio  (12.5s)
  ✗ [2/3] Analyze codebase  (8.3s)
```

`_build_child_progress_callback()` 함수가 이 콜백을 구성한다:

```
자식 에이전트 도구 호출
        │
        ▼
  _callback("tool.started", tool_name, preview)
        │
        ├─ CLI 경로: spinner.print_above(...)  ← 스피너 위에 한 줄 출력
        │
        └─ Gateway 경로: _batch에 축적 → 5개마다 parent_cb에 전달
```

**배치 모드에서만** `[1]`, `[2]` 같은 인덱스 접두사가 붙는다. 단일 모드에서는 불필요하므로 생략된다.

### 3.3 작업 완료 추적

`as_completed(futures)` 이터레이터가 완료된 순서대로 결과를 수집한다. 각 완료 시점에:

1. 완료 라인을 스피너 위에 출력 (`✓` 또는 `✗`)
2. 남은 작업 수로 스피너 텍스트 업데이트
3. 최종적으로 `task_index` 기준 정렬하여 입력 순서와 결과 순서를 일치시킴

---

## 4. 차단된 도구 목록과 이유

```python
DELEGATE_BLOCKED_TOOLS = frozenset([
    "delegate_task",   # 재귀 위임 방지
    "clarify",         # 사용자 상호작용 불가
    "memory",          # 공유 MEMORY.md 쓰기 방지
    "send_message",    # 크로스 플랫폼 부작용 방지
    "execute_code",    # 단계별 추론을 유도하기 위해 차단
])
```

각 항목의 차단 이유를 상세히 분석한다:

| 도구 | 차단 이유 | 발생 가능한 문제 |
|------|----------|----------------|
| `delegate_task` | **재귀 위임 방지**. 자식이 다시 자식을 생성하면 지수적 에이전트 폭발이 일어남 | fork bomb의 LLM 버전. 비용 폭주와 시스템 자원 고갈 |
| `clarify` | **사용자 상호작용 불가**. 자식은 백그라운드에서 실행되며 `clarify_callback=None` | 자식이 사용자에게 질문하면 부모의 스피너가 무한 대기 상태에 빠짐 |
| `memory` | **공유 상태 격리**. MEMORY.md는 세션 전체의 학습 기록 | 여러 자식이 동시에 MEMORY.md를 쓰면 경쟁 상태(race condition) 발생 |
| `send_message` | **부작용 격리**. 메시지 전송은 외부 세계에 영향을 줌 | 자식이 사용자에게 직접 메시지를 보내면 혼란 야기 |
| `execute_code` | **추론 유도**. 자식은 도구를 직접 호출하여 단계별 사고해야 함 | 자식이 스크립트를 작성하면 이중 간접 참조가 되어 디버깅 불가 |

**왜 이렇게 만들었는가?** `_strip_blocked_tools()` 함수는 도구세트 레벨에서 차단한다:

```python
blocked_toolset_names = {"delegation", "clarify", "memory", "code_execution"}
return [t for t in toolsets if t not in blocked_toolset_names]
```

개별 도구가 아니라 **도구세트 전체**를 제거하는 점에 주목하라. 이는 향후 같은 카테고리에 새 도구가 추가되어도 자동으로 차단되게 만드는 방어적 설계이다.

---

## 5. 깊이 제한

```python
MAX_DEPTH = 2  # parent (0) -> child (1) -> grandchild rejected (2)
```

```
깊이 0: 부모 에이전트       ← 사용자와 직접 대화
   │
   └─ 깊이 1: 자식 에이전트   ← 위임받은 작업 수행 (허용)
         │
         └─ 깊이 2: 손자 에이전트  ← 거부! 깊이 제한 초과
```

깊이 검사는 `delegate_task()` 진입 시점에 수행된다:

```python
depth = getattr(parent_agent, '_delegate_depth', 0)
if depth >= MAX_DEPTH:
    return json.dumps({
        "error": "Delegation depth limit reached (2). "
                 "Subagents cannot spawn further subagents."
    })
```

그리고 자식 생성 시 깊이를 증가시킨다:

```python
child._delegate_depth = getattr(parent_agent, '_delegate_depth', 0) + 1
```

**왜 2단계인가?** 1단계(자식만 허용)는 너무 제한적이다. 자식이 복잡한 작업을 더 작은 단위로 분해하는 것은 유용할 수 있다. 하지만 3단계 이상은:
- 디버깅이 사실상 불가능 (어떤 에이전트가 무엇을 했는지 추적 불가)
- 비용이 지수적으로 증가 (3^3 = 27개 동시 에이전트 가능)
- 타임아웃 계단식 전파 문제 (손자가 느리면 자식도 느리고 부모도 느림)

---

## 6. _last_resolved_tool_names 전역 상태 관리

이것은 `delegate_tool.py`에서 가장 미묘한 부분이다. 문제의 원인부터 살펴보자.

### 6.1 문제 상황

`model_tools._last_resolved_tool_names`는 **프로세스 전역 변수**이다. `AIAgent()` 생성자가 `get_tool_definitions()`를 호출하면, 이 전역 변수가 해당 에이전트의 도구 이름으로 덮어씌워진다.

```
시간순서:
1. 부모 생성 → _last_resolved_tool_names = ["terminal", "file", "web", ...]
2. 자식 A 생성 → _last_resolved_tool_names = ["terminal", "file"]  ← 부모 값 소실!
3. 자식 B 생성 → _last_resolved_tool_names = ["terminal", "web"]   ← 자식 A 값 소실!
4. 자식 A 실행 완료 → execute_code가 _last_resolved_tool_names를 참조
   → 자식 B의 도구 목록을 보게 됨!  ← 버그!
```

### 6.2 해결: 저장/복원 패턴

```python
# delegate_task() 진입 시: 부모의 도구 이름 저장
import model_tools as _model_tools
_parent_tool_names = list(_model_tools._last_resolved_tool_names)

# 각 자식에게 부모의 도구 이름 첨부
try:
    for i, t in enumerate(task_list):
        child = _build_child_agent(...)
        child._delegate_saved_tool_names = _parent_tool_names
finally:
    # 자식 빌드 후 즉시 부모 값으로 복원 (예외가 발생해도)
    _model_tools._last_resolved_tool_names = _parent_tool_names
```

그리고 `_run_single_child()`의 `finally` 블록에서:

```python
finally:
    saved_tool_names = getattr(child, "_delegate_saved_tool_names", None)
    if isinstance(saved_tool_names, list):
        model_tools._last_resolved_tool_names = list(saved_tool_names)
```

**왜 이렇게 만들었는가?** 전역 변수를 스레드 로컬이나 `ContextVar`로 바꾸는 것이 이상적이지만, `_last_resolved_tool_names`는 `execute_code` 샌드박스의 RPC 서버를 포함해 여러 모듈에서 참조한다. 기존 코드의 대규모 리팩토링 없이, 위임 전후로 저장/복원하는 실용적인 접근을 택했다.

---

## 7. execute_code 샌드박스

`delegate_task`와는 다른 접근인 `execute_code`도 일종의 "작업 위임"이다. LLM이 Python 스크립트를 작성하면, 격리된 환경에서 실행하고 결과만 반환한다.

### 7.1 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                  부모 프로세스 (Hermes)                │
│                                                     │
│  ┌──────────────┐     ┌──────────────────────────┐  │
│  │ RPC 서버      │◄────│ Unix Domain Socket (UDS) │  │
│  │ (스레드)      │     │ 또는 파일 기반 RPC        │  │
│  │              │────►│                          │  │
│  │ tool dispatch │     └──────────┬───────────────┘  │
│  └──────────────┘                │                   │
│         │                        │                   │
│  handle_function_call()          │                   │
└─────────────────────────────────│───────────────────┘
                                   │
                    ┌──────────────▼───────────────┐
                    │      자식 프로세스 (격리)       │
                    │                              │
                    │  import hermes_tools         │
                    │  result = hermes_tools.      │
                    │           web_search(...)    │
                    │                              │
                    │  API 키: 제거됨               │
                    │  stdout만 부모에게 전달         │
                    └──────────────────────────────┘
```

### 7.2 허용된 도구 (7개만)

```python
SANDBOX_ALLOWED_TOOLS = frozenset([
    "web_search", "web_extract",       # 웹 접근
    "read_file", "write_file",         # 파일 I/O
    "search_files", "patch",           # 파일 검색/수정
    "terminal",                        # 셸 명령
])
```

`delegate_task`, `clarify`, `memory`, `send_message`, `execute_code` 자체는 샌드박스 내에서 사용할 수 없다. RPC 서버가 허용 목록을 강제한다:

```python
if tool_name not in allowed_tools:
    resp = json.dumps({
        "error": f"Tool '{tool_name}' is not available in execute_code."
    })
```

### 7.3 API 키 제거

로컬 백엔드에서는 `_sanitize_subprocess_env()`가 모든 LLM 프로바이더의 API 키를 환경변수에서 제거한다:

```python
_HERMES_PROVIDER_ENV_BLOCKLIST = _build_provider_env_blocklist()
# OPENAI_API_KEY, ANTHROPIC_API_KEY, OPENROUTER_API_KEY, ...
# 총 40+ 개의 환경변수가 차단됨
```

### 7.4 출력 검열

스크립트의 stdout/stderr는 `redact_sensitive_text()`를 거쳐 비밀이 LLM 컨텍스트에 유출되지 않도록 한다:

```python
from agent.redact import redact_sensitive_text
stdout_text = redact_sensitive_text(stdout_text)
stderr_text = redact_sensitive_text(stderr_text)
```

**왜 이렇게 만들었는가?** 환경변수를 차단해도, 스크립트가 `open('~/.hermes/.env')`로 디스크에서 비밀을 읽을 수 있다. 따라서 출력 단계에서도 이중으로 검열하는 심층 방어(defense in depth) 전략을 적용한다.

---

## 8. 실전 패턴

### 8.1 효과적인 단일 위임

```json
{
  "goal": "src/auth.py의 login() 함수에서 발생하는 JWT 만료 버그를 분석하고 수정 방안 제안",
  "context": "파일 경로: /workspace/src/auth.py\n에러: jwt.ExpiredSignatureError at line 45\nPython 3.11, PyJWT 2.8.0",
  "toolsets": ["terminal", "file"]
}
```

**핵심 원칙**: 자식은 부모의 대화를 전혀 모른다. `context`에 파일 경로, 에러 메시지, 환경 정보를 모두 포함해야 한다.

### 8.2 효과적인 병렬 위임

```json
{
  "tasks": [
    {
      "goal": "경쟁사 A의 가격 정책을 조사하고 요약",
      "toolsets": ["web"]
    },
    {
      "goal": "경쟁사 B의 가격 정책을 조사하고 요약",
      "toolsets": ["web"]
    },
    {
      "goal": "우리 제품의 현재 가격 구조를 분석",
      "toolsets": ["terminal", "file"]
    }
  ]
}
```

**언제 병렬이 좋은가**: 각 작업이 독립적이고, 서로의 결과를 필요로 하지 않을 때. 위 예시에서 세 조사는 완전히 독립적이다.

### 8.3 결과 구조 이해

각 자식의 결과는 다음 JSON 구조를 따른다:

```json
{
  "task_index": 0,
  "status": "completed",        // "completed" | "failed" | "error" | "interrupted"
  "summary": "분석 결과 요약...",
  "api_calls": 12,
  "duration_seconds": 15.3,
  "model": "hermes-3-llama-3.1-70b",
  "exit_reason": "completed",   // "completed" | "max_iterations" | "interrupted"
  "tokens": {"input": 15000, "output": 3000},
  "tool_trace": [
    {"tool": "read_file", "args_bytes": 45, "result_bytes": 1200, "status": "ok"},
    {"tool": "terminal", "args_bytes": 30, "result_bytes": 500, "status": "ok"}
  ]
}
```

`tool_trace`는 디버깅에 특히 유용하다. 자식이 어떤 도구를 어떤 순서로 호출했는지, 에러가 발생했는지를 부모가 파악할 수 있다.

### 8.4 위임 vs execute_code 선택 기준

```
                        추론이 필요한가?
                             │
                    ┌────────┴────────┐
                   예                  아니오
                    │                  │
              delegate_task       execute_code
                    │                  │
          "이 버그를 분석해"      "이 10개 파일의 줄 수를
                                  세고 CSV로 만들어"
```

| 기준 | delegate_task | execute_code |
|------|--------------|-------------|
| LLM 추론 | 자식이 독립적으로 추론 | 스크립트 로직만 실행 |
| 비용 | 높음 (별도 LLM 세션) | 낮음 (스크립트 실행만) |
| 도구 접근 | 제한된 도구세트 | RPC를 통한 7개 도구 |
| 적합한 작업 | 디버깅, 리서치, 코드 리뷰 | 데이터 수집, 반복 작업, 변환 |

### 8.5 인터럽트 전파

부모가 Ctrl+C로 중단되면, 활성 자식들에게도 전파된다:

```python
# 자식 생성 시 등록
if hasattr(parent_agent, '_active_children'):
    parent_agent._active_children.append(child)

# 자식 완료 시 등록 해제 (finally 블록)
parent_agent._active_children.remove(child)
```

이 구조 덕분에 부모가 중단되면 모든 자식도 함께 중단되어 API 비용 낭비를 방지한다.

---

## 핵심 정리

1. **서브에이전트 위임은 컨텍스트 격리, 비용 절감, 병렬성의 세 가지 이점을 제공한다.** 부모는 위임 호출과 요약만 보고, 자식의 중간 과정은 완전히 숨겨진다.

2. **각 자식은 완전히 격리된 환경에서 실행된다.** 별도 대화, 별도 task_id, 제한된 도구세트, 독립 시스템 프롬프트를 갖는다.

3. **ThreadPoolExecutor로 최대 3개 작업을 동시 실행하며**, 진행 상황 콜백으로 부모의 CLI/게이트웨이에 실시간 표시된다.

4. **5개 도구가 차단된다**: `delegate_task`(재귀 방지), `clarify`(사용자 접근 불가), `memory`(공유 상태 보호), `send_message`(부작용 격리), `execute_code`(이중 간접 방지).

5. **깊이 제한 MAX_DEPTH=2**는 parent -> child까지만 허용하고, grandchild를 거부하여 비용 폭발을 방지한다.

6. **`_last_resolved_tool_names` 전역 변수**는 자식 생성이 부모의 도구 목록을 덮어쓰는 문제를 try/finally 저장/복원 패턴으로 해결한다.

7. **`execute_code`는 다른 종류의 위임**으로, LLM 추론 없이 Python 스크립트를 격리 실행한다. API 키 제거와 출력 검열로 이중 방어한다.

8. **위임 선택 기준**: 추론이 필요하면 `delegate_task`, 기계적 반복이면 `execute_code`, 단순 호출이면 직접 도구 사용.
