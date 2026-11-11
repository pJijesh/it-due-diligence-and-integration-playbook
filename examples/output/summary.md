# IT due diligence summary: Brightwater Fixings Ltd

Acquirer: Larkfield Components Group | Target: Brightwater Fixings Ltd

## Headline

- Overall weighted score: **53.4 out of 100**, status **AMBER**.
- Questions answered: 101 of 104 (98.3% of total weight).
- Red flags: **15** (7 critical).
- Scored answers without evidence seen: 7 (capped at 2 in the maths).

## Domain scores

| Domain | Score | Status | Answered | Red flags |
| --- | ---: | --- | ---: | ---: |
| Governance and strategy | 53.0 | AMBER | 10 of 10 | 2 |
| Infrastructure and cloud | 58.3 | AMBER | 10 of 10 | 1 |
| Applications and ERP | 46.1 | RED | 10 of 10 | 3 |
| Data and data protection | 58.6 | AMBER | 9 of 10 | 0 |
| Cyber security | 35.6 | RED | 12 of 12 | 3 |
| People and skills | 55.6 | AMBER | 9 of 10 | 1 |
| Suppliers, contracts and licences | 58.1 | AMBER | 10 of 10 | 2 |
| IT spend | 71.1 | GREEN | 9 of 10 | 0 |
| Service management and continuity | 47.1 | RED | 10 of 10 | 2 |
| Integration readiness | 57.1 | AMBER | 12 of 12 | 1 |

## Red-flag register

| ID | Severity | Question | Why flagged | Assessor notes |
| --- | --- | --- | --- | --- |
| SEC-01 | Critical | Is multi-factor authentication enforced for remote access, email and every administrator account? | high-weight item (weight 5) with a low score (0); scored 0, so the red-flag condition applies; assessor marked the red-flag condition as observed | No MFA on remote desktop gateway, email for 60 staff, or administrator accounts. Confirmed from the identity settings export. |
| APP-02 | Critical | Is the core ERP or finance system within vendor support, with a known version, module list, user count and funded upgrade plan? | high-weight item (weight 5) with a low score (1) | ERP in use for 11 years. Vendor support ends in 14 months and no upgrade or replacement is funded. |
| INT-07 | Critical | How does the target's security compare with the buyer's minimum standard, and is the cost of closing the gaps before connection known? | high-weight item (weight 5) with a low score (1) | Target is below the acquirer's baseline on MFA, patching, endpoint management and logging. Gap list drafted, not costed. |
| PPL-02 | Critical | Is knowledge of core systems and administrator access shared across more than one person, with written documentation? | high-weight item (weight 5) with a low score (1) | The IT lead alone knows the ERP customisations, firewall configuration and backup set-up. Credentials in a notebook and a personal password manager. |
| SEC-03 | Critical | Are security patches applied promptly to internet-facing systems and endpoints, with evidence of timing? | high-weight item (weight 5) with a low score (1) | Patch report shows 22 devices and the firewall with critical updates more than 60 days old. |
| SUP-02 | Critical | Have IT contracts been checked for change of control, assignment and termination terms that the transaction could trigger? | high-weight item (weight 5) with a low score (1) | ERP support and licence agreement requires vendor consent on a change of control and allows repricing. Legal diligence to confirm wording. |
| SVC-04 | Critical | Are all critical systems and SaaS data backed up to a separate location, and has a full restore been tested in the last 12 months? | high-weight item (weight 5) with a low score (1) | Daily backups go to a device in the same server room. No restore test has been done. Cloud copy covers email only. |
| APP-03 | High | Is customisation of the ERP limited, documented, in source control and maintained by more than one person? | high-weight item (weight 4) with a low score (1) | Around 140 custom reports and 12 custom modules. A single former contractor wrote most of them. No source control. |
| APP-10 | High | Are production, warehouse and machine-connected systems supported by a known party and separated from the office network? | high-weight item (weight 4) with a low score (1) | Warehouse scanners and one machine controller sit on the office network and run unsupported software. |
| GOV-05 | High | Has the target avoided deferring IT spend (renewals, upgrades, hires) ahead of the sale? | high-weight item (weight 4) with a low score (1) | Server refresh and ERP upgrade were each postponed twice. No IT capital spend approved for three years. |
| GOV-07 | High | Does the target meet the IT requirements set by its regulators and major customers (audit rights, certifications, security questionnaires)? | high-weight item (weight 4) with a low score (1) | Two largest customers require a current Cyber Essentials certificate. Certificate lapsed 8 months ago and renewal has not started. |
| INF-04 | High | Are cloud, hosting and domain accounts registered to the company, with named administrators and more than one recovery route? | high-weight item (weight 4) with a low score (1) | Main company domain and the website hosting account are registered to the founder personally. |
| SUP-10 | High | Are any IT services supplied by related parties (former owners, directors' companies) under written commercial terms at market prices? | high-weight item (weight 4) with a low score (1) | Telephony and website hosting supplied by a company owned by the seller's family. No contract and no price list. |
| SVC-07 | High | Is system documentation current (diagrams, procedures, runbooks) with privileged credentials held in a managed vault? | high-weight item (weight 4) with a low score (1) | Few diagrams and no runbooks. Privileged credentials are in the IT lead's notebook. |
| SEC-11 | High | Are leavers' accounts and access removed promptly, and are dormant, service and shared accounts reviewed? | assessor marked the red-flag condition as observed | No formal process. 9 accounts of leavers from the last year were still active at the time of review. |

## Evidence gaps on high-weight questions

These answers carry high weight but no evidence was seen, so they are scored on the capped value. Request the evidence before relying on them.

| ID | Stated score | Scored as | Evidence to request |
| --- | ---: | ---: | --- |
| APP-08 | 2 | 2 | Runbooks, installation media and licences, restore test records, vendor support status for each critical application. |
| PPL-03 | 2 | 2 | Retention or notice terms for key roles, summary of conversations with management (HR and legal lead the detail). |
| SEC-02 | 3 | 2 | Console screenshots or exports showing coverage, alert handling records, monitoring service contract. |
| SVC-05 | 2 | 2 | Business impact analysis, objectives list, recovery test results against objectives. |
| SVC-06 | 3 | 2 | Plan documents, last exercise report, actions arising, supplier recovery commitments. |

## How this was calculated

Each answer is scored 0 to 4. A domain score is the weight-averaged score of its answered questions, as a percentage. Status is GREEN at 70 or above, AMBER at 50 or above, otherwise RED. A domain with less than 60% of its weight answered shows INSUFFICIENT DATA. A domain or overall result with a critical red flag cannot be GREEN. A question is flagged when its weight is 4 or more and the scored value is 1 or less, when it scores 0 and has weight 3 or more, or when the assessor marks the red-flag condition as observed.

Inputs: assessment SHA-256 `99a4bad9b1cf69cd`, question bank SHA-256 `d6415338b82a9b88`.

This is a structured diligence aid, not legal, tax or HR advice. Legal, tax, financial and HR diligence run alongside IT diligence and are out of scope here.
