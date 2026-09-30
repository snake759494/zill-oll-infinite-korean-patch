"""RES.RBB (Koei 'RC ver2.1') 아카이브.
헤더 0x80부터 태그 구역: 'RIDX'+len : N×(u32 오프셋, u32 크기|0x80000000=zlib)
'TYPE'+len : N×4바이트 확장자, 'EXIX'+len : N×u32 풀린 크기, 'GAP0'+len : 채움.
데이터 시작 = GAP0 끝 (0x800 정렬). 오프셋은 데이터 시작 기준."""
import struct, zlib, iso
class RBB:
    def __init__(self, name='RES.RBB'):
        self.name = name
        self.lba, self.size = iso.FILES[name]
        h = iso.read(self.lba, 0x200000)
        self.head = h
        p = 0x80; sec = {}
        while True:
            tag = h[p:p+4]; ln = struct.unpack_from('<I', h, p+4)[0]
            sec[tag] = (p+8, ln); p += 8 + ln
            if tag == b'GAP0': break
        self.sec = sec
        o, ln = sec[b'RIDX']; self.n = n = ln // 8
        self.ent = [struct.unpack_from('<II', h, o+8*k) for k in range(n)]
        o, _ = sec[b'TYPE']
        self.ext = [h[o+4*k:o+4*k+4].rstrip(b'0').decode('latin1') for k in range(n)]
        o, _ = sec[b'EXIX']
        self.usize = list(struct.unpack_from('<%dI' % n, h, o))
        self.data0 = (p + 0x7ff) & ~0x7ff
    def _read(self, off, size):
        with open(iso.ISO, 'rb') as f:
            f.seek(self.lba*2048 + off); return f.read(size)
    def raw(self, i):
        o, s = self.ent[i]
        return self._read(self.data0 + o, s & 0x7fffffff)
    def get(self, i):
        d = self.raw(i)
        if self.ent[i][1] & 0x80000000:
            d = zlib.decompress(d)
        return d
if __name__ == '__main__':
    import sys
    r = RBB(sys.argv[1] if len(sys.argv) > 1 else 'RES.RBB')
    print(r.n, hex(r.data0), {k: hex(v[1]) for k, v in r.sec.items()})

def build(r, repl, out_path, level=9):
    """repl: {항목번호: 풀린 바이트}. 나머지는 원본 압축 그대로 복사. out_path 에 새 RBB 저장, 크기 반환."""
    import io
    head = bytearray(r.head[:r.data0])
    o_ridx = r.sec[b'RIDX'][0]; o_exix = r.sec[b'EXIX'][0]
    with open(iso.ISO, 'rb') as src, open(out_path, 'wb') as out:
        out.write(bytes(len(head)))
        pos = 0
        for i in range(r.n):
            o, s = r.ent[i]
            if i in repl:
                u = repl[i]
                c = zlib.compress(u, level)
                if s & 0x80000000 or len(c) < len(u):
                    data, flag = c, 0x80000000
                else:
                    data, flag = u, 0
                usz = len(u)
            else:
                src.seek(r.lba*2048 + r.data0 + o); data = src.read(s & 0x7fffffff)
                flag = s & 0x80000000; usz = r.usize[i]
            struct.pack_into('<II', head, o_ridx + 8*i, pos, len(data) | flag)
            struct.pack_into('<I', head, o_exix + 4*i, usz)
            out.write(data)
            pad = (-len(data)) % 0x80
            out.write(bytes(pad)); pos += len(data) + pad
        total = r.data0 + pos
        pad = (-total) % 2048; out.write(bytes(pad))
        out.seek(0); out.write(head)
    return total

def build_append(r, repl, f, level=9):
    """원본 RES.RBB 자리(LBA 그대로)에서: 헤더만 고치고, 바뀐 항목은 원본 데이터 끝 뒤에 덧붙인다.
    바뀌지 않은 항목은 원본과 같은 위치·같은 바이트 → 패치 크기 최소. f 는 r+b 로 연 ISO. 새 RBB 크기 반환."""
    head = bytearray(r.head[:r.data0])
    o_ridx = r.sec[b'RIDX'][0]; o_exix = r.sec[b'EXIX'][0]
    base = r.lba * 2048
    pos = r.size - r.data0                        # 원본 데이터 끝(데이터 기준)
    pos = (pos + 0x7f) & ~0x7f
    for i in sorted(repl):
        u = repl[i]; c = zlib.compress(u, level)
        data, flag = (c, 0x80000000) if len(c) < len(u) else (u, 0)
        struct.pack_into('<II', head, o_ridx + 8*i, pos, len(data) | flag)
        struct.pack_into('<I', head, o_exix + 4*i, len(u))
        f.seek(base + r.data0 + pos); f.write(data)
        pos += (len(data) + 0x7f) & ~0x7f
    f.seek(base); f.write(head)
    total = r.data0 + pos
    f.seek(base + total); f.write(bytes((-total) % 2048))
    return total


def build_inplace(r, repl, f, level=9):
    """★원본 배치 그대로: 각 수정 항목을 원래 오프셋·원래 칸 안에 쓰고, 풀린 크기는 원본과 동일(0 채움).
    규칙 위반(내용 > 원본 풀린 크기, 압축 > 원래 칸)이면 예외. RBB 크기·RES.RID·ISO 레코드 불변."""
    head = bytearray(r.head[:r.data0])
    o_ridx = r.sec[b'RIDX'][0]
    base = r.lba * 2048
    errs = []
    for i in sorted(repl):
        u = repl[i].rstrip(bytes(1)) if r.ext[i] in ('dat', 'NONE') else repl[i]
        if len(u) > r.usize[i]:
            errs.append('항목 %d: 풀린 크기 %d > 원본 %d' % (i, len(u), r.usize[i])); continue
        u = u + bytes(r.usize[i] - len(u))
        o, s = r.ent[i]
        slot = (r.ent[i+1][0] if i + 1 < r.n else r.size - r.data0) - o
        c = min((zlib.compress(u, lv) for lv in (9, 6)), key=len)
        if not (s & 0x80000000):
            c = u
        if len(c) > slot:
            errs.append('항목 %d: 압축 %d > 칸 %d' % (i, len(c), slot)); continue
        struct.pack_into('<I', head, o_ridx + 8*i + 4, len(c) | (s & 0x80000000))
        f.seek(base + r.data0 + o); f.write(c + bytes(slot - len(c)))
    if errs:
        raise SystemExit('RBB 제자리 규칙 위반:' + chr(10) + chr(10).join(errs))
    f.seek(base); f.write(head)
