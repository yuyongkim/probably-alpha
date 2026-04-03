# Frontend/Backend 실행 가이드 (KO)

## 0) 원샷 로컬 부트스트랩
```powershell
scripts\start_local.bat
scripts\start_local.bat -InstallDeps
```

`start_local`은 `.env`를 우선 읽고, 값이 없으면 `.env.example` 기본값을 사용합니다. 의존성 설치가 필요할 때는 `requirements.txt`를 기준으로 처리합니다.

이제 조회용 GET API는 쓰기 작업을 하지 않습니다. 특정 날짜 산출물이 없으면 `POST /api/admin/daily-signals` 또는 `python -m sepa.pipeline.run_after_close`로 명시적으로 생성해야 합니다. persistence 히스토리 보강도 `POST /api/admin/history/backfill`로 분리되었습니다.

## 1) 파이프라인 산출물 생성
```bash
python3 -m sepa.pipeline.run_live_cycle
```

## 2) 백엔드 API 실행
```bash
uvicorn sepa.api.app:app --host 127.0.0.1 --port 8000 --reload
```

주요 API:
- `/api/summary`
- `/api/alpha`
- `/api/beta`
- `/api/gamma`
- `/api/delta`
- `/api/omega`

## 3) 프론트 실행
정적 파일이므로 아래 중 택1:
```bash
python3 -m http.server 8080 --directory sepa/frontend
```
브라우저: `http://127.0.0.1:8080`

API Base 입력값: `http://127.0.0.1:8000`
