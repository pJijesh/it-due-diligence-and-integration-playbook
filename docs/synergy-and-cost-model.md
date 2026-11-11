# Synergy and cost model

How to estimate the one-off costs, the run-rate savings, the payback and a three-year view of an IT integration, and why the savings in a deal model are usually too high.

> Scope. This is a planning aid for the IT part of a deal model. Tax treatment, accounting classification and people-related costs (redundancy, retention, transfer terms) are for finance, tax, HR and legal advisers. Figures in the examples are invented.

## 1. Terms

| Term | Meaning |
|---|---|
| **One-off cost (cost to achieve)** | Money spent once to make something happen: hardware, migration, external support, backfill, early termination, programme management |
| **Run-rate saving** | An annual recurring reduction in cost once a change is complete, such as a licence no longer renewed |
| **Dis-synergy** | An extra recurring cost caused by the integration, such as security tooling for the new users or more service desk capacity. Enter it as a negative run-rate item |
| **Catch-up cost** | Cost to bring the target to a supportable, secure state whether or not it joins the buyer. A price topic, not a synergy |
| **Integration cost** | Cost to join the target to the buyer. A synergy-case cost |
| **Payback** | The point after which the cumulative net position (savings minus costs) stays at or above zero |
| **Confidence** | How sure the estimator is: high (quote or signed contract), medium (informed estimate), low (assumption) |

## 2. Estimating one-off costs

Build bottom-up from the [integration plan](../data/integration-plan.csv). For each workstream, list what has to be bought, paid for or done by someone who is not already on the payroll.

| Category | Examples | Often forgotten |
|---|---|---|
| Technology | Hardware refresh, firewall, licences for new users, tooling, ERP bridging support or upgrade | Licence true-ups, extra environments for testing |
| Migration | Mailboxes, files, ERP data, interfaces, renumbering a network | Data clean-up before migration, parallel running |
| External support | System integrator, security testing, network supplier, programme management | The target's suppliers charging for change |
| People | Backfill for target IT staff, contractors, training, retention (HR and legal lead) | Overtime, the cost of a key person leaving |
| Contracts | Early termination, notice-period overlap, consent fees | Double running while two systems are paid for |
| Compliance | Certification renewal, independent testing, audit | Re-testing after remediation |
| Contingency | Allowance for what is not yet known | Not applying it to low-confidence items |

Method:

1. **Use ranges.** Estimate low, likely and high for each item. Use the likely value in the model and keep the range for discussion.
2. **Ask suppliers for quotes** on the large items before signing. A quote moves an item from low to high confidence.
3. **Compare with the buyer's earlier projects.** A buyer that completed a similar migration knows what it really cost.
4. **Add a contingency by confidence.** The tool does this in the risk-adjusted view: costs rise by a default 0%, 15% or 30% for high, medium and low confidence items. These are illustrative assumptions and should be replaced with the buyer's own history.
5. **Separate catch-up from integration cost** in the CSV by naming, or by running two files.

## 3. Estimating run-rate savings

Start from the target's addressable spend, not from a percentage. For each saving, identify the specific contract, licence or cost line it removes.

Typical sources:

- **Licences:** moving users to the buyer's existing agreement, or retiring duplicate products.
- **Suppliers:** consolidating network, telecoms, hosting and support providers, and renegotiating on combined volume.
- **Infrastructure:** retiring servers, circuits and hosting that duplicate buyer services.
- **Systems:** retiring a duplicate finance or ERP platform after migration, usually the largest and latest saving.
- **People:** changes to IT staffing need HR and legal input and are not estimated here.

Sense checks before a saving goes in the model:

- **Compare with the spend line.** A saving cannot exceed the cost it removes. In the [worked example](worked-example.md) the total IT spend is small, so a claimed saving of half of it should prompt questions.
- **Name the contract and the date.** Savings start after the notice period and the end of the term, not when the decision is made.
- **Include the new costs.** Security tooling, monitoring and service desk capacity for the new users are real recurring costs.
- **Check whether the saving is already in the target's forecast.** Counting a saving the seller had already planned double counts it.
- **Give each saving an owner** who is accountable for removing the cost from a budget.

## 4. Timing

The tool uses simple, visible conventions. Change them if the plan justifies it.

- **One-off costs** are spent evenly across the twelve months of the stated year.
- **Run-rate savings** start in month 7 of the stated year (a mid-year convention, adjustable with `--savings-start-month`) and continue to month 36.
- **Year** means year 1, 2 or 3 after completion.
- **Payback** is the month after which the cumulative net position stays at or above zero. If it does not reach zero in 36 months the tool says so. If there are no one-off costs, payback is not defined.

## 5. Why synergy numbers are usually optimistic

Deal models tend to overstate savings and understate costs and delay. Common reasons:

1. **Planning optimism.** Plans assume things go to plan. The well-known planning fallacy applies to IT projects as much as to any other.
2. **Savings start at decision, not at contract end.** Notice periods and fixed terms delay them, sometimes by years.
3. **Double running.** Old and new systems both cost money during migration, and migrations overrun.
4. **Catch-up cost is mixed in or left out.** If the target's IT has been under-funded, the cost of repair swallows the saving. If it is left out, the case looks better than it is.
5. **Dis-synergies are forgotten.** Extra security tooling, support and licences for new users are rarely in the first draft.
6. **The same saving appears twice** under different workstreams.
7. **Savings are not removed from budgets.** A saving that stays in a budget is spent.
8. **The biggest saving is the latest and least certain.** Retiring a duplicate ERP depends on the longest, riskiest project, so it often falls outside the three-year window.
9. **Sellers present normalised numbers.** Spend that looks low because investment was deferred overstates the room to cut.
10. **People leave.** The knowledge needed to deliver savings may go with them.
11. **No owner and no tracking.** Without a named owner and a monthly check, nobody notices when a saving does not arrive.
12. **Confidence is not recorded.** A model that treats an assumption and a signed quote alike hides how fragile it is.

How the tool responds: it keeps the stated and the risk-adjusted views side by side, shows how much of the savings is low confidence, and reports how many years of savings the one-off costs equal. The risk-adjusted view multiplies savings by a factor (0.9, 0.6 or 0.3 for high, medium and low confidence by default) and raises costs by the uplift above. Negative run-rate items are treated as costs and raised, never reduced. The defaults are illustrative, not benchmarks.

## 6. Using the tool

Create a CSV with these columns:

| Column | Meaning |
|---|---|
| `item` | Short description (avoid commas, or quote the field) |
| `type` | `one-off` (a cost) or `run-rate` (an annual saving, negative for an extra recurring cost) |
| `amount` | Number. A one-off amount must not be negative. Currency symbols and thousands separators are accepted |
| `year` | 1, 2 or 3 |
| `confidence` | `high`, `medium` or `low` |

Run it:

```bash
python -m dd_playbook synergy examples/brightwater-synergy.csv --out dd-output
python -m dd_playbook synergy my-synergy.csv --assumptions my-assumptions.json --savings-start-month 4
```

An assumptions file overrides any of the defaults:

```json
{
  "savings_factor": {"high": 0.95, "medium": 0.7, "low": 0.4},
  "cost_uplift": {"high": 1.05, "medium": 1.2, "low": 1.4},
  "savings_start_month": 4
}
```

Output (`synergy-summary.md` and `synergy.json`):

- Totals of one-off costs and run-rate savings, as stated and risk-adjusted.
- Payback month for each view, or a plain statement that it is not within 36 months.
- A three-year table of costs, savings realised, net and cumulative net.
- A breakdown by confidence.
- A short list of observations.

## 7. Reading the example

The [Brightwater example](../examples/output/synergy-summary.md) has £815,000 of one-off costs and £59,000 of annual run-rate savings once new recurring costs are netted off. It does not pay back within three years on the stated numbers, and the risk-adjusted view turns the net saving negative. This is a realistic outcome for a small target with deferred investment: the IT integration does not pay for itself, and the bill is a price and planning matter. Most of the one-off cost is catch-up and consolidation, not saving-generating work.

## 8. Good practice

- Keep catch-up and integration costs visible and separate.
- Show the range and the confidence, not a single figure.
- Tie every saving to a contract, a date and an owner.
- Update the model at day 60 with actual spend (the plan has a task for this) and at day 100 with realised savings.
- Present the risk-adjusted view to the steering group alongside the stated one.
