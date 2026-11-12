# agilon's federal lobbying disclosures (LDA), totals by year and filer, and every mention of the No UPCODE Act.
import os, json, collections
HERE = os.path.dirname(os.path.abspath(__file__))
res = json.load(open(os.path.join(HERE, '..', 'data', 'lda_agilon_filings.json')))
tot = collections.defaultdict(float)
for x in res:
    amt = x.get('income') or x.get('expenses')
    if amt: tot[(x['filing_year'], x['registrant']['name'])] += float(amt)
for k, v in sorted(tot.items()): print(k[0], k[1], f"${v:,.0f}")
for x in res:
    for a in x.get('lobbying_activities', []):
        if 'UPCODE' in (a.get('description') or ''):
            print('No UPCODE Act:', x['filing_year'], x['filing_period'], x['registrant']['name'])
