# 03 — The Operating Workflow

A process that isn't on a calendar isn't a process. This is the weekly, monthly,
and quarterly machine that keeps 200 households moving.

---

## The pipeline stages

| Stage | Definition | Exit criteria |
|---|---|---|
| **0 — Universe** | Anchor entity identified | Passes the wealth-signal screen |
| **1 — Resolved** | Anchor converted to a named household | Name + role confirmed in a public source |
| **2 — Routed** | A specific warm path identified | A named introducer has agreed to make the introduction |
| **3 — Engaged** | First substantive conversation held | Household confirms a real need |
| **4 — Opportunity** | Defined need + timeline + approximate size | Team meeting scheduled |
| **5 — Proposal** | Formal solution presented | Terms under discussion |
| **6 — Won / Lost** | Account funded, or a documented loss reason | Post-mortem recorded |

**Target standing volumes** for a banker running a 200-name list:

```
Stage 1  Resolved      200
Stage 2  Routed         80
Stage 3  Engaged        50   ← the number that actually predicts your year
Stage 4  Opportunity    20
Stage 5  Proposal       12
Stage 6  Won            10
```

If Stage 3 is below 40, nothing downstream will work. It is the only number worth
managing weekly.

---

## Weekly cadence (~11 hours of protected prospecting time)

| Day | Block | Activity |
|---|---|---|
| **Mon** | 60 min | **Trigger sweep.** New Form 4/144 filings from the 20 OC issuers; OC M&A announcements; new grant deeds over $4M; probate filings. Anything found is scored and inserted at the correct band. |
| **Mon** | 60 min | **Week plan.** Select 10 households for active work. Confirm each has a named path in. |
| **Tue** | 3 hrs | **COI block.** Two meetings with centres of influence — CPAs, M&A attorneys, estate attorneys, 1031 intermediaries, CRE brokers, insurance specialists. Every meeting must end with a specific named introduction request. |
| **Wed** | 2 hrs | **Direct outreach.** 10 personalised approaches. Never a template. Each references the specific public event that prompted the contact. |
| **Thu** | 3 hrs | **Client and prospect meetings.** Protected. Nothing else booked. |
| **Fri** | 60 min | **Hygiene and follow-up.** Update stages, log notes, schedule next touches, re-verify names before next week's outreach. |
| **Fri** | 30 min | **Content.** One piece of genuine market commentary — see below. |

## Monthly

- **One hosted event or co-hosted seminar** (rotating format — see `04`).
- **Board and committee time** — one nonprofit board meeting or committee session.
- **Pipeline review** with your team lead: stage volumes, conversion rates, and
  every stalled Stage 3 relationship diagnosed individually.
- **List refresh** — re-run `build_lead_list.py` with new triggers; retire dead
  rows, promote new ones. The list is a living instrument, not a document.

## Quarterly

- **Segment campaign.** Pick one segment and run a themed campaign end to end
  (e.g. Q1: concentrated-stock holders ahead of the spring vest cycle).
- **Conversion audit.** Where are households dying? By segment, by source, by
  introducer. Kill what doesn't convert.
- **COI scorecard.** Rank every centre of influence by introductions *delivered*,
  not meetings taken. Fire the bottom third of your COI time.
- **Re-score the full list.** Triggers age. A hot Q1 lead is a cold Q3 lead.

---

## The COI engine — the highest-leverage part of the whole plan

For a $10M+ household, cold outreach converts in the low single digits. A referral
from the household's own CPA or attorney converts **10-20x better**. Your primary
job is not prospecting households; it is **building a referral network that
prospects for you.**

**Target: 25 active COIs, each producing 2+ qualified introductions per year.**
That alone is 50 qualified introductions — five times the volume you need.

| COI type | Why they matter | What you give them |
|---|---|---|
| **M&A / transaction attorneys** | See the liquidity event 6-12 months early | Pre-transaction planning for their client; deal-financing certainty |
| **CPAs (esp. Spanish-speaking, Santa Ana / Anaheim)** | Know owner financials precisely; deeply trusted | Tax-aware portfolio construction; entity and QSBS planning |
| **Estate planning attorneys** | Control the generational transfer | Trust and custody execution; valuation support |
| **1031 qualified intermediaries** | See the exchange clock start | Bridge liquidity; parking-period cash management |
| **CRE brokers (multifamily, industrial)** | Know every OC portfolio owner | Financing certainty for their buyers |
| **Business brokers / lower-middle-market bankers** | The $5-50M revenue business sale pipeline | Buyer financing; seller post-close planning |
| **Insurance and benefits specialists** | Own the buy-sell and key-person conversation | Premium financing; policy review |
| **Commercial bankers inside JPM** | Already bank the operating company | The personal-side relationship they cannot serve |

That last row deserves emphasis in the interview: **the highest-yield referral
source for a J.P. Morgan Private Bank banker is J.P. Morgan itself.** Chase
Business Banking and Commercial Banking already bank hundreds of OC companies
whose owners have no Private Bank relationship. Ask directly about the internal
referral protocol and how partner credit is allocated — it shows you understand
that the firm's own balance sheet is your best lead source.

---

## Tooling

The plan deliberately assumes **firm-provided tools plus free public sources**.
Nothing here requires an unapproved outside purchase.

| Function | Tool |
|---|---|
| CRM / pipeline | Firm-provided (system of record — all notes live here) |
| Securities disclosure | SEC EDGAR (free) |
| Property records | OC Assessor + OC Clerk-Recorder (free) |
| Business entities | CA SoS bizfile, CSLB, ABC (free) |
| Philanthropy | IRS 990-PF via ProPublica Nonprofit Explorer (free) |
| Wealth screening | Firm-provided |
| News and triggers | Orange County Business Journal subscription; Google Alerts on the 20 issuers and top 45 private companies |
| List scoring | `build_lead_list.py` in this repo |

**One discipline above all:** the firm's CRM is the system of record. A private
spreadsheet of client information is a supervisory problem and it will not survive
a review. The scoring model here is a *targeting* tool; confirmed household
information belongs in the firm's system.

---

## The metrics that matter

Track weekly. Lagging indicators tell you about last year; lead indicators tell
you about next quarter.

**Leading (manage these):**
- New qualified households resolved per week — target 5
- First meetings booked per week — target 2
- COI introductions requested vs. delivered
- Stage 3 (Engaged) standing volume — target 50

**Lagging (report these):**
- New relationships won
- New assets under supervision
- Revenue and lending balances
- Average relationship size — if it falls below $8M you are fishing too shallow
