# After-Close 자동추천 운영서

## 실행
```bash
python -m sepa.pipeline.run_after_close
```

## 생성 파일
- `leader-sectors.json`
- `leader-stocks.json`
- `recommendations.json`
- `briefing.json`
- `daily-leaders-report.md`
- `recommendations-report.html`

## 철학 반영 체크
- EPS 성장 게이트
- 최소저항선 게이트
- Minervini 가중치(설정 파일): `config/minervini_config.json`
