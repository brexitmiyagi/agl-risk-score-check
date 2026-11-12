# How unusual is agilon Kentucky's first-year risk-score growth? Every ACO in the first year of an initial
# agreement, 2020-2024 files, aged non-dual risk score: performance year vs benchmark year 3.
import os, csv, re, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
f = lambda x: float(x) if x not in ('', '-', None) else None
pool = []
for y in (2020, 2022, 2023, 2024):
    for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', f'mssp_py{y}.csv'), encoding='latin-1')):
        m = re.findall(r'(20\d\d)', r['Current_Start_Date'])
        a, b = f(r['CMS_HCC_RiskScore_AGND_PY']), f(r['CMS_HCC_RiskScore_AGND_BY3'])
        if m and int(m[0]) == y and r['Agree_Type'].lower().startswith('initial') and a and b:
            pool.append((a / b - 1, y, r['ACO_Name']))
pool.sort(reverse=True)
print(f"first-year ACOs: {len(pool)}, median {100*st.median(g for g,_,_ in pool):+.2f}%, at 9% or more: {sum(g>=0.09 for g,_,_ in pool)}")
for g, y, n in pool[:5]: print(f"  {100*g:+.2f}%  {y}  {n}")
