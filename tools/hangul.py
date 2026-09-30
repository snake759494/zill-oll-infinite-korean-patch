"""한글 음절 ↔ SJIS 코드 배정.
KS X 1001 2,350자 + 추가 음절을 JIS 1수준 한자 SJIS 코드(889F부터)에 순서대로 배정한다.
게임은 SJIS → 유니코드(cp932) 로 바꿔 폰트 레코드를 찾으므로, 폰트 레코드 코드 = 그 한자의 유니코드."""
import os, json
ROOT = os.path.join(os.path.dirname(__file__), '..')
EXTRA = os.path.join(ROOT, 'translation', 'extra_syllables.txt')

def ks2350():
    out = []
    for hi in range(0xB0, 0xC9):
        for lo in range(0xA1, 0xFF):
            try: out.append(bytes([hi, lo]).decode('euc-kr'))
            except UnicodeDecodeError: pass
    return out

def sjis_codes():
    """JIS 1·2수준 한자 SJIS 코드(유효한 cp932 한자만)."""
    out = []
    for hi in list(range(0x88, 0xA0)) + list(range(0xE0, 0xEB)):
        for lo in list(range(0x40, 0x7F)) + list(range(0x80, 0xFD)):
            if hi == 0x88 and lo < 0x9F: continue
            b = bytes([hi, lo])
            try: ch = b.decode('cp932')
            except UnicodeDecodeError: continue
            if 0x4E00 <= ord(ch) <= 0x9FFF: out.append(b)
    return out

def syllables():
    s = ks2350()
    if os.path.exists(EXTRA):
        for ch in open(EXTRA, encoding='utf-8').read().split():
            if ch not in s: s.append(ch)
    return s

_MAP = None
def table():
    """{한글: sjis bytes}"""
    global _MAP
    if _MAP is None:
        codes = sjis_codes()
        syl = syllables()
        _MAP = {ch: codes[i] for i, ch in enumerate(syl)}
        _MAP[' '] = codes[len(syl)]          # 좁은 띄어쓰기 전용 코드
    return _MAP

def unicode_of(b):
    return ord(b.decode('cp932'))


# ── 1바이트 코드: 대사 파일 안에서 0xA6~0xDD(0xB0 제외)는 현재 가나 모드(기본 히라가나)로 해석돼
#    히라가나 유니코드로 폰트를 찾는다. 한글판 대사엔 히라가나가 없으므로 이 55칸을
#    가장 자주 쓰는 음절 54자 + 좁은 띄어쓰기에 배정(대사 크기 약 25% 감소 → 메시지 버퍼 한계 대응).
#    0xDE/0xDF(탁점·반탁점)는 앞 글자와 합쳐지므로 쓰지 않는다. 시스템(ELF) 문자열에는 쓰지 않는다.
SINGLE_BYTES = [b for b in range(0xA6, 0xDE) if b != 0xB0]
TOP = os.path.join(ROOT, 'translation', 'single_byte_syllables.txt')
_S1 = None
def single():
    """{글자: 1바이트} — ' ' 포함"""
    global _S1
    if _S1 is None:
        chars = [' '] + open(TOP, encoding='utf-8').read().split()
        assert len(chars) <= len(SINGLE_BYTES)
        _S1 = {ch: bytes([SINGLE_BYTES[i]]) for i, ch in enumerate(chars)}
    return _S1

def single_unicode(b):
    """1바이트 코드가 게임에서 찾는 히라가나 유니코드."""
    import zmsg
    return ord(zmsg.hw2fw(zmsg.HW[b - 0xA1], 'H'))
