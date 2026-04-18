# 작업 메모

## 이번 대화에서 한 일

- Market Wizards / preset 매핑 관련 작업을 이어서 복구했습니다.
- 트레이더 preset direct 매핑, runtime conditions 노출, Korea/Overview/People 페이지 연동 작업을 점검했습니다.
- `sepa/api/factory.py`에서 CSP가 Google Fonts를 막던 문제를 수정했습니다.
- `tests/api/test_factory.py`에 CSP 회귀 테스트를 추가했습니다.
- 전체 테스트를 실행했고 `python -m pytest` 기준 `124 passed`를 확인했습니다.
- 불필요한 `.omx/*` 변경과 로컬 스크린샷 산물을 정리했습니다.
- 아래 커밋을 생성했습니다.
  - `2d54ccb` `Make preset-driven wizard pages explain their runtime logic`

## 생성한 산출물

- bundle: `C:\Users\USER\Desktop\Company_Credit-2d54ccb.bundle`
- patch: `C:\Users\USER\Desktop\Company_Credit-2d54ccb.patch`

## 리포 이름 아이디어

- `wizard-of-kospi`
- `probably-alpha`

현재는 사용자가 새 원격 리포를 만든 뒤 알려주면 다음 단계를 진행하는 상태였습니다.

## 현재 상태

- 워킹트리: clean 상태였음
- 원격 저장소: 미연결 상태였음
- 다음 작업: 사용자가 만든 원격 repo 연결 후 push 또는 PR 흐름 진행

## 방금 추가된 작업 원칙

- 사용자가 대화를 이어갈수록 이 `note.md`를 계속 업데이트합니다.
- 긴 대화가 끊겨도 이 파일을 기준으로 바로 복구할 수 있게 유지합니다.
- 채팅창에는 짧게 요약하고, 상세 상태는 이 파일에 누적합니다.

## 최근 대화 추가 메모

- 사용자는 GitHub 저장소 생성 중이며, repo 이름으로 `probably-alpha`를 고려 중입니다.
- 라이선스 선택을 고민 중입니다.
- 현재 추천 방향은 프로젝트 공개 범위와 재사용 허용 수준에 따라 결정하는 것입니다.
- 새 공개 원격 저장소가 생성되었습니다: `https://github.com/yuyongkim/probably-alpha`
- 다음 단계는 로컬 저장소에 remote를 연결하고 현재 커밋을 push하는 것입니다.
- 공개 repo로 push 완료했습니다.
- compare/PR 대신 필요한 공개용 기본 문서를 직접 채우는 방향으로 진행 중입니다.
- 현재 추가 작업: 루트 `README.md` 작성 및 저장소 첫인상 정리.
- 루트 `README.md` 작성 완료, 공개 repo에 push 완료.
- 최근 공개용 정리 커밋:
  - `be8a6a5` Preserve session context in a top-level note
  - `2a11006` Give the public repo a usable front door
- GitHub compare 화면에서 `main` 과 `master` 가 서로 다른 히스토리라고 뜨는 문제를 확인했습니다.
- 원인: GitHub에서 생성된 `main` 초기 커밋과 로컬에서 push한 `master` 히스토리가 따로 시작했기 때문입니다.
- 정리 방향: 원격 `main` 을 현재 작업 히스토리와 맞추고, 이후 기본 작업 브랜치도 `main` 기준으로 정렬합니다.
- 실제 조치 완료:
  - 현재 작업 히스토리를 `main` 으로 정렬
  - 로컬 기본 브랜치를 `main` 으로 전환
  - 이후 추가 정리로 원격 `master` 브랜치 제거까지 진행 중

## 보안 점검 메모

- 사용자가 보안 점검 여부를 질문했습니다.
- 현재 결론: **기본 보안 항목 일부는 확인됐지만, 전체 보안 감사가 끝난 상태는 아님**.
- 확인된 항목:
  - `.env` 는 `.gitignore` 로 제외되어 있고 tracked 상태가 아님
  - admin 엔드포인트는 `SEPA_ADMIN_TOKEN` bearer 검증이 없으면 503, 틀리면 401 처리
  - CORS 는 wildcard 대신 명시 origin 목록 사용, credentials 비활성화
  - CSP / 보안 헤더는 적용 중
- 확인된 리스크:
  - `npm audit` 기준 **high 1건**
  - 경로: `puppeteer -> @puppeteer/browsers -> proxy-agent -> pac-proxy-agent -> get-uri -> basic-ftp@5.2.0`
  - advisory: `basic-ftp` CRLF / command injection 계열
- 아직 안 한 것:
  - Python dependency 전용 취약점 스캔
  - git 히스토리 전체 비밀값 누출 스캔
  - 배포 환경 기준 보안 점검
  - 전체 코드베이스 대상의 정식 security review

## 정식 security review 결과 (2026-04-16)

- 결론: **FAIR, but not ready for unrestricted internet exposure**
- CRITICAL: 없음
- HIGH:
  - `/api/backtest/run` 이 공개 GET 엔드포인트인데 무거운 백테스트 실행 + 결과 저장까지 수행
- MEDIUM:
  - CSP가 `unsafe-inline` 에 의존
  - `/docs` 노출 여부가 `API_HOST == 127.0.0.1` 같은 환경 휴리스틱에 묶여 있음
  - in-memory rate limiting 만 사용
- LOW:
  - 일부 요청이 글로벌 preset 상태를 직접 변경
  - admin auth 가 단일 static bearer token + plain equality 비교
  - npm tree 에 `basic-ftp@5.2.0` transitive advisory 존재
- confirmed non-findings:
  - tracked 파일 내 하드코딩된 실제 비밀값은 확인되지 않음
  - `.env` 는 ignore 중
  - `requirements.txt` 기준 `pip_audit` 는 known vulnerability 없음
- 즉시 우선순위:
  1. `/api/backtest/run` 보호
  2. CSP 강화
  3. docs 노출 플래그를 명시 env 로 변경
  4. preset 글로벌 mutation 제거
  5. npm transitive advisory 정리

## 현재 진행 중

- 사용자가 `$ultrawork` 로 바로 진행하라고 지시했습니다.
- 병렬 작업으로 보안 수정 진행 중:
  - 백엔드 보안 수정
  - npm/dependency 및 공개 repo 표면 정리
- 사용자 요구사항:
  - 수정된 사항을 git 에 반영
  - README 까지 포함해서 push

## ?? ?? ?? ?? (2026-04-16)

- `$ultrawork` ?? ? ?? ??? ?? repo ??? ?? ??????.
- ???/API ??:
  - `/api/backtest/run` ?? ?? ??? ???? `POST /api/admin/backtest/run` ?? ??
  - admin ?? ??? `secrets.compare_digest` ? ??
  - `SEPA_ENABLE_DOCS` ???? ??? docs ??? ?? ????
  - `preset_picks` ??? ?? preset ??? ?? ??? ??? ??? ??
  - `stock_quant` ?? ??? public route ???? ??
- ???/?? ??:
  - `sepa/frontend/backtest.html` ? admin ???? ??? ????? ??
  - `sepa/frontend/app.js` ? raw HTML ?? ?? ??? ??? `textContent` ???? ??
  - `puppeteer` ? `devDependencies` ? ???? `npm audit` ? ?? `0 vulnerabilities`
- ??:
  - `python -m pytest tests/api/test_factory.py tests/api/test_services.py tests/api/test_security_routes.py -q` ? `13 passed`
  - `python -m pytest -q` ? `131 passed`
  - `npm audit --json` ? high / critical ?? `0 vulnerabilities`
- ?? ???:
  - CSP ? `unsafe-inline` ? ?? ?? ?? ?? ??? ??? ???
  - ?? ???? reverse proxy/CDN ? ?? ??? ???? ??? ?? ?? ??

## Security remediation completion (2026-04-16)

- Full verification completed.
- `python -m pytest -q` -> `131 passed`
- `npm audit --json` -> `0 vulnerabilities`
- Security changes now staged for commit/push:
  - admin-only backtest execution via `/api/admin/backtest/run`
  - explicit `SEPA_ENABLE_DOCS` flag
  - constant-time admin token comparison
  - preset copy isolation and symbol validation hardening
  - puppeteer moved to `devDependencies`
- ?? ??/?? repo ?? ??:
  - `58176e3` Document the security posture in the public README
  - `0097073` Harden public repo defaults before wider exposure

## Final security hardening checkpoint (2026-04-16)

- Public repo branch is `main` and current security hardening commit is `0097073`.
- Verified in this session:
  - `python -m pytest -q` -> `131 passed`
  - `npm audit --json` -> `0 vulnerabilities`
- Main security changes now live on GitHub:
  - public backtest execution removed; backtest runs require `POST /api/admin/backtest/run`
  - API docs are off by default unless `SEPA_ENABLE_DOCS=1`
  - admin bearer token uses constant-time comparison
  - public preset routes no longer mutate shared preset state
  - `puppeteer` moved to `devDependencies`
- Remaining known security debt:
  - CSP still depends on `unsafe-inline`
  - rate limiting is still in-memory only
  - admin auth is still a static bearer-token model


## 2026-04-16 security follow-up

- Verified the current security hardening state already landed in git (`0097073`, `58176e3`).
- Re-ran verification after the repo-surface cleanup pass.
- `python -m pytest -q` -> `131 passed`
- `npm audit --json` -> `0 vulnerabilities`
- README security note was tightened to clarify that public request paths do not write backtest result files.

## 2026-04-17 ultrawork security pass

- User requested all remaining security follow-ups in parallel (`$ultrawork`).
- In progress / integrated in working tree:
  - CSP builder + security header wiring to block inline script execution on tracked dashboard pages.
  - Configurable proxy-aware rate limiting (`SEPA_RATE_LIMIT_*` envs) with response headers.
  - Admin auth rotation support via `SEPA_ADMIN_PREVIOUS_TOKENS` / `SEPA_ADMIN_TOKENS` plus optional legacy header shutdown.
  - README / `.env.example` / `docs/40_operations/SECURITY_HARDENING.md` updates for deployment posture.
- Verification plan before commit/push:
  - `python -m pytest tests/api/test_factory.py tests/api/test_rate_limit.py tests/api/test_admin_auth.py tests/api/test_routes_public.py -q`
  - `python -m pytest -q`

## 2026-04-17 ultrawork security/public hardening

- Ran a five-lane hardening pass covering CSP/script externalization, proxy-aware rate limiting, admin token rotation/legacy-header handling, README/public docs updates, and deployment security checklist refresh.
- Frontend pages now avoid inline `<script>` blocks; shared helpers added for back-to-top and global error banners, and page-specific scripts were externalized.
- CSP now keeps `script-src 'self'` strict; inline styles are still allowed for now because the frontend still uses style attributes.
- Admin auth now supports rotation env vars and optional legacy header fallback; public/admin security tests were updated.
- Verification completed:
  - `python -m pytest tests/api/test_factory.py tests/api/test_admin_auth.py tests/api/test_rate_limit.py tests/api/test_routes_public.py tests/api/test_etf_routes.py tests/api/test_kis_routes.py -q` -> passed
  - `python -m pytest -q` -> `165 passed, 12 subtests passed`
  - `npm audit --json` -> `0 vulnerabilities`
- Next repo action in this session: stage the coherent source/docs/tests set (excluding `.omx`), commit, and push to `origin/main`.


## 2026-04-17 ultrawork security pass (completed)

- Completed parallel-style security follow-up integration across CSP, rate limiting, admin auth, README/front-door docs, and deployment guidance.
- Current verified state:
  - `python -m pytest -q` -> `165 passed, 12 subtests passed`
  - `npm audit --json` -> `0 vulnerabilities`
- Landed security behaviors in working tree:
  - public mutation stays admin-only
  - docs stay off by default unless `SEPA_ENABLE_DOCS=1`
  - admin auth supports token rotation envs and legacy-header shutdown
  - rate limiting is proxy-aware when explicitly configured and now emits rate-limit headers
  - CSP no longer allows inline scripts; inline page bootstraps moved into JS files
- Remaining known debt:
  - rate limiting is still in-memory/process-local
  - admin auth is still shared-token based
  - inline styles still keep `style-src 'unsafe-inline'`

## 2026-04-18 pre-QA checkpoint

- Git remote remains `origin -> https://github.com/yuyongkim/probably-alpha.git`
- Active branch remains `main`
- Before running `/qa`, current uncommitted work is being snapshotted into git first so QA fixes can stay isolated.
- Current WIP includes:
  - workspace/KIS hub UI expansion on `index.html`
  - shared chat assistant assets and page wiring for ETF/KIS/overseas mobile pages
  - assistant API/service scaffolding and related settings/tests
