"""질올 메시지 파일(.dat): u16 개수 N, u16 오프셋 N개(파일 절대 위치), 본문.
본문 = CP932 + 1바이트 가나(0xA1-0xDF, 현재 모드 ESC H=히라가나, ESC K=가타카나)."""
import struct
HW = '｡｢｣､･ｦｧｨｩｪｫｬｭｮｯｰｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝﾞﾟ'
def parse(d):
    n = struct.unpack_from('<H', d, 0)[0]
    off = list(struct.unpack_from('<%dH' % n, d, 2))
    ends = off[1:] + [None]
    return [d[o:e] if e is not None else d[o:] for o, e in zip(off, ends)]
def is_msg(d):
    if len(d) < 6: return False
    n = struct.unpack_from('<H', d, 0)[0]
    if not n or 2+2*n > len(d): return False
    off = struct.unpack_from('<%dH' % n, d, 2)
    return off[0] == 2+2*n and all(off[i] <= off[i+1] for i in range(n-1)) and off[-1] <= len(d)
def decode(b):
    """사람이 읽는 문자열. 제어는 {..} 로 표시."""
    out = []; i = 0; mode = 'H'
    while i < len(b):
        c = b[i]
        if c == 0x1b:
            m = chr(b[i+1]);
            if m in 'HK': mode = m; out.append('{%s}' % m) if False else None
            else: out.append('{ESC%s}' % m)
            i += 2; continue
        if 0x81 <= c <= 0x9f or 0xe0 <= c <= 0xfc:
            out.append(b[i:i+2].decode('cp932', 'replace')); i += 2; continue
        if 0xa1 <= c <= 0xdf:
            ch = HW[c-0xa1]
            out.append(hw2fw(ch, mode)); i += 1; continue
        if 0x20 <= c < 0x7f:
            out.append(chr(c)); i += 1; continue
        out.append('{%02X}' % c); i += 1
    return ''.join(out)
import unicodedata
def hw2fw(ch, mode):
    k = unicodedata.normalize('NFKC', ch)
    if mode == 'H' and 'ァ' <= k <= 'ヶ':
        k = chr(ord(k) - 0x60)
    return k

def build32(entries):
    """u32 오프셋 형식: [u16 N][u16 0][u32 오프셋×N][본문], 파일 끝 0x800 정렬."""
    n = len(entries); head = 4 + 4*n
    offs = []; pos = head
    for e in entries:
        offs.append(pos); pos += len(e)
    out = struct.pack('<HH', n, 0) + struct.pack('<%dI' % n, *offs) + b''.join(entries)
    return out + bytes((-len(out)) % 0x800)

def parse32(d):
    """build32 형식 읽기(마지막 항목 뒤 0 채움 제거)."""
    n = struct.unpack_from('<H', d, 0)[0]
    off = list(struct.unpack_from('<%dI' % n, d, 4))
    ends = off[1:] + [len(d.rstrip(bytes(1)))]
    return [d[o:e] for o, e in zip(off, ends)]

def build16(entries):
    """원본 형식: [u16 N][u16 오프셋×N][본문]. 오프셋이 64KB 를 넘으면 예외."""
    n = len(entries); pos = 2 + 2*n; offs = []
    for e in entries:
        offs.append(pos); pos += len(e)
    assert offs[-1] <= 0xFFFF, ('u16 오프셋 초과', offs[-1])
    return struct.pack('<H', n) + struct.pack('<%dH' % n, *offs) + b''.join(entries)
