"""번역 결과 검사: python tools/check_job.py NNN  (translation/out/NNN.jsonl)
- 모든 id 존재, 태그(<Vxx><Cx><Xxx><Exx>) 순서·개수 동일, 줄 수 ≤ 원문 줄 수(원문 줄 수 초과 금지)
- 줄 폭(한글·전각 1, 반각 0.5, <V28>=4) ≤ max(원문 최대 줄 폭, 원문폭+2) 단 원문이 짧은 한 줄이면 +3
- 인코딩 가능(한글은 KS X 1001 2350자 밖이면 경고), 일본어 가나/한자 잔존 금지"""
import os, sys, json, re
sys.path.insert(0, os.path.dirname(__file__))
import hangul
ROOT = os.path.join(os.path.dirname(__file__), '..')
TAG = re.compile(r'<[VCEX][0-9A-Za-z]{1,2}>')
KS = set(hangul.ks2350())
def width(s):
    s = s.replace('<V28>', '　' * 4)
    s = TAG.sub('', s)
    return sum(0.5 if ord(c) < 0x80 else 1 for c in s)
def check(job):
    src = [json.loads(l) for l in open(os.path.join(ROOT, 'translation', 'jobs', job + '.jsonl'), encoding='utf-8')]
    p = os.path.join(ROOT, 'translation', 'out', job + '.jsonl')
    if not os.path.exists(p): return ['출력 없음']
    out = {}
    for l in open(p, encoding='utf-8'):
        if l.strip(): o = json.loads(l); out[o['id']] = o['ko']
    errs = []
    for s in src:
        i = s['id']; jp = s['jp']
        if i not in out: errs.append('%d: 누락' % i); continue
        ko = out[i]
        if TAG.findall(jp) != TAG.findall(ko): errs.append('%d: 태그 불일치 %s / %s' % (i, TAG.findall(jp), TAG.findall(ko)))
        jl = jp.split('\n'); kl = ko.split('\n')
        if len(kl) > len(jl): errs.append('%d: 줄 수 초과 %d>%d' % (i, len(kl), len(jl)))
        lim = max(width(l) for l in jl)
        lim = lim + 3 if len(jl) == 1 and lim < 12 else lim + 1
        for l in kl:
            if width(l.strip('　')) > lim: errs.append('%d: 줄 폭 %.1f>%.1f [%s]' % (i, width(l.strip('　')), lim, l))
        if re.search('[ぁ-んァ-ヶ一-龯]', TAG.sub('', ko)): errs.append('%d: 일본어 잔존 [%s]' % (i, ko[:40]))
        for ch in ko:
            if '가' <= ch <= '힣' and ch not in KS: errs.append('%d: 2350자 밖 음절 %s' % (i, ch))
            elif ord(ch) >= 0x80 and not ('가' <= ch <= '힣'):
                try: ch.encode('cp932')
                except UnicodeEncodeError: errs.append('%d: 표시 불가 문자 %r' % (i, ch))
    return errs
if __name__ == '__main__':
    tot = 0
    for j in sys.argv[1:]:
        e = check(j); tot += len(e)
        print('== %s: %d건' % (j, len(e)))
        for x in e[:60]: print(x)
    sys.exit(1 if tot else 0)
