# CMS ACO REACH, PY2023 and PY2024. "Haircut" = 1 - (risk score after CIF and cap) / (normalized risk score).
# Compares agilon's ACOs with standard ACOs that joined the same year, then ranks ACOs of listed companies
# within their own type-and-start-year group. Parent names come from each company's own SEC filings.
import os, csv, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
f = lambda x: float(x) if x not in ('', '-', None) else None
parents = {'agilon': 'agilon (AGL)', 'CVS Accountable': 'CVS Health (CVS)', 'Oak Street': 'CVS Health (CVS)',
           'Humana Direct': 'Humana (HUM)', 'CenterWell': 'Humana (HUM)', 'Alignment Health ACO': 'Alignment (ALHC)',
           'APA ACO': 'Astrana (ASTH)', 'P3 Health': 'P3 Health (PIII)', 'Clover Health': 'Clover (CLOV)'}
def parent(n):
    for k, v in parents.items():
        if k.lower() in n.lower(): return v
for fn, py in [('reach_py2023.csv', 2023), ('reach_py2024.csv', 2024)]:
    rows = [r for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', fn), encoding='latin-1')) if f(r['NORM_RISK_SCORE']) and f(r['CIF_CAP_RISK'])]
    for r in rows: r['h'] = 1 - f(r['CIF_CAP_RISK']) / f(r['NORM_RISK_SCORE']); r['b'] = f(r['FINAL_BENCHMARK']); r['s'] = f(r['GROSS_SAVINGS'])
    std = [r for r in rows if r['ACO_TYPE'].lower() == 'standard']
    for yr in ('2021', '2022'):
        coh = [r for r in std if r['FIRST_PART_YEAR'] == yr]
        ag = [r for r in coh if 'agilon' in r['ACO_NAME'].lower()]; ot = [r for r in coh if r not in ag]
        w = lambda xs, k: 100 * sum(r[k] * r['b'] for r in xs) / sum(r['b'] for r in xs) if k == 'h' else 100 * sum(r['s'] for r in xs) / sum(r['b'] for r in xs)
        med = st.median(r['h'] for r in ot)
        print(f"PY{py} joined {yr}: agilon {len(ag)} haircut {w(ag,'h'):.2f}% vs peers ({len(ot)}) {w(ot,'h'):.2f}% | above peer median {sum(r['h']>med for r in ag)} of {len(ag)} | savings {w(ag,'s'):.1f}% vs {w(ot,'s'):.1f}%")
    agg = {}
    for r in rows:
        p = parent(r['ACO_NAME'])
        if not p: continue
        coh = [x for x in rows if x['ACO_TYPE'] == r['ACO_TYPE'] and x['FIRST_PART_YEAR'] == r['FIRST_PART_YEAR'] and x is not r]
        pct = 100 * sum(x['h'] < r['h'] for x in coh) / len(coh)
        agg.setdefault(p, []).append((pct, r['b']))
    print(f"PY{py} listed groups, benchmark-weighted percentile within own cohort:")
    for p, v in sorted(agg.items(), key=lambda kv: -sum(a*b for a, b in kv[1]) / sum(b for _, b in kv[1])):
        print(f"   {p:18s} {sum(a*b for a,b in v)/sum(b for _,b in v):5.0f}  ({len(v)} ACO{'s' if len(v)>1 else ''})")
