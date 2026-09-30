"""PS2 텍스처 스위즐(PSMT8 / PSMT4) 풀기·걸기 — 표준 unswizzle 공식."""
import numpy as np
def _map8(w, h):
    y, x = np.mgrid[0:h, 0:w]
    block = (y & ~0xf) * w + (x & ~0xf) * 2
    swap = (((y + 2) >> 2) & 1) * 4
    posy = (((y & ~3) >> 1) + (y & 1)) & 7
    col = posy * w * 2 + ((x + swap) & 7) * 4
    byte = ((y >> 1) & 1) + ((x >> 2) & 2)
    return block + col + byte
def unswizzle8(buf, w, h):
    return np.frombuffer(buf, np.uint8)[_map8(w, h)]
def swizzle8(img):
    h, w = img.shape
    out = np.zeros(w*h, np.uint8); out[_map8(w, h)] = img; return out.tobytes()
