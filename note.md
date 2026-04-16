# 작업 메모

## 이번 대화에서 한 일

- Market Wizards / preset 매핑 관련 작업을 이어서 복구했습니다.
- 트레이더 preset direct 매핑, runtime conditions 노출, Korea/Overview/People 페이지 연동 작업을 점검했습니다.
- `sepa/api/factory.py`에서 CSP가 Google Fonts를 막던 문제를 수정했습니다.
- `tests/api/test_factory.py`에 CSP 회귀 테스트를 추가했습니다.
- 전체 테스트를 실행했고 `python -m pytest` 기준 `124 passed`를 확인했습니다.
- 불필요한 `.omx/*` 변경과 로컬 스크린샷 산물을 정리했습니다.
- 아래 커밋을 생성했습니다.
  - `2d54ccb` `Make preset-driven wizard pages explain their runtime logic`

## 생성한 산출물

- bundle: `C:\Users\USER\Desktop\Company_Credit-2d54ccb.bundle`
- patch: `C:\Users\USER\Desktop\Company_Credit-2d54ccb.patch`

## 리포 이름 아이디어

- `wizard-of-kospi`
- `probably-alpha`

현재는 사용자가 새 원격 리포를 만든 뒤 알려주면 다음 단계를 진행하는 상태였습니다.

## 현재 상태

- 워킹트리: clean 상태였음
- 원격 저장소: 미연결 상태였음
- 다음 작업: 사용자가 만든 원격 repo 연결 후 push 또는 PR 흐름 진행

## 방금 추가된 작업 원칙

- 사용자가 대화를 이어갈수록 이 `note.md`를 계속 업데이트합니다.
- 긴 대화가 끊겨도 이 파일을 기준으로 바로 복구할 수 있게 유지합니다.
- 채팅창에는 짧게 요약하고, 상세 상태는 이 파일에 누적합니다.

## 최근 대화 추가 메모

- 사용자는 GitHub 저장소 생성 중이며, repo 이름으로 `probably-alpha`를 고려 중입니다.
- 라이선스 선택을 고민 중입니다.
- 현재 추천 방향은 프로젝트 공개 범위와 재사용 허용 수준에 따라 결정하는 것입니다.
- 새 공개 원격 저장소가 생성되었습니다: `https://github.com/yuyongkim/probably-alpha`
- 다음 단계는 로컬 저장소에 remote를 연결하고 현재 커밋을 push하는 것입니다.
- 공개 repo로 push 완료했습니다.
- compare/PR 대신 필요한 공개용 기본 문서를 직접 채우는 방향으로 진행 중입니다.
- 현재 추가 작업: 루트 `README.md` 작성 및 저장소 첫인상 정리.
- 루트 `README.md` 작성 완료, 공개 repo에 push 완료.
- 최근 공개용 정리 커밋:
  - `be8a6a5` Preserve session context in a top-level note
  - `2a11006` Give the public repo a usable front door
- GitHub compare 화면에서 `main` 과 `master` 가 서로 다른 히스토리라고 뜨는 문제를 확인했습니다.
- 원인: GitHub에서 생성된 `main` 초기 커밋과 로컬에서 push한 `master` 히스토리가 따로 시작했기 때문입니다.
- 정리 방향: 원격 `main` 을 현재 작업 히스토리와 맞추고, 이후 기본 작업 브랜치도 `main` 기준으로 정렬합니다.
