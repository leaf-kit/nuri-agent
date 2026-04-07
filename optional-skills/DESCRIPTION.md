# 선택적 스킬

Nous Research에서 관리하는 공식 스킬로, **기본적으로 활성화되지 않습니다**.

이 스킬들은 hermes-agent 저장소에 포함되어 있지만, 설정 시
`~/.hermes/skills/`로 복사되지 않습니다. Skills Hub를 통해 검색할 수 있습니다:

```bash
hermes skills browse               # 모든 스킬 검색, 공식 스킬이 먼저 표시됨
hermes skills browse --source official  # 공식 선택적 스킬만 검색
hermes skills search <query>       # "official" 레이블이 붙은 선택적 스킬 검색
hermes skills install <identifier> # ~/.hermes/skills/에 복사하고 활성화
```

## 왜 선택적인가?

일부 스킬은 유용하지만 모든 사용자에게 널리 필요하지는 않습니다:

- **특수 통합** -- 특정 유료 서비스, 전문 도구
- **실험적 기능** -- 유망하지만 아직 검증되지 않음
- **무거운 의존성** -- 상당한 설정 필요 (API 키, 설치 등)

선택적으로 유지함으로써 기본 스킬 세트를 가볍게 유지하면서도,
원하는 사용자에게 엄선되고 테스트된 공식 스킬을 제공합니다.
