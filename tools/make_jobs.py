"""고유 페이지 → 번역 작업 파일 translation/jobs/NNN.jsonl (파일·항목 순서로 문맥 유지, 작업당 약 12,000자)."""
import os, json, re
ROOT = os.path.join(os.path.dirname(__file__), '..')
rows = json.load(open(os.path.join(ROOT, 'work', 'pages.json'), encoding='utf-8'))
JP = re.compile('[ぁ-んァ-ヶ一-龯々]')
seen = {}; order = []
for f, e, p, h, t in rows:
    if not JP.search(t) or t in seen: continue
    seen[t] = len(order); order.append((f, e, p, t))
out = os.path.join(ROOT, 'translation', 'jobs'); os.makedirs(out, exist_ok=True)
job = []; n = 0; size = 0; LIM = 12000
def flush():
    global job, n, size
    if job:
        with open(os.path.join(out, '%03d.jsonl' % n), 'w', encoding='utf-8') as fo:
            for x in job: fo.write(json.dumps(x, ensure_ascii=False) + '\n')
        n += 1; job = []; size = 0
for i, (f, e, p, t) in enumerate(order):
    job.append({'id': i, 'file': f, 'entry': e, 'jp': t}); size += len(t)
    if size >= LIM: flush()
flush()
print(len(order), 'units', n, 'jobs')
