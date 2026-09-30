"""번역 결과 용어 통일: 원문에 해당 일본어가 있는 줄에서만 한국어 표기를 바꾼다.
python tools/unify_terms.py  (translation/out/*.jsonl 제자리 수정, 바뀐 줄 수 출력)"""
import os, glob, json
ROOT = os.path.join(os.path.dirname(__file__), '..')
RULES = [  # (원문 포함, 바꿀 표기, 새 표기)
    ('オッシ', '옷시', '오시'), ('ノクサ', '노크사', '녹사'), ('ヒャンデ', '히안데', '히얀데'),
    ('きれぐも', '키레구모 집', '조각구름 둥지'), ('きれぐも', '키레구모', '조각구름'),
    ('エア', '에어', '에아'), ('ボウヤ', '보이', '꼬마'), ('竜の座', '용의 옥좌', '용의 자리'),
    ('開け放つもの', '열어젖히는 자', '여는 자'), ('告げる者', '고하는 자', '알리는 자'),
    ('封士', '봉사', '봉인사'), ('制御の間', '제어의 방', '제어실'), ('妖術宰相', '요술 재상', '요술재상'),
    ('パンタ・レイ', '판타・레이', '판타 레이'), ('バイアス', '바이아스', '바이어스'),
    ('ロッシマ', '롯시마', '로시마'), ('ラミュ', '라뮈', '라뮤'), ('鉄火姫', '철화 공주', '철화희'),
    ('竜殺し', '용 사냥꾼', '용살해자'), ('セリューン', '셀륜', '세륜'),
]
def main():
    tot = 0
    for fn in sorted(glob.glob(os.path.join(ROOT, 'translation', 'out', '*.jsonl'))):
        jf = os.path.join(ROOT, 'translation', 'jobs', os.path.basename(fn))
        src = {json.loads(l)['id']: json.loads(l)['jp'] for l in open(jf, encoding='utf-8')}
        rows = [json.loads(l) for l in open(fn, encoding='utf-8') if l.strip()]
        ch = 0
        for r in rows:
            jp = src.get(r['id'])
            if jp is None: continue
            ko = r['ko']
            for j, a, b in RULES:
                if j in jp and a in ko: ko = ko.replace(a, b)
            if ko != r['ko']: r['ko'] = ko; ch += 1
        if ch:
            with open(fn, 'w', encoding='utf-8') as f:
                for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')
            tot += ch
    print('changed', tot)
if __name__ == '__main__': main()
