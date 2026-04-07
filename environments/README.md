# Hermes-Agent Atropos 환경

이 디렉토리는 **hermes-agent**의 도구 호출 기능과 **Atropos** RL 훈련 프레임워크 간의 통합 레이어를 포함합니다. 에이전트 LLM을 다중 턴 도구 호출 루프를 통해 실행하고, 임의의 보상 함수로 출력을 평가하며, 결과를 Atropos에 전달하여 훈련 또는 평가하는 데 필요한 모든 것을 제공합니다.

## 아키텍처 개요

```
                        Atropos Framework
                    ┌───────────────────────┐
                    │       BaseEnv          │  (atroposlib)
                    │  - 서버 관리           │
                    │  - 워커 스케줄링       │
                    │  - Wandb 로깅          │
                    │  - CLI (serve/process/ │
                    │    evaluate)           │
                    └───────────┬───────────┘
                                │ 상속
                    ┌───────────┴───────────┐
                    │  HermesAgentBaseEnv    │  hermes_base_env.py
                    │  - 터미널 백엔드       │
                    │  - 도구 해석           │
                    │  - 에이전트 루프       │
                    │  - ToolContext          │
                    │  - 비동기 패치         │
                    └───────────┬───────────┘
                                │ 상속
              ┌─────────────────┼─────────────────┐
              │                 │                  │
     TerminalTestEnv     HermesSweEnv    TerminalBench2EvalEnv
     (스택 테스트)       (SWE 훈련)      (TB2 벤치마크 평가)
```

### 상속 체인

**BaseEnv** (`atroposlib` 제공)은 Atropos 기본 클래스입니다. 다음을 제공합니다:
- 서버 관리 (OpenAI 호환 API 서버, VLLM, SGLang)
- 병렬 롤아웃을 위한 워커 스케줄링
- 메트릭 및 롤아웃 로깅을 위한 Wandb 통합
- 세 가지 하위 명령을 갖는 CLI 인터페이스: `serve`, `process`, `evaluate`
- 평가 결과를 JSON + samples.jsonl로 저장하는 `evaluate_log()`

**HermesAgentBaseEnv** (`hermes_base_env.py`)는 BaseEnv를 hermes-agent 전용 기능으로 확장합니다:
- `os.environ["TERMINAL_ENV"]`를 설정하여 터미널 백엔드를 구성 (local, docker, modal, daytona, ssh, singularity)
- `_resolve_tools_for_group()`을 통해 hermes-agent 도구 세트를 해석 (`get_tool_definitions()`를 호출하여 `tools/registry.py`를 쿼리)
- 전체 에이전트 루프를 실행하고 보상을 계산하는 `collect_trajectory()` 구현
- 2단계 운영 지원 (1단계: OpenAI 서버, 2단계: VLLM ManagedServer)
- 임포트 시 비동기 안전 도구 운영을 위한 몽키 패치 적용

구체적인 환경은 `HermesAgentBaseEnv`를 상속받아 다음을 구현합니다:
- `setup()` -- 데이터셋 로드, 상태 초기화
- `get_next_item()` -- 롤아웃을 위한 다음 항목 반환
- `format_prompt()` -- 데이터셋 항목을 사용자 메시지로 변환
- `compute_reward()` -- ToolContext를 사용하여 롤아웃 점수 산정
- `evaluate()` -- 주기적 평가 로직

## 핵심 구성 요소

### 에이전트 루프 (`agent_loop.py`)

`HermesAgentLoop`는 재사용 가능한 다중 턴 에이전트 엔진입니다. hermes-agent의 `run_agent.py`와 동일한 패턴을 실행합니다:

1. `server.chat_completion()`을 통해 메시지 + 도구를 API로 전송
2. 응답에 `tool_calls`가 포함되면 `handle_function_call()`을 통해 각각 실행 (`tools/registry.py`의 `dispatch()`에 위임)
3. 도구 결과를 대화에 추가하고 1단계로 복귀
4. 응답에 tool_calls가 없으면 에이전트 완료

도구 호출은 스레드 풀(`run_in_executor`)에서 실행되므로, 내부적으로 `asyncio.run()`을 사용하는 백엔드(Modal, Docker)가 Atropos의 이벤트 루프 내에서 데드락을 일으키지 않습니다.

전체 대화 기록, 턴 수, 턴별 추론 내용, 도구 오류, 그리고 선택적 ManagedServer 상태(2단계용)를 포함하는 `AgentResult`를 반환합니다.

### 도구 컨텍스트 (`tool_context.py`)

`ToolContext`는 롤아웃별 핸들로, 보상/검증 함수가 롤아웃의 `task_id`로 범위가 지정된 **모든** hermes-agent 도구에 직접 접근할 수 있게 합니다. 동일한 `task_id`는 터미널/브라우저 세션이 모델이 롤아웃 중에 사용한 것과 동일한 세션임을 의미합니다 -- 모든 상태(파일, 프로세스, 브라우저 탭)가 보존됩니다.

```python
async def compute_reward(self, item, result, ctx: ToolContext):
    # 모델의 터미널 샌드박스에서 테스트 실행
    test = ctx.terminal("pytest -v")
    if test["exit_code"] == 0:
        return 1.0

    # 파일이 생성되었는지 확인
    content = ctx.read_file("/workspace/solution.py")
    if content.get("content"):
        return 0.5

    # 검증을 위해 로컬로 파일 다운로드 (바이너리 안전)
    ctx.download_file("/remote/output.bin", "/local/output.bin")

    return 0.0
```

사용 가능한 메서드:
- **터미널**: `terminal(command, timeout)` -- 셸 명령 실행
- **파일**: `read_file(path)`, `write_file(path, content)`, `search(query, path)`
- **전송**: `upload_file()`, `upload_dir()`, `download_file()`, `download_dir()` -- 호스트와 샌드박스 간 바이너리 안전 파일 전송
- **웹**: `web_search(query)`, `web_extract(urls)`
- **브라우저**: `browser_navigate(url)`, `browser_snapshot()`
- **범용**: `call_tool(name, args)` -- 이름으로 모든 hermes-agent 도구 호출
- **정리**: `cleanup()` -- 모든 리소스 해제 (`compute_reward` 이후 자동 호출)

### 패치 (`patches.py`)

**문제**: 일부 hermes-agent 도구가 내부적으로 `asyncio.run()`을 사용합니다(예: Modal 백엔드). 이는 Atropos의 이벤트 루프 내에서 호출될 때 충돌합니다. `asyncio.run()`은 중첩할 수 없기 때문입니다.

**해결책**: `ModalEnvironment`는 자체 이벤트 루프를 가진 전용 `_AsyncWorker` 백그라운드 스레드를 사용합니다. 호출 코드는 동기 인터페이스를 보지만, 내부적으로 모든 비동기 Modal SDK 호출은 워커 스레드에서 수행되어 Atropos의 루프와 충돌하지 않습니다. 이는 `tools/environments/modal.py`에 직접 내장되어 있으며 -- 몽키 패칭이 필요하지 않습니다.

`patches.py`는 현재 아무 작업도 수행하지 않습니다 (임포트와의 하위 호환성을 위해 유지).

### 도구 호출 파서 (`tool_call_parsers/`)

원시 모델 출력 텍스트에서 구조화된 `tool_calls`를 추출하는 클라이언트 측 파서입니다. ManagedServer의 `/generate` 엔드포인트가 도구 호출 파싱 없이 원시 텍스트를 반환하는 **2단계** (VLLM 서버 타입)에서 사용됩니다.

각 파서는 해당 VLLM 파서의 `extract_tool_calls()` 로직을 독립적으로 재구현한 것입니다. VLLM 의존성 없음 -- 표준 라이브러리(`re`, `json`, `uuid`)와 `openai` 타입만 사용합니다.

사용 가능한 파서:
- `hermes` -- Hermes/ChatML `<tool_call>` XML 형식
- `mistral` -- Mistral `[TOOL_CALLS]` 형식
- `llama3_json` -- Llama 3 JSON 도구 호출
- `qwen` -- Qwen 도구 호출 형식
- `qwen3_coder` -- Qwen3 Coder 형식
- `deepseek_v3` -- DeepSeek V3 형식
- `deepseek_v3_1` -- DeepSeek V3.1 형식
- `kimi_k2` -- Kimi K2 형식
- `longcat` -- Longcat 형식
- `glm45` / `glm47` -- GLM 모델 형식

사용법:
```python
from environments.tool_call_parsers import get_parser

parser = get_parser("hermes")
content, tool_calls = parser.parse(raw_model_output)
```

1단계 (OpenAI 서버 타입)에서는 서버가 도구 호출 파싱을 기본적으로 처리하므로 이 파서들이 필요하지 않습니다.

## 2단계 운영

### 1단계: OpenAI 서버 (평가 / SFT 데이터 생성)

`tools=` 매개변수와 함께 `server.chat_completion()`을 사용합니다. 서버(VLLM, SGLang, OpenRouter, OpenAI)가 도구 호출 파싱을 기본적으로 처리합니다. 구조화된 `tool_calls`가 포함된 `ChatCompletion` 객체를 반환합니다.

- 적합한 용도: 평가, SFT 데이터 생성, 테스트
- 실행 방법: `serve` (`run-api` 포함), `process`, 또는 `evaluate` 하위 명령
- Atropos 파이프라인용 플레이스홀더 토큰이 생성됩니다

### 2단계: VLLM ManagedServer (전체 RL 훈련)

ManagedServer를 사용하여 `/generate`를 통해 정확한 토큰 ID + logprobs를 획득합니다. 클라이언트 측 도구 호출 파서(`tool_call_parsers/`)가 원시 출력에서 구조화된 `tool_calls`를 재구성합니다.

- 적합한 용도: GRPO/PPO를 사용한 전체 RL 훈련
- 실행 방법: `serve` 하위 명령
- 실제 토큰, 마스크, logprobs가 파이프라인을 통해 전달됩니다

## 디렉토리 구조

```
environments/
├── README.md                     # 이 파일
├── __init__.py                   # 패키지 내보내기
├── hermes_base_env.py            # 추상 기본 클래스 (HermesAgentBaseEnv)
├── agent_loop.py                 # 다중 턴 에이전트 엔진 (HermesAgentLoop)
├── tool_context.py               # 보상 함수용 롤아웃별 도구 접근
├── patches.py                    # Modal 백엔드용 비동기 안전 패치
│
├── tool_call_parsers/            # 2단계 클라이언트 측 파서
│   ├── __init__.py               # 레지스트리 + 기본 클래스
│   ├── hermes_parser.py
│   ├── mistral_parser.py
│   ├── llama_parser.py
│   ├── qwen_parser.py
│   ├── qwen3_coder_parser.py
│   ├── deepseek_v3_parser.py
│   ├── deepseek_v3_1_parser.py
│   ├── kimi_k2_parser.py
│   ├── longcat_parser.py
│   ├── glm45_parser.py
│   └── glm47_parser.py
│
├── terminal_test_env/            # 스택 검증 환경
│   └── terminal_test_env.py
│
├── hermes_swe_env/               # SWE-bench 스타일 훈련 환경
│   └── hermes_swe_env.py
│
└── benchmarks/                   # 평가 벤치마크
    ├── terminalbench_2/          # 89개 터미널 작업, Modal 샌드박스
    │   └── terminalbench2_env.py
    ├── tblite/                   # 100개 교정된 작업 (빠른 TB2 프록시)
    │   └── tblite_env.py
    └── yc_bench/                 # 장기 전략 벤치마크
        └── yc_bench_env.py
```

## 구체적 환경

### TerminalTestEnv (`terminal_test_env/`)

인라인 작업이 포함된 자체 완결형 환경(외부 데이터셋 불필요)으로, 전체 스택을 엔드투엔드로 검증합니다. 각 작업은 모델에게 알려진 경로에 파일을 생성하도록 요청하며, 검증기가 내용이 일치하는지 확인합니다.

```bash
# Serve 모드 (run-api 필요)
run-api
python environments/terminal_test_env/terminal_test_env.py serve

# Process 모드 (run-api 불필요, JSONL로 저장)
python environments/terminal_test_env/terminal_test_env.py process \
    --env.data_path_to_save_groups terminal_test_output.jsonl
```

### HermesSweEnv (`hermes_swe_env/`)

SWE-bench 스타일 훈련 환경입니다. 모델이 코딩 작업을 받고, 터미널 + 파일 + 웹 도구를 사용하여 해결하며, 보상 함수가 동일한 Modal 샌드박스에서 테스트를 실행합니다.

```bash
python environments/hermes_swe_env/hermes_swe_env.py serve \
    --openai.model_name YourModel \
    --env.dataset_name bigcode/humanevalpack \
    --env.terminal_backend modal
```

### TerminalBench2EvalEnv (`benchmarks/terminalbench_2/`)

Terminal-Bench 2.0 벤치마크(89개 작업)를 위한 **평가 전용** 환경입니다. 각 작업은 사전 빌드된 Docker Hub 이미지, 자연어 지시문, 테스트 스위트를 제공받습니다. 에이전트는 터미널 + 파일 도구를 사용하여 작업을 해결한 후, 테스트 스위트가 정확성을 검증합니다.

표준 Atropos 평가 패턴(GPQA, MMLU 등)을 따릅니다:
- `evaluate` 하위 명령으로 실행 (`run-api` 불필요)
- `setup()`이 데이터셋을 로드하고, `evaluate()`가 모든 작업을 실행
- `rollout_and_score_eval()`이 작업별 에이전트 루프 + 테스트 검증을 처리
- 안정적인 보상 확인을 위해 검증기 출력을 로컬로 다운로드 (Harbor 패턴)

```bash
# 전체 벤치마크 실행
python environments/benchmarks/terminalbench_2/terminalbench2_env.py evaluate \
    --openai.model_name anthropic/claude-opus-4.6

# 작업 부분 집합 실행
python environments/benchmarks/terminalbench_2/terminalbench2_env.py evaluate \
    --openai.model_name anthropic/claude-opus-4.6 \
    --env.task_filter fix-git,git-multibranch

# 특정 작업 건너뛰기
python environments/benchmarks/terminalbench_2/terminalbench2_env.py evaluate \
    --openai.model_name anthropic/claude-opus-4.6 \
    --env.skip_tasks heavy-task,slow-task
```

## 새 환경 만들기

### 훈련 환경

1. `environments/` 아래에 새 디렉토리 생성
2. `HermesAgentBaseEnv`를 상속받는 환경 파일 생성
3. 네 가지 추상 메서드 + `evaluate()` 구현

```python
from environments.hermes_base_env import HermesAgentBaseEnv, HermesAgentEnvConfig

class MyEnvConfig(HermesAgentEnvConfig):
    pass  # 필요에 따라 커스텀 필드 추가

class MyEnv(HermesAgentBaseEnv):
    name = "my-env"
    env_config_cls = MyEnvConfig

    @classmethod
    def config_init(cls):
        env_config = MyEnvConfig(
            enabled_toolsets=["terminal", "file"],
            terminal_backend="modal",
            # ... 기타 설정
        )
        server_configs = [APIServerConfig(...)]
        return env_config, server_configs

    async def setup(self):
        self.dataset = load_dataset(...)
        self.iter = 0

    async def get_next_item(self):
        item = self.dataset[self.iter % len(self.dataset)]
        self.iter += 1
        return item

    def format_prompt(self, item):
        return item["instruction"]

    async def compute_reward(self, item, result, ctx):
        # ctx를 통해 롤아웃의 샌드박스에 대한 전체 도구 접근 가능
        test = ctx.terminal("pytest -v")
        return 1.0 if test["exit_code"] == 0 else 0.0

    async def evaluate(self, *args, **kwargs):
        # 주기적 평가 로직
        ...

if __name__ == "__main__":
    MyEnv.cli()
```

### 평가 전용 환경 (벤치마크)

평가 벤치마크의 경우 `terminalbench2_env.py`의 패턴을 따르세요:
1. `environments/benchmarks/your-benchmark/` 아래에 생성
2. `HermesAgentBaseEnv`를 상속
3. 평가 전용 설정: `eval_handling=STOP_TRAIN`, `steps_per_eval=1`, `total_steps=1`
4. 훈련 메서드 스텁 처리 (`collect_trajectories`, `score`)
5. `rollout_and_score_eval()`과 `evaluate()` 구현
6. `evaluate` 하위 명령으로 실행

## 주요 설정 필드

| 필드 | 설명 | 기본값 |
|------|------|--------|
| `enabled_toolsets` | 활성화할 hermes 도구 세트 | `None` (전체) |
| `disabled_toolsets` | 비활성화할 도구 세트 | `None` |
| `distribution` | 확률적 도구 세트 분포 이름 | `None` |
| `max_agent_turns` | 롤아웃당 최대 LLM 호출 수 | `30` |
| `agent_temperature` | 샘플링 온도 | `1.0` |
| `terminal_backend` | `local`, `docker`, `modal`, `daytona`, `ssh`, `singularity` | `local` |
| `system_prompt` | 에이전트용 시스템 메시지 | `None` |
| `tool_call_parser` | 2단계용 파서 이름 | `hermes` |
| `eval_handling` | `STOP_TRAIN`, `LIMIT_TRAIN`, `NONE` | `STOP_TRAIN` |
