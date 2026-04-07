# Hermes Agent v0.7.0 (v2026.4.3)

**출시일:** 2026년 4월 3일

> 복원력 릴리스 — 플러그형 메모리 프로바이더, 자격 증명 풀 로테이션, Camofox 안티디텍션 브라우저, 인라인 diff 미리보기, 경쟁 조건 및 승인 라우팅에 걸친 게이트웨이 강화, 168개의 PR과 46개의 해결된 이슈에 걸친 심층 보안 수정.

---

## ✨ 주요 변경사항

- **플러그형 메모리 프로바이더 인터페이스** — 메모리가 이제 확장 가능한 플러그인 시스템입니다. 서드파티 메모리 백엔드(Honcho, 벡터 저장소, 커스텀 DB)가 간단한 프로바이더 ABC를 구현하고 플러그인 시스템을 통해 등록합니다. 내장 메모리가 기본 프로바이더입니다. Honcho 통합이 프로필 범위 host/peer 해석을 갖춘 참조 플러그인으로 완전한 동등성을 회복했습니다. ([#4623](https://github.com/NousResearch/hermes-agent/pull/4623), [#4616](https://github.com/NousResearch/hermes-agent/pull/4616), [#4355](https://github.com/NousResearch/hermes-agent/pull/4355))

- **동일 프로바이더 자격 증명 풀** — 동일한 프로바이더에 대해 자동 로테이션이 되는 여러 API 키를 설정합니다. 스레드 안전한 `least_used` 전략으로 키 간 부하를 분산하고, 401 실패 시 자동으로 다음 자격 증명으로 로테이션합니다. 설정 마법사 또는 `credential_pool` 설정을 통해 설정합니다. ([#4188](https://github.com/NousResearch/hermes-agent/pull/4188), [#4300](https://github.com/NousResearch/hermes-agent/pull/4300), [#4361](https://github.com/NousResearch/hermes-agent/pull/4361))

- **Camofox 안티디텍션 브라우저 백엔드** — 스텔스 브라우징을 위한 Camoufox를 사용하는 새로운 로컬 브라우저 백엔드. 시각적 디버깅을 위한 VNC URL 검색이 가능한 영구 세션, 로컬 백엔드용 설정 가능한 SSRF 우회, `hermes tools`를 통한 자동 설치. ([#4008](https://github.com/NousResearch/hermes-agent/pull/4008), [#4419](https://github.com/NousResearch/hermes-agent/pull/4419), [#4292](https://github.com/NousResearch/hermes-agent/pull/4292))

- **인라인 Diff 미리보기** — 파일 쓰기 및 패치 작업이 이제 도구 활동 피드에서 인라인 diff를 표시하여 에이전트가 다음 작업으로 넘어가기 전에 변경된 내용을 시각적으로 확인할 수 있습니다. ([#4411](https://github.com/NousResearch/hermes-agent/pull/4411), [#4423](https://github.com/NousResearch/hermes-agent/pull/4423))

- **API 서버 세션 연속성 및 도구 스트리밍** — API 서버(Open WebUI 통합)가 이제 도구 진행 이벤트를 실시간으로 스트리밍하고 요청 간 영구 세션을 위한 `X-Hermes-Session-Id` 헤더를 지원합니다. 세션은 공유 SessionDB에 지속됩니다. ([#4092](https://github.com/NousResearch/hermes-agent/pull/4092), [#4478](https://github.com/NousResearch/hermes-agent/pull/4478), [#4802](https://github.com/NousResearch/hermes-agent/pull/4802))

- **ACP: 클라이언트 제공 MCP 서버** — 에디터 통합(VS Code, Zed, JetBrains)이 이제 자체 MCP 서버를 등록할 수 있으며, Hermes가 이를 추가 에이전트 도구로 사용합니다. 에디터의 MCP 생태계가 에이전트에 직접 흘러들어갑니다. ([#4705](https://github.com/NousResearch/hermes-agent/pull/4705))

- **게이트웨이 강화** — 경쟁 조건, 사진 미디어 전달, 홍수 제어, 멈춘 세션, 승인 라우팅, 압축 데스 스파이럴에 걸친 주요 안정성 개선. 게이트웨이가 프로덕션에서 상당히 더 안정적입니다. ([#4727](https://github.com/NousResearch/hermes-agent/pull/4727), [#4750](https://github.com/NousResearch/hermes-agent/pull/4750), [#4798](https://github.com/NousResearch/hermes-agent/pull/4798), [#4557](https://github.com/NousResearch/hermes-agent/pull/4557))

- **보안: 시크릿 유출 차단** — 브라우저 URL과 LLM 응답이 이제 시크릿 패턴을 스캔하여 URL 인코딩, base64, 프롬프트 인젝션을 통한 유출 시도를 차단합니다. 자격 증명 디렉토리 보호가 `.docker`, `.azure`, `.config/gh`로 확장되었습니다. execute_code 샌드박스 출력이 편집됩니다. ([#4483](https://github.com/NousResearch/hermes-agent/pull/4483), [#4360](https://github.com/NousResearch/hermes-agent/pull/4360), [#4305](https://github.com/NousResearch/hermes-agent/pull/4305), [#4327](https://github.com/NousResearch/hermes-agent/pull/4327))

---

## 🏗️ 코어 에이전트 및 아키텍처

### 프로바이더 및 모델 지원
- **동일 프로바이더 자격 증명 풀** — 자동 `least_used` 로테이션 및 401 장애 조치를 갖춘 다중 API 키 설정 ([#4188](https://github.com/NousResearch/hermes-agent/pull/4188), [#4300](https://github.com/NousResearch/hermes-agent/pull/4300))
- **스마트 라우팅을 통한 자격 증명 풀 보존** — 폴백 프로바이더 전환 시에도 풀 상태가 유지되며 429에 대한 즉시 폴백을 지연 ([#4361](https://github.com/NousResearch/hermes-agent/pull/4361))
- **턴별 기본 런타임 복원** — 폴백 프로바이더 사용 후 에이전트가 다음 턴에 트랜스포트 복구와 함께 기본 프로바이더를 자동 복원 ([#4624](https://github.com/NousResearch/hermes-agent/pull/4624))
- **GPT-5 및 Codex 모델용 `developer` 역할** — 최신 모델에 OpenAI의 권장 시스템 메시지 역할 사용 ([#4498](https://github.com/NousResearch/hermes-agent/pull/4498))
- **Google 모델 운영 지침** — Gemini 및 Gemma 모델에 프로바이더별 프롬프팅 지침 제공 ([#4641](https://github.com/NousResearch/hermes-agent/pull/4641))
- **Anthropic 장문 컨텍스트 티어 429 처리** — 티어 제한 도달 시 컨텍스트를 자동으로 200k로 축소 ([#4747](https://github.com/NousResearch/hermes-agent/pull/4747))
- **서드파티 Anthropic 엔드포인트용 URL 기반 인증** + CI 테스트 수정 ([#4148](https://github.com/NousResearch/hermes-agent/pull/4148))
- **MiniMax Anthropic 엔드포인트용 Bearer 인증** ([#4028](https://github.com/NousResearch/hermes-agent/pull/4028))
- **Fireworks 컨텍스트 길이 감지** ([#4158](https://github.com/NousResearch/hermes-agent/pull/4158))
- Alibaba 프로바이더용 **표준 DashScope 국제 엔드포인트** ([#4133](https://github.com/NousResearch/hermes-agent/pull/4133), closes [#3912](https://github.com/NousResearch/hermes-agent/issues/3912))
- 위생 압축에서 **커스텀 프로바이더 context_length** 존중 ([#4085](https://github.com/NousResearch/hermes-agent/pull/4085))
- **non-sk-ant 키**를 OAuth 토큰이 아닌 일반 API 키로 처리 ([#4093](https://github.com/NousResearch/hermes-agent/pull/4093))
- OpenRouter 및 Nous 모델 목록에 **Claude-sonnet-4.6** 추가 ([#4157](https://github.com/NousResearch/hermes-agent/pull/4157))
- 모델 목록에 **Qwen 3.6 Plus Preview** 추가 ([#4376](https://github.com/NousResearch/hermes-agent/pull/4376))
- hermes 모델 선택기 및 OpenCode에 **MiniMax M2.7** 추가 ([#4208](https://github.com/NousResearch/hermes-agent/pull/4208))
- 커스텀 엔드포인트 설정에서 **서버 탐색을 통한 모델 자동 감지** ([#4218](https://github.com/NousResearch/hermes-agent/pull/4218))
- 엔드포인트 URL에 대한 **Config.yaml 단일 진실 소스** — 더 이상 환경 변수와 config.yaml 간 충돌 없음 ([#4165](https://github.com/NousResearch/hermes-agent/pull/4165))
- **설정 마법사가 더 이상 커스텀 엔드포인트 설정을 덮어쓰지 않음** ([#4180](https://github.com/NousResearch/hermes-agent/pull/4180), closes [#4172](https://github.com/NousResearch/hermes-agent/issues/4172))
- `hermes model`과 함께 **통합된 설정 마법사 프로바이더 선택** — 두 흐름에 대한 단일 코드 경로 ([#4200](https://github.com/NousResearch/hermes-agent/pull/4200))
- **루트 레벨 프로바이더 설정**이 더 이상 `model.provider`를 재정의하지 않음 ([#4329](https://github.com/NousResearch/hermes-agent/pull/4329))
- 스팸 방지를 위한 **페어링 거부 메시지 속도 제한** ([#4081](https://github.com/NousResearch/hermes-agent/pull/4081))

### 에이전트 루프 및 대화
- 도구 사용 턴 간 **Anthropic 사고 블록 서명 보존** ([#4626](https://github.com/NousResearch/hermes-agent/pull/4626))
- 재시도 전 **사고 전용 빈 응답 분류** — 콘텐츠 없이 사고 블록만 생성하는 모델에서의 무한 재시도 루프 방지 ([#4645](https://github.com/NousResearch/hermes-agent/pull/4645))
- API 연결 해제로 인한 **압축 데스 스파이럴 방지** — 압축이 트리거되고 실패하면 다시 압축하는 루프를 중지 ([#4750](https://github.com/NousResearch/hermes-agent/pull/4750), closes [#2153](https://github.com/NousResearch/hermes-agent/issues/2153))
- 실행 중 압축 후 게이트웨이 세션에 **압축된 컨텍스트 지속** ([#4095](https://github.com/NousResearch/hermes-agent/pull/4095))
- **컨텍스트 초과 에러 메시지**에 실행 가능한 안내 포함 ([#4155](https://github.com/NousResearch/hermes-agent/pull/4155), closes [#4061](https://github.com/NousResearch/hermes-agent/issues/4061))
- 사용자 대면 응답에서 **고아 think/reasoning 태그 제거** ([#4311](https://github.com/NousResearch/hermes-agent/pull/4311), closes [#4285](https://github.com/NousResearch/hermes-agent/issues/4285))
- **Codex 응답 사전검사 강화** 및 스트림 에러 처리 ([#4313](https://github.com/NousResearch/hermes-agent/pull/4313))
- 프롬프트 캐시 일관성을 위해 임의 UUID 대신 **결정론적 call_id 폴백** ([#3991](https://github.com/NousResearch/hermes-agent/pull/3991))
- 압축 후 **컨텍스트 압력 경고 스팸** 방지 ([#4012](https://github.com/NousResearch/hermes-agent/pull/4012))
- 닫힌 이벤트 루프 에러를 방지하기 위해 궤적 압축기에서 **AsyncOpenAI 지연 생성** ([#4013](https://github.com/NousResearch/hermes-agent/pull/4013))

### 메모리 및 세션
- **플러그형 메모리 프로바이더 인터페이스** — 프로필 격리를 갖춘 커스텀 메모리 백엔드용 ABC 기반 플러그인 시스템 ([#4623](https://github.com/NousResearch/hermes-agent/pull/4623))
- 참조 메모리 프로바이더 플러그인으로 **Honcho 완전 통합 동등성** 복원 ([#4355](https://github.com/NousResearch/hermes-agent/pull/4355)) — @erosika
- **Honcho 프로필 범위** host 및 peer 해석 ([#4616](https://github.com/NousResearch/hermes-agent/pull/4616))
- 게이트웨이 재시작 시 중복 재플러시를 방지하기 위해 **메모리 플러시 상태 지속** ([#4481](https://github.com/NousResearch/hermes-agent/pull/4481))
- 순차 실행 경로를 통해 **메모리 프로바이더 도구** 라우팅 ([#4803](https://github.com/NousResearch/hermes-agent/pull/4803))
- 프로필 격리를 위해 인스턴스 로컬 경로에 **Honcho 설정** 기록 ([#4037](https://github.com/NousResearch/hermes-agent/pull/4037))
- 공유 SessionDB에 **API 서버 세션** 지속 ([#4802](https://github.com/NousResearch/hermes-agent/pull/4802))
- 비CLI 세션에 대한 **토큰 사용량 지속** ([#4627](https://github.com/NousResearch/hermes-agent/pull/4627))
- **FTS5 쿼리에서 점이 포함된 용어 따옴표 처리** — 점이 포함된 용어에 대한 세션 검색 수정 ([#4549](https://github.com/NousResearch/hermes-agent/pull/4549))

---

## 📱 메시징 플랫폼 (게이트웨이)

### 게이트웨이 코어
- **경쟁 조건 수정** — 사진 미디어 손실, 홍수 제어, 멈춘 세션, STT 설정 문제를 한 번의 강화 패스로 해결 ([#4727](https://github.com/NousResearch/hermes-agent/pull/4727))
- **실행 중인 에이전트 가드를 통한 승인 라우팅** — `/approve` 및 `/deny`가 이제 인터럽트로 삼키는 대신 에이전트가 승인을 대기하며 차단되었을 때 올바르게 라우팅 ([#4798](https://github.com/NousResearch/hermes-agent/pull/4798), [#4557](https://github.com/NousResearch/hermes-agent/pull/4557), closes [#4542](https://github.com/NousResearch/hermes-agent/issues/4542))
- **/approve 후 에이전트 재개** — 차단된 명령 실행 시 도구 결과가 더 이상 손실되지 않음 ([#4418](https://github.com/NousResearch/hermes-agent/pull/4418))
- 컨텍스트를 보존하기 위해 부모 트랜스크립트로 **DM 스레드 세션 시딩** ([#4559](https://github.com/NousResearch/hermes-agent/pull/4559))
- **스킬 인식 슬래시 명령** — 게이트웨이가 설치된 스킬을 슬래시 명령으로 동적 등록, 페이지네이션된 `/commands` 목록 및 Telegram 100개 명령 제한 ([#3934](https://github.com/NousResearch/hermes-agent/pull/3934), [#4005](https://github.com/NousResearch/hermes-agent/pull/4005), [#4006](https://github.com/NousResearch/hermes-agent/pull/4006), [#4010](https://github.com/NousResearch/hermes-agent/pull/4010), [#4023](https://github.com/NousResearch/hermes-agent/pull/4023))
- Telegram 메뉴 및 게이트웨이 디스패치에서 **플랫폼별 비활성화된 스킬** 존중 ([#4799](https://github.com/NousResearch/hermes-agent/pull/4799))
- **사용자 대면 압축 경고 제거** — 더 깔끔한 메시지 흐름 ([#4139](https://github.com/NousResearch/hermes-agent/pull/4139))
- 게이트웨이 서비스용 **`-v/-q` 플래그를 stderr 로깅에 연결** ([#4474](https://github.com/NousResearch/hermes-agent/pull/4474))
- 시스템 서비스 유닛에서 대상 사용자로 **HERMES_HOME 재매핑** ([#4456](https://github.com/NousResearch/hermes-agent/pull/4456))
- **잘못된 불리언 유사 설정 값에 대한 기본값 존중** ([#4029](https://github.com/NousResearch/hermes-agent/pull/4029))
- systemd 권한 문제를 피하기 위해 `/update` 명령에서 **systemd-run 대신 setsid 사용** ([#4104](https://github.com/NousResearch/hermes-agent/pull/4104), closes [#4017](https://github.com/NousResearch/hermes-agent/issues/4017))
- 더 나은 UX를 위해 첫 메시지에 **'Initializing agent...'** 표시 ([#4086](https://github.com/NousResearch/hermes-agent/pull/4086))
- LXC/컨테이너 환경을 위해 **root로 게이트웨이 서비스 실행 허용** ([#4732](https://github.com/NousResearch/hermes-agent/pull/4732))

### Telegram
- 충돌 방지와 함께 **명령 이름 32자 제한** ([#4211](https://github.com/NousResearch/hermes-agent/pull/4211))
- 메뉴에서 **우선순위 순서 시행** — 코어 > 플러그인 > 스킬 ([#4023](https://github.com/NousResearch/hermes-agent/pull/4023))
- **50개 명령으로 제한** — API가 ~60개 이상을 거부 ([#4006](https://github.com/NousResearch/hermes-agent/pull/4006))
- 400 에러를 방지하기 위해 **빈/공백 텍스트 건너뛰기** ([#4388](https://github.com/NousResearch/hermes-agent/pull/4388))
- **E2E 게이트웨이 테스트** 추가 ([#4497](https://github.com/NousResearch/hermes-agent/pull/4497)) — @pefontana

### Discord
- **버튼 기반 승인 UI** — 인터랙티브 버튼 프롬프트와 함께 `/approve` 및 `/deny` 슬래시 명령 등록 ([#4800](https://github.com/NousResearch/hermes-agent/pull/4800))
- **설정 가능한 리액션** — 메시지 처리 리액션을 비활성화하는 `discord.reactions` 설정 옵션 ([#4199](https://github.com/NousResearch/hermes-agent/pull/4199))
- 인증되지 않은 사용자에 대한 **리액션 및 자동 스레딩 건너뛰기** ([#4387](https://github.com/NousResearch/hermes-agent/pull/4387))

### Slack
- **스레드에 답장** — 스레드 응답을 위한 `slack.reply_in_thread` 설정 옵션 ([#4643](https://github.com/NousResearch/hermes-agent/pull/4643), closes [#2662](https://github.com/NousResearch/hermes-agent/issues/2662))

### WhatsApp
- **그룹 채팅에서 require_mention 시행** ([#4730](https://github.com/NousResearch/hermes-agent/pull/4730))

### Webhook
- **플랫폼 지원 수정** — 웹훅 어댑터에 대한 홈 채널 프롬프트 건너뛰기, 도구 진행 비활성화 ([#4660](https://github.com/NousResearch/hermes-agent/pull/4660))

### Matrix
- **E2EE 복호화 강화** — 누락된 키 요청, 디바이스 자동 신뢰, 버퍼된 이벤트 재시도 ([#4083](https://github.com/NousResearch/hermes-agent/pull/4083))

---

## 🖥️ CLI 및 사용자 경험

### 새로운 슬래시 명령
- **`/yolo`** — 세션에 대한 위험 명령 승인 토글 ([#3990](https://github.com/NousResearch/hermes-agent/pull/3990))
- **`/btw`** — 주 대화 컨텍스트에 영향을 미치지 않는 임시 사이드 질문 ([#4161](https://github.com/NousResearch/hermes-agent/pull/4161))
- **`/profile`** — 채팅 세션을 떠나지 않고 활성 프로필 정보 표시 ([#4027](https://github.com/NousResearch/hermes-agent/pull/4027))

### 대화형 CLI
- 도구 활동 피드에서 쓰기 및 패치 작업에 대한 **인라인 diff 미리보기** ([#4411](https://github.com/NousResearch/hermes-agent/pull/4411), [#4423](https://github.com/NousResearch/hermes-agent/pull/4423))
- 시작 시 **TUI를 하단에 고정** — 응답과 입력 사이의 큰 빈 공간 해소 ([#4412](https://github.com/NousResearch/hermes-agent/pull/4412), [#4359](https://github.com/NousResearch/hermes-agent/pull/4359), closes [#4398](https://github.com/NousResearch/hermes-agent/issues/4398), [#4421](https://github.com/NousResearch/hermes-agent/issues/4421))
- **`/history` 및 `/resume`**이 이제 검색 없이 직접 최근 세션을 표시 ([#4728](https://github.com/NousResearch/hermes-agent/pull/4728))
- 합계가 맞도록 `/insights` 개요에 **캐시 토큰 표시** ([#4428](https://github.com/NousResearch/hermes-agent/pull/4428))
- 에이전트 반복을 제한하는 `hermes chat`용 **`--max-turns` CLI 플래그** ([#4314](https://github.com/NousResearch/hermes-agent/pull/4314))
- 슬래시 명령으로 처리하는 대신 **드래그된 파일 경로 감지** ([#4533](https://github.com/NousResearch/hermes-agent/pull/4533)) — @rolme
- `config set`에서 **빈 문자열 및 거짓 값 허용** ([#4310](https://github.com/NousResearch/hermes-agent/pull/4310), closes [#4277](https://github.com/NousResearch/hermes-agent/issues/4277))
- PulseAudio 브릿지가 설정된 경우 **WSL에서 음성 모드** ([#4317](https://github.com/NousResearch/hermes-agent/pull/4317))
- 접근성을 위한 **`NO_COLOR` 환경 변수** 및 `TERM=dumb` 존중 ([#4079](https://github.com/NousResearch/hermes-agent/pull/4079), closes [#4066](https://github.com/NousResearch/hermes-agent/issues/4066)) — @SHL0MS
- macOS/zsh 사용자를 위한 **올바른 셸 리로드 안내** ([#4025](https://github.com/NousResearch/hermes-agent/pull/4025))
- 성공적인 조용한 모드 쿼리에서 **종료 코드 0** 반환 ([#4613](https://github.com/NousResearch/hermes-agent/pull/4613), closes [#4601](https://github.com/NousResearch/hermes-agent/issues/4601)) — @devorun
- 중단된 종료 시 **on_session_end 훅 실행** ([#4159](https://github.com/NousResearch/hermes-agent/pull/4159))
- **프로필 목록 표시**가 `model.default` 키를 올바르게 읽음 ([#4160](https://github.com/NousResearch/hermes-agent/pull/4160))
- 재설정 메뉴에 **브라우저 및 TTS** 표시 ([#4041](https://github.com/NousResearch/hermes-agent/pull/4041))
- **웹 백엔드 우선순위** 감지 단순화 ([#4036](https://github.com/NousResearch/hermes-agent/pull/4036))

### 설정 및 구성
- 설정 중 **Allowed_users 보존** 및 비설정 프로바이더 경고 조용히 처리 ([#4551](https://github.com/NousResearch/hermes-agent/pull/4551)) — @kshitijk4poor
- 커스텀 엔드포인트에 대한 **모델 설정에 API 키 저장** ([#4202](https://github.com/NousResearch/hermes-agent/pull/4202), closes [#4182](https://github.com/NousResearch/hermes-agent/issues/4182))
- 마법사 트리거에서 명시적 Hermes 설정 뒤에 **Claude Code 자격 증명 게이팅** ([#4210](https://github.com/NousResearch/hermes-agent/pull/4210))
- 인터럽트 시 설정 손실을 방지하기 위한 **save_config_value의 원자적 쓰기** ([#4298](https://github.com/NousResearch/hermes-agent/pull/4298), [#4320](https://github.com/NousResearch/hermes-agent/pull/4320))
- 토큰 새로고침 시 Claude Code 자격 증명에 **Scopes 필드 기록** ([#4126](https://github.com/NousResearch/hermes-agent/pull/4126))

### 업데이트 시스템
- `hermes update`에서 **포크 감지 및 업스트림 동기화** ([#4744](https://github.com/NousResearch/hermes-agent/pull/4744))
- 업데이트 중 하나의 추가 기능이 실패해도 **작동하는 선택적 extras 보존** ([#4550](https://github.com/NousResearch/hermes-agent/pull/4550))
- hermes update 중 **충돌된 git 인덱스 처리** ([#4735](https://github.com/NousResearch/hermes-agent/pull/4735))
- macOS에서 **launchd 재시작 경쟁 조건 방지** ([#4736](https://github.com/NousResearch/hermes-agent/pull/4736))
- doctor 및 status 명령에 **누락된 subprocess.run() 타임아웃** 추가 ([#4009](https://github.com/NousResearch/hermes-agent/pull/4009))

---

## 🔧 도구 시스템

### 브라우저
- **Camofox 안티디텍션 브라우저 백엔드** — `hermes tools`를 통한 자동 설치가 가능한 로컬 스텔스 브라우징 ([#4008](https://github.com/NousResearch/hermes-agent/pull/4008))
- 시각적 디버깅을 위한 VNC URL 검색이 가능한 **영구 Camofox 세션** ([#4419](https://github.com/NousResearch/hermes-agent/pull/4419))
- 로컬 백엔드(Camofox, 헤드리스 Chromium)에 대한 **SSRF 검사 건너뛰기** ([#4292](https://github.com/NousResearch/hermes-agent/pull/4292))
- `browser.allow_private_urls`를 통한 **설정 가능한 SSRF 검사** ([#4198](https://github.com/NousResearch/hermes-agent/pull/4198)) — @nils010485
- Docker 명령에 **CAMOFOX_PORT=9377** 추가 ([#4340](https://github.com/NousResearch/hermes-agent/pull/4340))

### 파일 작업
- 쓰기 및 패치 동작에 대한 **인라인 diff 미리보기** ([#4411](https://github.com/NousResearch/hermes-agent/pull/4411), [#4423](https://github.com/NousResearch/hermes-agent/pull/4423))
- 쓰기 및 패치 시 **오래된 파일 감지** — 마지막 읽기 이후 외부에서 수정된 경우 경고 ([#4345](https://github.com/NousResearch/hermes-agent/pull/4345))
- 쓰기 후 **신선도 타임스탬프 새로고침** ([#4390](https://github.com/NousResearch/hermes-agent/pull/4390))
- read_file에서 **크기 제한, 중복 제거, 디바이스 차단** ([#4315](https://github.com/NousResearch/hermes-agent/pull/4315))

### MCP
- **안정성 수정 팩** — 리로드 타임아웃, 종료 정리, 이벤트 루프 핸들러, OAuth 비차단 ([#4757](https://github.com/NousResearch/hermes-agent/pull/4757), closes [#4462](https://github.com/NousResearch/hermes-agent/issues/4462), [#2537](https://github.com/NousResearch/hermes-agent/issues/2537))

### ACP (에디터 통합)
- **클라이언트 제공 MCP 서버**를 에이전트 도구로 등록 — 에디터가 자체 MCP 서버를 Hermes에 전달 ([#4705](https://github.com/NousResearch/hermes-agent/pull/4705))

### 스킬 시스템
- **에이전트 쓰기에 대한 크기 제한** 및 **스킬 패치에 대한 퍼지 매칭** — 과도한 크기의 스킬 쓰기를 방지하고 편집 안정성 개선 ([#4414](https://github.com/NousResearch/hermes-agent/pull/4414))
- 설치 전 **허브 번들 경로 검증** — 스킬 번들에서 경로 순회 차단 ([#3986](https://github.com/NousResearch/hermes-agent/pull/3986))
- **hermes-agent와 hermes-agent-setup을 단일 스킬로 통합** ([#4332](https://github.com/NousResearch/hermes-agent/pull/4332))
- extract_skill_conditions에서 **스킬 메타데이터 타입 검사** ([#4479](https://github.com/NousResearch/hermes-agent/pull/4479))

### 새로운/업데이트된 스킬
- **research-paper-writing** — 완전한 엔드투엔드 연구 파이프라인 (ml-paper-writing 교체) ([#4654](https://github.com/NousResearch/hermes-agent/pull/4654)) — @SHL0MS
- **ascii-video** — 텍스트 가독성 기법 및 외부 레이아웃 오라클 ([#4054](https://github.com/NousResearch/hermes-agent/pull/4054)) — @SHL0MS
- **youtube-transcript** — youtube-transcript-api v1.x에 맞게 업데이트 ([#4455](https://github.com/NousResearch/hermes-agent/pull/4455)) — @el-analista
- 문서 사이트에 **스킬 탐색 및 검색 페이지** 추가 ([#4500](https://github.com/NousResearch/hermes-agent/pull/4500)) — @IAvecilla

---

## 🔒 보안 및 안정성

### 보안 강화
- 브라우저 URL 및 LLM 응답을 통한 **시크릿 유출 차단** — URL 인코딩, base64, 프롬프트 인젝션 벡터에서 시크릿 패턴 스캔 ([#4483](https://github.com/NousResearch/hermes-agent/pull/4483))
- **execute_code 샌드박스 출력에서 시크릿 편집** ([#4360](https://github.com/NousResearch/hermes-agent/pull/4360))
- 파일 도구 및 터미널을 통한 읽기/쓰기에서 **`.docker`, `.azure`, `.config/gh` 자격 증명 디렉토리 보호** ([#4305](https://github.com/NousResearch/hermes-agent/pull/4305), [#4327](https://github.com/NousResearch/hermes-agent/pull/4327)) — @memosr
- 편집에 **GitHub OAuth 토큰 패턴** 추가 + 스냅샷 편집 플래그 ([#4295](https://github.com/NousResearch/hermes-agent/pull/4295))
- Telegram DoH 폴백에서 **사설 및 루프백 IP 거부** ([#4129](https://github.com/NousResearch/hermes-agent/pull/4129))
- 자격 증명 파일 등록에서 **경로 순회 거부** ([#4316](https://github.com/NousResearch/hermes-agent/pull/4316))
- 프로필 가져오기 시 **tar 아카이브 멤버 경로 검증** — zip-slip 공격 차단 ([#4318](https://github.com/NousResearch/hermes-agent/pull/4318))
- 프로필 내보내기에서 **auth.json 및 .env 제외** ([#4475](https://github.com/NousResearch/hermes-agent/pull/4475))

### 안정성
- API 연결 해제로 인한 **압축 데스 스파이럴 방지** ([#4750](https://github.com/NousResearch/hermes-agent/pull/4750), closes [#2153](https://github.com/NousResearch/hermes-agent/issues/2153))
- OpenAI SDK에서 **`is_closed`를 메서드로 처리** — 잘못된 양성 클라이언트 종료 감지 방지 ([#4416](https://github.com/NousResearch/hermes-agent/pull/4416), closes [#4377](https://github.com/NousResearch/hermes-agent/issues/4377))
- **[all] extras에서 matrix 제외** — python-olm이 업스트림에서 깨져 설치 실패 방지 ([#4615](https://github.com/NousResearch/hermes-agent/pull/4615), closes [#4178](https://github.com/NousResearch/hermes-agent/issues/4178))
- **OpenCode 모델 라우팅** 수리 ([#4508](https://github.com/NousResearch/hermes-agent/pull/4508))
- **Docker 컨테이너 이미지** 최적화 ([#4034](https://github.com/NousResearch/hermes-agent/pull/4034)) — @bcross

### Windows 및 크로스 플랫폼
- PulseAudio 브릿지를 통한 **WSL에서 음성 모드** ([#4317](https://github.com/NousResearch/hermes-agent/pull/4317))
- **Homebrew 패키징** 준비 ([#4099](https://github.com/NousResearch/hermes-agent/pull/4099))
- 포크에서의 워크플로우 실패를 방지하기 위한 **CI 포크 조건** ([#4107](https://github.com/NousResearch/hermes-agent/pull/4107))

---

## 🐛 주요 버그 수정

- **게이트웨이 승인이 에이전트 스레드를 차단** — 이제 승인이 CLI처럼 에이전트 스레드를 차단하여 도구 결과 손실 방지 ([#4557](https://github.com/NousResearch/hermes-agent/pull/4557), closes [#4542](https://github.com/NousResearch/hermes-agent/issues/4542))
- API 연결 해제로 인한 **압축 데스 스파이럴** — 루프 대신 감지 및 중지 ([#4750](https://github.com/NousResearch/hermes-agent/pull/4750), closes [#2153](https://github.com/NousResearch/hermes-agent/issues/2153))
- 도구 사용 턴 간 **Anthropic 사고 블록 손실** ([#4626](https://github.com/NousResearch/hermes-agent/pull/4626))
- `-p` 플래그에서 **프로필 모델 설정 무시** — model.model이 이제 model.default로 올바르게 승격 ([#4160](https://github.com/NousResearch/hermes-agent/pull/4160), closes [#4486](https://github.com/NousResearch/hermes-agent/issues/4486))
- 응답과 입력 영역 사이의 **CLI 빈 공간** ([#4412](https://github.com/NousResearch/hermes-agent/pull/4412), [#4359](https://github.com/NousResearch/hermes-agent/pull/4359), closes [#4398](https://github.com/NousResearch/hermes-agent/issues/4398))
- 파일 참조 대신 슬래시 명령으로 처리된 **드래그된 파일 경로** ([#4533](https://github.com/NousResearch/hermes-agent/pull/4533)) — @rolme
- 사용자 대면 응답에 노출된 **고아 `</think>` 태그** ([#4311](https://github.com/NousResearch/hermes-agent/pull/4311), closes [#4285](https://github.com/NousResearch/hermes-agent/issues/4285))
- **OpenAI SDK `is_closed`**가 속성이 아닌 메서드 — 잘못된 양성 클라이언트 종료 ([#4416](https://github.com/NousResearch/hermes-agent/pull/4416), closes [#4377](https://github.com/NousResearch/hermes-agent/issues/4377))
- **MCP OAuth 서버**가 정상적으로 성능 저하되는 대신 Hermes 시작을 차단할 수 있었음 ([#4757](https://github.com/NousResearch/hermes-agent/pull/4757), closes [#4462](https://github.com/NousResearch/hermes-agent/issues/4462))
- HTTP 서버가 있는 종료 시 **MCP 이벤트 루프 종료** ([#4757](https://github.com/NousResearch/hermes-agent/pull/4757), closes [#2537](https://github.com/NousResearch/hermes-agent/issues/2537))
- 잘못된 엔드포인트로 하드코딩된 **Alibaba 프로바이더** ([#4133](https://github.com/NousResearch/hermes-agent/pull/4133), closes [#3912](https://github.com/NousResearch/hermes-agent/issues/3912))
- 누락된 설정 옵션 **Slack reply_in_thread** ([#4643](https://github.com/NousResearch/hermes-agent/pull/4643), closes [#2662](https://github.com/NousResearch/hermes-agent/issues/2662))
- **조용한 모드 종료 코드** — 성공적인 `-q` 쿼리가 더 이상 비정상 종료하지 않음 ([#4613](https://github.com/NousResearch/hermes-agent/pull/4613), closes [#4601](https://github.com/NousResearch/hermes-agent/issues/4601))
- 문서 사이트에서 backdrop-filter 문제로 닫기 버튼만 표시되는 **모바일 사이드바** ([#4207](https://github.com/NousResearch/hermes-agent/pull/4207)) — @xsmyile
- stale-branch squash merge로 되돌려진 **설정 복원** — `_config_version` 수정 ([#4440](https://github.com/NousResearch/hermes-agent/pull/4440))

---

## 🧪 테스트

- **Telegram 게이트웨이 E2E 테스트** — Telegram 어댑터용 전체 통합 테스트 스위트 ([#4497](https://github.com/NousResearch/hermes-agent/pull/4497)) — @pefontana
- **11개의 실제 테스트 실패 수정** 및 sys.modules 연쇄 오염 해결 ([#4570](https://github.com/NousResearch/hermes-agent/pull/4570))
- 훅, 플러그인, 스킬 테스트 전반에 걸쳐 **7개의 CI 실패 해결** ([#3936](https://github.com/NousResearch/hermes-agent/pull/3936))
- CI 호환성을 위해 **Codex 401 새로고침 테스트** 업데이트 ([#4166](https://github.com/NousResearch/hermes-agent/pull/4166))
- **오래된 OPENAI_BASE_URL 테스트** 수정 ([#4217](https://github.com/NousResearch/hermes-agent/pull/4217))

---

## 📚 문서

- **포괄적인 문서 감사** — 21개 파일에 걸쳐 9개의 HIGH 및 20개 이상의 MEDIUM 격차 수정 ([#4087](https://github.com/NousResearch/hermes-agent/pull/4087))
- **사이트 네비게이션 재구성** — 기능 및 플랫폼을 최상위로 승격 ([#4116](https://github.com/NousResearch/hermes-agent/pull/4116))
- API 서버 및 Open WebUI용 **도구 진행 스트리밍** 문서화 ([#4138](https://github.com/NousResearch/hermes-agent/pull/4138))
- **Telegram 웹훅 모드** 문서화 ([#4089](https://github.com/NousResearch/hermes-agent/pull/4089))
- 컨텍스트 길이 경고가 포함된 **로컬 LLM 프로바이더 가이드** ([#4294](https://github.com/NousResearch/hermes-agent/pull/4294))
- `WHATSAPP_ALLOW_ALL_USERS` 문서화와 함께 **WhatsApp 허용 목록 동작** 명확화 ([#4293](https://github.com/NousResearch/hermes-agent/pull/4293))
- **Slack 설정 옵션** — Slack 문서에 새로운 설정 섹션 ([#4644](https://github.com/NousResearch/hermes-agent/pull/4644))
- **터미널 백엔드 섹션** 확장 + 문서 빌드 수정 ([#4016](https://github.com/NousResearch/hermes-agent/pull/4016))
- 통합 설정 흐름에 맞게 **프로바이더 추가 가이드** 업데이트 ([#4201](https://github.com/NousResearch/hermes-agent/pull/4201))
- **ACP Zed 설정** 수정 ([#4743](https://github.com/NousResearch/hermes-agent/pull/4743))
- 일반적인 워크플로우 및 문제 해결을 위한 **커뮤니티 FAQ** 항목 ([#4797](https://github.com/NousResearch/hermes-agent/pull/4797))
- 문서 사이트의 **스킬 탐색 및 검색 페이지** ([#4500](https://github.com/NousResearch/hermes-agent/pull/4500)) — @IAvecilla

---

## 👥 기여자

### 코어
- **@teknium1** — 모든 하위 시스템에 걸친 135개의 커밋

### 주요 커뮤니티 기여자
- **@kshitijk4poor** — 13개의 커밋: 설정 중 allowed_users 보존 ([#4551](https://github.com/NousResearch/hermes-agent/pull/4551)), 및 다양한 수정
- **@erosika** — 12개의 커밋: 메모리 프로바이더 플러그인으로 Honcho 완전 통합 동등성 복원 ([#4355](https://github.com/NousResearch/hermes-agent/pull/4355))
- **@pefontana** — 9개의 커밋: Telegram 게이트웨이 E2E 테스트 스위트 ([#4497](https://github.com/NousResearch/hermes-agent/pull/4497))
- **@bcross** — 5개의 커밋: Docker 컨테이너 이미지 최적화 ([#4034](https://github.com/NousResearch/hermes-agent/pull/4034))
- **@SHL0MS** — 4개의 커밋: NO_COLOR/TERM=dumb 지원 ([#4079](https://github.com/NousResearch/hermes-agent/pull/4079)), ascii-video 스킬 업데이트 ([#4054](https://github.com/NousResearch/hermes-agent/pull/4054)), research-paper-writing 스킬 ([#4654](https://github.com/NousResearch/hermes-agent/pull/4654))

### 모든 기여자
@0xbyt4, @arasovic, @Bartok9, @bcross, @binhnt92, @camden-lowrance, @curtitoo, @Dakota, @Dave Tist, @Dean Kerr, @devorun, @dieutx, @Dilee, @el-analista, @erosika, @Gutslabs, @IAvecilla, @Jack, @Johannnnn506, @kshitijk4poor, @Laura Batalha, @Leegenux, @Lume, @MacroAnarchy, @maymuneth, @memosr, @NexVeridian, @Nick, @nils010485, @pefontana, @Penov, @rolme, @SHL0MS, @txchen, @xsmyile

### 커뮤니티에서 해결된 이슈
@acsezen ([#2537](https://github.com/NousResearch/hermes-agent/issues/2537)), @arasovic ([#4285](https://github.com/NousResearch/hermes-agent/issues/4285)), @camden-lowrance ([#4462](https://github.com/NousResearch/hermes-agent/issues/4462)), @devorun ([#4601](https://github.com/NousResearch/hermes-agent/issues/4601)), @eloklam ([#4486](https://github.com/NousResearch/hermes-agent/issues/4486)), @HenkDz ([#3719](https://github.com/NousResearch/hermes-agent/issues/3719)), @hypotyposis ([#2153](https://github.com/NousResearch/hermes-agent/issues/2153)), @kazamak ([#4178](https://github.com/NousResearch/hermes-agent/issues/4178)), @lstep ([#4366](https://github.com/NousResearch/hermes-agent/issues/4366)), @Mark-Lok ([#4542](https://github.com/NousResearch/hermes-agent/issues/4542)), @NoJster ([#4421](https://github.com/NousResearch/hermes-agent/issues/4421)), @patp ([#2662](https://github.com/NousResearch/hermes-agent/issues/2662)), @pr0n ([#4601](https://github.com/NousResearch/hermes-agent/issues/4601)), @saulmc ([#4377](https://github.com/NousResearch/hermes-agent/issues/4377)), @SHL0MS ([#4060](https://github.com/NousResearch/hermes-agent/issues/4060), [#4061](https://github.com/NousResearch/hermes-agent/issues/4061), [#4066](https://github.com/NousResearch/hermes-agent/issues/4066), [#4172](https://github.com/NousResearch/hermes-agent/issues/4172), [#4277](https://github.com/NousResearch/hermes-agent/issues/4277)), @Z-Mackintosh ([#4398](https://github.com/NousResearch/hermes-agent/issues/4398))

---

**전체 변경 로그**: [v2026.3.30...v2026.4.3](https://github.com/NousResearch/hermes-agent/compare/v2026.3.30...v2026.4.3)
