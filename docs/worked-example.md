# Worked example: Larkfield Components Group and Brightwater Fixings Ltd

A fictional deal that runs the whole method end to end. Both companies, the people, the figures and the findings are invented for illustration, and any resemblance to a real business is accidental. The data is not a benchmark.

## The deal

Larkfield Components Group (the acquirer) is buying Brightwater Fixings Ltd (the target), a family-owned supplier of industrial fasteners with about 235 staff, two sites and a small IT team. Planned completion is three days before a payroll cut-off, which the readiness work flags as a problem.

The target has two IT staff and a part-time contractor. Its ERP is eleven years old, heavily customised and has a vendor support end date 14 months away. There is no multi-factor authentication on remote access, backups sit in the same room as the servers, and key knowledge is held by one person. The founder holds the main domain personally, and telephony and website hosting come from a company owned by the seller's family.

## Files

| File | What it is |
|---|---|
| [`examples/brightwater-assessment.csv`](../examples/brightwater-assessment.csv) | The completed assessment (worksheet format, all 104 questions, 3 marked NA) |
| [`examples/brightwater-synergy.csv`](../examples/brightwater-synergy.csv) | The synergy and cost inputs (19 items) |
| [`examples/output/summary.md`](../examples/output/summary.md) | Generated one-page summary |
| [`examples/output/scores.json`](../examples/output/scores.json) | Generated scores in JSON |
| [`examples/output/red-flags.csv`](../examples/output/red-flags.csv) | Generated red-flag register |
| [`examples/output/synergy-summary.md`](../examples/output/synergy-summary.md) | Generated synergy summary |
| [`examples/output/synergy.json`](../examples/output/synergy.json) | Generated synergy figures in JSON |

Regenerate the outputs with `python scripts/regenerate_examples.py`. A test compares a fresh run with the committed files.

## Step 1: score the assessment

```bash
python -m dd_playbook score examples/brightwater-assessment.csv \
  --target "Brightwater Fixings Ltd" --acquirer "Larkfield Components Group" --out examples/output
```

Result: overall **53.4**, status **AMBER**, with 15 red flags, of which 7 are critical.

| Domain | Score | Status |
|---|---:|---|
| Governance and strategy | 53.0 | AMBER |
| Infrastructure and cloud | 58.3 | AMBER |
| Applications and ERP | 46.1 | RED |
| Data and data protection | 58.6 | AMBER |
| Cyber security | 35.6 | RED |
| People and skills | 55.6 | AMBER |
| Suppliers, contracts and licences | 58.1 | AMBER |
| IT spend | 71.1 | GREEN |
| Service management and continuity | 47.1 | RED |
| Integration readiness | 57.1 | AMBER |

Points to notice:

- **Cyber security is RED** because of the MFA gap, outstanding patches and weak logging. The insurance proposal and the real position disagree, so legal advisers need to know.
- **IT spend is GREEN** on the numbers. The spend reconciles to the ledger and the target is standalone, but total spend is low because investment was deferred. The score does not capture that, which is why the question on deferred spend (GOV-05) is a red flag in a different domain.
- **Five high-weight answers have no evidence yet.** The tool scores them at no more than 2 and lists them with the evidence to request.
- **The seven critical flags** are MFA (SEC-01), ERP support (APP-02), the security gap against the buyer's baseline (INT-07), key person dependency (PPL-02), patching (SEC-03), change of control on the ERP contract (SUP-02) and untested backups (SVC-04).

## Step 2: triage

Using [Risk and red flags](risk-and-red-flags.md), the deal team sorts the findings. There is no deal-breaker. The price-or-terms group contains the ERP support position, the change of control clause, the key person dependency, the related-party services and the catch-up cost for servers, firewall and devices. The rest are fix-after-completion items with Day 1 actions: MFA, backups, domain ownership and isolation of warehouse systems.

## Step 3: model the cost

```bash
python -m dd_playbook synergy examples/brightwater-synergy.csv --out examples/output
```

| Measure | As stated | Risk-adjusted |
|---|---:|---:|
| One-off costs | £815,000 | £939,500 |
| Net run-rate savings | £59,000 | -£14,900 |
| Net position after 3 years | -£819,500 | -£1,031,950 |
| Payback | not within 36 months | not within 36 months |

The result is the lesson. IT integration of a small, under-invested target is a cost to be priced, not a source of savings. The business case for the deal rests on commercial synergies, and the IT bill, mostly catch-up, belongs in the price discussion. Half of the positive run-rate savings are rated low confidence, chiefly the retirement of the target ERP.

## Step 4: plan the first 100 days

The [integration plan](../data/integration-plan.csv) applies. For Brightwater the dated risks are the payroll cut-off after completion, two contract renewals that fall due 40 and 75 days after completion (both auto-renewing for three years), and the ERP support end date. The plan puts notice decisions inside the first 30 days, MFA and backups on Day 1 and the first month, the ERP options paper in days 31 to 60 and the funded ERP decision in days 61 to 100.
