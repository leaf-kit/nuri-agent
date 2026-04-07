# Hermes Agent v0.4.0 (v2026.3.23)

**릴리스 날짜:** 2026년 3월 23일

> 플랫폼 확장 릴리스 — OpenAI 호환 API 서버, 6개의 새로운 메시징 어댑터, 4개의 새로운 추론 프로바이더, OAuth 2.1을 갖춘 MCP 서버 관리, @ 컨텍스트 참조, 게이트웨이 프롬프트 캐싱, 기본 활성화된 스트리밍, 그리고 200건 이상의 버그 수정을 포함하는 전면적인 안정성 개선.

---

## ✨ 주요 하이라이트

- **OpenAI 호환 API 서버** — 크론 작업 관리를 위한 새로운 `/api/jobs` REST API와 함께 Hermes를 `/v1/chat/completions` 엔드포인트로 노출합니다. 입력 제한, 필드 화이트리스트, SQLite 기반 응답 영속성, CORS 오리진 보호로 강화되었습니다. ([#1756](https://github.com/NousResearch/hermes-agent/pull/1756), [#2450](https://github.com/NousResearch/hermes-agent/pull/2450), [#2456](https://github.com/NousResearch/hermes-agent/pull/2456), [#2451](https://github.com/NousResearch/hermes-agent/pull/2451), [#2472](https://github.com/NousResearch/hermes-agent/pull/2472))

- **6개의 새로운 메시징 플랫폼 어댑터** — Signal, DingTalk, SMS (Twilio), Mattermost, Matrix, Webhook 어댑터가 Telegram, Discord, WhatsApp에 합류합니다. 게이트웨이가 지수 백오프로 실패한 플랫폼을 자동 재연결합니다. ([#2206](https://github.com/NousResearch/hermes-agent/pull/2206), [#1685](https://github.com/NousResearch/hermes-agent/pull/1685), [#1688](https://github.com/NousResearch/hermes-agent/pull/1688), [#1683](https://github.com/NousResearch/hermes-agent/pull/1683), [#2166](https://github.com/NousResearch/hermes-agent/pull/2166), [#2584](https://github.com/NousResearch/hermes-agent/pull/2584))

- **@ 컨텍스트 참조** — CLI에서 탭 완성을 지원하는 Claude Code 스타일의 `@file` 및 `@url` 컨텍스트 주입. ([#2343](https://github.com/NousResearch/hermes-agent/pull/2343), [#2482](https://github.com/NousResearch/hermes-agent/pull/2482))

- **4개의 새로운 추론 프로바이더** — GitHub Copilot (OAuth + 토큰 검증), Alibaba Cloud / DashScope, Kilo Code, OpenCode Zen/Go. ([#1924](https://github.com/NousResearch/hermes-agent/pull/1924), [#1879](https://github.com/NousResearch/hermes-agent/pull/1879) by @mchzimm, [#1673](https://github.com/NousResearch/hermes-agent/pull/1673), [#1666](https://github.com/NousResearch/hermes-agent/pull/1666), [#1650](https://github.com/NousResearch/hermes-agent/pull/1650))

- **MCP 서버 관리 CLI** — 전체 OAuth 2.1 PKCE 플로우를 갖춘 MCP 서버 설치, 설정, 인증을 위한 `hermes mcp` 명령어. ([#2465](https://github.com/NousResearch/hermes-agent/pull/2465))

- **게이트웨이 프롬프트 캐싱** — 세션별 AIAgent 인스턴스를 캐시하여 긴 대화에서 Anthropic 프롬프트 캐시를 턴 간 보존, 극적인 비용 절감 효과. ([#2282](https://github.com/NousResearch/hermes-agent/pull/2282), [#2284](https://github.com/NousResearch/hermes-agent/pull/2284), [#2361](https://github.com/NousResearch/hermes-agent/pull/2361))

- **컨텍스트 압축 전면 개선** — 반복 업데이트를 포함한 구조화된 요약, 토큰 예산 테일 보호, 설정 가능한 요약 엔드포인트, 폴백 모델 지원. ([#2323](https://github.com/NousResearch/hermes-agent/pull/2323), [#1727](https://github.com/NousResearch/hermes-agent/pull/1727), [#2224](https://github.com/NousResearch/hermes-agent/pull/2224))

- **스트리밍 기본 활성화** — CLI에서 스트리밍이 기본으로 활성화되며, 스트리밍 모드 중 적절한 스피너/도구 진행 표시, 그리고 광범위한 줄바꿈 및 연결 수정. ([#2340](https://github.com/NousResearch/hermes-agent/pull/2340), [#2161](https://github.com/NousResearch/hermes-agent/pull/2161), [#2258](https://github.com/NousResearch/hermes-agent/pull/2258))

---

## 🖥️ CLI 및 사용자 경험

### 새로운 명령어 및 상호작용
- **@ 컨텍스트 완성** — 파일 콘텐츠나 웹 페이지를 대화에 주입하는 탭 완성 가능한 `@file`/`@url` 참조 ([#2482](https://github.com/NousResearch/hermes-agent/pull/2482), [#2343](https://github.com/NousResearch/hermes-agent/pull/2343))
- **`/statusbar`** — 프롬프트에 모델 + 프로바이더 정보를 표시하는 영구 설정 바 토글 ([#2240](https://github.com/NousResearch/hermes-agent/pull/2240), [#1917](https://github.com/NousResearch/hermes-agent/pull/1917))
- **`/queue`** — 현재 실행을 중단하지 않고 에이전트에 프롬프트 대기열 추가 ([#2191](https://github.com/NousResearch/hermes-agent/pull/2191), [#2469](https://github.com/NousResearch/hermes-agent/pull/2469))
- **`/permission`** — 세션 중 동적으로 승인 모드 전환 ([#2207](https://github.com/NousResearch/hermes-agent/pull/2207))
- **`/browser`** — CLI에서의 대화형 브라우저 세션 ([#2273](https://github.com/NousResearch/hermes-agent/pull/2273), [#1814](https://github.com/NousResearch/hermes-agent/pull/1814))
- **`/cost`** — 게이트웨이 모드에서의 실시간 가격 및 사용량 추적 ([#2180](https://github.com/NousResearch/hermes-agent/pull/2180))
- **`/approve` 및 `/deny`** — 게이트웨이에서 일반 텍스트 승인을 명시적 명령어로 대체 ([#2002](https://github.com/NousResearch/hermes-agent/pull/2002))

### 스트리밍 및 표시
- CLI에서 스트리밍 기본 활성화 ([#2340](https://github.com/NousResearch/hermes-agent/pull/2340))
- 스트리밍 모드 중 스피너 및 도구 진행 표시 ([#2161](https://github.com/NousResearch/hermes-agent/pull/2161))
- `show_reasoning` 활성화 시 추론/사고 블록 표시 ([#2118](https://github.com/NousResearch/hermes-agent/pull/2118))
- CLI 및 게이트웨이를 위한 컨텍스트 압력 경고 ([#2159](https://github.com/NousResearch/hermes-agent/pull/2159))
- 수정: 스트리밍 청크가 공백 없이 연결되는 문제 ([#2258](https://github.com/NousResearch/hermes-agent/pull/2258))
- 수정: 반복 경계 줄바꿈이 스트림 연결을 방해하는 문제 ([#2413](https://github.com/NousResearch/hermes-agent/pull/2413))
- 수정: 빈 줄 스태킹을 방지하기 위한 스트리밍 줄바꿈 지연 ([#2473](https://github.com/NousResearch/hermes-agent/pull/2473))
- 수정: 비TTY 환경에서 스피너 애니메이션 억제 ([#2216](https://github.com/NousResearch/hermes-agent/pull/2216))
- 수정: API 에러 메시지에 프로바이더 및 엔드포인트 표시 ([#2266](https://github.com/NousResearch/hermes-agent/pull/2266))
- 수정: 상태 출력에서 깨진 ANSI 이스케이프 코드 해결 ([#2448](https://github.com/NousResearch/hermes-agent/pull/2448))
- 수정: 골드 ANSI 색상을 트루 컬러 형식으로 업데이트 ([#2246](https://github.com/NousResearch/hermes-agent/pull/2246))
- 수정: 도구셋 레이블 정규화 및 배너에서 스킨 색상 사용 ([#1912](https://github.com/NousResearch/hermes-agent/pull/1912))

### CLI 개선
- 수정: 종료 시 'Press ENTER to continue...' 방지 ([#2555](https://github.com/NousResearch/hermes-agent/pull/2555))
- 수정: macOS 표시 멈춤을 방지하기 위한 에이전트 루프 중 stdout 플러시 ([#1654](https://github.com/NousResearch/hermes-agent/pull/1654))
- 수정: `hermes setup`에서 권한 에러 발생 시 사람이 읽을 수 있는 에러 표시 ([#2196](https://github.com/NousResearch/hermes-agent/pull/2196))
- 수정: `/stop` 명령어 충돌 + 스트리밍 미디어 전달에서의 UnboundLocalError ([#2463](https://github.com/NousResearch/hermes-agent/pull/2463))
- 수정: API 키 없이 커스텀/로컬 엔드포인트 허용 ([#2556](https://github.com/NousResearch/hermes-agent/pull/2556))
- 수정: Ghostty/WezTerm을 위한 Kitty 키보드 프로토콜 Shift+Enter (시도 후 prompt_toolkit 충돌로 인해 되돌림) ([#2345](https://github.com/NousResearch/hermes-agent/pull/2345), [#2349](https://github.com/NousResearch/hermes-agent/pull/2349))

### 설정
- config.yaml에서 **`${ENV_VAR}` 대체** ([#2684](https://github.com/NousResearch/hermes-agent/pull/2684))
- **실시간 설정 리로드** — 재시작 없이 config.yaml 변경 적용 ([#2210](https://github.com/NousResearch/hermes-agent/pull/2210))
- 사용자 관리 모델 추가를 위한 **`custom_models.yaml`** ([#2214](https://github.com/NousResearch/hermes-agent/pull/2214))
- **우선순위 기반 컨텍스트 파일 선택** + CLAUDE.md 지원 ([#2301](https://github.com/NousResearch/hermes-agent/pull/2301))
- 설정 업데이트 시 대체 대신 **중첩 YAML 섹션 병합** ([#2213](https://github.com/NousResearch/hermes-agent/pull/2213))
- 수정: config.yaml 프로바이더 키가 환경 변수를 자동으로 오버라이드 ([#2272](https://github.com/NousResearch/hermes-agent/pull/2272))
- 수정: config.yaml 에러를 자동으로 무시하는 대신 로그 경고 ([#2683](https://github.com/NousResearch/hermes-agent/pull/2683))
- 수정: 비활성화된 도구셋이 `hermes tools` 후 다시 활성화 ([#2268](https://github.com/NousResearch/hermes-agent/pull/2268))
- 수정: 플랫폼 기본 도구셋이 도구 선택 해제를 자동으로 오버라이드 ([#2624](https://github.com/NousResearch/hermes-agent/pull/2624))
- 수정: 단순 YAML `approvals.mode: off` 준수 ([#2620](https://github.com/NousResearch/hermes-agent/pull/2620))
- 수정: `hermes update`에서 폴백과 함께 `.[all]` extras 사용 ([#1728](https://github.com/NousResearch/hermes-agent/pull/1728))
- 수정: stash 충돌 시 작업 트리 리셋 전 `hermes update` 프롬프트 ([#2390](https://github.com/NousResearch/hermes-agent/pull/2390))
- 수정: 분기 브랜치 에러를 방지하기 위해 update/install에서 git pull --rebase 사용 ([#2274](https://github.com/NousResearch/hermes-agent/pull/2274))
- 수정: 새 macOS 설치에서 zprofile 폴백 추가 및 zshrc 생성 ([#2320](https://github.com/NousResearch/hermes-agent/pull/2320))
- 수정: 충돌 방지를 위해 `ANTHROPIC_BASE_URL` 환경 변수 제거 ([#1675](https://github.com/NousResearch/hermes-agent/pull/1675))
- 수정: 키링 또는 환경에 이미 있으면 IMAP 비밀번호 묻지 않기 ([#2212](https://github.com/NousResearch/hermes-agent/pull/2212))
- 수정: OpenCode Zen/Go가 자체 모델 대신 OpenRouter 모델을 표시 ([#2277](https://github.com/NousResearch/hermes-agent/pull/2277))

---

## 🏗️ 코어 에이전트 및 아키텍처

### 새로운 프로바이더
- **GitHub Copilot** — 전체 OAuth 인증, API 라우팅, 토큰 검증, 400k 컨텍스트. ([#1924](https://github.com/NousResearch/hermes-agent/pull/1924), [#1896](https://github.com/NousResearch/hermes-agent/pull/1896), [#1879](https://github.com/NousResearch/hermes-agent/pull/1879) by @mchzimm, [#2507](https://github.com/NousResearch/hermes-agent/pull/2507))
- **Alibaba Cloud / DashScope** — DashScope v1 런타임, 모델 점 보존, 401 인증 수정을 갖춘 전체 통합 ([#1673](https://github.com/NousResearch/hermes-agent/pull/1673), [#2332](https://github.com/NousResearch/hermes-agent/pull/2332), [#2459](https://github.com/NousResearch/hermes-agent/pull/2459))
- **Kilo Code** — 일급 추론 프로바이더 ([#1666](https://github.com/NousResearch/hermes-agent/pull/1666))
- **OpenCode Zen 및 OpenCode Go** — 새로운 프로바이더 백엔드 ([#1650](https://github.com/NousResearch/hermes-agent/pull/1650), [#2393](https://github.com/NousResearch/hermes-agent/pull/2393) by @0xbyt4)
- **NeuTTS** — 내장 설정 플로우를 갖춘 로컬 TTS 프로바이더 백엔드, 이전 선택적 스킬 대체 ([#1657](https://github.com/NousResearch/hermes-agent/pull/1657), [#1664](https://github.com/NousResearch/hermes-agent/pull/1664))

### 프로바이더 개선
- 속도 제한 에러 시 백업 모델로 **즉시 폴백** ([#1730](https://github.com/NousResearch/hermes-agent/pull/1730))
- 커스텀 모델 컨텍스트 및 가격을 위한 **엔드포인트 메타데이터**; 로컬 서버에서 실제 컨텍스트 윈도우 크기 조회 ([#1906](https://github.com/NousResearch/hermes-agent/pull/1906), [#2091](https://github.com/NousResearch/hermes-agent/pull/2091) by @dusterbloom)
- **컨텍스트 길이 감지 전면 개선** — models.dev 통합, 프로바이더 인식 해석, 커스텀 엔드포인트를 위한 퍼지 매칭, llama.cpp를 위한 `/v1/props` ([#2158](https://github.com/NousResearch/hermes-agent/pull/2158), [#2051](https://github.com/NousResearch/hermes-agent/pull/2051), [#2403](https://github.com/NousResearch/hermes-agent/pull/2403))
- **모델 카탈로그 업데이트** — gpt-5.4-mini, gpt-5.4-nano, healer-alpha, haiku-4.5, minimax-m2.7, 1M 컨텍스트의 claude 4.6 ([#1913](https://github.com/NousResearch/hermes-agent/pull/1913), [#1915](https://github.com/NousResearch/hermes-agent/pull/1915), [#1900](https://github.com/NousResearch/hermes-agent/pull/1900), [#2155](https://github.com/NousResearch/hermes-agent/pull/2155), [#2474](https://github.com/NousResearch/hermes-agent/pull/2474))
- **커스텀 엔드포인트 개선** — config.yaml에서의 `model.base_url`, responses API를 위한 `api_mode` 오버라이드, API 키 없는 엔드포인트 허용, 누락된 키에 대한 빠른 실패 ([#2330](https://github.com/NousResearch/hermes-agent/pull/2330), [#1651](https://github.com/NousResearch/hermes-agent/pull/1651), [#2556](https://github.com/NousResearch/hermes-agent/pull/2556), [#2445](https://github.com/NousResearch/hermes-agent/pull/2445), [#1994](https://github.com/NousResearch/hermes-agent/pull/1994), [#1998](https://github.com/NousResearch/hermes-agent/pull/1998))
- 시스템 프롬프트에 모델 및 프로바이더 주입 ([#1929](https://github.com/NousResearch/hermes-agent/pull/1929))
- 환경 변수 대신 프로바이더 설정에 `api_mode` 연결 ([#1656](https://github.com/NousResearch/hermes-agent/pull/1656))
- 수정: 서드파티 `anthropic_messages` 프로바이더에 Anthropic 토큰 누출 방지 ([#2389](https://github.com/NousResearch/hermes-agent/pull/2389))
- 수정: 비Anthropic `base_url`을 상속하는 Anthropic 폴백 방지 ([#2388](https://github.com/NousResearch/hermes-agent/pull/2388))
- 수정: `auxiliary_is_nous` 플래그가 리셋되지 않음 — 다른 프로바이더에 Nous 태그 누출 ([#1713](https://github.com/NousResearch/hermes-agent/pull/1713))
- 수정: Anthropic `tool_choice 'none'`이 여전히 도구 호출을 허용 ([#1714](https://github.com/NousResearch/hermes-agent/pull/1714))
- 수정: Mistral 파서 중첩 JSON 폴백 추출 ([#2335](https://github.com/NousResearch/hermes-agent/pull/2335))
- 수정: `anthropic_messages` 기본값으로 MiniMax 401 인증 해결 ([#2103](https://github.com/NousResearch/hermes-agent/pull/2103))
- 수정: 대소문자 무시 모델 패밀리 매칭 ([#2350](https://github.com/NousResearch/hermes-agent/pull/2350))
- 수정: 활성화 검사에서 플레이스홀더 프로바이더 키 무시 ([#2358](https://github.com/NousResearch/hermes-agent/pull/2358))
- 수정: 컨텍스트 길이 감지에서 Ollama model:tag 콜론 보존 ([#2149](https://github.com/NousResearch/hermes-agent/pull/2149))
- 수정: 시작 게이트에서 Claude Code OAuth 인증 정보 인식 ([#1663](https://github.com/NousResearch/hermes-agent/pull/1663))
- 수정: OAuth user-agent를 위한 Claude Code 버전 동적 감지 ([#1670](https://github.com/NousResearch/hermes-agent/pull/1670))
- 수정: 갱신/폴백 후 OAuth 플래그 부실 ([#1890](https://github.com/NousResearch/hermes-agent/pull/1890))
- 수정: 보조 클라이언트가 만료된 Codex JWT 건너뛰기 ([#2397](https://github.com/NousResearch/hermes-agent/pull/2397))

### 에이전트 루프
- **게이트웨이 프롬프트 캐싱** — 세션별 AIAgent 캐시, 어시스턴트 턴 유지, 세션 복원 수정 ([#2282](https://github.com/NousResearch/hermes-agent/pull/2282), [#2284](https://github.com/NousResearch/hermes-agent/pull/2284), [#2361](https://github.com/NousResearch/hermes-agent/pull/2361))
- **컨텍스트 압축 전면 개선** — 구조화된 요약, 반복 업데이트, 토큰 예산 테일 보호, 설정 가능한 `summary_base_url` ([#2323](https://github.com/NousResearch/hermes-agent/pull/2323), [#1727](https://github.com/NousResearch/hermes-agent/pull/1727), [#2224](https://github.com/NousResearch/hermes-agent/pull/2224))
- **사전 호출 살균 및 사후 호출 도구 가드레일** ([#1732](https://github.com/NousResearch/hermes-agent/pull/1732))
- 프로바이더가 거부한 `tool_choice`에서 제거 후 재시도로 **자동 복구** ([#2174](https://github.com/NousResearch/hermes-agent/pull/2174))
- 인라인 넛지를 대체하는 **백그라운드 메모리/스킬 검토** ([#2235](https://github.com/NousResearch/hermes-agent/pull/2235))
- 하드코딩된 기본값 대신 **SOUL.md를 기본 에이전트 정체성으로** ([#1922](https://github.com/NousResearch/hermes-agent/pull/1922))
- 수정: 컨텍스트 압축 중 자동 도구 결과 손실 방지 ([#1993](https://github.com/NousResearch/hermes-agent/pull/1993))
- 수정: 도구 호출 복구에서 빈/null 함수 인수 처리 ([#2163](https://github.com/NousResearch/hermes-agent/pull/2163))
- 수정: 충돌 대신 API 거부 응답을 우아하게 처리 ([#2156](https://github.com/NousResearch/hermes-agent/pull/2156))
- 수정: 잘못된 도구 호출에서 에이전트 루프 멈춤 방지 ([#2114](https://github.com/NousResearch/hermes-agent/pull/2114))
- 수정: 빈 인수로 디스패치하는 대신 JSON 파싱 에러를 모델에 반환 ([#2342](https://github.com/NousResearch/hermes-agent/pull/2342))
- 수정: 혼합 타입에서 연속 어시스턴트 메시지 병합 시 콘텐츠 누락 ([#1703](https://github.com/NousResearch/hermes-agent/pull/1703))
- 수정: JSON 복구 및 에러 핸들러에서 메시지 역할 교대 위반 ([#1722](https://github.com/NousResearch/hermes-agent/pull/1722))
- 수정: `compression_attempts`가 매 반복마다 리셋 — 무제한 압축 허용 ([#1723](https://github.com/NousResearch/hermes-agent/pull/1723))
- 수정: `length_continue_retries`가 리셋되지 않음 — 이후 잘림에서 재시도 횟수 감소 ([#1717](https://github.com/NousResearch/hermes-agent/pull/1717))
- 수정: 압축기 요약 역할이 연속 역할 제약 위반 ([#1720](https://github.com/NousResearch/hermes-agent/pull/1720), [#1743](https://github.com/NousResearch/hermes-agent/pull/1743))
- 수정: 하드코딩된 `gemini-3-flash-preview`를 기본 요약 모델에서 제거 ([#2464](https://github.com/NousResearch/hermes-agent/pull/2464))
- 수정: 빈 도구 결과 올바르게 처리 ([#2201](https://github.com/NousResearch/hermes-agent/pull/2201))
- 수정: `tool_calls` 목록에서 None 항목으로 인한 충돌 ([#2209](https://github.com/NousResearch/hermes-agent/pull/2209) by @0xbyt4, [#2316](https://github.com/NousResearch/hermes-agent/pull/2316))
- 수정: 워커 스레드에서 스레드별 영구 이벤트 루프 ([#2214](https://github.com/NousResearch/hermes-agent/pull/2214) by @jquesnelle)
- 수정: 비동기 도구가 병렬 실행될 때 '이벤트 루프가 이미 실행 중' 방지 ([#2207](https://github.com/NousResearch/hermes-agent/pull/2207))
- 수정: 소스에서 ANSI 제거 — 모델에 도달하기 전 깨끗한 터미널 출력 ([#2115](https://github.com/NousResearch/hermes-agent/pull/2115))
- 수정: OpenRouter에서 role:tool의 최상위 `cache_control` 건너뛰기 ([#2391](https://github.com/NousResearch/hermes-agent/pull/2391))
- 수정: 위임 도구 — 자식 생성이 전역을 변경하기 전에 부모 도구 이름 저장 ([#2083](https://github.com/NousResearch/hermes-agent/pull/2083) by @ygd58, [#1894](https://github.com/NousResearch/hermes-agent/pull/1894))
- 수정: 빈 문자열인 경우에만 마지막 어시스턴트 메시지 제거 ([#2326](https://github.com/NousResearch/hermes-agent/pull/2326))

### 세션 및 메모리
- **세션 검색** 및 관리 슬래시 명령어 ([#2198](https://github.com/NousResearch/hermes-agent/pull/2198))
- **자동 세션 제목** 및 `.hermes.md` 프로젝트 설정 ([#1712](https://github.com/NousResearch/hermes-agent/pull/1712))
- 수정: 동시 메모리 쓰기가 자동으로 항목을 삭제 — 파일 잠금 추가 ([#1726](https://github.com/NousResearch/hermes-agent/pull/1726))
- 수정: `session_search`에서 기본적으로 모든 소스 검색 ([#1892](https://github.com/NousResearch/hermes-agent/pull/1892))
- 수정: 하이픈이 있는 FTS5 쿼리 처리 및 인용된 리터럴 보존 ([#1776](https://github.com/NousResearch/hermes-agent/pull/1776))
- 수정: 충돌 대신 `load_transcript`에서 손상된 줄 건너뛰기 ([#1744](https://github.com/NousResearch/hermes-agent/pull/1744))
- 수정: 대소문자 구분 중복을 방지하기 위한 세션 키 정규화 ([#2157](https://github.com/NousResearch/hermes-agent/pull/2157))
- 수정: 세션이 없을 때 `session_search` 충돌 방지 ([#2194](https://github.com/NousResearch/hermes-agent/pull/2194))
- 수정: 정확한 사용량 표시를 위해 새 세션에서 토큰 카운터 리셋 ([#2101](https://github.com/NousResearch/hermes-agent/pull/2101) by @InB4DevOps)
- 수정: 플러시 에이전트에 의한 오래된 메모리 덮어쓰기 방지 ([#2687](https://github.com/NousResearch/hermes-agent/pull/2687))
- 수정: 합성 에러 메시지 주입 제거, 반복 실패 후 세션 재개 수정 ([#2303](https://github.com/NousResearch/hermes-agent/pull/2303))
- 수정: `--resume`을 사용하는 조용 모드가 이제 conversation_history 전달 ([#2357](https://github.com/NousResearch/hermes-agent/pull/2357))
- 수정: 배치 모드에서 재개 로직 통합 ([#2331](https://github.com/NousResearch/hermes-agent/pull/2331))

### Honcho 메모리
- Honcho 설정 수정 및 @ 컨텍스트 참조 통합 ([#2343](https://github.com/NousResearch/hermes-agent/pull/2343))
- 자체 호스팅 / Docker 설정 문서 ([#2475](https://github.com/NousResearch/hermes-agent/pull/2475))

---

## 📱 메시징 플랫폼 (게이트웨이)

### 새로운 플랫폼 어댑터
- **Signal Messenger** — 첨부 파일 처리, 그룹 메시지 필터링, Note to Self 에코백 보호를 갖춘 전체 어댑터 ([#2206](https://github.com/NousResearch/hermes-agent/pull/2206), [#2400](https://github.com/NousResearch/hermes-agent/pull/2400), [#2297](https://github.com/NousResearch/hermes-agent/pull/2297), [#2156](https://github.com/NousResearch/hermes-agent/pull/2156))
- **DingTalk** — 게이트웨이 연결 및 설정 문서가 있는 어댑터 ([#1685](https://github.com/NousResearch/hermes-agent/pull/1685), [#1690](https://github.com/NousResearch/hermes-agent/pull/1690), [#1692](https://github.com/NousResearch/hermes-agent/pull/1692))
- **SMS (Twilio)** ([#1688](https://github.com/NousResearch/hermes-agent/pull/1688))
- **Mattermost** — @멘션 전용 채널 필터 포함 ([#1683](https://github.com/NousResearch/hermes-agent/pull/1683), [#2443](https://github.com/NousResearch/hermes-agent/pull/2443))
- **Matrix** — 비전 지원 및 이미지 캐싱 포함 ([#1683](https://github.com/NousResearch/hermes-agent/pull/1683), [#2520](https://github.com/NousResearch/hermes-agent/pull/2520))
- **Webhook** — 외부 이벤트 트리거를 위한 플랫폼 어댑터 ([#2166](https://github.com/NousResearch/hermes-agent/pull/2166))
- **OpenAI 호환 API 서버** — `/api/jobs` 크론 관리를 갖춘 `/v1/chat/completions` 엔드포인트 ([#1756](https://github.com/NousResearch/hermes-agent/pull/1756), [#2450](https://github.com/NousResearch/hermes-agent/pull/2450), [#2456](https://github.com/NousResearch/hermes-agent/pull/2456))

### Telegram 개선
- MarkdownV2 지원 — 취소선, 스포일러, 인용구, 괄호/중괄호/백슬래시/백틱 이스케이프 ([#2199](https://github.com/NousResearch/hermes-agent/pull/2199), [#2200](https://github.com/NousResearch/hermes-agent/pull/2200) by @llbn, [#2386](https://github.com/NousResearch/hermes-agent/pull/2386))
- HTML 태그 자동 감지 및 `parse_mode=HTML` 사용 ([#1709](https://github.com/NousResearch/hermes-agent/pull/1709))
- Telegram 그룹 비전 지원 + 스레드 기반 세션 ([#2153](https://github.com/NousResearch/hermes-agent/pull/2153))
- 네트워크 중단 후 폴링 자동 재연결 ([#2517](https://github.com/NousResearch/hermes-agent/pull/2517))
- 디스패치 전 분할된 텍스트 메시지 집계 ([#1674](https://github.com/NousResearch/hermes-agent/pull/1674))
- 수정: 스트리밍 설정 브릿지, not-modified, 플러드 제어 ([#1782](https://github.com/NousResearch/hermes-agent/pull/1782), [#1783](https://github.com/NousResearch/hermes-agent/pull/1783))
- 수정: edited_message 이벤트 충돌 ([#2074](https://github.com/NousResearch/hermes-agent/pull/2074))
- 수정: 포기 전 409 폴링 충돌 재시도 ([#2312](https://github.com/NousResearch/hermes-agent/pull/2312))
- 수정: `platform:chat_id:thread_id` 형식을 통한 토픽 전달 ([#2455](https://github.com/NousResearch/hermes-agent/pull/2455))

### Discord 개선
- 문서 캐싱 및 텍스트 파일 주입 ([#2503](https://github.com/NousResearch/hermes-agent/pull/2503))
- DM을 위한 영구 타이핑 인디케이터 ([#2468](https://github.com/NousResearch/hermes-agent/pull/2468))
- Discord DM 비전 — 인라인 이미지 + 첨부 파일 분석 ([#2186](https://github.com/NousResearch/hermes-agent/pull/2186))
- 게이트웨이 재시작 간 스레드 참여 유지 ([#1661](https://github.com/NousResearch/hermes-agent/pull/1661))
- 수정: 비ASCII 길드 이름에서의 게이트웨이 충돌 ([#2302](https://github.com/NousResearch/hermes-agent/pull/2302))
- 수정: 스레드 권한 에러 ([#2073](https://github.com/NousResearch/hermes-agent/pull/2073))
- 수정: 스레드에서의 슬래시 이벤트 라우팅 ([#2460](https://github.com/NousResearch/hermes-agent/pull/2460))
- 수정: 버그가 있는 후속 메시지 + `/ask` 명령어 제거 ([#1836](https://github.com/NousResearch/hermes-agent/pull/1836))
- 수정: 우아한 WebSocket 재연결 ([#2127](https://github.com/NousResearch/hermes-agent/pull/2127))
- 수정: 스트리밍 활성화 시 음성 채널 TTS ([#2322](https://github.com/NousResearch/hermes-agent/pull/2322))

### WhatsApp 및 기타 어댑터
- WhatsApp: 아웃바운드 `send_message` 라우팅 ([#1769](https://github.com/NousResearch/hermes-agent/pull/1769) by @sai-samarth), LID 형식 셀프 채팅 ([#1667](https://github.com/NousResearch/hermes-agent/pull/1667)), `reply_prefix` 설정 수정 ([#1923](https://github.com/NousResearch/hermes-agent/pull/1923)), 브릿지 자식 프로세스 종료 시 재시작 ([#2334](https://github.com/NousResearch/hermes-agent/pull/2334)), 이미지/브릿지 개선 ([#2181](https://github.com/NousResearch/hermes-agent/pull/2181))
- Matrix: 올바른 `reply_to_message_id` 파라미터 ([#1895](https://github.com/NousResearch/hermes-agent/pull/1895)), 기본 미디어 타입 수정 ([#1736](https://github.com/NousResearch/hermes-agent/pull/1736))
- Mattermost: 미디어 첨부에 MIME 타입 ([#2329](https://github.com/NousResearch/hermes-agent/pull/2329))

### 게이트웨이 코어
- 지수 백오프를 통한 실패 플랫폼 **자동 재연결** ([#2584](https://github.com/NousResearch/hermes-agent/pull/2584))
- **세션 자동 리셋 시 사용자에게 알림** ([#2519](https://github.com/NousResearch/hermes-agent/pull/2519))
- 세션 외 답장에 대한 **답장 대상 메시지 컨텍스트** ([#1662](https://github.com/NousResearch/hermes-agent/pull/1662))
- **승인되지 않은 DM 무시** 설정 옵션 ([#1919](https://github.com/NousResearch/hermes-agent/pull/1919))
- 수정: 스레드 모드에서 `/reset`이 스레드 대신 전역 세션을 리셋 ([#2254](https://github.com/NousResearch/hermes-agent/pull/2254))
- 수정: 스트리밍 응답 후 MEDIA: 파일 전달 ([#2382](https://github.com/NousResearch/hermes-agent/pull/2382))
- 수정: 리소스 고갈 방지를 위한 인터럽트 재귀 깊이 제한 ([#1659](https://github.com/NousResearch/hermes-agent/pull/1659))
- 수정: `--replace`에서 중단된 프로세스 감지 및 오래된 잠금 해제 ([#2406](https://github.com/NousResearch/hermes-agent/pull/2406), [#1908](https://github.com/NousResearch/hermes-agent/pull/1908))
- 수정: 게이트웨이 재시작을 위한 PID 기반 대기와 강제 종료 ([#1902](https://github.com/NousResearch/hermes-agent/pull/1902))
- 수정: `--replace` 모드가 호출자 프로세스를 종료하는 것 방지 ([#2185](https://github.com/NousResearch/hermes-agent/pull/2185))
- 수정: `/model`이 설정 기본값 대신 활성 폴백 모델 표시 ([#1660](https://github.com/NousResearch/hermes-agent/pull/1660))
- 수정: SQLite에 세션이 아직 없을 때 `/title` 명령어 실패 ([#2379](https://github.com/NousResearch/hermes-agent/pull/2379) by @ten-jampa)
- 수정: 에이전트 완료 후 `/queue` 메시지 처리 ([#2469](https://github.com/NousResearch/hermes-agent/pull/2469))
- 수정: 고아 `tool_results` 제거 + 실행 중인 에이전트를 우회하는 `/reset` 허용 ([#2180](https://github.com/NousResearch/hermes-agent/pull/2180))
- 수정: systemd 관리 외부에서 에이전트가 게이트웨이를 시작하는 것 방지 ([#2617](https://github.com/NousResearch/hermes-agent/pull/2617))
- 수정: 게이트웨이 연결 실패 시 systemd 재시작 폭풍 방지 ([#2327](https://github.com/NousResearch/hermes-agent/pull/2327))
- 수정: systemd 유닛에 해석된 node 경로 포함 ([#1767](https://github.com/NousResearch/hermes-agent/pull/1767) by @sai-samarth)
- 수정: 게이트웨이 외부 예외 핸들러에서 사용자에게 에러 세부 정보 전송 ([#1966](https://github.com/NousResearch/hermes-agent/pull/1966))
- 수정: 429 사용 제한 및 500 컨텍스트 오버플로우에 대한 에러 처리 개선 ([#1839](https://github.com/NousResearch/hermes-agent/pull/1839))
- 수정: 시작 경고 확인에 모든 누락된 플랫폼 허용 목록 환경 변수 추가 ([#2628](https://github.com/NousResearch/hermes-agent/pull/2628))
- 수정: 공백이 포함된 파일 경로에서 미디어 전달 실패 ([#2621](https://github.com/NousResearch/hermes-agent/pull/2621))
- 수정: 다중 플랫폼 게이트웨이에서 중복 세션 키 충돌 ([#2171](https://github.com/NousResearch/hermes-agent/pull/2171))
- 수정: Matrix 및 Mattermost가 연결됨으로 보고되지 않음 ([#1711](https://github.com/NousResearch/hermes-agent/pull/1711))
- 수정: PII 수정 설정이 읽히지 않음 — yaml 임포트 누락 ([#1701](https://github.com/NousResearch/hermes-agent/pull/1701))
- 수정: 스킬 슬래시 명령어에서의 NameError ([#1697](https://github.com/NousResearch/hermes-agent/pull/1697))
- 수정: 충돌 복구를 위해 체크포인트에 감시자 메타데이터 유지 ([#1706](https://github.com/NousResearch/hermes-agent/pull/1706))
- 수정: send_image_file, send_document, send_video에서 `message_thread_id` 전달 ([#2339](https://github.com/NousResearch/hermes-agent/pull/2339))
- 수정: 빠른 연속 사진 메시지에서 미디어 그룹 집계 ([#2160](https://github.com/NousResearch/hermes-agent/pull/2160))

---

## 🔧 도구 시스템

### MCP 개선
- OAuth 2.1 PKCE 인증을 갖춘 **MCP 서버 관리 CLI** ([#2465](https://github.com/NousResearch/hermes-agent/pull/2465))
- **MCP 서버를 독립 도구셋으로 노출** ([#1907](https://github.com/NousResearch/hermes-agent/pull/1907))
- `hermes tools`에서의 **대화형 MCP 도구 설정** ([#1694](https://github.com/NousResearch/hermes-agent/pull/1694))
- 수정: MCP-OAuth 포트 불일치, 경로 탐색, 공유 핸들러 상태 ([#2552](https://github.com/NousResearch/hermes-agent/pull/2552))
- 수정: 세션 리셋 간 MCP 도구 등록 보존 ([#2124](https://github.com/NousResearch/hermes-agent/pull/2124))
- 수정: 동시 파일 접근 충돌 + 중복 MCP 등록 ([#2154](https://github.com/NousResearch/hermes-agent/pull/2154))
- 수정: MCP 스키마 정규화 + 세션 목록 컬럼 확장 ([#2102](https://github.com/NousResearch/hermes-agent/pull/2102))
- 수정: `tool_choice` `mcp_` 접두사 처리 ([#1775](https://github.com/NousResearch/hermes-agent/pull/1775))

### 웹 도구 백엔드
- 웹 검색/추출/크롤링 백엔드로 **Tavily** ([#1731](https://github.com/NousResearch/hermes-agent/pull/1731))
- 대체 웹 검색/추출 백엔드로 **Parallel** ([#1696](https://github.com/NousResearch/hermes-agent/pull/1696))
- **설정 가능한 웹 백엔드** — Firecrawl/BeautifulSoup/Playwright 선택 ([#2256](https://github.com/NousResearch/hermes-agent/pull/2256))
- 수정: 공백만 있는 환경 변수가 웹 백엔드 감지를 우회 ([#2341](https://github.com/NousResearch/hermes-agent/pull/2341))

### 새로운 도구
- **IMAP email** 읽기 및 전송 ([#2173](https://github.com/NousResearch/hermes-agent/pull/2173))
- Whisper API를 사용한 **STT (음성-텍스트)** 도구 ([#2072](https://github.com/NousResearch/hermes-agent/pull/2072))
- **경로 인식 가격 견적** ([#1695](https://github.com/NousResearch/hermes-agent/pull/1695))

### 도구 개선
- TTS: OpenAI TTS 프로바이더를 위한 `base_url` 지원 ([#2064](https://github.com/NousResearch/hermes-agent/pull/2064) by @hanai)
- 비전: 설정 가능한 타임아웃, 파일 경로에서 물결표 확장, 다중 이미지 및 base64 폴백을 갖춘 DM 비전 ([#2480](https://github.com/NousResearch/hermes-agent/pull/2480), [#2585](https://github.com/NousResearch/hermes-agent/pull/2585), [#2211](https://github.com/NousResearch/hermes-agent/pull/2211))
- 브라우저: 세션 생성에서의 레이스 컨디션 수정 ([#1721](https://github.com/NousResearch/hermes-agent/pull/1721)), 예상치 못한 LLM 파라미터에서의 TypeError ([#1735](https://github.com/NousResearch/hermes-agent/pull/1735))
- 파일 도구: write_file 및 patch 콘텐츠에서 ANSI 이스케이프 코드 제거 ([#2532](https://github.com/NousResearch/hermes-agent/pull/2532)), 반복 검색 키에 페이지네이션 인수 포함 ([#1824](https://github.com/NousResearch/hermes-agent/pull/1824) by @cutepawss), 퍼지 매칭 정확도 향상 + 위치 계산 리팩토링 ([#2096](https://github.com/NousResearch/hermes-agent/pull/2096), [#1681](https://github.com/NousResearch/hermes-agent/pull/1681))
- 코드 실행: 리소스 누수 및 이중 소켓 닫기 수정 ([#2381](https://github.com/NousResearch/hermes-agent/pull/2381))
- 위임: 동시 서브에이전트 위임을 위한 스레드 안전성 ([#1672](https://github.com/NousResearch/hermes-agent/pull/1672)), 위임 후 부모 에이전트의 도구 목록 보존 ([#1778](https://github.com/NousResearch/hermes-agent/pull/1778))
- 수정: 파일 변이를 위한 동시 도구 배칭 경로 인식 ([#1914](https://github.com/NousResearch/hermes-agent/pull/1914))
- 수정: 플랫폼 디스패치 전 `send_message_tool`에서 긴 메시지 청크 분할 ([#1646](https://github.com/NousResearch/hermes-agent/pull/1646))
- 수정: 누락된 'messaging' 도구셋 추가 ([#1718](https://github.com/NousResearch/hermes-agent/pull/1718))
- 수정: 사용 불가능한 도구 이름이 모델 스키마에 누출되는 것 방지 ([#2072](https://github.com/NousResearch/hermes-agent/pull/2072))
- 수정: 다이아몬드 의존성 중복을 방지하기 위해 방문 집합을 참조로 전달 ([#2311](https://github.com/NousResearch/hermes-agent/pull/2311))
- 수정: Daytona 샌드박스 조회가 `find_one`에서 `get/list`로 마이그레이션 ([#2063](https://github.com/NousResearch/hermes-agent/pull/2063) by @rovle)

---

## 🧩 스킬 생태계

### 스킬 시스템 개선
- **에이전트 생성 스킬** — 주의 수준 발견 허용, 위험 스킬은 차단 대신 질문 ([#1840](https://github.com/NousResearch/hermes-agent/pull/1840), [#2446](https://github.com/NousResearch/hermes-agent/pull/2446))
- `/skills install` 및 uninstall에서 확인을 건너뛰는 **`--yes` 플래그** ([#1647](https://github.com/NousResearch/hermes-agent/pull/1647))
- 배너, 시스템 프롬프트, 슬래시 명령어 전반에서 **비활성화된 스킬 존중** ([#1897](https://github.com/NousResearch/hermes-agent/pull/1897))
- 수정: 스킬 custom_tools 임포트 충돌 + 샌드박스 file_tools 통합 ([#2239](https://github.com/NousResearch/hermes-agent/pull/2239))
- 수정: pip 요구사항이 있는 에이전트 생성 스킬 설치 시 충돌 ([#2145](https://github.com/NousResearch/hermes-agent/pull/2145))
- 수정: `hub.yaml` 누락 시 `Skills.__init__`에서의 레이스 컨디션 ([#2242](https://github.com/NousResearch/hermes-agent/pull/2242))
- 수정: 설치 전 스킬 메타데이터 검증 및 중복 차단 ([#2241](https://github.com/NousResearch/hermes-agent/pull/2241))
- 수정: 스킬 허브 inspect/resolve — inspect, 리다이렉트, 탐색, tap 목록의 4가지 버그 ([#2447](https://github.com/NousResearch/hermes-agent/pull/2447))
- 수정: 세션 리셋 후에도 에이전트 생성 스킬이 계속 작동 ([#2121](https://github.com/NousResearch/hermes-agent/pull/2121))

### 새로운 스킬
- **OCR-and-documents** — 선택적 GPU를 갖춘 PDF/DOCX/XLS/PPTX/이미지 OCR ([#2236](https://github.com/NousResearch/hermes-agent/pull/2236), [#2461](https://github.com/NousResearch/hermes-agent/pull/2461))
- **Huggingface-hub** 번들 스킬 ([#1921](https://github.com/NousResearch/hermes-agent/pull/1921))
- **Sherlock OSINT** 사용자명 검색 ([#1671](https://github.com/NousResearch/hermes-agent/pull/1671))
- **Meme-generation** — Pillow를 사용한 이미지 생성기 ([#2344](https://github.com/NousResearch/hermes-agent/pull/2344))
- **Bioinformatics** 게이트웨이 스킬 — 400개 이상의 생물 스킬 인덱스 ([#2387](https://github.com/NousResearch/hermes-agent/pull/2387))
- **Inference.sh** 스킬 (터미널 기반) ([#1686](https://github.com/NousResearch/hermes-agent/pull/1686))
- **Base blockchain** 선택적 스킬 ([#1643](https://github.com/NousResearch/hermes-agent/pull/1643))
- **3D-model-viewer** 선택적 스킬 ([#2226](https://github.com/NousResearch/hermes-agent/pull/2226))
- **FastMCP** 선택적 스킬 ([#2113](https://github.com/NousResearch/hermes-agent/pull/2113))
- **Hermes-agent-setup** 스킬 ([#1905](https://github.com/NousResearch/hermes-agent/pull/1905))

---

## 🔌 플러그인 시스템 개선

- **TUI 확장 훅** — Hermes 위에 커스텀 CLI 빌드 ([#2333](https://github.com/NousResearch/hermes-agent/pull/2333))
- **`hermes plugins install/remove/list`** 명령어 ([#2337](https://github.com/NousResearch/hermes-agent/pull/2337))
- 플러그인을 위한 **슬래시 명령어 등록** ([#2359](https://github.com/NousResearch/hermes-agent/pull/2359))
- **`session:end` 라이프사이클 이벤트** 훅 ([#1725](https://github.com/NousResearch/hermes-agent/pull/1725))
- 수정: 프로젝트 플러그인 탐색을 위한 옵트인 요구 ([#2215](https://github.com/NousResearch/hermes-agent/pull/2215))

---

## 🔒 보안 및 안정성

### 보안
- vision_tools 및 web_tools를 위한 **SSRF 보호** ([#2679](https://github.com/NousResearch/hermes-agent/pull/2679))
- `~user` 경로 접미사를 통한 `_expand_path`에서의 **셸 인젝션 방지** ([#2685](https://github.com/NousResearch/hermes-agent/pull/2685))
- **신뢰할 수 없는 브라우저 오리진** API 서버 접근 차단 ([#2451](https://github.com/NousResearch/hermes-agent/pull/2451))
- 서브프로세스 환경에서 **샌드박스 백엔드 인증 정보 차단** ([#1658](https://github.com/NousResearch/hermes-agent/pull/1658))
- 작업 공간 외부 시크릿 읽기를 위한 **@ 참조 차단** ([#2601](https://github.com/NousResearch/hermes-agent/pull/2601) by @Gutslabs)
- terminal_tool을 위한 **악성 코드 패턴 사전 실행 스캐너** ([#2245](https://github.com/NousResearch/hermes-agent/pull/2245))
- **터미널 안전성 강화** 및 샌드박스 파일 쓰기 ([#1653](https://github.com/NousResearch/hermes-agent/pull/1653))
- **PKCE 검증자 누출** 수정 + OAuth 갱신 Content-Type ([#1775](https://github.com/NousResearch/hermes-agent/pull/1775))
- `execute()` 호출에서 **SQL 문자열 포맷팅 제거** ([#2061](https://github.com/NousResearch/hermes-agent/pull/2061) by @dusterbloom)
- **작업 API 강화** — 입력 제한, 필드 화이트리스트, 시작 검사 ([#2456](https://github.com/NousResearch/hermes-agent/pull/2456))

### 안정성
- 4개 SessionDB 메서드에 스레드 잠금 ([#1704](https://github.com/NousResearch/hermes-agent/pull/1704))
- 동시 메모리 쓰기를 위한 파일 잠금 ([#1726](https://github.com/NousResearch/hermes-agent/pull/1726))
- OpenRouter 에러 우아하게 처리 ([#2112](https://github.com/NousResearch/hermes-agent/pull/2112))
- OSError에 대한 print() 호출 보호 ([#1668](https://github.com/NousResearch/hermes-agent/pull/1668))
- 수정 포맷터에서 비문자열 입력 안전하게 처리 ([#2392](https://github.com/NousResearch/hermes-agent/pull/2392), [#1700](https://github.com/NousResearch/hermes-agent/pull/1700))
- ACP: 모델 전환 시 세션 프로바이더 보존, 세션을 디스크에 영구 저장 ([#2380](https://github.com/NousResearch/hermes-agent/pull/2380), [#2071](https://github.com/NousResearch/hermes-agent/pull/2071))
- API 서버: 재시작 간 ResponseStore를 SQLite에 영구 저장 ([#2472](https://github.com/NousResearch/hermes-agent/pull/2472))
- 수정: `fetch_nous_models`가 위치 인수로 항상 TypeError 발생 ([#1699](https://github.com/NousResearch/hermes-agent/pull/1699))
- 수정: cli.py에서 병합 충돌 마커 해결로 인한 시작 실패 ([#2347](https://github.com/NousResearch/hermes-agent/pull/2347))
- 수정: wheel에서 `minisweagent_path.py` 누락 ([#2098](https://github.com/NousResearch/hermes-agent/pull/2098) by @JiwaniZakir)

### 크론 시스템
- **`[SILENT]` 응답** — 크론 에이전트가 전달을 억제할 수 있음 ([#1833](https://github.com/NousResearch/hermes-agent/pull/1833))
- 스케줄 빈도에 따라 **누락된 작업 유예 기간 조정** ([#2449](https://github.com/NousResearch/hermes-agent/pull/2449))
- **최근 일회성 작업 복구** ([#1918](https://github.com/NousResearch/hermes-agent/pull/1918))
- 수정: `repeat<=0`을 None으로 정규화 — LLM이 -1을 전달할 때 첫 실행 후 작업 삭제 ([#2612](https://github.com/NousResearch/hermes-agent/pull/2612) by @Mibayy)
- 수정: 스케줄러 전달 platform_map에 Matrix 추가 ([#2167](https://github.com/NousResearch/hermes-agent/pull/2167) by @buntingszn)
- 수정: 시간대 없는 naive ISO 타임스탬프 — 작업이 잘못된 시간에 실행 ([#1729](https://github.com/NousResearch/hermes-agent/pull/1729))
- 수정: `get_due_jobs`가 `jobs.json`을 두 번 읽음 — 레이스 컨디션 ([#1716](https://github.com/NousResearch/hermes-agent/pull/1716))
- 수정: 자동 작업이 전달 건너뛰기를 위해 빈 응답 반환 ([#2442](https://github.com/NousResearch/hermes-agent/pull/2442))
- 수정: 게이트웨이 세션 히스토리에 크론 출력 주입 중단 ([#2313](https://github.com/NousResearch/hermes-agent/pull/2313))
- 수정: `asyncio.run()`이 RuntimeError를 발생시킬 때 방치된 코루틴 닫기 ([#2317](https://github.com/NousResearch/hermes-agent/pull/2317))

---

## 🧪 테스트

- 모든 지속적으로 실패하는 테스트 해결 ([#2488](https://github.com/NousResearch/hermes-agent/pull/2488))
- Python 3.12 호환성을 위해 `FakePath`를 `monkeypatch`로 대체 ([#2444](https://github.com/NousResearch/hermes-agent/pull/2444))
- Hermes 설정 및 전체 스위트 기대 정렬 ([#1710](https://github.com/NousResearch/hermes-agent/pull/1710))

---

## 📚 문서

- 최근 기능에 대한 종합 문서 업데이트 ([#1693](https://github.com/NousResearch/hermes-agent/pull/1693), [#2183](https://github.com/NousResearch/hermes-agent/pull/2183))
- Alibaba Cloud 및 DingTalk 설정 가이드 ([#1687](https://github.com/NousResearch/hermes-agent/pull/1687), [#1692](https://github.com/NousResearch/hermes-agent/pull/1692))
- 상세한 스킬 문서 ([#2244](https://github.com/NousResearch/hermes-agent/pull/2244))
- Honcho 자체 호스팅 / Docker 설정 ([#2475](https://github.com/NousResearch/hermes-agent/pull/2475))
- 컨텍스트 길이 감지 FAQ 및 빠른 시작 참조 ([#2179](https://github.com/NousResearch/hermes-agent/pull/2179))
- 참조 및 사용자 가이드 전반의 문서 불일치 수정 ([#1995](https://github.com/NousResearch/hermes-agent/pull/1995))
- MCP 설치 명령어 수정 — bare pip 대신 uv 사용 ([#1909](https://github.com/NousResearch/hermes-agent/pull/1909))
- ASCII 다이어그램을 Mermaid/목록으로 대체 ([#2402](https://github.com/NousResearch/hermes-agent/pull/2402))
- Gemini OAuth 프로바이더 구현 계획 ([#2467](https://github.com/NousResearch/hermes-agent/pull/2467))
- Discord Server Members Intent가 필수로 표시 ([#2330](https://github.com/NousResearch/hermes-agent/pull/2330))
- api-server.md의 MDX 빌드 에러 수정 ([#1787](https://github.com/NousResearch/hermes-agent/pull/1787))
- 설치 프로그램과 일치하도록 venv 경로 정렬 ([#2114](https://github.com/NousResearch/hermes-agent/pull/2114))
- 허브 인덱스에 새로운 스킬 추가 ([#2281](https://github.com/NousResearch/hermes-agent/pull/2281))

---

## 👥 기여자

### 코어
- **@teknium1** (Teknium) — 280개 PR

### 커뮤니티 기여자
- **@mchzimm** (to_the_max) — GitHub Copilot 프로바이더 통합 ([#1879](https://github.com/NousResearch/hermes-agent/pull/1879))
- **@jquesnelle** (Jeffrey Quesnelle) — 스레드별 영구 이벤트 루프 수정 ([#2214](https://github.com/NousResearch/hermes-agent/pull/2214))
- **@llbn** (lbn) — Telegram MarkdownV2 취소선, 스포일러, 인용구, 이스케이프 수정 ([#2199](https://github.com/NousResearch/hermes-agent/pull/2199), [#2200](https://github.com/NousResearch/hermes-agent/pull/2200))
- **@dusterbloom** — SQL 인젝션 방지 + 로컬 서버 컨텍스트 윈도우 조회 ([#2061](https://github.com/NousResearch/hermes-agent/pull/2061), [#2091](https://github.com/NousResearch/hermes-agent/pull/2091))
- **@0xbyt4** — Anthropic tool_calls None 가드 + OpenCode-Go 프로바이더 설정 수정 ([#2209](https://github.com/NousResearch/hermes-agent/pull/2209), [#2393](https://github.com/NousResearch/hermes-agent/pull/2393))
- **@sai-samarth** (Saisamarth) — WhatsApp send_message 라우팅 + systemd node 경로 ([#1769](https://github.com/NousResearch/hermes-agent/pull/1769), [#1767](https://github.com/NousResearch/hermes-agent/pull/1767))
- **@Gutslabs** (Guts) — @ 참조의 시크릿 읽기 차단 ([#2601](https://github.com/NousResearch/hermes-agent/pull/2601))
- **@Mibayy** (Mibay) — 크론 작업 반복 정규화 ([#2612](https://github.com/NousResearch/hermes-agent/pull/2612))
- **@ten-jampa** (Tenzin Jampa) — 게이트웨이 /title 명령어 수정 ([#2379](https://github.com/NousResearch/hermes-agent/pull/2379))
- **@cutepawss** (lila) — 파일 도구 검색 페이지네이션 수정 ([#1824](https://github.com/NousResearch/hermes-agent/pull/1824))
- **@hanai** (Hanai) — OpenAI TTS base_url 지원 ([#2064](https://github.com/NousResearch/hermes-agent/pull/2064))
- **@rovle** (Lovre Pesut) — Daytona 샌드박스 API 마이그레이션 ([#2063](https://github.com/NousResearch/hermes-agent/pull/2063))
- **@buntingszn** (bunting szn) — Matrix 크론 전달 지원 ([#2167](https://github.com/NousResearch/hermes-agent/pull/2167))
- **@InB4DevOps** — 새 세션에서 토큰 카운터 리셋 ([#2101](https://github.com/NousResearch/hermes-agent/pull/2101))
- **@JiwaniZakir** (Zakir Jiwani) — wheel에서 누락된 파일 수정 ([#2098](https://github.com/NousResearch/hermes-agent/pull/2098))
- **@ygd58** (buray) — 위임 도구 부모 도구 이름 수정 ([#2083](https://github.com/NousResearch/hermes-agent/pull/2083))

---

**전체 변경 로그**: [v2026.3.17...v2026.3.23](https://github.com/NousResearch/hermes-agent/compare/v2026.3.17...v2026.3.23)
