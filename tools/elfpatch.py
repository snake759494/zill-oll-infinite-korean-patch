"""실행파일 코드 패치.
메시지 접근(0x183450 함수): 오프셋표 u16 → u32. 새 메시지 파일 형식 = [u16 개수][u16 0][u32 오프셋 × N][본문]."""
import struct
def fo(va): return va - 0x100000 + 0x1000
def sll(rd, rt, sa): return (rt << 16) | (rd << 11) | (sa << 6)
def lw(rt, off, base): return (0x23 << 26) | (base << 21) | (rt << 16) | (off & 0xffff)
def lhu(rt, off, base): return (0x25 << 26) | (base << 21) | (rt << 16) | (off & 0xffff)
V0, V1, S1 = 2, 3, 17
MSG32 = [  # (va, 원래 명령, 새 명령)
    (0x1834a0, sll(V0, S1, 1), sll(V0, S1, 2)),
    (0x1834ec, lhu(V1, 2, V0), lw(V1, 4, V0)),
    (0x183588, sll(V1, S1, 1), sll(V1, S1, 2)),
    (0x1835e8, lhu(V0, 2, V1), lw(V0, 4, V1)),
]
# 메시지 버퍼(0xB69CEC, 게임 데이터 0xB83028 직전까지 = 0x1933C 바이트) 구역:
#   그룹0 [0, 0x6800) / 그룹 A5~A7 [0x6800, GEN_START) / 일반 [GEN_START, MSG_LIMIT)
# 원본 일반 구역 시작 0x8800 → 한글판 A5~A7 파일(최대 8.4KB)에 맞춰 0x8A00.
MSG_BUF = 0xB69CEC
MSG_LIMIT = 0xB83028 - MSG_BUF        # 0x1933C: 이 뒤는 다른 게임 데이터(코드가 직접 참조)
G0_END = 0x6800
GEN_START = 0x8800
BUF = [
    (0x1843a4, 0x34028800, 0x34020000 | GEN_START),   # ori v0,zero,0x8800 → GEN_START
]
# ★원본 u16 메시지 형식 유지 → MSG32 불필요. 구역 경계도 원본(0x8800) 유지 가능하면 BUF 도 불필요.
PATCHES = []
def apply(elf):
    elf = bytearray(elf)
    for va, old, new in PATCHES:
        cur = struct.unpack_from('<I', elf, fo(va))[0]
        assert cur == old, (hex(va), hex(cur), hex(old))
        struct.pack_into('<I', elf, fo(va), new)
    return bytes(elf)
