# Hermes Agent — ACP (Agent Client Protocol) 설정 가이드

Hermes Agent는 **Agent Client Protocol (ACP)** 을 지원하여 에디터 내에서
코딩 에이전트로 실행할 수 있습니다. ACP를 통해 IDE에서 Hermes에 작업을 전달하면,
Hermes가 파일 편집, 터미널 명령, 설명 등을 에디터 UI에 네이티브로 표시합니다.

---

## 사전 요구 사항

- Hermes Agent 설치 및 구성 완료 (`hermes setup` 완료)
- `~/.hermes/.env` 또는 `hermes login`을 통해 API 키 / 제공자 설정 완료
- Python 3.11+

ACP 확장 패키지 설치:

```bash
pip install -e ".[acp]"
```

---

## VS Code 설정

### 1. ACP Client 확장 프로그램 설치

VS Code를 열고 마켓플레이스에서 **ACP Client**를 설치합니다:

- `Ctrl+Shift+X` (macOS에서는 `Cmd+Shift+X`) 누르기
- **"ACP Client"** 검색
- **Install** 클릭

또는 명령줄에서 설치:

```bash
code --install-extension anysphere.acp-client
```

### 2. settings.json 구성

VS Code 설정을 엽니다 (`Ctrl+,` → JSON을 위해 `{}` 아이콘 클릭) 후 다음을 추가합니다:

```json
{
  "acpClient.agents": [
    {
      "name": "hermes-agent",
      "registryDir": "/path/to/hermes-agent/acp_registry"
    }
  ]
}
```

`/path/to/hermes-agent`를 실제 Hermes Agent 설치 경로로 변경합니다
(예: `~/.hermes/hermes-agent`).

또는, `hermes`가 PATH에 있으면 ACP Client가 레지스트리 디렉토리를 통해
자동으로 검색할 수 있습니다.

### 3. VS Code 재시작

설정 후 VS Code를 재시작합니다. 채팅/에이전트 패널의 ACP 에이전트 선택기에서
**Hermes Agent**가 표시되어야 합니다.

---

## Zed 설정

Zed는 ACP를 기본 지원합니다.

### 1. Zed 설정 구성

Zed 설정을 엽니다 (macOS에서 `Cmd+,` 또는 Linux에서 `Ctrl+,`) 후
`settings.json`에 다음을 추가합니다:

```json
{
  "agent_servers": {
    "hermes-agent": {
      "type": "custom",
      "command": "hermes",
      "args": ["acp"],
    },
  },
}
```

### 2. Zed 재시작

에이전트 패널에 Hermes Agent가 표시됩니다. 선택하여 대화를 시작하세요.

---

## JetBrains 설정 (IntelliJ, PyCharm, WebStorm 등)

### 1. ACP 플러그인 설치

- **Settings** → **Plugins** → **Marketplace** 열기
- **"ACP"** 또는 **"Agent Client Protocol"** 검색
- 설치 후 IDE 재시작

### 2. 에이전트 구성

- **Settings** → **Tools** → **ACP Agents** 열기
- **+** 를 클릭하여 새 에이전트 추가
- 레지스트리 디렉토리를 `acp_registry/` 폴더로 설정:
  `/path/to/hermes-agent/acp_registry`
- **OK** 클릭

### 3. 에이전트 사용

ACP 패널(보통 오른쪽 사이드바)을 열고 **Hermes Agent**를 선택합니다.

---

## 표시되는 내용

연결되면 에디터가 Hermes Agent에 대한 네이티브 인터페이스를 제공합니다:

### 채팅 패널
작업을 설명하고, 질문하고, 지시를 내릴 수 있는 대화형 인터페이스입니다.
Hermes가 설명과 액션으로 응답합니다.

### 파일 Diff
Hermes가 파일을 편집하면 에디터에 표준 diff가 표시됩니다. 다음을 수행할 수 있습니다:
- 개별 변경 사항 **수락**
- 원하지 않는 변경 사항 **거부**
- 적용 전 전체 diff **검토**

### 터미널 명령
Hermes가 셸 명령(빌드, 테스트, 설치)을 실행해야 할 때 에디터가 통합 터미널에
표시합니다. 설정에 따라:
- 명령이 자동으로 실행될 수 있음
- 또는 각 명령에 대해 **승인** 요청을 받을 수 있음

### 승인 흐름
잠재적으로 위험한 작업의 경우 에디터가 Hermes 진행 전에 승인을 요청합니다.
다음이 포함됩니다:
- 파일 삭제
- 셸 명령
- Git 작업

---

## 설정

ACP에서 Hermes Agent는 CLI와 **동일한 설정**을 사용합니다:

- **API 키 / 제공자**: `~/.hermes/.env`
- **에이전트 설정**: `~/.hermes/config.yaml`
- **스킬**: `~/.hermes/skills/`
- **세션**: `~/.hermes/state.db`

`hermes setup`을 실행하여 제공자를 구성하거나, `~/.hermes/.env`를
직접 편집할 수 있습니다.

### 모델 변경

`~/.hermes/config.yaml`을 편집합니다:

```yaml
model: openrouter/nous/hermes-3-llama-3.1-70b
```

또는 `HERMES_MODEL` 환경 변수를 설정합니다.

### 도구 세트

ACP 세션은 기본적으로 큐레이션된 `hermes-acp` 도구 세트를 사용합니다. 이 도구 세트는
에디터 워크플로우를 위해 설계되었으며 메시징 전달, cronjob 관리, 오디오 중심 UX 기능 등은
의도적으로 제외되어 있습니다.

---

## 문제 해결

### 에이전트가 에디터에 표시되지 않음

1. **레지스트리 경로 확인** — 에디터 설정의 `acp_registry/` 디렉토리 경로가
   올바르고 `agent.json`이 포함되어 있는지 확인합니다.
2. **`hermes`가 PATH에 있는지 확인** — 터미널에서 `which hermes`를 실행합니다.
   찾을 수 없는 경우 virtualenv를 활성화하거나 PATH에 추가해야 할 수 있습니다.
3. 설정 변경 후 **에디터를 재시작**합니다.

### 에이전트가 시작되지만 즉시 오류 발생

1. `hermes doctor`를 실행하여 설정을 확인합니다.
2. 유효한 API 키가 있는지 확인합니다: `hermes status`
3. 터미널에서 `hermes acp`를 직접 실행하여 오류 출력을 확인합니다.

### "Module not found" 오류

ACP 확장 패키지를 설치했는지 확인합니다:

```bash
pip install -e ".[acp]"
```

### 느린 응답

- ACP는 응답을 스트리밍하므로 점진적인 출력이 표시되어야 합니다. 에이전트가
  멈춘 것처럼 보이면 네트워크 연결과 API 제공자 상태를 확인하세요.
- 일부 제공자에는 속도 제한이 있습니다. 다른 모델/제공자로 전환해 보세요.

### 터미널 명령 권한 거부

에디터가 터미널 명령을 차단하는 경우 ACP Client 확장 프로그램 설정에서
자동 승인 또는 수동 승인 기본 설정을 확인하세요.

### 로그

Hermes 로그는 ACP 모드에서 실행할 때 stderr에 기록됩니다. 확인 방법:
- VS Code: **Output** 패널 → **ACP Client** 또는 **Hermes Agent** 선택
- Zed: **View** → **Toggle Terminal**에서 프로세스 출력 확인
- JetBrains: **Event Log** 또는 ACP 도구 창

자세한 로깅을 활성화할 수도 있습니다:

```bash
HERMES_LOG_LEVEL=DEBUG hermes acp
```

---

## 추가 참고 자료

- [ACP 명세](https://github.com/anysphere/acp)
- [Hermes Agent 문서](https://github.com/NousResearch/hermes-agent)
- 모든 CLI 옵션은 `hermes --help`로 확인
