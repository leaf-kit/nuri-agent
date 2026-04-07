# Hermes Agent v0.3.0 (v2026.3.17)

**릴리스 날짜:** 2026년 3월 17일

> 스트리밍, 플러그인, 프로바이더 릴리스 — 통합 실시간 토큰 전달, 일급 플러그인 아키텍처, Vercel AI Gateway를 갖춘 재구축된 프로바이더 시스템, 네이티브 Anthropic 프로바이더, 스마트 승인, 라이브 Chrome CDP 브라우저 연결, ACP IDE 통합, Honcho 메모리, 음성 모드, 영구 셸, 그리고 모든 플랫폼에 걸친 50건 이상의 버그 수정.

---

## ✨ 주요 하이라이트

- **통합 스트리밍 인프라** — CLI 및 모든 게이트웨이 플랫폼에서 실시간 토큰 단위 전달. 응답이 블록으로 도착하는 대신 생성되는 즉시 스트리밍됩니다. ([#1538](https://github.com/NousResearch/hermes-agent/pull/1538))

- **일급 플러그인 아키텍처** — `~/.hermes/plugins/`에 Python 파일을 넣어 커스텀 도구, 명령어, 훅으로 Hermes를 확장할 수 있습니다. 포크가 필요 없습니다. ([#1544](https://github.com/NousResearch/hermes-agent/pull/1544), [#1555](https://github.com/NousResearch/hermes-agent/pull/1555))

- **네이티브 Anthropic 프로바이더** — Claude Code 인증 정보 자동 탐색, OAuth PKCE 플로우, 네이티브 프롬프트 캐싱을 갖춘 직접 Anthropic API 호출. OpenRouter 중개가 필요 없습니다. ([#1097](https://github.com/NousResearch/hermes-agent/pull/1097))

- **스마트 승인 + /stop 명령어** — 어떤 명령어가 안전한지 학습하고 사용자의 선호를 기억하는 Codex 영감의 승인 시스템. `/stop`은 현재 에이전트 실행을 즉시 종료합니다. ([#1543](https://github.com/NousResearch/hermes-agent/pull/1543))

- **Honcho 메모리 통합** — 비동기 메모리 쓰기, 설정 가능한 회상 모드, 세션 제목 통합, 게이트웨이 모드에서의 다중 사용자 격리. @erosika 기여. ([#736](https://github.com/NousResearch/hermes-agent/pull/736))

- **음성 모드** — CLI에서의 푸시 투 토크, Telegram/Discord에서의 음성 노트, Discord 음성 채널 지원, faster-whisper를 통한 로컬 Whisper 전사. ([#1299](https://github.com/NousResearch/hermes-agent/pull/1299), [#1185](https://github.com/NousResearch/hermes-agent/pull/1185), [#1429](https://github.com/NousResearch/hermes-agent/pull/1429))

- **동시 도구 실행** — 여러 독립적인 도구 호출이 이제 ThreadPoolExecutor를 통해 병렬로 실행되어, 다중 도구 턴의 지연 시간이 크게 감소합니다. ([#1152](https://github.com/NousResearch/hermes-agent/pull/1152))

- **PII 수정** — `privacy.redact_pii`가 활성화되면, 개인 식별 정보가 LLM 프로바이더에 컨텍스트를 전송하기 전에 자동으로 제거됩니다. ([#1542](https://github.com/NousResearch/hermes-agent/pull/1542))

- **`/browser connect` (CDP 경유)** — Chrome DevTools Protocol을 통해 브라우저 도구를 실행 중인 Chrome 인스턴스에 연결합니다. 이미 열려 있는 페이지를 디버그, 검사, 상호작용할 수 있습니다. ([#1549](https://github.com/NousResearch/hermes-agent/pull/1549))

- **Vercel AI Gateway 프로바이더** — Vercel의 AI Gateway를 통해 Hermes를 라우팅하여 모델 카탈로그 및 인프라에 접근합니다. ([#1628](https://github.com/NousResearch/hermes-agent/pull/1628))

- **중앙집중식 프로바이더 라우터** — `call_llm` API, 통합 `/model` 명령어, 모델 전환 시 프로바이더 자동 감지, 보조/위임 클라이언트를 위한 직접 엔드포인트 오버라이드를 갖춘 재구축된 프로바이더 시스템. ([#1003](https://github.com/NousResearch/hermes-agent/pull/1003), [#1506](https://github.com/NousResearch/hermes-agent/pull/1506), [#1375](https://github.com/NousResearch/hermes-agent/pull/1375))

- **ACP 서버 (IDE 통합)** — VS Code, Zed, JetBrains가 이제 전체 슬래시 명령어 지원과 함께 Hermes에 에이전트 백엔드로 연결할 수 있습니다. ([#1254](https://github.com/NousResearch/hermes-agent/pull/1254), [#1532](https://github.com/NousResearch/hermes-agent/pull/1532))

- **영구 셸 모드** — 로컬 및 SSH 터미널 백엔드가 도구 호출 간에 셸 상태를 유지할 수 있습니다 — cd, 환경 변수, 별칭이 유지됩니다. @alt-glitch 기여. ([#1067](https://github.com/NousResearch/hermes-agent/pull/1067), [#1483](https://github.com/NousResearch/hermes-agent/pull/1483))

- **에이전틱 온폴리시 증류 (OPD)** — 에이전트 정책을 증류하기 위한 새로운 RL 훈련 환경으로, Atropos 훈련 생태계를 확장합니다. ([#1149](https://github.com/NousResearch/hermes-agent/pull/1149))

---

## 🏗️ 코어 에이전트 및 아키텍처

### 프로바이더 및 모델 지원
- `call_llm` API 및 통합 `/model` 명령어를 갖춘 **중앙집중식 프로바이더 라우터** — 모델과 프로바이더를 원활하게 전환 ([#1003](https://github.com/NousResearch/hermes-agent/pull/1003))
- **Vercel AI Gateway** 프로바이더 지원 ([#1628](https://github.com/NousResearch/hermes-agent/pull/1628))
- `/model`을 통한 모델 전환 시 **프로바이더 자동 감지** ([#1506](https://github.com/NousResearch/hermes-agent/pull/1506))
- 보조 및 위임 클라이언트를 위한 **직접 엔드포인트 오버라이드** — 비전/서브에이전트 호출을 특정 엔드포인트로 지정 ([#1375](https://github.com/NousResearch/hermes-agent/pull/1375))
- **네이티브 Anthropic 보조 비전** — OpenAI 호환 엔드포인트를 통해 라우팅하는 대신 Claude의 네이티브 비전 API 사용 ([#1377](https://github.com/NousResearch/hermes-agent/pull/1377))
- Anthropic OAuth 플로우 개선 — `claude setup-token` 자동 실행, 재인증, PKCE 상태 영속성, ID 핑거프린팅 ([#1132](https://github.com/NousResearch/hermes-agent/pull/1132), [#1360](https://github.com/NousResearch/hermes-agent/pull/1360), [#1396](https://github.com/NousResearch/hermes-agent/pull/1396), [#1597](https://github.com/NousResearch/hermes-agent/pull/1597))
- Claude 4.6 모델에서 `budget_tokens` 없는 적응형 사고 수정 — @ASRagab ([#1128](https://github.com/NousResearch/hermes-agent/pull/1128))
- 어댑터를 통한 Anthropic 캐시 마커 수정 — @brandtcormorant ([#1216](https://github.com/NousResearch/hermes-agent/pull/1216))
- Anthropic 429/529 에러 재시도 및 사용자에게 세부 정보 표시 — @0xbyt4 ([#1585](https://github.com/NousResearch/hermes-agent/pull/1585))
- Anthropic 어댑터 max_tokens, 폴백 충돌, 프록시 base_url 수정 — @0xbyt4 ([#1121](https://github.com/NousResearch/hermes-agent/pull/1121))
- 여러 병렬 도구 호출을 삭제하는 DeepSeek V3 파서 수정 — @mr-emmett-one ([#1365](https://github.com/NousResearch/hermes-agent/pull/1365), [#1300](https://github.com/NousResearch/hermes-agent/pull/1300))
- 거부 대신 경고와 함께 미등록 모델 수락 ([#1047](https://github.com/NousResearch/hermes-agent/pull/1047), [#1102](https://github.com/NousResearch/hermes-agent/pull/1102))
- 지원되지 않는 OpenRouter 모델에 대한 추론 파라미터 건너뛰기 ([#1485](https://github.com/NousResearch/hermes-agent/pull/1485))
- MiniMax Anthropic API 호환성 수정 ([#1623](https://github.com/NousResearch/hermes-agent/pull/1623))
- 커스텀 엔드포인트 `/models` 검증 및 `/v1` base URL 제안 ([#1480](https://github.com/NousResearch/hermes-agent/pull/1480))
- `custom_providers` 설정에서 위임 프로바이더 해석 ([#1328](https://github.com/NousResearch/hermes-agent/pull/1328))
- Kimi 모델 추가 및 User-Agent 수정 ([#1039](https://github.com/NousResearch/hermes-agent/pull/1039))
- Mistral 호환성을 위한 `call_id`/`response_item_id` 제거 ([#1058](https://github.com/NousResearch/hermes-agent/pull/1058))

### 에이전트 루프 및 대화
- **Anthropic Context Editing API** 지원 ([#1147](https://github.com/NousResearch/hermes-agent/pull/1147))
- 개선된 컨텍스트 압축 인수인계 요약 — 압축기가 더 많은 실행 가능한 상태를 보존 ([#1273](https://github.com/NousResearch/hermes-agent/pull/1273))
- 실행 중 컨텍스트 압축 후 session_id 동기화 ([#1160](https://github.com/NousResearch/hermes-agent/pull/1160))
- 더 능동적인 압축을 위해 세션 위생 임계값을 50%로 조정 ([#1096](https://github.com/NousResearch/hermes-agent/pull/1096), [#1161](https://github.com/NousResearch/hermes-agent/pull/1161))
- `--pass-session-id` 플래그를 통해 시스템 프롬프트에 세션 ID 포함 ([#1040](https://github.com/NousResearch/hermes-agent/pull/1040))
- 재시도 간 닫힌 OpenAI 클라이언트 재사용 방지 ([#1391](https://github.com/NousResearch/hermes-agent/pull/1391))
- 채팅 페이로드 살균 및 프로바이더 우선순위 ([#1253](https://github.com/NousResearch/hermes-agent/pull/1253))
- Codex 및 로컬 백엔드에서의 dict 도구 호출 인수 처리 ([#1393](https://github.com/NousResearch/hermes-agent/pull/1393), [#1440](https://github.com/NousResearch/hermes-agent/pull/1440))

### 메모리 및 세션
- **메모리 우선순위 개선** — 사용자 선호와 수정이 절차적 지식보다 높은 가중치 ([#1548](https://github.com/NousResearch/hermes-agent/pull/1548))
- 시스템 프롬프트에서 더 엄격한 메모리 및 세션 회상 안내 ([#1329](https://github.com/NousResearch/hermes-agent/pull/1329))
- `/insights`를 위해 CLI 토큰 수를 세션 DB에 영구 저장 ([#1498](https://github.com/NousResearch/hermes-agent/pull/1498))
- 캐시된 시스템 접두사에서 Honcho 회상 제외 ([#1201](https://github.com/NousResearch/hermes-agent/pull/1201))
- `session.add_messages()`를 사용하도록 `seed_ai_identity` 수정 ([#1475](https://github.com/NousResearch/hermes-agent/pull/1475))
- 다중 사용자 게이트웨이를 위한 Honcho 세션 라우팅 격리 ([#1500](https://github.com/NousResearch/hermes-agent/pull/1500))

---

## 📱 메시징 플랫폼 (게이트웨이)

### 게이트웨이 코어
- **시스템 게이트웨이 서비스 모드** — 사용자 수준이 아닌 시스템 수준 systemd 서비스로 실행 ([#1371](https://github.com/NousResearch/hermes-agent/pull/1371))
- **게이트웨이 설치 범위 프롬프트** — 설정 중 사용자 vs 시스템 범위 선택 ([#1374](https://github.com/NousResearch/hermes-agent/pull/1374))
- **추론 핫 리로드** — 게이트웨이 재시작 없이 추론 설정 변경 ([#1275](https://github.com/NousResearch/hermes-agent/pull/1275))
- 기본 그룹 세션을 사용자별 격리로 변경 — 그룹 채팅에서 사용자 간 공유 상태 제거 ([#1495](https://github.com/NousResearch/hermes-agent/pull/1495), [#1417](https://github.com/NousResearch/hermes-agent/pull/1417))
- 게이트웨이 재시작 복구 강화 ([#1310](https://github.com/NousResearch/hermes-agent/pull/1310))
- 종료 중 활성 실행 취소 ([#1427](https://github.com/NousResearch/hermes-agent/pull/1427))
- NixOS 및 비표준 시스템을 위한 SSL 인증서 자동 감지 ([#1494](https://github.com/NousResearch/hermes-agent/pull/1494))
- 헤드리스 서버에서 `systemctl --user`를 위한 D-Bus 세션 버스 자동 감지 ([#1601](https://github.com/NousResearch/hermes-agent/pull/1601))
- 헤드리스 서버에서 게이트웨이 설치 중 systemd linger 자동 활성화 ([#1334](https://github.com/NousResearch/hermes-agent/pull/1334))
- `hermes`가 PATH에 없을 때 모듈 진입점으로 폴백 ([#1355](https://github.com/NousResearch/hermes-agent/pull/1355))
- `hermes update` 후 macOS launchd에서 이중 게이트웨이 수정 ([#1567](https://github.com/NousResearch/hermes-agent/pull/1567))
- systemd 유닛에서 재귀적 ExecStop 제거 ([#1530](https://github.com/NousResearch/hermes-agent/pull/1530))
- 게이트웨이 모드에서 로깅 핸들러 누적 방지 ([#1251](https://github.com/NousResearch/hermes-agent/pull/1251))
- 재시도 가능한 시작 실패 시 재시작 — @jplew ([#1517](https://github.com/NousResearch/hermes-agent/pull/1517))
- 에이전트 실행 후 게이트웨이 세션에 모델 정보 보충 ([#1306](https://github.com/NousResearch/hermes-agent/pull/1306))
- PID 기반 게이트웨이 종료 및 지연된 설정 쓰기 ([#1499](https://github.com/NousResearch/hermes-agent/pull/1499))

### Telegram
- 사진 연사 촬영으로 인한 자기 중단을 방지하기 위한 미디어 그룹 버퍼링 ([#1341](https://github.com/NousResearch/hermes-agent/pull/1341), [#1422](https://github.com/NousResearch/hermes-agent/pull/1422))
- 연결 및 전송 중 일시적 TLS 실패 시 재시도 ([#1535](https://github.com/NousResearch/hermes-agent/pull/1535))
- 폴링 충돌 처리 강화 ([#1339](https://github.com/NousResearch/hermes-agent/pull/1339))
- MarkdownV2에서 청크 표시자 및 인라인 코드 이스케이프 ([#1478](https://github.com/NousResearch/hermes-agent/pull/1478), [#1626](https://github.com/NousResearch/hermes-agent/pull/1626))
- 연결 해제 전 updater/app 상태 확인 ([#1389](https://github.com/NousResearch/hermes-agent/pull/1389))

### Discord
- `auto_thread` 설정 및 미디어 메타데이터 수정이 포함된 `/thread` 명령어 ([#1178](https://github.com/NousResearch/hermes-agent/pull/1178))
- @멘션 시 자동 스레드, 봇 스레드에서 멘션 텍스트 건너뛰기 ([#1438](https://github.com/NousResearch/hermes-agent/pull/1438))
- 시스템 메시지에 대한 답장 참조 없이 재시도 ([#1385](https://github.com/NousResearch/hermes-agent/pull/1385))
- 네이티브 문서 및 비디오 첨부 지원 유지 ([#1392](https://github.com/NousResearch/hermes-agent/pull/1392))
- 선택적 임포트 충돌을 방지하기 위한 Discord 어댑터 주석 지연 ([#1314](https://github.com/NousResearch/hermes-agent/pull/1314))

### Slack
- 스레드 처리 전면 개선 — 진행 메시지, 응답, 세션 격리가 모두 스레드를 존중 ([#1103](https://github.com/NousResearch/hermes-agent/pull/1103))
- 포맷팅, 반응, 사용자 해석, 명령어 개선 ([#1106](https://github.com/NousResearch/hermes-agent/pull/1106))
- MAX_MESSAGE_LENGTH 3900 → 39000 수정 ([#1117](https://github.com/NousResearch/hermes-agent/pull/1117))
- 파일 업로드 폴백이 스레드 컨텍스트를 유지 — @0xbyt4 ([#1122](https://github.com/NousResearch/hermes-agent/pull/1122))
- 설정 안내 개선 ([#1387](https://github.com/NousResearch/hermes-agent/pull/1387))

### Email
- IMAP UID 추적 및 SMTP TLS 검증 수정 ([#1305](https://github.com/NousResearch/hermes-agent/pull/1305))
- config.yaml을 통한 `skip_attachments` 옵션 추가 ([#1536](https://github.com/NousResearch/hermes-agent/pull/1536))

### Home Assistant
- 이벤트 필터링이 기본적으로 닫힘 ([#1169](https://github.com/NousResearch/hermes-agent/pull/1169))

---

## 🖥️ CLI 및 사용자 경험

### 대화형 CLI
- **영구 CLI 상태 표시줄** — 항상 보이는 모델, 프로바이더, 토큰 수 ([#1522](https://github.com/NousResearch/hermes-agent/pull/1522))
- **입력 프롬프트에서의 파일 경로 자동완성** ([#1545](https://github.com/NousResearch/hermes-agent/pull/1545))
- **`/plan` 명령어** — 사양에서 구현 계획 생성 ([#1372](https://github.com/NousResearch/hermes-agent/pull/1372), [#1381](https://github.com/NousResearch/hermes-agent/pull/1381))
- **주요 `/rollback` 개선** — 더 풍부한 체크포인트 히스토리, 더 명확한 UX ([#1505](https://github.com/NousResearch/hermes-agent/pull/1505))
- **실행 시 CLI 스킬 사전 로딩** — 첫 번째 프롬프트 전에 스킬이 준비됨 ([#1359](https://github.com/NousResearch/hermes-agent/pull/1359))
- **중앙집중식 슬래시 명령어 레지스트리** — 모든 명령어가 한 번 정의되어 모든 곳에서 사용 ([#1603](https://github.com/NousResearch/hermes-agent/pull/1603))
- `/background`의 별칭으로 `/bg` ([#1590](https://github.com/NousResearch/hermes-agent/pull/1590))
- 슬래시 명령어의 접두사 매칭 — `/mod`가 `/model`로 해석 ([#1320](https://github.com/NousResearch/hermes-agent/pull/1320))
- `/new`, `/reset`, `/clear`가 이제 완전히 새로운 세션을 시작 ([#1237](https://github.com/NousResearch/hermes-agent/pull/1237))
- 세션 작업에 세션 ID 접두사 수락 ([#1425](https://github.com/NousResearch/hermes-agent/pull/1425))
- TUI 프롬프트 및 강조 출력이 활성 스킨을 존중 ([#1282](https://github.com/NousResearch/hermes-agent/pull/1282))
- 레지스트리 + 스킨 통합에서 도구 이모지 메타데이터 중앙화 ([#1484](https://github.com/NousResearch/hermes-agent/pull/1484))
- 위험 명령어 승인에 "전체 명령어 보기" 옵션 추가 — 커뮤니티 디자인 기반 @teknium1 ([#887](https://github.com/NousResearch/hermes-agent/pull/887))
- 비차단 시작 시 업데이트 확인 및 배너 중복 제거 ([#1386](https://github.com/NousResearch/hermes-agent/pull/1386))
- `/reasoning` 명령어 출력 순서 및 인라인 think 추출 수정 ([#1031](https://github.com/NousResearch/hermes-agent/pull/1031))
- 상세 모드에서 잘리지 않은 전체 출력 표시 ([#1472](https://github.com/NousResearch/hermes-agent/pull/1472))
- 라이브 상태 및 토큰을 보고하도록 `/status` 수정 ([#1476](https://github.com/NousResearch/hermes-agent/pull/1476))
- 기본 전역 SOUL.md 시드 ([#1311](https://github.com/NousResearch/hermes-agent/pull/1311))

### 설정 및 구성
- **OpenClaw 마이그레이션** — 최초 설정 중 — @kshitijk4poor ([#981](https://github.com/NousResearch/hermes-agent/pull/981))
- `hermes claw migrate` 명령어 + 마이그레이션 문서 ([#1059](https://github.com/NousResearch/hermes-agent/pull/1059))
- 사용자가 선택한 프로바이더를 존중하는 스마트 비전 설정 ([#1323](https://github.com/NousResearch/hermes-agent/pull/1323))
- 헤드리스 설정 플로우 전체 처리 ([#1274](https://github.com/NousResearch/hermes-agent/pull/1274))
- setup.py에서 `simple_term_menu` 대신 curses 선호 ([#1487](https://github.com/NousResearch/hermes-agent/pull/1487))
- `/status`에서 유효 모델 및 프로바이더 표시 ([#1284](https://github.com/NousResearch/hermes-agent/pull/1284))
- 설정 예제에서 플레이스홀더 구문 사용 ([#1322](https://github.com/NousResearch/hermes-agent/pull/1322))
- 오래된 셸 오버라이드 대신 .env 다시 로드 ([#1434](https://github.com/NousResearch/hermes-agent/pull/1434))
- is_coding_plan NameError 충돌 수정 — @0xbyt4 ([#1123](https://github.com/NousResearch/hermes-agent/pull/1123))
- setuptools 설정에 누락된 패키지 추가 — @alt-glitch ([#912](https://github.com/NousResearch/hermes-agent/pull/912))
- 설치 프로그램: 모든 프롬프트에서 sudo가 필요한 이유 명확화 ([#1602](https://github.com/NousResearch/hermes-agent/pull/1602))

---

## 🔧 도구 시스템

### 터미널 및 실행
- 로컬 및 SSH 백엔드를 위한 **영구 셸 모드** — 도구 호출 간 셸 상태 유지 — @alt-glitch ([#1067](https://github.com/NousResearch/hermes-agent/pull/1067), [#1483](https://github.com/NousResearch/hermes-agent/pull/1483))
- **Tirith 사전 실행 명령어 스캐닝** — 실행 전 명령어를 분석하는 보안 레이어 ([#1256](https://github.com/NousResearch/hermes-agent/pull/1256))
- 모든 서브프로세스 환경에서 Hermes 프로바이더 환경 변수 제거 ([#1157](https://github.com/NousResearch/hermes-agent/pull/1157), [#1172](https://github.com/NousResearch/hermes-agent/pull/1172), [#1399](https://github.com/NousResearch/hermes-agent/pull/1399), [#1419](https://github.com/NousResearch/hermes-agent/pull/1419)) — 초기 수정 @eren-karakus0
- SSH 사전 점검 ([#1486](https://github.com/NousResearch/hermes-agent/pull/1486))
- Docker 백엔드: cwd 작업 공간 마운트를 명시적 옵트인으로 변경 ([#1534](https://github.com/NousResearch/hermes-agent/pull/1534))
- execute_code 샌드박스에서 PYTHONPATH에 프로젝트 루트 추가 ([#1383](https://github.com/NousResearch/hermes-agent/pull/1383))
- 게이트웨이 플랫폼에서 execute_code 진행 스팸 제거 ([#1098](https://github.com/NousResearch/hermes-agent/pull/1098))
- 더 명확한 Docker 백엔드 사전 점검 에러 ([#1276](https://github.com/NousResearch/hermes-agent/pull/1276))

### 브라우저
- **`/browser connect`** — CDP를 통해 실행 중인 Chrome 인스턴스에 브라우저 도구 연결 ([#1549](https://github.com/NousResearch/hermes-agent/pull/1549))
- 브라우저 정리, 로컬 브라우저 PATH 설정, 스크린샷 복구 개선 ([#1333](https://github.com/NousResearch/hermes-agent/pull/1333))

### MCP
- 유틸리티 정책을 통한 **선택적 도구 로딩** — 사용 가능한 MCP 도구 필터링 ([#1302](https://github.com/NousResearch/hermes-agent/pull/1302))
- 재시작 없이 `mcp_servers` 설정 변경 시 MCP 도구 자동 리로드 ([#1474](https://github.com/NousResearch/hermes-agent/pull/1474))
- npx stdio 연결 실패 해결 ([#1291](https://github.com/NousResearch/hermes-agent/pull/1291))
- 플랫폼 도구 설정 저장 시 MCP 도구셋 보존 ([#1421](https://github.com/NousResearch/hermes-agent/pull/1421))

### 비전
- 비전 백엔드 게이팅 통합 ([#1367](https://github.com/NousResearch/hermes-agent/pull/1367))
- 일반 메시지 대신 실제 에러 이유 표시 ([#1338](https://github.com/NousResearch/hermes-agent/pull/1338))
- Claude 이미지 처리 전체 동작 수정 ([#1408](https://github.com/NousResearch/hermes-agent/pull/1408))

### 크론
- **크론 관리를 하나의 도구로 압축** — 여러 명령어를 대체하는 단일 `cronjob` 도구 ([#1343](https://github.com/NousResearch/hermes-agent/pull/1343))
- 자동 전달 대상에 대한 중복 크론 전송 억제 ([#1357](https://github.com/NousResearch/hermes-agent/pull/1357))
- 크론 세션을 SQLite에 영구 저장 ([#1255](https://github.com/NousResearch/hermes-agent/pull/1255))
- 작업별 런타임 오버라이드 (프로바이더, 모델, base_url) ([#1398](https://github.com/NousResearch/hermes-agent/pull/1398))
- 충돌 시 데이터 손실을 방지하기 위한 `save_job_output` 원자적 쓰기 ([#1173](https://github.com/NousResearch/hermes-agent/pull/1173))
- `deliver=origin`에 대한 스레드 컨텍스트 보존 ([#1437](https://github.com/NousResearch/hermes-agent/pull/1437))

### 패치 도구
- V4A 패치 적용에서 파이프 문자 손상 방지 ([#1286](https://github.com/NousResearch/hermes-agent/pull/1286))
- 관대한 `block_anchor` 임계값 및 유니코드 정규화 ([#1539](https://github.com/NousResearch/hermes-agent/pull/1539))

### 위임
- 서브에이전트 결과에 관찰 가능성 메타데이터 추가 (모델, 토큰, 지속 시간, 도구 추적) ([#1175](https://github.com/NousResearch/hermes-agent/pull/1175))

---

## 🧩 스킬 생태계

### 스킬 시스템
- ClawHub와 함께 허브 소스로 **skills.sh 통합** ([#1303](https://github.com/NousResearch/hermes-agent/pull/1303))
- 로드 시 안전한 스킬 환경 설정 ([#1153](https://github.com/NousResearch/hermes-agent/pull/1153))
- 위험 판정에 대한 정책 테이블 준수 ([#1330](https://github.com/NousResearch/hermes-agent/pull/1330))
- ClawHub 스킬 검색 정확 매치 강화 ([#1400](https://github.com/NousResearch/hermes-agent/pull/1400))
- ClawHub 스킬 설치 수정 — `/download` ZIP 엔드포인트 사용 ([#1060](https://github.com/NousResearch/hermes-agent/pull/1060))
- 로컬 스킬을 builtin으로 잘못 표시하는 문제 방지 — @arceus77-7 ([#862](https://github.com/NousResearch/hermes-agent/pull/862))

### 새로운 스킬
- **Linear** 프로젝트 관리 ([#1230](https://github.com/NousResearch/hermes-agent/pull/1230))
- **X/Twitter** (x-cli 경유) ([#1285](https://github.com/NousResearch/hermes-agent/pull/1285))
- **Telephony** — Twilio, SMS, AI 통화 ([#1289](https://github.com/NousResearch/hermes-agent/pull/1289))
- **1Password** — @arceus77-7 ([#883](https://github.com/NousResearch/hermes-agent/pull/883), [#1179](https://github.com/NousResearch/hermes-agent/pull/1179))
- **NeuroSkill BCI** 통합 ([#1135](https://github.com/NousResearch/hermes-agent/pull/1135))
- **Blender MCP** (3D 모델링용) ([#1531](https://github.com/NousResearch/hermes-agent/pull/1531))
- **OSS Security Forensics** ([#1482](https://github.com/NousResearch/hermes-agent/pull/1482))
- **Parallel CLI** 리서치 스킬 ([#1301](https://github.com/NousResearch/hermes-agent/pull/1301))
- **OpenCode** CLI 스킬 ([#1174](https://github.com/NousResearch/hermes-agent/pull/1174))
- **ASCII Video** 스킬 리팩토링 — @SHL0MS ([#1213](https://github.com/NousResearch/hermes-agent/pull/1213), [#1598](https://github.com/NousResearch/hermes-agent/pull/1598))

---

## 🎙️ 음성 모드

- 음성 모드 기반 — CLI에서 푸시 투 토크, Telegram/Discord 음성 노트 ([#1299](https://github.com/NousResearch/hermes-agent/pull/1299))
- faster-whisper를 통한 무료 로컬 Whisper 전사 ([#1185](https://github.com/NousResearch/hermes-agent/pull/1185))
- Discord 음성 채널 안정성 수정 ([#1429](https://github.com/NousResearch/hermes-agent/pull/1429))
- 게이트웨이 음성 노트를 위한 로컬 STT 폴백 복원 ([#1490](https://github.com/NousResearch/hermes-agent/pull/1490))
- 게이트웨이 전사 전반에서 `stt.enabled: false` 준수 ([#1394](https://github.com/NousResearch/hermes-agent/pull/1394))
- Telegram 음성 노트에서의 잘못된 비기능 메시지 수정 (이슈 [#1033](https://github.com/NousResearch/hermes-agent/issues/1033))

---

## 🔌 ACP (IDE 통합)

- ACP 서버 구현 복원 ([#1254](https://github.com/NousResearch/hermes-agent/pull/1254))
- ACP 어댑터에서 슬래시 명령어 지원 ([#1532](https://github.com/NousResearch/hermes-agent/pull/1532))

---

## 🧪 RL 훈련

- **에이전틱 온폴리시 증류 (OPD)** 환경 — 에이전트 정책 증류를 위한 새로운 RL 훈련 환경 ([#1149](https://github.com/NousResearch/hermes-agent/pull/1149))
- tinker-atropos RL 훈련을 완전히 선택적으로 변경 ([#1062](https://github.com/NousResearch/hermes-agent/pull/1062))

---

## 🔒 보안 및 안정성

### 보안 강화
- **Tirith 사전 실행 명령어 스캐닝** — 실행 전 터미널 명령어의 정적 분석 ([#1256](https://github.com/NousResearch/hermes-agent/pull/1256))
- `privacy.redact_pii` 활성화 시 **PII 수정** ([#1542](https://github.com/NousResearch/hermes-agent/pull/1542))
- 모든 서브프로세스 환경에서 Hermes 프로바이더/게이트웨이/도구 환경 변수 제거 ([#1157](https://github.com/NousResearch/hermes-agent/pull/1157), [#1172](https://github.com/NousResearch/hermes-agent/pull/1172), [#1399](https://github.com/NousResearch/hermes-agent/pull/1399), [#1419](https://github.com/NousResearch/hermes-agent/pull/1419))
- Docker cwd 작업 공간 마운트를 명시적 옵트인으로 변경 — 호스트 디렉토리 자동 마운트 금지 ([#1534](https://github.com/NousResearch/hermes-agent/pull/1534))
- 포크 폭탄 정규식 패턴에서 괄호 및 중괄호 이스케이프 ([#1397](https://github.com/NousResearch/hermes-agent/pull/1397))
- `.worktreeinclude` 경로 격리 강화 ([#1388](https://github.com/NousResearch/hermes-agent/pull/1388))
- 승인 충돌을 방지하기 위해 description을 `pattern_key`로 사용 ([#1395](https://github.com/NousResearch/hermes-agent/pull/1395))

### 안정성
- 초기화 시 stdio 쓰기 보호 ([#1271](https://github.com/NousResearch/hermes-agent/pull/1271))
- 세션 로그 쓰기가 공유 원자적 JSON 헬퍼 재사용 ([#1280](https://github.com/NousResearch/hermes-agent/pull/1280))
- 인터럽트 시 원자적 임시 파일 정리 보호 ([#1401](https://github.com/NousResearch/hermes-agent/pull/1401))

---

## 🐛 주요 버그 수정

- **`/status`가 항상 0 토큰을 표시** — 이제 라이브 상태를 보고 (이슈 [#1465](https://github.com/NousResearch/hermes-agent/issues/1465), [#1476](https://github.com/NousResearch/hermes-agent/pull/1476))
- **커스텀 모델 엔드포인트가 작동하지 않음** — 설정 저장된 엔드포인트 해석 복원 (이슈 [#1460](https://github.com/NousResearch/hermes-agent/issues/1460), [#1373](https://github.com/NousResearch/hermes-agent/pull/1373))
- **재시작까지 MCP 도구가 보이지 않음** — 설정 변경 시 자동 리로드 (이슈 [#1036](https://github.com/NousResearch/hermes-agent/issues/1036), [#1474](https://github.com/NousResearch/hermes-agent/pull/1474))
- **`hermes tools`가 MCP 도구를 제거** — 저장 시 MCP 도구셋 보존 (이슈 [#1247](https://github.com/NousResearch/hermes-agent/issues/1247), [#1421](https://github.com/NousResearch/hermes-agent/pull/1421))
- **터미널 서브프로세스가 `OPENAI_BASE_URL`을 상속**하여 외부 도구 손상 (이슈 [#1002](https://github.com/NousResearch/hermes-agent/issues/1002), [#1399](https://github.com/NousResearch/hermes-agent/pull/1399))
- **게이트웨이 재시작 시 백그라운드 프로세스 손실** — 복구 개선 (이슈 [#1144](https://github.com/NousResearch/hermes-agent/issues/1144))
- **크론 작업이 상태를 유지하지 않음** — 이제 SQLite에 저장 (이슈 [#1416](https://github.com/NousResearch/hermes-agent/issues/1416), [#1255](https://github.com/NousResearch/hermes-agent/pull/1255))
- **크론 작업 `deliver: origin`이 스레드 컨텍스트를 보존하지 않음** (이슈 [#1219](https://github.com/NousResearch/hermes-agent/issues/1219), [#1437](https://github.com/NousResearch/hermes-agent/pull/1437))
- **브라우저 프로세스 고아 시 게이트웨이 systemd 서비스 자동 재시작 실패** (이슈 [#1617](https://github.com/NousResearch/hermes-agent/issues/1617))
- **Telegram에서 `/background` 완료 보고서 잘림** (이슈 [#1443](https://github.com/NousResearch/hermes-agent/issues/1443))
- **모델 전환이 적용되지 않음** (이슈 [#1244](https://github.com/NousResearch/hermes-agent/issues/1244), [#1183](https://github.com/NousResearch/hermes-agent/pull/1183))
- **`hermes doctor`가 cronjob을 사용 불가능으로 보고** (이슈 [#878](https://github.com/NousResearch/hermes-agent/issues/878), [#1180](https://github.com/NousResearch/hermes-agent/pull/1180))
- **모바일에서 WhatsApp 브릿지 메시지가 수신되지 않음** (이슈 [#1142](https://github.com/NousResearch/hermes-agent/issues/1142))
- **헤드리스 SSH에서 설정 마법사 멈춤** (이슈 [#905](https://github.com/NousResearch/hermes-agent/issues/905), [#1274](https://github.com/NousResearch/hermes-agent/pull/1274))
- **로그 핸들러 누적**으로 게이트웨이 성능 저하 (이슈 [#990](https://github.com/NousResearch/hermes-agent/issues/990), [#1251](https://github.com/NousResearch/hermes-agent/pull/1251))
- **게이트웨이 DB에서 NULL 모델** (이슈 [#987](https://github.com/NousResearch/hermes-agent/issues/987), [#1306](https://github.com/NousResearch/hermes-agent/pull/1306))
- **엄격한 엔드포인트가 재생된 tool_calls를 거부** (이슈 [#893](https://github.com/NousResearch/hermes-agent/issues/893))
- **남아있는 하드코딩된 `~/.hermes` 경로** — 모두 `HERMES_HOME`을 존중하도록 변경 (이슈 [#892](https://github.com/NousResearch/hermes-agent/issues/892), [#1233](https://github.com/NousResearch/hermes-agent/pull/1233))
- **커스텀 추론 프로바이더에서 위임 도구가 작동하지 않음** (이슈 [#1011](https://github.com/NousResearch/hermes-agent/issues/1011), [#1328](https://github.com/NousResearch/hermes-agent/pull/1328))
- **Skills Guard가 공식 스킬을 차단** (이슈 [#1006](https://github.com/NousResearch/hermes-agent/issues/1006), [#1330](https://github.com/NousResearch/hermes-agent/pull/1330))
- **모델 선택 전에 프로바이더를 쓰는 설정** (이슈 [#1182](https://github.com/NousResearch/hermes-agent/issues/1182))
- **`GatewayConfig.get()` AttributeError**로 모든 메시지 처리 충돌 (이슈 [#1158](https://github.com/NousResearch/hermes-agent/issues/1158), [#1287](https://github.com/NousResearch/hermes-agent/pull/1287))
- **`/update`가 "command not found"로 하드 실패** (이슈 [#1049](https://github.com/NousResearch/hermes-agent/issues/1049))
- **이미지 분석이 자동으로 실패** (이슈 [#1034](https://github.com/NousResearch/hermes-agent/issues/1034), [#1338](https://github.com/NousResearch/hermes-agent/pull/1338))
- **`'dict'` 객체에 `'strip'` 속성이 없는 API `BadRequestError`** (이슈 [#1071](https://github.com/NousResearch/hermes-agent/issues/1071))
- **슬래시 명령어가 정확한 전체 이름 필요** — 이제 접두사 매칭 사용 (이슈 [#928](https://github.com/NousResearch/hermes-agent/issues/928), [#1320](https://github.com/NousResearch/hermes-agent/pull/1320))
- **헤드리스에서 터미널 닫을 때 게이트웨이가 응답을 중단** (이슈 [#1005](https://github.com/NousResearch/hermes-agent/issues/1005))

---

## 🧪 테스트

- 빈 캐시된 Anthropic tool-call 턴 커버 ([#1222](https://github.com/NousResearch/hermes-agent/pull/1222))
- 파서 및 빠른 명령어 커버리지에서 오래된 CI 가정 수정 ([#1236](https://github.com/NousResearch/hermes-agent/pull/1236))
- 암시적 이벤트 루프 없이 게이트웨이 비동기 테스트 수정 ([#1278](https://github.com/NousResearch/hermes-agent/pull/1278))
- 게이트웨이 비동기 테스트를 xdist 안전하게 변경 ([#1281](https://github.com/NousResearch/hermes-agent/pull/1281))
- 크론을 위한 시간대 간 naive 타임스탬프 회귀 ([#1319](https://github.com/NousResearch/hermes-agent/pull/1319))
- 로컬 환경에서 codex 프로바이더 테스트 격리 ([#1335](https://github.com/NousResearch/hermes-agent/pull/1335))
- 재시도 대체 시맨틱 잠금 ([#1379](https://github.com/NousResearch/hermes-agent/pull/1379))
- 세션 검색 도구에서 에러 로깅 개선 — @aydnOktay ([#1533](https://github.com/NousResearch/hermes-agent/pull/1533))

---

## 📚 문서

- 종합 SOUL.md 가이드 ([#1315](https://github.com/NousResearch/hermes-agent/pull/1315))
- 음성 모드 문서 ([#1316](https://github.com/NousResearch/hermes-agent/pull/1316), [#1362](https://github.com/NousResearch/hermes-agent/pull/1362))
- 프로바이더 기여 가이드 ([#1361](https://github.com/NousResearch/hermes-agent/pull/1361))
- ACP 및 내부 시스템 구현 가이드 ([#1259](https://github.com/NousResearch/hermes-agent/pull/1259))
- CLI, 도구, 스킬, 스킨 전반의 Docusaurus 커버리지 확대 ([#1232](https://github.com/NousResearch/hermes-agent/pull/1232))
- 터미널 백엔드 및 Windows 문제 해결 ([#1297](https://github.com/NousResearch/hermes-agent/pull/1297))
- Skills Hub 참조 섹션 ([#1317](https://github.com/NousResearch/hermes-agent/pull/1317))
- 체크포인트, /rollback, git worktrees 가이드 ([#1493](https://github.com/NousResearch/hermes-agent/pull/1493), [#1524](https://github.com/NousResearch/hermes-agent/pull/1524))
- CLI 상태 표시줄 및 /usage 참조 ([#1523](https://github.com/NousResearch/hermes-agent/pull/1523))
- 폴백 프로바이더 + /background 명령어 문서 ([#1430](https://github.com/NousResearch/hermes-agent/pull/1430))
- 게이트웨이 서비스 범위 문서 ([#1378](https://github.com/NousResearch/hermes-agent/pull/1378))
- Slack 스레드 답장 동작 문서 ([#1407](https://github.com/NousResearch/hermes-agent/pull/1407))
- Nous 블루 팔레트로 재설계된 랜딩 페이지 — @austinpickett ([#974](https://github.com/NousResearch/hermes-agent/pull/974))
- 여러 문서 오타 수정 — @JackTheGit ([#953](https://github.com/NousResearch/hermes-agent/pull/953))
- 웹사이트 다이어그램 안정화 ([#1405](https://github.com/NousResearch/hermes-agent/pull/1405))
- README에 CLI vs 메시징 빠른 참조 ([#1491](https://github.com/NousResearch/hermes-agent/pull/1491))
- Docusaurus에 검색 추가 ([#1053](https://github.com/NousResearch/hermes-agent/pull/1053))
- Home Assistant 통합 문서 ([#1170](https://github.com/NousResearch/hermes-agent/pull/1170))

---

## 👥 기여자

### 코어
- **@teknium1** — 코드베이스 전 영역에 걸친 220개 이상의 PR

### 주요 커뮤니티 기여자

- **@0xbyt4** (4개 PR) — Anthropic 어댑터 수정(max_tokens, 폴백 충돌, 429/529 재시도), Slack 파일 업로드 스레드 컨텍스트, 설정 NameError 수정
- **@erosika** (1개 PR) — Honcho 메모리 통합: 비동기 쓰기, 메모리 모드, 세션 제목 통합
- **@SHL0MS** (2개 PR) — ASCII video 스킬 디자인 패턴 및 리팩토링
- **@alt-glitch** (2개 PR) — 로컬/SSH 백엔드를 위한 영구 셸 모드, setuptools 패키징 수정
- **@arceus77-7** (2개 PR) — 1Password 스킬, 스킬 목록 잘못된 레이블 수정
- **@kshitijk4poor** (1개 PR) — 설정 마법사 중 OpenClaw 마이그레이션
- **@ASRagab** (1개 PR) — Claude 4.6 모델을 위한 적응형 사고 수정
- **@eren-karakus0** (1개 PR) — 서브프로세스 환경에서 Hermes 프로바이더 환경 변수 제거
- **@mr-emmett-one** (1개 PR) — DeepSeek V3 파서 다중 도구 호출 지원 수정
- **@jplew** (1개 PR) — 재시도 가능한 시작 실패 시 게이트웨이 재시작
- **@brandtcormorant** (1개 PR) — 빈 텍스트 블록에 대한 Anthropic 캐시 제어 수정
- **@aydnOktay** (1개 PR) — 세션 검색 도구에서 에러 로깅 개선
- **@austinpickett** (1개 PR) — Nous 블루 팔레트로 랜딩 페이지 재설계
- **@JackTheGit** (1개 PR) — 문서 오타 수정

### 전체 기여자

@0xbyt4, @alt-glitch, @arceus77-7, @ASRagab, @austinpickett, @aydnOktay, @brandtcormorant, @eren-karakus0, @erosika, @JackTheGit, @jplew, @kshitijk4poor, @mr-emmett-one, @SHL0MS, @teknium1

---

**전체 변경 로그**: [v2026.3.12...v2026.3.17](https://github.com/NousResearch/hermes-agent/compare/v2026.3.12...v2026.3.17)
