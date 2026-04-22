# CONTRIBUTING — ky-platform

> 모듈화는 이 레포의 생존 조건이다. 아래 규칙은 권고가 아니라 **가드레일**.

---

## 1. 파일 크기 예산

| 유형 | 상한 | 근거 |
|---|---|---|
| `app/**/page.tsx` | **100 줄** | 페이지는 조립만. 로직은 훅·컴포넌트로 분리 |
| `components/**/*.tsx` | **300 줄** | 한 화면이 한 컴포넌트에 몰리면 리팩터 |
| `app/**/layout.tsx` | **80 줄** | 레이아웃은 네비게이션/슬롯만 |
| `hooks/**/*.ts` | **150 줄** | 단일 책임 훅 |
| `apps/api/routers/**/*.py` | **200 줄** | 라우트 = 얇은 어댑터. 비즈니스 로직은 services |
| `apps/api/services/**/*.py` | **400 줄** | 그 이상이면 도메인 분리 |

초과 시 — **리뷰어는 반드시 분할을 요구**.

---

## 2. 디렉터리 역할

```
apps/web/
├─ app/                 라우팅 + 최소 조립
├─ components/
│  ├─ shared/           프로젝트 전반 재사용 (SummaryRow, DenseTable, QuoteStrip ...)
│  └─ <feature>/        특정 탭 전용
├─ hooks/               데이터 페칭 / 글로벌 상태
├─ lib/                 순수 유틸 (format, date, number)
└─ styles/              globals.css + tailwind entry

apps/api/
├─ main.py              FastAPI 앱 생성 + 라우터 등록
├─ config.py            Pydantic BaseSettings
├─ routers/<tab>/       탭 단위 라우터 (6개)
├─ services/            도메인 로직 (pure, testable)
└─ adapters/            외부 API 어댑터는 packages/adapters 사용
```

---

## 3. 재사용 원칙

### 3.1 Shared components
`components/shared/` 하위는 **프롭만 바뀌면 어디서든 쓰이는** 수준으로 작성.

- `SummaryRow` — 상단 요약 한 줄 (label · value · delta)
- `DenseTable` — Bloomberg 스타일 고밀도 테이블
- `QuoteStrip` — 편집용 인용/하이라이트 스트립
- `KpiCard`, `MetricTile`, `SparkBar` (추가 예정)

### 3.2 6-Wizard 패턴
Alpha / Beta / Gamma / Delta / Omega / Sigma 스크리너 6종은 **단일 컴포넌트**로 구현:

```tsx
<WizardPage config={WIZARD_CONFIGS.alpha} />
```

각 config 는 schema(JSON) + query key + 컬럼 맵만 다름. 6개 페이지 파일은 각 15줄 미만.

### 3.3 Stock Detail Modal
종목 상세 모달은 **단일 글로벌 상태** + **dynamic import**.

```tsx
const StockDetailModal = dynamic(() => import('@/components/shared/StockDetailModal'))
// 어디서 클릭하든 useStockDetail().open(symbol)
```

---

## 4. 스타일 규약

- Tailwind utility 우선, 반복되면 `components/shared` 로 승격
- 색상/간격/타이포는 `styles/globals.css` 의 **CSS variables** 만 사용 (`var(--accent)`, `var(--border)` ...)
- 하드코딩된 헥스/숫자 금지 (디자인 토큰만)
- 모달·오버레이는 `backdrop-filter` 남용 금지 (성능 이슈, 참고: `memory/feedback_frontend_perf.md`)

---

## 5. 데이터 페칭

- 모든 fetching 은 `hooks/` 에 분리 (`useLeadersToday`, `useFactorUniverse` ...)
- 컴포넌트 내부 `fetch()` 직접 호출 금지
- 에러·로딩·빈상태 3가지는 훅이 반환, UI 는 분기만
- 캐시: 같은 날짜 데이터는 SWR/React Query 로 재사용 — 새로고침 전까진 재요청 X

---

## 6. API 계약

- snake_case JSON
- 공통 envelope: `{ ok, data, error }`
- 모든 경로 `/api/v1/...`
- 스키마 변경 시 `schema_version` 증가
- 필수 필드는 NULL 금지

---

## 7. 백엔드 서비스 규칙

- `routers/*` 는 **얇은 어댑터** (입력 검증 + 서비스 호출 + 응답 포맷)
- 비즈니스 로직 = `services/*` (순수 함수, 테스트 가능)
- 외부 API 콜 = `packages/adapters/*` (race/retry/timeout 통일)

---

## 8. 테스트

- API: `apps/api/tests/` — `pytest`, 라우터별 smoke + 서비스 유닛
- Web: `apps/web/__tests__/` — 컴포넌트는 snapshot, 훅은 @testing-library
- 커밋 전 `scripts/check.sh` (추후 추가) 통과 필수

---

## 9. 커밋 메시지

[Conventional Commits](https://www.conventionalcommits.org/) 채택:
```
feat(chartist): add today summary row component
fix(api): handle empty factor universe
chore: bump next to 15.1.2
docs: expand ARCHITECTURE tab map
```

---

## 10. 금지 사항

- 페이지에 비즈니스 로직 혼재
- `components/shared` 외부에서 재사용 컴포넌트 만들기
- `.env` 커밋
- `legacy/` 디렉터리에 원본 **복사** (참조 README 만 허용)
- 포트 8200 건드리기 (`sepa.yule.pics` 운영 중)
