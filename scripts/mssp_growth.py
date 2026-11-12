# CMS Shared Savings Program PY2024 results: risk score growth from benchmark year 3 to the performance year,
# aged non-dual (AGND) and aged dual (AGDU), against all ACOs and against ACOs with the same agreement type and start date.
import os, csv, statistics as st
HERE = os.path.dirname(os.path.abspath(__file__))
f = lambda x: float(x) if x not in ('', '-', None) else None
rows = list(csv.DictReader(open(os.path.join(HERE, '..', 'data', 'mssp_py2024.csv'), encoding='latin-1')))
for aid in ('A5386', 'A5387'):
    me = [r for r in rows if r['ACO_ID'] == aid][0]
    print(me['ACO_Name'], '|', me['Agree_Type'], me['Current_Start_Date'], '| savings rate', me['Sav_rate'], '% | gross savings/loss $', me['GenSaveLoss'])
    for grp in ('AGND', 'AGDU'):
        for label, pool in (('all', rows), ('same type and start', [r for r in rows if r['Agree_Type'] == me['Agree_Type'] and r['Current_Start_Date'] == me['Current_Start_Date']])):
            g = sorted(((f(r[f'CMS_HCC_RiskScore_{grp}_PY']) / f(r[f'CMS_HCC_RiskScore_{grp}_BY3']) - 1, r['ACO_ID']) for r in pool if f(r[f'CMS_HCC_RiskScore_{grp}_PY']) and f(r[f'CMS_HCC_RiskScore_{grp}_BY3'])), reverse=True)
            mine = [v for v, a in g if a == aid][0]
            print(f"   {grp} {label:20s} growth {100*mine:+.2f}%  rank {[a for _,a in g].index(aid)+1} of {len(g)}  median {100*st.median(v for v,_ in g):+.2f}%")
