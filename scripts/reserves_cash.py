# Where the money sits: receivables, the claims reserve and how past reserves developed.
# Inputs: agilon's own XBRL facts from SEC EDGAR (data/sec_xbrl_agl.csv, pulled from
# https://data.sec.gov/api/xbrl/companyfacts/CIK0001831097.json on 12 Nov 2026), plus the reserve tables in the Q3 10-Qs.
# Receivable days = receivables / quarter's revenue x 91. Claims days = medical claims payable / quarter's medical expense x 91.
# Unpaid current-year claims at Q3 = current-year incurred less current-year paid, from the 10-Q reserve roll-forward.
import os, csv, collections, datetime as dt
HERE = os.path.dirname(os.path.abspath(__file__))
F = collections.defaultdict(dict)
for r in csv.DictReader(open(os.path.join(HERE, '..', 'data', 'sec_xbrl_agl.csv'))):
    F[r['concept']][(r['start'], r['end'])] = float(r['value'])   # later filings overwrite earlier ones
def inst(k): return {e: v for (s, e), v in F[k].items() if not s}
def quarterly(*ks):
    q = {}
    for k in ks:
        ytd = {key: v for key, v in F[k].items() if key[0]}
        for (s, e), v in ytd.items():
            if e in q: continue
            n = (dt.date.fromisoformat(e) - dt.date.fromisoformat(s)).days
            if n < 100: q[e] = v; continue
            prev = [(s2, e2) for (s2, e2) in ytd if s2 == s and e2 < e and (dt.date.fromisoformat(e) - dt.date.fromisoformat(e2)).days < 100]
            if prev: q[e] = v - ytd[max(prev)]
    return q
rec, cl = inst('ReceivablesNetCurrent'), inst('LiabilityForClaimsAndClaimsAdjustmentExpense')
rev = quarterly('RevenueFromContractWithCustomerExcludingAssessedTax')
me = quarterly('LiabilityForUnpaidClaimsAndClaimsAdjustmentExpenseIncurredClaims1', 'PolicyholderBenefitsAndClaimsIncurredHealthCare')
print('1. Receivable days and claims days by quarter, from 2023 (earlier Q4s are distorted by discontinued-operations restatements)')
print('   quarter      receivables  receivable days   claims payable  claims days')
for e in sorted(rec):
    if e < '2023-01-01' or e not in rev or e not in cl or e not in me: continue
    print(f'   {e}  {rec[e]/1e6:9.1f}  {rec[e]/rev[e]*91:12.1f}  {cl[e]/1e6:14.1f}  {cl[e]/me[e]*91:11.1f}')
print('2. Prior-year reserve development in the first nine months (negative = favourable), against the reserve at the start of the year')
pyd = F['SupplementalInformationForPropertyCasualtyInsuranceUnderwritersPriorYearClaimsAndClaimsAdjustmentExpense']
for y in range(2022, 2027):
    v = pyd.get((f'{y}-01-01', f'{y}-09-30'))
    open_ = cl.get(f'{y-1}-12-31')
    if v is not None and open_: print(f'   {y}: {v/1e6:+7.1f}m on a {open_/1e6:,.1f}m reserve ({100*v/open_:+.1f}%)')
print('3. Current-year claims still unpaid at September 30, in days of third-quarter current-year cost')
cy = F['SupplementalInformationForPropertyCasualtyInsuranceUnderwritersCurrentYearClaimsAndClaimsAdjustmentExpense']
paid = F['LiabilityForUnpaidClaimsAndClaimsAdjustmentExpenseClaimsPaidCurrentYear1']
for y in range(2022, 2027):
    i9, i6, p9 = cy.get((f'{y}-01-01', f'{y}-09-30')), cy.get((f'{y}-01-01', f'{y}-06-30')), paid.get((f'{y}-01-01', f'{y}-09-30'))
    p6 = paid.get((f'{y}-01-01', f'{y}-06-30'))
    if None not in (i9, i6, p9):
        u9, uq = i9 - p9, i9 - i6
        u6 = (i6 - p6) if p6 is not None else None
        print(f'   {y}: unpaid {u9/1e6:7.1f}m = {u9/uq*92:5.1f} days; current-year share paid by Q3 {100*p9/i9:4.1f}%' + (f'; change in unpaid during Q3 {(u9-u6)/1e6:+7.1f}m' if u6 is not None else ''))
print('4. Cash: first nine months')
ocf, ni = F['NetCashProvidedByUsedInOperatingActivities'], F['NetIncomeLoss']
for y in range(2023, 2027):
    a, b = ocf.get((f'{y}-01-01', f'{y}-09-30')), ni.get((f'{y}-01-01', f'{y}-09-30'))
    if a is not None and b is not None: print(f'   {y}: operating cash flow {a/1e6:+7.1f}m, net income {b/1e6:+7.1f}m')
