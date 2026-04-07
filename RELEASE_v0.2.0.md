# Hermes Agent v0.2.0 (v2026.3.12)

**릴리스 날짜:** 2026년 3월 12일

> v0.1.0(초기 비공개 기반) 이후 첫 번째 태그 릴리스입니다. 단 2주 만에 Hermes Agent는 소규모 내부 프로젝트에서 완전한 기능을 갖춘 AI 에이전트 플랫폼으로 성장했습니다 — 커뮤니티의 폭발적인 기여 덕분입니다. 이번 릴리스는 **63명의 기여자**가 참여한 **216개의 병합된 풀 리퀘스트**를 포함하며, **119개의 이슈**를 해결했습니다.

---

## ✨ 주요 하이라이트

- **멀티 플랫폼 메시징 게이트웨이** — Telegram, Discord, Slack, WhatsApp, Signal, Email (IMAP/SMTP), Home Assistant 플랫폼을 통합 세션 관리, 미디어 첨부, 플랫폼별 도구 설정과 함께 지원합니다.

- **MCP (Model Context Protocol) 클라이언트** — stdio 및 HTTP 전송 방식, 재연결, 리소스/프롬프트 탐색, 샘플링(서버 주도 LLM 요청)을 갖춘 네이티브 MCP 지원. ([#291](https://github.com/NousResearch/hermes-agent/pull/291) — @0xbyt4, [#301](https://github.com/NousResearch/hermes-agent/pull/301), [#753](https://github.com/NousResearch/hermes-agent/pull/753))

- **스킬 생태계** — 15개 이상의 카테고리에 걸쳐 70개 이상의 번들 및 선택적 스킬, 커뮤니티 탐색을 위한 Skills Hub, 플랫폼별 활성화/비활성화, 도구 가용성 기반 조건부 활성화, 전제조건 검증 기능. ([#743](https://github.com/NousResearch/hermes-agent/pull/743) — @teyrebaz33, [#785](https://github.com/NousResearch/hermes-agent/pull/785) — @teyrebaz33)

- **중앙집중식 프로바이더 라우터** — 분산된 프로바이더 로직을 비전, 요약, 압축, 트라젝토리 저장 전반에 걸쳐 통합한 `call_llm()`/`async_call_llm()` API. 모든 보조 소비자가 자동 인증 정보 해석과 함께 단일 코드 경로를 통해 라우팅됩니다. ([#1003](https://github.com/NousResearch/hermes-agent/pull/1003))

- **ACP 서버** — Agent Communication Protocol 표준을 통한 VS Code, Zed, JetBrains 에디터 통합. ([#949](https://github.com/NousResearch/hermes-agent/pull/949))

- **CLI 스킨/테마 엔진** — 데이터 기반 시각적 커스터마이징: 배너, 스피너, 색상, 브랜딩. 7개의 내장 스킨 + 커스텀 YAML 스킨.

- **Git Worktree 격리** — `hermes -w`로 동일 저장소에서 안전한 병렬 작업을 위한 격리된 에이전트 세션을 실행합니다. ([#654](https://github.com/NousResearch/hermes-agent/pull/654))

- **파일시스템 체크포인트 및 롤백** — 파괴적 작업 전 자동 스냅샷과 `/rollback`을 통한 복원. ([#824](https://github.com/NousResearch/hermes-agent/pull/824))

- **3,289개의 테스트** — 거의 제로 수준의 테스트 커버리지에서 에이전트, 게이트웨이, 도구, 크론, CLI를 포괄하는 종합 테스트 스위트로 성장.

---

## 🏗️ 코어 에이전트 및 아키텍처

### 프로바이더 및 모델 지원
- `resolve_provider_client()` + `call_llm()` API를 갖춘 중앙집중식 프로바이더 라우터 ([#1003](https://github.com/NousResearch/hermes-agent/pull/1003))
- 설정에서 Nous Portal을 일급 프로바이더로 지원 ([#644](https://github.com/NousResearch/hermes-agent/issues/644))
- ChatGPT 구독 지원을 포함한 OpenAI Codex (Responses API) ([#43](https://github.com/NousResearch/hermes-agent/pull/43)) — @grp06
- Codex OAuth 비전 지원 + 멀티모달 콘텐츠 어댑터
- 하드코딩된 목록 대신 라이브 API를 통한 `/model` 검증
- 자체 호스팅 Firecrawl 지원 ([#460](https://github.com/NousResearch/hermes-agent/pull/460)) — @caentzminger
- Kimi Code API 지원 ([#635](https://github.com/NousResearch/hermes-agent/pull/635)) — @christomitov
- MiniMax 모델 ID 업데이트 ([#473](https://github.com/NousResearch/hermes-agent/pull/473)) — @tars90percent
- OpenRouter 프로바이더 라우팅 설정 (provider_preferences)
- 401 에러 시 Nous 인증 정보 갱신 ([#571](https://github.com/NousResearch/hermes-agent/pull/571), [#269](https://github.com/NousResearch/hermes-agent/pull/269)) — @rewbs
- z.ai/GLM, Kimi/Moonshot, MiniMax, Azure OpenAI를 일급 프로바이더로 지원
- `/model`과 `/provider`를 단일 뷰로 통합

### 에이전트 루프 및 대화
- 프로바이더 복원력을 위한 간단한 폴백 모델 ([#740](https://github.com/NousResearch/hermes-agent/pull/740))
- 부모 + 서브에이전트 위임 간 공유 반복 예산
- 도구 결과 주입을 통한 반복 예산 압력
- 전체 인증 정보 해석이 가능한 설정 가능한 서브에이전트 프로바이더/모델
- 중단 대신 압축을 통한 413 payload-too-large 처리 ([#153](https://github.com/NousResearch/hermes-agent/pull/153)) — @tekelala
- 압축 후 재구성된 페이로드로 재시도 ([#616](https://github.com/NousResearch/hermes-agent/pull/616)) — @tripledoublev
- 병적으로 큰 게이트웨이 세션 자동 압축 ([#628](https://github.com/NousResearch/hermes-agent/issues/628))
- 도구 호출 복구 미들웨어 — 자동 소문자 변환 및 잘못된 도구 핸들러
- 추론 노력 설정 및 `/reasoning` 명령어 ([#921](https://github.com/NousResearch/hermes-agent/pull/921))
- 컨텍스트 압축 후 파일 재읽기/검색 루프 감지 및 차단 ([#705](https://github.com/NousResearch/hermes-agent/pull/705)) — @0xbyt4

### 세션 및 메모리
- 고유 제목, 자동 계보, 풍부한 목록, 이름으로 재개를 지원하는 세션 명명 ([#720](https://github.com/NousResearch/hermes-agent/pull/720))
- 검색 필터링이 가능한 대화형 세션 브라우저 ([#733](https://github.com/NousResearch/hermes-agent/pull/733))
- 세션 재개 시 이전 메시지 표시 ([#734](https://github.com/NousResearch/hermes-agent/pull/734))
- Honcho AI 네이티브 교차 세션 사용자 모델링 ([#38](https://github.com/NousResearch/hermes-agent/pull/38)) — @erosika
- 세션 만료 시 능동적 비동기 메모리 플러시
- 영구 캐싱 + 배너 표시를 갖춘 스마트 컨텍스트 길이 탐색
- 게이트웨이에서 명명된 세션으로 전환하는 `/resume` 명령어
- 메시징 플랫폼을 위한 세션 재설정 정책

---

## 📱 메시징 플랫폼 (게이트웨이)

### Telegram
- 네이티브 파일 첨부: send_document + send_video
- PDF, 텍스트, Office 파일을 위한 문서 파일 처리 — @tekelala
- 포럼 토픽 세션 격리 ([#766](https://github.com/NousResearch/hermes-agent/pull/766)) — @spanishflu-est1918
- MEDIA: 프로토콜을 통한 브라우저 스크린샷 공유 ([#657](https://github.com/NousResearch/hermes-agent/pull/657))
- find-nearby 스킬을 위한 위치 지원
- TTS 음성 메시지 누적 수정 ([#176](https://github.com/NousResearch/hermes-agent/pull/176)) — @Bartok9
- 에러 처리 및 로깅 개선 ([#763](https://github.com/NousResearch/hermes-agent/pull/763)) — @aydnOktay
- 이탤릭 정규식 줄바꿈 수정 + 43개 포맷 테스트 ([#204](https://github.com/NousResearch/hermes-agent/pull/204)) — @0xbyt4

### Discord
- 세션 컨텍스트에 채널 토픽 포함 ([#248](https://github.com/NousResearch/hermes-agent/pull/248)) — @Bartok9
- 봇 메시지 필터링을 위한 DISCORD_ALLOW_BOTS 설정 ([#758](https://github.com/NousResearch/hermes-agent/pull/758))
- 문서 및 비디오 지원 ([#784](https://github.com/NousResearch/hermes-agent/pull/784))
- 에러 처리 및 로깅 개선 ([#761](https://github.com/NousResearch/hermes-agent/pull/761)) — @aydnOktay

### Slack
- App_mention 404 수정 + 문서/비디오 지원 ([#784](https://github.com/NousResearch/hermes-agent/pull/784))
- print 문을 대체하는 구조화된 로깅 — @aydnOktay

### WhatsApp
- 네이티브 미디어 전송 — 이미지, 비디오, 문서 ([#292](https://github.com/NousResearch/hermes-agent/pull/292)) — @satelerd
- 다중 사용자 세션 격리 ([#75](https://github.com/NousResearch/hermes-agent/pull/75)) — @satelerd
- Linux 전용 fuser를 대체하는 크로스 플랫폼 포트 정리 ([#433](https://github.com/NousResearch/hermes-agent/pull/433)) — @Farukest
- DM 인터럽트 키 불일치 수정 ([#350](https://github.com/NousResearch/hermes-agent/pull/350)) — @Farukest

### Signal
- signal-cli-rest-api를 통한 완전한 Signal 메신저 게이트웨이 ([#405](https://github.com/NousResearch/hermes-agent/issues/405))
- 메시지 이벤트에서의 미디어 URL 지원 ([#871](https://github.com/NousResearch/hermes-agent/pull/871))

### Email (IMAP/SMTP)
- 새로운 이메일 게이트웨이 플랫폼 — @0xbyt4

### Home Assistant
- REST 도구 + WebSocket 게이트웨이 통합 ([#184](https://github.com/NousResearch/hermes-agent/pull/184)) — @0xbyt4
- 서비스 탐색 및 향상된 설정
- 도구셋 매핑 수정 ([#538](https://github.com/NousResearch/hermes-agent/pull/538)) — @Himess

### 게이트웨이 코어
- 사용자에게 서브에이전트 도구 호출 및 사고 과정 노출 ([#186](https://github.com/NousResearch/hermes-agent/pull/186)) — @cutepawss
- 설정 가능한 백그라운드 프로세스 감시자 알림 ([#840](https://github.com/NousResearch/hermes-agent/pull/840))
- 폴백 기능이 있는 Telegram/Discord/Slack용 `edit_message()`
- `/compress`, `/usage`, `/update` 슬래시 명령어
- 게이트웨이 세션에서 3배 SQLite 메시지 중복 제거 ([#873](https://github.com/NousResearch/hermes-agent/pull/873))
- 캐시 히트를 위한 게이트웨이 턴 간 시스템 프롬프트 안정화 ([#754](https://github.com/NousResearch/hermes-agent/pull/754))
- 게이트웨이 종료 시 MCP 서버 종료 ([#796](https://github.com/NousResearch/hermes-agent/pull/796)) — @0xbyt4
- session_search 에러를 수정하기 위해 AIAgent에 session_db 전달 ([#108](https://github.com/NousResearch/hermes-agent/pull/108)) — @Bartok9
- /retry, /undo에서 트랜스크립트 변경 사항 유지; /reset 속성 수정 ([#217](https://github.com/NousResearch/hermes-agent/pull/217)) — @Farukest
- Windows 충돌을 방지하는 UTF-8 인코딩 수정 ([#369](https://github.com/NousResearch/hermes-agent/pull/369)) — @ch3ronsa

---

## 🖥️ CLI 및 사용자 경험

### 대화형 CLI
- 데이터 기반 스킨/테마 엔진 — 7개의 내장 스킨 (default, ares, mono, slate, poseidon, sisyphus, charizard) + 커스텀 YAML 스킨
- 커스텀 성격 + 비활성화 지원이 있는 `/personality` 명령어 ([#773](https://github.com/NousResearch/hermes-agent/pull/773)) — @teyrebaz33
- 에이전트 루프를 우회하는 사용자 정의 빠른 명령어 ([#746](https://github.com/NousResearch/hermes-agent/pull/746)) — @teyrebaz33
- 노력 수준 및 표시 토글을 위한 `/reasoning` 명령어 ([#921](https://github.com/NousResearch/hermes-agent/pull/921))
- 런타임에 디버그를 토글하는 `/verbose` 슬래시 명령어 ([#94](https://github.com/NousResearch/hermes-agent/pull/94)) — @cesareth
- `/insights` 명령어 — 사용 분석, 비용 추정 및 활동 패턴 ([#552](https://github.com/NousResearch/hermes-agent/pull/552))
- 백그라운드 프로세스 관리를 위한 `/background` 명령어
- 명령어 카테고리가 있는 `/help` 포맷팅
- Bell-on-complete — 에이전트 완료 시 터미널 벨 ([#738](https://github.com/NousResearch/hermes-agent/pull/738))
- 위/아래 화살표 히스토리 탐색
- 클립보드 이미지 붙여넣기 (Alt+V / Ctrl+V)
- 느린 슬래시 명령어를 위한 로딩 인디케이터 ([#882](https://github.com/NousResearch/hermes-agent/pull/882))
- patch_stdout에서의 스피너 깜박임 수정 ([#91](https://github.com/NousResearch/hermes-agent/pull/91)) — @0xbyt4
- 프로그래밍 방식 단일 쿼리 모드를 위한 `--quiet/-Q` 플래그
- 모든 승인 프롬프트를 우회하는 `--fuck-it-ship-it` 플래그 ([#724](https://github.com/NousResearch/hermes-agent/pull/724)) — @dmahan93
- 도구 요약 플래그 ([#767](https://github.com/NousResearch/hermes-agent/pull/767)) — @luisv-1
- SSH에서의 터미널 깜박임 수정 ([#284](https://github.com/NousResearch/hermes-agent/pull/284)) — @ygd58
- 멀티라인 붙여넣기 감지 수정 ([#84](https://github.com/NousResearch/hermes-agent/pull/84)) — @0xbyt4

### 설정 및 구성
- 섹션 하위 명령어와 도구 우선 UX를 갖춘 모듈형 설정 마법사
- 컨테이너 리소스 설정 프롬프트
- 필수 바이너리에 대한 백엔드 검증
- 설정 마이그레이션 시스템 (현재 v7)
- API 키를 config.yaml 대신 .env로 올바르게 라우팅 ([#469](https://github.com/NousResearch/hermes-agent/pull/469)) — @ygd58
- 충돌 시 API 키 손실을 방지하는 .env 원자적 쓰기 ([#954](https://github.com/NousResearch/hermes-agent/pull/954))
- `hermes tools` — curses UI를 사용한 플랫폼별 도구 활성화/비활성화
- 모든 설정된 프로바이더를 대상으로 한 `hermes doctor` 건강 검사
- 게이트웨이 서비스 자동 재시작을 포함한 `hermes update`
- CLI 배너에 업데이트 가능 알림 표시
- 여러 개의 명명된 커스텀 프로바이더
- PATH 설정을 위한 셸 설정 감지 개선 ([#317](https://github.com/NousResearch/hermes-agent/pull/317)) — @mehmetkr-31
- 일관된 HERMES_HOME 및 .env 경로 해석 ([#51](https://github.com/NousResearch/hermes-agent/pull/51), [#48](https://github.com/NousResearch/hermes-agent/pull/48)) — @deankerr
- macOS에서의 Docker 백엔드 수정 + Nous Portal용 서브에이전트 인증 ([#46](https://github.com/NousResearch/hermes-agent/pull/46)) — @rsavitt

---

## 🔧 도구 시스템

### MCP (Model Context Protocol)
- stdio + HTTP 전송 방식을 갖춘 네이티브 MCP 클라이언트 ([#291](https://github.com/NousResearch/hermes-agent/pull/291) — @0xbyt4, [#301](https://github.com/NousResearch/hermes-agent/pull/301))
- 샘플링 지원 — 서버 주도 LLM 요청 ([#753](https://github.com/NousResearch/hermes-agent/pull/753))
- 리소스 및 프롬프트 탐색
- 자동 재연결 및 보안 강화
- 배너 통합, `/reload-mcp` 명령어
- `hermes tools` UI 통합

### 브라우저
- 로컬 브라우저 백엔드 — 비용 없는 헤드리스 Chromium (Browserbase 불필요)
- 콘솔/에러 도구, 주석이 달린 스크린샷, 자동 녹화, dogfood QA 스킬 ([#745](https://github.com/NousResearch/hermes-agent/pull/745))
- 모든 메시징 플랫폼에서 MEDIA:를 통한 스크린샷 공유 ([#657](https://github.com/NousResearch/hermes-agent/pull/657))

### 터미널 및 실행
- json_parse, shell_quote, retry 헬퍼를 갖춘 `execute_code` 샌드박스
- Docker: 커스텀 볼륨 마운트 ([#158](https://github.com/NousResearch/hermes-agent/pull/158)) — @Indelwin
- Daytona 클라우드 샌드박스 백엔드 ([#451](https://github.com/NousResearch/hermes-agent/pull/451)) — @rovle
- SSH 백엔드 수정 ([#59](https://github.com/NousResearch/hermes-agent/pull/59)) — @deankerr
- 환경 일관성을 위한 셸 노이즈 필터링 및 로그인 셸 실행
- execute_code stdout 오버플로우를 위한 Head+tail 잘라내기
- 설정 가능한 백그라운드 프로세스 알림 모드

### 파일 작업
- 파일시스템 체크포인트 및 `/rollback` 명령어 ([#824](https://github.com/NousResearch/hermes-agent/pull/824))
- patch 및 search_files를 위한 구조화된 도구 결과 힌트(다음 작업 안내) ([#722](https://github.com/NousResearch/hermes-agent/issues/722))
- 샌드박스 컨테이너 설정에 Docker 볼륨 전달 ([#687](https://github.com/NousResearch/hermes-agent/pull/687)) — @manuelschipper

---

## 🧩 스킬 생태계

### 스킬 시스템
- 플랫폼별 스킬 활성화/비활성화 ([#743](https://github.com/NousResearch/hermes-agent/pull/743)) — @teyrebaz33
- 도구 가용성 기반 조건부 스킬 활성화 ([#785](https://github.com/NousResearch/hermes-agent/pull/785)) — @teyrebaz33
- 스킬 전제조건 — 충족되지 않은 의존성이 있는 스킬 숨김 ([#659](https://github.com/NousResearch/hermes-agent/pull/659)) — @kshitijk4poor
- 선택적 스킬 — 제공되지만 기본적으로 활성화되지 않음
- `hermes skills browse` — 페이지네이션된 허브 탐색
- 스킬 하위 카테고리 구성
- 플랫폼 조건부 스킬 로딩
- 원자적 스킬 파일 쓰기 ([#551](https://github.com/NousResearch/hermes-agent/pull/551)) — @aydnOktay
- 스킬 동기화 데이터 손실 방지 ([#563](https://github.com/NousResearch/hermes-agent/pull/563)) — @0xbyt4
- CLI 및 게이트웨이를 위한 동적 스킬 슬래시 명령어

### 새로운 스킬 (일부)
- **ASCII Art** — pyfiglet (571개 폰트), cowsay, image-to-ascii ([#209](https://github.com/NousResearch/hermes-agent/pull/209)) — @0xbyt4
- **ASCII Video** — 완전한 프로덕션 파이프라인 ([#854](https://github.com/NousResearch/hermes-agent/pull/854)) — @SHL0MS
- **DuckDuckGo Search** — Firecrawl 폴백 ([#267](https://github.com/NousResearch/hermes-agent/pull/267)) — @gamedevCloudy; DDGS API 확장 ([#598](https://github.com/NousResearch/hermes-agent/pull/598)) — @areu01or00
- **Solana Blockchain** — 지갑 잔액, USD 가격, 토큰 이름 ([#212](https://github.com/NousResearch/hermes-agent/pull/212)) — @gizdusum
- **AgentMail** — 에이전트 소유 이메일 수신함 ([#330](https://github.com/NousResearch/hermes-agent/pull/330)) — @teyrebaz33
- **Polymarket** — 예측 시장 데이터 (읽기 전용) ([#629](https://github.com/NousResearch/hermes-agent/pull/629))
- **OpenClaw Migration** — 공식 마이그레이션 도구 ([#570](https://github.com/NousResearch/hermes-agent/pull/570)) — @unmodeled-tyler
- **Domain Intelligence** — 수동 정찰: 서브도메인, SSL, WHOIS, DNS ([#136](https://github.com/NousResearch/hermes-agent/pull/136)) — @FurkanL0
- **Superpowers** — 소프트웨어 개발 스킬 ([#137](https://github.com/NousResearch/hermes-agent/pull/137)) — @kaos35
- **Hermes-Atropos** — RL 환경 개발 스킬 ([#815](https://github.com/NousResearch/hermes-agent/pull/815))
- 추가: arXiv 검색, OCR/문서, Excalidraw 다이어그램, YouTube 자막, GIF 검색, 포켓몬 플레이어, Minecraft 모드팩 서버, OpenHue (Philips Hue), Google Workspace, Notion, PowerPoint, Obsidian, find-nearby, 그리고 40개 이상의 MLOps 스킬

---

## 🔒 보안 및 안정성

### 보안 강화
- skill_view에서의 경로 탐색 수정 — 임의 파일 읽기 방지 ([#220](https://github.com/NousResearch/hermes-agent/issues/220)) — @Farukest
- sudo 비밀번호 파이핑에서의 셸 인젝션 방지 ([#65](https://github.com/NousResearch/hermes-agent/pull/65)) — @leonsgithub
- 위험 명령어 감지: 멀티라인 우회 수정 ([#233](https://github.com/NousResearch/hermes-agent/pull/233)) — @Farukest; tee/프로세스 대체 패턴 ([#280](https://github.com/NousResearch/hermes-agent/pull/280)) — @dogiladeveloper
- skills_guard에서의 심볼릭 링크 경계 검사 수정 ([#386](https://github.com/NousResearch/hermes-agent/pull/386)) — @Farukest
- macOS에서 write deny list의 심볼릭 링크 우회 수정 ([#61](https://github.com/NousResearch/hermes-agent/pull/61)) — @0xbyt4
- 다중 단어 프롬프트 인젝션 우회 방지 ([#192](https://github.com/NousResearch/hermes-agent/pull/192)) — @0xbyt4
- 크론 프롬프트 인젝션 스캐너 우회 수정 ([#63](https://github.com/NousResearch/hermes-agent/pull/63)) — @0xbyt4
- 민감한 파일에 0600/0700 파일 권한 적용 ([#757](https://github.com/NousResearch/hermes-agent/pull/757))
- .env 파일 권한을 소유자만 접근 가능하도록 제한 ([#529](https://github.com/NousResearch/hermes-agent/pull/529)) — @Himess
- `--force` 플래그가 위험 판정을 무시하지 못하도록 올바르게 차단 ([#388](https://github.com/NousResearch/hermes-agent/pull/388)) — @Farukest
- FTS5 쿼리 살균 + DB 연결 누수 수정 ([#565](https://github.com/NousResearch/hermes-agent/pull/565)) — @0xbyt4
- 비밀 정보 수정 패턴 확장 + 비활성화를 위한 설정 토글
- 데이터 유출 방지를 위한 인메모리 영구 허용 목록 ([#600](https://github.com/NousResearch/hermes-agent/pull/600)) — @alireza78a

### 원자적 쓰기 (데이터 손실 방지)
- sessions.json ([#611](https://github.com/NousResearch/hermes-agent/pull/611)) — @alireza78a
- 크론 작업 ([#146](https://github.com/NousResearch/hermes-agent/pull/146)) — @alireza78a
- .env 설정 ([#954](https://github.com/NousResearch/hermes-agent/pull/954))
- 프로세스 체크포인트 ([#298](https://github.com/NousResearch/hermes-agent/pull/298)) — @aydnOktay
- 배치 러너 ([#297](https://github.com/NousResearch/hermes-agent/pull/297)) — @aydnOktay
- 스킬 파일 ([#551](https://github.com/NousResearch/hermes-agent/pull/551)) — @aydnOktay

### 안정성
- systemd/헤드리스 환경을 위한 모든 print() OSError 보호 ([#963](https://github.com/NousResearch/hermes-agent/pull/963))
- run_conversation 시작 시 모든 재시도 카운터 초기화 ([#607](https://github.com/NousResearch/hermes-agent/pull/607)) — @0xbyt4
- 승인 콜백 타임아웃 시 None 대신 거부 반환 ([#603](https://github.com/NousResearch/hermes-agent/pull/603)) — @0xbyt4
- 코드베이스 전반의 None 메시지 콘텐츠 충돌 수정 ([#277](https://github.com/NousResearch/hermes-agent/pull/277))
- 로컬 LLM 백엔드에서의 컨텍스트 초과 충돌 수정 ([#403](https://github.com/NousResearch/hermes-agent/pull/403)) — @ch3ronsa
- `_flush_sentinel`이 외부 API로 누출되는 것 방지 ([#227](https://github.com/NousResearch/hermes-agent/pull/227)) — @Farukest
- 호출자에서의 conversation_history 변이 방지 ([#229](https://github.com/NousResearch/hermes-agent/pull/229)) — @Farukest
- systemd 재시작 루프 수정 ([#614](https://github.com/NousResearch/hermes-agent/pull/614)) — @voidborne-d
- fd 누수를 방지하기 위한 파일 핸들 및 소켓 닫기 ([#568](https://github.com/NousResearch/hermes-agent/pull/568) — @alireza78a, [#296](https://github.com/NousResearch/hermes-agent/pull/296) — @alireza78a, [#709](https://github.com/NousResearch/hermes-agent/pull/709) — @memosr)
- 클립보드 PNG 변환에서의 데이터 손실 방지 ([#602](https://github.com/NousResearch/hermes-agent/pull/602)) — @0xbyt4
- 터미널 출력에서 셸 노이즈 제거 ([#293](https://github.com/NousResearch/hermes-agent/pull/293)) — @0xbyt4
- 프롬프트, 크론, execute_code를 위한 시간대 인식 now() ([#309](https://github.com/NousResearch/hermes-agent/pull/309)) — @areu01or00

### Windows 호환성
- POSIX 전용 프로세스 함수 보호 ([#219](https://github.com/NousResearch/hermes-agent/pull/219)) — @Farukest
- Git Bash + ZIP 기반 업데이트 폴백을 통한 Windows 네이티브 지원
- PTY 지원을 위한 pywinpty ([#457](https://github.com/NousResearch/hermes-agent/pull/457)) — @shitcoinsherpa
- 모든 설정/데이터 파일 I/O에서 명시적 UTF-8 인코딩 ([#458](https://github.com/NousResearch/hermes-agent/pull/458)) — @shitcoinsherpa
- Windows 호환 경로 처리 ([#354](https://github.com/NousResearch/hermes-agent/pull/354), [#390](https://github.com/NousResearch/hermes-agent/pull/390)) — @Farukest
- 드라이브 문자 경로를 위한 정규식 기반 검색 출력 파싱 ([#533](https://github.com/NousResearch/hermes-agent/pull/533)) — @Himess
- Windows용 인증 저장소 파일 잠금 ([#455](https://github.com/NousResearch/hermes-agent/pull/455)) — @shitcoinsherpa

---

## 🐛 주요 버그 수정

- DeepSeek V3 도구 호출 파서가 멀티라인 JSON 인수를 자동으로 삭제하는 문제 수정 ([#444](https://github.com/NousResearch/hermes-agent/pull/444)) — @PercyDikec
- 오프셋 불일치로 인해 게이트웨이 트랜스크립트에서 턴당 1개 메시지가 손실되는 문제 수정 ([#395](https://github.com/NousResearch/hermes-agent/pull/395)) — @PercyDikec
- /retry 명령어가 에이전트의 최종 응답을 자동으로 폐기하는 문제 수정 ([#441](https://github.com/NousResearch/hermes-agent/pull/441)) — @PercyDikec
- think-block 제거 후 max-iterations 재시도가 빈 문자열을 반환하는 문제 수정 ([#438](https://github.com/NousResearch/hermes-agent/pull/438)) — @PercyDikec
- 하드코딩된 max_tokens를 사용하는 max-iterations 재시도 수정 ([#436](https://github.com/NousResearch/hermes-agent/pull/436)) — @Farukest
- Codex 상태 dict 키 불일치 ([#448](https://github.com/NousResearch/hermes-agent/pull/448)) 및 가시성 필터 ([#446](https://github.com/NousResearch/hermes-agent/pull/446)) 수정 — @PercyDikec
- 최종 사용자 대면 응답에서 \<think\> 블록 제거 ([#174](https://github.com/NousResearch/hermes-agent/pull/174)) — @Bartok9
- 모델이 태그를 문자 그대로 논의할 때 \<think\> 블록 정규식이 보이는 콘텐츠를 제거하는 문제 수정 ([#786](https://github.com/NousResearch/hermes-agent/issues/786))
- 어시스턴트 메시지에 남은 finish_reason로 인한 Mistral 422 에러 수정 ([#253](https://github.com/NousResearch/hermes-agent/pull/253)) — @Sertug17
- 모든 코드 경로에서의 OPENROUTER_API_KEY 해석 순서 수정 ([#295](https://github.com/NousResearch/hermes-agent/pull/295)) — @0xbyt4
- OPENAI_BASE_URL API 키 우선순위 수정 ([#420](https://github.com/NousResearch/hermes-agent/pull/420)) — @manuelschipper
- Anthropic "prompt is too long" 400 에러가 컨텍스트 길이 에러로 감지되지 않는 문제 수정 ([#813](https://github.com/NousResearch/hermes-agent/issues/813))
- SQLite 세션 트랜스크립트가 중복 메시지를 누적하는 문제 수정 — 3-4배 토큰 인플레이션 ([#860](https://github.com/NousResearch/hermes-agent/issues/860))
- 첫 설치 시 설정 마법사가 API 키 프롬프트를 건너뛰는 문제 수정 ([#748](https://github.com/NousResearch/hermes-agent/pull/748))
- 설정 마법사가 Nous Portal에 OpenRouter 모델 목록을 표시하는 문제 수정 ([#575](https://github.com/NousResearch/hermes-agent/pull/575)) — @PercyDikec
- hermes model을 통해 전환할 때 프로바이더 선택이 유지되지 않는 문제 수정 ([#881](https://github.com/NousResearch/hermes-agent/pull/881))
- macOS에서 docker가 PATH에 없을 때 Docker 백엔드 실패 수정 ([#889](https://github.com/NousResearch/hermes-agent/pull/889))
- API 엔드포인트 변경에 대한 ClawHub Skills Hub 어댑터 수정 ([#286](https://github.com/NousResearch/hermes-agent/pull/286)) — @BP602
- API 키가 있을 때 Honcho 자동 활성화 수정 ([#243](https://github.com/NousResearch/hermes-agent/pull/243)) — @Bartok9
- Python 3.11+에서의 중복 'skills' subparser 충돌 수정 ([#898](https://github.com/NousResearch/hermes-agent/issues/898))
- 콘텐츠에 섹션 기호가 포함될 때 메모리 도구 항목 파싱 수정 ([#162](https://github.com/NousResearch/hermes-agent/pull/162)) — @aydnOktay
- 대화형 프롬프트 실패 시 파이프 설치가 자동으로 중단되는 문제 수정 ([#72](https://github.com/NousResearch/hermes-agent/pull/72)) — @cutepawss
- 재귀적 삭제 감지에서의 오탐 수정 ([#68](https://github.com/NousResearch/hermes-agent/pull/68)) — @cutepawss
- 코드베이스 전반의 Ruff lint 경고 수정 ([#608](https://github.com/NousResearch/hermes-agent/pull/608)) — @JackTheGit
- Anthropic 네이티브 base URL fail-fast 수정 ([#173](https://github.com/NousResearch/hermes-agent/pull/173)) — @adavyas
- install.sh가 Node.js 디렉토리를 이동하기 전에 ~/.hermes를 생성하는 문제 수정 ([#53](https://github.com/NousResearch/hermes-agent/pull/53)) — @JoshuaMart
- Ctrl+C에서 atexit 정리 중 SystemExit 트레이스백 수정 ([#55](https://github.com/NousResearch/hermes-agent/pull/55)) — @bierlingm
- 누락된 MIT 라이선스 파일 복원 ([#620](https://github.com/NousResearch/hermes-agent/pull/620)) — @stablegenius49

---

## 🧪 테스트

- 에이전트, 게이트웨이, 도구, 크론, CLI를 포괄하는 **3,289개의 테스트**
- pytest-xdist를 사용한 병렬화된 테스트 스위트 ([#802](https://github.com/NousResearch/hermes-agent/pull/802)) — @OutThisLife
- 단위 테스트 배치 1: 8개 코어 모듈 ([#60](https://github.com/NousResearch/hermes-agent/pull/60)) — @0xbyt4
- 단위 테스트 배치 2: 8개 추가 모듈 ([#62](https://github.com/NousResearch/hermes-agent/pull/62)) — @0xbyt4
- 단위 테스트 배치 3: 8개 미테스트 모듈 ([#191](https://github.com/NousResearch/hermes-agent/pull/191)) — @0xbyt4
- 단위 테스트 배치 4: 5개 보안/로직 핵심 모듈 ([#193](https://github.com/NousResearch/hermes-agent/pull/193)) — @0xbyt4
- AIAgent (run_agent.py) 단위 테스트 ([#67](https://github.com/NousResearch/hermes-agent/pull/67)) — @0xbyt4
- 트라젝토리 압축기 테스트 ([#203](https://github.com/NousResearch/hermes-agent/pull/203)) — @0xbyt4
- Clarify 도구 테스트 ([#121](https://github.com/NousResearch/hermes-agent/pull/121)) — @Bartok9
- Telegram 포맷 테스트 — 이탤릭/볼드/코드 렌더링을 위한 43개 테스트 ([#204](https://github.com/NousResearch/hermes-agent/pull/204)) — @0xbyt4
- 비전 도구 타입 힌트 + 42개 테스트 ([#792](https://github.com/NousResearch/hermes-agent/pull/792))
- 압축기 도구 호출 경계 회귀 테스트 ([#648](https://github.com/NousResearch/hermes-agent/pull/648)) — @intertwine
- 테스트 구조 재구성 ([#34](https://github.com/NousResearch/hermes-agent/pull/34)) — @0xbyt4
- 셸 노이즈 제거 + 36개 테스트 실패 수정 ([#293](https://github.com/NousResearch/hermes-agent/pull/293)) — @0xbyt4

---

## 🔬 RL 및 평가 환경

- WebResearchEnv — 다단계 웹 연구 RL 환경 ([#434](https://github.com/NousResearch/hermes-agent/pull/434)) — @jackx707
- 교착 상태를 방지하기 위한 Modal 샌드박스 동시성 제한 ([#621](https://github.com/NousResearch/hermes-agent/pull/621)) — @voteblake
- Hermes-atropos-environments 번들 스킬 ([#815](https://github.com/NousResearch/hermes-agent/pull/815))
- 평가를 위한 로컬 vLLM 인스턴스 지원 — @dmahan93
- YC-Bench 장기 에이전트 벤치마크 환경
- OpenThoughts-TBLite 평가 환경 및 스크립트

---

## 📚 문서

- 37개 이상의 페이지를 갖춘 전체 문서 웹사이트 (Docusaurus)
- Telegram, Discord, Slack, WhatsApp, Signal, Email을 위한 종합 플랫폼 설정 가이드
- AGENTS.md — AI 코딩 어시스턴트를 위한 개발 가이드
- CONTRIBUTING.md ([#117](https://github.com/NousResearch/hermes-agent/pull/117)) — @Bartok9
- 슬래시 명령어 참조 ([#142](https://github.com/NousResearch/hermes-agent/pull/142)) — @Bartok9
- 종합 AGENTS.md 정확성 감사 ([#732](https://github.com/NousResearch/hermes-agent/pull/732))
- 스킨/테마 시스템 문서
- MCP 문서 및 예제
- 문서 정확성 감사 — 35건 이상 수정
- 문서 오타 수정 ([#825](https://github.com/NousResearch/hermes-agent/pull/825), [#439](https://github.com/NousResearch/hermes-agent/pull/439)) — @JackTheGit
- CLI 설정 우선순위 및 용어 표준화 ([#166](https://github.com/NousResearch/hermes-agent/pull/166), [#167](https://github.com/NousResearch/hermes-agent/pull/167), [#168](https://github.com/NousResearch/hermes-agent/pull/168)) — @Jr-kenny
- Telegram 토큰 정규식 문서 ([#713](https://github.com/NousResearch/hermes-agent/pull/713)) — @VolodymyrBg

---

## 👥 기여자

이 릴리스를 가능하게 해준 63명의 기여자에게 감사드립니다! 단 2주 만에 Hermes Agent 커뮤니티가 함께 모여 놀라운 양의 작업을 완수했습니다.

### 코어
- **@teknium1** — 43개 PR: 프로젝트 리드, 코어 아키텍처, 프로바이더 라우터, 세션, 스킬, CLI, 문서

### 주요 커뮤니티 기여자
- **@0xbyt4** — 40개 PR: MCP 클라이언트, Home Assistant, 보안 수정(심볼릭 링크, 프롬프트 인젝션, 크론), 광범위한 테스트 커버리지(6개 배치), ascii-art 스킬, 셸 노이즈 제거, 스킬 동기화, Telegram 포맷팅 등
- **@Farukest** — 16개 PR: 보안 강화(경로 탐색, 위험 명령어 감지, 심볼릭 링크 경계), Windows 호환성(POSIX 보호, 경로 처리), WhatsApp 수정, max-iterations 재시도, 게이트웨이 수정
- **@aydnOktay** — 11개 PR: 원자적 쓰기(프로세스 체크포인트, 배치 러너, 스킬 파일), Telegram, Discord, 코드 실행, 전사, TTS, 스킬 전반의 에러 처리 개선
- **@Bartok9** — 9개 PR: CONTRIBUTING.md, 슬래시 명령어 참조, Discord 채널 토픽, think-block 제거, TTS 수정, Honcho 수정, 세션 카운트 수정, clarify 테스트
- **@PercyDikec** — 7개 PR: DeepSeek V3 파서 수정, /retry 응답 폐기, 게이트웨이 트랜스크립트 오프셋, Codex 상태/가시성, max-iterations 재시도, 설정 마법사 수정
- **@teyrebaz33** — 5개 PR: 스킬 활성화/비활성화 시스템, 빠른 명령어, 성격 커스터마이징, 조건부 스킬 활성화
- **@alireza78a** — 5개 PR: 원자적 쓰기(크론, 세션), fd 누수 방지, 보안 허용 목록, 코드 실행 소켓 정리
- **@shitcoinsherpa** — 3개 PR: Windows 지원(pywinpty, UTF-8 인코딩, 인증 저장소 잠금)
- **@Himess** — 3개 PR: Cron/HomeAssistant/Daytona 수정, Windows 드라이브 문자 파싱, .env 권한
- **@satelerd** — 2개 PR: WhatsApp 네이티브 미디어, 다중 사용자 세션 격리
- **@rovle** — 1개 PR: Daytona 클라우드 샌드박스 백엔드 (4개 커밋)
- **@erosika** — 1개 PR: Honcho AI 네이티브 메모리 통합
- **@dmahan93** — 1개 PR: --fuck-it-ship-it 플래그 + RL 환경 작업
- **@SHL0MS** — 1개 PR: ASCII video 스킬

### 전체 기여자
@0xbyt4, @BP602, @Bartok9, @Farukest, @FurkanL0, @Himess, @Indelwin, @JackTheGit, @JoshuaMart, @Jr-kenny, @OutThisLife, @PercyDikec, @SHL0MS, @Sertug17, @VencentSoliman, @VolodymyrBg, @adavyas, @alireza78a, @areu01or00, @aydnOktay, @batuhankocyigit, @bierlingm, @caentzminger, @cesareth, @ch3ronsa, @christomitov, @cutepawss, @deankerr, @dmahan93, @dogiladeveloper, @dragonkhoi, @erosika, @gamedevCloudy, @gizdusum, @grp06, @intertwine, @jackx707, @jdblackstar, @johnh4098, @kaos35, @kshitijk4poor, @leonsgithub, @luisv-1, @manuelschipper, @mehmetkr-31, @memosr, @PeterFile, @rewbs, @rovle, @rsavitt, @satelerd, @spanishflu-est1918, @stablegenius49, @tars90percent, @tekelala, @teknium1, @teyrebaz33, @tripledoublev, @unmodeled-tyler, @voidborne-d, @voteblake, @ygd58

---

**전체 변경 로그**: [v0.1.0...v2026.3.12](https://github.com/NousResearch/hermes-agent/compare/v0.1.0...v2026.3.12)
