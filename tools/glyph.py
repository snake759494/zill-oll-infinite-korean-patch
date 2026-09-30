"""한글 글리프 렌더(18x18 칸, 회색조 0..1)."""
import os, numpy as np
from PIL import Image, ImageDraw, ImageFont
ROOT = os.path.join(os.path.dirname(__file__), '..')
FONT = os.path.join(ROOT, 'NanumSquareNeo-bRg.ttf')
SIZE = 17
CELL = 18
_f = {}
def font(path=FONT, size=SIZE):
    k = (path, size)
    if k not in _f: _f[k] = ImageFont.truetype(path, size)
    return _f[k]

def render(ch, path=FONT, size=SIZE, cell=CELL, dy=0):
    """ch 를 cell x cell 가운데 정렬로 그림. 4배 크게 그린 뒤 줄여 부드럽게."""
    S = 4
    f = font(path, size * S)
    im = Image.new('L', (cell * S, cell * S), 0)
    dr = ImageDraw.Draw(im)
    bb = dr.textbbox((0, 0), ch, font=f)
    w = bb[2] - bb[0]
    # 가로 가운데, 세로는 한글 기준선 고정('한' 박스 기준)
    hb = dr.textbbox((0, 0), '한', font=f)
    x = (cell * S - w) / 2 - bb[0]
    y = (cell * S - (hb[3] - hb[1])) / 2 - hb[1] + dy * S
    dr.text((x, y), ch, font=f, fill=255)
    im = im.resize((cell, cell), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255.0
