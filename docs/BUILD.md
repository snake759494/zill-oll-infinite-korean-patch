# 재빌드

필요: Python 3.13, numpy, Pillow, capstone(선택), zstandard(선택), 원본 ISO, NanumSquareNeo-bRg.ttf / NanumSquareNeo-dEb.ttf.

폴더 구성: 저장소 최상위에 `Zill O'll Infinite (Japan).iso` 와 글꼴 두 개를 둡니다.

```
python tools/extract_res.py      # RES.RBB 전체를 work/res/ 로 풀기 (약 2.5GB)
python tools/units.py            # 메시지 페이지 목록 work/pages.json
python tools/make_jobs.py        # 번역 작업 원문 translation/jobs/NNN.jsonl (id 가 번역과 대응)
python tools/build.py            # 한글판 ISO 생성 (원본 옆)
python tools/verify_iso.py       # 전 항목 해제·크기 검사
xdelta3 -e -9 -S none -A -s "Zill O'll Infinite (Japan).iso" "Zill O'll Infinite (Japan) (Korean).iso" out.xdelta
```

실행파일 문자열 번역의 원문 목록은 `python tools/elf_text.py` 로 `translation/elf_jobs.jsonl` 을 다시 만듭니다.

build.py 는 멈춤 방지 규칙(TECHNICAL.md)을 어기면 중단합니다. 번역을 고칠 때는 `translation/out/NNN.jsonl` 또는 `translation/ko/fix_*.jsonl`(나중 파일이 우선)을 수정하고 `python tools/check_job.py NNN` 으로 태그·줄 수·폭을 검사하세요.
