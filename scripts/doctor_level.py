# Doctor-level check. CMS publishes Part B data by clinician, including the average HCC risk score of each
# clinician's traditional Medicare patients and annual wellness visits (G0438, G0439). This script:
#  1. downloads CMS's ACO REACH PY2024 provider list and takes agilon's eight ACOs' participant clinicians,
#  2. downloads Part B data for 2022 and 2024 for primary-care clinicians in those ACOs' states,
#  3. matches agilon clinicians by first name, last name and state (names that match more than one NPI are dropped),
#  4. keeps office-based primary care (at least 11 wellness-visit patients in both years, at least 50 patients),
#  5. compares each agilon clinician's patient risk-score growth with peers of the same state and specialty.
# Raw downloads are cached in ../cache (not in the repo). Only aggregate results are printed; no individual names.
import os, csv, io, json, urllib.request, urllib.parse, collections, statistics as st, random, time
HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.environ.get('AGL_CACHE', os.path.join(HERE, '..', 'cache')); os.makedirs(CACHE, exist_ok=True)
PRV_URL = 'https://data.cms.gov/sites/default/files/2026-07/695b301a-ce48-4ae5-a40c-1555cbbd1d8f/ACO_REACH_PY2024_PRVDR_PUF.csv'
PROV = {2022: '21555c17-ec1b-4e74-b2c6-925c6cbb3147', 2024: '8889d81e-2ee7-448f-8713-f071038289b5'}
SERV = {2022: 'e650987d-01b7-4f09-b75e-b0b075afbf98', 2024: '92396110-2aed-4d63-a6a2-5d6207d46a29'}
ACOST = {'D0033': 'TX', 'D0056': 'OH', 'D0107': 'HI', 'D0109': 'NY', 'D0113': 'PA', 'D0114': 'OH', 'D0116': 'OH', 'D0156': 'NC'}
TYPES = ['Family Practice', 'Internal Medicine', 'Geriatric Medicine', 'General Practice', 'Nurse Practitioner', 'Physician Assistant']
def cached(name, fn):
    p = os.path.join(CACHE, name)
    if not os.path.exists(p): json.dump(fn(), open(p, 'w'))
    return json.load(open(p))
def api(ds, flt):
    out, off = [], 0
    while True:
        q = '&'.join(f'filter%5B{k}%5D={urllib.parse.quote(v)}' for k, v in flt.items())
        d = json.load(urllib.request.urlopen(f'https://data.cms.gov/data-api/v1/dataset/{ds}/data?{q}&size=5000&offset={off}', timeout=120))
        out += d
        if len(d) < 5000: return out
        off += 5000
f = lambda x: float(x) if x not in (None, '') else None
prv = cached('reach_prvdr_2024.json', lambda: list(csv.DictReader(io.StringIO(urllib.request.urlopen(PRV_URL).read().decode('latin-1')))))
names = {(r['par_lbn'].upper().split()[0], r['par_lbn'].upper().split()[-1], ACOST[r['aco_id']]) for r in prv
         if r['aco_id'] in ACOST and r['prvdr_class'] == 'PART' and len(r['par_lbn'].split()) >= 2}
P, S = [], []
for y in PROV:
    for s in sorted(set(ACOST.values())):
        for t in TYPES:
            P += [{**r, 'year': y} for r in cached(f'prov_{y}_{s}_{t}.json', lambda: [{k: r.get(k) for k in ('Rndrng_NPI','Rndrng_Prvdr_Last_Org_Name','Rndrng_Prvdr_First_Name','Rndrng_Prvdr_Type','Rndrng_Prvdr_State_Abrvtn','Tot_Benes','Bene_Avg_Risk_Scre')} for r in api(PROV[y], {'Rndrng_Prvdr_State_Abrvtn': s, 'Rndrng_Prvdr_Type': t})])]
        for h in ('G0438', 'G0439'):
            S += [{**r, 'year': y} for r in cached(f'serv_{y}_{s}_{h}.json', lambda: [{'Rndrng_NPI': r['Rndrng_NPI'], 'Tot_Benes': r['Tot_Benes']} for r in api(SERV[y], {'Rndrng_Prvdr_State_Abrvtn': s, 'HCPCS_Cd': h})])]
idx = collections.defaultdict(set)
for r in P:
    fn, ln = (r['Rndrng_Prvdr_First_Name'] or '').upper().split(), (r['Rndrng_Prvdr_Last_Org_Name'] or '').upper().split()
    if fn and ln: idx[(fn[0], ln[-1], r['Rndrng_Prvdr_State_Abrvtn'])].add(r['Rndrng_NPI'])
agilon = {next(iter(idx[k])) for k in names if len(idx.get(k, ())) == 1}
D = collections.defaultdict(dict)
for r in P: D[r['Rndrng_NPI']][r['year']] = r
awv = collections.defaultdict(float)
for r in S: awv[(r['Rndrng_NPI'], r['year'])] += f(r['Tot_Benes']) or 0
rows = []
for npi, ys in D.items():
    if 2022 in ys and 2024 in ys:
        a, b = ys[2022], ys[2024]
        if a['Rndrng_Prvdr_Type'] != b['Rndrng_Prvdr_Type'] or a['Rndrng_Prvdr_State_Abrvtn'] != b['Rndrng_Prvdr_State_Abrvtn']: continue
        ra, rb, na, nb = f(a['Bene_Avg_Risk_Scre']), f(b['Bene_Avg_Risk_Scre']), f(a['Tot_Benes']), f(b['Tot_Benes'])
        if not (ra and rb and na and nb) or na < 50 or nb < 50 or awv[(npi, 2022)] < 11 or awv[(npi, 2024)] < 11: continue
        rows.append(dict(st=a['Rndrng_Prvdr_State_Abrvtn'], ty=a['Rndrng_Prvdr_Type'], g=rb/ra-1, r22=ra, r24=rb, aw24=awv[(npi, 2024)]/nb, ag=npi in agilon))
grp = collections.defaultdict(list)
for r in rows:
    if not r['ag']: grp[(r['st'], r['ty'])].append(r)
res = [r for r in rows if r['ag'] and len(grp[(r['st'], r['ty'])]) >= 20]
for r in res:
    g = grp[(r['st'], r['ty'])]; r['ex'] = r['g'] - st.median(x['g'] for x in g); r['pct'] = 100 * sum(x['g'] < r['g'] for x in g) / len(g)
peers = [x for g in grp.values() if len(g) >= 20 for x in g]
print(f"agilon participant names {len(names)}, matched to one NPI {len(agilon)}")
print(f"office-based primary care compared: agilon {len(res)}, peers {len(peers)}")
print(f"patient risk-score growth 2022-24: agilon median {100*st.median(r['g'] for r in res):.2f}%, peers {100*st.median(x['g'] for x in peers):.2f}%")
print(f"median excess over own state-and-specialty peers {100*st.median(r['ex'] for r in res):+.2f} pts; median percentile {st.median(r['pct'] for r in res):.0f}; above peer median {100*sum(r['ex']>0 for r in res)/len(res):.0f}%")
print(f"average patient risk score 2022: agilon {st.median(r['r22'] for r in res):.3f} vs peers {st.median(x['r22'] for x in peers):.3f}; 2024: {st.median(r['r24'] for r in res):.3f} vs {st.median(x['r24'] for x in peers):.3f}")
print(f"wellness-visit rate 2024: agilon {100*st.median(r['aw24'] for r in res):.1f}% vs peers {100*st.median(x['aw24'] for x in peers):.1f}%")
for s in sorted(set(r['st'] for r in res)):
    a = [r for r in res if r['st'] == s]; pe = [x for x in peers if x['st'] == s]
    print(f"  {s}: agilon {len(a)} growth {100*st.median(r['g'] for r in a):.2f}% vs peers {100*st.median(x['g'] for x in pe):.2f}%")
random.seed(1); bs = sorted(st.median(r['ex'] for r in [random.choice(res) for _ in res]) for _ in range(2000))
print(f"bootstrap 95% range for the median excess: {100*bs[50]:+.2f} to {100*bs[1949]:+.2f} pts")
