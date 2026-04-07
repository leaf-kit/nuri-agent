---
name: backlink-manager
description: NURI Base의 노트 간 백링크를 분석하고, MOC(Map of Content)를 자동 생성/업데이트하며, 고아 노트를 발견합니다.
version: 1.0.0
author: NURI Agent
license: MIT
metadata:
  hermes:
    tags: [PKM, Backlink, MOC, Graph, NURI]
    related_skills: [note-capture, zettelkasten, vault-search]
    requires_toolsets: [terminal, file]
---

# 백링크 매니저 (Backlink Manager)

NURI Base의 노트 간 연결 관계를 분석하고 관리합니다.

## 트리거 조건

- "백링크 정리해", "링크 분석해"
- "MOC 만들어", "MOC 업데이트"
- "고아 노트 찾아", "연결 안 된 노트"
- "이 노트를 참조하는 노트 찾아"

## 핵심 기능

### 1. 링크 스캔

NURI Base 전체에서 `[[위키링크]]`와 `[마크다운](링크)` 패턴을 스캔합니다.

```bash
# 위키링크 추출 ([[...]] 형식)
grep -roh '\[\[[^]]*\]\]' notes/ | sort | uniq -c | sort -rn

# 마크다운 내부 링크 추출
grep -roh '\[.*\](\.\.*/[^)]*\.md)' notes/ | sort | uniq -c | sort -rn
```

### 2. 백링크 분석

특정 노트를 참조하는 모든 노트를 찾습니다:

```bash
# "대상노트" 를 참조하는 파일 찾기
grep -rl '대상노트' notes/ --include="*.md"
```

결과를 대상 노트의 하단에 `## 백링크` 섹션으로 업데이트합니다:

```markdown
## 백링크

이 노트를 참조하는 문서:
- [[참조-노트-1]] — "관련 맥락 발췌"
- [[참조-노트-2]] — "관련 맥락 발췌"

_마지막 업데이트: YYYY-MM-DD_
```

### 3. MOC (Map of Content) 생성

주제별 MOC 파일을 자동 생성합니다.

**절차:**
1. 노트의 태그와 제목을 분석하여 주제 클러스터를 식별합니다
2. 각 클러스터에 대한 MOC 파일을 생성합니다
3. MOC 파일에 해당 클러스터의 노트를 계층적으로 배치합니다

**MOC 템플릿:**

```markdown
---
title: "MOC: 주제명"
date: YYYY-MM-DD
tags: [MOC]
type: moc
---

# 주제명

## 개요
(이 주제에 대한 간략한 설명)

## 핵심 노트
- [[핵심-노트-1]] — 한줄 설명
- [[핵심-노트-2]] — 한줄 설명

## 관련 노트
- [[관련-노트-1]]
- [[관련-노트-2]]

## 탐구할 주제
- (아직 노트가 없는 관련 주제 제안)

_자동 생성: YYYY-MM-DD | 노트 N개 연결_
```

### 4. 고아 노트 탐지

다른 어떤 노트에서도 참조되지 않는 노트를 찾습니다:

```bash
# 모든 노트 파일 목록
find notes/ -name "*.md" -not -name "MOC-*" > /tmp/all_notes.txt

# 참조되는 노트 목록
grep -roh '\[\[[^]]*\]\]' notes/ | tr -d '[]' | sort -u > /tmp/linked_notes.txt

# 차집합 = 고아 노트
comm -23 /tmp/all_notes.txt /tmp/linked_notes.txt
```

고아 노트 발견 시 사용자에게 보고하고 연결 후보를 제안합니다.

### 5. 링크 무결성 검사

깨진 링크(존재하지 않는 노트를 참조)를 찾습니다:

```bash
# [[링크]]에서 참조하는 파일이 실제로 존재하는지 확인
grep -roh '\[\[[^]]*\]\]' notes/ | tr -d '[]' | sort -u | while read note; do
  find notes/ -name "${note}.md" | grep -q . || echo "깨진 링크: $note"
done
```

## 절차

1. `terminal`로 NURI Base의 링크 구조를 스캔합니다
2. 요청된 작업(백링크 분석/MOC 생성/고아 탐지)을 수행합니다
3. 결과를 마크다운으로 정리하여 보고합니다
4. 필요 시 노트 파일을 직접 업데이트합니다 (`write_file` 또는 `patch_file`)

## 주의사항

- MOC 파일명은 `MOC-주제명.md` 형식으로 통일합니다
- 백링크 섹션 업데이트 시 사용자가 수동 작성한 내용은 보존합니다
- 대량 업데이트 전에 변경 예정 목록을 먼저 보여주고 확인을 받습니다
- `_마지막 업데이트` 타임스탬프로 자동 생성 구간을 명시합니다
