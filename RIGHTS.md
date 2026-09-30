# 권리 및 외부 자료

이 저장소는 비공식 한국어 패치의 제작 도구·번역·검증 자료 공개용입니다. 원작 게임 「ジルオール インフィニット (Zill O'll Infinite)」와 그 텍스트·이미지·음성·영상·실행 코드의 권리는 원 권리자(코에이 테크모 게임스)에게 있습니다. 원본 게임, 패치 적용 게임, 게임에서 추출한 파일·글꼴은 배포하지 않으며, 릴리즈에는 원본 디스크 이미지가 있어야만 쓸 수 있는 차분 파일(xdelta)만 첨부합니다.

`translation/` 에는 한국어 번역 결과만 있고 **일본어 원문 대사는 넣지 않았습니다**. 번역은 작업 번호(id)로 저장되며, 원문과의 대응은 사용자가 가진 원본 ISO 에서 `tools/extract_res.py`·`tools/units.py`·`tools/make_jobs.py` 로 다시 만들 수 있습니다. 용어집(`glossary.tsv`)에는 대조용으로 고유명사의 원어 표기가 들어 있습니다.

저장소 공개 자체가 모든 파일에 동일한 오픈소스 라이선스를 부여한다는 뜻은 아닙니다. 자체 제작 코드·번역 전체에 대한 별도 포괄 라이선스는 현재 지정하지 않았습니다.

게임 안 한글 글꼴과 그림 글자는 NanumSquare Neo(Regular·ExtraBold)로 그렸습니다. NanumSquare Neo 는 SIL Open Font License 1.1 을 따르며 전문을 `LICENSES/NanumSquareNeo-OFL-1.1.txt` 에 보존했습니다. 글꼴 파일 자체는 포함하지 않습니다(`docs/FONT_CREDITS.md`).

xdelta, PCSX2, Python 라이브러리(numpy, Pillow, capstone, zstandard) 등 외부 도구는 각 프로젝트의 라이선스를 따르며 바이너리를 재배포하지 않습니다. `tools/gsmem.py` 는 같은 제작자의 다른 한글패치에서 가져온 것입니다. 게임 코드의 디스어셈블 결과물은 넣지 않았고, 해석한 내용만 `docs/TECHNICAL.md` 에 정리했습니다.
