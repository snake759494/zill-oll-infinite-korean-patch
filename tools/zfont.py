"""00012.frb 폰트 뱅크 (Jill08/Jill10/JillAll/JillBtn/Jill8bit).
노드: +0 이름(32) +0x1c 노드크기 +0x20 -1 +0x24 텍스처오프셋(노드기준) +0x28 텍스처크기 +0x2c 1 +0x30 글자수
      +0x38 f16 f16  +0x40 'PlayStation2' ... +0xa0 글자 레코드 24B = [u32 유니코드][f x0,y0,x1,y1][u8 0,폭,진행,0]
텍스처(MFZQ): +0x40 w,h,log2w,log2h,psm(0x14=4bpp) ... 픽셀은 PSMCT32 폭64(bw1)로 올린 PSMT4 스위즐.
JillAll 1024x1024 4bpp, 팔레트 16색(흰색 + 알파) 픽셀 뒤."""
import struct, os, numpy as np
import gsmem
FRB = os.path.join(os.path.dirname(__file__), '..', 'work', 'res', '00012.frb')
NODES = {'Jill08': 0x40, 'Jill10': 0x51c0, 'JillAll': 0xa340, 'JillBtn': 0x98ba0, 'Jill8bit': 0xa1080}
ALL = 0xa340
PIX = 0x18a80           # JillAll 픽셀 시작(파일 오프셋)
PIXLEN = 0x80000
PAL = 0x98b00           # JillAll 팔레트
_CACHE = os.path.join(os.path.dirname(__file__), '..', 'work', 'swz4_1024.npy')

def records(d, base=ALL):
    n = struct.unpack_from('<I', d, base + 0x30)[0]
    return [list(struct.unpack_from('<I4f4B', d, base + 0xa0 + 24*k)) for k in range(n)]

def _maps():
    if os.path.exists(_CACHE):
        return np.load(_CACHE)
    # PSMT4(1024x1024, bw16) 각 픽셀의 니블 주소 → 선형 업로드(PSMCT32 64폭) 바이트 위치로 변환
    A4 = np.array([[gsmem.addr4(0, 16, x, y) for x in range(1024)] for y in range(1024)], np.int64)
    w, h = 64, 131072 // 64
    I = np.array([[gsmem.addr32(0, 1, x, y) for x in range(w)] for y in range(h)], np.int64)
    inv = np.zeros(4 << 20, np.int64) - 1
    lin = np.arange(w*h*4).reshape(h, w, 4)
    for k in range(4):
        inv[I + k] = lin[..., k]
    byte = inv[A4 >> 1]
    m = byte * 2 + (A4 & 1)       # 선형 니블 위치
    np.save(_CACHE, m)
    return m

def decode(d):
    raw = np.frombuffer(d[PIX:PIX+PIXLEN], np.uint8)
    nib = np.stack([raw & 15, raw >> 4], -1).reshape(-1)
    return nib[_maps()]

def encode(img):
    nib = np.zeros(PIXLEN*2, np.uint8)
    nib[_maps()] = np.asarray(img).reshape(1024, 1024)
    nib = nib.reshape(-1, 2)
    return (nib[:, 0] | (nib[:, 1] << 4)).astype(np.uint8).tobytes()

def palette(d):
    return np.frombuffer(d[PAL:PAL+64], np.uint8).reshape(16, 4)
