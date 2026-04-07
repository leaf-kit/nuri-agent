# 강좌 03: 도구 시스템 완전 해부

> **이 강좌에서 배우는 것**
>
> - 자가 등록 레지스트리 패턴의 메커니즘과 설계 이유
> - 도구의 전체 생애주기 (등록부터 결과 반환까지)
> - 도구세트(Toolset) 시스템으로 도구를 논리적으로 그룹화하는 방법
> - 동기 에이전트 루프에서 비동기 도구를 호출하는 async 브릿징
> - 새 도구를 추가하는 실습 가이드 (step-by-step)
> - 핸들러 규약과 에러 래핑
> - 에이전트 수준 도구가 일반 레지스트리를 거치지 않는 이유

---

## 1. 자가 등록 레지스트리 패턴

### 메커니즘

Hermes Agent의 도구 시스템은 **Python import 부수효과**를 활용한 자가 등록 패턴을 사용한다.

```
[시점 1] model_tools.py가 로드됨
    |
    v
[시점 2] _discover_tools() 호출
    |
    v
[시점 3] importlib.import_module("tools.web_tools") 실행
    |
    v
[시점 4] tools/web_tools.py 모듈이 파이썬 인터프리터에 로드됨
    |
    v
[시점 5] 모듈 하단의 registry.register() 호출이 실행됨 (import 부수효과)
    |
    v
[시점 6] ToolRegistry._tools 딕셔너리에 도구 등록 완료
```

핵심 코드:

```python
# model_tools.py
def _discover_tools():
    _modules = [
        "tools.web_tools",
        "tools.terminal_tool",
        "tools.file_tools",
        "tools.vision_tools",
        # ... 20+ 모듈
    ]
    import importlib
    for mod_name in _modules:
        try:
            importlib.import_module(mod_name)
        except Exception as e:
            logger.warning("Could not import tool module %s: %s", mod_name, e)

_discover_tools()  # 모듈 로드 시 즉시 실행
```

```python
# tools/registry.py
class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, ToolEntry] = {}     # name -> ToolEntry
        self._toolset_checks: Dict[str, Callable] = {}  # toolset -> check_fn

    def register(self, name, toolset, schema, handler, check_fn=None,
                 requires_env=None, is_async=False, description="", emoji=""):
        self._tools[name] = ToolEntry(
            name=name, toolset=toolset, schema=schema, handler=handler,
            check_fn=check_fn, requires_env=requires_env or [],
            is_async=is_async, description=description, emoji=emoji,
        )

# 모듈 수준 싱글턴
registry = ToolRegistry()
```

### 왜 이 패턴을 선택했는가?

**대안 1: 중앙 등록 파일**

```python
# 이렇게 하지 않는다!
TOOLS = {
    "web_search": {"handler": web_tools.handle_web_search, ...},
    "terminal": {"handler": terminal_tool.handle_terminal, ...},
    # ... 50개의 도구를 여기에 모두 나열
}
```

문제점:
- 새 도구 추가 시 이 파일 수정 필요 -> 병합 충돌
- 도구 파일과 등록이 분리 -> 불일치 발생 가능
- 20명 기여자가 동시에 같은 파일 수정

**대안 2: 데코레이터 기반 등록**

```python
@tool_registry.register(name="web_search", ...)
def handle_web_search(args): ...
```

문제점:
- 데코레이터가 함수 시그니처를 변경할 수 있음
- 스키마 정의가 데코레이터 인자에 묶여 가독성 저하
- 런타임에 등록 순서 제어 어려움

**선택: 명시적 register() 호출**

```python
# 각 도구 파일 하단에서
registry.register(
    name="web_search",
    toolset="web",
    schema={
        "name": "web_search",
        "description": "Search the web using...",
        "parameters": {...}
    },
    handler=handle_web_search,
    check_fn=lambda: bool(os.getenv("SERPER_API_KEY")),
    requires_env=["SERPER_API_KEY"],
    emoji="🔍",
)
```

장점:
- **자기 완결적**: 도구 파일 하나에 스키마 + 핸들러 + 가용성 검사 + 메타데이터가 모두 있음
- **독립적**: 다른 도구 파일을 수정하지 않고 새 파일 추가만으로 등록
- **실패 격리**: `_discover_tools()`가 try/except으로 감싸므로, 하나가 실패해도 나머지 등록 가능
- **순환 의존 방지**: `registry.py`가 어떤 도구 파일도 import하지 않음

---

## 2. 도구의 생애주기

도구 하나가 사용자의 요청을 처리하는 전체 생애주기:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 등록 (Registration)                                       │
│    시점: Python 프로세스 시작 시 (import 부수효과)             │
│    동작: registry.register() -> ToolEntry 생성 -> _tools에 저장 │
└─────────────────────────────────────────┬───────────────────┘
                                          v
┌─────────────────────────────────────────────────────────────┐
│ 2. 발견 (Discovery)                                          │
│    시점: _discover_tools() + MCP 탐색 + 플러그인 탐색         │
│    동작: importlib.import_module() -> 각 모듈의 register() 트리거 │
│    추가: discover_mcp_tools() -> 외부 MCP 서버 도구도 등록     │
│    추가: discover_plugins() -> pip/user 플러그인 도구 등록     │
└─────────────────────────────────────────┬───────────────────┘
                                          v
┌─────────────────────────────────────────────────────────────┐
│ 3. 스키마 수집 (Schema Collection)                            │
│    시점: AIAgent.__init__() -> get_tool_definitions()         │
│    동작:                                                      │
│      (a) toolsets.py에서 활성 도구세트 해석 -> 도구 이름 집합   │
│      (b) registry.get_definitions(tool_names) 호출            │
│      (c) 각 도구의 check_fn() 실행 -> 가용성 확인             │
│      (d) 가용한 도구만 OpenAI 형식 스키마로 반환               │
│    결과: self.tools = [{"type":"function","function":{...}}, ...]│
└─────────────────────────────────────────┬───────────────────┘
                                          v
┌─────────────────────────────────────────────────────────────┐
│ 4. 가용성 확인 (Availability Check)                           │
│    시점: get_definitions() 내부, 도구별 1회                   │
│    동작: check_fn이 있으면 호출                               │
│    예시:                                                      │
│      web_search: lambda: bool(os.getenv("SERPER_API_KEY"))   │
│      terminal:   lambda: True (항상 가용)                     │
│      browser_*:  lambda: playwright_available()               │
│    캐싱: 같은 check_fn 객체는 결과를 재사용 (동일 toolset)     │
│    실패 처리: 예외 발생 시 False 반환 (crash 방지)             │
└─────────────────────────────────────────┬───────────────────┘
                                          v
┌─────────────────────────────────────────────────────────────┐
│ 5. 디스패치 (Dispatch)                                        │
│    시점: LLM이 tool_calls를 반환했을 때                       │
│    경로:                                                      │
│      run_agent.py -> handle_function_call() -> registry.dispatch() │
│    동작:                                                      │
│      (a) coerce_tool_args(): 문자열 "42" -> 정수 42 변환      │
│      (b) pre_tool_call 플러그인 훅 호출                       │
│      (c) registry.dispatch(name, args, task_id=...) 호출     │
│      (d) handler 실행 (sync 또는 async 브릿징)               │
│      (e) post_tool_call 플러그인 훅 호출                      │
└─────────────────────────────────────────┬───────────────────┘
                                          v
┌─────────────────────────────────────────────────────────────┐
│ 6. 결과 반환 (Result Return)                                  │
│    형식: JSON 문자열 (항상)                                   │
│    대형 결과: 100K 문자 초과 시 파일 저장 + 미리보기 반환      │
│    에러: {"error": "Tool execution failed: ..."} JSON         │
│    후처리: messages에 {"role":"tool","content":result} 추가   │
└─────────────────────────────────────────────────────────────┘
```

### check_fn 캐싱의 영리한 설계

```python
# registry.py get_definitions() 내부
check_results: Dict[Callable, bool] = {}  # check_fn 객체 -> 결과

for name in sorted(tool_names):
    entry = self._tools.get(name)
    if entry.check_fn:
        if entry.check_fn not in check_results:  # 같은 함수면 재사용
            check_results[entry.check_fn] = bool(entry.check_fn())
```

같은 toolset의 도구 11개(browser_*)가 모두 동일한 `check_fn`을 공유하면, 가용성 검사는 **1번만** 실행된다. 함수 **객체의 identity**를 키로 사용하는 영리한 캐싱이다.

---

## 3. 도구세트(Toolset) 시스템

### 왜 도구를 그룹으로 묶는가?

Hermes Agent에는 50개 이상의 도구가 있다. 모든 도구의 스키마를 LLM에 전달하면:

1. **토큰 낭비**: 도구 스키마만 20,000-30,000+ 토큰 소비
2. **선택 혼란**: LLM이 불필요한 도구를 선택할 확률 증가
3. **보안 리스크**: 특정 환경에서 터미널 접근을 차단해야 할 수 있음

### 도구세트 정의 구조

```python
# toolsets.py
TOOLSETS = {
    # 기본 도구세트: 개별 도구 그룹
    "web": {
        "description": "Web research and content extraction tools",
        "tools": ["web_search", "web_extract"],
        "includes": []
    },
    "terminal": {
        "description": "Terminal/command execution and process management tools",
        "tools": ["terminal", "process"],
        "includes": []
    },
    "browser": {
        "description": "Browser automation tools",
        "tools": ["browser_navigate", "browser_snapshot", "browser_click",
                  "browser_type", "browser_scroll", "browser_back",
                  "browser_press", "browser_close", "browser_get_images",
                  "browser_vision", "browser_console"],
        "includes": []
    },

    # 합성 도구세트: 다른 도구세트를 포함
    "research": {
        "description": "Research-focused toolset",
        "tools": [],
        "includes": ["web", "vision", "file"]  # 다른 도구세트 참조
    },
    "development": {
        "description": "Software development toolset",
        "tools": [],
        "includes": ["terminal", "file", "web", "code_execution"]
    },
}
```

### 플랫폼별 도구세트 프리셋

```python
# toolsets.py
_HERMES_CORE_TOOLS = [
    "web_search", "web_extract",
    "terminal", "process",
    "read_file", "write_file", "patch", "search_files",
    "vision_analyze", "image_generate",
    # ... 전체 목록
]
```

`_HERMES_CORE_TOOLS`는 **모든 플랫폼**이 공유하는 기본 도구 목록이다. 플랫폼별 도구세트(`hermes-cli`, `hermes-telegram` 등)는 이 공유 목록을 기반으로 정의된다. 한 곳을 수정하면 모든 플랫폼에 반영된다.

### 도구세트 해석 (Resolution)

```python
# toolsets.py
def resolve_toolset(name: str) -> Set[str]:
    """도구세트 이름을 실제 도구 이름 집합으로 해석"""
    toolset = TOOLSETS.get(name)
    if not toolset:
        return set()
    
    result = set(toolset.get("tools", []))
    
    # includes로 참조된 다른 도구세트를 재귀적으로 해석
    for included in toolset.get("includes", []):
        result.update(resolve_toolset(included))
    
    return result
```

CLI에서의 사용:

```bash
# web + vision 도구만 활성화
hermes --enabled-toolsets web,vision "이미지 분석해줘"

# terminal 도구 비활성화 (보안 환경)
hermes --disabled-toolsets terminal "코드 리뷰해줘"

# 합성 도구세트 사용
hermes --enabled-toolsets research "최신 논문 조사해줘"
```

### 동적 스키마 재작성

도구세트 필터링 후, 일부 도구의 스키마가 **동적으로 재작성**된다:

```python
# model_tools.py get_tool_definitions() 내부

# execute_code의 스키마: 실제 가용한 도구만 명시
if "execute_code" in available_tool_names:
    sandbox_enabled = SANDBOX_ALLOWED_TOOLS & available_tool_names
    dynamic_schema = build_execute_code_schema(sandbox_enabled)

# browser_navigate의 설명: web_search가 없으면 참조 제거
if "browser_navigate" in available_tool_names:
    if not {"web_search", "web_extract"} & available_tool_names:
        # "prefer web_search or web_extract" 문구 삭제
        desc = desc.replace("prefer web_search or web_extract...", "")
```

**왜 이렇게 만들었는가?** LLM은 스키마에 언급된 도구를 실제로 호출하려 한다. `web_search`가 비활성화되었는데 스키마에 "prefer web_search"라고 적혀 있으면, LLM이 환각(hallucination)으로 `web_search`를 호출한다. 가용한 도구만 스키마에 언급되도록 동적으로 정리한다.

---

## 4. 비동기 브릿징

### 문제

에이전트의 메인 루프(`run_conversation`)는 **동기(synchronous)** 코드다. 하지만 일부 도구(웹 검색, 브라우저 자동화, MCP 서버 통신)는 **비동기(async)** 함수다.

```python
# 동기 루프
while budget.remaining > 0:
    response = api_call()           # 동기 (또는 스트리밍)
    for tool_call in tool_calls:
        result = dispatch(tool)     # 여기서 async 도구를 호출해야 함!
```

### 해결: 3계층 비동기 브릿지

`model_tools.py`의 `_run_async()` 함수가 모든 sync->async 변환의 **단일 소스**다:

```python
def _run_async(coro):
    """동기 컨텍스트에서 비동기 코루틴을 실행"""
    
    try:
        loop = asyncio.get_running_loop()  # 이미 이벤트 루프가 있는가?
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # ── 경우 1: async 컨텍스트 안 (gateway, RL 환경) ──
        # 이미 이벤트 루프가 돌고 있으므로 같은 루프에서 실행 불가
        # 별도 스레드에서 asyncio.run() 실행
        with ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result(timeout=300)

    if threading.current_thread() is not threading.main_thread():
        # ── 경우 2: 워커 스레드 (delegate_task의 병렬 실행) ──
        # 스레드별 영속 루프 사용 (스레드 수명 동안 유지)
        worker_loop = _get_worker_loop()
        return worker_loop.run_until_complete(coro)

    # ── 경우 3: 메인 스레드 CLI 경로 (가장 흔한 경우) ──
    # 영속 이벤트 루프 사용 (프로세스 수명 동안 유지)
    tool_loop = _get_tool_loop()
    return tool_loop.run_until_complete(coro)
```

### 왜 영속 루프(persistent loop)인가?

```python
# _get_tool_loop() - 영속 루프
_tool_loop = None
_tool_loop_lock = threading.Lock()

def _get_tool_loop():
    global _tool_loop
    with _tool_loop_lock:
        if _tool_loop is None or _tool_loop.is_closed():
            _tool_loop = asyncio.new_event_loop()
        return _tool_loop
```

`asyncio.run()`을 매번 호출하면 **새 루프를 만들고 닫는다**. 문제는 httpx, AsyncOpenAI 같은 비동기 HTTP 클라이언트가 루프에 캐시되어 있다는 것이다. 루프가 닫히면 이 클라이언트들이 가비지 컬렉션 시 "Event loop is closed" 에러를 발생시킨다.

영속 루프는 프로세스(또는 스레드) 수명 동안 살아 있으므로, 캐시된 클라이언트가 정상적으로 정리된다.

### 워커 스레드 루프의 격리

```python
# 스레드 로컬 저장소에 루프 보관
_worker_thread_local = threading.local()

def _get_worker_loop():
    loop = getattr(_worker_thread_local, 'loop', None)
    if loop is None or loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        _worker_thread_local.loop = loop
    return loop
```

`delegate_task`의 `ThreadPoolExecutor`에서 여러 서브에이전트가 동시 실행될 때, **각 워커 스레드가 자신만의 루프**를 가진다. 메인 스레드의 공유 루프와 경합하지 않고, 스레드 간에도 격리된다.

---

## 5. 도구 추가 실습 (Step-by-step)

새로운 도구 `weather_check`를 추가하는 전체 과정:

### Step 1: 도구 파일 생성

```python
# tools/weather_tool.py
"""Weather information tool for Hermes Agent."""

import json
import os
import logging
from tools.registry import registry

logger = logging.getLogger(__name__)


def _check_weather_available():
    """가용성 검사: API 키가 설정되었는가?"""
    return bool(os.getenv("WEATHER_API_KEY"))


def handle_weather_check(args: dict, **kwargs) -> str:
    """도구 핸들러: 날씨 정보 조회"""
    city = args.get("city", "")
    if not city:
        return json.dumps({"error": "city parameter is required"})
    
    api_key = os.getenv("WEATHER_API_KEY")
    # task_id는 kwargs에서 추출 (세션 격리용)
    task_id = kwargs.get("task_id", "default")
    
    try:
        # 실제 API 호출 로직
        import requests
        resp = requests.get(
            f"https://api.weather.example.com/current",
            params={"city": city, "key": api_key},
            timeout=10,
        )
        data = resp.json()
        return json.dumps({
            "city": city,
            "temperature": data["temp"],
            "condition": data["condition"],
        }, ensure_ascii=False)
    except Exception as e:
        logger.error("Weather API error: %s", e)
        return json.dumps({"error": f"Weather lookup failed: {e}"})


# ═══ 자가 등록 ═══
registry.register(
    name="weather_check",           # LLM이 호출할 도구 이름
    toolset="weather",              # 논리적 그룹 (toolsets.py에도 추가 필요)
    schema={
        "name": "weather_check",
        "description": "Get current weather information for a city. "
                       "Returns temperature and weather condition.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name (e.g., 'Seoul', 'Tokyo', 'New York')"
                },
            },
            "required": ["city"],
        },
    },
    handler=handle_weather_check,
    check_fn=_check_weather_available,
    requires_env=["WEATHER_API_KEY"],
    is_async=False,                 # 동기 핸들러
    description="Check weather for a city",
    emoji="🌤️",
)
```

### Step 2: 발견 목록에 추가

```python
# model_tools.py _discover_tools() 내부의 _modules 리스트에 추가
_modules = [
    "tools.web_tools",
    "tools.terminal_tool",
    # ...
    "tools.weather_tool",       # ← 추가
]
```

### Step 3: 도구세트 정의 (선택사항)

```python
# toolsets.py TOOLSETS에 추가
TOOLSETS = {
    # ...
    "weather": {
        "description": "Weather information tools",
        "tools": ["weather_check"],
        "includes": [],
    },
}
```

### Step 4: 코어 도구 목록에 추가 (모든 플랫폼에서 사용하려면)

```python
# toolsets.py
_HERMES_CORE_TOOLS = [
    # ...
    "weather_check",    # ← 추가
]
```

### Step 5: 테스트

```bash
# 도구 등록 확인
python -c "from model_tools import get_all_tool_names; print(get_all_tool_names())"

# 가용성 확인
export WEATHER_API_KEY="test-key"
python -c "from model_tools import check_tool_availability; print(check_tool_availability())"

# 직접 호출 테스트
python -c "
from model_tools import handle_function_call
result = handle_function_call('weather_check', {'city': 'Seoul'})
print(result)
"
```

### register()의 각 매개변수 의미

| 매개변수 | 타입 | 필수 | 설명 |
|----------|------|------|------|
| `name` | `str` | O | LLM이 호출할 고유 이름. OpenAI function calling의 `name` 필드 |
| `toolset` | `str` | O | 논리적 그룹명. 필터링과 가용성 검사의 단위 |
| `schema` | `dict` | O | OpenAI function calling 형식의 JSON Schema |
| `handler` | `Callable` | O | 실제 도구 로직. `(args: dict, **kwargs) -> str` |
| `check_fn` | `Callable` | X | `() -> bool`. False 반환 시 도구가 LLM에 노출되지 않음 |
| `requires_env` | `list` | X | 필요한 환경 변수 목록 (진단 표시용, 실제 검사는 check_fn) |
| `is_async` | `bool` | X | True이면 handler가 코루틴, `_run_async`로 브릿징됨 |
| `description` | `str` | X | 사람이 읽는 설명 (schema.description 대체) |
| `emoji` | `str` | X | CLI 출력에서 사용하는 이모지 |

---

## 6. 핸들러 규약

모든 도구 핸들러는 다음 규약을 따른다:

### 규약 1: JSON 문자열 반환

```python
# 올바른 패턴
def handle_my_tool(args: dict, **kwargs) -> str:
    result = {"data": "value", "count": 42}
    return json.dumps(result, ensure_ascii=False)

# 잘못된 패턴 (dict 반환 - 안됨!)
def handle_my_tool(args: dict, **kwargs) -> dict:  # X
    return {"data": "value"}
```

**이유**: LLM API는 도구 결과를 문자열로만 받는다. `registry.dispatch()`가 반환값을 그대로 `messages`에 삽입하므로, 핸들러가 문자열을 반환해야 한다.

### 규약 2: task_id 전파

```python
def handle_terminal(args: dict, **kwargs) -> str:
    task_id = kwargs.get("task_id", "default")
    # task_id로 VM 인스턴스를 격리
    # 동시 실행되는 여러 에이전트가 서로의 터미널을 간섭하지 않음
```

`task_id`는 `run_conversation()`에서 생성되어 모든 도구 호출에 전파된다. 터미널 도구는 이를 사용해 VM 인스턴스를 격리하고, 브라우저 도구는 세션을 격리한다.

### 규약 3: 에러 래핑

```python
# registry.py dispatch() 내부
try:
    return entry.handler(args, **kwargs)
except Exception as e:
    logger.exception("Tool %s dispatch error: %s", name, e)
    return json.dumps({"error": f"Tool execution failed: {type(e).__name__}: {e}"})
```

도구 핸들러가 예외를 발생시켜도 에이전트 루프는 중단되지 않는다. 예외는 JSON 에러로 래핑되어 LLM에게 반환된다. LLM은 에러를 보고 다른 접근법을 시도하거나 사용자에게 보고한다.

**핸들러 내부에서도 에러를 JSON으로 반환하는 것이 모범 사례**:

```python
def handle_my_tool(args: dict, **kwargs) -> str:
    city = args.get("city")
    if not city:
        return json.dumps({"error": "city parameter is required"})
    # ...
```

### 규약 4: 인자 타입 강제 변환 (coercion)

LLM이 `"42"`(문자열)를 보내야 할 곳에 `42`(정수)를 보내거나 그 반대인 경우가 흔하다. `model_tools.py`의 `coerce_tool_args()`가 스키마를 기반으로 자동 변환한다:

```python
def coerce_tool_args(tool_name, args):
    schema = registry.get_schema(tool_name)
    properties = schema["parameters"]["properties"]
    
    for key, value in args.items():
        if isinstance(value, str):
            expected = properties[key].get("type")
            if expected == "integer":
                args[key] = int(value)      # "42" -> 42
            elif expected == "boolean":
                args[key] = value == "true"  # "true" -> True
```

---

## 7. 에이전트 수준 도구 vs 레지스트리 도구

### 가로채기(intercept) 대상 도구

```python
# run_agent.py
_AGENT_LOOP_TOOLS = {"todo", "memory", "session_search", "delegate_task"}
```

이 4개 도구는 `model_tools.handle_function_call()`로 가지 **않는다**. `run_agent.py`의 루프 내부에서 **직접 처리**된다.

```python
# run_agent.py run_conversation() 내부 (의사 코드)
for tool_call in tool_calls:
    if tool_call.name == "memory":
        result = self._memory_store.handle(tool_call.args)  # 직접 처리
    elif tool_call.name == "todo":
        result = self._todo_store.handle(tool_call.args)    # 직접 처리
    elif tool_call.name == "delegate_task":
        result = self._handle_delegation(tool_call.args)    # 서브에이전트 생성
    elif tool_call.name == "session_search":
        result = self._session_db.search(tool_call.args)    # DB 직접 접근
    else:
        result = handle_function_call(tool_call.name, ...)  # 레지스트리 경로
```

### 왜 레지스트리를 거치지 않는가?

| 도구 | 이유 |
|------|------|
| `memory` | `MemoryStore` 인스턴스가 `AIAgent`에 종속. 세션별 메모리 격리 필요 |
| `todo` | `TodoStore` 인스턴스가 `AIAgent`에 종속. Gateway에서 메시지마다 새 인스턴스 |
| `session_search` | `session_db` (SQLite 연결)가 `AIAgent`에 종속 |
| `delegate_task` | **새 `AIAgent`를 생성**해야 함. 부모의 설정(API 키, 모델, 콜백)을 상속 |

핵심 차이점:

```
레지스트리 도구 (stateless):
    handler(args) -> result
    외부 상태 없음, 어디서든 동일하게 동작

에이전트 수준 도구 (stateful):
    self._memory_store.handle(args) -> result
    AIAgent 인스턴스의 상태에 의존
```

### 스키마는 레지스트리에 등록되어 있다

가로채기 대상 도구도 **스키마만은** 레지스트리에 등록되어 있다. 이유:

1. `get_tool_definitions()`이 LLM에 전달할 스키마를 수집할 때 통합된 경로를 사용
2. toolset 필터링이 일관되게 동작
3. 도구 가용성 진단(`check_tool_availability`)에 포함

`registry.dispatch()`가 이 도구들을 받으면 스텁 에러를 반환한다:

```python
# model_tools.py
if function_name in _AGENT_LOOP_TOOLS:
    return json.dumps({"error": f"{function_name} must be handled by the agent loop"})
```

이 에러는 정상 경로에서는 절대 발생하지 않는다 (에이전트 루프가 먼저 가로채므로). 무언가 잘못되어 도구가 레지스트리 경로로 빠졌을 때의 안전장치다.

### deregister()의 용도

```python
# registry.py
def deregister(self, name: str) -> None:
    """도구 제거. MCP 동적 도구 갱신에 사용."""
    entry = self._tools.pop(name, None)
    if entry and not any(e.toolset == entry.toolset for e in self._tools.values()):
        self._toolset_checks.pop(entry.toolset, None)
```

MCP 서버가 `notifications/tools/list_changed` 알림을 보내면, 기존 도구를 모두 `deregister()`하고 새 목록으로 다시 `register()`한다 ("nuke and repave" 전략). 일반 도구에서는 사용하지 않는다.

---

## 핵심 정리

| 항목 | 요약 |
|------|------|
| **자가 등록 패턴** | `registry.register()`가 import 시 호출 -> 중앙 파일 수정 없이 도구 추가 |
| **생애주기 6단계** | 등록 -> 발견 -> 스키마 수집 -> 가용성 확인 -> 디스패치 -> 결과 반환 |
| **도구세트** | 논리적 그룹으로 필터링 + 합성 도구세트로 시나리오별 프리셋 |
| **비동기 브릿지** | `_run_async()` 단일 함수가 3가지 경우(async 컨텍스트, 워커 스레드, 메인 스레드) 처리 |
| **영속 루프** | `asyncio.run()` 대신 영속 루프 사용 -> httpx/AsyncOpenAI "Event loop is closed" 방지 |
| **핸들러 규약** | JSON 문자열 반환, task_id 전파, 예외는 JSON 에러로 래핑 |
| **에이전트 수준 도구** | memory, todo, session_search, delegate_task -> AIAgent 상태에 의존하므로 직접 처리 |
| **동적 스키마 재작성** | 가용한 도구만 스키마에 언급되도록 런타임에 정리 -> LLM 환각 방지 |
| **새 도구 추가** | 파일 생성 + register() + _modules 추가 + toolsets 추가 (4단계) |
