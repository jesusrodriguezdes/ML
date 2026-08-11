# 02 — The Identification Process

## The core problem

**No lawful data source publishes a list of households by net worth.** Anyone who
claims to sell you one is selling modelled estimates, scraped data, or both. If
you say "I'll buy a list of the 75,000" in the interview, you will sound naive.

The correct answer is that wealth is not *found*, it is **inferred from public
signals and then confirmed through a relationship**. Every serious private banking
prospecting operation works the same way:

```
ANCHOR  →  INFER  →  RESOLVE  →  QUALIFY  →  ENGAGE
```

1. **ANCHOR** — tie a prospective household to a real, verifiable entity: a public
   company, an operating business, a property portfolio, a foundation.
2. **INFER** — assign an estimated wealth tier from the strength of the public
   signal. Always labelled as an inference, never asserted as fact.
3. **RESOLVE** — convert the anchor into a named household using a specific public
   source.
4. **QUALIFY** — confirm through conversation. This is the only step that produces
   truth.
5. **ENGAGE** — run the relationship play appropriate to the segment.

A compliance note that matters: as a J.P. Morgan employee, your prospect records,
outreach materials, and any external data you import are subject to supervisory
review. This process is deliberately built on **public-record and firm-provided
sources only** — nothing scraped, nothing purchased from a grey-market vendor,
nothing that would fail a compliance review. Say that out loud in the interview.

---

## The five signal layers

Wealth in Orange County shows up in five public forms. Each has a different
source, a different confidence level, and a different natural trigger event.

### Layer 1 — Securities disclosure (highest confidence, fastest)

Officers and directors of public companies file their holdings publicly. This is
the only layer where wealth is close to *directly observable*.

| Source | What it gives you | Where |
|---|---|---|
| **DEF 14A** (proxy) | Named executives, total compensation, beneficial ownership | SEC EDGAR |
| **Forms 3 / 4 / 5** | Every insider transaction, dated | SEC EDGAR |
| **Form 144** | Notice of intent to sell restricted stock — a *pre-liquidity* signal | SEC EDGAR |
| **SC 13D / 13G** | Holders above 5% | SEC EDGAR |
| **8-K / S-4** | Merger agreements — the earliest legal warning of a cash event | SEC EDGAR |

**Method:** build a standing list of Orange County-headquartered issuers, pull
each one's CIK, and monitor Forms 4 and 144 weekly. A Form 144 filed by an officer
of an Irvine issuer is a household about to convert restricted stock into cash on
a known date.

**Twenty OC-headquartered issuers to anchor on** (see the lead list for the
household-level breakdown): Edwards Lifesciences, Masimo, Skyworks Solutions,
Rivian, Ingram Micro, First American Financial, Chipotle, Glaukos, ICU Medical,
Pacific Premier Bancorp, Alignment Healthcare, El Pollo Loco, Tilly's, TTM
Technologies, Ducommun, CorVel, Sunstone Hotel Investors, Landsea Homes, STAAR
Surgical, BJ's Restaurants.

### Layer 2 — Real property records (highest coverage in OC)

Orange County's wealth is disproportionately real-estate-shaped, and property
records are fully public.

| Source | What it gives you |
|---|---|
| **OC Assessor parcel roll** | Owner of record, assessed value, exemptions |
| **OC Clerk-Recorder** | Grant deeds, deeds of trust, reconveyances, transfer dates |
| **City permit / entitlement records** | Active developers and repeat sponsors |

**The four highest-value queries:**

1. **Repeat ownership** — the same name or LLC across 5+ parcels. A portfolio
   owner, not a homeowner. Strongest single signal in the county.
2. **High value, no open deed of trust** — an $8M Newport waterfront property with
   no recorded mortgage implies substantial liquid reserves sitting idle. A direct
   securities-based-lending and liquidity conversation.
3. **Recent sale + qualified intermediary** — a 1031 exchange in flight. The
   45-day identification and 180-day closing clock is the sharpest dated trigger
   available anywhere in this process.
4. **Low basis, long tenure** — pre-1990 acquisition dates under Prop 13 signal
   enormous unrealised gain and an unavoidable estate-planning conversation.

### Layer 3 — Business ownership records

| Source | What it gives you |
|---|---|
| **CA Secretary of State (bizfile)** | Entity, registered agent, officers, formation date |
| **CSLB** | Contractor licenses, class, bond amount, tenure — excellent for OC's large Latino-owned construction base |
| **CA ABC** | Liquor licenses — restaurant and hospitality ownership |
| **DBO / NMLS** | Lenders, mortgage and finance companies |
| **County fictitious business name filings** | DBAs and their true owners |
| **UCC-1 filings** | Equipment and working-capital lenders — reveals company scale and existing banking relationships |

**Method:** entity age (15+ years) × employee count × industry margin is a
reliable proxy for owner net worth. A Santa Ana Class B contractor licensed since
1998 with a $1M bond and 80 employees is, with high probability, a $10M+ household.

### Layer 4 — Philanthropic disclosure (best proxy for realised wealth)

**A private foundation is almost never created by a household worth less than
$5M.** The 990-PF is public, names trustees, and states assets.

Newport Beach alone hosts approximately **265 private foundations holding roughly
$7.6 billion** in assets. That single fact identifies several hundred qualifying
households with near-certainty — and it is free.

| Source | What it gives you |
|---|---|
| **IRS Form 990-PF** | Foundation assets, grants, **named trustees** |
| **990** (public charities) | Board rosters — OC nonprofit boards are dense with wealth |
| **Donor walls / gala programs** | Named-gift donors at Hoag, Segerstrom Center, Chapman, OC Community Foundation, CHOC |

Nonprofit board service is the highest-yield warm-introduction surface in the
entire process. It is also the only layer where the households have already
self-identified as willing to be approached.

### Layer 5 — Event and transaction intelligence (highest conversion)

| Signal | Why it matters |
|---|---|
| M&A announcements involving OC companies | Cash settlement on a known date |
| IPO / de-SPAC / take-private of an OC issuer | Lockups and rollover equity |
| Employee tender offers at private companies | Creates first-time liquid millionaires in cohorts |
| ESOP formation or share repurchase | Employee-owners receive diversification elections |
| Litigation settlements, verdicts | Sudden concentrated liquidity |
| Obituaries and probate filings | Estate settlement and inherited assets in motion |

**This layer converts several times better than any other**, because the household
faces a dated decision it cannot avoid making.

---

## The scoring model

Implemented in [`build_lead_list.py`](build_lead_list.py). Each household scores
0-100 across five weighted dimensions:

| Dimension | Weight | What it measures |
|---|---:|---|
| **Wealth tier** | 35 | Strength of the public signal (T1 $5-10M → T4 $100M+) |
| **Trigger proximity** | 25 | How close a liquidity or life event is |
| **Access quality** | 20 | Whether a realistic warm path exists |
| **Whitespace** | 10 | Likelihood the household is *not* already well banked |
| **Affinity fit** | 10 | Fit with your Spanish-language and portfolio-management edge |

Trigger proximity is weighted second-heaviest deliberately. A $50M household with
no event is a three-year cultivation; a $12M household 60 days from a closing is a
this-quarter opportunity. **Bankers who sort by wealth alone starve.**

Output bands:

| Band | Score | Action |
|---|---|---|
| **P1 — Work now** | 80+ | Immediate, named outreach plan |
| **P2 — Work this quarter** | 65-79 | Sequenced into the quarterly campaign |
| **P3 — Nurture** | 50-64 | Content and event track |
| **P4 — Monitor** | <50 | Watchlist, trigger-driven only |

## Data integrity rules

These rules are what make the process survive both a compliance review and an
interview cross-examination:

1. **Never assert a net worth.** Record the *signal* and an explicitly inferred
   tier. Every tier field in the output carries the `_INFERRED` suffix.
2. **Every row carries its verification source.** A row without a resolution path
   is a rumour, not a lead.
3. **`NAMED-VERIFY` vs `ROLE-RESOLVE`.** Names sourced from public reporting must
   be re-confirmed in the firm's system of record before any contact. Roles must
   be resolved to a person via the cited source. Nothing is contacted on the basis
   of this file alone.
4. **Public and firm-provided sources only.** No scraped data, no grey-market
   vendors, no personal-network data imported without approval.
5. **Business information only.** Company, role, entity, public filing. No home
   addresses, personal phone numbers, family details, or health information in the
   prospect record.
6. **Re-verify before every touch.** Executive rosters change constantly. A stale
   title in a first email destroys credibility permanently.
