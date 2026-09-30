"""실행파일 SJIS 문자열 추출/적용. 제자리 교체(같은 바이트 길이 이하, 남는 곳 NUL)."""
import os, re, json, sys
sys.path.insert(0, os.path.dirname(__file__))
ROOT = os.path.join(os.path.dirname(__file__), '..')
ELF = os.path.join(ROOT, 'work', 'ext', 'SLPM_658.92')
PAT = re.compile(rb'(?:[\x81-\x9f\xe0-\xef][\x40-\xfc]|[\x20-\x7e\x0a])+\x00')
JP = re.compile('[ぁ-んァ-ヶ一-龯]')
def extract():
    d = open(ELF, 'rb').read(); out = []
    for m in PAT.finditer(d, 0x2e0000):
        b = m.group()[:-1]
        if m.start() > 0 and d[m.start()-1] not in (0,):  # 문자열 경계
            continue
        try: s = b.decode('cp932')
        except UnicodeDecodeError: continue
        if len(re.findall('[ぁ-んァ-ヶ一-龯]', s)) >= 2 and not re.search('[\x00-\x09]', s):
            out.append({'off': m.start(), 'len': len(b), 'jp': s})
    return out
def encode_ko(s):
    import units
    return units.encode(s, False)
def apply(elf, tr):
    elf = bytearray(elf)
    for o in tr:
        b = encode_ko(o['ko'])
        assert len(b) <= o['len'], (o['off'], o['ko'], len(b), o['len'])
        elf[o['off']:o['off'] + o['len']] = b + bytes(o['len'] - len(b))
    return bytes(elf)
if __name__ == '__main__':
    x = extract()
    with open(os.path.join(ROOT, 'translation', 'elf_jobs.jsonl'), 'w', encoding='utf-8') as f:
        for o in x: f.write(json.dumps(o, ensure_ascii=False) + '\n')
    print(len(x), sum(len(o['jp']) for o in x))
