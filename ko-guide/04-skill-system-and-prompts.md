# 강좌 04: 스킬 시스템과 프롬프트 엔지니어링

> **이 강좌에서 배우는 것**
>
> - 마크다운 파일 하나가 어떻게 에이전트의 "능력"이 되는지 이해한다
> - `prompt_builder.py`가 시스템 프롬프트를 레이어별로 조립하는 전체 과정을 파악한다
> - Anthropic 프롬프트 캐싱과 스킬 주입 전략의 관계를 학습한다
> - 조건부 스킬 활성화(`fallback_for_toolsets`, `requires_toolsets`)의 동작 원리를 분석한다
> - 프롬프트 인젝션 방어 메커니즘 18가지 패턴을 살펴본다
> - 실제로 SKILL.md를 작성하고 테스트하는 방법을 익힌다

---

## 1. 스킬이란 무엇인가

Hermes Agent에서 **스킬(Skill)** 이란 마크다운 파일(`SKILL.md`) 하나로 정의되는 에이전트의 확장 능력이다. 코드를 작성하지 않고도, 마크다운 문서에 지침을 적으면 에이전트가 그것을 읽고 행동 패턴을 습득한다.

### 스킬의 물리적 구조

```
~/.hermes/skills/
  apple/
    DESCRIPTION.md          # 카테고리 설명
    apple-notes/
      SKILL.md              # 스킬 정의 파일
    imessage/
      SKILL.md
  research/
    arxiv/
      SKILL.md
    research-paper-writing/
      SKILL.md
      references/           # 스킬이 참조하는 추가 문서
        checklists.md
        writing-guide.md
  software-development/
    test-driven-development/
      SKILL.md
```

### SKILL.md 프론트매터 해부

모든 스킬 파일은 YAML 프론트매터로 시작한다.

```yaml
---
name: apple-notes
description: Manage Apple Notes via the memo CLI on macOS
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [macos]               # OS 제한 (darwin/linux/win32)
metadata:
  hermes:
    tags: [Notes, Apple, macOS]
    related_skills: [obsidian]
prerequisites:
  commands: [memo]               # 필요한 CLI 도구
---
```

`skill_utils.py`의 `parse_frontmatter()` 함수가 이 YAML을 파싱한다:

```python
def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """YAML frontmatter를 파싱한다. CSafeLoader 우선 사용."""
    if not content.startswith("---"):
        return {}, content
    end_match = re.search(r"\n---\s*\n", content[3:])
    if not end_match:
        return {}, content
    yaml_content = content[3 : end_match.start() + 3]
    body = content[end_match.end() + 3 :]
    parsed = yaml_load(yaml_content)  # CSafeLoader 또는 SafeLoader
    return parsed if isinstance(parsed, dict) else {}, body
```

**왜 이렇게 만들었는가?** YAML 프론트매터를 사용하면 스킬의 메타데이터(이름, 플랫폼, 조건)를 본문과 분리하여 효율적으로 인덱싱할 수 있다. 전체 마크다운 본문을 읽지 않고 첫 2000자만 읽어 메타데이터를 추출한다(`[:2000]`).

---

## 2. 시스템 프롬프트 레이어 조립 과정

`prompt_builder.py`는 시스템 프롬프트를 6개 레이어로 조립한다. 각 레이어는 독립적이며 순서가 중요하다.

```
+------------------------------------------------------+
|  Layer 1: Identity (DEFAULT_AGENT_IDENTITY)           |
|  "You are Hermes Agent, an intelligent AI assistant   |
|   created by Nous Research..."                        |
+------------------------------------------------------+
|  Layer 2: Tool Guidance                               |
|  - TOOL_USE_ENFORCEMENT_GUIDANCE (GPT/Gemini 전용)    |
|  - OPENAI_MODEL_EXECUTION_GUIDANCE (GPT 전용)         |
|  - GOOGLE_MODEL_OPERATIONAL_GUIDANCE (Gemini 전용)    |
+------------------------------------------------------+
|  Layer 3: Memory & Session Guidance                   |
|  - MEMORY_GUIDANCE                                    |
|  - SESSION_SEARCH_GUIDANCE                            |
|  - SKILLS_GUIDANCE                                    |
+------------------------------------------------------+
|  Layer 4: Skills Index                                |
|  - build_skills_system_prompt()                       |
|  - 카테고리별 스킬 목록 + 설명                         |
+------------------------------------------------------+
|  Layer 5: Context Files                               |
|  - HERMES.md / .hermes.md                             |
|  - SOUL.md, AGENTS.md, .cursorrules                   |
+------------------------------------------------------+
|  Layer 6: Platform Hints                              |
|  - PLATFORM_HINTS[platform]                           |
|  - WhatsApp/Telegram/Discord/Slack/Signal/CLI별 지침  |
+------------------------------------------------------+
```

### Layer 1: Identity -- 에이전트의 정체성

```python
DEFAULT_AGENT_IDENTITY = (
    "You are Hermes Agent, an intelligent AI assistant created by Nous Research. "
    "You are helpful, knowledgeable, and direct. You assist users with a wide "
    "range of tasks including answering questions, writing and editing code, "
    "analyzing information, creative work, and executing actions via your tools. "
    ...
)
```

이 레이어는 **절대 변하지 않는** 불변 접두사다. Anthropic의 프롬프트 캐싱에서 캐시 적중률을 극대화하려면 시스템 프롬프트의 앞부분이 안정적이어야 한다.

### Layer 2: Tool Guidance -- 모델별 맞춤 지침

모델명을 검사하여 조건부로 주입한다:

```python
TOOL_USE_ENFORCEMENT_MODELS = ("gpt", "codex", "gemini", "gemma", "grok")
DEVELOPER_ROLE_MODELS = ("gpt-5", "codex")
```

GPT 계열은 "약속만 하고 실행하지 않는" 경향이 있어 명시적 강제 지침이 필요하다:

> "Every response should either (a) contain tool calls that make progress,
> or (b) deliver a final result to the user."

**왜 이렇게 만들었는가?** 모든 LLM이 동일하게 도구를 사용하지 않는다. Claude는 도구 호출에 적극적이지만, GPT 계열은 "Let me do that" 이라고만 말하고 실제 호출을 생략하는 경우가 잦다. Gemini는 상대 경로를 사용하거나 라이브러리 존재를 가정하는 실패 패턴이 있다. 모델별로 보정 지침을 주입하는 것이 핵심이다.

### Layer 3: Memory & Session Guidance

```python
MEMORY_GUIDANCE = (
    "You have persistent memory across sessions. Save durable facts using the memory "
    "tool: user preferences, environment details, tool quirks, and stable conventions. "
    ...
    "Do NOT save task progress, session outcomes, completed-work logs, or temporary TODO "
    "state to memory; use session_search to recall those from past transcripts."
)
```

이 레이어는 에이전트가 메모리를 **언제** 저장하고 **무엇을** 저장해야 하는지를 규정한다.

### Layer 4: Skills Index

`build_skills_system_prompt()`가 스킬 디렉토리를 스캔하여 인덱스를 생성한다:

```
## Skills (mandatory)
Before replying, scan the skills below. If one clearly matches your task,
load it with skill_view(name) and follow its instructions.

<available_skills>
  apple: Apple ecosystem tools
    - apple-notes: Manage Apple Notes via the memo CLI on macOS
    - imessage: Send and receive iMessages
  research: Research and academic tools
    - arxiv: Search and download papers from arXiv
    - research-paper-writing: Write academic papers
</available_skills>
```

### Layer 5: Context Files

```python
_HERMES_MD_NAMES = (".hermes.md", "HERMES.md")
CONTEXT_FILE_MAX_CHARS = 20_000
CONTEXT_TRUNCATE_HEAD_RATIO = 0.7   # 앞쪽 70%
CONTEXT_TRUNCATE_TAIL_RATIO = 0.2   # 뒤쪽 20%
```

프로젝트 루트의 `.hermes.md` 파일을 git root까지 올라가며 검색한다. 20,000자를 초과하면 앞 70% + 뒤 20%만 유지하고 중간을 잘라낸다.

### Layer 6: Platform Hints

```python
PLATFORM_HINTS = {
    "whatsapp": "You are on a text messaging communication platform, WhatsApp. "
                "Please do not use markdown as it does not render. ...",
    "telegram": "You are on a text messaging communication platform, Telegram. ...",
    "discord":  "You are in a Discord server or group chat...",
    "cli":      "You are a CLI AI Agent. Try not to use markdown...",
    "cron":     "You are running as a scheduled cron job. There is no user present...",
}
```

**왜 이렇게 만들었는가?** 동일한 에이전트가 CLI, Telegram, Discord 등 다양한 플랫폼에서 동작한다. 마크다운이 렌더링되지 않는 WhatsApp에서 마크다운을 쓰면 가독성이 떨어진다. 플랫폼별 힌트로 응답 포맷을 자동 조정한다.

---

## 3. 프롬프트 캐싱 전략

### 핵심 원리: 스킬은 시스템 프롬프트가 아닌 사용자 메시지로 주입

스킬의 **인덱스**(목록)는 시스템 프롬프트에 포함되지만, 스킬의 **본문**(상세 지침)은 `skill_view()` 도구를 통해 사용자 메시지로 주입된다. 이 설계의 이유는 Anthropic의 프롬프트 캐싱 메커니즘과 직결된다.

```
시스템 프롬프트 (캐시됨, 안정적)          사용자 메시지 (동적)
+-----------------------------------+    +----------------------------+
| Identity                          |    | [사용자 질문]              |
| Tool Guidance                     |    |                            |
| Memory Guidance                   |    | [skill_view 결과]          |
| Skills INDEX (목록만)             |    | [도구 실행 결과]           |
| Context Files                     |    |                            |
| Platform Hints                    |    |                            |
+-----------------------------------+    +----------------------------+
     ^^ 이 부분이 캐시됨                      ^^ 이 부분은 매번 변함
```

### 캐시 무효화를 피하는 설계 원칙

1. **시스템 프롬프트의 접두사를 고정**: Identity + Tool Guidance는 세션 내내 변하지 않음
2. **스킬 인덱스는 LRU 캐시**: `_SKILLS_PROMPT_CACHE`로 최대 8개 캐시 엔트리 유지
3. **디스크 스냅샷으로 콜드 스타트 최적화**: `.skills_prompt_snapshot.json`에 스킬 메타데이터 저장

```python
_SKILLS_PROMPT_CACHE_MAX = 8
_SKILLS_PROMPT_CACHE: OrderedDict[tuple, str] = OrderedDict()

# 캐시 키는 5개 요소의 튜플
cache_key = (
    str(skills_dir.resolve()),           # 스킬 디렉토리 경로
    tuple(str(d) for d in external_dirs), # 외부 스킬 디렉토리
    tuple(sorted(available_tools)),       # 사용 가능한 도구 집합
    tuple(sorted(available_toolsets)),    # 사용 가능한 도구셋
    _platform_hint,                      # 현재 플랫폼
)
```

### 디스크 스냅샷의 유효성 검증

```python
def _build_skills_manifest(skills_dir: Path) -> dict[str, list[int]]:
    """모든 SKILL.md의 mtime/size 매니페스트를 구축."""
    manifest = {}
    for path in iter_skill_index_files(skills_dir, "SKILL.md"):
        st = path.stat()
        manifest[str(path.relative_to(skills_dir))] = [st.st_mtime_ns, st.st_size]
    return manifest
```

파일의 수정 시간(`mtime_ns`)과 크기(`size`)가 일치하면 스냅샷을 재사용한다. 스킬 파일 하나라도 변경되면 전체 재스캔이 발생한다.

**왜 이렇게 만들었는가?** 스킬 디렉토리에는 수십~수백 개의 SKILL.md가 있을 수 있다. 매 프롬프트 조립마다 모든 파일을 읽고 YAML을 파싱하면 수백ms의 지연이 발생한다. 스냅샷 + LRU 캐시로 이를 수ms 이내로 줄인다.

---

## 4. 조건부 스킬 활성화

모든 스킬이 항상 보여야 하는 것은 아니다. 특정 도구가 있을 때만 의미 있는 스킬, 또는 특정 도구가 없을 때만 보여야 하는 대체 스킬이 있다.

### 프론트매터의 조건부 필드

```yaml
---
name: my-fallback-skill
fallback_for_toolsets: [browser-automation]  # 이 도구셋이 있으면 숨김
requires_toolsets: [hermes-telegram]          # 이 도구셋이 없으면 숨김
requires_tools: [web_search]                  # 이 도구가 없으면 숨김
fallback_for_tools: [browser_navigate]        # 이 도구가 있으면 숨김
---
```

### `_skill_should_show()` 평가 로직

```python
def _skill_should_show(
    conditions: dict,
    available_tools: set[str] | None,
    available_toolsets: set[str] | None,
) -> bool:
    """조건부 활성화 규칙에 따라 스킬 표시 여부를 결정한다."""

    # 필터링 정보가 없으면 모두 표시 (하위 호환성)
    if available_tools is None and available_toolsets is None:
        return True

    at = available_tools or set()
    ats = available_toolsets or set()

    # fallback_for: 주 도구/도구셋이 사용 가능하면 숨김
    for ts in conditions.get("fallback_for_toolsets", []):
        if ts in ats:
            return False
    for t in conditions.get("fallback_for_tools", []):
        if t in at:
            return False

    # requires: 필요한 도구/도구셋이 없으면 숨김
    for ts in conditions.get("requires_toolsets", []):
        if ts not in ats:
            return False
    for t in conditions.get("requires_tools", []):
        if t not in at:
            return False

    return True
```

평가 순서를 다이어그램으로 표현하면:

```
스킬 표시 여부 결정 플로우:

  [조건 확인 시작]
       |
       v
  available_tools/toolsets == None?
       |yes                |no
       v                   v
    표시(True)     fallback_for 도구 있음?
                        |yes        |no
                        v           v
                    숨김(False)  requires 도구 없음?
                                    |yes        |no
                                    v           v
                                숨김(False)  표시(True)
```

**왜 이렇게 만들었는가?** 브라우저 자동화 도구셋이 설치되어 있으면 "수동 웹 검색" 스킬은 불필요하다. 반대로, Telegram 도구셋이 없는데 Telegram 전용 스킬을 보여주면 에이전트가 혼란을 겪는다. 이런 "도구 환경 인식"이 스킬 시스템의 핵심이다.

---

## 5. 프롬프트 인젝션 방어

`prompt_builder.py`는 외부 컨텍스트 파일(AGENTS.md, .cursorrules, SOUL.md 등)을 시스템 프롬프트에 주입하기 전에 보안 스캔을 수행한다.

### 위협 패턴 탐지 (10가지)

```python
_CONTEXT_THREAT_PATTERNS = [
    (r'ignore\s+(previous|all|above|prior)\s+instructions', "prompt_injection"),
    (r'do\s+not\s+tell\s+the\s+user', "deception_hide"),
    (r'system\s+prompt\s+override', "sys_prompt_override"),
    (r'disregard\s+(your|all|any)\s+(instructions|rules|guidelines)', "disregard_rules"),
    (r'act\s+as\s+(if|though)\s+you\s+(have\s+no|don\'t\s+have)\s+restrictions',
        "bypass_restrictions"),
    (r'<!--[^>]*(?:ignore|override|system|secret|hidden)[^>]*-->',
        "html_comment_injection"),
    (r'<\s*div\s+style\s*=\s*["\'].*display\s*:\s*none', "hidden_div"),
    (r'translate\s+.*\s+into\s+.*\s+and\s+(execute|run|eval)', "translate_execute"),
    (r'curl\s+[^\n]*\$\{?\w*(KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL|API)',
        "exfil_curl"),
    (r'cat\s+[^\n]*(\.env|credentials|\.netrc|\.pgpass)', "read_secrets"),
]
```

### 보이지 않는 유니코드 문자 탐지

```python
_CONTEXT_INVISIBLE_CHARS = {
    '\u200b',  # Zero Width Space
    '\u200c',  # Zero Width Non-Joiner
    '\u200d',  # Zero Width Joiner
    '\u2060',  # Word Joiner
    '\ufeff',  # BOM (Byte Order Mark)
    '\u202a',  # Left-to-Right Embedding
    '\u202b',  # Right-to-Left Embedding
    '\u202c',  # Pop Directional Formatting
    '\u202d',  # Left-to-Right Override
    '\u202e',  # Right-to-Left Override
}
```

### 스캔 및 차단 과정

```python
def _scan_context_content(content: str, filename: str) -> str:
    findings = []

    # 1. 보이지 않는 유니코드 검사
    for char in _CONTEXT_INVISIBLE_CHARS:
        if char in content:
            findings.append(f"invisible unicode U+{ord(char):04X}")

    # 2. 위협 패턴 매칭
    for pattern, pid in _CONTEXT_THREAT_PATTERNS:
        if re.search(pattern, content, re.IGNORECASE):
            findings.append(pid)

    # 3. 탐지 시 콘텐츠 차단
    if findings:
        logger.warning("Context file %s blocked: %s", filename, ", ".join(findings))
        return f"[BLOCKED: {filename} contained potential prompt injection ...]"

    return content
```

**왜 이렇게 만들었는가?** 프로젝트의 `.cursorrules`나 `AGENTS.md` 같은 파일은 다른 사람이 작성한 것일 수 있다. 악의적인 지침(`"ignore all previous instructions"`)이 포함되면 에이전트가 탈취될 수 있다. 이 방어 레이어는 외부 파일이 에이전트의 핵심 행동을 변경하지 못하도록 보호한다.

공격 유형별 분류:

| 카테고리 | 패턴 ID | 공격 방식 |
|---------|---------|----------|
| 직접 주입 | `prompt_injection`, `disregard_rules` | 기존 지침 무시 시도 |
| 권한 상승 | `sys_prompt_override`, `bypass_restrictions` | 제한 우회 시도 |
| 은닉 주입 | `html_comment_injection`, `hidden_div` | 보이지 않는 HTML로 지침 삽입 |
| 데이터 유출 | `exfil_curl`, `read_secrets` | 비밀키/자격증명 탈취 시도 |
| 기만 | `deception_hide` | 사용자에게 정보 은닉 지시 |
| 간접 실행 | `translate_execute` | 번역을 가장한 코드 실행 |

---

## 6. 스킬 개발 실습

### SKILL.md 작성법

최소한의 스킬 파일:

```markdown
---
name: my-custom-skill
description: 한 줄 설명 (시스템 프롬프트 인덱스에 표시됨)
version: 1.0.0
---

# My Custom Skill

## When to Use
- 사용자가 X를 요청할 때
- Y 작업이 필요할 때

## When NOT to Use
- Z 상황에서는 다른 접근법 사용

## Steps
1. 첫 번째 단계
2. 두 번째 단계
3. 결과 확인

## Common Pitfalls
- 주의할 점 1
- 주의할 점 2
```

### bundled vs optional vs hub 스킬의 차이

```
스킬의 세 가지 출처:

+-------------------+    +-------------------+    +-------------------+
| Bundled Skills    |    | Optional Skills   |    | Hub Skills        |
| ~/.hermes/skills/ |    | optional-skills/  |    | 커뮤니티 제작     |
|                   |    |                   |    |                   |
| - 기본 설치됨     |    | - 저장소에 포함   |    | - 별도 설치       |
| - 항상 인덱싱     |    | - 수동 설치 필요  |    | - external_dirs   |
| - 수정 가능       |    | - hermes skills   |    |   설정으로 등록   |
|                   |    |   install로 설치  |    |                   |
+-------------------+    +-------------------+    +-------------------+
```

**Bundled Skills**: `~/.hermes/skills/` 아래에 직접 위치. 기본 제공되며, 사용자가 자유롭게 수정 가능.

**Optional Skills**: 저장소의 `optional-skills/` 디렉토리에 존재. `hermes skills install official/<category>/<name>` 명령으로 설치.

**External/Hub Skills**: `config.yaml`의 `skills.external_dirs`에 경로를 등록하여 사용. 읽기 전용으로 인덱싱되며, 이름 충돌 시 로컬 스킬이 우선.

### 테스트 방법

```bash
# 1. 스킬 목록 확인
hermes skills list

# 2. 특정 스킬 내용 보기
hermes skills view my-custom-skill

# 3. 에이전트에서 스킬 로드 테스트
# 대화 중: "my-custom-skill 스킬을 사용해서 X를 해줘"

# 4. 스킬 비활성화/활성화
hermes skills config
```

### 에이전트가 스킬을 자동 생성하는 메커니즘

`SKILLS_GUIDANCE` 상수가 에이전트에게 스킬 자가 생성을 유도한다:

```python
SKILLS_GUIDANCE = (
    "After completing a complex task (5+ tool calls), fixing a tricky error, "
    "or discovering a non-trivial workflow, save the approach as a "
    "skill with skill_manage so you can reuse it next time.\n"
    "When using a skill and finding it outdated, incomplete, or wrong, "
    "patch it immediately with skill_manage(action='patch')..."
)
```

에이전트가 복잡한 작업(도구 호출 5회 이상)을 완료하면, 그 접근법을 `skill_manage(action='create')` 도구로 자동 저장하도록 넛지한다.

---

## 7. 스킬 vs 도구 판단 기준

스킬과 도구는 모두 에이전트의 능력을 확장하지만, 구현 방식과 적합한 용도가 다르다.

```
스킬 vs 도구 결정 트리:

  [새로운 능력이 필요하다]
          |
          v
  외부 API 호출이나 시스템 조작이 필요한가?
          |yes                          |no
          v                             v
  실시간 데이터가 필요한가?       지침/워크플로우만으로 충분한가?
          |yes        |no              |yes            |no
          v           v                v               v
     도구(Tool)    도구(Tool)       스킬(Skill)    도구+스킬 조합
     (API 연동)   (파일 조작)      (마크다운)      (하이브리드)
```

### 판단 기준 상세

| 기준 | 스킬 (SKILL.md) | 도구 (Python 함수) |
|------|-----------------|-------------------|
| **구현 방식** | 마크다운 문서 | Python 코드 |
| **실행 주체** | LLM이 지침을 읽고 기존 도구 조합 | 런타임이 직접 실행 |
| **외부 통신** | 불가 (기존 도구에 의존) | 가능 (API, 파일시스템) |
| **업데이트** | 마크다운 편집만으로 즉시 반영 | 코드 변경 + 재시작 필요 |
| **사용자 생성** | 가능 (`skill_manage`) | 플러그인 개발 필요 |
| **적합한 용도** | 워크플로우, 코딩 패턴, 체크리스트 | 데이터 조회, 시스템 제어 |

### 실전 예시

- **스킬이 적합**: "TDD 워크플로우", "PR 리뷰 체크리스트", "논문 작성 가이드"
- **도구가 적합**: "웹 검색", "파일 읽기/쓰기", "터미널 명령 실행"
- **하이브리드**: "Kubernetes 디버깅" -- 도구(kubectl 실행)와 스킬(디버깅 절차서)의 조합

---

## 핵심 정리

1. **스킬 = 마크다운 지침서**: SKILL.md의 YAML 프론트매터가 메타데이터를, 본문이 행동 지침을 정의한다

2. **프롬프트 레이어 조립**: Identity -> Tool Guidance -> Memory -> Skills Index -> Context Files -> Platform Hints 순서로 6개 레이어가 조립된다

3. **캐싱 전략**: 스킬 인덱스(목록)만 시스템 프롬프트에 넣고, 스킬 본문은 사용자 메시지로 주입하여 캐시 무효화를 최소화한다

4. **조건부 활성화**: `fallback_for_toolsets`는 "대체 도구가 있으면 숨기고", `requires_toolsets`는 "필요한 도구가 없으면 숨긴다"

5. **프롬프트 인젝션 방어**: 10개의 위협 패턴 + 10개의 보이지 않는 유니코드 문자를 탐지하여 외부 파일의 악성 지침을 차단한다

6. **스킬 자가 진화**: 에이전트가 복잡한 작업 완료 후 자동으로 스킬을 생성하고, 사용 중 문제를 발견하면 즉시 패치한다

7. **2단계 캐시**: 인메모리 LRU(8 엔트리) + 디스크 스냅샷(mtime/size 매니페스트 검증)으로 스킬 인덱싱 비용을 최소화한다
