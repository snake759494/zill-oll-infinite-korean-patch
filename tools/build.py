"""전체 빌드: 원본 ISO → 한글판 ISO.
  python tools/build.py [--out 경로] [--no-movie]
번역: translation/ko/*.jsonl  ({"jp": 원문 표기, "ko": 번역 표기})  — units.py 표기 형식."""
import os, sys, json, glob, shutil, argparse, struct, re
sys.path.insert(0, os.path.dirname(__file__))
import iso, rbb, zmsg, units, isopatch, elfpatch, build_font, hangul

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, "Zill O'll Infinite (Japan) (Korean).iso")
TR = os.path.join(ROOT, 'translation', 'ko')

def load_translation():
    tr = {}
    jobs = os.path.join(ROOT, 'translation', 'jobs'); outs = os.path.join(ROOT, 'translation', 'out')
    for fn in sorted(glob.glob(os.path.join(outs, '*.jsonl'))):
        src = {}
        jf = os.path.join(jobs, os.path.basename(fn))
        if not os.path.exists(jf): continue
        for l in open(jf, encoding='utf-8'):
            o = json.loads(l); src[o['id']] = o['jp']
        for l in open(fn, encoding='utf-8'):
            if not l.strip(): continue
            o = json.loads(l)
            if o.get('id', -1) in src and o.get('ko') is not None: tr[src[o['id']]] = o['ko']
    id2jp = {}
    for jf in glob.glob(os.path.join(jobs, '*.jsonl')):
        for l in open(jf, encoding='utf-8'):
            o = json.loads(l); id2jp[o['id']] = o['jp']
    for fn in sorted(glob.glob(os.path.join(TR, '*.jsonl'))):
        for line in open(fn, encoding='utf-8'):
            line = line.strip()
            if not line: continue
            o = json.loads(line)
            if o.get('ko') is None: continue
            if 'jp' in o: tr[o['jp']] = o['ko']
            else: tr[id2jp[o['id']]] = o['ko']          # 수정 파일은 작업 id 기준
    return tr

WIDE_PAD = '　'
def recenter(jp, ko):
    """원문 줄이 전각 공백으로 가운데 맞춤된 경우 번역 줄도 같은 가운데에 맞춘다."""
    jl = jp.split('\n'); kl = ko.split('\n')
    if not all(l.startswith(WIDE_PAD) or not l.strip() for l in jl[:1]) or len(jl) < 2:
        return ko
    if sum(1 for l in jl if l.startswith(WIDE_PAD)) < len(jl) * 0.6:
        return ko
    width = lambda s: sum(0.5 if ord(c) < 0x80 else 1 for c in re.sub(r'<[A-Z][0-9A-Za-z]{1,2}>', '', s))
    full = max(width(l) for l in jl)
    out = []
    for l in kl:
        t = l.strip(' 　')
        pad = max(0.0, (full - width(t)) / 2)
        out.append(WIDE_PAD * int(pad) + (' ' if pad - int(pad) >= 0.5 else '') + t)
    return '\n'.join(out)

def build_messages(tr, stats):
    repl = {}
    for f in units.msg_files():
        d = open(os.path.join(units.RES, f), 'rb').read()
        ents = []
        for e in zmsg.parse(d):
            pages, tail = units.split_pages(e)
            nb = bytearray()
            for h, body in pages:
                jp = units.to_text(body)
                if jp in tr:
                    ko = tr[jp]
                    if ko.startswith('　') is False and jp.startswith('　'):
                        ko = recenter(jp, ko)
                    if h:   # 조건 머리 뒤 반각 숫자는 조건값으로 읽히므로 전각으로
                        m = re.match(r'[0-9]+', ko)
                        if m: ko = ''.join(chr(ord(c) + 0xFEE0) for c in m.group()) + ko[m.end():]
                    body = units.encode(ko, single=True); stats['tr'] += 1
                else:
                    stats['untr'] += 1
                nb += h + body + b'\x05\x05\x05'
            ents.append(bytes(nb) + tail)
        repl[int(f[:5])] = zmsg.build16(ents)
    return repl

def used_syllables(tr):
    import namegrid
    u = set()
    for ko in tr.values(): u.update(ko)
    for l in open(os.path.join(ROOT, 'translation', 'elf_out.jsonl'), encoding='utf-8'): u.update(json.loads(l)['ko'])
    for fn in ('elf_extra.json', 'item_names.json'):
        for o in json.load(open(os.path.join(ROOT, 'translation', fn), encoding='utf-8')): u.update(o['ko'])
    u.update(namegrid.SYL); u.update('한글이름영숫맡김공백취소입력완료기호중지')
    return {c for c in u if '가' <= c <= '힣'}

def check_message_budget(repl):
    """메시지 버퍼 규칙(PLAN.md '멈춤 방지 규칙'). 어기면 빌드 중단."""
    errs = []
    for f in units.msg_files():
        k = int(f[:5]); orig = os.path.getsize(os.path.join(units.RES, f))
        n = len(repl[k].rstrip(bytes(1)))
        if n > elfpatch.MSG_LIMIT - elfpatch.GEN_START:
            errs.append('%s %d > 일반 구역 %d' % (f, n, elfpatch.MSG_LIMIT - elfpatch.GEN_START))
        if orig <= 0x6800 and n > elfpatch.G0_END:
            errs.append('%s %d > 그룹0 구역 %d' % (f, n, elfpatch.G0_END))
        if orig <= 0x2000 and n > elfpatch.GEN_START - elfpatch.G0_END:
            errs.append('%s %d > A5~A7 구역 %d' % (f, n, elfpatch.GEN_START - elfpatch.G0_END))
    # 줄바꿈 없는 짧은 문자열(이름·항목명 등)은 고정 칸에 복사될 수 있음:
    # 파일마다 한글판 최장 ≤ 원본 최장
    for f in units.msg_files():
        d = open(os.path.join(units.RES, f), 'rb').read()
        new = zmsg.parse(repl[int(f[:5])])
        omax = nmax = 0
        for e in zmsg.parse(d):
            for h, body in units.split_pages(e)[0]:
                if 0x0a not in body: omax = max(omax, len(body))
        for e in new:
            for h, body in units.split_pages(e)[0]:
                if 0x0a not in body: nmax = max(nmax, len(body))
        if nmax > omax: errs.append('%s 한 줄 문자열 최장 %d > 원본 %d' % (f, nmax, omax))
    mx = max(len(repl[int(f[:5])].rstrip(bytes(1))) for f in units.msg_files())
    print('message budget: max %d / 일반 구역 %d (여유 %d)' % (mx, elfpatch.MSG_LIMIT - elfpatch.GEN_START, elfpatch.MSG_LIMIT - elfpatch.GEN_START - mx))
    if errs:
        raise SystemExit('메시지 버퍼 규칙 위반:' + chr(10) + chr(10).join(errs))

def apply_elf_text(elf):
    import elf_text
    p = os.path.join(ROOT, 'translation', 'elf_out.jsonl')
    if not os.path.exists(p): return elf
    src = {json.loads(l)['off']: json.loads(l) for l in open(os.path.join(ROOT, 'translation', 'elf_jobs.jsonl'), encoding='utf-8')}
    tr = []
    for l in open(p, encoding='utf-8'):
        if not l.strip(): continue
        o = json.loads(l); s = src.get(o['off'])
        if s is None or o['ko'] == s['jp']: continue
        try:
            if len(units.encode(o['ko'], False)) > s['len']: continue
        except Exception: continue
        tr.append({'off': s['off'], 'len': s['len'], 'ko': o['ko']})
    # 짧은 문자열(직접 번역): 뒤쪽 0 채움까지 쓸 수 있음
    ex = os.path.join(ROOT, 'translation', 'elf_extra.json')
    if os.path.exists(ex):
        for o in json.load(open(ex, encoding='utf-8')):
            off = o['off']; cap = len(o['jp'].encode('cp932'))
            z = 0
            while elf[off + cap + z] == 0 and z < 64: z += 1
            cap += max(0, z - 1)                      # 뒤따르는 0 채움(마지막 1바이트는 종료 NUL)
            b = units.encode(o['ko'], False)
            if len(b) <= cap: tr.append({'off': off, 'len': cap, 'ko': o['ko']})
            else: print('  elf_extra 넘침', hex(off), o['ko'])
    print('elf strings', len(tr))
    return elf_text.apply(elf, tr)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=OUT)
    a = ap.parse_args()
    assert os.path.abspath(a.out) != os.path.abspath(iso.ISO)
    tr = load_translation()
    stats = {'tr': 0, 'untr': 0}
    R = rbb.RBB()
    repl = build_messages(tr, stats)
    check_message_budget(repl)
    frb, nglyph = build_font.build(used=used_syllables(tr))
    repl[12] = frb
    import images
    repl.update(images.build())
    # 아이템 기본 이름(00001.dat, 34바이트 레코드의 16바이트 칸)
    db = bytearray(open(os.path.join(units.RES, '00001.dat'), 'rb').read())
    for o in json.load(open(os.path.join(ROOT, 'translation', 'item_names.json'), encoding='utf-8')):
        b = units.encode(o['ko'])[:15]
        db[o['off']:o['off'] + 16] = b + bytes([0]) + bytes([0xcd]) * (15 - len(b))
    repl[1] = bytes(db)
    print('messages: translated %(tr)d / untranslated %(untr)d pages' % stats, 'glyphs', nglyph)
    shutil.copyfile(iso.ISO, a.out)                 # 매번 원본에서 시작
    with open(a.out, 'r+b') as f:
        # ★RES.RBB 는 원본 배치 그대로 제자리 교체(PLAN.md 멈춤 방지 규칙 0). RID·ISO 레코드 불변.
        rbb.build_inplace(R, repl, f)
        elf = elfpatch.apply(iso.readfile('SLPM_658.92'))
        elf = apply_elf_text(elf)
        import namegrid
        elf, ncell = namegrid.apply(elf); print('name grid cells', ncell)
        f.seek(332 * 2048); f.write(elf)
    print('written', a.out)

if __name__ == '__main__':
    main()
