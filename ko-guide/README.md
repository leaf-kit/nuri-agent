# Hermes Agent 한국어 심층 가이드

> 이 가이드는 원본 문서의 단순 번역이 아닌, Hermes Agent의 내부 구조와 동작 원리를 **강좌 형식**으로 분석한 독립 콘텐츠입니다.

---

## 강좌 목차

### 기초편

| # | 강좌 | 파일 | 내용 |
|---|------|------|------|
| 01 | [아키텍처 전체 조감도](01-architecture-overview.md) | `01-architecture-overview.md` | 프로젝트 구조, 핵심 모듈 관계, 데이터 흐름 전체 그림 |
| 02 | [에이전트 루프 심층 분석](02-agent-loop-deep-dive.md) | `02-agent-loop-deep-dive.md` | AIAgent 클래스, 대화 루프, 도구 호출 사이클, 반복 예산 관리 |
| 03 | [도구 시스템 완전 해부](03-tool-system-anatomy.md) | `03-tool-system-anatomy.md` | 자가등록 레지스트리, 도구세트, 비동기 브릿징, 도구 추가 실습 |

### 중급편

| # | 강좌 | 파일 | 내용 |
|---|------|------|------|
| 04 | [스킬 시스템과 프롬프트 엔지니어링](04-skill-system-and-prompts.md) | `04-skill-system-and-prompts.md` | 스킬 구조, 시스템 프롬프트 레이어 조립, 프롬프트 캐싱 전략 |
| 05 | [메모리와 세션 관리](05-memory-and-sessions.md) | `05-memory-and-sessions.md` | SQLite 세션 DB, FTS5 검색, 컨텍스트 압축, 메모리 영속화 |
| 06 | [게이트웨이와 멀티플랫폼](06-gateway-multiplatform.md) | `06-gateway-multiplatform.md` | 게이트웨이 아키텍처, 플랫폼 어댑터 패턴, Telegram/Discord 연동 |

### 고급편

| # | 강좌 | 파일 | 내용 |
|---|------|------|------|
| 07 | [서브에이전트와 병렬 실행](07-subagent-and-parallelism.md) | `07-subagent-and-parallelism.md` | 위임 메커니즘, 격리 전략, 병렬 워크스트림, execute_code 샌드박스 |
| 08 | [보안 모델과 방어 체계](08-security-model.md) | `08-security-model.md` | 명령어 승인, 프롬프트 인젝션 방어, 비밀 유출 차단, 컨테이너 격리 |
| 09 | [프로바이더와 모델 관리](09-provider-and-model-management.md) | `09-provider-and-model-management.md` | 멀티 프로바이더, 자격 증명 풀, 폴백 전략, 프롬프트 캐싱 비용 최적화 |
| 10 | [확장과 커스터마이징](10-extending-and-customizing.md) | `10-extending-and-customizing.md` | 스킨 엔진, 프로필 시스템, MCP 통합, ACP 에디터 통합, RL 훈련 환경 |

---

## 이 가이드의 특징

- **소스코드 기반 분석**: 실제 코드를 읽고 동작 원리를 추적한 결과물
- **다이어그램과 흐름도**: ASCII 다이어그램으로 복잡한 흐름을 시각화
- **설계 의도 해설**: "왜 이렇게 만들었는가"에 대한 분석
- **실습 예제**: 직접 따라할 수 있는 코드 예제 포함
- **함정과 주의사항**: 실제 개발 시 마주칠 수 있는 문제점 정리

## 대상 독자

- Hermes Agent를 사용하려는 한국 개발자
- 오픈소스 AI 에이전트 프레임워크의 내부 구조를 공부하고 싶은 개발자
- Hermes Agent에 기여하고 싶은 기여자
- AI 에이전트 아키텍처를 자체 프로젝트에 참고하려는 개발자

## 선수 지식

- Python 기본 문법 (클래스, 데코레이터, asyncio 개념)
- LLM API 기본 이해 (OpenAI chat completion 형식)
- 터미널/CLI 사용 경험

---

*이 강좌는 hermes-agent v0.7.0 (2026년 4월 기준) 소스코드를 기반으로 작성되었습니다.*
