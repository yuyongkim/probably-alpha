# legacy/kis_korea_investment — 한국투자증권 공식 샘플

## Origin
- Path: `C:/Users/USER/Desktop/한국투자증권/`
- Backup: `C:/Users/USER/Desktop/_integration_backup_20260422/한국투자증권/`

## Current Status
- KIS (한국투자증권) OpenAPI 공식 샘플 레포
- 주문/체결/조회 레퍼런스 코드

## Git
- **Not a git repo** — raw 샘플 파일 모음
- 향후 포팅 시 git 이력 없이 선택적 복사

## Port Target
- `packages/adapters/kis/` — **P0** 핵심 어댑터
- `apps/api/routers/execute/` — 주문·포지션·체결
- `apps/web/app/execute/` — 실행 UI

## Priority
- **P0** — Execute 탭 전체가 이 어댑터에 의존

## 주의
- 실전 주문이 가능한 API — `PLATFORM_OWNER_ID=self` 이전엔 **paper trading only**
- `shared.env` 에 `KIS_APP_KEY` / `KIS_APP_SECRET` 로 보관
