# Orange County Private Bank — Market Entry Plan

A business plan and working prospecting system for a **J.P. Morgan Private Bank
banker** covering Orange County, California.

Built around a specific profile: portfolio-management background, Spanish-language
and Latino-community edge, fully licensed, firm-provided data tooling.

## Contents

| File | What it is |
|---|---|
| [`01_market_sizing.md`](01_market_sizing.md) | Stress-tests the "75,000 households at $5M+" claim and derives the real addressable market, book economics, and the funnel that justifies a 200-name list |
| [`02_identification_process.md`](02_identification_process.md) | The five public signal layers used to identify $5M+ households, the scoring model, and the data-integrity rules |
| [`03_workflow.md`](03_workflow.md) | Pipeline stages, weekly/monthly/quarterly cadence, the COI referral engine, tooling, and metrics |
| [`04_outreach_strategy.md`](04_outreach_strategy.md) | Five access routes, the Spanish-language franchise build, the 30/60/90 plan, and the interview close |
| [`build_lead_list.py`](build_lead_list.py) | Generates and scores the lead list — re-runnable as triggers change |
| [`leads_orange_county_200.csv`](leads_orange_county_200.csv) | **200 scored target households** |

## Quick start

```bash
python3 build_lead_list.py     # regenerates leads_orange_county_200.csv
```

## The headline finding

Orange County's 75,000 households at $5M+ **net worth** is a defensible figure.
But it is the wrong number to plan against. Stripping out primary-residence equity
and stepping up to the Private Bank's real threshold:

```
 75,000   net worth ≥ $5M            ← the number they gave you
 37,000   investable ≥ $5M
 12,000   investable ≥ $10M          ← the actual addressable market
  3,200   investable ≥ $25M          ← the core
    450   investable ≥ $100M
```

Twelve thousand households is small enough for one banker to map. That reframes
the strategy from volume to precision — and makes competitive displacement, not
discovery, the central problem.

## The list

200 households across six segments, scored 0-100 on wealth signal, trigger
proximity, access quality, competitive whitespace, and affinity fit.

| Segment | Count |
|---|---:|
| A — Concentrated public-company equity | 60 |
| B — Private business owner, pre-liquidity | 45 |
| C — Real estate owner / operator | 35 |
| D — Professional practice equity | 25 |
| E — Inherited / multi-generational + foundation | 25 |
| F — Recent or imminent liquidity event | 10 |

| Priority band | Count |
|---|---:|
| P1 — Work now (80+) | 11 |
| P2 — Work this quarter (65-79) | 116 |
| P3 — Nurture (50-64) | 73 |

26 households carry a Spanish-language affinity flag.

## ⚠️ How to read the list — important

**This file contains no verified net worth data, and no such source exists.**

- `est_wealth_tier_INFERRED` is a **modelled inference** from public signals. It is
  never an assertion about anyone's actual finances.
- `name_status = NAMED-VERIFY` means a name drawn from public business reporting
  that **must be re-confirmed** in the firm's system of record before any contact.
  Executive rosters change constantly.
- `name_status = ROLE-RESOLVE` means the row identifies a *role* at a real entity;
  `verification_source` tells you exactly how to resolve it to a person.
- Records contain **business information only** — entity, role, public filing. No
  home addresses, personal contact details, or family information.
- All sourcing is **public record or firm-provided**. Nothing scraped, nothing
  purchased from an unapproved vendor. This is deliberate: as a JPM employee your
  prospect records and outreach materials are subject to supervisory review.

Treat every row as a **research task with a known answer path**, not as a fact.

## Sources

Public reporting from the Orange County Business Journal (largest private
companies, OC's wealthiest, OC500), Forbes billionaires coverage identifying 12
Orange County residents, IRS 990-PF foundation data via ProPublica Nonprofit
Explorer, SEC EDGAR, and California public business and property records.
Household counts and wealth tiers are modelled estimates with the method stated in
`01_market_sizing.md`.
