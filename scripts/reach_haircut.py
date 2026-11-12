# CMS ACO REACH: gap between normalized risk score and score after CIF and cap, by ACO.
# Files: CMS "ACO REACH Financial and Quality Results" PY2023 (py3.csv) and PY2024 (py4.csv), data.cms.gov.
import csv, math, os
HERE = os.path.dirname(os.path.abspath(__file__))
def f(x):
    try: return float(x)
    except: return None
for fn, py in [('py3.csv', 2023), ('py4.csv', 2024)]:
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', {'py3.csv':'reach_py2023.csv','py4.csv':'reach_py2024.csv'}[fn]), encoding='latin-1'))
            if f(r['NORM_RISK_SCORE']) and f(r['CIF_CAP_RISK'])]
    hs = sorted(((1 - f(r['CIF_CAP_RISK']) / f(r['NORM_RISK_SCORE']), r) for r in rows),
                key=lambda x: -x[0])
    ag = [(i + 1, h, r) for i, (h, r) in enumerate(hs) if 'agilon' in r['ACO_NAME'].lower()]
    wb = lambda xs: sum(h * f(r['FINAL_BENCHMARK']) for h, r in xs) / sum(f(r['FINAL_BENCHMARK']) for h, r in xs)
    print(f"PY{py}: {len(hs)} ACOs, median haircut {sorted(h for h,_ in hs)[len(hs)//2]*100:.2f}%")
    print(f"  benchmark-weighted: agilon {wb([(h,r) for _,h,r in ag])*100:.2f}% vs all {wb(hs)*100:.2f}%")
    for rank, h, r in ag:
        print(f"  #{rank:>3}  {h*100:5.2f}%  {r['ACO_NAME'].split(' (DBA')[0]}")
for k, top, n in [(5, 21, 132), (6, 23, 115)]:
    p = top / n
    print(f"P(>= {k} of 8 in top {top} of {n}) = {sum(math.comb(8,i)*p**i*(1-p)**(8-i) for i in range(k,9)):.4f}")
