"""MFZQ(qtx) / XTex 텍스처 해독. MFZQ: +0x30 w,h,log2w,log2h,psm(0x13=8bpp,0x14=4bpp,0=32bpp), 픽셀 +0x200,
팔레트 = 픽셀 끝 + 0x80 (8bpp 는 CSM1 스위즐). 스위즐 여부는 정돈도 점수로 판별."""
import struct, numpy as np, swz, gsmem, os
_c4 = {}
def unswz4(raw, w, h):
    """PSMT4 (PSMCT32 폭64 업로드) — zfont 과 같은 방식, 크기별 캐시."""
    k = (w, h)
    if k not in _c4:
        bw = max(1, w // 64)
        A4 = np.array([[gsmem.addr4(0, bw if bw % 2 == 0 or bw == 1 else bw, x, y) for x in range(w)] for y in range(h)], np.int64)
        n = w * h // 2; W = 64; H = max(1, n // 4 // W)
        I = np.array([[gsmem.addr32(0, 1, x, y) for x in range(W)] for y in range(H)], np.int64)
        inv = np.full(4 << 20, -1, np.int64); lin = np.arange(W * H * 4).reshape(H, W, 4)
        for q in range(4): inv[I + q] = lin[..., q]
        b = inv[A4 >> 1]; _c4[k] = np.where(b < 0, 0, b * 2 + (A4 & 1))
    nib = np.stack([raw & 15, raw >> 4], -1).reshape(-1)
    return nib[_c4[k]]
def csm1(pal):
    p = pal.copy()
    for i in range(0, 256, 32):
        p[i+8:i+16], p[i+16:i+24] = pal[i+16:i+24].copy(), pal[i+8:i+16].copy()
    return p
_cg = {}
def gs_maps(w, h, bpp):
    """업로드 폭 후보별 (선형 인덱스 맵) 목록: PSMCT32 로 올리고 PSMT8/PSMT4 로 읽음."""
    k = (w, h, bpp)
    if k in _cg: return _cg[k]
    rbw = max(1, w // 64)
    if bpp == 8:
        A = np.array([[gsmem.addr8(0, rbw if rbw % 2 == 0 else rbw + 1, x, y) for x in range(w)] for y in range(h)], np.int64) * 2
    else:
        A = np.array([[gsmem.addr4(0, rbw if rbw % 2 == 0 else rbw + 1, x, y) for x in range(w)] for y in range(h)], np.int64)
    nbytes = w * h * bpp // 8
    maps = []
    for W in (64, 128, 256, 512):
        H = nbytes // 4 // W
        if H < 1: continue
        I = np.array([[gsmem.addr32(0, W // 64, x, y) for x in range(W)] for y in range(H)], np.int64)
        inv = np.full(8 << 20, -1, np.int64); lin = np.arange(W * H * 4).reshape(H, W, 4)
        for q in range(4): inv[I + q] = lin[..., q]
        b = inv[A >> 1]
        m = np.where(b < 0, 0, b * 2 + (A & 1))   # 니블 위치
        maps.append(m)
    _cg[k] = maps
    return maps
def score(a): return (a[:, 1:] != a[:, :-1]).mean() + (a[1:] != a[:-1]).mean()
def decode_mfzq(d, o=0):
    w, h, lw, lh, psm = struct.unpack_from('<5I', d, o + 0x30)
    pix = o + 0x200
    if psm == 0x13:
        n = w * h; raw = np.frombuffer(d[pix:pix+n], np.uint8)
        a = raw.reshape(h, w)
        if w >= 16 and h >= 4:
            if w >= 256 and h >= 32:
                b = raw[np.minimum(gs_maps(w, h, 8)[0] // 2, n - 1)]
            else:
                b = swz.unswizzle8(d[pix:pix+n], w, h)
            if score(b) < score(a): a = b
        pal = np.frombuffer(d[pix+n+0x80:pix+n+0x80+1024], np.uint8).reshape(256, 4)
        pal = csm1(pal)
    elif psm == 0x14:
        n = w * h // 2; raw = np.frombuffer(d[pix:pix+n], np.uint8)
        a = np.stack([raw & 15, raw >> 4], -1).reshape(h, w)
        if w >= 32 and h >= 16:
            nib = np.stack([raw & 15, raw >> 4], -1).reshape(-1)
            for m in gs_maps(w, h, 4):
                b = nib[np.minimum(m, 2 * n - 1)]
                if score(b) < score(a): a = b
        pal = np.frombuffer(d[pix+n+0x80:pix+n+0x80+64], np.uint8).reshape(16, 4)
    elif psm == 0:
        n = w * h * 4
        return np.frombuffer(d[pix:pix+n], np.uint8).reshape(h, w, 4).copy()
    else:
        return None
    return pal[a]
def to_rgb(rgba, bg=(40, 40, 40)):
    a = np.clip(rgba[..., 3:4].astype(float) / 128, 0, 1)
    return (rgba[..., :3] * a + np.array(bg) * (1 - a)).astype(np.uint8)
