# OpenClaw에서 Hermes Agent로 마이그레이션

이 가이드는 OpenClaw 설정, 메모리, 스킬, API 키를 Hermes Agent로 가져오는 방법을 다룹니다.

## 마이그레이션 3가지 방법

### 1. 자동 (최초 설정 시)

`hermes setup`을 처음 실행할 때 Hermes가 `~/.openclaw`을 감지하면, 설정이 시작되기 전에 자동으로 OpenClaw 데이터 가져오기를 제안합니다. 프롬프트를 수락하기만 하면 모든 것이 처리됩니다.

### 2. CLI 명령 (빠르고 스크립트 가능)

```bash
hermes claw migrate                      # 확인 프롬프트와 함께 전체 마이그레이션
hermes claw migrate --dry-run            # 실행될 내용 미리보기
hermes claw migrate --preset user-data   # API 키/비밀 정보 제외하고 마이그레이션
hermes claw migrate --yes                # 확인 프롬프트 건너뜀
```

**모든 옵션:**

| 플래그 | 설명 |
|------|-------------|
| `--source PATH` | OpenClaw 디렉토리 경로 (기본값: `~/.openclaw`) |
| `--dry-run` | 미리보기만 — 파일 수정 없음 |
| `--preset {user-data,full}` | 마이그레이션 프리셋 (기본값: `full`). `user-data`는 비밀 정보 제외 |
| `--overwrite` | 기존 파일 덮어쓰기 (기본값: 충돌 건너뜀) |
| `--migrate-secrets` | 허용 목록의 비밀 정보 포함 (`full` 프리셋에서 자동 활성화) |
| `--workspace-target PATH` | 워크스페이스 지침(AGENTS.md)을 이 절대 경로에 복사 |
| `--skill-conflict {skip,overwrite,rename}` | 스킬 이름 충돌 처리 방법 (기본값: `skip`) |
| `--yes`, `-y` | 확인 프롬프트 건너뜀 |

### 3. 에이전트 안내 (대화형, 미리보기 포함)

에이전트에게 마이그레이션 실행을 요청합니다:

```
> Migrate my OpenClaw setup to Hermes
```

에이전트는 `openclaw-migration` 스킬을 사용하여:
1. 먼저 dry-run을 실행하여 변경 사항을 미리봄
2. 충돌 해결에 대해 질문 (SOUL.md, 스킬 등)
3. `user-data`와 `full` 프리셋 중 선택하게 함
4. 선택한 옵션으로 마이그레이션 실행
5. 마이그레이션된 항목의 상세 요약을 출력

## 마이그레이션 대상

### `user-data` 프리셋
| 항목 | 원본 | 대상 |
|------|--------|-------------|
| SOUL.md | `~/.openclaw/workspace/SOUL.md` | `~/.hermes/SOUL.md` |
| 메모리 항목 | `~/.openclaw/workspace/MEMORY.md` | `~/.hermes/memories/MEMORY.md` |
| 사용자 프로필 | `~/.openclaw/workspace/USER.md` | `~/.hermes/memories/USER.md` |
| 스킬 | `~/.openclaw/workspace/skills/` | `~/.hermes/skills/openclaw-imports/` |
| 명령 허용 목록 | `~/.openclaw/workspace/exec_approval_patterns.yaml` | `~/.hermes/config.yaml`에 병합 |
| 메시징 설정 | `~/.openclaw/config.yaml` (TELEGRAM_ALLOWED_USERS, MESSAGING_CWD) | `~/.hermes/.env` |
| TTS 에셋 | `~/.openclaw/workspace/tts/` | `~/.hermes/tts/` |

### `full` 프리셋 (`user-data`에 추가)
| 항목 | 원본 | 대상 |
|------|--------|-------------|
| Telegram 봇 토큰 | `~/.openclaw/config.yaml` | `~/.hermes/.env` |
| OpenRouter API 키 | `~/.openclaw/.env` 또는 config | `~/.hermes/.env` |
| OpenAI API 키 | `~/.openclaw/.env` 또는 config | `~/.hermes/.env` |
| Anthropic API 키 | `~/.openclaw/.env` 또는 config | `~/.hermes/.env` |
| ElevenLabs API 키 | `~/.openclaw/.env` 또는 config | `~/.hermes/.env` |

허용 목록에 있는 이 6개의 비밀 정보만 가져옵니다. 다른 자격 증명은 건너뛰고 보고됩니다.

## 충돌 처리

기본적으로 마이그레이션은 기존 Hermes 데이터를 **덮어쓰지 않습니다**:

- **SOUL.md** — `~/.hermes/`에 이미 존재하면 건너뜀
- **메모리 항목** — 메모리가 이미 존재하면 건너뜀 (중복 방지)
- **스킬** — 동일한 이름의 스킬이 이미 존재하면 건너뜀
- **API 키** — `~/.hermes/.env`에 이미 키가 설정되어 있으면 건너뜀

충돌을 덮어쓰려면 `--overwrite`를 사용합니다. 마이그레이션은 덮어쓰기 전에 백업을 생성합니다.

스킬의 경우 `--skill-conflict rename`을 사용하여 충돌하는 스킬을 새 이름으로 가져올 수도 있습니다 (예: `skill-name-imported`).

## 마이그레이션 보고서

모든 마이그레이션(dry-run 포함)은 다음을 보여주는 보고서를 생성합니다:
- **마이그레이션된 항목** — 성공적으로 가져온 항목
- **충돌** — 이미 존재하여 건너뛴 항목
- **건너뛴 항목** — 원본에서 찾을 수 없는 항목
- **오류** — 가져오기에 실패한 항목

실행 run의 경우 전체 보고서가 `~/.hermes/migration/openclaw/<timestamp>/`에 저장됩니다.

## 문제 해결

### "OpenClaw directory not found"
마이그레이션은 기본적으로 `~/.openclaw`을 찾습니다. OpenClaw이 다른 곳에 설치되어 있으면 `--source`를 사용합니다:
```bash
hermes claw migrate --source /path/to/.openclaw
```

### "Migration script not found"
마이그레이션 스크립트는 Hermes Agent와 함께 제공됩니다. pip로 설치한 경우(git clone이 아닌) `optional-skills/` 디렉토리가 없을 수 있습니다. Skills Hub에서 스킬을 설치합니다:
```bash
hermes skills install openclaw-migration
```

### 메모리 오버플로우
OpenClaw의 MEMORY.md 또는 USER.md가 Hermes의 글자 수 제한을 초과하면, 초과 항목은 마이그레이션 보고서 디렉토리의 오버플로우 파일로 내보내집니다. 가장 중요한 항목을 수동으로 검토하여 추가할 수 있습니다.
