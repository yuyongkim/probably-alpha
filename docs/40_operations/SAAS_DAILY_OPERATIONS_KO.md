# SaaS 일일 운영 표준 (사장님 대시보드)

## 목표 출력 (매일 동일)
1. 최종 추천 TOP3
2. 추천 근거(EPS/최소저항/RS/VCP)
3. 리스크 플랜(entry/stop/target/qty/RR)
4. 화면 반영(오늘+히스토리)

## 자동 실행
```bash
python -m sepa.pipeline.run_after_close
```

## 저장 체계
- 파일: `.omx/artifacts/daily-signals/{YYYYMMDD}/`
- DB: `.omx/artifacts/recommendations.db` (daily_recommendations)

## SaaS 조회 API
- `/api/recommendations/latest`
- `/api/recommendations/history?limit=30`
- `/api/briefing/latest`

## 화면 구성
- 오늘 추천 TOP3
- 사장님 브리핑
- 주도섹터/주도주
- 추천 히스토리(30일)
