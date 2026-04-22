# legacy/

> 6개 기존 프로젝트에 대한 **포인터 전용** 디렉터리.
> 실제 파일은 복사하지 않는다 — 원본은 각자 경로에, 백업은 `_integration_backup_20260422/` 에 있다.

## 정책

- 각 하위 폴더에는 `PORT_OF_ORIGIN.md` 만 둔다.
- 원본 경로, 현재 상태(운영 여부), git 상태, 포팅 우선순위를 기록한다.
- **복사·심볼릭 링크 금지** (Windows 심링크 안전성 + 중복 저장 낭비).

## 인덱스

| Folder | Origin | Status | 우선순위 |
|---|---|---|---|
| `company_credit/`     | `C:/Users/USER/Desktop/Company_Credit/`      | 운영 중 (sepa.yule.pics, port 8200) | P1 병렬 |
| `quantdb/`            | `C:/Users/USER/Desktop/QuantDB/`             | 최근 작업 | P0 승격 |
| `quantplatform/`      | `C:/Users/USER/Desktop/QuantPlatform/`       | PIT + RAG | P1 |
| `finance_analysis/`   | `C:/Users/USER/Desktop/Finance_analysis/`    | DCF 도구 | P2 |
| `dart_analysis/`      | `C:/Users/USER/Desktop/Dart_Analysis/`       | PDF 분석 | P2 |
| `kis_korea_investment/` | `C:/Users/USER/Desktop/한국투자증권/`       | KIS 샘플 | P0 |

## 백업

```
C:/Users/USER/Desktop/_integration_backup_20260422/
```

Phase 0 에서 robocopy 로 전체 스냅샷 완료.
