# 인사이트 #002: 업스트림 머지 시 마크다운 파일 보호하기

> **날짜**: 2026-04-07  
> **카테고리**: Git / 업스트림 동기화  
> **난이도**: ★★☆ (중급)

## 상황

nuri-agent는 NousResearch/hermes-agent의 포크(fork)다. 원본 저장소에 새로운 기능과 버그 수정이 계속 올라오는데, nuri-agent에서는 `*.md` 파일을 한국어로 번역하고 독자적인 문서를 추가해 두었다. 단순히 `git merge upstream/main`을 하면 원본의 영문 마크다운이 한국어 버전을 덮어쓰게 된다.

## 목표

- 원본의 **코드 변경(`.py`, `.ts`, `.yaml` 등)은 그대로 반영**
- `*.md` 파일은 **포크 쪽 버전을 유지**
- 충돌을 최소화하고 반복 가능한 워크플로우로 만들기

## 해결: `.gitattributes` + merge driver

### 1단계: upstream 리모트 추가 및 fetch

```bash
git remote add upstream https://github.com/NousResearch/hermes-agent.git
git fetch upstream main
```

### 2단계: `.gitattributes`로 마크다운 보호 설정

```bash
# .gitattributes에 한 줄 추가
echo "*.md merge=ours" >> .gitattributes

# "ours" merge driver 등록 (현재 쪽을 항상 채택)
git config merge.ours.driver true
```

`merge=ours`는 Git에게 "이 패턴의 파일은 충돌 시 항상 현재 브랜치(ours) 버전을 유지하라"고 지시한다.

### 3단계: 머지 실행

```bash
git merge upstream/main --no-edit
```

- 코드 파일: upstream 변경이 정상 머지됨
- `*.md` 파일: 포크 버전이 그대로 유지됨

### 4단계: 정리 및 push

```bash
# 임시로 추가한 .gitattributes 정리 (필요 시)
rm -f .gitattributes
git push origin main
```

## 실제 적용 결과

| 항목 | 결과 |
|------|------|
| upstream 커밋 30개 | 코드 변경 모두 반영 |
| `.md` 파일 (한국어 번역) | 포크 버전 유지 |
| 충돌 | 0건 |
| 새로 추가된 `.md` (upstream only) | 정상 추가됨 |

> **참고**: `merge=ours`는 양쪽 모두 수정한 파일에만 적용된다. upstream에만 존재하는 새 `.md` 파일은 정상적으로 추가된다.

## 반복 동기화 워크플로우

앞으로 정기적으로 upstream을 동기화할 때:

```bash
# 1. 최신 가져오기
git fetch upstream main

# 2. 마크다운 보호 설정 (매번 필요)
echo "*.md merge=ours" >> .gitattributes
git config merge.ours.driver true

# 3. 머지
git merge upstream/main --no-edit

# 4. 정리 및 push
rm -f .gitattributes
git push origin main
```

## 핵심 교훈

- **`.gitattributes`의 `merge=ours`**: 특정 파일 패턴에 대해 머지 전략을 파일 단위로 제어할 수 있다.
- **포크 관리의 핵심**: 코드는 upstream을 따르되, 문서는 독자적으로 유지하는 것이 포크의 정체성을 지키는 방법이다.
- **`merge.ours.driver true`**: 이 설정이 없으면 `merge=ours`가 동작하지 않는다. 반드시 함께 설정해야 한다.
- **새 파일은 보호 대상이 아니다**: `merge=ours`는 "양쪽 모두 수정한 파일"에만 적용되므로, upstream에서 새로 추가된 `.md`는 그대로 들어온다.
