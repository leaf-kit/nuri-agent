# 인사이트 #001: Claude Code Max 구독과 API 키는 별개다

> **날짜**: 2026-04-07  
> **카테고리**: 환경 설정 / API 키  
> **난이도**: ★☆☆ (초급)

## 상황

Claude Code Max 요금제에 가입한 상태에서, hermes-agent(nuri-agent)의 `.env`에 Claude API 키를 넣어 바로 사용하려 했다.

## 오해

"Claude Code Max 구독자니까 Claude API도 자유롭게 쓸 수 있겠지?"

## 실제 동작

| 항목 | Claude Code Max | Anthropic API |
|------|----------------|---------------|
| 사용 범위 | Claude Code CLI/IDE 내부 전용 | 외부 앱에서 HTTP 호출 |
| 인증 방식 | Anthropic 계정 로그인 (OAuth) | API 키 (`sk-ant-...`) |
| 과금 | 월 정액 구독 | 토큰 사용량 기반 종량제 |
| hermes-agent 사용 | **불가** | **가능** |

Claude Code Max는 Claude Code CLI 안에서만 유효한 구독이다. hermes-agent 같은 외부 애플리케이션은 **별도 API 키**가 필요하다.

## 해결 방법

hermes-agent에서 Claude, GPT, Gemini를 사용하려면 각각 API 키를 발급받아 `.env`에 설정해야 한다.

```bash
# .env 예시
ANTHROPIC_API_KEY=sk-ant-...   # https://console.anthropic.com/settings/keys
OPENAI_API_KEY=sk-...          # https://platform.openai.com/api-keys
GOOGLE_API_KEY=AI...           # https://aistudio.google.com/app/apikey
GEMINI_API_KEY=AI...           # GOOGLE_API_KEY의 별칭
```

### 키 발급 요약

| 제공자 | 콘솔 URL | 환경변수 |
|--------|----------|----------|
| Anthropic (Claude) | https://console.anthropic.com/settings/keys | `ANTHROPIC_API_KEY` |
| OpenAI (GPT) | https://platform.openai.com/api-keys | `OPENAI_API_KEY` |
| Google (Gemini) | https://aistudio.google.com/app/apikey | `GOOGLE_API_KEY` |

## 핵심 교훈

- **구독 ≠ API 키**: SaaS 구독과 API 접근은 별개 과금 체계다.
- **외부 앱 연동 시**: 항상 해당 제공자의 API 콘솔에서 키를 따로 발급받아야 한다.
- **비용 주의**: API 키는 종량제이므로 hermes-agent 사용량에 따라 별도 비용이 발생한다.
