"""RES.RBB 전체를 work/res/NNNNN.ext 로 풀기."""
import os, rbb, iso
out = os.path.join(os.path.dirname(__file__), '..', 'work', 'res'); os.makedirs(out, exist_ok=True)
r = rbb.RBB()
with open(iso.ISO, 'rb') as f:
    import zlib
    for i in range(r.n):
        o, s = r.ent[i]
        f.seek(r.lba*2048 + r.data0 + o); d = f.read(s & 0x7fffffff)
        if s & 0x80000000: d = zlib.decompress(d)
        open(os.path.join(out, '%05d.%s' % (i, r.ext[i])), 'wb').write(d)
print('done')
