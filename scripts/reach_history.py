# agilon's REACH ACOs, 2021-2024: percentile of risk-score growth (performance-year blend score vs most recent
# baseline year) among standard ACOs that joined in the same year.
import os, csv, statistics as st
# agilon's REACH ACO IDs (names in the 2021 file use earlier DCE names, so match on ID)
AGILON = {'D0033', 'D0056', 'D0107', 'D0109', 'D0113', 'D0114', 'D0116', 'D0156'}
HERE = os.path.dirname(os.path.abspath(__file__))
f = lambda x: float(x) if x not in ('', '-', None) else None
for y in (2021, 2022, 2023, 2024):
    rows = list(csv.DictReader(open(os.path.join(HERE, '..', 'data', f'reach_py{y}.csv'), encoding='latin-1')))
    for r in rows:
        a, b = f(r['PY_AD_BLEND_RISKSCORE']), f(r['HIST_BY3_AD_RISKSCORE'])
        r['g'] = a / b - 1 if a and b else None
    std = [r for r in rows if r['ACO_TYPE'].lower() == 'standard' and r['g'] is not None]
    pcts = []
    for r in std:
        if r['ACO_ID'] in AGILON:
            coh = [x['g'] for x in std if x['FIRST_PART_YEAR'] == r['FIRST_PART_YEAR'] and x is not r]
            pcts.append(100 * sum(c < r['g'] for c in coh) / len(coh))
    print(f"PY{y}: {len(pcts)} agilon ACOs, median percentile {st.median(pcts):.0f}, above peer median {sum(p>50 for p in pcts)}")
