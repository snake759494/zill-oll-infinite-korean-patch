"""이름 입력판: 히라가나·가타카나 칸(8바이트 문자열)을 이름용 한글 음절로 교체, 탭 이름 번역.
표 두 벌(캐릭터 생성 0x3261e8 부근, 대장간 무기 이름 0x3424c0 부근)."""
import units
# 이름에 많이 쓰이는 음절(가나다 순이 아니라 입력판 행 단위로 보기 좋게 배치)
SYL = ('가나다라마바사아자차카타파하'
       '거너더러머버서어저처커터퍼허'
       '고노도로모보소오조초코토포호'
       '구누두루무부수우주추쿠투푸후'
       '기니디리미비시이지치키티피히'
       '레베세에제테페헤렌린민빈신인'
       '진한현연영윤준민수희은혜지성'
       '용철훈재태석호규상원')
HIRA = 'あいうえおかきくけこさしすせそたちつてとなにぬねのはひふへほまみむめもやゆよらりるれろわをんぁぃぅぇぉゃゅょっゎ'
KATA = 'アイウエオカキクケコサシスセソタチツテトナニヌネノハヒフヘホマミムメモヤユヨラリルレロワヲンァィゥェォャュョッヮ'
TABS = [('カナ かな 英数 ゆだねる 空白 取消 入力完了', '한글 이름 영숫 맡김 공백 취소 입력완료'),
        ('カナ かな 記号 ゆだねる 空白 取消 中止 完了', '한글 이름 기호 맡김 공백 취소 중지 완료')]
def apply(elf):
    elf = bytearray(elf)
    syl = iter(SYL)
    mapping = {}
    for ch in HIRA + KATA:
        mapping[ch] = next(syl, None)
    n = 0
    for start in (0x325f68, 0x342240):
        for k in range(200):
            a = start + 8 * k
            cell = bytes(elf[a:a+8]).split(b'\0')[0]
            try: s = cell.decode('cp932')
            except UnicodeDecodeError: continue
            if len(s) == 1 and s in mapping and mapping[s]:
                b = units.encode(mapping[s]); elf[a:a+8] = b + bytes(8 - len(b)); n += 1
    for jp, ko in TABS:
        jb = jp.encode('cp932'); kb = b' '.join(units.encode(t) for t in ko.split(' '))
        assert len(kb) <= len(jb), (ko, len(kb), len(jb))
        i = elf.find(jb)
        while i >= 0:
            elf[i:i+len(jb)] = kb + bytes(len(jb) - len(kb)); i = elf.find(jb, i + 1)
    return bytes(elf), n
