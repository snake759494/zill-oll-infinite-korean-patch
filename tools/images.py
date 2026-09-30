"""그림 글자 한글화 작업 목록. build.py 가 images.build() 로 {항목번호: 새 바이트} 를 받는다."""
import os, numpy as np
import tex_edit as T
ROOT = os.path.join(os.path.dirname(__file__), '..')
RES = os.path.join(ROOT, 'work', 'res')
FB = os.path.join(ROOT, 'NanumSquareNeo-dEb.ttf')   # 굵은 글자
FM = os.path.join(ROOT, 'NanumSquareNeo-cBd.ttf')

dark = lambda s: (s[..., :3].mean(-1) < 110) & (s[..., 3] > 40)
bright = lambda s: (s[..., :3].mean(-1) > 110) & (s[..., 3] > 40)
banner_txt = lambda s: ~((s[..., 0] > 2 * s[..., 1] + 15) & (s[..., 0] > 45)) & (s[..., 3] > 40)

SIGNS = {4: '길드', 5: '주점', 6: '여관', 7: '대장간', 8: '도구점'}
# 상태 아이콘(00026.mqt): (x, y, 글자)
ICONS = [(80, 0, '독'), (96, 0, '환'), (112, 0, '석'), (128, 0, '마비'), (144, 0, '잠'),
         (80, 16, '주'), (96, 16, '묵'), (112, 16, '혼'), (128, 16, '사'),
         (176, 32, '암'), (160, 48, '실'), (176, 48, '속'), (160, 64, '력'), (176, 64, '지'),
         (160, 80, '둔'), (176, 80, '광'), (160, 96, '방'), (176, 96, '방'), (160, 112, '생')]

TAN = None
def icon(t, x, y, ch):
    img = T.rgba(t)[y:y+16, x:x+16]
    bg = TAN
    diff = np.abs(img[..., :3] - bg[:3]).sum(-1)
    txt = img[diff > 120]
    fill = (20, 15, 10, 255)
    if len(txt):
        c = txt.mean(0)[:3]
        if c.max() - c.min() > 60: fill = tuple(int(v) for v in c) + (255,)   # 녹색·파랑 글자
    px = 14 if len(ch) == 1 else 8
    inner = np.zeros((16, 16), bool); inner[1:15, 1:15] = True
    T.replace_text(t, (x, y, x + 16, y + 16), lambda s: inner, ch, FB, px, fill,
                   alpha_scale=int(bg[3]) or 128, dilate=0, flat=bg)

def repaint_banner(t, y0, y1):
    """배너 행 범위의 글자색을 지우고 행별 붉은 바탕색으로 다시 칠함(알파는 원본 유지)."""
    img = T.rgba(t); band = img[y0:y1]
    red = (band[..., 0] > 2 * band[..., 1] + 15) & (band[..., 0] > 45) & (band[..., 3] > 30)
    out = band.copy()
    for r in range(band.shape[0]):
        if red[r].any():
            col = np.median(band[r][red[r]][:, :3], 0)
        else:
            col = np.array([90., 15., 15.])
        m = band[r, :, 3] > 20
        out[r, m, :3] = col
    full = img.copy(); full[y0:y1] = out
    mask = np.zeros(img.shape[:2], bool); mask[y0:y1] = band[..., 3] > 20
    T.quantize(t, full, mask)

def build(preview_dir=None):
    out = {}
    for n, text in SIGNS.items():
        p = os.path.join(RES, '%05d.qtx' % n); d = open(p, 'rb').read()
        t = T.load(d)
        T.replace_text(t, (16, 5, 74, 25), dark, text, FB, 14 if len(text) == 2 else 12, (30, 20, 10, 255))
        out[n] = T.save(d, t)
        if preview_dir: T.preview(t, os.path.join(preview_dir, 'img_%05d.png' % n), 3)
    # 전투 배너
    p = os.path.join(RES, '00024.mqt'); d = open(p, 'rb').read(); o = d.find(b'MFZQ')
    t = T.load(d, o)
    repaint_banner(t, 0, 22); repaint_banner(t, 22, 46)
    T.replace_text(t, (30, 1, 150, 21), lambda s: np.zeros(s.shape[:2], bool), '선제공격', FB, 14, (250, 245, 235, 255), (40, 10, 10, 255), 1, dilate=1)
    T.replace_text(t, (30, 22, 200, 44), lambda s: np.zeros(s.shape[:2], bool), '기습당했다!', FB, 14, (250, 245, 235, 255), (40, 10, 10, 255), 1, dilate=1)
    out[24] = d[:o] + T.save(d[o:], {**t, 'pix': t['pix'] - o}) if o else T.save(d, t)
    if preview_dir: T.preview(t, os.path.join(preview_dir, 'img_00024.png'), 2)
    # 상태 아이콘
    p = os.path.join(RES, '00026.mqt'); d = open(p, 'rb').read(); o = d.find(b'MFZQ')
    t = T.load(d, o)
    global TAN
    ref = T.rgba(t)[1:15, 97:111].reshape(-1, 4)          # 幻 칸 배경(황갈색)
    TAN = np.median(ref[ref[..., :3].mean(-1) > 100], 0)
    for x, y, ch in ICONS: icon(t, x, y, ch)
    out[26] = d[:o] + T.save(d[o:], {**t, 'pix': t['pix'] - o}) if o else T.save(d, t)
    if preview_dir: T.preview(t, os.path.join(preview_dir, 'img_00026.png'), 3)
    # 투기장 대진 글자(00224.qtx 128x128)
    p = os.path.join(RES, '00224.qtx'); d = open(p, 'rb').read()
    t = T.load(d)
    clear = T.rgba(t)[127, 127].copy()                   # 투명 바탕
    vis = lambda s: s[..., 3] > 20
    for box, text, fill, ol in [((1, 1, 53, 23), '회전', (215, 225, 245, 255), (20, 30, 90, 255)),
                                ((54, 1, 110, 23), '결승', (250, 230, 60, 255), (10, 10, 10, 255)),
                                ((1, 24, 53, 46), '번째', (215, 225, 245, 255), (20, 30, 90, 255)),
                                ((54, 24, 124, 46), '준결승', (250, 230, 60, 255), (10, 10, 10, 255))]:
        T.replace_text(t, box, vis, text, FB, 15, fill, ol, 1, dilate=0, flat=clear)
    out[224] = T.save(d, t)
    if preview_dir: T.preview(t, os.path.join(preview_dir, 'img_00224.png'), 3)
    return out

if __name__ == '__main__':
    pd = os.path.join(ROOT, 'work', 'imgprev'); os.makedirs(pd, exist_ok=True)
    r = build(pd); print({k: len(v) for k, v in r.items()})
