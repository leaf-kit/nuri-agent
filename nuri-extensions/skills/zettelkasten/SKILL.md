---
name: zettelkasten
description: 제텔카스텐(Zettelkasten) 방식의 원자적 노트 관리. 플리팅 노트 → 문헌 노트 → 영구 노트 워크플로우를 지원합니다.
version: 1.0.0
author: NURI Agent
license: MIT
metadata:
  hermes:
    tags: [PKM, Zettelkasten, Atomic, Note, NURI]
    related_skills: [note-capture, backlink-manager]
    requires_toolsets: [terminal, file]
---

# 제텔카스텐 (Zettelkasten)

니클라스 루만의 제텔카스텐 방법론에 기반한 원자적 노트 관리 워크플로우입니다.

## 트리거 조건

- "제텔 만들어", "영구 노트로 변환"
- "플리팅 노트 정리", "문헌 노트 만들어"
- "inbox 정리해"

## 노트 유형

| 유형 | 경로 | 설명 |
|------|------|------|
| **플리팅 노트** (Fleeting) | `notes/inbox/` | 순간적인 생각, 메모. 처리 대기 상태 |
| **문헌 노트** (Literature) | `notes/literature/` | 외부 소스 요약. 원본 참조 포함 |
| **영구 노트** (Permanent) | `notes/permanent/` | 자신의 언어로 재구성된 원자적 지식 |
| **프로젝트 노트** (Project) | `notes/projects/` | 특정 프로젝트에 종속된 실행 노트 |
| **MOC** | `notes/moc/` | 주제별 노트 연결 지도 |

## 원자적 노트 원칙

영구 노트는 다음 원칙을 따릅니다:

1. **하나의 아이디어** — 한 노트에 하나의 개념만 담습니다
2. **자기 완결적** — 다른 노트 없이도 이해할 수 있어야 합니다
3. **자신의 언어** — 출처를 복사하지 않고 자신의 말로 재구성합니다
4. **연결 필수** — 최소 1개 이상의 기존 노트와 연결합니다

## 절차

### 1. 플리팅 → 영구 노트 변환

사용자가 "inbox 정리해" 또는 "플리팅 노트 정리"를 요청하면:

```bash
# inbox의 플리팅 노트 목록
ls notes/inbox/*.md
```

각 플리팅 노트에 대해:
1. 내용을 읽고 핵심 아이디어를 추출합니다
2. 하나의 아이디어 = 하나의 영구 노트로 분리합니다
3. 자기 완결적인 문장으로 재구성합니다
4. 기존 영구 노트와의 연결점을 찾아 링크합니다
5. 프론트매터의 `status: permanent`로 설정합니다
6. `notes/permanent/`에 저장합니다
7. 원본 플리팅 노트에 처리 완료 표시를 합니다

**영구 노트 템플릿:**

```markdown
---
title: "핵심 아이디어 한 문장"
date: YYYY-MM-DD
tags: [주제태그]
type: permanent
source: "원본 플리팅 노트 또는 문헌 노트 경로"
status: permanent
---

# 핵심 아이디어 한 문장

(자신의 언어로 재구성한 설명. 2~5문장.)

## 근거

(이 아이디어를 뒷받침하는 논거나 예시)

## 연결

- [[관련-영구-노트-1]] — 연결 이유
- [[관련-영구-노트-2]] — 연결 이유

## 출처

- [[원본-문헌-노트]] 또는 원본 플리팅 노트 경로
```

### 2. 문헌 노트 생성

URL이나 논문을 전달받으면:
1. `web_extract`로 내용을 추출합니다
2. 핵심 주장, 근거, 결론을 구조화합니다
3. 원본 출처를 명시합니다
4. `notes/literature/`에 저장합니다

**문헌 노트 템플릿:**

```markdown
---
title: "출처 제목"
date: YYYY-MM-DD
tags: [문헌, 주제태그]
type: literature
source: "URL 또는 서지 정보"
author: "원저자"
status: review
---

# 출처 제목

## 핵심 주장

(저자의 핵심 주장 요약)

## 주요 내용

1. (핵심 포인트 1)
2. (핵심 포인트 2)
3. (핵심 포인트 3)

## 나의 생각

(이 내용에 대한 나의 해석이나 비판 — 영구 노트 후보)

## 출처

- 원본: [제목](URL)
- 접근일: YYYY-MM-DD
```

### 3. 제텔카스텐 상태 대시보드

```bash
echo "=== 제텔카스텐 상태 ==="
echo "플리팅 노트 (미처리): $(ls notes/inbox/*.md 2>/dev/null | wc -l)개"
echo "문헌 노트: $(ls notes/literature/*.md 2>/dev/null | wc -l)개"
echo "영구 노트: $(ls notes/permanent/*.md 2>/dev/null | wc -l)개"
echo "프로젝트 노트: $(find notes/projects/ -name '*.md' 2>/dev/null | wc -l)개"
echo "MOC: $(ls notes/moc/*.md 2>/dev/null | wc -l)개"
```

## 주의사항

- 플리팅 노트를 영구 노트로 변환할 때 원본은 삭제하지 않고 프론트매터에 `processed: true`를 추가합니다
- 영구 노트 파일명은 내용을 요약하는 짧은 구문으로 합니다 (날짜 접두사 없음)
- 하나의 플리팅 노트에서 여러 영구 노트가 나올 수 있습니다
- 변환 전에 사용자에게 추출된 아이디어 목록을 보여주고 확인을 받습니다
