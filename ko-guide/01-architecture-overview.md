# 강좌 01: 아키텍처 전체 조감도

> **이 강좌에서 배우는 것**
>
> - Hermes Agent가 해결하려는 문제와 기존 에이전트 프레임워크와의 차별점
> - 핵심 모듈 6개의 역할과 상호 관계
> - 사용자 메시지가 최종 응답으로 변환되는 전체 데이터 흐름
> - 6가지 핵심 설계 원칙의 "왜"와 "어떻게"
> - 디렉토리 구조가 아키텍처를 어떻게 반영하는지
> - 순환 의존 없는 모듈 계층 구조

---

## 1. 프로젝트를 한마디로

Hermes Agent는 Nous Research가 만든 **자율형 도구 호출(tool-calling) AI 에이전트**다.

핵심 한 문장: **"LLM이 스스로 도구를 선택하고, 실행하고, 결과를 관찰하고, 다음 행동을 결정하는 폐쇄형 루프를 실행한다."**

기존 에이전트 프레임워크(LangChain, CrewAI 등)가 "체인"이나 "그래프"를 명시적으로 정의하도록 요구하는 반면, Hermes Agent는 다르다:

| 특징 | 기존 프레임워크 | Hermes Agent |
|------|----------------|--------------|
| 실행 흐름 제어 | 개발자가 체인/그래프 정의 | LLM이 자율적으로 도구 루프 실행 |
| 도구 등록 | 중앙 설정 파일 필요 | 자가 등록 패턴 (import 시 자동) |
| 컨텍스트 관리 | 수동 또는 없음 | 자동 압축 (5단계 알고리즘) |
| 멀티 플랫폼 | 별도 어댑터 직접 작성 | gateway 추상화로 CLI/Telegram/Discord 통합 |
| 학습 루프 | 없음 | RL 훈련 환경 내장, 궤적(trajectory) 저장 |

Hermes Agent의 진정한 차별점은 **자기 개선 루프**다. 에이전트가 실행한 궤적을 저장하고, 이를 강화학습(RL) 훈련 데이터로 재활용하며, 압축하여 더 효율적인 모델을 만들 수 있다. `trajectory_compressor.py`와 `rl_cli.py`가 이 순환을 완성한다.

---

## 2. 핵심 모듈 관계도

```
                        사용자 입력
                            |
                            v
    +---------------------------------------------------+
    |               run_agent.py (AIAgent)               |
    |  - 대화 루프 관리 (while loop)                     |
    |  - 시스템 프롬프트 조립                            |
    |  - 에이전트 수준 도구 가로채기 (memory, todo)       |
    |  - 컨텍스트 압축 트리거                            |
    |  - 반복 예산(IterationBudget) 관리                 |
    +--------+------------------+-----------+-----------+
             |                  |           |
             v                  v           v
    +-----------------+  +-------------+  +-------------------+
    | agent/           |  | model_tools |  | hermes_state.py   |
    | prompt_builder   |  |   .py       |  |  - SQLite 세션 DB |
    | context_compressor|  | (오케스트라) |  |  - FTS5 검색      |
    | model_metadata   |  |             |  |  - WAL 모드       |
    | prompt_caching   |  |             |  +-------------------+
    | usage_pricing    |  |             |
    +-----------------+  +------+------+
                                |
                                v
                   +-------------------------+
                   |  tools/registry.py      |
                   |  (ToolRegistry 싱글턴)   |
                   |  - register()           |
                   |  - get_definitions()    |
                   |  - dispatch()           |
                   +------+------------------+
                          |
          +-------+-------+-------+-------+-------+
          |       |       |       |       |       |
          v       v       v       v       v       v
       web_    file_  terminal browser  vision  ...20+
       tools   tools  _tool   _tool    _tools  도구들

    +---------------------------------------------------+
    |            gateway/run.py (GatewayRunner)          |
    |  - 플랫폼 어댑터 관리 (Telegram, Discord, ...)     |
    |  - SSL 인증서 자동 탐지                            |
    |  - config.yaml 환경 변수 브리지                    |
    +---------------------------------------------------+
```

**화살표의 의미**: 위에서 아래로 의존한다. `run_agent.py`는 `model_tools.py`에 의존하고, `model_tools.py`는 `tools/registry.py`에 의존한다. 역방향 의존은 없다.

---

## 3. 데이터 흐름: 사용자 메시지가 응답이 되기까지

### 단계 1: 메시지 수신

```
CLI (cli.py)  또는  Gateway (gateway/run.py)
        |
        v
    AIAgent.run_conversation(user_message, conversation_history)
```

- CLI는 `AIAgent`를 세션 동안 유지한다 (1개 인스턴스, 여러 번 `run_conversation` 호출).
- Gateway는 **메시지마다** 새 `AIAgent`를 생성한다 (상태는 SQLite `hermes_state.py`에서 복원).

### 단계 2: 시스템 프롬프트 조립

`agent/prompt_builder.py`의 여러 함수가 호출되어 시스템 프롬프트를 조립한다:

```python
# run_agent.py _build_system_prompt() 의사 코드
system_prompt = DEFAULT_AGENT_IDENTITY          # "You are Hermes Agent..."
system_prompt += PLATFORM_HINTS[platform]       # 플랫폼별 포매팅 힌트
system_prompt += build_skills_system_prompt()   # 스킬 인덱스
system_prompt += build_context_files_prompt()   # SOUL.md, AGENTS.md, .hermes.md
system_prompt += MEMORY_GUIDANCE                # 메모리 사용 가이드
system_prompt += load_soul_md()                 # 전역 퍼소나 파일
system_prompt += memory_store.format()          # 디스크에서 로드된 기억
```

**왜 이렇게 만들었는가?** 시스템 프롬프트가 한 번 조립되면 세션 동안 캐싱된다(`_cached_system_prompt`). Anthropic의 프롬프트 캐싱은 접두사(prefix)가 동일할 때 75% 비용 절감을 제공하므로, 시스템 프롬프트를 변경하지 않는 것이 경제적이다.

### 단계 3: LLM API 호출

```python
# run_agent.py 내부
api_messages = [system_prompt] + prefill_messages + conversation_history + [user_message]
api_messages = apply_anthropic_cache_control(api_messages)  # 캐시 브레이크포인트 삽입
api_messages = self._sanitize_api_messages(api_messages)    # 고아 도구 결과 정리
response = self._interruptible_streaming_api_call(api_kwargs)
```

스트리밍이 기본이다. 비스트리밍은 Mock 테스트에서만 사용된다. 이유: 90초 유휴 스트림 탐지와 60초 읽기 타임아웃으로 좀비 연결을 감지할 수 있기 때문이다.

### 단계 4: 도구 실행

LLM이 `tool_calls`를 반환하면:

```
response.choices[0].message.tool_calls = [
    {name: "web_search", arguments: '{"query": "..."}'},
    {name: "read_file", arguments: '{"path": "..."}'},
]
```

1. **에이전트 수준 도구 가로채기**: `memory`, `todo`, `session_search`, `delegate_task`는 `run_agent.py`에서 직접 처리
2. **레지스트리 디스패치**: 나머지는 `model_tools.handle_function_call()` -> `registry.dispatch()` 경로
3. **병렬 실행 판단**: `_should_parallelize_tool_batch()`가 배치 내 도구들이 안전하게 병렬 실행 가능한지 판단
4. **결과 크기 검증**: 100K 문자 초과 시 파일로 저장하고 미리보기만 반환

### 단계 5: 루프 반복 또는 종료

```
도구 결과를 messages에 추가 -> while 루프 상단으로 돌아감
     |
     +--> tool_calls가 없으면 -> 최종 응답 반환
     +--> IterationBudget 소진 -> 강제 종료
     +--> 인터럽트 요청 -> 즉시 종료
     +--> 컨텍스트 초과 -> 압축 후 재시도
```

### 단계 6: 응답 반환 및 세션 저장

```python
return {
    "messages": messages,           # 전체 대화 이력
    "final_response": content,      # 최종 텍스트 응답
    "api_calls": api_call_count,    # API 호출 횟수
    "completed": True,              # 정상 완료 여부
}
```

동시에 `hermes_state.py`의 SQLite DB에 메시지가 플러시되고, 궤적 저장이 활성화되어 있으면 JSONL 파일로 기록된다.

---

## 4. 6가지 핵심 설계 원칙

### 원칙 1: 자가 등록 레지스트리

**WHY**: 도구를 추가할 때 중앙 파일을 수정할 필요가 없어야 한다. 20개 이상의 도구 파일이 동시에 중앙 파일을 수정하면 병합 충돌이 폭발한다.

**HOW**: 각 `tools/*.py` 파일이 모듈 수준에서 `registry.register()`를 호출한다. `model_tools.py`가 `importlib.import_module()`로 모든 도구 모듈을 임포트하면, import 부수효과로 등록이 완료된다.

```python
# tools/web_tools.py (파일 하단)
registry.register(
    name="web_search",
    toolset="web",
    schema={...},
    handler=handle_web_search,
    check_fn=lambda: bool(os.getenv("SERPER_API_KEY")),
)
```

### 원칙 2: 레이어식 프롬프트

**WHY**: 시스템 프롬프트는 여러 관심사(identity, 플랫폼, 스킬, 메모리, 컨텍스트 파일)를 포함해야 하지만, 각각 독립적으로 변경 가능해야 한다.

**HOW**: `agent/prompt_builder.py`는 각 관심사를 별도 함수로 분리한다. `DEFAULT_AGENT_IDENTITY`, `PLATFORM_HINTS`, `MEMORY_GUIDANCE`, `build_skills_system_prompt()`, `build_context_files_prompt()`가 조합된다. 보안 스캐너(`_scan_context_content`)가 프롬프트 인젝션 패턴을 탐지한다.

### 원칙 3: 프롬프트 캐싱 보호

**WHY**: Anthropic Claude는 프롬프트 접두사가 동일하면 캐시 히트로 입력 비용 75%를 절감한다. 시스템 프롬프트가 턴마다 바뀌면 캐시가 무효화된다.

**HOW**:
- 시스템 프롬프트는 세션당 한 번 생성 후 `_cached_system_prompt`에 저장
- 플러그인 컨텍스트는 **시스템 프롬프트가 아닌 사용자 메시지에** 삽입 (캐시 접두사 보호)
- 외부 메모리 provider 결과도 사용자 메시지에 삽입
- `apply_anthropic_cache_control()`이 전략적 위치에 `cache_control` 브레이크포인트 삽입

### 원칙 4: 프로파일 격리

**WHY**: 한 사용자가 여러 사용 맥락(개인, 업무, 프로젝트별)을 가질 수 있다. 메모리와 설정이 격리되어야 한다.

**HOW**: `hermes_cli/profiles.py`의 프로파일 시스템이 `~/.hermes/` 하위에 프로파일별 디렉토리를 관리한다. 메모리 provider에 `agent_identity`로 프로파일 이름이 전달된다.

### 원칙 5: 플랫폼 추상화

**WHY**: 동일한 에이전트 로직을 CLI, Telegram, Discord, WhatsApp에서 재사용해야 한다. 각 플랫폼은 메시지 길이, 마크다운 지원, 인라인 이미지 등이 다르다.

**HOW**: `gateway/run.py`의 `GatewayRunner`가 플랫폼 어댑터를 관리한다. `AIAgent`는 `platform` 매개변수를 받아 `PLATFORM_HINTS`로 포매팅 힌트를 주입한다. `clarify_callback`, `stream_delta_callback` 같은 콜백이 플랫폼별 UI를 추상화한다.

### 원칙 6: 도구세트 필터링

**WHY**: 모든 도구를 항상 활성화하면 토큰 낭비(도구 스키마가 20K+ 토큰)이고, 사용자가 불필요한 도구를 실수로 호출할 수 있다.

**HOW**: `toolsets.py`가 도구를 논리적 그룹(web, terminal, browser 등)으로 묶고, 합성 도구세트(research = web + vision)를 정의한다. `--enabled-toolsets research`처럼 CLI에서 필터링하면, `get_tool_definitions()`이 해당 도구만 LLM에 전달한다.

---

## 5. 디렉토리 구조 해설

```
hermes-agent/
├── run_agent.py          # 진입점: AIAgent 클래스, 대화 루프, 도구 실행 오케스트레이션
├── model_tools.py        # 도구 발견(discovery) + 디스패치 오케스트레이션 계층
├── toolsets.py           # 도구 그룹 정의 (web, terminal, hermes-cli 등)
├── hermes_state.py       # SQLite 세션 저장소 (WAL, FTS5)
├── hermes_constants.py   # 전역 상수 (HERMES_HOME, OPENROUTER_BASE_URL)
├── hermes_logging.py     # 중앙 로깅 설정
├── hermes_time.py        # 시간대 유틸리티
├── trajectory_compressor.py  # RL 훈련용 궤적 압축 (후처리)
├── utils.py              # atomic_json_write, env_var_enabled 등
│
├── agent/                # AIAgent 내부 로직을 모듈화한 패키지
│   ├── prompt_builder.py     # 시스템 프롬프트 조립 (identity, 스킬, 컨텍스트 파일)
│   ├── context_compressor.py # 실시간 컨텍스트 압축 (대화 중)
│   ├── model_metadata.py     # 모델 메타데이터 캐시 (컨텍스트 길이, 가격)
│   ├── prompt_caching.py     # Anthropic 프롬프트 캐시 브레이크포인트
│   ├── usage_pricing.py      # 토큰 비용 추정
│   ├── anthropic_adapter.py  # Anthropic Messages API 어댑터
│   ├── auxiliary_client.py   # 보조 LLM 클라이언트 (요약, 비전 fallback)
│   ├── memory_manager.py     # 외부 메모리 provider 관리
│   ├── display.py            # KawaiiSpinner, 도구 미리보기 포맷
│   ├── trajectory.py         # 궤적 저장/변환 유틸리티
│   └── subdirectory_hints.py # 서브디렉토리 힌트 추적
│
├── tools/                # 자가 등록 도구 모음
│   ├── registry.py           # ToolRegistry 싱글턴 (핵심 인프라)
│   ├── web_tools.py          # web_search, web_extract
│   ├── terminal_tool.py      # 터미널 명령 실행 (VM 격리)
│   ├── file_tools.py         # read_file, write_file, patch, search_files
│   ├── browser_tool.py       # Playwright 기반 브라우저 자동화 (11개 도구)
│   ├── delegate_tool.py      # 서브에이전트 위임
│   ├── code_execution_tool.py # 샌드박스 코드 실행
│   ├── memory_tool.py        # 영속적 메모리 (MEMORY.md, USER.md)
│   ├── todo_tool.py          # 작업 계획 관리
│   ├── mcp_tool.py           # MCP 서버 연동 (외부 도구 발견)
│   └── ... (20+ 도구 파일)
│
├── gateway/              # 멀티 플랫폼 메시징 게이트웨이
│   ├── run.py                # GatewayRunner 진입점
│   └── adapters/             # Telegram, Discord, WhatsApp 어댑터
│
├── hermes_cli/           # CLI 인터페이스 (TUI, 설정, 프로파일)
├── skills/               # 재사용 가능한 스킬 마크다운 파일
├── plugins/              # 플러그인 시스템 (메모리 provider 등)
├── environments/         # RL 훈련 환경 정의
└── tests/                # 테스트 스위트
```

**왜 이렇게 나뉘어 있는가?**

- `agent/`와 `tools/`의 분리: 에이전트 **로직**(어떻게 생각하는가)과 에이전트 **능력**(무엇을 할 수 있는가)의 관심사 분리
- `gateway/`의 독립: 플랫폼 어댑터는 에이전트 로직에 의존하지만, 에이전트는 게이트웨이에 의존하지 않는다
- `hermes_cli/`의 분리: CLI 전용 코드(TUI, 프로파일, 인터랙티브 설정)가 에이전트 코어를 오염시키지 않도록
- `tools/registry.py`의 독립: 순환 import 방지를 위해 레지스트리는 어떤 도구 파일도 import하지 않는다

---

## 6. 의존성 계층

순환 의존을 피하기 위해 엄격한 계층 구조를 따른다. `tools/registry.py` 파일 상단 주석에 이 계층이 명시되어 있다:

```
Layer 0 (기반):  tools/registry.py
                 - 어떤 도구 파일도, model_tools도 import하지 않음
                 - 순수 데이터 구조 + 디스패치 로직
                      ^
Layer 1 (도구):  tools/*.py
                 - registry.py만 import (register() 호출)
                 - 서로 간에는 import하지 않음 (독립적)
                      ^
Layer 2 (오케스트레이션): model_tools.py
                 - registry.py import
                 - 모든 도구 모듈을 importlib로 동적 import (발견)
                 - toolsets.py import (도구세트 해석)
                      ^
Layer 3 (에이전트): run_agent.py, cli.py, batch_runner.py
                 - model_tools.py import
                 - agent/ 패키지 import
                      ^
Layer 4 (진입점): gateway/run.py, hermes_cli/
                 - run_agent.py import
                 - 플랫폼별 의존성
```

**순환 의존이 없는 이유**:

1. `registry.py`는 **아무것도 import하지 않는다** (logging, json, typing만 사용)
2. 각 도구 파일은 `registry.py`만 import한다. 다른 도구 파일을 import하지 않는다.
3. `model_tools.py`가 도구를 import할 때 `importlib.import_module()`을 사용하므로, 파일 상단의 import 문이 아닌 함수 실행 시점에 발생한다.
4. `registry.dispatch()`가 비동기 핸들러를 실행할 때 `model_tools._run_async`를 **지연 import**한다 (`from model_tools import _run_async`가 dispatch 메서드 내부에 있음).

이 단방향 의존 구조 덕분에:
- 새 도구를 추가해도 기존 코드를 수정할 필요 없음
- 도구 import 실패가 다른 도구에 영향 없음 (try/except으로 보호)
- 테스트에서 개별 계층을 독립적으로 mock 가능

---

## 핵심 정리

| 항목 | 요약 |
|------|------|
| **Hermes Agent란?** | LLM이 도구를 자율적으로 선택/실행하는 폐쇄형 에이전트 루프 + RL 자기개선 파이프라인 |
| **핵심 파일 6개** | `run_agent.py`, `model_tools.py`, `tools/registry.py`, `agent/prompt_builder.py`, `hermes_state.py`, `gateway/run.py` |
| **데이터 흐름** | 메시지 -> 프롬프트 조립 -> LLM 호출 -> 도구 실행 -> 결과 관찰 -> 반복 또는 종료 |
| **설계 핵심** | 자가등록 레지스트리, 캐싱 친화적 프롬프트, 플랫폼 추상화 |
| **의존성 방향** | registry -> tools -> model_tools -> run_agent -> gateway (단방향) |
| **확장 방법** | `tools/` 디렉토리에 파일 추가 + `registry.register()` 호출만으로 새 도구 등록 |

다음 강좌에서는 `run_agent.py`의 에이전트 루프를 코드 수준에서 심층 분석한다.
