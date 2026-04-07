# NURI Extensions

Hermes Agent 원본을 수정하지 않고 PKM 기능을 확장하는 플러그인 모듈입니다.

## 구조

```
nuri-extensions/
├── skills/                     ← PKM 특화 스킬 (SKILL.md 형식)
│   ├── note-capture/           ← 노트 캡처 자동화
│   ├── backlink-manager/       ← 백링크/MOC 관리
│   ├── weekly-review/          ← 주간 지식 리뷰
│   ├── zettelkasten/           ← 제텔카스텐 워크플로우
│   └── vault-search/           ← NURI Base 시맨틱 검색
├── tools/                      ← PKM 전용 도구
│   └── nuri_pkm_tools.py       ← registry.register() 방식
├── config/                     ← NURI 기본 설정
│   └── nuri-preset.yaml        ← PKM 최적화 설정 프리셋
└── README.md                   ← 본 문서
```

## 설치

NURI 스킬을 Hermes에 등록하려면:

```bash
# 스킬 심링크 (Hermes가 인식하는 경로에 연결)
ln -sf "$(pwd)/nuri-extensions/skills/"* ~/.hermes/skills/

# 또는 hermes skills install로 개별 설치
hermes skills install ./nuri-extensions/skills/note-capture
```

## 스킬 목록

| 스킬 | 설명 | 트리거 |
|------|------|--------|
| [note-capture](skills/note-capture/SKILL.md) | 다양한 소스에서 마크다운 노트 자동 생성 | "노트 만들어", "저장해", URL 전달 |
| [backlink-manager](skills/backlink-manager/SKILL.md) | 노트 간 백링크 분석, MOC 생성/업데이트 | "링크 정리", "MOC 업데이트" |
| [weekly-review](skills/weekly-review/SKILL.md) | 주간 지식 리뷰 리포트 자동 생성 | 크론 예약 또는 "주간 리뷰" |
| [zettelkasten](skills/zettelkasten/SKILL.md) | 제텔카스텐 방식의 원자적 노트 관리 | "제텔 만들어", "영구 노트로" |
| [vault-search](skills/vault-search/SKILL.md) | NURI Base 전체 시맨틱 검색 및 맥락 요약 | "찾아줘", "관련 노트" |

## 도구

| 도구 | 설명 |
|------|------|
| `nuri_scan_vault` | NURI Base 파일 목록/메타데이터 스캔 |
| `nuri_find_links` | 노트 간 링크 관계 분석 |
| `nuri_frontmatter` | 프론트매터 일괄 읽기/수정 |
