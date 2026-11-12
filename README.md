# agl-risk-score-check

This is the data and code behind my Seeking Alpha piece "agilon health: What Changed When Its Doctors Joined". Every number in the piece that doesn't come straight from a filing or a call comes out of one of these scripts.

## How to run it

You need Python 3, nothing else. From any folder:

    python3 scripts/reach_haircut.py
    python3 scripts/reach_peers.py
    python3 scripts/mssp_growth.py
    python3 scripts/reach_history.py
    python3 scripts/mssp_base_rate.py
    python3 scripts/lobbying.py
    python3 scripts/model.py
    python3 scripts/pull_partb.py
    python3 scripts/doctor_level.py
    python3 scripts/event_study.py
    python3 scripts/deep_dives.py
    python3 scripts/reserves_cash.py

My own run is saved in results/. Before publishing I cloned this repo into an empty folder and reran every script from a different directory; every output matched the files in results/. pull_partb.py downloads about 350MB from CMS and takes several minutes. It keeps the downloads in a cache/ folder that isn't in the repo. doctor_level.py and event_study.py read from that folder.

The spreadsheet in model/ is the full model: income statement, balance sheet and cash flow for 2023 to 2028, members by year, the 2027 consensus line by line, what's disclosed about payors and contracts, and agilon's REACH ACOs by market. Inputs are blue with their sources; change the yellow cells and the rating cell updates. model.py does the same 2027 base in Python and the two agree.

## What each script does

- reach_haircut.py ranks every ACO REACH ACO by how much CMS took off its risk score for coding intensity and the growth cap, and shows where agilon's eight ACOs land.
- reach_peers.py compares agilon's ACOs with standard ACOs that joined REACH in the same year, and ranks the REACH ACOs of listed companies inside their own groups.
- mssp_growth.py works out risk-score growth for agilon's two Shared Savings Program ACOs in 2024 against every ACO and against ACOs that started the same way and on the same date.
- reach_history.py tracks where agilon's REACH ACOs ranked on risk-score growth from 2021 to 2024 against same-year peers. ACOs are matched by CMS ID, because the 2021 file uses older names.
- mssp_base_rate.py checks how unusual the Kentucky ACO's first-year growth was against every first-year ACO since 2020.
- lobbying.py totals agilon's federal lobbying disclosures by year and lists every filing that names the No UPCODE Act.
- doctor_level.py matches agilon's REACH clinicians to CMS's doctor-level Part B data and compares how fast their patients' risk scores grew from 2022 to 2024 with other primary care clinicians in the same state and specialty. It prints totals only. I'm not publishing a list of named doctors.
- pull_partb.py downloads CMS's doctor-level Part B files for 2016 to 2024 (risk score, patient age, dual-eligible count, ten chronic-condition rates, practice address) and the office-visit codes 99212 to 99215.
- event_study.py lines each clinician up on the year their ACO entered REACH and compares the change in their patients' risk scores with other REACH clinicians, both measured against peers of the same state and specialty. It gives ranges resampled three ways (by clinician, by practice address and by ACO), breaks the result down ACO by ACO, checks whether patient age, dual-eligible share, panel size and chronic-condition rates moved the same way, runs the 2022 to 2024 comparison against peers who started at a similar risk score and the higher-level office visit check, and prints the year-by-year gains so you can see whether they're slowing.
- deep_dives.py follows up the doctor-level result: whether agilon's clinicians moved toward billing home visits, whether the rise in kidney disease diagnoses came with more in-office kidney testing, and why doctors in other REACH ACOs fell against their peers (split by ACO type, payment arrangement and entry year, plus a check on whether ACOs that rose most before entry fell most after).
- reserves_cash.py works from agilon's own XBRL filings: receivable days and claims-payable days by quarter, prior-year reserve development each year, how much of the current year's claims were still unpaid at September 30, and operating cash flow against net income.
- model.py has the valuation, the three 2027 paths, the peer multiples, the cash-flow check, the audit cases and my 2026 to 2028 estimates.

## Sources

- CMS ACO REACH Financial and Quality Results, PY2023 and PY2024: https://data.cms.gov/cms-innovation-center-programs/accountable-care-models/aco-reach-financial-and-quality-results
- CMS Shared Savings Program Performance Year Financial and Quality Results, PY2020, PY2022, PY2023, PY2024 (data.cms.gov)
- Lobbying Disclosure Act filings for client "agilon": https://lda.gov/api/v1/filings/?client_name=agilon
- CMS Medicare Physician & Other Practitioners, by provider and by provider and service, 2022 and 2024: https://data.cms.gov/provider-summary-by-type-of-service/medicare-physician-other-practitioners
- CMS ACO REACH PY2024 provider file (participant clinicians by ACO), from the same CMS REACH page
- agilon's XBRL facts from SEC EDGAR, saved as data/sec_xbrl_agl.csv: https://data.sec.gov/api/xbrl/companyfacts/CIK0001831097.json
- agilon's 10-K, 10-Qs and 8-K earnings releases on EDGAR (CIK 1831097)
- agilon's Q1, Q2 and Q3 2026 earnings calls
- Peer guidance from the Q3 2026 8-K releases of Privia, Astrana and Alignment
- CMS FY2025 Medicare Part C improper payment findings, and CMS's 21 May 2025 RADV announcement
- data/inputs.csv lists every hand-entered number with where it came from

## Things to be careful with

- REACH and the Shared Savings Program cover traditional Medicare. agilon's money is in Medicare Advantage, and I can't show the same clinicians code both.
- A REACH haircut measures growth against a reference year. Sicker or newer patients can drive that too.
- Parent companies for the league table come from each company's own SEC filings, matched by ACO name.
- The per-point figures come from management's own sizing on the Q1 and Q2 calls.
- The 2027 base is built line by line from the 2026 guide: revenue per member grows at CMS's 4.98% (which includes the industry's 2.50% risk-score trend), medical cost at 6.4%, partners take a third of the margin, G&A grows 3%. Every one of those is an assumption you can change.
- The path weights, audit probabilities and pass-through rates are my judgment calls. Change them in model.py and see what moves.
- The bridge from adjusted EBITDA to GAAP net income is calibrated to the first nine months of 2026, which had unusual severance. The script checks it reproduces the $82.8m actual.
- The doctor match is by first name, last name and state. 1,109 of 1,631 names matched one NPI; names that matched more than one were dropped. Clinicians who changed state or specialty between 2022 and 2024 are left out.
- The event study uses the 2024 roster, so a clinician who joined an ACO after its first year is lined up on the ACO's entry year, not their own. The comparison group is other REACH clinicians only; Shared Savings Program rosters are published by practice tax ID, not by clinician, so I couldn't add them.
- CMS's chronic-condition rates come from all of a patient's claims, including the doctor's own, so they aren't fully independent of how that doctor documents. Age and dual-eligible share are. CMS rounds both to whole numbers, so the patient-mix check uses trimmed means.
- Practice is approximated by street address and ZIP in the year before entry. agilon has only eight ACOs, so the range resampled by ACO is the widest and the most honest.
- Kidney tests only show up under a doctor when the practice runs them in the office. Tests sent to an outside lab are billed by the lab, so the numbers understate testing, more so for practices without their own lab.
- Receivable and claims days use the quarter's revenue and medical cost, so they move with the seasons; compare the same quarter across years. Before 2023 the fourth quarters are distorted by restatements for discontinued operations, so the table starts in 2023.
- Part B risk scores are for traditional Medicare patients only, and a doctor's average moves if their patient mix changes.
- The lobbying filings don't say which side agilon took on any bill.

## Corrections

None so far.
