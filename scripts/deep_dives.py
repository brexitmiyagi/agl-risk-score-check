# Follow-up checks on the doctor-level result. Same setup as event_study.py (copied, so each script runs on its own).
#  A. home visits: did agilon's clinicians move toward billing home visits after joining?
#  B. in-office kidney tests: is the rise in kidney disease diagnoses matched by testing billed under the doctor?
#  C. why did doctors in other REACH ACOs fall against their peers? split by ACO type, payment arrangement and entry year,
#     and test whether ACOs that rose most just before entry fell most after (drift back to the average).
# Setup notes from event_study.py:
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

def tmean(v):
    v = sorted(v); k = len(v) // 20; v = v[k:len(v) - k]
    return sum(v) / len(v) if v else float('nan')
HOME = ['99341','99342','99343','99344','99345','99347','99348','99349','99350','99334','99335','99336','99337']
LABS = ['82043','82570']
def load(codes):
    out = collections.defaultdict(float)
    for y in (2019, 2022, 2024):
        for s in STATES:
            for c in codes:
                for r in json.load(open(os.path.join(CACHE, f'serv_{y}_{s}_{c}.json'))):
                    out[(r['Rndrng_NPI'], y)] += f(r['Tot_Srvcs']) or 0
    return out
def panel(y0, y1):
    keep = {}
    for npi, ys in P.items():
        if y0 in ys and y1 in ys:
            a, b = ys[y0], ys[y1]
            if (a['Rndrng_Prvdr_State_Abrvtn'], a['Rndrng_Prvdr_Type']) != (b['Rndrng_Prvdr_State_Abrvtn'], b['Rndrng_Prvdr_Type']): continue
            na, nb = f(a['Tot_Benes']), f(b['Tot_Benes'])
            if na and nb and na >= 50 and nb >= 50: keep[npi] = (na, nb, (a['Rndrng_Prvdr_State_Abrvtn'], a['Rndrng_Prvdr_Type']))
    return keep
def billing_check(name, codes, y0=2019, y1=2024):
    S = load(codes); pan = panel(y0, y1)
    rate = lambda npi, y, n: 100 * S.get((npi, y), 0) / n
    cell = collections.defaultdict(lambda: {y0: [], y1: []})
    for npi, (na, nb, c) in pan.items():
        if npi not in group: cell[c][y0].append(rate(npi, y0, na)); cell[c][y1].append(rate(npi, y1, nb))
    print(f'{name}: services per 100 patients and share of clinicians billing any, {y0} and {y1} (same clinicians both years)')
    for g in ('agilon', 'other REACH', 'peers'):
        mem = [npi for npi in pan if (group.get(npi) == g if g != 'peers' else npi not in group)]
        if g != 'peers': mem = [n for n in mem if entry.get(n) in (2021, 2022)]
        r0 = [rate(n, y0, pan[n][0]) for n in mem]; r1 = [rate(n, y1, pan[n][1]) for n in mem]
        exc = [(rate(n, y1, pan[n][1]) - tmean(cell[pan[n][2]][y1])) - (rate(n, y0, pan[n][0]) - tmean(cell[pan[n][2]][y0])) for n in mem]
        print(f'   {g:12s} n={len(mem):6d}  per 100 patients {tmean(r0):6.2f} -> {tmean(r1):6.2f}   billing any {100*sum(x>0 for x in r0)/len(mem):5.1f}% -> {100*sum(x>0 for x in r1)/len(mem):5.1f}%   change vs own state-specialty peers {tmean(exc):+.2f}')
    return S, pan
print('A.'); billing_check('Home visits', HOME)
print('B.'); S, pan = billing_check('In-office kidney tests (82043, 82570)', LABS)
ck = [(change(n, 'CKD', -1, 2), n) for n in group if group[n] == 'agilon']
ck = [(c, n) for c, n in ck if c is not None and n in pan]
tested = [c for c, n in ck if S.get((n, 2024), 0) > 0]; untested = [c for c, n in ck if S.get((n, 2024), 0) == 0]
if tested and untested:
    print(f'   agilon clinicians: change in CKD rate vs peers, billing any kidney test in 2024 {tmean(tested):+.2f} pts (n={len(tested)}), billing none {tmean(untested):+.2f} pts (n={len(untested)})')
print('C. Other REACH clinicians, change vs peers from the year before entry to 2 years after, by group (median; n)')
for label, key in (('ACO type', 'ACO_TYPE'), ('capitation', 'CAPITATION_ARRANGEMENT'), ('risk arrangement', 'RISK_ARRANGEMENT'), ('entry year', 'FIRST_PART_YEAR')):
    by = collections.defaultdict(list)
    for n in group:
        if group[n] == 'other REACH':
            c = change(n, 'risk', -1, 2)
            if c is not None: by[reach[aco[n]][key]].append(c)
    print(f'   {label}: ' + '; '.join(f'{k} {st.median(v):+.2f} (n={len(v)})' for k, v in sorted(by.items()) if len(v) >= 30))
pre, post = [], []
for a_id in {aco[n] for n in group if group[n] == 'other REACH'}:
    p0 = [change(n, 'risk', -2, -1) for n in group if aco.get(n) == a_id]; p1 = [change(n, 'risk', -1, 2) for n in group if aco.get(n) == a_id]
    p0 = [x for x in p0 if x is not None]; p1 = [x for x in p1 if x is not None]
    if len(p0) >= 20 and len(p1) >= 20: pre.append(st.median(p0)); post.append(st.median(p1))
mx, my = sum(pre) / len(pre), sum(post) / len(post)
corr = sum((a - mx) * (b - my) for a, b in zip(pre, post)) / math.sqrt(sum((a - mx) ** 2 for a in pre) * sum((b - my) ** 2 for b in post))
slope = sum((a - mx) * (b - my) for a, b in zip(pre, post)) / sum((a - mx) ** 2 for a in pre)
print(f'   other REACH ACOs with 20+ clinicians: {len(pre)}. Correlation between the rise in the year before entry and the change after: {corr:+.2f}; slope {slope:+.2f}')
top = [b for a, b in zip(pre, post) if a > sorted(pre)[len(pre) // 2]]; bot = [b for a, b in zip(pre, post) if a <= sorted(pre)[len(pre) // 2]]
print(f'   ACOs that rose more than the median before entry: after {st.median(top):+.2f} (n={len(top)}); the rest: after {st.median(bot):+.2f} (n={len(bot)})')
