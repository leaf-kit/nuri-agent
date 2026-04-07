# 새 메시징 플랫폼 추가하기

Hermes 게이트웨이에 새 메시징 플랫폼을 통합하기 위한 체크리스트입니다.
새 어댑터를 구축할 때 이 문서를 참고하세요 -- 여기에 나열된 모든 항목은
코드베이스에 실제로 존재하는 통합 지점입니다. 하나라도 누락하면
기능 결함, 기능 누락, 또는 일관성 없는 동작이 발생합니다.

---

## 1. 핵심 어댑터 (`gateway/platforms/<platform>.py`)

어댑터는 `gateway/platforms/base.py`의 `BasePlatformAdapter` 하위 클래스입니다.

### 필수 메서드

| 메서드 | 목적 |
|--------|------|
| `__init__(self, config)` | 설정 파싱, 상태 초기화. `super().__init__(config, Platform.YOUR_PLATFORM)` 호출 |
| `connect() -> bool` | 플랫폼에 연결하고 리스너를 시작. 성공 시 True 반환 |
| `disconnect()` | 리스너 중지, 연결 종료, 작업 취소 |
| `send(chat_id, text, ...) -> SendResult` | 텍스트 메시지 전송 |
| `send_typing(chat_id)` | 입력 중 표시기 전송 |
| `send_image(chat_id, image_url, caption) -> SendResult` | 이미지 전송 |
| `get_chat_info(chat_id) -> dict` | 채팅의 `{name, type, chat_id}` 반환 |

### 선택적 메서드 (기본 스텁이 base에 존재)

| 메서드 | 목적 |
|--------|------|
| `send_document(chat_id, path, caption)` | 파일 첨부 전송 |
| `send_voice(chat_id, path)` | 음성 메시지 전송 |
| `send_video(chat_id, path, caption)` | 동영상 전송 |
| `send_animation(chat_id, path, caption)` | GIF/애니메이션 전송 |
| `send_image_file(chat_id, path, caption)` | 로컬 파일에서 이미지 전송 |

### 필수 함수

```python
def check_<platform>_requirements() -> bool:
    """이 플랫폼의 의존성이 사용 가능한지 확인합니다."""
```

### 따라야 할 핵심 패턴

- `self.build_source(...)`를 사용하여 `SessionSource` 객체 구성
- `self.handle_message(event)`를 호출하여 수신 메시지를 게이트웨이로 디스패치
- base의 `MessageEvent`, `MessageType`, `SendResult` 사용
- 첨부 파일에는 `cache_image_from_bytes`, `cache_audio_from_bytes`, `cache_document_from_bytes` 사용
- 자기 자신의 메시지 필터링 (응답 루프 방지)
- 플랫폼에 동기화/에코 메시지가 있는 경우 필터링
- 모든 로그 출력에서 민감한 식별자(전화번호, 토큰) 마스킹
- 스트리밍 연결에 대해 지수 백오프 + 지터를 사용한 재연결 구현
- 플랫폼에 메시지 크기 제한이 있는 경우 `MAX_MESSAGE_LENGTH` 설정

---

## 2. 플랫폼 Enum (`gateway/config.py`)

`Platform` enum에 플랫폼을 추가합니다:

```python
class Platform(Enum):
    ...
    YOUR_PLATFORM = "your_platform"
```

`_apply_env_overrides()`에 환경 변수 로딩을 추가합니다:

```python
# Your Platform
your_token = os.getenv("YOUR_PLATFORM_TOKEN")
if your_token:
    if Platform.YOUR_PLATFORM not in config.platforms:
        config.platforms[Platform.YOUR_PLATFORM] = PlatformConfig()
    config.platforms[Platform.YOUR_PLATFORM].enabled = True
    config.platforms[Platform.YOUR_PLATFORM].token = your_token
```

플랫폼이 token/api_key를 사용하지 않는 경우 `get_connected_platforms()`를 업데이트합니다
(예: WhatsApp는 `enabled` 플래그를 사용하고, Signal은 `extra` dict를 사용).

---

## 3. 어댑터 팩토리 (`gateway/run.py`)

`_create_adapter()`에 추가합니다:

```python
elif platform == Platform.YOUR_PLATFORM:
    from gateway.platforms.your_platform import YourAdapter, check_your_requirements
    if not check_your_requirements():
        logger.warning("Your Platform: dependencies not met")
        return None
    return YourAdapter(config)
```

---

## 4. 인증 맵 (`gateway/run.py`)

`_is_user_authorized()`의 두 dict 모두에 추가합니다:

```python
platform_env_map = {
    ...
    Platform.YOUR_PLATFORM: "YOUR_PLATFORM_ALLOWED_USERS",
}
platform_allow_all_map = {
    ...
    Platform.YOUR_PLATFORM: "YOUR_PLATFORM_ALLOW_ALL_USERS",
}
```

---

## 5. 세션 소스 (`gateway/session.py`)

플랫폼에 추가 ID 필드가 필요한 경우(예: Signal의 전화번호와 함께 사용되는 UUID),
`SessionSource` 데이터클래스에 `Optional` 기본값과 함께 추가하고,
base.py의 `to_dict()`, `from_dict()`, `build_source()`를 업데이트합니다.

---

## 6. 시스템 프롬프트 힌트 (`agent/prompt_builder.py`)

에이전트가 어떤 플랫폼에 있는지 알 수 있도록 `PLATFORM_HINTS` 항목을 추가합니다:

```python
PLATFORM_HINTS = {
    ...
    "your_platform": (
        "You are on Your Platform. "
        "Describe formatting capabilities, media support, etc."
    ),
}
```

이것이 없으면 에이전트는 자신이 어떤 플랫폼에 있는지 모르고
부적절한 포맷팅을 사용할 수 있습니다(예: 마크다운을 렌더링하지 않는 플랫폼에서 마크다운 사용).

---

## 7. 도구 세트 (`toolsets.py`)

플랫폼용 이름이 지정된 도구 세트를 추가합니다:

```python
"hermes-your-platform": {
    "description": "Your Platform bot toolset",
    "tools": _HERMES_CORE_TOOLS,
    "includes": []
},
```

그리고 `hermes-gateway` 복합체에 추가합니다:

```python
"hermes-gateway": {
    "includes": [..., "hermes-your-platform"]
}
```

---

## 8. 크론 전달 (`cron/scheduler.py`)

`_deliver_result()`의 `platform_map`에 추가합니다:

```python
platform_map = {
    ...
    "your_platform": Platform.YOUR_PLATFORM,
}
```

이것이 없으면 `cronjob(action="create", deliver="your_platform", ...)`가 조용히 실패합니다.

---

## 9. 메시지 전송 도구 (`tools/send_message_tool.py`)

`send_message_tool()`의 `platform_map`에 추가합니다:

```python
platform_map = {
    ...
    "your_platform": Platform.YOUR_PLATFORM,
}
```

`_send_to_platform()`에 라우팅을 추가합니다:

```python
elif platform == Platform.YOUR_PLATFORM:
    return await _send_your_platform(pconfig, chat_id, message)
```

`_send_your_platform()`을 구현합니다 -- 전체 어댑터 없이 단일 메시지를 전송하는
독립형 비동기 함수입니다(게이트웨이 프로세스 외부의 크론 작업과
send_message 도구에서 사용).

도구 스키마의 `target` 설명에 플랫폼 예시를 포함하도록 업데이트합니다.

---

## 10. 크론잡 도구 스키마 (`tools/cronjob_tools.py`)

`deliver` 매개변수 설명과 docstring에 플랫폼을
전달 옵션으로 언급하도록 업데이트합니다.

---

## 11. 채널 디렉토리 (`gateway/channel_directory.py`)

플랫폼이 채팅을 열거할 수 없는 경우(대부분 불가능), 세션 기반
검색 목록에 추가합니다:

```python
for plat_name in ("telegram", "whatsapp", "signal", "your_platform"):
```

---

## 12. 상태 표시 (`hermes_cli/status.py`)

메시징 플랫폼 섹션의 `platforms` dict에 추가합니다:

```python
platforms = {
    ...
    "Your Platform": ("YOUR_PLATFORM_TOKEN", "YOUR_PLATFORM_HOME_CHANNEL"),
}
```

---

## 13. 게이트웨이 설정 마법사 (`hermes_cli/gateway.py`)

`_PLATFORMS` 리스트에 추가합니다:

```python
{
    "key": "your_platform",
    "label": "Your Platform",
    "emoji": "📱",
    "token_var": "YOUR_PLATFORM_TOKEN",
    "setup_instructions": [...],
    "vars": [...],
}
```

플랫폼에 커스텀 설정 로직(연결 테스트, QR 코드,
정책 선택)이 필요한 경우 `_setup_your_platform()` 함수를 추가하고
플랫폼 선택 스위치에서 라우팅합니다.

플랫폼의 "구성됨" 확인이 표준 `bool(get_env_value(token_var))`과
다른 경우 `_platform_status()`를 업데이트합니다.

---

## 14. 전화번호/ID 마스킹 (`agent/redact.py`)

플랫폼이 민감한 식별자(전화번호 등)를 사용하는 경우, `agent/redact.py`에
정규식 패턴과 마스킹 함수를 추가합니다. 이를 통해 어댑터 로그뿐만 아니라
모든 로그 출력에서 식별자가 마스킹됩니다.

---

## 15. 문서화

| 파일 | 업데이트 내용 |
|------|--------------|
| `README.md` | 기능 표 + 문서 표의 플랫폼 목록 |
| `AGENTS.md` | 게이트웨이 설명 + 환경 변수 설정 섹션 |
| `website/docs/user-guide/messaging/<platform>.md` | **신규** -- 전체 설정 가이드 (기존 플랫폼 문서를 템플릿으로 참조) |
| `website/docs/user-guide/messaging/index.md` | 아키텍처 다이어그램, 도구 세트 표, 보안 예시, 다음 단계 링크 |
| `website/docs/reference/environment-variables.md` | 플랫폼의 모든 환경 변수 |

---

## 16. 테스트 (`tests/gateway/test_<platform>.py`)

권장 테스트 커버리지:

- 플랫폼 enum이 올바른 값으로 존재하는지 확인
- `_apply_env_overrides`를 통한 환경 변수 설정 로딩
- 어댑터 초기화 (설정 파싱, 허용 목록 처리, 기본값)
- 헬퍼 함수 (마스킹, 파싱, 파일 타입 감지)
- 세션 소스 왕복 테스트 (to_dict -> from_dict)
- 인증 통합 (허용 목록 맵에 플랫폼 포함)
- 메시지 전송 도구 라우팅 (platform_map에 플랫폼 포함)

선택적이지만 가치 있는 테스트:
- 메시지 처리 흐름에 대한 비동기 테스트 (플랫폼 API 모킹)
- SSE/WebSocket 재연결 로직
- 첨부 파일 처리
- 그룹 메시지 필터링

---

## 빠른 검증

모든 구현을 완료한 후 다음으로 검증합니다:

```bash
# 모든 테스트 통과
python -m pytest tests/ -q

# 플랫폼 이름으로 grep하여 누락된 통합 지점 찾기
grep -r "telegram\|discord\|whatsapp\|slack" gateway/ tools/ agent/ cron/ hermes_cli/ toolsets.py \
  --include="*.py" -l | sort -u
# 출력의 각 파일을 확인 -- 다른 플랫폼은 언급하지만 여러분의 플랫폼이 없다면 누락된 것입니다
```
