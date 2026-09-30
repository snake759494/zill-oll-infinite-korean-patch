"""MFZQ 8bpp 텍스처의 글자 영역을 지우고 한글을 다시 그린다(원본 팔레트로 양자화, 같은 스위즐로 재인코딩).
사용: images.py 의 작업 목록이 호출."""
import struct, numpy as np
from PIL import Image, ImageDraw, ImageFont
import swz, qtx, os

ROOT = os.path.join(os.path.dirname(__file__), '..')

def load(d, o=0):
    w, h, _, _, psm = struct.unpack_from('<5I', d, o + 0x30)
    assert psm == 0x13
    pix = o + 0x200; n = w * h
    raw = np.frombuffer(d[pix:pix+n], np.uint8)
    if w >= 256 and h >= 32:
        m = np.minimum(qtx.gs_maps(w, h, 8)[0] // 2, n - 1)
    else:
        m = swz._map8(w, h)
    idx = raw[m]
    palraw = np.frombuffer(d[pix+n+0x80:pix+n+0x80+1024], np.uint8).reshape(256, 4)
    pal = qtx.csm1(palraw)
    return {'w': w, 'h': h, 'pix': pix, 'map': m, 'idx': idx.copy(), 'pal': pal}

def save(d, t):
    d = bytearray(d); n = t['w'] * t['h']
    raw = np.frombuffer(bytes(d[t['pix']:t['pix']+n]), np.uint8).copy()
    raw[t['map']] = t['idx']
    d[t['pix']:t['pix']+n] = raw.tobytes()
    return bytes(d)

def rgba(t):
    return t['pal'][t['idx']].astype(np.float32)

def quantize(t, img, mask):
    """img(h,w,4 float) 의 mask 위치를 팔레트 최근접 색으로."""
    pal = t['pal'].astype(np.float32)
    ys, xs = np.nonzero(mask)
    px = img[ys, xs]
    dist = ((px[:, None, :] - pal[None, :, :]) ** 2 * np.array([1, 1, 1, 2])).sum(-1)
    t['idx'][ys, xs] = dist.argmin(1).astype(np.uint8)

def inpaint(img, mask, iters=60):
    """mask 영역을 주변 색으로 채움(반복 평균)."""
    img = img.copy(); known = ~mask
    for _ in range(iters):
        acc = np.zeros_like(img); cnt = np.zeros(img.shape[:2], np.float32)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sh = np.roll(np.roll(img, dy, 0), dx, 1); k = np.roll(np.roll(known, dy, 0), dx, 1)
            acc += sh * k[..., None]; cnt += k
        upd = (~known) & (cnt > 0)
        img[upd] = acc[upd] / cnt[upd][:, None]
        known = known | upd
    return img

def draw_text(size_wh, text, font_path, px, fill, outline=None, ow=1, bold=0):
    """RGBA float 레이어(4배 슈퍼샘플)."""
    W, H = size_wh; S = 4
    im = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im); f = ImageFont.truetype(font_path, px * S)
    bb = dr.textbbox((0, 0), text, font=f, stroke_width=ow * S if outline else 0)
    x = (W * S - (bb[2] - bb[0])) / 2 - bb[0]; y = (H * S - (bb[3] - bb[1])) / 2 - bb[1]
    if outline:
        dr.text((x, y), text, font=f, fill=outline, stroke_width=(ow + bold) * S, stroke_fill=outline)
    dr.text((x, y), text, font=f, fill=fill, stroke_width=bold * S, stroke_fill=fill)
    im = im.resize((W, H), Image.LANCZOS)
    return np.asarray(im, np.float32)

def replace_text(t, box, text_pred, text, font, px, fill, outline=None, ow=1, bold=0, alpha_scale=128, dilate=1, flat=None):
    """box=(x0,y0,x1,y1). text_pred(rgba)->bool 로 원래 글자 픽셀 검출 → 지우고 새 글자."""
    x0, y0, x1, y1 = box
    img = rgba(t)
    sub = img[y0:y1, x0:x1]
    m = text_pred(sub)
    # 글자 테두리까지 1px 넓힘
    mm = m.copy()
    for _ in range(dilate):
        b = mm.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            b |= np.roll(np.roll(mm, dy, 0), dx, 1)
        mm = b
    if flat is not None:          # 칸 전체를 한 색으로(아이콘)
        clean = sub.copy(); clean[mm] = flat
    else:
        clean = inpaint(sub, mm)
    lay = draw_text((x1 - x0, y1 - y0), text, font, px, fill, outline, ow, bold)
    a = lay[..., 3:4] / 255.0
    col = lay.copy(); col[..., 3] = alpha_scale
    out = clean * (1 - a) + col * a
    out[..., 3] = np.maximum(clean[..., 3], a[..., 0] * alpha_scale)
    full = img.copy(); full[y0:y1, x0:x1] = out
    mask = np.zeros(img.shape[:2], bool); mask[y0:y1, x0:x1] = mm | (a[..., 0] > 0.02)
    quantize(t, full, mask)

def preview(t, path, scale=3):
    im = Image.fromarray(qtx.to_rgb(t['pal'][t['idx']]))
    im.resize((t['w'] * scale, t['h'] * scale), Image.NEAREST).save(path)
