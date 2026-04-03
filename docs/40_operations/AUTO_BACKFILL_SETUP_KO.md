# Auto Backfill 자동화 설정 가이드

## 개요
컴퓨터를 켤 때마다 자동으로 빠진 날짜의 시그널 데이터를 채워주는 자동화 설정입니다.
별도의 서버나 클라우드 없이 Windows 시작 프로그램으로 동작합니다.

## 동작 흐름
1. Windows 로그인
2. `auto_backfill.bat` 자동 실행
3. 키움 REST API로 시세 데이터 갱신 (실패 시 Yahoo Finance 폴백)
4. 최근 30거래일 중 빠진 날짜 감지
5. 빠진 날짜만 골라서 시그널 생성 (alpha/beta/gamma/delta/omega + leaders + recommendations)
6. 이미 최신이면 스킵

## 관련 파일

| 파일 | 역할 |
|------|------|
| `scripts/auto_backfill.py` | 메인 스크립트 (시세 갱신 + backfill) |
| `scripts/auto_backfill.bat` | Windows 실행용 래퍼 |
| `scripts/register_auto_backfill.ps1` | 작업 스케줄러 등록용 (관리자 권한 필요, 선택사항) |

## 설치 위치
Windows 시작 프로그램 폴더에 등록됨:
```
%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\sepa_auto_backfill.bat
```

## 시세 데이터 소스 우선순위
1. **키움 REST API** (HTS 불필요, `.env`에 키 설정 필요)
2. **QuantDB** (로컬 DB 있으면 사용)
3. **Yahoo Finance** (폴백, `.KS`/`.KQ` suffix)

## 필수 환경변수 (.env)
```
KIWOOM_APP_KEY=<키움 앱키>
KIWOOM_SECRET_KEY=<키움 시크릿키>
KIWOOM_MARKET_TYPE=0,10,3
```

## 수동 실행
```bash
python scripts/auto_backfill.py
```

## 특정 날짜 범위 backfill
```bash
python -m sepa.pipeline.backfill_history --date-from 20260315 --date-to 20260325
```

## 용량 참고
- 하루당 시그널 데이터: ~70KB
- 연간 증가량: ~18MB (252거래일 기준)
- 전체 6년치: ~195MB

## 제거 방법
시작 프로그램에서 제거:
```powershell
Remove-Item "$env:APPDATA\Microsoft\Windows\Start Menu\Programs\Startup\sepa_auto_backfill.bat"
```
