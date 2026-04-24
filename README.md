# ky-platform

> probably-alpha 통합 금융 플랫폼 — 6개 레거시 프로젝트를 하나의 모듈화된 모노레포로 재구성.

## 구조

```
ky-platform/
├─ apps/
│  ├─ api/        FastAPI  (port 8300)
│  └─ web/        Next.js 15 App Router  (port 8380)
├─ packages/
│  ├─ core/       데이터 코어 (QuantDB mvp_platform 승격 대상)
│  └─ adapters/   KIS / Kiwoom / DART / FRED / ECOS / KOSIS / Naver
├─ legacy/        기존 6개 프로젝트 참조 (원본 경로만 기록, 복사 X)
└─ scripts/       dev.sh / dev.bat
```

## 6 탭 구조 (한눈에)

| Tab | Role | Key surfaces |
|---|---|---|
| **Chartist** | 오늘의 시장 · 섹터 로테이션 · 리더 스캔 | Today, Sectors, Leaders, Wizards |
| **Quant** | 팩터 · 백테스트 · 리스크 | Factors, Backtests, Research |
| **Value** | DCF · 재무 · 버핏 RAG | DCF, Financials, RAG-Q&A |
| **Execute** | 포지션 · 주문 · 리스크 가드 | Overview, Orders, Positions |
| **Research** | 논문 · 리포트 · 거시 | Papers, Reports, Macro |
| **Admin** | 상태 · 로그 · 토큰 · 데이터 품질 | Status, Jobs, Audit |

자세한 맵: [ARCHITECTURE.md](./ARCHITECTURE.md)

## 개발 실행

```bash
# 1. 의존성 설치 (최초 1회)
cd apps/api && pip install -e . && cd ../..
cd apps/web && npm install && cd ../..

# 2. 개발 서버 기동 (api 8300 + web 8380 동시)
./scripts/dev.sh        # macOS / Linux / Git Bash
scripts\dev.bat         # Windows cmd / PowerShell
```

## 포트 정책

| Port | Service | 비고 |
|---|---|---|
| **8200** | `sepa.yule.pics` (legacy Company_Credit) | **운영 중 — 절대 건드리지 말 것** |
| 8300 | ky-platform API | 신규 |
| 8380 | ky-platform Web | 신규 |

## 시크릿 관리

- **공용 시크릿**: `~/.ky-platform/shared.env` — 모든 dev 스크립트가 가장 먼저 로드
- **프로젝트 로컬**: `apps/api/.env` — 포트 등 로컬 오버라이드만
- `.env.example` 참고, 실제 `.env` 파일은 `.gitignore`로 차단

## 백업 위치

모든 레거시 원본은 아래에 보존됨 (Phase 0 완료):
```
C:/Users/USER/Desktop/_integration_backup_20260422/
```

## 기여 가이드

모듈화 규칙은 [CONTRIBUTING.md](./CONTRIBUTING.md) 참고. 
요약:
- 페이지 파일 **100줄 이하**, 컴포넌트 **300줄 이하**
- 6-wizard 는 단일 `<WizardPage config={...}/>` 로 재사용
- Stock Detail Modal 은 글로벌 상태 + dynamic import
- 스타일은 Tailwind + CSS variables (`styles/globals.css`)

## Knowledge base

- **BOK RAG** — 한국은행 보고서 ~40K 청크를 Ollama `bge-m3` (1024-dim) 로 임베딩한 벡터 인덱스. 저장: `~/.ky-platform/data/rag_bok/` (`vectors.npy` + `chunks.jsonl` + `meta.json`). 빌드 스크립트: `scripts/build_rag_bok.py`.
- **Broker Report RAG (Drive-first)** — Google Drive에 모아둔 증권사/리서치 보고서가 primary source. 로컬 export/mirror를 `scripts/build_rag_broker.py --source-path <dir>`로 인덱싱해 `~/.ky-platform/data/rag_broker/`에 저장한다. CSV manifest의 `pdf_direct_url`은 `--download-pdfs --pdf-cache-dir ~/.ky-platform/data/broker_pdf_cache`로 본문 캐시/추출까지 확장한다. 3060 Ti/CUDA dense vector 인덱스는 `scripts/build_rag_broker_vec.py --device cuda`로 `~/.ky-platform/data/rag_broker_vec/`에 만든다. Naver Finance는 fallback/listing 용도다.
- **Buffett RAG (TF-IDF)** — `packages/core/ky_core/research/buffett.py`. 기존 QuantPlatform 포팅분, 로컬 기동만으로 동작.

## 상태

Phase 2 (scaffold) 완료. 다음 단계:
1. `packages/core/` 로 QuantDB 승격
2. `apps/api/routers/*/` 실제 로직 이식
3. `apps/web/` UI 목업 이식 (`_integration_mockup.html` 참조)
