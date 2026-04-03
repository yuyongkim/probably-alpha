# leader-scan.md
> 매일 EOD 기준으로 주도 섹터/주도주를 스캔할 때 ���용하는 스킬.
> 섹터/리더 점수 ���펙은 `docs/20_architecture/LEADER_SCORING_SPEC.md`를 Source of Truth로 사용한다.

---

## 1. 이 스킬을 언제 쓸 것인가

다음과 같은 요청이 있을 때 이 스킬을 사용한다.

- "오늘 주도 ��터/주도주 뽑아줘"
- "리더 섹터/리더 종목 리스트 갱신"
- "Alpha/Beta 통과 종목으로 ��더 스캔 돌리자"
- "leader-sectors.json / leader-stocks.json 다시 생성"

---

## 2. ��업 개요

1. 시장 데이���/유니버스 준비
2. 섹터별 점수 계산 (SectorScore)
3. 섹터 내 ��더 종목 점수 계산 (LeaderScore)
4. JSON 산출물 ���장 및 요약 출력

모든 구체적인 수학/필드는 `LEADER_SCORING_SPEC.md`에 정의되��� ��고, 이 스킬은 **그 ���칙을 어기지 않는 선��서** 구현과 실행을 안내한다.

---

## 3. 선행 조건

작업 전 다음을 확인한다.

- `.omx/artifacts/market-data/` 아래 일봉 데이터가 최���인지
- `docs/30_data_contracts/SYMBOL_MAPPING_SPEC.md`에 맞게 유니버스 필터가 동작하는지
- 오늘 날짜 기준 유니버스가 생성되어 있는지 (없으면 먼저 생성)

---

## 4. 구현/실행 단계

### 4.1 섹터 점수 계산

- 참조 문서:
  - `docs/20_architecture/LEADER_SCORING_SPEC.md` 1���
- 구�� 위치:
  - `sepa/scoring/sector_strength.py` (예상)
- 해야 할 일:
  - RS_20, RS_60, Breadth_50MA, NearHighRatio, TurnoverTrend ��산
  - SectorScore 공식대로 합성
  - 제외 조건(종목 수, 거래대금) 적용
  - `leader-sectors.json`에 저�� (`OUTPUT_SCHEMA_SPEC.md` 형식 준수)

### 4.2 리더 종목 점수 계산

- 참조 문서:
  - `LEADER_SCORING_SPEC.md` 2장
- 구현 위치:
  - `sepa/scoring/leader_stock.py`
- 해�� 할 일:
  - LeaderScore 공식대로 RS, TT, 근접도, 거래량, 변동성, 실적 프록시 등을 계산
  - 최소 자격 게이��(TrendTemplate >= 5/8, close > MA50 등)를 먼저 적용
  - `leader-stocks.json`에 저장

---

## 5. 산출물 검증

스킬을 사용할 때 다음을 점검한다.

1. `leader-sectors.json`을 열어 Top N 섹터가 직관적으로 말이 되는지 검토
2. `leader-stocks.json`에서 각 ���목의 선정 사유(`reason`)가 규칙과 일관한지 확인
3. Alpha/Beta/Gamma/Delta/Omega 체인과 자연스럽게 연결되는지 확인
4. 이상치:
   - 예: 거래대금이 너무 낮은 종목이 리더로 뜨는 경��� → 규칙/필터 재검토

---

## 6. 금지 사항

- 점수 공식을 임의로 바꾸지 않는다. 변경이 필요하면 반드시 `LEADER_SCORING_SPEC.md`를 먼저 수���한다.
- 단순 등락률 상위만 리더로 취급하지 않는다.
- 테스트용으로 막 만든 필드/지표를 LeaderScore에 몰�� 끼워 넣지 않는다.
