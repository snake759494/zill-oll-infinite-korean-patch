"""JillAll 폰트 재구성: 비한자 원본 글리프 유지 + 한글(hangul.table) 추가, 한자 글리프는 뺀다.
배치 19px 간격 53x53칸, 레코드는 유니코드 순. 노드 크기·텍스처 오프셋·상위 노드 크기 갱신."""
import struct, numpy as np
import zfont, glyph, hangul

PITCH = 19
SPACE_W = 7
COLS = (1024 - 1) // PITCH          # 53
KEEP_KANJI = set()                  # 남길 한자(없음)

def quantizer(pal):
    alpha = pal[:, 3].astype(float)
    cand = np.array([1, 6, 3, 5, 4, 2])   # 알파 0,8,34,73,118,155 — 6단계(압축 크기를 원본 칸 이하로)
    ca = alpha[cand]
    def q(v):
        return cand[np.abs(ca[None, :] - (v.ravel() * 155)[:, None]).argmin(1)].reshape(v.shape).astype(np.uint8)
    return q

def build(frb=None, used=None):
    d = bytearray(frb if frb is not None else open(zfont.FRB, 'rb').read())
    base = zfont.ALL
    recs = zfont.records(d)
    img = zfont.decode(d).reshape(1024, 1024)
    q = quantizer(zfont.palette(d))
    glyphs = {}   # code -> 18x18 index array
    for r in recs:
        c = r[0]
        if 0x4E00 <= c <= 0x9FFF and chr(c) not in KEEP_KANJI: continue
        x0, y0 = int(r[1]), int(r[2])
        glyphs[c] = img[y0:y0+18, x0:x0+18].copy()
    narrow = set()
    # ★글자 수 ≤ 원본(2438) → 폰트 파일 크기 ≤ 원본. 사용 음절 전부 + 남는 칸은 완성형 순서로.
    table = hangul.table()
    room = len(recs) - sum(1 for c in glyphs) - 1          # 1 = 좁은 공백
    syl = [ch for ch in table if ch != ' ']
    if used is not None:
        used = [ch for ch in syl if ch in used]
        rest = [ch for ch in syl if ch not in set(used)]
        assert len(used) <= room, ('사용 음절이 폰트 칸보다 많음', len(used), room)
        keep = set(used + rest[:room - len(used)])
    else:
        keep = set(syl)
    for ch, sj in table.items():
        if ch != ' ' and ch not in keep: continue
        if ch == ' ':
            glyphs[hangul.unicode_of(sj)] = np.ones((18, 18), np.uint8); narrow.add(hangul.unicode_of(sj))
        else:
            glyphs[hangul.unicode_of(sj)] = q(glyph.render(ch))
    for ch, b in hangul.single().items():             # 1바이트 코드 → 히라가나 칸에 음절/공백
        u = hangul.single_unicode(b[0])
        if ch == ' ':
            glyphs[u] = np.ones((18, 18), np.uint8); narrow.add(u)
        else:
            glyphs[u] = q(glyph.render(ch))
    codes = sorted(glyphs)
    assert len(codes) <= COLS * COLS, len(codes)
    new = np.ones((1024, 1024), np.uint8)       # 1 = 투명
    rec = bytearray()
    for k, c in enumerate(codes):
        x = 1 + (k % COLS) * PITCH; y = 1 + (k // COLS) * PITCH
        new[y:y+18, x:x+18] = glyphs[c]
        wdt = SPACE_W if c in narrow else 18
        rec += struct.pack('<I4f4B', c, x, y, x + wdt, y + 18, 0, wdt, wdt, 0)
    # 노드 재조립: [이름 0x20][본문: 헤더(0x80) + 레코드 + 채움 + 텍스처]
    body0 = base + 0x20
    size, _m1, texoff, texsize = struct.unpack_from('<IiII', d, base + 0x1c)
    tex = bytearray(d[body0 + texoff: body0 + texoff + texsize])
    old_rec_end = base + 0xa0 + 24 * len(recs)
    gap = d[old_rec_end: body0 + texoff]                  # 레코드 끝~텍스처 사이(0 채움)
    new_rec_end = base + 0xa0 + len(rec)
    new_tex_abs = (new_rec_end + len(gap) + 0x7f) & ~0x7f
    new_texoff = new_tex_abs - body0
    # 픽셀 교체
    pix_rel = zfont.PIX - (body0 + texoff)
    tex[pix_rel: pix_rel + zfont.PIXLEN] = zfont.encode(new)
    node = bytearray(d[base: base + 0xa0]) + rec
    node += bytes(new_tex_abs - base - len(node)) + tex
    new_size = len(node) - 0x20
    struct.pack_into('<I', node, 0x1c, new_size)
    struct.pack_into('<I', node, 0x24, new_texoff)
    struct.pack_into('<I', node, 0x30, len(codes))
    delta = new_size - size
    out = d[:base] + node + d[base + 0x20 + size:]
    for top in (0x0, 0x20):                                 # root, scene 크기
        v = struct.unpack_from('<I', out, top + 0x1c)[0]
        struct.pack_into('<I', out, top + 0x1c, v + delta)
    return bytes(out), len(codes)

if __name__ == '__main__':
    from PIL import Image
    out, n = build()
    print('glyphs', n, 'size', len(out))
    # 검증: 새 파일을 다시 읽어 표본 렌더
    base = zfont.ALL
    size, _m1, texoff, texsize = struct.unpack_from('<IiII', out, base + 0x1c)
    pix = base + 0x20 + texoff + (zfont.PIX - (base + 0x20 + 0xe520))
    raw = np.frombuffer(out[pix:pix + zfont.PIXLEN], np.uint8)
    nib = np.stack([raw & 15, raw >> 4], -1).reshape(-1)
    im = nib[zfont._maps()]
    a = zfont.palette(open(zfont.FRB, 'rb').read())[:, 3].astype(int)
    Image.fromarray((255 - np.clip(a[im] * 1.6, 0, 255)).astype(np.uint8)).crop((0, 0, 1024, 400)).save('../work/font_new.png')
