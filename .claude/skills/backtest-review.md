# backtest-review.md
> 백테스�� 결과를 검토/요약/비판하는 스킬.
> 결과 해석은 `docs/20_architecture/BACKTEST_RULES.md`를 ��준으로 한다.

---

## 1. 이 스킬을 언제 쓸 것인가

- "이 백테스트 결과가 신뢰할 만한지 검토해줘"
- "전략 A vs 벤치마크 비교해줘"
- "과최적화/바이어스 있는지 봐줘"
- "백테스트 리포트 요약 + 인사이트 뽑아줘"

---

## 2. 입력

- `backtest_result.json` 형식의 결과 파일:
  - `metrics` (cagr, total_return, sharpe, max_drawdown, win_rate, etc.)
  - `benchmark`
  - `params` (execution, commission, slippage, rebalance 등)
  - `survivorship_bias_note`, `lookback_check`, `schema_version`

---

## 3. 리뷰 체크리스트

이 스킬을 사용할 때 반드시 아래를 점검한다.

1. **룰 준수 ���부**
   - 실행 방식: `execution`이 `next-open`인지
   - 비용: 수수료/슬리피지/세금이 적절히 반영됐는지
   - look-ahead: `lookback_check`가 PASSED인지

2. **성과 지표**
   - CAGR vs 벤치마크
   - Max Drawdown
   - Sharpe / Sortino
   - Win Rate / Profit Factor
   - Turnover (과도한 회전율 여부)

3. **스트레스 포인트**
   - MDD 구간과 그 길이
   - 연속 손실 횟수
   - 특정 시장 국면(상승/횡보/하락)에서 취약한지

4. **과최적화 의�� 신호**
   - IS/OOS 분리 여부
   - 파라미터 수 vs 샘플 수
   - 특정 기간에서만 유난히 좋은지

---

## 4. 출력(요약 리포트) 구조

생성해야 할 텍스트 구조:

1. 간단 요약
   - "전략 A는 3�� 동안 CAGR xx%, MDD yy%, 샤프 zz를 기록했다..."
2. 장점
   - 시장 대비 어디에서 강점이 ��는지
3. 단점/위험
   - MDD, 특정 구간에서의 취약함 ���
4. 개선 아이디어
   - 리밸런싱 주기, 유니버스 ��터, 리스크 한도 등 ��정 포���트
5. 결론
   - "실전 적용 전 ��� 필요한 것" 또는 "���액으로 트라이얼 가능" 등

---

## 5. 금지 사항

- 비용/바이어스를 무시한 채 수익률만 보고 호평하지 않는다.
- 단일 성과 지표(CAGR 하나 등)로 전략을 평가하지 않는���.
- 충분한 데이터가 없는데 강한 확신을 드러내는 표현 금지.
