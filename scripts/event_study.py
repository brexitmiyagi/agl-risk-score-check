# Event study, comparison with other value-based doctors, patient-mix test, and clustered ranges.
# Run pull_partb.py and doctor_level.py first; this reads the CMS downloads they leave in ../cache.
# Groups (primary care in TX, OH, HI, NY, PA, NC, matched to one NPI by name):
#   agilon       clinicians listed under agilon's eight REACH ACOs in CMS's 2024 provider file
#   other REACH  clinicians listed under any other REACH ACO in the same file
#   peers        everyone else of the same specialty in the same state
# Every measure is taken relative to the median of peers of the same state, specialty and year, then each clinician
# is lined up on the year their ACO entered Direct Contracting/REACH (FIRST_PART_YEAR in CMS's REACH results file).
# Only totals are printed; no clinician is named.
import os, json, csv, math, random, collections, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get('AGL_CACHE', os.path.join(HERE, '..', 'cache'))
ST = {'D0033': 'TX', 'D0056': 'OH', 'D0107': 'HI', 'D0109': 'NY', 'D0113': 'PA', 'D0114': 'OH', 'D0116': 'OH', 'D0156': 'NC'}
STATES = sorted(set(ST.values()))
TY = ['Family Practice', 'Internal Medicine', 'Geriatric Medicine', 'General Practice', 'Nurse Practitioner', 'Physician Assistant']
YEARS = range(2016, 2025)
CC = ['Diabetes', 'HF_NonIHD', 'COPD', 'CKD', 'IschemicHeart', 'Afib', 'Cancer6', 'Stroke_TIA', 'Hypertension', 'Hyperlipidemia']
f = lambda x: float(x) if x not in (None, '') else None
reach = {r['ACO_ID']: r for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'reach_py2024.csv')))}
first = {k: int(r['FIRST_PART_YEAR']) for k, r in reach.items()}
prv = json.load(open(os.path.join(CACHE, 'reach_prvdr_2024.json')))
P = collections.defaultdict(dict)
for y in YEARS:
    for s in STATES:
        for t in TY:
            for r in json.load(open(os.path.join(CACHE, f'provx_{y}_{s}_{t}.json'))):
                P[r['Rndrng_NPI']][y] = r
idx = collections.defaultdict(set)
for npi, ys in P.items():
    for y in (2022, 2024):
        r = ys.get(y)
        if not r: continue
        fn = (r.get('Rndrng_Prvdr_First_Name') or '').upper().split(); ln = (r.get('Rndrng_Prvdr_Last_Org_Name') or '').upper().split()
        if fn and ln: idx[(fn[0], ln[-1], r['Rndrng_Prvdr_State_Abrvtn'])].add(npi); idx[(fn[0], ln[-1], '*')].add(npi)
group, aco = {}, {}
for r in prv:
    if r['prvdr_class'] != 'PART' or len(r['par_lbn'].split()) < 2 or r['aco_id'] not in first: continue
    w = r['par_lbn'].upper().split()
    key = (w[0], w[-1], ST[r['aco_id']]) if r['aco_id'] in ST else (w[0], w[-1], '*')
    if len(idx.get(key, ())) != 1: continue
    npi = next(iter(idx[key])); g = 'agilon' if r['aco_id'] in ST else 'other REACH'
    if npi in group and aco[npi] != r['aco_id']: group[npi] = 'drop'; continue
    group[npi] = g; aco[npi] = r['aco_id']
group = {k: v for k, v in group.items() if v != 'drop'}
entry = {k: first[aco[k]] for k in group}
def measures(r):
    v, n = f(r['Bene_Avg_Risk_Scre']), f(r['Tot_Benes'])
    if not (v and n and n >= 50): return None
    m = {'risk': 100 * math.log(v), 'benes': 100 * math.log(n), 'age': f(r['Bene_Avg_Age']),
         'dual': 100 * (f(r['Bene_Dual_Cnt']) or 0) / n if r.get('Bene_Dual_Cnt') not in (None, '') else None}
    ccs = [f(r.get(f'Bene_CC_PH_{c}_V2_Pct')) for c in CC]
    m['cc'] = sum(ccs) / len(ccs) if all(c is not None for c in ccs) else None
    for c in ('Diabetes', 'HF_NonIHD', 'COPD', 'CKD'):
        m[c] = f(r.get(f'Bene_CC_PH_{c}_V2_Pct')) if f(r.get(f'Bene_CC_PH_{c}_V2_Pct')) is not None else None
    return m
KEYS = ['risk', 'benes', 'age', 'dual', 'cc', 'Diabetes', 'HF_NonIHD', 'COPD', 'CKD']
cells = collections.defaultdict(lambda: collections.defaultdict(list))
for npi, ys in P.items():
    if npi in group: continue
    for y, r in ys.items():
        m = measures(r)
        if m:
            for k in KEYS:
                if m[k] is not None: cells[(r['Rndrng_Prvdr_State_Abrvtn'], r['Rndrng_Prvdr_Type'], y)][k].append(m[k])
med = {c: {k: st.median(v) for k, v in d.items() if len(v) >= 20} for c, d in cells.items()}
def resid(npi):
    out, home = {}, None
    for y in sorted(P[npi]):
        r = P[npi][y]; c = (r['Rndrng_Prvdr_State_Abrvtn'], r['Rndrng_Prvdr_Type'], y)
        if home is None: home = c[:2]
        m = measures(r)
        if m and c in med and c[:2] == home:
            out[y] = {k: m[k] - med[c][k] for k in KEYS if m[k] is not None and k in med[c]}
    return out
RES = {npi: resid(npi) for npi in group}
def practice(npi):
    e = entry[npi]
    for y in (e - 1, e, e + 1, 2024):
        r = P[npi].get(y)
        if r: return (r.get('Rndrng_Prvdr_Zip5'), (r.get('Rndrng_Prvdr_St1') or '').upper()[:12])
    return None
def change(npi, k, a, b):
    rs, e = RES[npi], entry[npi]
    if e not in (2021, 2022) or (e + a) not in rs or (e + b) not in rs: return None
    if k not in rs[e + a] or k not in rs[e + b]: return None
    return rs[e + b][k] - rs[e + a][k]
def members(g, k, a, b):
    return [(npi, change(npi, k, a, b)) for npi in group if group[npi] == g and change(npi, k, a, b) is not None]
random.seed(1)
def cluster_boot(g, k, a, b, by, other=None, n=1000):
    def draw(gg):
        cl = collections.defaultdict(list)
        for npi, v in members(gg, k, a, b): cl[by(npi)].append(v)
        keys = list(cl)
        return lambda: st.median([v for c in (random.choice(keys) for _ in keys) for v in cl[c]])
    d1 = draw(g); d2 = draw(other) if other else (lambda: 0)
    bs = sorted(d1() - d2() for _ in range(n))
    return bs[int(.025 * n)], bs[int(.975 * n) - 1]
def m_(g, k, a, b):
    v = [x for _, x in members(g, k, a, b)]
    return st.median(v), len(v)
print('1. Event study, patient risk score vs same-state, same-specialty peers, change from the year before entry (pct pts, median)')
for kk in range(-5, 4):
    a, na = m_('agilon', 'risk', -1, kk) if kk != -1 else (0, 0)
    o, no = m_('other REACH', 'risk', -1, kk) if kk != -1 else (0, 0)
    print(f'   year {kk:+d}: agilon {a:+5.2f} (n={na:4d})  other REACH {o:+5.2f} (n={no:4d})')
print('2. Main tests with ranges resampled by clinician, by practice (same address in the year before entry) and by ACO')
byc = lambda npi: npi; byp = practice; bya = lambda npi: aco[npi]
for label, a, b in (('3 years before entry to the year before', -4, -1), ('year before entry to 2 years after', -1, 2)):
    A, na = m_('agilon', 'risk', a, b); O, no = m_('other REACH', 'risk', a, b)
    print(f'   {label}: agilon vs peers {A:+.2f} (n={na}); other REACH vs peers {O:+.2f} (n={no}); gap {A-O:+.2f}')
    for nm, by in (('clinician', byc), ('practice', byp), ('ACO', bya)):
        lo, hi = cluster_boot('agilon', 'risk', a, b, by); lo2, hi2 = cluster_boot('agilon', 'risk', a, b, by, 'other REACH')
        print(f'      resampled by {nm:9s}: agilon vs peers {lo:+.2f} to {hi:+.2f}; gap {lo2:+.2f} to {hi2:+.2f}')
print('   practices: agilon', len({practice(n) for n in group if group[n] == 'agilon'}), ' ACOs: agilon 8, other REACH', len({aco[n] for n in group if group[n] == 'other REACH'}))
print('3. agilon by ACO: change from year before entry to 2 years after vs peers (and 3 years before)')
for a_id in sorted(ST, key=lambda x: reach[x]['ACO_NAME']):
    post = [change(n, 'risk', -1, 2) for n in group if aco.get(n) == a_id]; post = [x for x in post if x is not None]
    pre = [change(n, 'risk', -4, -1) for n in group if aco.get(n) == a_id]; pre = [x for x in pre if x is not None]
    if post:
        print(f'   {ST[a_id]} {reach[a_id]["ACO_NAME"][:48]:48s} entry {first[a_id]}: after {st.median(post):+5.2f} (n={len(post):3d}); before {st.median(pre) if pre else float("nan"):+5.2f} (n={len(pre)}); above 0: {100*sum(x>0 for x in post)/len(post):.0f}%')
def tmean(v):
    v = sorted(v); k = len(v) // 20; v = v[k:len(v) - k]
    return sum(v) / len(v)
def tm_(g, k, a, b):
    v = [x for _, x in members(g, k, a, b)]
    return tmean(v), len(v)
print('4. Patient mix: same window (year before entry to 2 years after), change vs peers, 5%-trimmed mean (CMS rounds age and condition rates to whole numbers)')
for k, lab in (('risk', 'risk score (log x100)'), ('cc', 'average of 10 chronic-condition rates, pts (includes the doctor\'s own codes)'), ('Diabetes', 'diabetes rate, pts'), ('HF_NonIHD', 'heart failure rate, pts'), ('COPD', 'COPD rate, pts'), ('CKD', 'chronic kidney disease rate, pts'), ('age', 'average patient age, years'), ('dual', 'dual-eligible share, pts'), ('benes', 'patient count (log x100)')):
    A, na = tm_('agilon', k, -1, 2); O, no = tm_('other REACH', k, -1, 2)
    cl = collections.defaultdict(list)
    for npi, v in members('agilon', k, -1, 2): cl[practice(npi)].append(v)
    keys = list(cl); bs = sorted(tmean([v for c in (random.choice(keys) for _ in keys) for v in cl[c]]) for _ in range(500)); lo, hi = bs[12], bs[487]
    print(f'   {lab:44s} agilon {A:+6.2f} (practice range {lo:+.2f} to {hi:+.2f})  other REACH {O:+6.2f}')
# 2022-24 against peers who started at a similar score
pool = collections.defaultdict(list)
for npi, ys in P.items():
    if npi in group or 2022 not in ys or 2024 not in ys: continue
    a, b = ys[2022], ys[2024]
    if (a['Rndrng_Prvdr_State_Abrvtn'], a['Rndrng_Prvdr_Type']) != (b['Rndrng_Prvdr_State_Abrvtn'], b['Rndrng_Prvdr_Type']): continue
    ra, rb, na, nb = f(a['Bene_Avg_Risk_Scre']), f(b['Bene_Avg_Risk_Scre']), f(a['Tot_Benes']), f(b['Tot_Benes'])
    if ra and rb and na and nb and na >= 50 and nb >= 50: pool[(a['Rndrng_Prvdr_State_Abrvtn'], a['Rndrng_Prvdr_Type'])].append((ra, rb / ra - 1))
print('5. 2022-24 growth vs peers who started within 0.05 of the same 2022 score')
for g in ('agilon', 'other REACH'):
    ex = []
    for npi in group:
        if group[npi] != g or 2022 not in P[npi] or 2024 not in P[npi]: continue
        a, b = P[npi][2022], P[npi][2024]; k = (a['Rndrng_Prvdr_State_Abrvtn'], a['Rndrng_Prvdr_Type'])
        if k != (b['Rndrng_Prvdr_State_Abrvtn'], b['Rndrng_Prvdr_Type']): continue
        ra, rb, na, nb = f(a['Bene_Avg_Risk_Scre']), f(b['Bene_Avg_Risk_Scre']), f(a['Tot_Benes']), f(b['Tot_Benes'])
        if not (ra and rb and na and nb and na >= 50 and nb >= 50): continue
        near = [gr for r0, gr in pool[k] if abs(r0 - ra) <= 0.05]
        if len(near) >= 20: ex.append((npi, 100 * ((rb / ra - 1) - st.median(near))))
    cl = collections.defaultdict(list)
    for npi, v in ex: cl[practice(npi) if npi in entry else npi].append(v)
    keys = list(cl); bs = sorted(st.median([v for c in (random.choice(keys) for _ in keys) for v in cl[c]]) for _ in range(1000))
    print(f'   {g}: median excess {st.median([v for _, v in ex]):+.2f} pts, resampled by practice {bs[25]:+.2f} to {bs[974]:+.2f}, above matched median {100*sum(v>0 for _, v in ex)/len(ex):.0f}% (n={len(ex)})')
# higher-level office visits
EM = collections.defaultdict(lambda: collections.defaultdict(float))
for y in (2019, 2022, 2024):
    for s in STATES:
        for c in ('99212', '99213', '99214', '99215'):
            for r in json.load(open(os.path.join(CACHE, f'serv_{y}_{s}_{c}.json'))):
                EM[(r['Rndrng_NPI'], y)][c] += f(r['Tot_Srvcs']) or 0
def share(npi, y):
    d = EM.get((npi, y)); tot = sum(d.values()) if d else 0
    return (d['99214'] + d['99215']) / tot if tot >= 100 else None
emcell = collections.defaultdict(list)
for npi, ys in P.items():
    if npi in group: continue
    for y in (2019, 2022, 2024):
        if y in ys and share(npi, y) is not None: emcell[(ys[y]['Rndrng_Prvdr_State_Abrvtn'], ys[y]['Rndrng_Prvdr_Type'], y)].append(share(npi, y))
emmed = {k: st.median(v) for k, v in emcell.items() if len(v) >= 20}
print('6. Share of office visits billed at 99214/99215, median gap to same-state, same-specialty peers (pts)')
for g in ('agilon', 'other REACH'):
    out = []
    for y in (2019, 2022, 2024):
        gaps = [100 * (share(n, y) - emmed[(P[n][y]['Rndrng_Prvdr_State_Abrvtn'], P[n][y]['Rndrng_Prvdr_Type'], y)]) for n in group
                if group[n] == g and y in P[n] and share(n, y) is not None and (P[n][y]['Rndrng_Prvdr_State_Abrvtn'], P[n][y]['Rndrng_Prvdr_Type'], y) in emmed]
        out.append(f'{y} {st.median(gaps):+.1f} (n={len(gaps)})')
    print(f'   {g}: ' + '; '.join(out))
print('clinicians matched: agilon', sum(v == 'agilon' for v in group.values()), 'other REACH', sum(v == 'other REACH' for v in group.values()))
print('7. Are the gains slowing? Yearly change vs peers, median of each clinician\'s own year-on-year change')
for label, cohort in (('all agilon', (2021, 2022)), ('agilon, 2021 entrants only', (2021,))):
    out = []
    for k in range(0, 4):
        v = [change(n, 'risk', k - 1, k) for n in group if group[n] == 'agilon' and entry[n] in cohort]
        v = [x for x in v if x is not None]
        if len(v) >= 30: out.append(f'year {k:+d}: {st.median(v):+.2f} (mean {tmean(v):+.2f}, n={len(v)})')
    print(f'   {label}: ' + '; '.join(out))
