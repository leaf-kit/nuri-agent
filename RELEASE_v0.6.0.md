# Hermes Agent v0.6.0 (v2026.3.30)

**출시일:** 2026년 3월 30일

> 다중 인스턴스 릴리스 — 격리된 에이전트 인스턴스 실행을 위한 프로필, MCP 서버 모드, Docker 컨테이너, 폴백 프로바이더 체인, 2개의 새 메시징 플랫폼(Feishu/Lark 및 WeCom), Telegram 웹훅 모드, Slack 다중 워크스페이스 OAuth, 2일간 95개의 PR과 16개의 해결된 이슈.

---

## ✨ 주요 변경사항

- **프로필 — 다중 인스턴스 Hermes** — 동일한 설치에서 여러 격리된 Hermes 인스턴스를 실행합니다. 각 프로필은 자체 설정, 메모리, 세션, 스킬, 게이트웨이 서비스를 갖습니다. `hermes profile create`로 생성하고, `hermes -p <name>`으로 전환하며, 공유를 위한 내보내기/가져오기를 지원합니다. 완전한 토큰 잠금 격리로 두 프로필이 동일한 봇 자격 증명을 사용하는 것을 방지합니다. ([#3681](https://github.com/NousResearch/hermes-agent/pull/3681))

- **MCP 서버 모드** — `hermes mcp serve`를 통해 MCP 호환 클라이언트(Claude Desktop, Cursor, VS Code 등)에 Hermes 대화 및 세션을 노출합니다. 대화 탐색, 메시지 읽기, 세션 간 검색, 첨부 파일 관리 등 모든 기능을 Model Context Protocol을 통해 수행합니다. stdio 및 Streamable HTTP 트랜스포트를 모두 지원합니다. ([#3795](https://github.com/NousResearch/hermes-agent/pull/3795))

- **Docker 컨테이너** — Hermes Agent를 컨테이너에서 실행하기 위한 공식 Dockerfile. 볼륨 마운트 설정으로 CLI 및 게이트웨이 모드를 모두 지원합니다. ([#3668](https://github.com/NousResearch/hermes-agent/pull/3668), closes [#850](https://github.com/NousResearch/hermes-agent/issues/850))

- **순서 기반 폴백 프로바이더 체인** — 자동 장애 조치를 갖춘 다중 추론 프로바이더를 설정합니다. 기본 프로바이더가 에러를 반환하거나 접근 불가능할 때 Hermes가 자동으로 체인의 다음 프로바이더를 시도합니다. config.yaml의 `fallback_providers`를 통해 설정합니다. ([#3813](https://github.com/NousResearch/hermes-agent/pull/3813), closes [#1734](https://github.com/NousResearch/hermes-agent/issues/1734))

- **Feishu/Lark 플랫폼 지원** — 이벤트 구독, 메시지 카드, 그룹 채팅, 이미지/파일 첨부, 인터랙티브 카드 콜백을 갖춘 Feishu(飞书) 및 Lark용 전체 게이트웨이 어댑터. ([#3799](https://github.com/NousResearch/hermes-agent/pull/3799), [#3817](https://github.com/NousResearch/hermes-agent/pull/3817), closes [#1788](https://github.com/NousResearch/hermes-agent/issues/1788))

- **WeCom(기업용 WeChat) 플랫폼 지원** — 텍스트/이미지/음성 메시지, 그룹 채팅, 콜백 검증을 갖춘 WeCom(企业微信)용 새로운 게이트웨이 어댑터. ([#3847](https://github.com/NousResearch/hermes-agent/pull/3847))

- **Slack 다중 워크스페이스 OAuth** — OAuth 토큰 파일을 통해 단일 Hermes 게이트웨이를 여러 Slack 워크스페이스에 연결합니다. 각 워크스페이스는 자체 봇 토큰을 가지며, 수신 이벤트별로 동적으로 해석됩니다. ([#3903](https://github.com/NousResearch/hermes-agent/pull/3903))

- **Telegram 웹훅 모드 및 그룹 제어** — 폴링의 대안으로 웹훅 모드에서 Telegram 어댑터를 실행합니다 — 리버스 프록시 뒤의 프로덕션 배포에 더 빠른 응답 시간과 더 나은 성능을 제공합니다. 봇이 응답하는 시점을 제어하는 새로운 그룹 멘션 게이팅: 항상, @멘션 시에만, 또는 정규식 트리거. ([#3880](https://github.com/NousResearch/hermes-agent/pull/3880), [#3870](https://github.com/NousResearch/hermes-agent/pull/3870))

- **Exa 검색 백엔드** — Firecrawl 및 DuckDuckGo와 함께 대체 웹 검색 및 콘텐츠 추출 백엔드로 Exa를 추가합니다. `EXA_API_KEY`를 설정하고 선호 백엔드로 구성합니다. ([#3648](https://github.com/NousResearch/hermes-agent/pull/3648))

- **원격 백엔드에서의 스킬 및 자격 증명** — Modal 및 Docker 컨테이너에 스킬 디렉토리와 자격 증명 파일을 마운트하여 원격 터미널 세션이 로컬 실행과 동일한 스킬 및 시크릿에 접근할 수 있습니다. ([#3890](https://github.com/NousResearch/hermes-agent/pull/3890), [#3671](https://github.com/NousResearch/hermes-agent/pull/3671), closes [#3665](https://github.com/NousResearch/hermes-agent/issues/3665), [#3433](https://github.com/NousResearch/hermes-agent/issues/3433))

---

## 🏗️ 코어 에이전트 및 아키텍처

### 프로바이더 및 모델 지원
- **순서 기반 폴백 프로바이더 체인** — 설정된 여러 프로바이더 간 자동 장애 조치 ([#3813](https://github.com/NousResearch/hermes-agent/pull/3813))
- **프로바이더 전환 시 api_mode 수정** — `hermes model`을 통한 프로바이더 전환이 이제 `chat_completions`를 하드코딩하는 대신 오래된 `api_mode`를 올바르게 지웁니다. Anthropic 호환 엔드포인트를 가진 프로바이더에서의 404 에러를 수정합니다 ([#3726](https://github.com/NousResearch/hermes-agent/pull/3726), [#3857](https://github.com/NousResearch/hermes-agent/pull/3857), closes [#3685](https://github.com/NousResearch/hermes-agent/issues/3685))
- **자동 OpenRouter 폴백 중지** — 프로바이더가 설정되지 않았을 때 조용히 OpenRouter로 라우팅하는 대신 명확한 에러를 발생시킵니다 ([#3807](https://github.com/NousResearch/hermes-agent/pull/3807), [#3862](https://github.com/NousResearch/hermes-agent/pull/3862))
- **Gemini 3.1 미리보기 모델** — OpenRouter 및 Nous Portal 카탈로그에 추가 ([#3803](https://github.com/NousResearch/hermes-agent/pull/3803), closes [#3753](https://github.com/NousResearch/hermes-agent/issues/3753))
- **Gemini 직접 API 컨텍스트 길이** — 직접 Google AI 엔드포인트에 대한 전체 컨텍스트 길이 해석 ([#3876](https://github.com/NousResearch/hermes-agent/pull/3876))
- Codex 폴백 카탈로그에 **gpt-5.4-mini** 추가 ([#3855](https://github.com/NousResearch/hermes-agent/pull/3855))
- 실시간 API 탐색이 더 적은 모델을 반환할 때 **선별된 모델 목록 우선 사용** ([#3856](https://github.com/NousResearch/hermes-agent/pull/3856), [#3867](https://github.com/NousResearch/hermes-agent/pull/3867))
- Retry-After 카운트다운이 포함된 **사용자 친화적인 429 속도 제한 메시지** ([#3809](https://github.com/NousResearch/hermes-agent/pull/3809))
- 인증이 필요 없는 로컬 서버용 **보조 클라이언트 플레이스홀더 키** ([#3842](https://github.com/NousResearch/hermes-agent/pull/3842))
- 보조 프로바이더 해석에 대한 **INFO 수준 로깅** ([#3866](https://github.com/NousResearch/hermes-agent/pull/3866))

### 에이전트 루프 및 대화
- **서브에이전트 상태 보고** — 요약이 존재할 때 일반 실패 대신 `completed` 상태 보고 ([#3829](https://github.com/NousResearch/hermes-agent/pull/3829))
- **압축 중 세션 로그 파일 업데이트** — 컨텍스트 압축 후 오래된 파일 참조 방지 ([#3835](https://github.com/NousResearch/hermes-agent/pull/3835))
- **비어있는 tools 파라미터 생략** — `None` 대신 비어있을 때 `tools` 파라미터를 전송하지 않아 엄격한 프로바이더와의 호환성 수정 ([#3820](https://github.com/NousResearch/hermes-agent/pull/3820))

### 프로필 및 다중 인스턴스
- **프로필 시스템** — `hermes profile create/list/switch/delete/export/import/rename`. 각 프로필은 격리된 HERMES_HOME, 게이트웨이 서비스, CLI 래퍼를 갖습니다. 토큰 잠금이 자격 증명 충돌을 방지합니다. 프로필 이름에 대한 탭 자동완성. ([#3681](https://github.com/NousResearch/hermes-agent/pull/3681))
- **프로필 인식 표시 경로** — 모든 사용자 대면 `~/.hermes` 경로를 `display_hermes_home()`으로 교체하여 올바른 프로필 디렉토리를 표시 ([#3623](https://github.com/NousResearch/hermes-agent/pull/3623))
- **지연 display_hermes_home 임포트** — 모듈이 오래된 바이트코드를 캐시할 때 `hermes update` 중 `ImportError` 방지 ([#3776](https://github.com/NousResearch/hermes-agent/pull/3776))
- **보호 경로에 HERMES_HOME 적용** — `.env` 쓰기 거부 경로가 이제 하드코딩된 `~/.hermes` 대신 HERMES_HOME을 존중 ([#3840](https://github.com/NousResearch/hermes-agent/pull/3840))

---

## 📱 메시징 플랫폼 (게이트웨이)

### 새로운 플랫폼
- **Feishu/Lark** — 이벤트 구독, 메시지 카드, 그룹 채팅, 이미지/파일 첨부, 인터랙티브 카드 콜백을 갖춘 전체 어댑터 ([#3799](https://github.com/NousResearch/hermes-agent/pull/3799), [#3817](https://github.com/NousResearch/hermes-agent/pull/3817))
- **WeCom(기업용 WeChat)** — 텍스트/이미지/음성 메시지, 그룹 채팅, 콜백 검증 ([#3847](https://github.com/NousResearch/hermes-agent/pull/3847))

### Telegram
- **웹훅 모드** — 프로덕션 배포를 위해 폴링 대신 웹훅 엔드포인트로 실행 ([#3880](https://github.com/NousResearch/hermes-agent/pull/3880))
- **그룹 멘션 게이팅 및 정규식 트리거** — 그룹에서의 봇 응답 동작 설정 가능: 항상, @멘션 시에만, 또는 정규식 매칭 ([#3870](https://github.com/NousResearch/hermes-agent/pull/3870))
- **삭제된 답장 대상을 정상적으로 처리** — 답장 대상 메시지가 삭제되었을 때 더 이상 충돌하지 않음 ([#3858](https://github.com/NousResearch/hermes-agent/pull/3858), closes [#3229](https://github.com/NousResearch/hermes-agent/issues/3229))

### Discord
- **메시지 처리 리액션** — 처리 중에 리액션 이모지를 추가하고 완료 시 제거하여 채널에서 시각적 피드백 제공 ([#3871](https://github.com/NousResearch/hermes-agent/pull/3871))
- **DISCORD_IGNORE_NO_MENTION** — 다른 사용자/봇을 @멘션하지만 Hermes는 아닌 메시지 건너뛰기 ([#3640](https://github.com/NousResearch/hermes-agent/pull/3640))
- **지연된 "thinking..." 정리** — 슬래시 명령 완료 후 "thinking..." 표시기를 올바르게 제거 ([#3674](https://github.com/NousResearch/hermes-agent/pull/3674), closes [#3595](https://github.com/NousResearch/hermes-agent/issues/3595))

### Slack
- **다중 워크스페이스 OAuth** — OAuth 토큰 파일을 통해 단일 게이트웨이에서 여러 Slack 워크스페이스에 연결 ([#3903](https://github.com/NousResearch/hermes-agent/pull/3903))

### WhatsApp
- **영구 aiohttp 세션** — 메시지당 새 세션을 생성하는 대신 요청 간 HTTP 세션 재사용 ([#3818](https://github.com/NousResearch/hermes-agent/pull/3818))
- **LID↔전화번호 별칭 해석** — 허용 목록에서 Linked ID와 전화번호 형식을 올바르게 매칭 ([#3830](https://github.com/NousResearch/hermes-agent/pull/3830))
- **봇 모드에서 답장 접두사 건너뛰기** — WhatsApp 봇으로 실행할 때 더 깔끔한 메시지 포맷 ([#3931](https://github.com/NousResearch/hermes-agent/pull/3931))

### Matrix
- **MSC3245를 통한 네이티브 음성 메시지** — 파일 첨부 대신 적절한 Matrix 음성 이벤트로 음성 메시지 전송 ([#3877](https://github.com/NousResearch/hermes-agent/pull/3877))

### Mattermost
- **설정 가능한 멘션 동작** — @멘션 없이도 메시지에 응답 ([#3664](https://github.com/NousResearch/hermes-agent/pull/3664))

### Signal
- **전화번호 URL 인코딩** 및 올바른 첨부 RPC 파라미터 — 특정 전화번호 형식에서의 전송 실패 수정 ([#3670](https://github.com/NousResearch/hermes-agent/pull/3670)) — @kshitijk4poor

### Email
- **실패 시 SMTP/IMAP 연결 닫기** — 에러 시나리오에서 연결 누수 방지 ([#3804](https://github.com/NousResearch/hermes-agent/pull/3804))

### 게이트웨이 코어
- **원자적 설정 쓰기** — 충돌 시 데이터 손실을 방지하기 위해 config.yaml에 원자적 파일 쓰기 사용 ([#3800](https://github.com/NousResearch/hermes-agent/pull/3800))
- **홈 채널 환경 변수 재정의** — 홈 채널에 대한 환경 변수 재정의를 일관되게 적용 ([#3796](https://github.com/NousResearch/hermes-agent/pull/3796), [#3808](https://github.com/NousResearch/hermes-agent/pull/3808))
- **print()를 logger로 교체** — BasePlatformAdapter가 이제 print문 대신 적절한 로깅 사용 ([#3669](https://github.com/NousResearch/hermes-agent/pull/3669))
- **Cron 전달 라벨** — 채널 디렉토리를 통한 사용자 친화적 전달 라벨 해석 ([#3860](https://github.com/NousResearch/hermes-agent/pull/3860), closes [#1945](https://github.com/NousResearch/hermes-agent/issues/1945))
- **Cron [SILENT] 강화** — 에이전트가 전달을 억제하기 위해 보고서에 [SILENT]를 접두사로 붙이는 것을 방지 ([#3901](https://github.com/NousResearch/hermes-agent/pull/3901))
- **백그라운드 태스크 미디어 전달** 및 비전 다운로드 타임아웃 수정 ([#3919](https://github.com/NousResearch/hermes-agent/pull/3919))
- **Boot-md 훅** — 게이트웨이 시작 시 BOOT.md 파일을 실행하는 예제 내장 훅 ([#3733](https://github.com/NousResearch/hermes-agent/pull/3733))

---

## 🖥️ CLI 및 사용자 경험

### 대화형 CLI
- **설정 가능한 도구 미리보기 길이** — 40자로 잘리는 대신 기본적으로 전체 파일 경로 표시 ([#3841](https://github.com/NousResearch/hermes-agent/pull/3841))
- **도구 토큰 컨텍스트 표시** — `hermes tools` 체크리스트가 이제 도구세트별 예상 토큰 비용 표시 ([#3805](https://github.com/NousResearch/hermes-agent/pull/3805))
- **/bg 스피너 TUI 수정** — 상태 바 충돌을 방지하기 위해 백그라운드 태스크 스피너를 TUI 위젯을 통해 라우팅 ([#3643](https://github.com/NousResearch/hermes-agent/pull/3643))
- **상태 바 줄바꿈으로 인한 중복 행 방지** ([#3883](https://github.com/NousResearch/hermes-agent/pull/3883)) — @kshitijk4poor
- **닫힌 stdout ValueError 처리** — 게이트웨이 스레드 종료 중 stdout이 닫혔을 때 충돌 수정 ([#3843](https://github.com/NousResearch/hermes-agent/pull/3843), closes [#3534](https://github.com/NousResearch/hermes-agent/issues/3534))
- **/tools disable에서 input() 제거** — 도구 비활성화 시 터미널 프리징 제거 ([#3918](https://github.com/NousResearch/hermes-agent/pull/3918))
- **대화형 CLI 명령에 대한 TTY 가드** — 터미널 없이 시작했을 때 CPU 스핀 방지 ([#3933](https://github.com/NousResearch/hermes-agent/pull/3933))
- **Argparse 진입점** — 더 깔끔한 에러 처리를 위해 최상위 런처에서 argparse 사용 ([#3874](https://github.com/NousResearch/hermes-agent/pull/3874))
- **지연 초기화된 도구가 배너에서 빨간색 대신 노란색으로 표시** — "누락된" 도구에 대한 잘못된 경보 감소 ([#3822](https://github.com/NousResearch/hermes-agent/pull/3822))
- 설정 시 배너에 **Honcho 도구 표시** ([#3810](https://github.com/NousResearch/hermes-agent/pull/3810))

### 설정 및 구성
- Matrix 선택 시 `hermes setup` 중 **matrix-nio 자동 설치** ([#3802](https://github.com/NousResearch/hermes-agent/pull/3802), [#3873](https://github.com/NousResearch/hermes-agent/pull/3873))
- **세션 내보내기 stdout 지원** — 파이핑을 위해 `-`로 세션을 stdout으로 내보내기 ([#3641](https://github.com/NousResearch/hermes-agent/pull/3641), closes [#3609](https://github.com/NousResearch/hermes-agent/issues/3609))
- **설정 가능한 승인 타임아웃** — 위험한 명령 승인 프롬프트가 자동 거부 전 대기하는 시간 설정 ([#3886](https://github.com/NousResearch/hermes-agent/pull/3886), closes [#3765](https://github.com/NousResearch/hermes-agent/issues/3765))
- **업데이트 시 __pycache__ 삭제** — `hermes update` 후 오래된 바이트코드 ImportError 방지 ([#3819](https://github.com/NousResearch/hermes-agent/pull/3819))

---

## 🔧 도구 시스템

### MCP
- **MCP 서버 모드** — `hermes mcp serve`가 stdio 또는 Streamable HTTP를 통해 MCP 클라이언트에 대화, 세션, 첨부 파일을 노출 ([#3795](https://github.com/NousResearch/hermes-agent/pull/3795))
- **동적 도구 발견** — `notifications/tools/list_changed` 이벤트에 응답하여 재연결 없이 MCP 서버에서 새 도구를 가져옴 ([#3812](https://github.com/NousResearch/hermes-agent/pull/3812))
- **비폐기 HTTP 트랜스포트** — `sse_client`에서 `streamable_http_client`로 전환 ([#3646](https://github.com/NousResearch/hermes-agent/pull/3646))

### 웹 도구
- **Exa 검색 백엔드** — 웹 검색 및 추출을 위한 Firecrawl과 DuckDuckGo의 대안 ([#3648](https://github.com/NousResearch/hermes-agent/pull/3648))

### 브라우저
- 브라우저 스냅샷 및 비전 도구에서 **None LLM 응답에 대한 보호** ([#3642](https://github.com/NousResearch/hermes-agent/pull/3642))

### 터미널 및 원격 백엔드
- Modal 및 Docker 컨테이너에 **스킬 디렉토리 마운트** ([#3890](https://github.com/NousResearch/hermes-agent/pull/3890))
- mtime+size 캐싱으로 원격 백엔드에 **자격 증명 파일 마운트** ([#3671](https://github.com/NousResearch/hermes-agent/pull/3671))
- 명령 타임아웃 시 모든 것을 잃는 대신 **부분 출력 보존** ([#3868](https://github.com/NousResearch/hermes-agent/pull/3868))
- 원격 백엔드에서 **지속된 환경 변수를 누락으로 표시하지 않음** ([#3650](https://github.com/NousResearch/hermes-agent/pull/3650))

### 오디오
- 트랜스크립션 도구에서 **.aac 형식 지원** ([#3865](https://github.com/NousResearch/hermes-agent/pull/3865), closes [#1963](https://github.com/NousResearch/hermes-agent/issues/1963))
- **오디오 다운로드 재시도** — 기존 이미지 다운로드 패턴과 일치하는 `cache_audio_from_url` 재시도 로직 ([#3401](https://github.com/NousResearch/hermes-agent/pull/3401)) — @binhnt92

### 비전
- **비이미지 파일 거부** 및 비전 분석에 대한 웹사이트 전용 정책 시행 ([#3845](https://github.com/NousResearch/hermes-agent/pull/3845))

### 도구 스키마
- 도구 정의에서 **name 필드 보장** — `KeyError: 'name'` 충돌 수정 ([#3811](https://github.com/NousResearch/hermes-agent/pull/3811), closes [#3729](https://github.com/NousResearch/hermes-agent/issues/3729))

### ACP (에디터 통합)
- VS Code/Zed/JetBrains 클라이언트용 **완전한 세션 관리 인터페이스** — 적절한 태스크 라이프사이클, 취소 지원, 세션 지속성 ([#3675](https://github.com/NousResearch/hermes-agent/pull/3675))

---

## 🧩 스킬 및 플러그인

### 스킬 시스템
- **외부 스킬 디렉토리** — config.yaml의 `skills.external_dirs`를 통해 추가 스킬 디렉토리 설정 ([#3678](https://github.com/NousResearch/hermes-agent/pull/3678))
- **카테고리 경로 순회 차단** — 스킬 카테고리 이름에서 `../` 공격 방지 ([#3844](https://github.com/NousResearch/hermes-agent/pull/3844))
- **parallel-cli를 optional-skills로 이동** — 기본 스킬 규모 축소 ([#3673](https://github.com/NousResearch/hermes-agent/pull/3673)) — @kshitijk4poor

### 새로운 스킬
- **memento-flashcards** — 간격 반복 플래시카드 시스템 ([#3827](https://github.com/NousResearch/hermes-agent/pull/3827))
- **songwriting-and-ai-music** — 작곡 기술 및 AI 음악 생성 프롬프트 ([#3834](https://github.com/NousResearch/hermes-agent/pull/3834))
- **SiYuan Note** — SiYuan 노트 앱과의 통합 ([#3742](https://github.com/NousResearch/hermes-agent/pull/3742))
- **Scrapling** — Scrapling 라이브러리를 사용한 웹 스크래핑 스킬 ([#3742](https://github.com/NousResearch/hermes-agent/pull/3742))
- **one-three-one-rule** — 커뮤니케이션 프레임워크 스킬 ([#3797](https://github.com/NousResearch/hermes-agent/pull/3797))

### 플러그인 시스템
- **플러그인 활성화/비활성화 명령** — 플러그인을 제거하지 않고 상태를 관리하는 `hermes plugins enable/disable <name>` ([#3747](https://github.com/NousResearch/hermes-agent/pull/3747))
- **플러그인 메시지 주입** — 플러그인이 이제 `ctx.inject_message()`를 통해 사용자를 대신하여 대화 스트림에 메시지를 주입 가능 ([#3778](https://github.com/NousResearch/hermes-agent/pull/3778)) — @winglian
- **Honcho 자체 호스팅 지원** — API 키 없이 로컬 Honcho 인스턴스 허용 ([#3644](https://github.com/NousResearch/hermes-agent/pull/3644))

---

## 🔒 보안 및 안정성

### 보안 강화
- **강화된 위험 명령 감지** — 위험한 셸 명령에 대한 패턴 매칭 확장 및 민감한 위치(`/etc/`, `/boot/`, docker.sock)에 대한 파일 도구 경로 보호 추가 ([#3872](https://github.com/NousResearch/hermes-agent/pull/3872))
- **승인 시스템의 민감한 경로 쓰기 검사** — 터미널뿐만 아니라 파일 도구를 통한 시스템 설정 파일 쓰기 감지 ([#3859](https://github.com/NousResearch/hermes-agent/pull/3859))
- **시크릿 편집 확장** — 이제 ElevenLabs, Tavily, Exa API 키도 포함 ([#3920](https://github.com/NousResearch/hermes-agent/pull/3920))
- **비전 파일 거부** — 정보 유출을 방지하기 위해 비전 분석에 전달된 비이미지 파일 거부 ([#3845](https://github.com/NousResearch/hermes-agent/pull/3845))
- **카테고리 경로 순회 차단** — 스킬 카테고리 이름에서 디렉토리 순회 방지 ([#3844](https://github.com/NousResearch/hermes-agent/pull/3844))

### 안정성
- **원자적 config.yaml 쓰기** — 게이트웨이 충돌 시 데이터 손실 방지 ([#3800](https://github.com/NousResearch/hermes-agent/pull/3800))
- **업데이트 시 __pycache__ 삭제** — 업데이트 후 오래된 바이트코드로 인한 ImportError 방지 ([#3819](https://github.com/NousResearch/hermes-agent/pull/3819))
- **업데이트 안전을 위한 지연 임포트** — 모듈이 새 함수를 참조할 때 `hermes update` 중 ImportError 체인 방지 ([#3776](https://github.com/NousResearch/hermes-agent/pull/3776))
- **패치 손상에서 terminalbench2 복원** — 패치 도구의 시크릿 편집으로 손상된 파일 복구 ([#3801](https://github.com/NousResearch/hermes-agent/pull/3801))
- **터미널 타임아웃 시 부분 출력 보존** — 더 이상 타임아웃 시 명령 출력이 손실되지 않음 ([#3868](https://github.com/NousResearch/hermes-agent/pull/3868))

---

## 🐛 주요 버그 수정

- **OpenClaw 마이그레이션 모델 설정 덮어쓰기** — 마이그레이션이 더 이상 모델 설정 딕셔너리를 문자열로 덮어쓰지 않음 ([#3924](https://github.com/NousResearch/hermes-agent/pull/3924)) — @0xbyt4
- **OpenClaw 마이그레이션 확장** — 세션, cron, 메모리를 포함한 전체 데이터 범위 포함 ([#3869](https://github.com/NousResearch/hermes-agent/pull/3869))
- **Telegram 삭제된 답장 대상** — 삭제된 메시지에 대한 답장을 충돌 없이 정상적으로 처리 ([#3858](https://github.com/NousResearch/hermes-agent/pull/3858))
- **Discord "thinking..." 지속** — 지연된 응답 표시기를 올바르게 정리 ([#3674](https://github.com/NousResearch/hermes-agent/pull/3674))
- **WhatsApp LID↔전화번호 별칭** — Linked ID 형식과의 허용 목록 매칭 실패 수정 ([#3830](https://github.com/NousResearch/hermes-agent/pull/3830))
- **Signal URL 인코딩된 전화번호** — 특정 형식에서의 전송 실패 수정 ([#3670](https://github.com/NousResearch/hermes-agent/pull/3670))
- **Email 연결 누수** — 에러 시 SMTP/IMAP 연결을 올바르게 닫음 ([#3804](https://github.com/NousResearch/hermes-agent/pull/3804))
- **_safe_print ValueError** — 닫힌 stdout에서 더 이상 게이트웨이 스레드 충돌 없음 ([#3843](https://github.com/NousResearch/hermes-agent/pull/3843))
- **도구 스키마 KeyError 'name'** — 도구 정의에서 name 필드가 항상 존재하도록 보장 ([#3811](https://github.com/NousResearch/hermes-agent/pull/3811))
- **프로바이더 전환 시 api_mode 오래됨** — `hermes model`을 통한 프로바이더 전환 시 올바르게 지움 ([#3857](https://github.com/NousResearch/hermes-agent/pull/3857))

---

## 🧪 테스트

- 훅, tiktoken, 플러그인, 스킬 테스트 전반에 걸쳐 10개 이상의 CI 실패 해결 ([#3848](https://github.com/NousResearch/hermes-agent/pull/3848), [#3721](https://github.com/NousResearch/hermes-agent/pull/3721), [#3936](https://github.com/NousResearch/hermes-agent/pull/3936))

---

## 📚 문서

- **포괄적인 OpenClaw 마이그레이션 가이드** — OpenClaw/Claw3D에서 Hermes Agent로 마이그레이션하기 위한 단계별 가이드 ([#3864](https://github.com/NousResearch/hermes-agent/pull/3864), [#3900](https://github.com/NousResearch/hermes-agent/pull/3900))
- **자격 증명 파일 전달 문서** — 원격 백엔드에 자격 증명 파일 및 환경 변수를 전달하는 방법 문서화 ([#3677](https://github.com/NousResearch/hermes-agent/pull/3677))
- **DuckDuckGo 요구사항 명확화** — duckduckgo-search 패키지에 대한 런타임 의존성 명시 ([#3680](https://github.com/NousResearch/hermes-agent/pull/3680))
- **스킬 카탈로그 업데이트** — 레드팀 카테고리 및 선택적 스킬 목록 추가 ([#3745](https://github.com/NousResearch/hermes-agent/pull/3745))
- **Feishu 문서 MDX 수정** — Docusaurus 빌드를 깨뜨리는 꺾쇠 괄호 URL 이스케이프 ([#3902](https://github.com/NousResearch/hermes-agent/pull/3902))

---

## 👥 기여자

### 코어
- **@teknium1** — 모든 하위 시스템에 걸친 90개의 PR

### 커뮤니티 기여자
- **@kshitijk4poor** — 3개의 PR: Signal 전화번호 수정 ([#3670](https://github.com/NousResearch/hermes-agent/pull/3670)), parallel-cli를 optional-skills로 이동 ([#3673](https://github.com/NousResearch/hermes-agent/pull/3673)), 상태 바 줄바꿈 수정 ([#3883](https://github.com/NousResearch/hermes-agent/pull/3883))
- **@winglian** — 1개의 PR: 플러그인 메시지 주입 인터페이스 ([#3778](https://github.com/NousResearch/hermes-agent/pull/3778))
- **@binhnt92** — 1개의 PR: 오디오 다운로드 재시도 로직 ([#3401](https://github.com/NousResearch/hermes-agent/pull/3401))
- **@0xbyt4** — 1개의 PR: OpenClaw 마이그레이션 모델 설정 수정 ([#3924](https://github.com/NousResearch/hermes-agent/pull/3924))

### 커뮤니티에서 해결된 이슈
@Material-Scientist ([#850](https://github.com/NousResearch/hermes-agent/issues/850)), @hanxu98121 ([#1734](https://github.com/NousResearch/hermes-agent/issues/1734)), @penwyp ([#1788](https://github.com/NousResearch/hermes-agent/issues/1788)), @dan-and ([#1945](https://github.com/NousResearch/hermes-agent/issues/1945)), @AdrianScott ([#1963](https://github.com/NousResearch/hermes-agent/issues/1963)), @clawdbot47 ([#3229](https://github.com/NousResearch/hermes-agent/issues/3229)), @alanfwilliams ([#3404](https://github.com/NousResearch/hermes-agent/issues/3404)), @kentimsit ([#3433](https://github.com/NousResearch/hermes-agent/issues/3433)), @hayka-pacha ([#3534](https://github.com/NousResearch/hermes-agent/issues/3534)), @primmer ([#3595](https://github.com/NousResearch/hermes-agent/issues/3595)), @dagelf ([#3609](https://github.com/NousResearch/hermes-agent/issues/3609)), @HenkDz ([#3685](https://github.com/NousResearch/hermes-agent/issues/3685)), @tmdgusya ([#3729](https://github.com/NousResearch/hermes-agent/issues/3729)), @TypQxQ ([#3753](https://github.com/NousResearch/hermes-agent/issues/3753)), @acsezen ([#3765](https://github.com/NousResearch/hermes-agent/issues/3765))

---

**전체 변경 로그**: [v2026.3.28...v2026.3.30](https://github.com/NousResearch/hermes-agent/compare/v2026.3.28...v2026.3.30)
