"""빌드된 ISO 의 RES.RBB 전 항목 검사: zlib 해제·EXIX 크기 일치·ISO 디렉터리 크기 안."""
import sys, os, struct, zlib
sys.path.insert(0, os.path.dirname(__file__))
import iso, rbb
path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), '..', "Zill O'll Infinite (Japan) (Korean).iso")
iso.ISO = path
# 디렉터리 레코드에서 RES.RBB 위치 읽기
with open(path, 'rb') as f:
    f.seek(261 * 2048); d = f.read(2048); p = 0; loc = {}
    while d[p]:
        nl = d[p + 32]; nm = d[p + 33:p + 33 + nl].decode(); loc[nm] = struct.unpack_from('<II', d, p + 2)[0], struct.unpack_from('<I', d, p + 10)[0]
        p += d[p]
print(loc)
iso.FILES['RES.RBB'] = loc['RES.RBB;1']; iso.FILES['RES.RID'] = loc['RES.RID;1']
_r = iso.read
iso.read = lambda lba, size, iso_=None: _r(lba, size, path)
R = rbb.RBB()
bad = 0
with open(path, 'rb') as f:
    for i in range(R.n):
        o, s = R.ent[i]; n = s & 0x7fffffff
        if R.data0 + o + n > R.size: print('범위 밖', i); bad += 1; continue
        f.seek(R.lba * 2048 + R.data0 + o); b = f.read(n)
        try:
            u = zlib.decompress(b) if s & 0x80000000 else b
        except Exception as e:
            print('해제 실패', i, e); bad += 1; continue
        if len(u) != R.usize[i]: print('크기 불일치', i, len(u), R.usize[i]); bad += 1
print('entries', R.n, 'bad', bad)
