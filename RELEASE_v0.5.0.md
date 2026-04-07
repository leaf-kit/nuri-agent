# Hermes Agent v0.5.0 (v2026.3.28)

**출시일:** 2026년 3월 28일

> 안정화 릴리스 — Hugging Face 프로바이더, /model 명령어 전면 개편, Telegram 비공개 채팅 토픽, 네이티브 Modal SDK, 플러그인 라이프사이클 훅, GPT 모델의 도구 사용 강제, Nix flake, 50개 이상의 보안 및 안정성 수정, 그리고 포괄적인 공급망 감사.

---

## ✨ 주요 변경사항

- **Nous Portal이 이제 400개 이상의 모델을 지원합니다** — Nous Research 추론 포털이 대폭 확장되어 Hermes Agent 사용자가 단일 프로바이더 엔드포인트를 통해 400개 이상의 모델에 접근할 수 있습니다

- **Hugging Face를 1급 추론 프로바이더로 지원** — 선별된 에이전트 모델 선택기(OpenRouter 대응 모델 매핑), 실시간 `/models` 엔드포인트 탐색, 설정 마법사 흐름을 포함한 HF Inference API 전체 통합 ([#3419](https://github.com/NousResearch/hermes-agent/pull/3419), [#3440](https://github.com/NousResearch/hermes-agent/pull/3440))

- **Telegram 비공개 채팅 토픽** — 토픽별 기능 스킬 바인딩이 가능한 프로젝트 기반 대화로, 단일 Telegram 채팅 내에서 격리된 워크플로우를 지원합니다 ([#3163](https://github.com/NousResearch/hermes-agent/pull/3163))

- **네이티브 Modal SDK 백엔드** — swe-rex 의존성을 네이티브 Modal SDK(`Sandbox.create.aio` + `exec.aio`)로 교체하여 터널을 제거하고 Modal 터미널 백엔드를 단순화했습니다 ([#3538](https://github.com/NousResearch/hermes-agent/pull/3538))

- **플러그인 라이프사이클 훅 활성화** — `pre_llm_call`, `post_llm_call`, `on_session_start`, `on_session_end` 훅이 이제 에이전트 루프와 CLI/게이트웨이에서 실행되어 플러그인 훅 시스템이 완성되었습니다 ([#3542](https://github.com/NousResearch/hermes-agent/pull/3542))

- **OpenAI 모델 안정성 개선** — GPT 모델이 도구 호출 대신 의도한 동작을 설명하는 것을 방지하는 `GPT_TOOL_USE_GUIDANCE` 추가, 그리고 모델이 여러 턴에 걸쳐 도구 사용을 회피하게 만드는 오래된 예산 경고를 대화 기록에서 자동 제거 ([#3528](https://github.com/NousResearch/hermes-agent/pull/3528))

- **Nix flake** — 완전한 uv2nix 빌드, 영구 컨테이너 모드를 갖춘 NixOS 모듈, Python 소스에서 자동 생성된 설정 키, 에이전트 친화적 접미사 PATH ([#20](https://github.com/NousResearch/hermes-agent/pull/20), [#3274](https://github.com/NousResearch/hermes-agent/pull/3274), [#3061](https://github.com/NousResearch/hermes-agent/pull/3061)) by @alt-glitch

- **공급망 보안 강화** — 손상된 `litellm` 의존성 제거, 모든 의존성 버전 범위 고정, 해시가 포함된 `uv.lock` 재생성, 공급망 공격 패턴을 스캔하는 PR용 CI 워크플로우 추가, CVE 수정을 위한 의존성 업데이트 ([#2796](https://github.com/NousResearch/hermes-agent/pull/2796), [#2810](https://github.com/NousResearch/hermes-agent/pull/2810), [#2812](https://github.com/NousResearch/hermes-agent/pull/2812), [#2816](https://github.com/NousResearch/hermes-agent/pull/2816), [#3073](https://github.com/NousResearch/hermes-agent/pull/3073))

- **Anthropic 출력 제한 수정** — 하드코딩된 16K `max_tokens`를 모델별 네이티브 출력 제한(Opus 4.6은 128K, Sonnet 4.6은 64K)으로 교체하여 직접 Anthropic API에서 발생하던 "Response truncated" 및 사고 예산 고갈 문제를 수정했습니다 ([#3426](https://github.com/NousResearch/hermes-agent/pull/3426), [#3444](https://github.com/NousResearch/hermes-agent/pull/3444))

---

## 🏗️ 코어 에이전트 및 아키텍처

### 새로운 프로바이더: Hugging Face
- 인증, 설정 마법사, 모델 선택기를 갖춘 1급 Hugging Face Inference API 통합 ([#3419](https://github.com/NousResearch/hermes-agent/pull/3419))
- OpenRouter 에이전트 기본값을 HF 동등 모델에 매핑하는 선별된 모델 목록 — 8개 이상의 선별된 모델이 있는 프로바이더는 속도를 위해 실시간 `/models` 탐색을 건너뜁니다 ([#3440](https://github.com/NousResearch/hermes-agent/pull/3440))
- Z.AI 프로바이더 모델 목록에 glm-5-turbo 추가 ([#3095](https://github.com/NousResearch/hermes-agent/pull/3095))

### 프로바이더 및 모델 개선
- `/model` 명령어 전면 개편 — CLI와 게이트웨이용 공유 `switch_model()` 파이프라인 추출, 사용자 정의 엔드포인트 지원, 프로바이더 인식 라우팅 ([#2795](https://github.com/NousResearch/hermes-agent/pull/2795), [#2799](https://github.com/NousResearch/hermes-agent/pull/2799))
- CLI와 게이트웨이에서 `/model` 슬래시 명령어를 제거하고 `hermes model` 하위 명령어로 대체 ([#3080](https://github.com/NousResearch/hermes-agent/pull/3080))
- `custom` 프로바이더를 자동으로 `openrouter`로 재매핑하지 않고 보존 ([#2792](https://github.com/NousResearch/hermes-agent/pull/2792))
- config.yaml의 루트 레벨 `provider` 및 `base_url`을 모델 설정에 반영 ([#3112](https://github.com/NousResearch/hermes-agent/pull/3112))
- Nous Portal 모델 슬러그를 OpenRouter 네이밍에 맞춤 ([#3253](https://github.com/NousResearch/hermes-agent/pull/3253))
- Alibaba 프로바이더 기본 엔드포인트 및 모델 목록 수정 ([#3484](https://github.com/NousResearch/hermes-agent/pull/3484))
- MiniMax 사용자가 `/v1` → `/anthropic` 자동 변환을 재정의할 수 있도록 허용 ([#3553](https://github.com/NousResearch/hermes-agent/pull/3553))
- OAuth 토큰 새로고침을 폴백과 함께 `platform.claude.com`으로 마이그레이션 ([#3246](https://github.com/NousResearch/hermes-agent/pull/3246))

### 에이전트 루프 및 대화
- **OpenAI 모델 안정성 개선** — `GPT_TOOL_USE_GUIDANCE`가 GPT 모델이 도구 호출 대신 동작을 설명하는 것을 방지 + 기록에서 자동 예산 경고 제거 ([#3528](https://github.com/NousResearch/hermes-agent/pull/3528))
- **라이프사이클 이벤트 표시** — 모든 재시도, 폴백, 압축 이벤트가 이제 포맷된 메시지로 사용자에게 표시됩니다 ([#3153](https://github.com/NousResearch/hermes-agent/pull/3153))
- **Anthropic 출력 제한** — 하드코딩된 16K `max_tokens` 대신 모델별 네이티브 출력 제한 ([#3426](https://github.com/NousResearch/hermes-agent/pull/3426))
- **사고 예산 고갈 감지** — 모델이 모든 출력 토큰을 추론에 사용했을 때 무의미한 계속 재시도를 건너뜁니다 ([#3444](https://github.com/NousResearch/hermes-agent/pull/3444))
- 멈춘 서브에이전트를 방지하기 위해 API 호출에 항상 스트리밍 선호 ([#3120](https://github.com/NousResearch/hermes-agent/pull/3120))
- 스트림 실패 후 안전한 비스트리밍 폴백 복원 ([#3020](https://github.com/NousResearch/hermes-agent/pull/3020))
- 서브에이전트에 독립적인 반복 예산 부여 ([#3004](https://github.com/NousResearch/hermes-agent/pull/3004))
- 서브에이전트 인증을 위해 `_try_activate_fallback`에서 `api_key` 업데이트 ([#3103](https://github.com/NousResearch/hermes-agent/pull/3103))
- 스레드 충돌 대신 최대 재시도 시 정상적으로 반환 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- 재시도 제한에 압축 재시작 횟수 포함 ([#3070](https://github.com/NousResearch/hermes-agent/pull/3070))
- 사전 검사 추정에 도구 토큰 포함, 컨텍스트 탐색 지속성 보호 ([#3164](https://github.com/NousResearch/hermes-agent/pull/3164))
- 폴백 활성화 후 컨텍스트 압축기 제한 업데이트 ([#3305](https://github.com/NousResearch/hermes-agent/pull/3305))
- Anthropic API 400 에러를 방지하기 위해 빈 사용자 메시지 검증 ([#3322](https://github.com/NousResearch/hermes-agent/pull/3322))
- GLM 추론 전용 및 최대 길이 처리 ([#3010](https://github.com/NousResearch/hermes-agent/pull/3010))
- 느린 사고 모델을 위해 API 타임아웃 기본값을 900초에서 1800초로 증가 ([#3431](https://github.com/NousResearch/hermes-agent/pull/3431))
- Claude/OpenRouter에 `max_tokens` 전송 + SSE 연결 오류 재시도 ([#3497](https://github.com/NousResearch/hermes-agent/pull/3497))
- 게이트웨이 모드에서 AsyncOpenAI/httpx 크로스 루프 데드락 방지 ([#2701](https://github.com/NousResearch/hermes-agent/pull/2701)) by @ctlst

### 스트리밍 및 추론
- **게이트웨이 세션 턴 간 추론 지속** — 새로운 스키마 v6 컬럼(`reasoning`, `reasoning_details`, `codex_reasoning_items`) ([#2974](https://github.com/NousResearch/hermes-agent/pull/2974))
- 오래된 SSE 연결 감지 및 종료 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- 가짜 `RemoteProtocolError`를 유발하는 오래된 스트림 감지기 경쟁 조건 수정 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- 스트리밍 중 `<think>` 추출 추론에 대한 중복 콜백 건너뛰기 ([#3116](https://github.com/NousResearch/hermes-agent/pull/3116))
- `rewrite_transcript`에서 추론 필드 보존 ([#3311](https://github.com/NousResearch/hermes-agent/pull/3311))
- 스트리밍된 도구 호출에서 Gemini 사고 서명 보존 ([#2997](https://github.com/NousResearch/hermes-agent/pull/2997))
- 추론 업데이트 중 첫 번째 델타가 반드시 발생하도록 보장 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))

### 세션 및 메모리
- **세션 검색 최근 세션 모드** — 쿼리를 생략하면 제목, 미리보기, 타임스탬프와 함께 최근 세션을 탐색합니다 ([#2533](https://github.com/NousResearch/hermes-agent/pull/2533))
- **세션 설정 표시** — `/new`, `/reset`, 자동 리셋 시 설정 표시 ([#3321](https://github.com/NousResearch/hermes-agent/pull/3321))
- **서드파티 세션 격리** — 출처별 세션 격리를 위한 `--source` 플래그 ([#3255](https://github.com/NousResearch/hermes-agent/pull/3255))
- `/resume` CLI 핸들러, 세션 로그 잘림 보호, `reopen_session` API 추가 ([#3315](https://github.com/NousResearch/hermes-agent/pull/3315))
- `/clear` 및 `/new`에서 압축기 요약 및 턴 카운터 초기화 ([#3102](https://github.com/NousResearch/hermes-agent/pull/3102))
- 세션 데이터 손실을 야기하는 조용한 SessionDB 실패 표시 ([#2999](https://github.com/NousResearch/hermes-agent/pull/2999))
- 요약 실패 시 세션 검색 폴백 미리보기 ([#3478](https://github.com/NousResearch/hermes-agent/pull/3478))
- 플러시 에이전트에 의한 오래된 메모리 덮어쓰기 방지 ([#2687](https://github.com/NousResearch/hermes-agent/pull/2687))

### 컨텍스트 압축
- 비활성 `summary_target_tokens`를 비율 기반 스케일링으로 교체 ([#2554](https://github.com/NousResearch/hermes-agent/pull/2554))
- `DEFAULT_CONFIG`에 `compression.target_ratio`, `protect_last_n`, `threshold` 노출 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- 합리적인 기본값 복원 및 요약을 12K 토큰으로 제한 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- `/compress` 및 위생 압축 시 트랜스크립트 보존 ([#3556](https://github.com/NousResearch/hermes-agent/pull/3556))
- 압축 후 컨텍스트 압력 경고 및 토큰 추정치 업데이트 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))

### 아키텍처 및 의존성
- **mini-swe-agent 의존성 제거** — Docker 및 Modal 백엔드를 직접 인라인 ([#2804](https://github.com/NousResearch/hermes-agent/pull/2804))
- **swe-rex를 네이티브 Modal SDK로 교체** — Modal 백엔드용 ([#3538](https://github.com/NousResearch/hermes-agent/pull/3538))
- **플러그인 라이프사이클 훅** — `pre_llm_call`, `post_llm_call`, `on_session_start`, `on_session_end`가 이제 에이전트 루프에서 실행됩니다 ([#3542](https://github.com/NousResearch/hermes-agent/pull/3542))
- `hermes tools` 및 독립 프로세스에서 플러그인 도구세트가 보이지 않는 문제 수정 ([#3457](https://github.com/NousResearch/hermes-agent/pull/3457))
- `get_hermes_home()` 및 `parse_reasoning_effort()` 통합 ([#3062](https://github.com/NousResearch/hermes-agent/pull/3062))
- 사용하지 않는 Hermes 네이티브 PKCE OAuth 흐름 제거 ([#3107](https://github.com/NousResearch/hermes-agent/pull/3107))
- 55개 파일에서 ~100개의 사용하지 않는 import 제거 ([#3016](https://github.com/NousResearch/hermes-agent/pull/3016))
- 154개의 f-string 수정, getattr/URL 패턴 단순화, 불필요한 코드 제거 ([#3119](https://github.com/NousResearch/hermes-agent/pull/3119))

---

## 📱 메시징 플랫폼 (게이트웨이)

### Telegram
- **비공개 채팅 토픽** — 토픽별 기능 스킬 바인딩이 가능한 프로젝트 기반 대화로, 단일 Telegram 채팅 내에서 격리된 워크플로우 지원 ([#3163](https://github.com/NousResearch/hermes-agent/pull/3163))
- **DNS-over-HTTPS를 통한 폴백 IP 자동 검색** — `api.telegram.org`에 접근할 수 없을 때 ([#3376](https://github.com/NousResearch/hermes-agent/pull/3376))
- **설정 가능한 답장 스레딩 모드** ([#2907](https://github.com/NousResearch/hermes-agent/pull/2907))
- "Message thread not found" BadRequest 시 `thread_id` 없이 폴백 ([#3390](https://github.com/NousResearch/hermes-agent/pull/3390))
- 502 이후 `start_polling` 실패 시 자체 재스케줄 재연결 ([#3268](https://github.com/NousResearch/hermes-agent/pull/3268))

### Discord
- 에이전트 턴 완료 후 유령 타이핑 표시기 중지 ([#3003](https://github.com/NousResearch/hermes-agent/pull/3003))

### Slack
- 올바른 Slack 스레드로 도구 호출 진행 메시지 전송 ([#3063](https://github.com/NousResearch/hermes-agent/pull/3063))
- 진행 스레드 폴백을 Slack으로만 한정 ([#3488](https://github.com/NousResearch/hermes-agent/pull/3488))

### WhatsApp
- 메시지에서 문서, 오디오, 비디오 미디어 다운로드 ([#2978](https://github.com/NousResearch/hermes-agent/pull/2978))

### Matrix
- `PLATFORMS` 딕셔너리에 누락된 Matrix 항목 추가 ([#3473](https://github.com/NousResearch/hermes-agent/pull/3473))
- E2EE 액세스 토큰 처리 강화 ([#3562](https://github.com/NousResearch/hermes-agent/pull/3562))
- 동기화 루프에서 `SyncError`에 대한 백오프 추가 ([#3280](https://github.com/NousResearch/hermes-agent/pull/3280))

### Signal
- SSE 키프얼라이브 코멘트를 연결 활동으로 추적 ([#3316](https://github.com/NousResearch/hermes-agent/pull/3316))

### Email
- EmailAdapter에서 `_seen_uids`의 무한 증가 방지 ([#3490](https://github.com/NousResearch/hermes-agent/pull/3490))

### 게이트웨이 코어
- **설정 기반 `/verbose` 명령어** — 메시징 플랫폼에서 도구 출력 상세도 토글 ([#3262](https://github.com/NousResearch/hermes-agent/pull/3262))
- **백그라운드 검토 알림** — 사용자 채팅으로 전달 ([#3293](https://github.com/NousResearch/hermes-agent/pull/3293))
- **일시적 전송 실패 재시도** 및 소진 시 사용자 알림 ([#3288](https://github.com/NousResearch/hermes-agent/pull/3288))
- 멈춘 에이전트 복구 — `/stop`이 세션 잠금을 강제 종료 ([#3104](https://github.com/NousResearch/hermes-agent/pull/3104))
- 스레드 안전 `SessionStore` — `threading.Lock`으로 `_entries` 보호 ([#3052](https://github.com/NousResearch/hermes-agent/pull/3052))
- 캐시된 에이전트와의 게이트웨이 토큰 이중 계산 수정 — 증분 대신 절대 세트 사용 ([#3306](https://github.com/NousResearch/hermes-agent/pull/3306), [#3317](https://github.com/NousResearch/hermes-agent/pull/3317))
- 에이전트 캐시 서명에 전체 인증 토큰 지문 반영 ([#3247](https://github.com/NousResearch/hermes-agent/pull/3247))
- 백그라운드 에이전트 터미널 출력 억제 ([#3297](https://github.com/NousResearch/hermes-agent/pull/3297))
- 시작 허용 목록 검사에 플랫폼별 `ALLOW_ALL` 및 `SIGNAL_GROUP` 포함 ([#3313](https://github.com/NousResearch/hermes-agent/pull/3313))
- systemd 유닛 PATH에 사용자 로컬 bin 경로 포함 ([#3527](https://github.com/NousResearch/hermes-agent/pull/3527))
- `GatewayRunner`에서 백그라운드 태스크 참조 추적 ([#3254](https://github.com/NousResearch/hermes-agent/pull/3254))
- HA, Email, Mattermost, SMS 어댑터에 요청 타임아웃 추가 ([#3258](https://github.com/NousResearch/hermes-agent/pull/3258))
- Mattermost, Slack, 기본 캐시에 미디어 다운로드 재시도 추가 ([#3323](https://github.com/NousResearch/hermes-agent/pull/3323))
- `venv/` 하드코딩 대신 가상환경 경로 감지 ([#2797](https://github.com/NousResearch/hermes-agent/pull/2797))
- 컨텍스트 파일 검색에 프로세스 cwd 대신 `TERMINAL_CWD` 사용 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- 게이트웨이 세션에 hermes 저장소 AGENTS.md 로딩 중지 (~10k 토큰 낭비) ([#2891](https://github.com/NousResearch/hermes-agent/pull/2891))

---

## 🖥️ CLI 및 사용자 경험

### 대화형 CLI
- **설정 가능한 바쁨 입력 모드** + `/queue` 항상 작동 수정 ([#3298](https://github.com/NousResearch/hermes-agent/pull/3298))
- **멀티라인 붙여넣기 시 사용자 입력 보존** ([#3065](https://github.com/NousResearch/hermes-agent/pull/3065))
- **도구 생성 콜백** — 도구 인수 생성 중 "preparing terminal..." 스트리밍 업데이트 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- 단순 "preparing" 대신 실질적인 도구에 대한 도구 진행 상태 표시 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- 추론 미리보기 청크 버퍼링 및 중복 표시 수정 ([#3013](https://github.com/NousResearch/hermes-agent/pull/3013))
- 도구 호출 루프 중 추론 상자가 3번 렌더링되는 것 방지 ([#3405](https://github.com/NousResearch/hermes-agent/pull/3405))
- "Event loop is closed" / "Press ENTER to continue" 유휴 시 발생 제거 — `neuter_async_httpx_del()`, 커스텀 예외 핸들러, 오래된 클라이언트 정리의 3단계 수정 ([#3398](https://github.com/NousResearch/hermes-agent/pull/3398))
- 토큰 수에서 후행 0이 있을 때 상태 바가 260K 대신 26K를 표시하는 문제 수정 ([#3024](https://github.com/NousResearch/hermes-agent/pull/3024))
- 긴 세션 중 상태 바 중복 및 성능 저하 수정 ([#3291](https://github.com/NousResearch/hermes-agent/pull/3291))
- 상태 바 겹침 방지를 위해 백그라운드 작업 출력 전 TUI 새로고침 ([#3048](https://github.com/NousResearch/hermes-agent/pull/3048))
- `patch_stdout` 하에서 KawaiiSpinner 애니메이션 억제 ([#2994](https://github.com/NousResearch/hermes-agent/pull/2994))
- TUI가 도구 진행을 처리할 때 KawaiiSpinner 건너뛰기 ([#2973](https://github.com/NousResearch/hermes-agent/pull/2973))
- `_is_tty` 속성을 통해 닫힌 스트림에 대한 `isatty()` 보호 ([#3056](https://github.com/NousResearch/hermes-agent/pull/3056))
- 도구 생성 중 스트리밍 상자의 단일 닫힘 보장 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- 표시에서 컨텍스트 압력 퍼센티지를 100%로 제한 ([#3480](https://github.com/NousResearch/hermes-agent/pull/3480))
- CLI 표시에서 HTML 에러 메시지 정리 ([#3069](https://github.com/NousResearch/hermes-agent/pull/3069))
- API 에러 출력에 HTTP 상태 코드 및 400 본문 표시 ([#3096](https://github.com/NousResearch/hermes-agent/pull/3096))
- HTML 에러 페이지에서 유용한 정보 추출, 최대 재시도 시 디버그 덤프 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- `base_url`이 None일 때 시작 시 TypeError 방지 ([#3068](https://github.com/NousResearch/hermes-agent/pull/3068))
- 비TTY 환경에서 업데이트 충돌 방지 ([#3094](https://github.com/NousResearch/hermes-agent/pull/3094))
- 세션 삭제/정리 확인 프롬프트에서 EOFError 처리 ([#3101](https://github.com/NousResearch/hermes-agent/pull/3101))
- 종료 시 `flush_memories` 중 KeyboardInterrupt 잡기 및 종료 정리 핸들러에서 처리 ([#3025](https://github.com/NousResearch/hermes-agent/pull/3025), [#3257](https://github.com/NousResearch/hermes-agent/pull/3257))
- YAML 설정의 None 값에 대한 `.strip()` 보호 ([#3552](https://github.com/NousResearch/hermes-agent/pull/3552))
- AttributeError 방지를 위한 YAML null 값에 대한 `config.get()` 보호 ([#3377](https://github.com/NousResearch/hermes-agent/pull/3377))
- GC 중간 실행 방지를 위해 asyncio 태스크 참조 저장 ([#3267](https://github.com/NousResearch/hermes-agent/pull/3267))

### 설정 및 구성
- 반환 사용자 메뉴 디스패치에 위치 인덱스 대신 명시적 키 매핑 사용 ([#3083](https://github.com/NousResearch/hermes-agent/pull/3083))
- PEP 668 수정을 위해 업데이트 명령에서 pip에 `sys.executable` 사용 ([#3099](https://github.com/NousResearch/hermes-agent/pull/3099))
- 분기된 히스토리, 비main 브랜치, 게이트웨이 엣지 케이스에 대한 `hermes update` 강화 ([#3492](https://github.com/NousResearch/hermes-agent/pull/3492))
- OpenClaw 마이그레이션이 기본값을 덮어쓰고 설정 마법사가 가져온 섹션을 건너뛰는 문제 수정 ([#3282](https://github.com/NousResearch/hermes-agent/pull/3282))
- 재귀 AGENTS.md 탐색 중지, 최상위 수준만 로드 ([#3110](https://github.com/NousResearch/hermes-agent/pull/3110))
- 브라우저 및 터미널 PATH 해석에 macOS Homebrew 경로 추가 ([#2713](https://github.com/NousResearch/hermes-agent/pull/2713))
- `tool_progress` 설정에 대한 YAML 불리언 처리 ([#3300](https://github.com/NousResearch/hermes-agent/pull/3300))
- 기본 SOUL.md를 기본 아이덴티티 텍스트로 리셋 ([#3159](https://github.com/NousResearch/hermes-agent/pull/3159))
- 컨테이너 터미널 백엔드에 대한 상대 cwd 경로 거부 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- API 서버 플랫폼용 명시적 `hermes-api-server` 도구세트 추가 ([#3304](https://github.com/NousResearch/hermes-agent/pull/3304))
- 설정 마법사 프로바이더 순서 변경 — OpenRouter 우선 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))

---

## 🔧 도구 시스템

### API 서버
- **Idempotency-Key 지원**, 본문 크기 제한, OpenAI 에러 엔벨로프 ([#2903](https://github.com/NousResearch/hermes-agent/pull/2903))
- CORS 헤더에서 Idempotency-Key 허용 ([#3530](https://github.com/NousResearch/hermes-agent/pull/3530))
- SSE 연결 해제 시 고아 에이전트 취소 + 실제 인터럽트 ([#3427](https://github.com/NousResearch/hermes-agent/pull/3427))
- 에이전트가 도구를 호출할 때 스트리밍이 중단되는 문제 수정 ([#2985](https://github.com/NousResearch/hermes-agent/pull/2985))

### 터미널 및 파일 작업
- V4A 패치 파서에서 추가 전용 헝크 처리 ([#3325](https://github.com/NousResearch/hermes-agent/pull/3325))
- 영구 셸 폴링에 대한 지수 백오프 ([#2996](https://github.com/NousResearch/hermes-agent/pull/2996))
- `context_references`의 서브프로세스 호출에 타임아웃 추가 ([#3469](https://github.com/NousResearch/hermes-agent/pull/3469))

### 브라우저 및 비전
- 비전 도구에서 402 크레딧 부족 에러 처리 ([#2802](https://github.com/NousResearch/hermes-agent/pull/2802))
- `browser_vision`이 `auxiliary.vision.timeout` 설정을 무시하는 문제 수정 ([#2901](https://github.com/NousResearch/hermes-agent/pull/2901))
- config.yaml을 통한 브라우저 명령 타임아웃 설정 가능 ([#2801](https://github.com/NousResearch/hermes-agent/pull/2801))

### MCP
- 런타임 및 설정에 대한 MCP 도구세트 해석 ([#3252](https://github.com/NousResearch/hermes-agent/pull/3252))
- MCP 도구 이름 충돌 보호 추가 ([#3077](https://github.com/NousResearch/hermes-agent/pull/3077))

### 보조 LLM
- None 콘텐츠에 대한 보조 LLM 호출 보호 + 추론 폴백 + 재시도 ([#3449](https://github.com/NousResearch/hermes-agent/pull/3449))
- 비전 자동 감지에서 `build_anthropic_client`의 ImportError 잡기 ([#3312](https://github.com/NousResearch/hermes-agent/pull/3312))

### 기타 도구
- `send_message_tool` HTTP 호출에 요청 타임아웃 추가 ([#3162](https://github.com/NousResearch/hermes-agent/pull/3162)) by @memosr
- 잘못된 제어 문자가 있는 `jobs.json` 자동 복구 ([#3537](https://github.com/NousResearch/hermes-agent/pull/3537))
- Claude/OpenRouter에 대한 세밀한 도구 스트리밍 활성화 ([#3497](https://github.com/NousResearch/hermes-agent/pull/3497))

---

## 🧩 스킬 생태계

### 스킬 시스템
- **스킬 및 사용자 설정에 대한 환경 변수 전달** — 스킬이 전달할 환경 변수를 선언 가능 ([#2807](https://github.com/NousResearch/hermes-agent/pull/2807))
- 더 빠른 TTFT를 위한 공유 `skill_utils` 모듈로 스킬 프롬프트 캐시 ([#3421](https://github.com/NousResearch/hermes-agent/pull/3421))
- 스킬 조건에 대한 불필요한 파일 재읽기 방지 ([#2992](https://github.com/NousResearch/hermes-agent/pull/2992))
- 설치 중 조용한 하위 디렉토리 손실을 방지하기 위해 Git Trees API 사용 ([#2995](https://github.com/NousResearch/hermes-agent/pull/2995))
- 깊이 중첩된 저장소 구조에 대한 skills-sh 설치 수정 ([#2980](https://github.com/NousResearch/hermes-agent/pull/2980))
- 스킬 프론트매터에서 null 메타데이터 처리 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- skills-sh 식별자에 대한 신뢰 보존 + 해석 변동 감소 ([#3251](https://github.com/NousResearch/hermes-agent/pull/3251))
- 에이전트가 만든 스킬이 신뢰할 수 없는 커뮤니티 콘텐츠로 잘못 처리되는 문제 수정 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))

### 새로운 스킬
- **G0DM0D3 godmode 탈옥 스킬** + 문서 ([#3157](https://github.com/NousResearch/hermes-agent/pull/3157))
- **Docker 관리 스킬** — optional-skills에 추가 ([#3060](https://github.com/NousResearch/hermes-agent/pull/3060))
- **OpenClaw 마이그레이션 v2** — OpenClaw에서 Hermes로 마이그레이션하기 위한 17개 새 모듈, 터미널 요약 ([#2906](https://github.com/NousResearch/hermes-agent/pull/2906))

---

## 🔒 보안 및 안정성

### 보안 강화
- `browser_navigate`에 **SSRF 보호** 추가 ([#3058](https://github.com/NousResearch/hermes-agent/pull/3058))
- `vision_tools` 및 `web_tools`에 **SSRF 보호** 추가 (강화) ([#2679](https://github.com/NousResearch/hermes-agent/pull/2679))
- **서브에이전트 도구세트를 부모의 활성화된 세트로 제한** ([#3269](https://github.com/NousResearch/hermes-agent/pull/3269))
- 자체 업데이트에서 **zip-slip 경로 순회 방지** ([#3250](https://github.com/NousResearch/hermes-agent/pull/3250))
- `~user` 경로 접미사를 통한 `_expand_path`에서 **셸 인젝션 방지** ([#2685](https://github.com/NousResearch/hermes-agent/pull/2685))
- 위험한 명령 감지 전 **입력 정규화** ([#3260](https://github.com/NousResearch/hermes-agent/pull/3260))
- tirith 차단 판정을 하드 블록 대신 승인 가능으로 변경 ([#3428](https://github.com/NousResearch/hermes-agent/pull/3428))
- 의존성에서 손상된 `litellm`/`typer`/`platformdirs` 제거 ([#2796](https://github.com/NousResearch/hermes-agent/pull/2796))
- 모든 의존성 버전 범위 고정 ([#2810](https://github.com/NousResearch/hermes-agent/pull/2810))
- 해시가 포함된 `uv.lock` 재생성, 설정에서 잠금 파일 사용 ([#2812](https://github.com/NousResearch/hermes-agent/pull/2812))
- CVE 수정을 위한 의존성 업데이트 + `uv.lock` 재생성 ([#3073](https://github.com/NousResearch/hermes-agent/pull/3073))
- PR 스캔을 위한 공급망 감사 CI 워크플로우 ([#2816](https://github.com/NousResearch/hermes-agent/pull/2816))

### 안정성
- 15-20초 TUI 프리징을 야기하던 **SQLite WAL 쓰기 잠금 경합** 수정 ([#3385](https://github.com/NousResearch/hermes-agent/pull/3385))
- **SQLite 동시성 강화** + 세션 트랜스크립트 무결성 ([#3249](https://github.com/NousResearch/hermes-agent/pull/3249))
- 게이트웨이 충돌/재시작 루프에서 반복 cron 작업 재실행 방지 ([#3396](https://github.com/NousResearch/hermes-agent/pull/3396))
- 작업 완료 후 cron 세션을 종료로 표시 ([#2998](https://github.com/NousResearch/hermes-agent/pull/2998))

---

## ⚡ 성능

- **TTFT 시작 최적화** — 쉽게 달성 가능한 시작 개선 사항 적용 ([#3395](https://github.com/NousResearch/hermes-agent/pull/3395))
- 공유 `skill_utils` 모듈로 스킬 프롬프트 캐시 ([#3421](https://github.com/NousResearch/hermes-agent/pull/3421))
- 프롬프트 빌더에서 스킬 조건에 대한 불필요한 파일 재읽기 방지 ([#2992](https://github.com/NousResearch/hermes-agent/pull/2992))

---

## 🐛 주요 버그 수정

- 캐시된 에이전트와의 게이트웨이 토큰 이중 계산 수정 ([#3306](https://github.com/NousResearch/hermes-agent/pull/3306), [#3317](https://github.com/NousResearch/hermes-agent/pull/3317))
- 유휴 세션 중 "Event loop is closed" / "Press ENTER to continue" 수정 ([#3398](https://github.com/NousResearch/hermes-agent/pull/3398))
- 도구 호출 루프 중 추론 상자가 3번 렌더링되는 문제 수정 ([#3405](https://github.com/NousResearch/hermes-agent/pull/3405))
- 토큰 수에서 상태 바가 260K 대신 26K를 표시하는 문제 수정 ([#3024](https://github.com/NousResearch/hermes-agent/pull/3024))
- 설정에 관계없이 `/queue`가 항상 작동하는 문제 수정 ([#3298](https://github.com/NousResearch/hermes-agent/pull/3298))
- 에이전트 턴 후 유령 Discord 타이핑 표시기 수정 ([#3003](https://github.com/NousResearch/hermes-agent/pull/3003))
- Slack 진행 메시지가 잘못된 스레드에 나타나는 문제 수정 ([#3063](https://github.com/NousResearch/hermes-agent/pull/3063))
- WhatsApp 미디어 다운로드(문서, 오디오, 비디오) 수정 ([#2978](https://github.com/NousResearch/hermes-agent/pull/2978))
- Telegram "Message thread not found"가 진행 메시지를 중단시키는 문제 수정 ([#3390](https://github.com/NousResearch/hermes-agent/pull/3390))
- OpenClaw 마이그레이션이 기본값을 덮어쓰는 문제 수정 ([#3282](https://github.com/NousResearch/hermes-agent/pull/3282))
- 반환 사용자 설정 메뉴가 잘못된 섹션을 디스패치하는 문제 수정 ([#3083](https://github.com/NousResearch/hermes-agent/pull/3083))
- `hermes update` PEP 668 "externally-managed-environment" 에러 수정 ([#3099](https://github.com/NousResearch/hermes-agent/pull/3099))
- 공유 예산으로 인한 서브에이전트의 조기 `max_iterations` 도달 수정 ([#3004](https://github.com/NousResearch/hermes-agent/pull/3004))
- `tool_progress` 설정에 대한 YAML 불리언 처리 수정 ([#3300](https://github.com/NousResearch/hermes-agent/pull/3300))
- YAML null 값에서 `config.get()` 충돌 수정 ([#3377](https://github.com/NousResearch/hermes-agent/pull/3377))
- YAML 설정의 None 값에서 `.strip()` 충돌 수정 ([#3552](https://github.com/NousResearch/hermes-agent/pull/3552))
- 게이트웨이에서 멈춘 에이전트 수정 — `/stop`이 이제 세션 잠금을 강제 종료 ([#3104](https://github.com/NousResearch/hermes-agent/pull/3104))
- `_custom` 프로바이더가 조용히 `openrouter`로 재매핑되는 문제 수정 ([#2792](https://github.com/NousResearch/hermes-agent/pull/2792))
- `PLATFORMS` 딕셔너리에서 Matrix 누락 수정 ([#3473](https://github.com/NousResearch/hermes-agent/pull/3473))
- Email 어댑터의 무한 `_seen_uids` 증가 수정 ([#3490](https://github.com/NousResearch/hermes-agent/pull/3490))

---

## 🧪 테스트

- 업스트림 호환성 문제를 처리하기 위해 `agent-client-protocol` < 0.9로 고정 ([#3320](https://github.com/NousResearch/hermes-agent/pull/3320))
- 비전 자동 감지 테스트에서 anthropic ImportError 잡기 ([#3312](https://github.com/NousResearch/hermes-agent/pull/3312))
- 새로운 정상 반환 동작에 맞게 재시도 소진 테스트 업데이트 ([#3320](https://github.com/NousResearch/hermes-agent/pull/3320))
- null 메타데이터 프론트매터에 대한 회귀 테스트 추가 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))

---

## 📚 문서

- `/model` 명령어 전면 개편 및 사용자 정의 프로바이더 지원에 대한 모든 문서 업데이트 ([#2800](https://github.com/NousResearch/hermes-agent/pull/2800))
- 18개 파일에 걸친 오래되고 잘못된 문서 수정 ([#2805](https://github.com/NousResearch/hermes-agent/pull/2805))
- 이전에 문서화되지 않은 9개 기능 문서화 ([#2814](https://github.com/NousResearch/hermes-agent/pull/2814))
- 문서에 누락된 스킬, CLI 명령어, 메시징 환경 변수 추가 ([#2809](https://github.com/NousResearch/hermes-agent/pull/2809))
- api-server 응답 저장 문서 수정 — 인메모리가 아닌 SQLite ([#2819](https://github.com/NousResearch/hermes-agent/pull/2819))
- zsh glob 에러를 수정하기 위해 pip install extras에 따옴표 추가 ([#2815](https://github.com/NousResearch/hermes-agent/pull/2815))
- 훅 문서 통합 — 훅 페이지에 플러그인 훅 추가, `session:end` 이벤트 추가 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- `session_search` 스키마 설명에 두 가지 모드 동작 명확화 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))
- Discord 제공 초대 링크에 대한 Discord 공개 봇 설정 수정 ([#3519](https://github.com/NousResearch/hermes-agent/pull/3519)) by @mehmoodosman
- v0.4.0 변경 로그 수정 — 기능 귀속 수정, 섹션 재정렬 ([태그 없는 커밋](https://github.com/NousResearch/hermes-agent))

---

## 👥 기여자

### 코어
- **@teknium1** — 이번 릴리스 전체 범위를 아우르는 157개의 PR

### 커뮤니티 기여자
- **@alt-glitch** (Siddharth Balyan) — 2개의 PR: uv2nix 빌드, NixOS 모듈, 영구 컨테이너 모드를 갖춘 Nix flake ([#20](https://github.com/NousResearch/hermes-agent/pull/20)); Nix 빌드를 위한 자동 생성 설정 키 및 접미사 PATH ([#3061](https://github.com/NousResearch/hermes-agent/pull/3061), [#3274](https://github.com/NousResearch/hermes-agent/pull/3274))
- **@ctlst** — 1개의 PR: 게이트웨이 모드에서 AsyncOpenAI/httpx 크로스 루프 데드락 방지 ([#2701](https://github.com/NousResearch/hermes-agent/pull/2701))
- **@memosr** (memosr.eth) — 1개의 PR: `send_message_tool` HTTP 호출에 요청 타임아웃 추가 ([#3162](https://github.com/NousResearch/hermes-agent/pull/3162))
- **@mehmoodosman** (Osman Mehmood) — 1개의 PR: 공개 봇 설정에 대한 Discord 문서 수정 ([#3519](https://github.com/NousResearch/hermes-agent/pull/3519))

### 모든 기여자
@alt-glitch, @ctlst, @mehmoodosman, @memosr, @teknium1

---

**전체 변경 로그**: [v2026.3.23...v2026.3.28](https://github.com/NousResearch/hermes-agent/compare/v2026.3.23...v2026.3.28)
