import json, os, urllib.request, urllib.parse, concurrent.futures as cf, time
# Downloads CMS Part B data for primary care clinicians in the six states where agilon has REACH ACOs:
# by provider for 2016 to 2024 (with patient age, dual share and chronic-condition rates), plus office-visit codes 99212 to 99215,
# home-visit codes and two in-office kidney tests (urine albumin 82043, urine creatinine 82570) for 2019, 2022 and 2024. About 350MB, cached in ../cache.
HERE = os.path.dirname(os.path.abspath(__file__))
C = os.environ.get('AGL_CACHE', os.path.join(HERE, '..', 'cache')); os.makedirs(C, exist_ok=True)
PROV = {2016:'2691839a-99fb-45a1-9bd9-86905ba975cc',2017:'44ea2789-993f-4d55-ac44-ed7f160b58fa',2018:'900850df-c9a9-47ce-a9e0-d0ceae5a811f',2019:'6a53afe5-1cbc-4b33-9dc8-926ee532dc66',2020:'29d799aa-c660-44fe-a51a-72c4b3e661ac',2021:'44e0a489-666c-4ea4-a1a2-360b6cdc19db',2022:'21555c17-ec1b-4e74-b2c6-925c6cbb3147',2023:'8ba584c6-a43a-4b0b-a35a-eb9a59e3a571',2024:'8889d81e-2ee7-448f-8713-f071038289b5'}
SERV = {2019:'867b8ac7-ccb7-4cc9-873d-b24340d89e32',2022:'e650987d-01b7-4f09-b75e-b0b075afbf98',2024:'92396110-2aed-4d63-a6a2-5d6207d46a29'}
ST = ['TX','OH','HI','NY','PA','NC']
CC = ['Diabetes','HF_NonIHD','COPD','CKD','IschemicHeart','Afib','Cancer6','Stroke_TIA','Hypertension','Hyperlipidemia']
FIELDS = ['Rndrng_NPI','Rndrng_Prvdr_Last_Org_Name','Rndrng_Prvdr_First_Name','Rndrng_Prvdr_Type','Rndrng_Prvdr_State_Abrvtn','Rndrng_Prvdr_St1','Rndrng_Prvdr_Zip5','Tot_Benes','Bene_Avg_Risk_Scre','Bene_Avg_Age','Bene_Dual_Cnt'] + [f'Bene_CC_PH_{c}_V2_Pct' for c in CC]
TY = ['Family Practice','Internal Medicine','Geriatric Medicine','General Practice','Nurse Practitioner','Physician Assistant']
def api(ds, flt):
    out, off = [], 0
    while True:
        q = '&'.join(f'filter%5B{k}%5D={urllib.parse.quote(v)}' for k, v in flt.items())
        for a in range(5):
            try:
                d = json.load(urllib.request.urlopen(f'https://data.cms.gov/data-api/v1/dataset/{ds}/data?{q}&size=5000&offset={off}', timeout=180)); break
            except Exception as e:
                time.sleep(3*(a+1))
        else: raise RuntimeError(f'{ds} {flt} {off}')
        out += d
        if len(d) < 5000: return out
        off += 5000
def job(kind, y, s, x):
    p = os.path.join(C, f'{"provx" if kind == "prov" else kind}_{y}_{s}_{x}.json')
    if os.path.exists(p): return p
    if kind == 'prov':
        rows = [{k: r.get(k) for k in FIELDS} for r in api(PROV[y], {'Rndrng_Prvdr_State_Abrvtn': s, 'Rndrng_Prvdr_Type': x})]
    else:
        rows = []
        for t in TY:
            rows += [{'Rndrng_NPI': r['Rndrng_NPI'], 'Tot_Srvcs': r['Tot_Srvcs']} for r in api(SERV[y], {'Rndrng_Prvdr_State_Abrvtn': s, 'HCPCS_Cd': x, 'Rndrng_Prvdr_Type': t})]
    json.dump(rows, open(p + '.tmp', 'w')); os.replace(p + '.tmp', p); return p
jobs = [('prov', y, s, t) for y in PROV for s in ST for t in TY] + [('serv', y, s, c) for y in SERV for s in ST for c in ('99212','99213','99214','99215')]
# home visits (2019 codes include the domiciliary series merged into home visits in 2023) and in-office kidney tests
HOME = ['99341','99342','99343','99344','99345','99347','99348','99349','99350','99334','99335','99336','99337']
LABS = ['82043','82570']
jobs += [('serv', y, s, c) for y in SERV for s in ST for c in HOME + LABS]
with cf.ThreadPoolExecutor(12) as ex:
    fs = [ex.submit(job, *j) for j in jobs]
    done = 0
    for f in cf.as_completed(fs):
        f.result(); done += 1
print('downloaded or found', done, 'files in', C)
