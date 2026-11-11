# IT due diligence guide

How to run IT due diligence on an acquisition target in the time a deal usually allows, and how to turn the findings into a decision, a price adjustment or a term in the agreement.

> Scope. This guide covers IT only. Legal, tax, financial and HR diligence run alongside and are out of scope. Where an IT finding touches a contract, a regulatory duty, an accounting treatment or an employment matter, the IT team reports the fact and the relevant adviser interprets it. Nothing here is legal, tax or HR advice.

## 1. What IT diligence is for

A deal team usually has days or weeks, not months. IT diligence has five jobs:

1. **Find anything that should stop or reshape the deal**, for example an active compromise or a core licence that cannot transfer.
2. **Estimate the real cost of bringing the target to a supportable, secure state**, so it reaches the price discussion as a number and not as a surprise after completion.
3. **Test the deal thesis.** If the plan assumes merging two finance systems in a year, check that it is technically possible.
4. **Identify what must work on Day 1** and what depends on the seller, a supplier or one person.
5. **Give the integration team a head start**: an inventory, a risk log and a list of early actions.

It is not an audit and it is not a penetration test. It is a structured, evidence-led look at a business that is being asked to share information quickly and has its own reasons to present itself well.

## 2. Scoping to the time available

Decide the depth first, then stick to it. The question bank in [`data/question-bank.csv`](../data/question-bank.csv) carries a weight from 1 to 5 on every question, which makes it easy to cut to the time available.

| Time available | Depth | What to ask | Questions in this bank |
|---|---|---|---|
| About a week | Red-flag screen | Weight 5 questions only, plus a short call with the IT lead | 17 |
| Two to three weeks | Standard | Weight 4 and 5 questions, document review and four to six interviews | 50 |
| Four weeks or more | Full | All questions, a site visit, sampled evidence checks and supplier calls | 104 |

Adjust for the target. A small manufacturer with an old ERP and a warehouse needs more time on applications and operational systems. A services business with mostly cloud tools needs more on identity, data and suppliers. A regulated target needs more on compliance and customer requirements.

Fix these points before starting:

- **Access.** What the seller will share, when, and whether the IT lead can be told about the deal (often they cannot until late).
- **Clean team rules.** If the buyer and target compete, some information may need to go to advisers only.
- **Materiality.** Ask the deal team for the amount of one-off IT cost that matters to them. Without it, every finding sounds equally important.
- **Who reads the result.** The deal team wants decisions and numbers. The integration lead wants detail. Write two outputs from one set of findings.

## 3. The request list

Send a short prioritised list on the first day, then follow up. A 200-line request overwhelms a small IT team and produces poor answers. Start with these items. Each one maps to questions in the bank, and the `evidence_to_request` column gives the specific wording for each question.

**First request (day 1):**

1. Organisation chart of IT, including contractors and outsourced services.
2. Asset and application inventory, hosting map and network diagram.
3. IT contract register with values, terms, notice periods and renewal dates.
4. Software licence agreements for the main systems, with entitlement and usage.
5. Three years of IT spend by category, reconciled to the ledger.
6. Capital plan and list of any deferred or committed spend.
7. List of in-flight projects with budget and status.
8. Cyber incident and outage history for three years, with root causes.
9. Backup schedule, last restore test and any recovery plan.
10. Latest security assessment, penetration test, certifications and insurance schedule.

**Follow-up request (after the first interviews):**

11. Evidence behind specific answers: identity settings export, patch report, endpoint console coverage, account lists.
12. Customer contract clauses on security, hosting and audit.
13. Data protection records: record of processing, breach log, processor list.
14. Detail on any item the first round raised: ERP support correspondence, custom code list, shared services list.

Record what was asked for, when, and what arrived. Evidence that never arrives is itself a finding.

## 4. Interviews

Four to six conversations usually cover the ground. For each, agree the questions in advance and take notes against question IDs so the answers can be scored.

| Who | Why | Typical focus |
|---|---|---|
| IT lead or manager | Knows the estate and the weak points | Whole bank, starting with the weight 5 questions |
| Finance lead | Knows spend, contracts and month-end pain | IT spend, contracts, reporting, ERP usage |
| Operations or warehouse lead | Knows what hurts when systems fail | Outages, operational systems, Day 1 needs |
| HR lead | Joiner and leaver reality, key staff | People, access removal, training |
| A heavy user of the main system | Sees workarounds | Spreadsheets, manual steps, customisations |
| Key supplier (if permitted) | Independent view | Support position, contract terms, service history |

Practical rules:

- **Ask for demonstrations, not statements.** "Show me the MFA settings" is better than "Do you use MFA?"
- **Ask the same question of two people.** Differences are informative.
- **Ask what they would fix first.** A good IT lead will answer immediately and the answer is often a red flag the documents do not show.
- **Treat tone as data.** Defensiveness, vagueness or "that is on the list" repeated across topics usually means the topics are not being handled.
- **Be fair to the IT team.** The people being interviewed may be affected by the deal and will be needed afterwards. Findings are about systems and processes, not individuals.

## 5. Scoring

Each question is scored from 0 to 4 on how well the target's position meets the good practice the question describes. Score what was seen, not what was said.

| Score | Meaning |
|---|---|
| 0 | Absent, or a serious problem was found |
| 1 | Weak, informal or mostly undocumented |
| 2 | Partly in place, with clear gaps or an unfunded plan |
| 3 | Largely in place, with minor gaps |
| 4 | Fully in place, current and evidenced |
| NA | Not applicable or not yet assessed (leaves the question out of the maths) |

Alongside the score, record notes and whether evidence was seen (`yes` or `no`). By default, an answer without evidence is scored as no higher than 2, so that a confident claim does not lift a domain until it has been backed up. The cap is configurable.

### Using the tool

```bash
python -m dd_playbook template --worksheet --out assessment.csv   # blank worksheet with questions
# ... fill in answer_score, notes and evidence_seen during interviews ...
python -m dd_playbook score assessment.csv --target "Target Ltd" --acquirer "Buyer Group" --out dd-output
```

The `score` command writes `summary.md` (one page), `scores.json` and `red-flags.csv`. It calculates:

- **Domain score:** the weight-averaged score of the answered questions, as a percentage of the maximum.
- **Status:** GREEN at 70 or above, AMBER at 50 or above, otherwise RED. A domain with less than 60 percent of its weight answered shows INSUFFICIENT DATA, and a domain with a critical red flag cannot be GREEN. Thresholds live in a JSON file ([`data/scoring-config.json`](../data/scoring-config.json) shows the defaults) and can be changed with `--config`.
- **Red-flag register:** every question that is weighted 4 or 5 and scored 1 or lower, every weight 3 or more question scored 0, and any question the assessor marks as a red flag in the optional `red_flag` column.
- **Evidence gaps:** high-weight answers with no evidence seen, with the evidence to ask for.

The scores are a way to organise judgement and to compare domains, not a verdict. A single critical item can matter more than an average of 70.

## 6. Red-flag triage

As findings emerge, sort each into one of three groups. [Risk and red flags](risk-and-red-flags.md) gives examples of each.

| Group | Test | Typical response |
|---|---|---|
| **Stop or re-think** | Threatens revenue, legal standing or the deal thesis, and cannot be fixed within the integration timeline or budget | Escalate to the deal lead immediately, with the evidence |
| **Price or terms** | Real and fixable, but with a cost or risk the buyer should not absorb silently | Quantify, then take to the deal team for price, conditions or protections |
| **Fix after completion** | Real, contained and within the integration budget | Add to the risk and cost log and the 100-day plan |

Triage questions for each finding:

1. What is the worst realistic outcome, and how likely is it in the first year?
2. What does it cost to fix, and how long does the fix take? Give a range.
3. Does it get worse once the buyer's network, staff or customers are connected?
4. Can it be contained before connection?
5. Does the seller know, and was it disclosed?

## 7. How findings change price or terms

IT diligence supplies facts and estimates. The deal team, with legal and finance advisers, decides how to use them. The usual mechanisms are below, and the right choice depends on the deal.

| Finding | Question for the deal team | Possible mechanism (advisers decide) |
|---|---|---|
| Large catch-up cost (unsupported platforms, deferred refresh, security remediation) | Is this a cost the buyer should absorb at the agreed price? | Price adjustment or treatment as a debt-like item, using the diligence estimate |
| Contract or licence that needs consent or reprices on change of control | Who obtains consent and what if it is refused? | Condition to completion, or a specific provision on cost |
| Services supplied by the seller or a related party | Will they continue, for how long and at what price? | Transitional services agreement with defined scope, price, term and exit help |
| Undisclosed or unremediated security incident | Is there a liability or a continuing exposure? | Specific warranty or indemnity, retention or escrow, remediation before completion |
| Domain, cloud or system accounts held by individuals | Can ownership be secured before completion? | Condition to completion or completion deliverable |
| Single key person | Will they stay, and is knowledge documented? | Retention and handover arrangements with HR and legal, documentation as a completion task |
| Missing certification that customers require | What revenue depends on it, and how long to regain it? | Condition or covenant, price consideration for revenue at risk |
| Licence non-compliance | What is the exposure and who bears it? | Warranty or indemnity, price consideration, remediation plan |
| Diligence access refused or evidence missing | What is the cost of not knowing? | Wider warranty protection, price for uncertainty, or walk away |

Put numbers in ranges: a low, likely and high case for each catch-up cost. A price conversation works better with "between X and Y, most likely Z, and this is what it includes" than with a single figure that cannot be defended.

Keep catch-up costs (what it takes to make the target safe and supportable regardless of the deal) separate from integration costs (what it takes to join it to the buyer). The first is a price topic. The second belongs in the synergy case. See [Synergy and cost model](synergy-and-cost-model.md).

## 8. What to hand over

Three outputs, in this order:

1. **Two-page summary for the deal team.** Overall position, domain scores, red-flag register with the triage group, cost ranges, and the three things to decide. The tool's `summary.md` is the starting point.
2. **Risk and cost log for the integration lead.** Every finding, owner, proposed action, cost range and the date by which it needs action. This feeds the [integration plan](../data/integration-plan.csv).
3. **Evidence index.** What was seen, where it is stored, and what is still outstanding.

## 9. Common mistakes

- **Treating the seller's IT lead as the only source.** Check with finance, operations and suppliers.
- **Scoring on intent.** A plan to enable MFA next quarter scores 0 or 1 today.
- **Spending the time on the wrong things.** In a short window, concentrate on the weight 5 questions: support status, MFA, patching, backups, key people, change of control, licences, shared services and Day 1 dates.
- **Forgetting the buyer.** Integration readiness includes the buyer's own capacity. Diligence that finds problems nobody can fix in the time is incomplete.
- **Late discovery of dates.** Renewals, notice periods, payroll cut-offs and peak trading periods decide how much can be done in the first 100 days.
- **Reporting everything.** A list of 80 findings hides the 8 that matter. Rank them.
