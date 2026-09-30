"""ISO 파일 읽기 도우미 (2048 바이트 섹터 DVD ISO)."""
import os
ISO = os.path.join(os.path.dirname(__file__), '..', "Zill O'll Infinite (Japan).iso")
FILES = {  # name: (lba, size)
 'SYSTEM.CNF':(331,54),'SLPM_658.92':(332,3613104),'RES.RID':(1640938,500016),
 'RES.RBB':(1132510,1041259302),'NOWLOAD.MQT':(2235,67552),'GZMVS.RBB':(681836,922980352),
 'DBGFONT.QTX':(2232,4896),
}
def read(lba, size, iso=ISO):
    with open(iso,'rb') as f:
        f.seek(lba*2048); return f.read(size)
def readfile(name):
    return read(*FILES[name])
