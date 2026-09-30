"""메시지 파일 → 번역 단위.
항목 = 페이지들(05 05 05 로 끝남). 페이지 = [머리(조건 헤더, 보존)] + 본문.
본문 표기(번역용):  줄바꿈 '\\n'(TSV 안에서는 ⏎), 변수 <Vxx>, 색 <Cx>, 기타 제어 <Xxx>.
가나 모드 전환(ESC H/K)은 표기에서 없앤다(인코딩 때 한글은 모드 무관)."""
import os, re, json, struct
import zmsg
ROOT = os.path.join(os.path.dirname(__file__), '..')
RES = os.path.join(ROOT, 'work', 'res')
HDR = re.compile(rb'\x01.\x02.(?:\x04)?[{}=%$<>#!&+\-*]?%?[0-9]*', re.S)
END = b'\x05\x05\x05'

def msg_files():
    out = []
    for f in sorted(os.listdir(RES)):
        if f.endswith(('.dat', '.NONE')):
            d = open(os.path.join(RES, f), 'rb').read()
            if zmsg.is_msg(d): out.append(f)
    return out

def split_pages(entry):
    """항목 → [(머리bytes, 본문bytes)], 꼬리(마지막 050505 뒤 나머지)."""
    pages = []; p = 0
    while True:
        q = entry.find(END, p)
        if q < 0: break
        body = entry[p:q]
        m = HDR.match(body)
        h = m.group() if m and body.startswith(b'\x01') else b''
        pages.append((h, body[len(h):])); p = q + 3
    return pages, entry[p:]

def to_text(b):
    out = []; i = 0; mode = 'H'
    while i < len(b):
        c = b[i]
        if c == 0x1b:
            m = b[i+1] if i+1 < len(b) else 0
            if m in (0x48, 0x4b): mode = chr(m); i += 2; continue
            if m == 0x43: out.append('<C%s>' % chr(b[i+2])); i += 3; continue
            out.append('<E%02X>' % m); i += 2; continue
        if c == 0x02:
            out.append('<V%02X>' % b[i+1]); i += 2; continue
        if c == 0x0a: out.append('\n'); i += 1; continue
        if 0x81 <= c <= 0x9f or 0xe0 <= c <= 0xfc:
            out.append(b[i:i+2].decode('cp932', 'replace')); i += 2; continue
        if 0xa1 <= c <= 0xdf:
            out.append(zmsg.hw2fw(zmsg.HW[c-0xa1], mode)); i += 1; continue
        if 0x20 <= c < 0x7f and c not in (0x3c, 0x3e):
            out.append(chr(c)); i += 1; continue
        out.append('<X%02X>' % c); i += 1
    import unicodedata
    t = ''.join(out).replace('゛', '゙').replace('゜', '゚')
    return unicodedata.normalize('NFC', t)

def extract():
    """모든 파일·항목·페이지 목록과 고유 본문 목록."""
    rows = []   # (file, entry, page, header_hex, text)
    for f in msg_files():
        d = open(os.path.join(RES, f), 'rb').read()
        for i, e in enumerate(zmsg.parse(d)):
            pages, tail = split_pages(e)
            for k, (h, body) in enumerate(pages):
                rows.append((f, i, k, h.hex(), to_text(body)))
    return rows

if __name__ == '__main__':
    rows = extract()
    json.dump(rows, open(os.path.join(ROOT, 'work', 'pages.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    uniq = {}
    for r in rows:
        uniq.setdefault(r[4], []).append(r)
    jp = [t for t in uniq if re.search('[ぁ-んァ-ヶ一-龯]', t)]
    print(len(rows), 'pages', len(uniq), 'unique', len(jp), 'with JP', sum(len(t) for t in jp), 'chars')

TAG = re.compile(r'<(V|C|E|X)([0-9A-Za-z]{1,2})>')
def encode(text, narrow_space=True, single=False):
    """번역문(표기 형식) → 게임 바이트."""
    import hangul
    tb = hangul.table(); s1 = hangul.single() if single else {}; out = bytearray(); i = 0
    while i < len(text):
        m = TAG.match(text, i)
        if m:
            k, v = m.groups()
            if k == 'V': out += bytes([2, int(v, 16)])
            elif k == 'C': out += b'\x1bC' + v.encode()
            elif k == 'E': out += bytes([0x1b, int(v, 16)])
            else: out.append(int(v, 16))
            i = m.end(); continue
        ch = text[i]; i += 1
        if ch == '\n': out.append(0x0a)
        elif ch == chr(0x2009): out += tb[' ']          # 얇은 공백 → 폰트의 좁은 공백(7px)
        elif ch == ' ' and not narrow_space: out.append(0x20)
        elif ch in s1: out += s1[ch]
        elif ch in tb: out += tb[ch]
        elif ord(ch) < 0x80: out.append(ord(ch))
        else:
            b = ch.encode('cp932')
            assert len(b) == 2, (ch, text)
            out += b
    return bytes(out)
