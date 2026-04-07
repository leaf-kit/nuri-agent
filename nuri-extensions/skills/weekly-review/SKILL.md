---
name: weekly-review
description: NURI Base의 주간 활동을 분석하여 지식 리뷰 리포트를 자동 생성합니다. 크론 예약으로 무인 실행 가능합니다.
version: 1.0.0
author: NURI Agent
license: MIT
metadata:
  hermes:
    tags: [PKM, Review, Report, Cron, NURI]
    related_skills: [backlink-manager, note-capture]
    requires_toolsets: [terminal, file]
---

# 주간 지식 리뷰 (Weekly Review)

NURI Base의 주간 변화를 분석하고 지식 리뷰 리포트를 생성합니다.

## 트리거 조건

- "주간 리뷰", "이번 주 정리"
- "지식 리뷰 리포트 만들어"
- 크론 예약: 매주 일요일 21:00 자동 실행

## 크론 설정

```
/cron 매주 일요일 21:00에 NURI Base 주간 리뷰 리포트를 생성해서 보여줘
```

## 절차

### 1. 주간 활동 스캔

```bash
# 이번 주 생성된 노트
find notes/ -name "*.md" -newermt "7 days ago" -type f | sort

# 이번 주 수정된 노트
find notes/ -name "*.md" -newermt "7 days ago" -not -newerBt "7 days ago" -type f | sort

# 이번 주 활동 통계
echo "생성: $(find notes/ -name '*.md' -newermt '7 days ago' -type f | wc -l)개"
echo "전체: $(find notes/ -name '*.md' -type f | wc -l)개"
```

### 2. 내용 분석

스캔된 노트들을 읽고 다음을 분석합니다:
- **주요 주제**: 이번 주 다룬 핵심 주제 3~5개
- **새로운 연결**: 이번 주 생성된 노트 간 링크
- **성장 영역**: 가장 활발하게 확장된 주제 클러스터
- **빈틈**: 참조는 있지만 아직 노트가 없는 주제

### 3. 고아 노트 점검

```bash
# 어디서도 참조되지 않는 노트 찾기
find notes/ -name "*.md" -type f | while read f; do
  basename=$(basename "$f" .md)
  grep -rl "$basename" notes/ --include="*.md" | grep -v "$f" | head -1 | grep -q . || echo "$f"
done
```

### 4. 리포트 생성

`reviews/YYYY-WNN-주간리뷰.md` 경로에 저장합니다:

```markdown
---
title: "주간 리뷰: YYYY년 N월 N주차"
date: YYYY-MM-DD
tags: [review, weekly]
type: review
---

# 주간 지식 리뷰 — YYYY년 N월 N주차

## 이번 주 요약

- 생성된 노트: N개
- 수정된 노트: N개
- 새로운 링크: N개
- 전체 노트 수: N개

## 주요 활동

### 다룬 주제
1. **주제 A** — 관련 노트 N개 (노트 목록)
2. **주제 B** — 관련 노트 N개
3. **주제 C** — 관련 노트 N개

### 이번 주 생성된 노트
| 날짜 | 노트 | 유형 | 태그 |
|------|------|------|------|
| MM-DD | [[노트명]] | article | #태그 |

## 지식 건강 진단

### 연결이 잘 된 노트 (Top 5)
1. [[노트명]] — 백링크 N개

### 고아 노트 (연결 필요)
- [[고아-노트-1]] — 연결 후보: [[후보-1]], [[후보-2]]
- [[고아-노트-2]] — 연결 후보: [[후보-1]]

### 빈틈 (아직 노트가 없는 참조)
- "주제 X" — [[노트-A]]에서 언급되었으나 노트 없음
- "주제 Y" — [[노트-B]], [[노트-C]]에서 참조

## 다음 주 제안

- [ ] 고아 노트 N개 연결하기
- [ ] "주제 X"에 대한 노트 작성
- [ ] MOC 업데이트: [[MOC-주제명]]

_자동 생성: YYYY-MM-DD HH:MM_
```

### 5. 전달

- CLI: 리포트 내용을 직접 출력
- 게이트웨이(Telegram/Discord): 요약본 전달 + 전체 리포트 파일 경로 안내

## 주의사항

- `reviews/` 디렉토리가 없으면 자동 생성합니다
- 과거 리뷰와 비교하여 성장 추이를 보여줍니다 (이전 리뷰 파일이 있을 때)
- 노트가 10개 미만이면 간략 리포트로 대체합니다
