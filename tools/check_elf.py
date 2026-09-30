"""translation/elf_out.jsonl ({"off","ko"}) 검사: 바이트 길이 ≤ 원문, 서식(%..) 동일, 인코딩 가능."""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(__file__))
import units
ROOT = os.path.join(os.path.dirname(__file__), '..')
src = {json.loads(l)['off']: json.loads(l) for l in open(os.path.join(ROOT, 'translation', 'elf_jobs.jsonl'), encoding='utf-8')}
p = os.path.join(ROOT, 'translation', 'elf_out.jsonl'); errs = []
out = {}
for l in open(p, encoding='utf-8'):
    if l.strip(): o = json.loads(l); out[o['off']] = o['ko']
for off, s in src.items():
    if off not in out: errs.append('%d 누락 %s' % (off, s['jp'])); continue
    ko = out[off]
    try: b = units.encode(ko, False)
    except Exception as e: errs.append('%d 인코딩 불가 %s %s' % (off, ko, e)); continue
    if len(b) > s['len']: errs.append('%d 길이 %d>%d [%s] [%s]' % (off, len(b), s['len'], s['jp'], ko))
    if re.findall(r'%[-0-9.]*l?[a-z]', s['jp']) != re.findall(r'%[-0-9.]*l?[a-z]', ko): errs.append('%d 서식 불일치 [%s] [%s]' % (off, s['jp'], ko))
    if s['jp'].count('\n') != ko.count('\n'): errs.append('%d 줄바꿈 수 불일치' % off)
    if re.search('[ぁ-んァ-ヶ一-龯]', ko): errs.append('%d 일본어 잔존 %s' % (off, ko))
print(len(errs), '건'); print('\n'.join(errs[:80]))
