# Risk and red flags

How to tell a deal-breaker from a fixable issue, with examples. Every question in [`data/question-bank.csv`](../data/question-bank.csv) has a `red_flag_if` column that describes the observation that should be treated as a red flag.

> Scope. IT findings only. Whether an issue is a legal breach, a warranty matter or an accounting adjustment is for legal, tax and finance advisers. This page helps the IT team classify and describe what it found, and does not give legal advice.

## 1. Three groups

| Group | Meaning | How often (practitioner judgement, not a statistic) |
|---|---|---|
| **Deal-breaker** (stop or re-think) | The problem cannot be fixed within the integration timeline and budget, or threatens revenue, legal standing or the deal thesis | Rare. Most deals have none |
| **Price or terms** | Real and fixable, but the cost or exposure is large enough that the buyer should not absorb it silently | A handful |
| **Fix after completion** | Real, contained and affordable within the integration budget | Most findings |

Four tests help decide the group:

1. **Reversibility.** Can it be fixed, and by when? A missing MFA setting takes days. An ERP with no vendor and lost source code takes years.
2. **Containment.** Can it be isolated until fixed? An unpatched warehouse system can be segmented. A compromised directory cannot be left connected.
3. **Revenue and legal exposure.** Does a customer contract, certification or regulatory duty depend on it?
4. **Disclosure.** Was it disclosed? A known weakness described honestly is a lesser concern than the same weakness discovered by accident.

## 2. Typical deal-breakers

These are uncommon. When one appears, escalate to the deal lead the same day with the evidence.

| Red flag | Example | Why it can end or reshape the deal |
|---|---|---|
| Evidence of a current compromise | Unknown administrator accounts, unexplained outbound connections or encrypted files on a server | Connecting the buyer's network would spread it, and the scope of loss is unknown |
| Core system the target has no right to use or transfer | Licence registered to a seller who will not assign it, or a vendor refusing consent on change of control | The business may not be able to run on completion, or must repurchase at a price the vendor sets |
| Essential service supplied by the seller with no commitment | The ERP, network or directory runs on seller infrastructure, and the seller will not agree transitional services at a fixed price | Day 1 depends on a counterparty with no obligation to help |
| Unreported or unmanaged serious data incident | A personal data breach that was never logged or assessed, with continuing exposure | Regulatory and customer liability transfers with the company (legal advisers assess) |
| Unrecoverable critical software | Bespoke system with no source, no vendor and no documentation | Cannot be supported, migrated or fixed, so the process it runs is at risk |
| Customer requirement that cannot be met | Customer contract requires a certification or hosting arrangement the target lacks and cannot regain in time | Revenue depends on it |
| Remediation cost beyond materiality | Catch-up cost exceeds the threshold the deal team set | The price no longer reflects the asset |
| Access to evidence refused | Seller will not show settings, reports or contracts for the highest-weight questions | The deal team is pricing blind |

## 3. Typical fixable issues

Most findings fall here. They matter for cost, timing and Day 1 control, and many belong in the price discussion.

| Issue | Typical fix | Time to fix | Group |
|---|---|---|---|
| No MFA on remote access and administrator accounts | Enforce MFA, with user communication | Days for administrators, weeks for all users | Fix after completion (Day 1 priority). Check insurance answers |
| Critical patches outstanding | Patch, replace unsupported devices, add monitoring | Weeks | Fix after completion, with cost in the catch-up estimate |
| Servers and firewall past vendor support | Replace or upgrade | Weeks to months | Price or terms if the cost is large |
| Backups never restored | Add a separate copy, test restores | Weeks | Fix after completion (first 30 days) |
| Key person dependency | Documentation, cover, retention and contractor support | Weeks to months | Price or terms (retention is for HR and legal) |
| Domains and cloud accounts held by individuals | Transfer to company ownership | Days to weeks | Completion deliverable |
| Lapsed security certification | Remediate and reassess | Weeks to months | Price or terms if customers require it |
| ERP nearing end of vendor support | Bridging support, upgrade or migration | Months to years | Price or terms, and a major workstream |
| Heavy ERP customisation | Document, move to source control, reduce | Months | Fix after completion, affects migration cost |
| Spreadsheets carrying critical processes | Move to controlled tools, add review | Months | Fix after completion |
| Unsegmented operational systems | Segment and isolate | Weeks | Fix after completion, before connection |
| Missing retention rules and old data | Define rules, clean up before migration | Months | Fix after completion |
| Auto-renewing contracts inside the first 100 days | Serve notice, renegotiate | Days if caught early | Fix after completion, but it needs action in the first 30 days |
| Undocumented joiner and leaver process | Define a process, run an account review | Weeks | Fix after completion |
| Related-party services with no contract | Contract at market terms, or transitional services | Weeks | Price or terms |

## 4. Context changes the answer

The same finding can sit in different groups depending on the situation:

- **Size of the target.** A small business with no DR plan is normal. A mid-sized one with an order system that stops trading when it fails is not.
- **What is being connected.** A weak environment that stays standalone is a different risk from one joined to the buyer's network on day 30.
- **Sector and data.** Regulated sectors, children's data, health data and payment data raise the stakes of the same control gap.
- **Customer reliance.** If two customers account for most of the revenue and both require a certification, a lapsed certificate moves up the list.
- **Deal timing.** A finding discovered before signing can change terms. After signing it becomes a cost.
- **Buyer capability.** A buyer with a mature security team can absorb more remediation than one without.

## 5. Worked classification

Using the fictional [worked example](worked-example.md) of Brightwater Fixings Ltd:

| Finding | Group | Reasoning |
|---|---|---|
| No MFA on remote access, email or administrators (SEC-01) | Fix after completion, Day 1 action | Fix takes days, but the insurance proposal says otherwise, so legal should look at the cover |
| ERP vendor support ends in 14 months, unfunded (APP-02) | Price or terms | Large cost and long timeline, and the migration is part of the deal thesis |
| ERP licence needs vendor consent on change of control (SUP-02) | Price or terms, possible condition | Consent is outside the buyer's control, legal reads the clause |
| One IT lead holds all undocumented knowledge (PPL-02) | Price or terms | Retention and handover decide how much of the plan can be delivered |
| Backups in the same room, never restored (SVC-04) | Fix after completion, first 30 days | Quick to fix, but should be proved before Day 1 where possible |
| Domains registered to the founder (INF-04) | Completion deliverable | Low effort, high consequence if missed |
| Services from a seller-related company with no contract (SUP-10) | Price or terms | Needs a written transitional agreement |
| Warehouse and machine systems on the office network (APP-10) | Fix after completion, before connection | Isolate first |
| No finding in the example reaches deal-breaker | n/a | The target is weak but recoverable, at a cost that belongs in the price discussion |

## 6. Warning signs in the process

How the target behaves during diligence tells as much as what the documents say:

- **Evidence arrives only as fresh screenshots**, with nothing historic.
- **The answer to many questions is "we are about to do that".**
- **The IT lead is not allowed to talk to the buyer's team**, or answers are filtered through someone else.
- **Documents contradict interviews.** For example, the insurance form says MFA is enforced and the identity export shows it is not.
- **Inventory counts do not match invoices.** Finance finds systems IT cannot describe.
- **Everything is "owned by the founder".** Accounts, domains and contacts tied to individuals.
- **No history of change.** No tickets, no change log and no incident record usually means the records are not kept, not that nothing happened.

## 7. Describing a red flag

A good entry in the red-flag register has:

1. **What was found**, in a sentence, with the question ID.
2. **Evidence**, meaning where it was seen and when.
3. **Impact**, meaning what could happen and how likely it is.
4. **Cost and time to fix**, as a range.
5. **Group**: stop, price or terms, or fix after completion.
6. **Owner and date** for the next step.

The tool's `red-flags.csv` carries the question, the trigger and the assessor's notes. Add the cost range, group and owner in the deal team's own tracker.
