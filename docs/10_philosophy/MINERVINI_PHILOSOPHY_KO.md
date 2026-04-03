# Minervini 철학 반영 설계 기준서 (KO)

작성일: 2026-03-09

## 1) 핵심 철학
1. **주도주/주도섹터만 거래**: 시장 평균이 아닌 상대강도 상위 집중
2. **추세 확인 후 진입**: 50/150/200MA 정배열, 고점 근접 종목 우선
3. **수급(거래량) 확인**: 조정 시 거래량 감소, 돌파 시 거래량 증가
4. **실적 가속(EPS/매출)**: 기술적 강세를 펀더멘털이 뒷받침해야 함
5. **최소 저항선(Least Resistance)**: 상승 추세선 위/근접 종목 선별
6. **리스크 선행 통제**: 손절 7~8%, R/R 최소 1.5 이상

## 2) 시스템 매핑
- Alpha: Trend Template 8조건 + RS
- Beta: VCP 수축/거래량 건조도
- Gamma: EPS YoY/가속도 + 섹터/매크로 힌트
- Delta: 진입/손절/목표/수량
- Omega: 최종 추천 종목 1~3개

## 3) 추천 로직(자동)
최종 추천점수 =
- Alpha(45%) + Beta(20%) + Gamma(20%) + RS120(10%) + 최소저항선(5%)

필수 게이트:
- Trend Template 통과
- EPS 품질 `positive_growth` 이상
- 최소저항선이 `up_least_resistance` 또는 `pullback_in_uptrend`

## 4) 일일 산출물
- `leader-sectors.json` : 주도섹터
- `leader-stocks.json` : 후보 주도주
- `recommendations.json` : 최종 추천 1~3종목 + 사유/리스크
