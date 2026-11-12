# Valuation, three risk-score paths, peer multiples, DCF cross-check, audit-exposure scenarios.
import os, csv
HERE = os.path.dirname(os.path.abspath(__file__))
I = {r['item']: float(r['value']) for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'inputs.csv')))}
px, sh, nc = I['price_2026_11_11'], I['diluted_shares_q3_2026'], I['net_cash_unrestricted']
val = lambda e, m=12: (e * m + nc) / sh
print(f"EV {px*sh-nc:,.1f}m  EV/2026 guide {(px*sh-nc)/I['adj_ebitda_2026_guide_mid']:.1f}x")
# EBITDA per point of risk score, from the Q2 call: 1.5 points = $20m YTD + $19m second half
per_pt = (I['raf_q2_ytd_ebitda'] + I['raf_q2_h2_ebitda']) / (I['raf_aug_2026_pct'] - I['raf_may_2026_pct'])
print(f"EBITDA per point {per_pt:.1f}m  = ${per_pt*12/sh:.1f}/share at 12x;  margin per point (Q1 call) {I['raf_q1_fy_margin_usd']/(I['raf_may_2026_pct']-I['raf_feb_2026_pct']):.1f}m")
# 2027 base, driver by driver (same logic as the spreadsheet model in the post's repo folder)
ms26 = I['revenue_2026_guide_mid'] - 7                     # medical services revenue, other revenue ~7
cost26 = ms26 * I['mser_2026_guide_mid']
part, othmed26, ga_cash26, aco26 = 0.333, 109, 280 - 68 - 16.9, 42.5   # 10-Q Q3 2026 based, see README
plug = I['adj_ebitda_2026_guide_mid'] - ((ms26 - cost26) * (1 - part) - othmed26 - ga_cash26 + aco26)
mem = 447.5 / 452                                          # 2027 avg MA members flat on 2026 year-end guide
rev27 = ms26 * mem * (1 + I['cms_2027_rate'] / 100)       # CMS rate includes the 2.50% industry risk-score trend
cost27 = cost26 * mem * (1 + 0.064) - 52.5                # 6.4% cost trend; recontracting worth 52.5 before partner share
base = (rev27 - cost27) * (1 - part) - othmed26 * 1.03 - ga_cash26 * 1.03 + aco26 + 10 + plug - 20
print(f"2027 base adj. EBITDA {base:.1f}m (2026 calibration item {plug:.1f}m)")
paths = [('gives back 1 point', base - per_pt, .35), ('holds (industry trend)', base, .45), ('adds 1 point', base + per_pt, .20)]
for n, e, w in paths: print(f"  {n:24s} EBITDA {e:6.1f}m  value ${val(e):6.2f}  weight {w:.0%}")
pw = sum(val(e) * w for _, e, w in paths); ev = sum(val(e) * w for (_, e, _), w in zip(paths, (.25, .5, .25)))
print(f"probability-weighted ${pw:.2f} ({pw/px-1:+.1%}); even weights ${ev:.2f} ({ev/px-1:+.1%}); rating under 15% rule: {'SELL' if pw/px-1 <= -.15 else 'BUY' if pw/px-1 >= .15 else 'HOLD'}")
# Bridge from adjusted EBITDA to GAAP net income, calibrated to 9M 2026 actuals (10-Q reconciliation):
# 187.1 - SBC 48.9 - D&A 20.4 - interest 5.2 - tax 3.7 - severance 16.9 - equity-method adj 41.2 + other 32.0 = 82.8
chk = 187.1 - 48.9 - 20.4 - 5.2 - 3.7 - 16.9 - 41.2 + 32.0
assert abs(chk - 82.8) < 0.15, chk
other = (5.2 + 3.7 + 41.2 - 32.0) / 0.75   # recurring interest, tax, ACO and other items, annualised (~24)
ce = I['cons_eps_2027'] * 17.0 + 60 + 27 + other   # consensus EPS is normalized, so severance is already out
print(f"consensus-implied 2027 adj. EBITDA ~{ce:.0f}m (normalized EPS x 17.0m shares + stock comp 60 + D&A 27 + other {other:.0f}); {(ce-base)/per_pt:.1f} points above my base")
for n_, eps_ in (('low', 1.61), ('high', 7.10)): print(f"  EPS {n_} {eps_}: EBITDA ~{eps_*17+60+27+other:.0f}m, {(eps_*17+60+27+other-base)/per_pt:+.1f} points")
for m in (8.0, 12.0, 12.4, 17.9): print(f"  price implies 2027 EBITDA of {(px*sh-nc)/m:.0f}m at {m}x")
for rs, w in ((-1, .35), (0, .45), (1, .20)):
    print('  grid', rs, w, [round(val(base + rs*per_pt - (gap-1.43)*35)) for gap in (0.5, 1.43, 2.5)])
# peers: EV / 2026 adj. EBITDA guide midpoint (company 8-Ks, Q3 2026); peer prices 10 Nov 2026
peers = {'Privia (PRVA)': (24.37, 132.710, 0.0, 446.3, 155.5), 'Astrana (ASTH)': (32.18, 49.916, 925.4, 396.2, 267.5), 'Alignment (ALHC)': (7.67, 214.815, 324.5, 727.7, 100.0)}
for k, (p, s, d, c, e) in peers.items(): print(f"  {k:18s} EV {p*s+d-c:8.1f}m  EV/EBITDA {(p*s+d-c)/e:5.1f}x")
# DCF cross-check on the base: FCF = EBITDA - capex 14 - cash interest 7 - cash tax 4; 10% discount, 3% growth
f = base - 14 - 7 - 4
print(f"DCF ex stock comp ${(f/.07+nc)/sh:.1f};  treating ~$60m stock comp as a cost ${((f-60)/.07+nc)/sh:.1f}")
# audit (RADV) exposure scenarios: PY2024-PY2026, ~$6.0bn revenue a year
for n, rate, passthru, prob in [('sample only, no extrapolation', 0, 0, .60), ('half national rate, half passed through', I['part_c_overpayment_rate']/2, .5, .30), ('national rate, fully passed through', I['part_c_overpayment_rate'], 1, .10)]:
    cost = rate/100 * passthru * 18000
    print(f"  {n:42s} ${cost:6.0f}m  ${cost/sh:5.1f}/share  p={prob:.0%}")
lo = .25*(I['part_c_overpayment_rate']/200*.5*18000)/sh + .05*(I['part_c_overpayment_rate']/100*18000)/sh
hi = .30*(I['part_c_overpayment_rate']/200*.5*18000)/sh + .10*(I['part_c_overpayment_rate']/100*18000)/sh
print(f"audit expected cost ${lo:.1f} to ${hi:.1f} a share; even weights less low end ${ev-lo:.2f}")
# Estimates 2026E-2028E (author). Medical margin = adj. EBITDA + the 2026 gap ($414m) grown 3% a year.
gap = 0.096 * 5873 - 150
rows = [(2026, 5880, 150, 68, 17.4), (2027, round(rev27 + 7), round(base), 60, 17.9)]
for i, (y, rev, e, sbc, s) in enumerate(rows):
    mm = e + gap * 1.03**i
    ni = {2026: 82.8 + (-37.1 - 19.1 - 6.6 - 6 - 1), 2027: e - sbc - 27 - 24 - 5, 2028: e - sbc - 27 - 24 - 3}[y]
    bs = {2026: 16.75, 2027: 17.0, 2028: 17.2}[y]
    print(f"{y}E rev {rev:,}  MSER {1-mm/(rev-7):.1%}  adj EBITDA {e}  net income {ni:.0f}  basic EPS {ni/bs:.2f}")
