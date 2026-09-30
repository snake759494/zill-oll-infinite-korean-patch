# 질 올 인피니트 (Zill O'll Infinite) PS2 한글패치

PS2 일본판 **ジルオール インフィニット (Zill O'll Infinite, SLPM-65892)** 용 비공식 한국어 패치입니다. 게임 대사·메시지 전부(고유 문장 31,128개), 메뉴·시스템 문장, 아이템 이름, 이름 입력판, 그림 글자(상점 간판·전투 배너·상태 아이콘·투기장 대진표)를 한국어로 바꿨습니다. 현재 배포판은 **v1.0 (2026-09-30)** 입니다.

[패치 다운로드](https://github.com/snake759494/zill-oll-infinite-korean-patch/releases/latest) · [기술 설명](docs/TECHNICAL.md) · [재빌드](docs/BUILD.md) · [변경 기록](CHANGELOG.md) · [권리 안내](RIGHTS.md)

릴리즈 첨부 파일은 **ZillOll_Infinite_PS2_KO_v1.0.xdelta 하나**입니다. 저장소에는 제작 도구·번역 결과·검증 자료만 공개합니다. 원본 및 완성 디스크 이미지, 게임에서 추출한 파일, 일본어 원문 대사, 글꼴 파일, 외부 실행 파일은 포함하지 않습니다.

> ⚠️ `translation/` 폴더에는 게임 대사 번역 전문이 들어 있어 **줄거리 스포일러**가 포함됩니다. 게임을 먼저 즐기실 분은 열어 보지 마세요.

## 대상 버전

이 패치는 **PS2 일본판 SLPM-65892 의 DVD ISO (2,048 바이트 섹터)** 에만 적용합니다. 파일 이름보다 아래 크기와 해시가 일치하는지가 중요합니다.

| 항목 | 값 |
| --- | --- |
| 게임 ID | SLPM-65892 |
| 원본 형식 | 수정되지 않은 일본판 DVD ISO |
| 원본 ISO 크기 | 3,361,144,832 바이트 |
| **원본 ISO MD5** | `0dff715c5ae54b1cff759c35ca977c4e` |
| 원본 ISO SHA-1 | `fbead9189f5c4690e84349eac980a5520bdbc7f9` |
| 원본 ISO SHA-256 | `d32ec5b594e9d7ab5b8eed764c8733ea55566037e65a8541c47646cbc964f1f2` |
| xdelta 파일 크기 | 2,910,120 바이트 |
| xdelta SHA-256 | `bf546e125d5781328159dc0f7c251156030c4c4bf2ac9c4aacee1de651ba98e7` |
| 적용 결과 ISO 크기 | 3,361,144,832 바이트 (원본과 같음) |
| 적용 결과 ISO SHA-1 | `7767e0cb25f564978c413a7b838b7ff13113e9d5` |
| 적용 결과 ISO SHA-256 | `55e17f0b45d53e5fa6d524d6a643469fc99c2223aa1919d8a2d585c794b899f4` |

## 패치 적용 방법

### 원본 확인 (Windows)

```powershell
Get-FileHash -Algorithm MD5 -LiteralPath ".\Zill O'll Infinite (Japan).iso"
```

위 표와 다르면 적용을 중단하세요. CHD·CSO 로 변환한 이미지에는 적용할 수 없습니다.

### xdelta UI 사용

1. 릴리즈에서 `ZillOll_Infinite_PS2_KO_v1.0.xdelta` 를 받습니다.
2. xdelta3 패치 도구의 **Apply Patch** 를 엽니다.
3. **Patch** 에 xdelta 파일, **Source File** 에 해시가 일치하는 원본 ISO 를 선택합니다.
4. **Output File** 에 새 파일명(예: `Zill O'll Infinite (Japan) (Korean).iso`)을 지정합니다.

xdelta 는 호환성을 위해 2차 압축과 파일 경로 헤더 없이 만들었습니다.

### 명령줄 사용

```powershell
.\xdelta3.exe -d -s ".\Zill O'll Infinite (Japan).iso" .\ZillOll_Infinite_PS2_KO_v1.0.xdelta ".\Zill O'll Infinite (Japan) (Korean).iso"
```

해시를 자동 검사하는 도구도 있습니다(Python 3 + xdelta3 필요, 기존 출력 파일은 덮어쓰지 않음).

```powershell
python tools/apply_release.py --xdelta .\xdelta3.exe --source ".\Zill O'll Infinite (Japan).iso" --patch .\ZillOll_Infinite_PS2_KO_v1.0.xdelta --output ".\Zill O'll Infinite (Japan) (Korean).iso"
```

### PCSX2 에서 실행

한글판 ISO 를 여세요. **원본판이나 다른 버전에서 만든 세이브 스테이트는 불러오지 마세요.** 이어 하기는 게임 안 메모리 카드 저장을 쓰세요. 메모리 카드 세이브는 원본판과 호환됩니다.

## 작업 내용과 범위

| 구분 | 내용 |
| --- | --- |
| 대사·메시지 | 메시지 파일 415개, 고유 문장 31,128개(원문 약 119만 자) 전부. 문맥을 보고 직접 번역, 인물별 말투 유지 |
| 시스템 문장 | 실행파일 안 문자열 약 1,020개(메뉴, 메모리 카드, 캐릭터 생성, 날짜·속성 표기 등) |
| 아이템 | 아이템 기본 이름 110개 |
| 이름 입력 | 가나 입력판을 이름용 한글 음절 108자로 교체, "맡김"은 번역된 기본 이름 목록 |
| 그림 글자 | 상점 간판 5종, 전투 배너(선제공격/기습당했다!), 상태 이상 아이콘, 투기장 대진표 |
| 글꼴 | 게임 글꼴에 번역에 쓰인 한글 음절 전부 추가(NanumSquare Neo Regular) |
| 성별 호칭 | 주인공 성별로 갈리는 대사는 형/오빠·누나/언니를 구분, 공용 대사는 이름·중립 표현 |
| 동영상 | 받아쓰기 결과 대사가 없는 음악 영상이라 작업 없음 |

제목 로고 아래 가타카나(ジルオール インフィニット)는 로고 그림이라 그대로 두었습니다.

## 안정성

한글판은 **원본 게임과 데이터 구조가 똑같습니다**. 디스크·리소스 아카이브의 모든 항목이 원래 위치·원래 크기 이하로 들어가고, 실행 코드는 한 명령도 바꾸지 않았습니다. 제작 중 겪은 멈춤 사례와 이를 막는 빌드 검사 규칙은 [docs/TECHNICAL.md](docs/TECHNICAL.md) 에 있습니다.

## 알려진 점

- 메모리 카드 안내창은 자동 줄바꿈이라 단어 중간에서 줄이 바뀔 수 있습니다.
- 대장간 무기 이름 입력의 한자 칸은 한자음 한 글자(검·창·룡…)로 바꿨습니다.
- 줄 넘침·오역 등은 이슈로 알려 주세요.
