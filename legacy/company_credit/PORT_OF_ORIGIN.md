# legacy/company_credit — Company_Credit

## Origin
- Path: `C:/Users/USER/Desktop/Company_Credit/`
- Backup: `C:/Users/USER/Desktop/_integration_backup_20260422/Company_Credit/`

## Current Status
- **운영 중** — `sepa.yule.pics` (localhost:8200)
- **절대 건드리지 말 것** (CLAUDE.md 프로젝트 헌법)
- SEPA/OmX 파이프라인, Minervini 기반 주도주 탐지

## Git
- Branch: `main`
- Commit: `e6501b3` (fix(qa): ISSUE-001)
- Working tree: dirty (14 lines) — 진행 중 작업 존재

## Port Target
- `apps/api/routers/chartist/` — 리더 스캔, 섹터 강도, TopN
- `packages/core/` — SEPA 스코어링(sector_strength, leader_stock)
- `packages/adapters/kiwoom/` — Kiwoom EOD 수집

## Priority
- **P1 병렬**: sepa.yule.pics 운영 안정화 이후 점진 이식
- 운영과 ky-platform 은 당분간 **별도 프로세스**로 공존

## Ports
- 8200 = sepa.yule.pics (legacy, 건드리지 말 것)
