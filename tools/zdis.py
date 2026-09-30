import capstone,struct,sys,os
d=open(os.path.join(os.path.dirname(__file__),'..','work','ext','SLPM_658.92'),'rb').read()
md=capstone.Cs(capstone.CS_ARCH_MIPS,capstone.CS_MODE_MIPS32+capstone.CS_MODE_LITTLE_ENDIAN); md.skipdata=True
def dis(va,n):
    fo=va-0x100000+0x1000
    for i in md.disasm(d[fo:fo+4*n],va): print('%08x  %s %s'%(i.address,i.mnemonic,i.op_str))
if __name__=='__main__': dis(int(sys.argv[1],16),int(sys.argv[2]))
