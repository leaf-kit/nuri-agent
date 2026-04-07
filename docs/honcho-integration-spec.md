# honcho-integration-spec

Hermes Agent와 openclaw-honcho의 비교 및 Hermes 패턴을 다른 Honcho 통합에 이식하기 위한 사양서.

---

## 개요

두 개의 독립적인 Honcho 통합이 서로 다른 에이전트 런타임용으로 구축되었습니다: **Hermes Agent** (Python, 러너에 내장)와 **openclaw-honcho** (TypeScript, hook/tool API를 통한 플러그인). 두 통합 모두 동일한 Honcho 피어 패러다임 — 이중 피어 모델, `session.context()`, `peer.chat()` — 을 사용하지만, 각 계층에서 서로 다른 트레이드오프를 선택했습니다.

이 문서는 해당 트레이드오프를 매핑하고 이식 사양을 정의합니다: 런타임이나 언어에 관계없이 모든 Honcho 통합이 채택할 수 있도록 통합 비종속적 인터페이스로 명시된 Hermes 유래 패턴들의 집합입니다.

> **범위** 두 통합 모두 현재 올바르게 동작합니다. 이 사양은 차이점(delta)에 관한 것입니다 — Hermes에서 전파할 가치가 있는 패턴과 Hermes가 결국 채택해야 할 openclaw-honcho의 패턴. 이 사양은 추가적이며, 규범적이지 않습니다.

---

## 아키텍처 비교

### Hermes: 내장 러너

Honcho는 `AIAgent.__init__` 내부에서 직접 초기화됩니다. 플러그인 경계가 없습니다. 세션 관리, 컨텍스트 주입, 비동기 프리페치, CLI 화면 모두가 러너의 일급 관심사입니다. 컨텍스트는 세션당 한 번만 주입되고 (`_cached_system_prompt`에 내장) 세션 중에 다시 가져오지 않습니다 — 이는 LLM 제공자에서 프리픽스 캐시 적중률을 극대화합니다.

턴 흐름:

```
user message
  → _honcho_prefetch()       (캐시 읽기 — HTTP 없음)
  → _build_system_prompt()   (첫 번째 턴에만, 캐시됨)
  → LLM 호출
  → response
  → _honcho_fire_prefetch()  (데몬 스레드, 턴 종료)
       → prefetch_context() thread  ──┐
       → prefetch_dialectic() thread ─┴→ _context_cache / _dialectic_cache
```

### openclaw-honcho: hook 기반 플러그인

플러그인은 OpenClaw의 이벤트 버스에 hook을 등록합니다. 컨텍스트는 매 턴마다 `before_prompt_build`에서 동기적으로 가져옵니다. 메시지 캡처는 `agent_end`에서 발생합니다. 다중 에이전트 계층은 `subagent_spawned`를 통해 추적됩니다. 이 모델은 올바르지만 매 턴마다 LLM 호출 전에 차단 Honcho 왕복이 발생합니다.

턴 흐름:

```
user message
  → before_prompt_build (차단 HTTP — 매 턴)
       → session.context()
  → 시스템 프롬프트 조립
  → LLM 호출
  → response
  → agent_end hook
       → session.addMessages()
       → session.setMetadata()
```

---

## 비교 테이블

| 항목 | Hermes Agent | openclaw-honcho |
|---|---|---|
| **컨텍스트 주입 시점** | 세션당 한 번 (캐시됨). 턴 1 이후 응답 경로에서 HTTP 제로. | 매 턴, 차단. 턴마다 최신 컨텍스트를 가져오지만 지연 시간 추가. |
| **프리페치 전략** | 데몬 스레드가 턴 종료 시 실행; 다음 턴에서 캐시로부터 소비. | 없음. 프롬프트 빌드 시점에 차단 호출. |
| **변증법 (peer.chat)** | 비동기 프리페치; 결과가 다음 턴 시스템 프롬프트에 주입. | `honcho_recall` / `honcho_analyze` 도구를 통해 온디맨드. |
| **추론 수준** | 동적: 메시지 길이에 따라 스케일링. 하한 = 설정 기본값. 상한 = "high". | 도구별 고정: recall=minimal, analyze=medium. |
| **메모리 모드** | `user_memory_mode` / `agent_memory_mode`: hybrid / honcho / local. | 없음. 항상 Honcho에 기록. |
| **쓰기 빈도** | 비동기 (백그라운드 큐), 턴, 세션, N턴. | 매 agent_end 후 (제어 불가). |
| **AI 피어 아이덴티티** | `observe_me=True`, `seed_ai_identity()`, `get_ai_representation()`, SOUL.md → AI 피어. | 설정 시 에이전트 파일이 에이전트 피어에 업로드됨. 지속적 자기 관찰 없음. |
| **컨텍스트 범위** | 사용자 피어 + AI 피어 표현, 둘 다 주입. | 사용자 피어 (소유자) 표현 + 대화 요약. 컨텍스트 호출 시 `peerPerspective`. |
| **세션 명명** | 디렉토리별 / 전역 / 수동 매핑 / 제목 기반. | 플랫폼 세션 키에서 파생. |
| **다중 에이전트** | 단일 에이전트만. | `subagent_spawned`를 통한 부모 관찰자 계층. |
| **도구 화면** | 단일 `query_user_context` 도구 (온디맨드 변증법). | 6개 도구: session, profile, search, context (빠름) + recall, analyze (LLM). |
| **플랫폼 메타데이터** | 제거하지 않음. | Honcho 저장 전에 명시적으로 제거. |
| **메시지 중복 제거** | 없음. | 세션 메타데이터의 `lastSavedIndex`가 재전송 방지. |
| **프롬프트 내 CLI 화면** | 관리 명령이 시스템 프롬프트에 주입됨. 에이전트가 자체 CLI를 인식. | 주입하지 않음. |
| **아이덴티티 내 AI 피어 이름** | 설정된 경우 DEFAULT_AGENT_IDENTITY에서 "Hermes Agent"를 대체. | 미구현. |
| **QMD / 로컬 파일 검색** | 미구현. | QMD 백엔드 설정 시 패스스루 도구. |
| **워크스페이스 메타데이터** | 미구현. | 워크스페이스 메타데이터의 `agentPeerMap`이 에이전트→피어 ID를 추적. |

---

## 패턴

Hermes에서 모든 Honcho 통합에 채택할 가치가 있는 6가지 패턴입니다. 각각 통합 비종속적 인터페이스로 설명됩니다.

**Hermes 기여:**
- 비동기 프리페치 (제로 레이턴시)
- 동적 추론 수준
- 피어별 메모리 모드
- AI 피어 아이덴티티 형성
- 세션 명명 전략
- CLI 화면 주입

**openclaw-honcho 역기여 (Hermes가 채택해야 할 것):**
- `lastSavedIndex` 중복 제거
- 플랫폼 메타데이터 제거
- 다중 에이전트 관찰자 계층
- `context()`에서의 `peerPerspective`
- 계층적 도구 화면 (빠름/LLM)
- 워크스페이스 `agentPeerMap`

---

## 사양: 비동기 프리페치

### 문제

각 LLM 호출 전에 `session.context()`와 `peer.chat()`을 동기적으로 호출하면 매 턴마다 200~800ms의 Honcho 왕복 지연 시간이 추가됩니다.

### 패턴

두 호출을 각 턴 **종료** 시 비차단 백그라운드 작업으로 실행합니다. 결과를 세션 ID로 키가 지정된 세션별 캐시에 저장합니다. 다음 턴 **시작** 시 캐시에서 꺼냅니다 — HTTP는 이미 완료되었습니다. 첫 번째 턴은 콜드(빈 캐시)이며, 이후 모든 턴은 응답 경로에서 제로 레이턴시입니다.

### 인터페이스 계약

```typescript
interface AsyncPrefetch {
  // 턴 종료 시 컨텍스트 + 변증법 페치를 실행. 비차단.
  firePrefetch(sessionId: string, userMessage: string): void;

  // 턴 시작 시 캐시된 결과를 꺼냄. 캐시가 콜드이면 빈 값 반환.
  popContextResult(sessionId: string): ContextResult | null;
  popDialecticResult(sessionId: string): string | null;
}

type ContextResult = {
  representation: string;
  card: string[];
  aiRepresentation?: string;  // 활성화된 경우 AI 피어 컨텍스트
  summary?: string;           // 가져온 경우 대화 요약
};
```

### 구현 참고 사항

- **Python:** `threading.Thread(daemon=True)`. `dict[session_id, result]`에 기록 — GIL이 단순 쓰기에서 안전하게 만듦.
- **TypeScript:** `Promise`를 `Map<string, Promise<ContextResult>>`에 저장. pop 시점에 await. 아직 해결되지 않은 경우 null 반환 — 차단하지 않음.
- pop은 파괴적: 읽은 후 캐시 항목을 지워 오래된 데이터가 누적되지 않도록 함.
- 프리페치는 첫 번째 턴에서도 실행해야 함 (턴 2까지 소비되지 않더라도).

### openclaw-honcho 채택

`session.context()`를 `before_prompt_build`에서 `agent_end` 후 백그라운드 태스크로 이동합니다. 결과를 `state.contextCache`에 저장합니다. `before_prompt_build`에서 Honcho를 호출하는 대신 캐시에서 읽습니다. 캐시가 비어 있으면 (턴 1) 아무것도 주입하지 않습니다 — 프롬프트는 첫 번째 턴에서 Honcho 컨텍스트 없이도 유효합니다.

---

## 사양: 동적 추론 수준

### 문제

Honcho의 변증법 엔드포인트는 `minimal`에서 `max`까지의 추론 수준을 지원합니다. 도구별 고정 수준은 간단한 쿼리에서 예산을 낭비하고 복잡한 쿼리에서는 부족합니다.

### 패턴

사용자의 메시지에 따라 추론 수준을 동적으로 선택합니다. 설정된 기본값을 하한으로 사용합니다. 메시지 길이에 따라 상향 조정합니다. 자동 선택의 상한은 `high` — `max`는 절대 자동 선택하지 않습니다.

### 로직

```
< 120자  → 기본값 (보통 "low")
120–400자 → 기본값보다 한 단계 위 (상한 "high")
> 400자  → 기본값보다 두 단계 위 (상한 "high")
```

### 설정 키

`dialecticReasoningLevel` (문자열, 기본값 `"low"`) 추가. 이것이 하한을 설정합니다. 동적 상향 조정은 항상 그 위에 적용됩니다.

### openclaw-honcho 채택

`honcho_recall`과 `honcho_analyze`에 적용: 고정 `reasoningLevel`을 동적 선택기로 교체합니다. `honcho_recall`은 하한 `"minimal"`, `honcho_analyze`는 하한 `"medium"` 사용 — 둘 다 메시지 길이에 따라 상향 조정합니다.

---

## 사양: 피어별 메모리 모드

### 문제

사용자는 사용자 컨텍스트와 에이전트 컨텍스트가 로컬, Honcho, 또는 둘 다에 기록되는지 독립적으로 제어하고 싶어 합니다.

### 모드

| 모드 | 효과 |
|---|---|
| `hybrid` | 로컬 파일과 Honcho 모두에 기록 (기본값) |
| `honcho` | Honcho만 — 해당 로컬 파일 쓰기 비활성화 |
| `local` | 로컬 파일만 — 이 피어에 대한 Honcho 동기화 건너뜀 |

### 설정 스키마

```json
{
  "memoryMode": "hybrid",
  "userMemoryMode": "honcho",
  "agentMemoryMode": "hybrid"
}
```

해결 순서: 피어별 필드 우선 → 약칭 `memoryMode` → 기본값 `"hybrid"`.

### Honcho 동기화에 대한 효과

- `userMemoryMode=local`: 사용자 피어 메시지를 Honcho에 추가하지 않음
- `agentMemoryMode=local`: 어시스턴트 피어 메시지를 Honcho에 추가하지 않음
- 둘 다 local: `session.addMessages()` 완전히 건너뜀
- `userMemoryMode=honcho`: 로컬 USER.md 쓰기 비활성화
- `agentMemoryMode=honcho`: 로컬 MEMORY.md / SOUL.md 쓰기 비활성화

---

## 사양: AI 피어 아이덴티티 형성

### 문제

Honcho는 사용자가 말하는 것을 관찰하여 사용자의 표현을 유기적으로 구축합니다. AI 피어에도 동일한 메커니즘이 존재하지만, 에이전트 피어에 `observe_me=True`가 설정된 경우에만 가능합니다. 이 설정 없이는 에이전트 피어가 아무것도 축적하지 않습니다.

또한, 기존 페르소나 파일 (SOUL.md, IDENTITY.md)은 첫 활성화 시 AI 피어의 Honcho 표현을 시드해야 합니다.

### Part A: 에이전트 피어에 observe_me=True 설정

```typescript
await session.addPeers([
  [ownerPeer.id, { observeMe: true,  observeOthers: false }],
  [agentPeer.id, { observeMe: true,  observeOthers: true  }], // 이전에는 false
]);
```

한 줄 변경. 근본적인 변경. 이것 없이는 에이전트가 무엇을 말하든 AI 피어 표현이 비어 있습니다.

### Part B: seedAiIdentity()

```typescript
async function seedAiIdentity(
  agentPeer: Peer,
  content: string,
  source: string
): Promise<boolean> {
  const wrapped = [
    `<ai_identity_seed>`,
    `<source>${source}</source>`,
    ``,
    content.trim(),
    `</ai_identity_seed>`,
  ].join("\n");

  await agentPeer.addMessage("assistant", wrapped);
  return true;
}
```

### Part C: 설정 시 에이전트 파일 마이그레이션

`honcho setup` 중에 에이전트 자기 파일 (SOUL.md, IDENTITY.md, AGENTS.md)을 `session.uploadFile()` 대신 `seedAiIdentity()`를 통해 에이전트 피어에 업로드합니다. 이렇게 하면 콘텐츠가 Honcho의 관찰 파이프라인을 통해 라우팅됩니다.

### Part D: 아이덴티티 내 AI 피어 이름

에이전트에 설정된 이름이 있으면 주입된 시스템 프롬프트 앞에 추가합니다:

```typescript
const namePrefix = agentName ? `You are ${agentName}.\n\n` : "";
return { systemPrompt: namePrefix + "## User Memory Context\n\n" + sections };
```

### CLI 화면

```
honcho identity <file>    # 파일에서 시드
honcho identity --show    # 현재 AI 피어 표현 표시
```

---

## 사양: 세션 명명 전략

### 문제

단일 전역 세션은 모든 프로젝트가 동일한 Honcho 컨텍스트를 공유하게 합니다. 디렉토리별 세션은 사용자가 수동으로 세션 이름을 지정하지 않고도 격리를 제공합니다.

### 전략

| 전략 | 세션 키 | 사용 시점 |
|---|---|---|
| `per-directory` | CWD의 basename | 기본값. 각 프로젝트가 자체 세션을 가짐. |
| `global` | 고정 문자열 `"global"` | 단일 크로스 프로젝트 세션. |
| 수동 매핑 | 경로별 사용자 설정 | `sessions` 설정 맵이 디렉토리 basename을 재정의. |
| 제목 기반 | 정리된 세션 제목 | 에이전트가 대화 중 이름이 지정된 세션을 지원할 때. |

### 설정 스키마

```json
{
  "sessionStrategy": "per-directory",
  "sessionPeerPrefix": false,
  "sessions": {
    "/home/user/projects/foo": "foo-project"
  }
}
```

### CLI 화면

```
honcho sessions              # 모든 매핑 나열
honcho map <name>            # cwd를 세션 이름에 매핑
honcho map                   # 인수 없음 = 매핑 나열
```

해결 순서: 수동 매핑 → 세션 제목 → 디렉토리 basename → 플랫폼 키.

---

## 사양: CLI 화면 주입

### 문제

사용자가 "메모리 설정을 어떻게 변경하나요?"라고 물으면 에이전트가 환각을 일으키거나 모른다고 말합니다. 에이전트는 자체 관리 인터페이스를 알아야 합니다.

### 패턴

Honcho가 활성화되면 시스템 프롬프트에 간결한 명령 참조를 추가합니다. 300자 이내로 유지합니다.

```
# Honcho memory integration
Active. Session: {sessionKey}. Mode: {mode}.
Management commands:
  honcho status                    — 설정 + 연결 표시
  honcho mode [hybrid|honcho|local] — 메모리 모드 표시 또는 설정
  honcho sessions                  — 세션 매핑 나열
  honcho map <name>                — 디렉토리를 세션에 매핑
  honcho identity [file] [--show]  — AI 아이덴티티 시드 또는 표시
  honcho setup                     — 전체 대화형 마법사
```

---

## openclaw-honcho 체크리스트

영향도 순서:

- [ ] **비동기 프리페치** — `session.context()`를 `before_prompt_build`에서 `agent_end` 후 백그라운드 Promise로 이동
- [ ] **에이전트 피어에 observe_me=True** — `session.addPeers()`에서 한 줄 변경
- [ ] **동적 추론 수준** — 헬퍼 추가; `honcho_recall`과 `honcho_analyze`에 적용; 설정에 `dialecticReasoningLevel` 추가
- [ ] **피어별 메모리 모드** — 설정에 `userMemoryMode` / `agentMemoryMode` 추가; Honcho 동기화와 로컬 쓰기 게이팅
- [ ] **seedAiIdentity()** — 헬퍼 추가; SOUL.md / IDENTITY.md 설정 마이그레이션 시 사용
- [ ] **세션 명명 전략** — `sessionStrategy`, `sessions` 맵, `sessionPeerPrefix` 추가
- [ ] **CLI 화면 주입** — `before_prompt_build` 반환 값에 명령 참조 추가
- [ ] **honcho identity 서브커맨드** — 파일에서 시드 또는 `--show`로 현재 표현 표시
- [ ] **AI 피어 이름 주입** — `aiPeer` 이름이 설정된 경우 주입된 시스템 프롬프트 앞에 추가
- [ ] **honcho mode / sessions / map** — Hermes와 CLI 동등성

openclaw-honcho에서 이미 완료됨 (재구현 불필요): `lastSavedIndex` 중복 제거, 플랫폼 메타데이터 제거, 다중 에이전트 부모 관찰자, `context()`에서의 `peerPerspective`, 계층적 도구 화면, 워크스페이스 `agentPeerMap`, QMD 패스스루, 자체 호스팅 Honcho.

---

## nanobot-honcho 체크리스트

그린필드 통합. openclaw-honcho의 아키텍처에서 시작하여 첫날부터 모든 Hermes 패턴을 적용합니다.

### 1단계 — 핵심 정확성

- [ ] 이중 피어 모델 (소유자 + 에이전트 피어), 둘 다 `observe_me=True`
- [ ] `lastSavedIndex` 중복 제거를 통한 턴 종료 시 메시지 캡처
- [ ] Honcho 저장 전 플랫폼 메타데이터 제거
- [ ] 첫날부터 비동기 프리페치 — 차단 컨텍스트 주입을 구현하지 않음
- [ ] 첫 활성화 시 레거시 파일 마이그레이션 (USER.md → 소유자 피어, SOUL.md → `seedAiIdentity()`)

### 2단계 — 설정

- [ ] 설정 스키마: `apiKey`, `workspaceId`, `baseUrl`, `memoryMode`, `userMemoryMode`, `agentMemoryMode`, `dialecticReasoningLevel`, `sessionStrategy`, `sessions`
- [ ] 피어별 메모리 모드 게이팅
- [ ] 동적 추론 수준
- [ ] 세션 명명 전략

### 3단계 — 도구 및 CLI

- [ ] 도구 화면: `honcho_profile`, `honcho_recall`, `honcho_analyze`, `honcho_search`, `honcho_context`
- [ ] CLI: `setup`, `status`, `sessions`, `map`, `mode`, `identity`
- [ ] 시스템 프롬프트에 CLI 화면 주입
- [ ] AI 피어 이름을 에이전트 아이덴티티에 연결
