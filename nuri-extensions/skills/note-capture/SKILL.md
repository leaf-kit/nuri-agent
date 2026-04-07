---
name: note-capture
description: 다양한 소스(URL, 텍스트, 음성 전사, 클립보드)에서 구조화된 마크다운 노트를 자동 생성하여 NURI Base에 저장합니다.
version: 1.0.0
author: NURI Agent
license: MIT
metadata:
  hermes:
    tags: [PKM, Note, Capture, Markdown, NURI]
    related_skills: [backlink-manager, zettelkasten]
    requires_toolsets: [terminal, file]
---

# 노트 캡처 (Note Capture)

다양한 형태의 정보를 구조화된 마크다운 노트로 변환하여 NURI Base에 저장합니다.

## 트리거 조건

사용자가 다음과 같은 요청을 할 때 이 스킬을 사용합니다:
- "이거 노트로 만들어", "저장해", "기록해"
- URL을 전달하며 "요약해서 저장해"
- 텍스트를 붙여넣으며 "정리해서 노트로"
- 음성 메모 전사 결과를 정리할 때

## 노트 템플릿

생성되는 모든 노트는 다음 프론트매터 구조를 따릅니다:

```markdown
---
title: "노트 제목"
date: YYYY-MM-DD
tags: [태그1, 태그2]
source: "출처 URL 또는 설명"
type: article | meeting | idea | reference | fleeting
status: draft | review | permanent
---

# 노트 제목

## 핵심 내용

(본문)

## 관련 노트

- [[관련-노트-1]]
- [[관련-노트-2]]
```

## 절차

### 1. 소스 유형 판별

| 입력 | 처리 방식 |
|------|----------|
| URL | `web_extract`로 내용 추출 → 핵심 요약 → 마크다운 변환 |
| 텍스트 블록 | 구조 분석 → 제목/섹션 자동 생성 → 프론트매터 부여 |
| 음성 전사 | 불필요한 구어체 제거 → 핵심 포인트 추출 → 구조화 |
| 이미지/스크린샷 | 비전 도구로 내용 추출 → 텍스트화 → 노트 생성 |

### 2. 노트 생성

```bash
# 저장 경로 규칙
# type=article  → notes/articles/YYYY-MM-DD-제목.md
# type=meeting  → notes/meetings/YYYY-MM-DD-제목.md
# type=idea     → notes/ideas/YYYY-MM-DD-제목.md
# type=reference→ notes/references/제목.md
# type=fleeting → notes/inbox/YYYY-MM-DD-제목.md
```

1. 소스에서 내용을 추출합니다
2. 핵심 내용을 요약하고 구조화합니다
3. 적절한 태그를 자동 부여합니다 (기존 태그 목록 참조)
4. 프론트매터를 포함한 마크다운 파일을 생성합니다
5. `write_file`로 적절한 경로에 저장합니다

### 3. 후처리

- 기존 노트와의 연관성을 분석하여 `관련 노트` 섹션에 링크를 추가합니다
- inbox에 저장된 fleeting 노트는 주간 리뷰 시 분류를 제안합니다

## 기존 태그 조회

노트 저장 전에 기존 태그 목록을 확인하여 일관성을 유지합니다:

```bash
# NURI Base 전체에서 사용 중인 태그 목록 추출
grep -rh "^tags:" notes/ | sed 's/tags: \[//;s/\]//;s/, /\n/g' | sort -u
```

## 주의사항

- 노트 파일명에는 한글과 하이픈만 사용합니다 (공백 → 하이픈)
- 프론트매터의 date는 항상 ISO 8601 형식 (YYYY-MM-DD)
- URL 소스의 경우 원본 URL을 source 필드에 반드시 보존합니다
- 기존 파일과 이름이 충돌하면 `-2`, `-3` 접미사를 붙입니다

## 검증

노트 생성 후:
1. 파일이 정상적으로 저장되었는지 `read_file`로 확인
2. 프론트매터 YAML이 유효한지 확인
3. 사용자에게 저장 경로와 요약을 보고
