# 강좌 05: 메모리와 세션 관리

> **이 강좌에서 배우는 것**
>
> - SQLite 기반 세션 저장소의 스키마와 WAL 모드의 동작 원리를 이해한다
> - FTS5 전문 검색으로 과거 대화를 검색하는 메커니즘을 파악한다
> - MEMORY.md와 USER.md 기반 메모리 시스템의 구조를 학습한다
> - 컨텍스트 압축 알고리즘의 5단계를 단계별로 분석한다
> - 압축 시 세션 분할과 parent_session_id 체인의 동작을 이해한다
> - Honcho 통합의 변증법적 사용자 모델링을 살펴본다

---

## 1. 세션 DB 구조

Hermes Agent는 모든 대화 이력을 SQLite 데이터베이스(`~/.hermes/state.db`)에 저장한다. 기존의 세션별 JSONL 파일 방식을 대체한 설계다.

### 핵심 테이블 3개

```sql
-- 1. sessions: 세션 메타데이터
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    source TEXT NOT NULL,           -- 'cli', 'telegram', 'discord' 등
    user_id TEXT,
    model TEXT,
    model_config TEXT,              -- JSON 문자열
    system_prompt TEXT,
    parent_session_id TEXT,         -- 압축 시 새 세션의 부모 참조
    started_at REAL NOT NULL,
    ended_at REAL,
    end_reason TEXT,
    message_count INTEGER DEFAULT 0,
    tool_call_count INTEGER DEFAULT 0,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cache_read_tokens INTEGER DEFAULT 0,
    cache_write_tokens INTEGER DEFAULT 0,
    reasoning_tokens INTEGER DEFAULT 0,
    billing_provider TEXT,
    estimated_cost_usd REAL,
    actual_cost_usd REAL,
    title TEXT,
    FOREIGN KEY (parent_session_id) REFERENCES sessions(id)
);

-- 2. messages: 개별 메시지
CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL REFERENCES sessions(id),
    role TEXT NOT NULL,              -- 'user', 'assistant', 'tool', 'system'
    content TEXT,
    tool_call_id TEXT,
    tool_calls TEXT,                 -- JSON (도구 호출 배열)
    tool_name TEXT,
    timestamp REAL NOT NULL,
    token_count INTEGER,
    finish_reason TEXT,
    reasoning TEXT,                  -- 추론 체인 텍스트 (v6)
    reasoning_details TEXT,          -- 구조화된 추론 상세 (v6)
);

-- 3. messages_fts: 전문 검색 가상 테이블
CREATE VIRTUAL TABLE messages_fts USING fts5(
    content,
    content=messages,
    content_rowid=id
);
```

### 테이블 관계도

```
+------------------+          +------------------+
|    sessions      |  1:N     |    messages       |
|                  |--------->|                   |
| id (PK)         |          | id (PK, AUTO)     |
| source           |          | session_id (FK)   |
| parent_session_id|--+       | role              |
| title            |  |       | content           |
| started_at       |  |       | timestamp         |
| ...              |  |       | ...               |
+------------------+  |       +------------------+
       ^              |              |
       |              |              | content sync
       +--------------+       +------------------+
       (자기 참조:             | messages_fts     |
        세션 체인)             | (FTS5 가상 테이블)|
                               +------------------+
```

### WAL 모드 선택 이유

```python
self._conn.execute("PRAGMA journal_mode=WAL")
```

**왜 이렇게 만들었는가?** Hermes Agent는 다중 프로세스 환경에서 동작한다:

```
동시 접근 시나리오:

[게이트웨이 프로세스]  ---+
   - Telegram 어댑터     |
   - Discord 어댑터      +--->  state.db (WAL 모드)
   - Slack 어댑터        |
[CLI 세션]             ---+
[워크트리 에이전트]    ---+
```

WAL(Write-Ahead Logging) 모드의 장점:
- **읽기/쓰기 동시성**: 읽기 작업이 쓰기를 차단하지 않음
- **쓰기/읽기 비차단**: 쓰기 중에도 읽기 가능
- **충돌 복구**: WAL 파일로 데이터 무결성 보장

### 쓰기 경합 해결: 지터 재시도

SQLite는 단일 쓰기자만 허용하므로, 다중 프로세스가 동시에 쓸 때 경합이 발생한다. Hermes는 SQLite의 내장 busy handler 대신 애플리케이션 레벨의 지터(jitter) 재시도를 사용한다:

```python
class SessionDB:
    _WRITE_MAX_RETRIES = 15
    _WRITE_RETRY_MIN_S = 0.020   # 20ms
    _WRITE_RETRY_MAX_S = 0.150   # 150ms
    _CHECKPOINT_EVERY_N_WRITES = 50

    def _execute_write(self, fn):
        for attempt in range(self._WRITE_MAX_RETRIES):
            try:
                with self._lock:
                    self._conn.execute("BEGIN IMMEDIATE")
                    result = fn(self._conn)
                    self._conn.commit()
                # 성공: 주기적 WAL 체크포인트
                self._write_count += 1
                if self._write_count % self._CHECKPOINT_EVERY_N_WRITES == 0:
                    self._try_wal_checkpoint()
                return result
            except sqlite3.OperationalError as exc:
                if "locked" in str(exc).lower():
                    # 랜덤 지터로 convoy 효과 방지
                    jitter = random.uniform(0.020, 0.150)
                    time.sleep(jitter)
                    continue
                raise
```

**왜 이렇게 만들었는가?** SQLite의 내장 busy handler는 결정적(deterministic) 지연을 사용한다. 여러 프로세스가 동시에 대기하면 모두 같은 시점에 재시도하여 "convoy 효과"가 발생한다. 랜덤 지터는 재시도 시점을 분산시켜 자연스럽게 쓰기를 직렬화한다.

### BEGIN IMMEDIATE의 의미

```python
self._conn.execute("BEGIN IMMEDIATE")
```

일반 `BEGIN`은 첫 번째 쓰기 시점에 락을 획득하지만, `BEGIN IMMEDIATE`는 트랜잭션 시작 시점에 즉시 WAL 쓰기 락을 획득한다. 락 경합이 커밋 시점이 아닌 시작 시점에 드러나므로, 실패를 빨리 감지하고 재시도할 수 있다.

---

## 2. FTS5 전문 검색

과거 대화를 키워드로 검색하는 기능은 FTS5(Full-Text Search 5) 가상 테이블로 구현된다.

### FTS5 트리거 기반 동기화

```sql
-- 메시지 삽입 시 자동 인덱싱
CREATE TRIGGER messages_fts_insert AFTER INSERT ON messages BEGIN
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;

-- 메시지 삭제 시 인덱스에서 제거
CREATE TRIGGER messages_fts_delete AFTER DELETE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content)
        VALUES('delete', old.id, old.content);
END;

-- 메시지 업데이트 시 인덱스 갱신
CREATE TRIGGER messages_fts_update AFTER UPDATE ON messages BEGIN
    INSERT INTO messages_fts(messages_fts, rowid, content)
        VALUES('delete', old.id, old.content);
    INSERT INTO messages_fts(rowid, content) VALUES (new.id, new.content);
END;
```

**왜 이렇게 만들었는가?** FTS5의 `content=messages` 옵션은 "콘텐츠리스" 테이블을 만든다. 원본 데이터는 `messages` 테이블에만 존재하고, FTS5는 역인덱스만 유지한다. 트리거가 양쪽을 동기화하므로 데이터 중복 없이 검색 성능을 확보한다.

### 검색 쿼리 구문

`search_messages()` 메서드가 FTS5 쿼리를 지원한다:

```python
def search_messages(
    self,
    query: str,                      # FTS5 쿼리
    source_filter: List[str] = None, # 소스 필터 ('cli', 'telegram' 등)
    exclude_sources: List[str] = None,
    role_filter: List[str] = None,   # 역할 필터 ('user', 'assistant')
    limit: int = 20,
    offset: int = 0,
) -> List[Dict[str, Any]]:
```

지원하는 FTS5 쿼리 예시:

| 쿼리 | 의미 |
|------|------|
| `docker deployment` | "docker"와 "deployment" 모두 포함 |
| `"exact phrase"` | 정확한 구문 매칭 |
| `docker OR kubernetes` | 둘 중 하나 포함 |
| `python NOT java` | "python" 포함, "java" 제외 |
| `deploy*` | "deploy"로 시작하는 단어 |

### 검색 결과에 맥락 포함

검색 결과는 단순히 매칭된 메시지만이 아니라, 해당 메시지 전후의 맥락(1개 메시지)도 함께 반환한다. 이를 통해 에이전트가 검색 결과를 올바른 맥락에서 이해할 수 있다.

---

## 3. 메모리 시스템

### MEMORY.md와 USER.md

Hermes의 기본(builtin) 메모리는 마크다운 파일 기반이다:

```
~/.hermes/
  MEMORY.md    # 에이전트가 저장한 지속적 사실
  USER.md      # 사용자 프로필/선호도
```

`MEMORY_GUIDANCE` 상수가 에이전트에게 메모리 사용법을 지시한다:

```python
MEMORY_GUIDANCE = (
    "You have persistent memory across sessions. Save durable facts using the memory "
    "tool: user preferences, environment details, tool quirks, and stable conventions.\n"
    "Prioritize what reduces future user steering -- the most valuable memory is one "
    "that prevents the user from having to correct or remind you again.\n"
    "Do NOT save task progress, session outcomes, completed-work logs, or temporary TODO "
    "state to memory; use session_search to recall those from past transcripts."
)
```

### 메모리 저장의 "넛지" 메커니즘

에이전트는 명시적 요청 없이도 자율적으로 메모리를 저장한다. 이 행동은 시스템 프롬프트의 넛지에 의해 유도된다:

```
메모리 저장 판단 흐름:

  [사용자 메시지 수신]
        |
        v
  사용자가 선호도/환경 정보를 언급했는가?
        |yes                    |no
        v                      v
  memory_tool(save)        작업 수행 중 반복 패턴 발견?
                               |yes              |no
                               v                 v
                           memory_tool(save)   무시
```

**무엇을 저장하는가:**
- 사용자 선호도: "Python 코드는 항상 type hints 사용"
- 환경 정보: "macOS, M2, Python 3.12"
- 도구 특이사항: "이 프로젝트는 pnpm을 사용"
- 안정적인 컨벤션: "커밋 메시지는 conventional commits 형식"

**무엇을 저장하지 않는가:**
- 작업 진행 상황 ("PR #42 리뷰 완료")
- 세션 결과물 ("config.yaml을 수정함")
- 임시 TODO 상태

### 메모리 프로바이더 플러그인 (v0.7.0)

v0.7.0부터 메모리 저장소를 플러그인으로 교체할 수 있다:

```
~/.hermes/plugins/memory/
  honcho/          # Honcho 기반 메모리
  retaindb/        # RetainDB 기반 메모리
  mem0/            # Mem0 기반 메모리
  holographic/     # Holographic 메모리
  hindsight/       # Hindsight 메모리
  byterover/       # ByteRover 메모리
  openviking/      # OpenViking 메모리
```

메모리 프로바이더 인터페이스:

```python
# agent/memory_provider.py (개념적 구조)
class MemoryProvider:
    def read_memory(self) -> str:
        """현재 메모리 내용을 반환"""
        ...

    def write_memory(self, content: str) -> None:
        """메모리에 내용 저장"""
        ...

    def search_memory(self, query: str) -> List[str]:
        """메모리 검색"""
        ...
```

**왜 이렇게 만들었는가?** 마크다운 파일 기반 메모리는 단순하지만 확장성에 한계가 있다. 벡터 검색, 시맨틱 검색, 클라우드 동기화 등 고급 기능이 필요한 사용자를 위해 플러그인 인터페이스를 제공한다. 기본 builtin 프로바이더는 항상 fallback으로 동작한다.

---

## 4. 컨텍스트 압축 알고리즘 5단계

`context_compressor.py`의 `ContextCompressor` 클래스가 대화가 길어질 때 자동으로 컨텍스트를 압축한다.

### 전체 흐름

```
컨텍스트 압축 5단계:

  [대화 메시지 배열]
  +----+----+----+----+----+----+----+----+----+----+
  | S  | U1 | A1 | T1 | U2 | A2 | T2 | U3 | A3 | U4 |
  +----+----+----+----+----+----+----+----+----+----+
    ^                                              ^
    시스템 프롬프트                            최신 메시지

  Phase 1: 구식 도구 결과 정리
  +----+----+----+----+----+----+----+----+----+----+
  | S  | U1 | A1 |PRND| U2 | A2 |PRND| U3 | A3 | U4 |
  +----+----+----+----+----+----+----+----+----+----+
                  ^^^^ 200자 이상 도구 결과 → 플레이스홀더

  Phase 2: 헤드 메시지 보호 (protect_first_n = 3)
  [S | U1 | A1] | ...나머지...

  Phase 3: 테일 메시지 보호 (토큰 예산 기반)
  ...나머지... | [U3 | A3 | U4]  (~20K 토큰)

  Phase 4: 중간 턴 요약
  [S | U1 | A1] | [SUMMARY] | [U3 | A3 | U4]

  Phase 5: 반복 요약 업데이트 (재압축 시)
  기존 요약 + 새 턴 → 업데이트된 요약
```

### Phase 1: 구식 도구 결과 정리 (LLM 호출 없음)

```python
def _prune_old_tool_results(self, messages, protect_tail_count):
    """오래된 도구 결과를 플레이스홀더로 교체 (비용 0)."""
    prune_boundary = len(result) - protect_tail_count
    for i in range(prune_boundary):
        msg = result[i]
        if msg.get("role") != "tool":
            continue
        if len(msg.get("content", "")) > 200:
            result[i] = {**msg, "content":
                "[Old tool output cleared to save context space]"}
    return result, pruned_count
```

**왜 이렇게 만들었는가?** 도구 결과(파일 내용, 명령어 출력)는 대화 초반에 사용되었지만 현재 시점에서는 불필요한 경우가 많다. LLM 호출 없이 문자열 교체만으로 토큰을 절약하는 "공짜" 최적화다.

### Phase 2: 헤드 메시지 보호

```python
compress_start = self.protect_first_n  # 기본값: 3
compress_start = self._align_boundary_forward(messages, compress_start)
```

시스템 프롬프트 + 첫 번째 사용자-어시스턴트 교환은 항상 보호한다. 대화의 원래 맥락과 목표를 유지하기 위해서다.

### Phase 3: 테일 메시지 보호 (토큰 예산 기반)

```python
def _find_tail_cut_by_tokens(self, messages, head_end, token_budget=None):
    """뒤에서부터 토큰 예산만큼 메시지를 보호."""
    if token_budget is None:
        token_budget = self.tail_token_budget  # threshold * target_ratio

    for i in range(n - 1, head_end - 1, -1):
        msg_tokens = len(content) // 4 + 10  # 대략적 토큰 추정
        if accumulated + msg_tokens > token_budget and (n - i) >= min_tail:
            break
        accumulated += msg_tokens
        cut_idx = i

    return max(cut_idx, head_end + 1)
```

고정된 메시지 수가 아닌 **토큰 예산**으로 보호 범위를 결정한다. 짧은 메시지 20개보다 긴 코드 블록 3개가 더 많은 컨텍스트를 차지할 수 있기 때문이다.

토큰 예산 계산:

```python
self.threshold_tokens = int(context_length * threshold_percent)  # 50%
self.tail_token_budget = int(self.threshold_tokens * summary_target_ratio)  # 20%
# 예: 200K 컨텍스트 → threshold 100K → tail budget 20K 토큰
```

### Phase 4: 중간 턴 요약

LLM에게 구조화된 요약을 요청한다:

```python
prompt = """Create a structured handoff summary...

Use this exact structure:

## Goal
[What the user is trying to accomplish]

## Constraints & Preferences
[User preferences, coding style, constraints]

## Progress
### Done
[Completed work -- file paths, commands, results]
### In Progress
[Work currently underway]
### Blocked
[Any blockers or issues]

## Key Decisions
[Important technical decisions and why]

## Relevant Files
[Files read, modified, or created]

## Next Steps
[What needs to happen next]

## Critical Context
[Values, error messages, config details to preserve]
"""
```

요약 토큰 예산 계산:

```python
_MIN_SUMMARY_TOKENS = 2000       # 최소
_SUMMARY_RATIO = 0.20            # 압축 대상의 20%
_SUMMARY_TOKENS_CEILING = 12_000 # 최대

def _compute_summary_budget(self, turns_to_summarize):
    content_tokens = estimate_messages_tokens_rough(turns_to_summarize)
    budget = int(content_tokens * 0.20)
    return max(2000, min(budget, self.max_summary_tokens))
```

### Phase 5: 반복 요약 업데이트

두 번째 이후의 압축에서는 이전 요약을 업데이트한다:

```python
if self._previous_summary:
    prompt = f"""You are updating a context compaction summary.

PREVIOUS SUMMARY:
{self._previous_summary}

NEW TURNS TO INCORPORATE:
{content_to_summarize}

Update the summary... PRESERVE all existing information that is still relevant.
ADD new progress. Move items from "In Progress" to "Done" when completed.
Remove information only if it is clearly obsolete."""
```

**왜 이렇게 만들었는가?** 첫 번째 요약 후 대화가 계속되면 또 압축이 필요해진다. 매번 처음부터 요약하면 초기 맥락이 점점 희석된다. 이전 요약을 "업데이트"하면 중요한 정보가 누적 보존된다.

### 도구 호출 쌍 무결성 보장

압축 후 고아(orphan) 도구 호출/결과가 발생할 수 있다:

```python
def _sanitize_tool_pairs(self, messages):
    """고아 도구 호출/결과를 정리한다."""
    # 1. 부모 없는 도구 결과 제거
    orphaned_results = result_call_ids - surviving_call_ids
    messages = [m for m in messages
                if not (m["role"] == "tool" and m["tool_call_id"] in orphaned_results)]

    # 2. 결과 없는 도구 호출에 스텁 결과 삽입
    missing_results = surviving_call_ids - result_call_ids
    for tc in msg.get("tool_calls", []):
        if tc_id in missing_results:
            patched.append({
                "role": "tool",
                "content": "[Result from earlier conversation -- see context summary above]",
                "tool_call_id": tc_id,
            })
```

API는 모든 tool_call에 대응하는 tool result를 요구한다. 압축으로 한쪽이 사라지면 API 오류가 발생하므로, 이 정리 과정이 필수적이다.

---

## 5. 압축과 세션 분할

### parent_session_id 체인

컨텍스트 압축 시 새로운 세션이 생성되고, 이전 세션의 ID가 `parent_session_id`로 참조된다:

```
세션 체인:

session_001 (원본)
    |
    +-- parent_session_id
    |
session_002 (첫 번째 압축 후)
    |
    +-- parent_session_id
    |
session_003 (두 번째 압축 후)
```

```sql
-- 세션 계보 추적 쿼리
SELECT id, parent_session_id, started_at
FROM sessions
WHERE id = 'session_003'
UNION ALL
SELECT s.id, s.parent_session_id, s.started_at
FROM sessions s
JOIN ... -- 재귀 CTE로 체인 추적
```

### 세션 타이틀과 lineage

```python
def get_next_title_in_lineage(self, base_title: str) -> str:
    """lineage의 다음 타이틀 생성.
    예: "my session" -> "my session #2" -> "my session #3"
    """
    match = re.match(r'^(.*?) #(\d+)$', base_title)
    base = match.group(1) if match else base_title
    # 기존 번호 중 최댓값 + 1
    return f"{base} #{max_num + 1}"
```

**왜 이렇게 만들었는가?** 게이트웨이에서 하나의 대화가 수십 턴 이어지면 여러 번 압축이 발생한다. 각 압축은 새 세션을 만들지만, 사용자 관점에서는 하나의 연속된 대화다. parent_session_id 체인과 타이틀 lineage로 이 연속성을 추적한다.

---

## 6. Honcho 통합

Honcho는 변증법적(dialectical) 사용자 모델링을 제공하는 외부 메모리 시스템이다.

### 변증법적 사용자 모델링

```
Honcho의 사용자 모델 업데이트:

  [기존 사용자 모델]     [새로운 대화에서 관찰된 사실]
        |                        |
        v                        v
  +-------------------------------------------+
  | 변증법적 합성 (Dialectical Synthesis)      |
  |                                           |
  | 정(Thesis): 기존 모델                     |
  | 반(Antithesis): 새 관찰이 기존과 모순?    |
  | 합(Synthesis): 통합된 새 모델             |
  +-------------------------------------------+
              |
              v
     [업데이트된 사용자 모델]
```

### user peer / agent peer 구조

```
Honcho의 이중 에이전트 구조:

+-------------------+     +-------------------+
|   User Peer       |     |   Agent Peer      |
|   (사용자 대리)    |     |   (에이전트 대리)  |
|                   |     |                   |
| - 사용자 행동 관찰 |     | - 에이전트 성능    |
| - 선호도 추론     |     |   모니터링         |
| - 피드백 수집     |     | - 응답 품질 평가   |
+-------------------+     +-------------------+
        |                          |
        v                          v
   [사용자 모델]              [에이전트 모델]
        |                          |
        +----------+---------------+
                   |
                   v
          [통합 컨텍스트]
          (시스템 프롬프트에 주입)
```

### 비동기 프리페치 패턴

게이트웨이에서 Honcho 데이터는 비동기로 프리페치된다:

```python
# 개념적 패턴 (gateway/run.py에서)
# 메시지 수신 시 즉시 Honcho 데이터 프리페치 시작
honcho_future = asyncio.ensure_future(honcho_manager.prefetch(user_id))

# 에이전트 응답 생성 전에 프리페치 결과 사용
honcho_context = await honcho_future
```

**왜 이렇게 만들었는가?** Honcho API 호출은 네트워크 지연이 있다. 메시지 수신과 동시에 프리페치를 시작하면, 에이전트가 프롬프트를 조립할 때 이미 데이터가 준비되어 있다. 체감 지연을 최소화하는 패턴이다.

---

## 7. 실전 팁

### 메모리 최적화

1. **메모리 정리**: `hermes memory edit`으로 MEMORY.md를 직접 편집. 중복되거나 오래된 항목 제거

2. **카테고리화**: 메모리 내용을 주제별로 정리하면 에이전트가 더 잘 활용

```markdown
## Environment
- OS: macOS Sonoma, M2 Max
- Python: 3.12, uv for package management
- Node: v22, pnpm

## Coding Preferences
- Always use type hints
- Prefer functional style
- Test with pytest + hypothesis
```

3. **session_search 활용**: 일회성 작업 결과는 메모리 대신 session_search로 회수

### 세션 검색 활용법

```
# CLI에서 과거 대화 검색
hermes session search "docker deployment"

# 특정 플랫폼의 대화만 검색
hermes session search "API key setup" --source telegram
```

### 컨텍스트 압축 설정 튜닝

`config.yaml`에서 압축 동작을 조정할 수 있다:

```yaml
compression:
  threshold_percent: 0.50    # 컨텍스트의 50% 도달 시 압축 트리거
  protect_first_n: 3         # 처음 3개 메시지 보호
  protect_last_n: 20         # 최소 마지막 20개 메시지 보호
  summary_target_ratio: 0.20 # 보호할 테일 비율 (20%)
```

**조정 가이드:**

| 상황 | 권장 설정 |
|------|----------|
| 긴 코딩 세션 (많은 파일 참조) | `threshold_percent: 0.60`, `summary_target_ratio: 0.30` |
| 짧은 Q&A 대화 | 기본값 유지 |
| 비용 절약 우선 | `threshold_percent: 0.40` |
| 맥락 보존 우선 | `protect_last_n: 30`, `summary_target_ratio: 0.25` |

### 압축 실패 시 쿨다운

요약 LLM 호출이 실패하면 600초(10분) 동안 재시도하지 않는다:

```python
_SUMMARY_FAILURE_COOLDOWN_SECONDS = 600

except Exception as e:
    self._summary_failure_cooldown_until = (
        time.monotonic() + _SUMMARY_FAILURE_COOLDOWN_SECONDS
    )
```

이 기간에는 중간 턴이 요약 없이 삭제된다. 요약 모델이 불안정하면 보조 모델을 `summary_model_override`로 지정하는 것이 좋다.

---

## 핵심 정리

1. **SQLite + WAL 모드**: 다중 프로세스 동시 접근을 지원하며, 지터 재시도로 쓰기 경합의 convoy 효과를 방지한다

2. **FTS5 전문 검색**: 트리거 기반 자동 인덱싱으로 모든 메시지가 검색 가능하다. 키워드, 구문, 불리언 쿼리를 지원한다

3. **메모리 = 지속적 사실**: MEMORY.md에 "사용자가 다시 말하지 않아도 되는 정보"만 저장한다. 작업 진행은 session_search로 회수한다

4. **5단계 압축**: (1) 구식 도구 결과 정리 -> (2) 헤드 보호 -> (3) 토큰 예산 기반 테일 보호 -> (4) 구조화된 중간 요약 -> (5) 반복 요약 업데이트

5. **세션 체인**: 압축 시 새 세션이 생성되고 parent_session_id로 연결된다. 하나의 대화가 여러 세션에 걸쳐 연속성을 유지한다

6. **메모리 프로바이더 플러그인**: v0.7.0부터 Honcho, Mem0, RetainDB 등 7개 외부 메모리 시스템을 플러그인으로 사용 가능하다

7. **도구 쌍 무결성**: 압축 후 고아 tool_call/tool_result 쌍을 자동으로 정리하여 API 오류를 방지한다
