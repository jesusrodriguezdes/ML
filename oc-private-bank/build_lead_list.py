#!/usr/bin/env python3
"""
Orange County $5M+ Household Identification Engine
==================================================

Builds a scored, 200-row prospect list for a J.P. Morgan Private Bank banker
covering Orange County, CA.

DESIGN PRINCIPLE — NO FABRICATED WEALTH DATA
--------------------------------------------
No lawful data source publishes "households with $5M+ net worth." This model
therefore never asserts a net worth. It does three things instead:

  1. ANCHOR    Tie each prospective household to a real, verifiable entity
               (a public company, an operating business, a property portfolio,
               a 990-PF filer).
  2. INFER     Assign an estimated wealth TIER from the strength of public
               signals, explicitly labelled as an inference.
  3. RESOLVE   Carry the exact public source that converts the anchor into a
               named, confirmed household before any outreach occurs.

Every row is therefore a research task with a known answer path, not a claim.
Names carried here are drawn from public business reporting and MUST be
re-verified in the firm's system of record before use. `name_status` says which
rows are a name-to-confirm vs. a role-to-resolve.

SCORING (0-100)
---------------
    tier         35   strength of the wealth signal
    trigger      25   proximity of a liquidity / life event
    access       20   quality of the realistic path in
    whitespace   10   likelihood the household is NOT already banked
    affinity     10   fit with this banker's edge (Spanish-language, PM craft)

Usage:  python3 build_lead_list.py
Output: leads_orange_county_200.csv
"""

import csv
from collections import Counter

OUT = "leads_orange_county_200.csv"

# Estimated wealth tiers. INFERRED — never asserted as fact.
TIER_PTS = {"T1": 15, "T2": 22, "T3": 30, "T4": 35}
TIER_LABEL = {
    "T1": "T1 ($5-10M est.)",
    "T2": "T2 ($10-25M est.)",
    "T3": "T3 ($25-100M est.)",
    "T4": "T4 ($100M+ est.)",
}

# Default verification source + entry path per segment.
SEG_META = {
    "A": ("SEC EDGAR: DEF 14A + Forms 3/4/144 (CIK by ticker)",
          "Equity-comp seminar via company HR/benefits; 10b5-1 planning hook"),
    "B": ("CA SoS bizfile entity search + CSLB/ABC/DBO license records",
          "M&A attorney / CPA / commercial banker COI referral"),
    "C": ("OC Assessor parcel roll + OC Clerk-Recorder grant deeds",
          "1031 intermediary, CRE broker, and construction-lender COIs"),
    "D": ("CA license boards (Medical, Dental, State Bar) + practice filings",
          "Practice-sale advisor, malpractice carrier, and CPA COIs"),
    "E": ("IRS 990-PF filings (ProPublica Nonprofit Explorer) + trustee lists",
          "Nonprofit board service and co-trustee/estate-attorney COIs"),
    "F": ("Deal press release + SEC 8-K/S-4; SC 13D/G and Form 144 follow-on",
          "Pre-close outreach through deal counsel and investment bankers"),
}

SEGMENT_NAME = {
    "A": "A - Concentrated public-company equity",
    "B": "B - Private business owner, pre-liquidity",
    "C": "C - Real estate owner / operator",
    "D": "D - Professional practice equity",
    "E": "E - Inherited / multi-generational + foundation",
    "F": "F - Recent or imminent liquidity event",
}

rows = []


def add(seg, anchor, city, target, status, tier, signal, trigger,
        trig=2, acc=3, white=3, es=0, verify=None, path=None):
    """Append one prospective household record."""
    rows.append({
        "segment": seg, "anchor": anchor, "city": city, "target": target,
        "status": status, "tier": tier, "signal": signal, "trigger": trigger,
        "trig": trig, "acc": acc, "white": white, "es": es,
        "verify": verify or SEG_META[seg][0],
        "path": path or SEG_META[seg][1],
    })


# =============================================================================
# SEGMENT A — Concentrated public-company equity  (60 households)
# 20 Orange County-headquartered public issuers x 3 insider households each.
# These are the *fastest* households to identify: Section 16 officers and
# directors file publicly, and Form 144 / 10b5-1 activity is a live trigger.
# =============================================================================

# (company, ticker, city, [(target, status, tier, signal, trigger, trig, acc, white, es)])
PUBLIC = [
    ("Edwards Lifesciences", "EW", "Irvine", [
        ("Chief Executive Officer (Bernard Zovighian)", "NAMED-VERIFY", "T4",
         "Section 16 officer; multi-year PSU/RSU vesting in a $40B+ cap issuer",
         "Annual Feb/Mar vest cliff; 10b5-1 renewal window", 4, 2, 2, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T3",
         "Named executive officer; disclosed equity holdings in DEF 14A",
         "Post-earnings trading window opens", 3, 2, 2, 0),
        ("Chairman / long-tenured director (Michael Mussallem)", "NAMED-VERIFY", "T4",
         "Founder-era equity accumulated across 20+ yrs as CEO",
         "Retirement-stage diversification and estate planning", 4, 3, 3, 0),
    ]),
    ("Masimo", "MASI", "Irvine", [
        ("Founder / former CEO (Joe Kiani)", "NAMED-VERIFY", "T4",
         "Founder stake in a multi-billion-dollar issuer",
         "Separation from company created a concentrated, unhedged position", 5, 3, 4, 0),
        ("Chief Executive Officer", "ROLE-RESOLVE", "T3",
         "Section 16 officer; new-hire equity grant on file", "Sign-on grant vesting schedule", 3, 2, 3, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T2",
         "Named executive officer equity in DEF 14A", "Annual vest", 3, 2, 3, 0),
    ]),
    ("Skyworks Solutions", "SWKS", "Irvine", [
        ("Chief Executive Officer", "ROLE-RESOLVE", "T3",
         "Section 16 officer of a large-cap semiconductor issuer", "Annual PSU determination", 3, 2, 2, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T3",
         "Named executive officer; recurring Form 4 sales", "Rule 10b5-1 plan adoption", 4, 2, 2, 0),
        ("Former CEO / retired senior officer", "ROLE-RESOLVE", "T3",
         "Retired insider with retained, concentrated holdings",
         "Post-separation diversification need", 4, 3, 4, 0),
    ]),
    ("Rivian Automotive", "RIVN", "Irvine", [
        ("Founder & CEO (RJ Scaringe)", "NAMED-VERIFY", "T4",
         "Founder equity position in a public EV manufacturer",
         "Long-dated founder award milestones", 3, 1, 1, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T3",
         "Section 16 officer with disclosed RSU schedule", "Quarterly vest and sell-to-cover", 4, 2, 2, 0),
        ("SVP/VP cohort below Section 16 (pre-IPO RSU holders)", "ROLE-RESOLVE", "T2",
         "Pre-IPO equity holders outside proxy disclosure",
         "Multi-year RSU cliffs; heavy single-stock concentration", 4, 3, 5, 0),
    ]),
    ("Ingram Micro Holding", "INGM", "Irvine", [
        ("Chief Executive Officer (Paul Bay)", "NAMED-VERIFY", "T3",
         "Section 16 officer following 2024 re-listing", "Post-IPO lockup expiry and first vests", 5, 2, 3, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T3",
         "Named executive officer; management rollover equity", "Lockup expiry", 5, 2, 3, 0),
        ("Management rollover equity cohort (EVP/SVP)", "ROLE-RESOLVE", "T2",
         "Sponsor-era rollover units converted at re-IPO",
         "First liquid window since 2021 take-private", 5, 3, 4, 0),
    ]),
    ("First American Financial", "FAF", "Santa Ana", [
        ("Chief Executive Officer (Kenneth DeGiorgio)", "NAMED-VERIFY", "T3",
         "Section 16 officer of an S&P 500 title insurer", "Annual equity vest", 3, 2, 2, 0),
        ("Chairman / Kennedy family principal (Parker Kennedy)", "NAMED-VERIFY", "T4",
         "Third-generation family holding in a 130-yr-old OC institution",
         "Multi-generational transfer planning", 4, 3, 3, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T2",
         "Named executive officer equity", "Trading window", 3, 2, 3, 0),
    ]),
    ("Chipotle Mexican Grill", "CMG", "Newport Beach", [
        ("Chief Executive Officer", "ROLE-RESOLVE", "T3",
         "Section 16 officer of a large-cap restaurant issuer", "Annual PSU payout", 3, 2, 2, 1),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T3",
         "Named executive officer; regular Form 4 activity", "10b5-1 renewal", 4, 2, 2, 1),
        ("Officer cohort relocated to Newport Beach HQ", "ROLE-RESOLVE", "T2",
         "Senior corporate officers domiciled in OC post-HQ move",
         "Relocation-driven home purchase and advisor change", 4, 3, 4, 1),
    ]),
    ("Glaukos", "GKOS", "Aliso Viejo", [
        ("Founder / CEO (Thomas Burns)", "NAMED-VERIFY", "T3",
         "Founder-era equity in a commercial-stage ophthalmic device issuer",
         "Long-tenure concentration; succession horizon", 4, 3, 3, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T2",
         "Named executive officer equity", "Annual vest", 3, 2, 3, 0),
        ("Chief Medical / Chief Commercial Officer", "ROLE-RESOLVE", "T2",
         "Section 16 officer with option overhang", "Option expiry pressure", 4, 3, 4, 0),
    ]),
    ("ICU Medical", "ICUI", "San Clemente", [
        ("Founder (Dr. George Lopez)", "NAMED-VERIFY", "T4",
         "Physician-founder equity stake built since company's 1984 founding",
         "Post-CEO diversification; legacy and philanthropic planning", 4, 4, 3, 1),
        ("Chief Executive Officer", "ROLE-RESOLVE", "T3",
         "Section 16 officer of a mid-cap medical device issuer", "Annual vest", 3, 2, 3, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T2",
         "Named executive officer equity", "Trading window", 3, 2, 3, 0),
    ]),
    ("Pacific Premier Bancorp", "PPBI", "Irvine", [
        ("Chief Executive Officer (Steven Gardner)", "NAMED-VERIFY", "T3",
         "Long-tenured bank CEO with accumulated restricted stock",
         "Bank M&A consolidation cycle", 5, 3, 3, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T2",
         "Named executive officer equity", "Change-in-control vesting", 5, 3, 3, 0),
        ("Independent director cohort", "ROLE-RESOLVE", "T3",
         "Bank directors are typically OC business owners themselves",
         "Director stock ownership guidelines; dual identity as owners", 3, 4, 4, 0),
    ]),
    ("Alignment Healthcare", "ALHC", "Orange", [
        ("Founder / CEO (John Kao)", "NAMED-VERIFY", "T3",
         "Founder equity in a public Medicare Advantage insurer", "Founder concentration", 3, 2, 3, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T2",
         "Named executive officer equity", "Annual vest", 3, 2, 3, 0),
        ("President / COO", "ROLE-RESOLVE", "T2",
         "Section 16 officer equity", "Trading window", 3, 2, 3, 0),
    ]),
    ("El Pollo Loco Holdings", "LOCO", "Costa Mesa", [
        ("Chief Executive Officer", "ROLE-RESOLVE", "T2",
         "Section 16 officer of a public restaurant issuer", "Annual vest", 3, 3, 4, 1),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T2",
         "Named executive officer equity", "Trading window", 3, 3, 4, 1),
        ("Large multi-unit franchisee owner cohort", "ROLE-RESOLVE", "T2",
         "Franchisee groups owning 10+ units; heavily Latino-owned in SoCal",
         "Franchise-agreement renewal and refranchising", 4, 4, 5, 1),
    ]),
    ("Tilly's", "TLYS", "Irvine", [
        ("Co-founder / Executive Chairman (Hezy Shaked)", "NAMED-VERIFY", "T4",
         "Controlling founder stake plus separate OC real estate holdings",
         "Founder succession; retail cycle pressure", 4, 3, 3, 0),
        ("Chief Executive Officer", "ROLE-RESOLVE", "T1",
         "Section 16 officer equity", "Annual vest", 3, 3, 4, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T1",
         "Named executive officer equity", "Trading window", 3, 3, 4, 0),
    ]),
    ("TTM Technologies", "TTMI", "Santa Ana", [
        ("Chief Executive Officer (Tom Edman)", "NAMED-VERIFY", "T3",
         "Long-tenured CEO of a defense/aerospace PCB manufacturer",
         "Defense-cycle share appreciation; concentration", 4, 2, 3, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T2",
         "Named executive officer equity", "Annual vest", 3, 2, 3, 0),
        ("EVP Operations / division president", "ROLE-RESOLVE", "T2",
         "Section 16 officer equity", "Trading window", 3, 3, 4, 0),
    ]),
    ("Ducommun", "DCO", "Santa Ana", [
        ("Chief Executive Officer", "ROLE-RESOLVE", "T2",
         "Section 16 officer of a century-old aerospace supplier", "Annual vest", 3, 3, 4, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T2",
         "Named executive officer equity", "Trading window", 3, 3, 4, 0),
        ("Independent director cohort", "ROLE-RESOLVE", "T2",
         "Directors typically hold senior roles at other OC firms",
         "Cross-board network effect", 2, 4, 4, 0),
    ]),
    ("CorVel Corporation", "CRVL", "Irvine", [
        ("Founder / Chairman (V. Gordon Clemons)", "NAMED-VERIFY", "T4",
         "Founder stake held since 1987 in a strongly appreciated issuer",
         "Advanced-age estate and legacy planning", 5, 3, 3, 0),
        ("Chief Executive Officer", "ROLE-RESOLVE", "T3",
         "Section 16 officer equity", "Annual vest", 3, 2, 3, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T2",
         "Named executive officer equity", "Trading window", 3, 2, 3, 0),
    ]),
    ("Sunstone Hotel Investors", "SHO", "Aliso Viejo", [
        ("Chief Executive Officer", "ROLE-RESOLVE", "T2",
         "Section 16 officer of a lodging REIT", "Annual LTIP vest", 3, 3, 4, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T2",
         "Named executive officer equity", "Trading window", 3, 3, 4, 0),
        ("Chief Investment Officer", "ROLE-RESOLVE", "T2",
         "Section 16 officer; deal-driven carry economics", "Asset-sale incentive payouts", 4, 3, 4, 0),
    ]),
    ("Landsea Homes", "LSEA", "Newport Beach", [
        ("Chief Executive Officer", "ROLE-RESOLVE", "T2",
         "Section 16 officer of a public homebuilder", "Annual vest", 3, 3, 4, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T2",
         "Named executive officer equity", "Trading window", 3, 3, 4, 0),
        ("Regional division president cohort", "ROLE-RESOLVE", "T1",
         "Division leaders on project-profit incentive plans", "Annual bonus/profit-share settlement", 3, 3, 4, 0),
    ]),
    ("STAAR Surgical", "STAA", "Lake Forest", [
        ("Chief Executive Officer", "ROLE-RESOLVE", "T2",
         "Section 16 officer of an ophthalmic implant issuer", "Annual vest", 3, 3, 4, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T2",
         "Named executive officer equity", "Trading window", 3, 3, 4, 0),
        ("Director cohort", "ROLE-RESOLVE", "T2",
         "Board members with medtech operating wealth", "Cross-board network", 2, 4, 4, 0),
    ]),
    ("BJ's Restaurants", "BJRI", "Huntington Beach", [
        ("Chief Executive Officer", "ROLE-RESOLVE", "T2",
         "Section 16 officer of a public casual-dining issuer", "Annual vest", 3, 3, 4, 0),
        ("Chief Financial Officer", "ROLE-RESOLVE", "T1",
         "Named executive officer equity", "Trading window", 3, 3, 4, 0),
        ("Founder-era shareholder / long-tenured director", "ROLE-RESOLVE", "T2",
         "Legacy holders from the company's OC founding", "Estate-stage diversification", 4, 3, 4, 0),
    ]),
]

for company, ticker, city, people in PUBLIC:
    for (target, status, tier, signal, trigger, trig, acc, white, es) in people:
        add("A", f"{company} ({ticker})", city, target, status, tier, signal, trigger,
            trig=trig, acc=acc, white=white, es=es,
            verify=f"SEC EDGAR full-text search: {ticker} DEF 14A + Forms 3/4/144")


# =============================================================================
# SEGMENT B — Private business owners, pre-liquidity  (45 households)
# The highest-value, longest-cycle segment. Wealth is illiquid and trapped in
# the operating company, which is exactly where a Private Bank team wins:
# credit, pre-transaction planning, and post-sale asset management.
# =============================================================================

B = [
    ("Applied Medical Resources", "Rancho Santa Margarita", "Founder / CEO (Said Hilal)", "NAMED-VERIFY", "T4",
     "Founder of a large private surgical-device manufacturer; ~4,000 OC employees",
     "Perennial IPO/strategic-sale speculation; succession horizon", 4, 3, 4, 0),
    ("Anduril Industries", "Costa Mesa", "Co-founder (Palmer Luckey)", "NAMED-VERIFY", "T4",
     "Founder stake in one of the most valuable private US defense companies",
     "Serial secondary tenders at rising valuations", 5, 1, 1, 0),
    ("Anduril Industries", "Costa Mesa", "Co-founder / CEO (Brian Schimpf)", "NAMED-VERIFY", "T4",
     "Co-founder equity in a decacorn-scale private issuer", "Secondary tender participation", 5, 1, 2, 0),
    ("Anduril Industries", "Costa Mesa", "Early employee equity cohort (first ~200 hires)", "ROLE-RESOLVE", "T3",
     "Pre-Series-C option holders realising cash in employee tenders",
     "Each tender creates a wave of first-time liquid millionaires", 5, 3, 5, 0),
    ("Glidewell Dental", "Irvine / Newport Beach", "Founder (Jim Glidewell)", "NAMED-VERIFY", "T4",
     "Sole owner of the largest private dental laboratory in the US",
     "Founder in succession window; no institutional sponsor", 4, 3, 4, 0),
    ("Pacific Dental Services", "Irvine", "Founder / CEO (Stephen Thorne IV)", "NAMED-VERIFY", "T4",
     "Founder of a 1,000+ location dental support organization",
     "DSO consolidation and recapitalisation cycle", 4, 3, 3, 0),
    ("Smile Brands", "Irvine", "CEO and equity management team", "ROLE-RESOLVE", "T2",
     "Sponsor-backed DSO management with rollover equity", "Sponsor exit horizon", 4, 3, 4, 0),
    ("Northgate González Market", "Anaheim", "González family principals (2nd generation)", "NAMED-VERIFY", "T4",
     "Family owners of a ~40-store Hispanic grocery chain founded 1980",
     "Multi-generational transfer across a large sibling group", 4, 5, 5, 1),
    ("Northgate González Market", "Anaheim", "González family principals (3rd generation / operating roles)", "ROLE-RESOLVE", "T3",
     "Next-generation family members entering ownership",
     "Generational wealth transfer and individual liquidity needs", 4, 5, 5, 1),
    ("Ganahl Lumber", "Anaheim", "Ganahl family owners (5th generation)", "NAMED-VERIFY", "T3",
     "California's oldest lumber company, family-held since 1884",
     "Fifth-generation succession; large owned industrial real estate", 4, 4, 5, 0),
    ("Extron Electronics", "Anaheim", "Founder (Andrew Edwards)", "NAMED-VERIFY", "T4",
     "Founder-owner of a large private AV-technology manufacturer",
     "No outside capital; founder succession", 4, 3, 5, 0),
    ("Galardi Group (Wienerschnitzel)", "Irvine", "Galardi family owners", "NAMED-VERIFY", "T3",
     "Second-generation family ownership of a national franchisor",
     "Franchisor family estate planning", 3, 4, 5, 0),
    ("In-N-Out Burger", "Irvine", "Owner (Lynsi Snyder) and family trust", "NAMED-VERIFY", "T4",
     "Sole heir/owner of a large private restaurant chain",
     "Trust administration and multi-state expansion", 3, 2, 2, 0),
    ("Javier's Restaurants", "Newport Beach", "Founder (Javier Sosa)", "NAMED-VERIFY", "T3",
     "Founder-owner of a high-volume restaurant group plus OC real estate",
     "Expansion financing; owner-operator concentration", 4, 5, 5, 1),
    ("Wahoo's Fish Taco", "Santa Ana", "Co-founder (Wing Lam) and family", "NAMED-VERIFY", "T2",
     "Founder-owners of a multi-unit regional restaurant brand",
     "Franchise system restructuring", 3, 4, 5, 1),
    ("Kingston Technology", "Fountain Valley", "Co-founder (David Sun)", "NAMED-VERIFY", "T4",
     "Co-owner of the largest private memory-module manufacturer",
     "Long-horizon family and philanthropic structuring", 3, 2, 2, 0),
    ("Kingston Technology", "Fountain Valley", "Co-founder (John Tu)", "NAMED-VERIFY", "T4",
     "Co-owner of a multi-billion-dollar private manufacturer",
     "Established large-scale philanthropy", 3, 2, 2, 0),
    ("Trace3", "Irvine", "Founding principals and management equity", "ROLE-RESOLVE", "T3",
     "Multi-billion-revenue private IT integrator with sponsor backing",
     "Sponsor exit / recapitalisation window", 5, 3, 4, 0),
    ("Allied Universal", "Irvine", "CEO and senior management equity holders", "ROLE-RESOLVE", "T4",
     "Management equity in the world's largest private security firm",
     "Sponsor liquidity event speculation", 4, 2, 3, 0),
    ("Pacific Life Insurance", "Newport Beach", "Senior executive / SVP cohort", "ROLE-RESOLVE", "T2",
     "Executives of a top-tier mutual insurer with large deferred comp",
     "Deferred-compensation election and distribution windows", 4, 3, 4, 0),
    ("PIMCO", "Newport Beach", "Managing Director cohort", "ROLE-RESOLVE", "T4",
     "MDs at one of the world's largest bond managers; profit-sharing units",
     "Annual comp cycle; deferred-award vesting", 4, 3, 2, 0),
    ("PIMCO", "Newport Beach", "Retired / former partner cohort resident in OC", "ROLE-RESOLVE", "T4",
     "Former MDs with realised deferred awards, still OC-domiciled",
     "Post-separation deferred payouts over 3-5 yrs", 5, 3, 3, 0),
    ("Research Affiliates", "Newport Beach", "Founder (Rob Arnott)", "NAMED-VERIFY", "T4",
     "Founder of a large quantitative index/strategy licensor",
     "Firm ownership restructuring", 3, 3, 3, 0),
    ("ROTH Capital Partners", "Newport Beach", "Co-founder (Byron Roth) and partner group", "NAMED-VERIFY", "T3",
     "Owner-partners of an OC-based investment bank",
     "Deal-cycle carry; partner distributions", 3, 4, 4, 0),
    ("Toba Capital / Quest Software legacy", "Aliso Viejo", "Founder (Vinny Smith)", "NAMED-VERIFY", "T4",
     "Proceeds from the Quest Software sale, redeployed via a family investment firm",
     "Ongoing venture portfolio realisations", 4, 3, 3, 0),
    ("Alteryx (legacy founder equity)", "Irvine", "Co-founder (Dean Stoecker)", "NAMED-VERIFY", "T4",
     "Founder proceeds from the 2024 take-private of Alteryx",
     "Fully liquid post-transaction; redeployment decision", 5, 3, 3, 0),
    ("Acorns", "Irvine", "CEO and founding equity holders", "ROLE-RESOLVE", "T2",
     "Late-stage private fintech equity", "Secondary sales and eventual exit", 4, 3, 4, 0),
    ("Sunwest Bank", "Irvine", "Kirchner family owners", "NAMED-VERIFY", "T3",
     "Family-controlled commercial bank holding company",
     "Bank consolidation cycle", 4, 4, 4, 0),
    ("Commercial Bank of California", "Irvine", "Founding investors and directors", "ROLE-RESOLVE", "T2",
     "Bank organisers are typically OC business owners themselves",
     "Capital raise / consolidation", 4, 4, 4, 1),
    ("CR&R Environmental Services", "Stanton", "Arakelian family owners", "NAMED-VERIFY", "T3",
     "Family-owned regional waste hauler with municipal franchise contracts",
     "Waste-sector roll-up pressure from strategics", 5, 4, 5, 0),
    ("Sukut Construction", "Santa Ana", "Sukut family / ESOP principals", "NAMED-VERIFY", "T3",
     "Family-founded heavy civil contractor with large equipment base",
     "ESOP repurchase obligations; ownership transition", 4, 4, 5, 0),
    ("Snyder Langston", "Irvine", "Owner-principals", "ROLE-RESOLVE", "T2",
     "Privately held general contractor, OC-founded 1958",
     "Internal ownership transition", 3, 4, 5, 0),
    ("Bomel Construction", "Buena Park", "Owner-principals", "ROLE-RESOLVE", "T2",
     "Family-held concrete/structures contractor", "Succession planning", 3, 4, 5, 1),
    ("R.D. Olson Construction", "Irvine", "Founder (Bob Olson) and principals", "NAMED-VERIFY", "T3",
     "Founder-owned hospitality contractor plus affiliated development arm",
     "Development-cycle liquidity", 4, 4, 4, 0),
    ("Griffith Company", "Brea", "Employee-owner principals", "ROLE-RESOLVE", "T2",
     "100% employee-owned heavy civil contractor",
     "ESOP share repurchase and diversification elections", 5, 4, 5, 1),
    ("Tarsadia Investments", "Newport Beach", "Patel family principals", "NAMED-VERIFY", "T4",
     "Family investment office built from a large hotel portfolio",
     "Portfolio recycling into new asset classes", 4, 3, 3, 0),
    ("Fluidmaster", "San Juan Capistrano", "Family owners", "ROLE-RESOLVE", "T3",
     "Family-held global plumbing-components manufacturer",
     "Generational transition", 4, 4, 5, 0),
    ("Behr Paint (Masco)", "Santa Ana", "Division executive cohort", "ROLE-RESOLVE", "T1",
     "Senior division leadership of a large consumer-products unit",
     "Parent-company LTIP vesting", 3, 3, 4, 0),
    ("Kia America", "Irvine", "US executive cohort", "ROLE-RESOLVE", "T1",
     "US-market senior executives of a global automaker",
     "Expatriate and cross-border comp structures", 3, 3, 4, 1),
    ("Hyundai Motor America", "Fountain Valley", "US executive cohort", "ROLE-RESOLVE", "T1",
     "US-market senior executives; large deferred and relocation packages",
     "Cross-border tax and comp events", 3, 3, 4, 1),
    ("Mazda North American Operations", "Irvine", "US executive cohort", "ROLE-RESOLVE", "T1",
     "US-market senior executives of a global automaker", "Deferred comp cycle", 3, 3, 4, 1),
    ("Blizzard Entertainment (Microsoft)", "Irvine", "Veteran equity-holding staff", "ROLE-RESOLVE", "T1",
     "Long-tenured staff holding appreciated parent-company RSUs",
     "Post-acquisition RSU conversion and vesting", 4, 3, 5, 0),
    ("Taco Bell (Yum! Brands)", "Irvine", "Brand executive cohort", "ROLE-RESOLVE", "T1",
     "Senior brand executives with parent-company equity", "Annual PSU settlement", 3, 3, 4, 1),
    ("Del Taco multi-unit franchisee groups", "Orange County", "Multi-unit franchise owners", "ROLE-RESOLVE", "T2",
     "Franchisees owning 10+ QSR units; heavily Latino-owned in SoCal",
     "Post-acquisition refranchising and remodel-capex cycle", 4, 4, 5, 1),
    ("Chronic Tacos / regional franchisor groups", "Orange County", "Franchisor owners and area developers", "ROLE-RESOLVE", "T2",
     "Owners of OC-founded franchise systems", "System sale or area-developer buyouts", 3, 4, 5, 1),
]

for (anchor, city, target, status, tier, signal, trigger, trig, acc, white, es) in B:
    add("B", anchor, city, target, status, tier, signal, trigger,
        trig=trig, acc=acc, white=white, es=es)


# =============================================================================
# SEGMENT C — Real estate owners / operators  (35 households)
# The most OC-native wealth form. Property records make this segment uniquely
# verifiable: ownership, debt, and transfer dates are all public.
# =============================================================================

C = [
    ("Irvine Company", "Newport Beach", "Chairman / owner (Donald Bren)", "NAMED-VERIFY", "T4",
     "Sole owner of the largest private landholder in Orange County",
     "Perpetual estate and philanthropic structuring", 2, 1, 1, 0),
    ("Irvine Company", "Newport Beach", "Senior executive / division president cohort", "ROLE-RESOLVE", "T3",
     "Senior leadership with long-term incentive participation",
     "LTIP settlement cycles", 3, 3, 3, 0),
    ("C.J. Segerstrom & Sons", "Costa Mesa", "Segerstrom family principals", "NAMED-VERIFY", "T4",
     "Fourth/fifth-generation owners of South Coast Plaza and adjacent land",
     "Large sibling-group generational transfer", 3, 3, 2, 0),
    ("Arnel & Affiliates / Argyros family", "Costa Mesa", "Argyros family principals", "NAMED-VERIFY", "T4",
     "Family real estate and investment holdings built over 50+ years",
     "Second-generation control transition", 4, 3, 2, 0),
    ("Olen Properties", "Newport Beach", "Founder (Igor Olenicoff) and family", "NAMED-VERIFY", "T4",
     "Owner of a large multi-state office and apartment portfolio",
     "Founder-age succession; portfolio recycling", 4, 3, 3, 0),
    ("Lyon Living / Lyon family", "Newport Beach", "Lyon family principals", "NAMED-VERIFY", "T4",
     "Multi-generational homebuilding and apartment ownership",
     "Post-homebuilder-sale redeployment", 4, 3, 3, 0),
    ("J.F. Shea Co. / Shea Homes", "Aliso Viejo / Walnut", "Shea family principals", "NAMED-VERIFY", "T4",
     "Family ownership spanning construction, homebuilding, and venture capital since 1881",
     "Fifth-generation transfer across a very large family group", 3, 3, 2, 0),
    ("The New Home Company", "Irvine", "Executive principals", "ROLE-RESOLVE", "T2",
     "Sponsor-owned homebuilder management equity", "Sponsor exit horizon", 4, 3, 4, 0),
    ("Sares Regis Group of Southern California", "Irvine", "Managing principals", "ROLE-RESOLVE", "T3",
     "Principals of a large private multifamily developer/operator",
     "Fund-level promote crystallisation", 4, 4, 4, 0),
    ("Western National Group", "Irvine", "Owner-principals", "ROLE-RESOLVE", "T3",
     "Owners of a large OC-based apartment developer and manager",
     "Portfolio refinancing and asset sales", 4, 4, 4, 0),
    ("Steadfast Companies", "Irvine", "Founder and principals", "ROLE-RESOLVE", "T3",
     "Founder-led multifamily investment platform",
     "Post-merger liquidity from portfolio-level transactions", 5, 4, 4, 0),
    ("Passco Companies", "Irvine", "Founding principals", "ROLE-RESOLVE", "T3",
     "Sponsor of 1031/DST multifamily programs",
     "Program wind-downs generating sponsor promotes", 4, 4, 4, 0),
    ("IRA Capital", "Irvine", "Managing principals", "ROLE-RESOLVE", "T3",
     "Principals of a $3B+ healthcare and commercial real estate investor",
     "Fund realisations", 4, 4, 4, 0),
    ("Waterford Property Company", "Newport Beach", "Co-founders (Sean Rawson, John Drachman)", "NAMED-VERIFY", "T2",
     "Co-founders of an active workforce-housing investor",
     "Deal-level promote events", 4, 5, 5, 0),
    ("Greenlaw Partners", "Irvine", "Founder and principals", "ROLE-RESOLVE", "T3",
     "Founder-led opportunistic commercial investor",
     "Asset-level dispositions", 4, 4, 4, 0),
    ("CT Realty", "Newport Beach", "Founding partners", "ROLE-RESOLVE", "T3",
     "Partners in a national industrial development platform",
     "Industrial-cycle portfolio sales generating large promotes", 5, 4, 4, 0),
    ("Buchanan Street Partners", "Newport Beach", "President and partners", "ROLE-RESOLVE", "T3",
     "Principals of a real estate investment and debt platform",
     "Fund realisations", 4, 4, 4, 0),
    ("Bixby Land Company", "Irvine", "Bixby family shareholders", "NAMED-VERIFY", "T4",
     "Family shareholders of a 150-year-old OC land company",
     "Post-portfolio-recapitalisation shareholder liquidity", 5, 3, 3, 0),
    ("The Bascom Group", "Irvine", "Co-founders (Jerry Fink, David Kim)", "NAMED-VERIFY", "T3",
     "Co-founders of a very active multifamily acquirer",
     "Continuous disposition and promote cycle", 5, 4, 4, 0),
    ("Advanced Real Estate", "Irvine", "Founder and principals", "ROLE-RESOLVE", "T3",
     "Founder-led OC apartment investor and operator",
     "Refinancing and partial sales", 4, 4, 4, 0),
    ("LBA Realty", "Irvine", "Founding partners", "ROLE-RESOLVE", "T4",
     "Partners in a large institutional industrial/office investment manager",
     "Fund-level carried interest realisations", 4, 3, 3, 0),
    ("The Koll Company", "Newport Beach", "Koll family principals", "NAMED-VERIFY", "T4",
     "Family principals of a historic OC commercial development firm",
     "Generational transition", 4, 4, 4, 0),
    ("The Robert Mayer Corporation", "Newport Beach", "Mayer family principals", "NAMED-VERIFY", "T4",
     "Family owners of Huntington Beach coastal resort and land holdings",
     "Resort asset monetisation", 4, 4, 4, 0),
    ("SmartStop Self Storage", "Ladera Ranch", "Founder (H. Michael Schwartz) and principals", "NAMED-VERIFY", "T3",
     "Founder-led self-storage REIT platform",
     "Listing/liquidity event for the non-traded vehicle", 5, 4, 4, 0),
    ("MBK Real Estate", "Irvine", "Senior principals", "ROLE-RESOLVE", "T2",
     "Leadership of a diversified developer (homes, senior living, industrial)",
     "Incentive settlement", 3, 3, 4, 0),
    ("Red Oak Investments", "Newport Beach", "Principals", "ROLE-RESOLVE", "T2",
     "Private real estate investment principals", "Asset dispositions", 3, 4, 5, 0),
    ("Independent OC infill developers (10-100 unit projects)", "Orange County", "Owner-developers", "ROLE-RESOLVE", "T2",
     "Repeat sponsors identifiable from city entitlement and permit records",
     "Project completion and construction-loan takeout", 5, 4, 5, 1),
    ("Santa Ana multifamily portfolio owners (5+ parcels)", "Santa Ana", "Portfolio-owning households", "ROLE-RESOLVE", "T2",
     "Assessor roll shows repeat ownership across multiple apartment parcels",
     "Long-hold, low-basis assets facing refinancing decisions", 4, 4, 5, 1),
    ("Anaheim multifamily portfolio owners (5+ parcels)", "Anaheim", "Portfolio-owning households", "ROLE-RESOLVE", "T2",
     "Repeat ownership across multiple parcels on the assessor roll",
     "Rate-reset refinancing on maturing loans", 4, 4, 5, 1),
    ("Garden Grove / Westminster multifamily owners", "Garden Grove", "Portfolio-owning households", "ROLE-RESOLVE", "T2",
     "Immigrant-founded portfolios accumulated over 20-40 years",
     "Generational transfer of property portfolios", 4, 4, 5, 1),
    ("Huntington Beach coastal multi-property owners", "Huntington Beach", "Multi-property households", "ROLE-RESOLVE", "T2",
     "Multiple high-value coastal parcels under common ownership",
     "Estate planning on highly appreciated, low-basis property", 3, 4, 4, 0),
    ("Newport Beach waterfront owners, no recorded mortgage", "Newport Beach", "Debt-free waterfront households", "ROLE-RESOLVE", "T3",
     "$8M+ assessed value with no open deed of trust implies large liquid reserves",
     "Idle equity; securities-based lending and liquidity opportunity", 3, 3, 3, 0),
    ("OC industrial owner-users (50,000+ sf, owner-occupied)", "Orange County", "Owner-operator households", "ROLE-RESOLVE", "T3",
     "Business owner also owns the real estate through a separate LLC",
     "Sale-leaseback and business-sale planning", 4, 4, 5, 1),
    ("OC 1031 exchange sellers, trailing 12 months", "Orange County", "Exchanging households", "ROLE-RESOLVE", "T2",
     "Recorded sale plus qualified-intermediary involvement in public records",
     "45/180-day exchange clock — the single sharpest timing trigger available", 5, 5, 5, 1),
    ("OC mobile home park and self-storage owners", "Orange County", "Owner households", "ROLE-RESOLVE", "T2",
     "Niche asset classes with concentrated private ownership",
     "Aggregator buy-out offers", 4, 4, 5, 0),
]

for (anchor, city, target, status, tier, signal, trigger, trig, acc, white, es) in C:
    add("C", anchor, city, target, status, tier, signal, trigger,
        trig=trig, acc=acc, white=white, es=es)


# =============================================================================
# SEGMENT D — Professional practice equity  (25 households)
# Steady, high-income, chronically under-advised. Best entered through the
# practice-transition and buy-in event, not through a generic investment pitch.
# =============================================================================

D = [
    ("Rutan & Tucker LLP", "Irvine", "Equity partner cohort", "T3",
     "Equity partners at Orange County's largest homegrown law firm"),
    ("Knobbe Martens LLP", "Irvine", "Equity partner cohort", "T3",
     "Equity partners at a leading national IP litigation firm"),
    ("Stradling Yocca Carlson & Rauth", "Newport Beach", "Shareholder cohort", "T2",
     "Shareholders at a corporate/securities firm serving OC issuers"),
    ("Snell & Wilmer LLP", "Costa Mesa", "Orange County partner cohort", "T2",
     "Partners in the OC office of a large regional firm"),
    ("Latham & Watkins LLP", "Costa Mesa", "Orange County partner cohort", "T3",
     "Partners in the OC office of a global firm; top-decile partner economics"),
    ("Gibson Dunn & Crutcher LLP", "Irvine", "Orange County partner cohort", "T3",
     "Partners in the OC office of a global firm"),
    ("Paul Hastings LLP", "Costa Mesa", "Orange County partner cohort", "T3",
     "Partners in the OC office of a global firm"),
    ("O'Melveny & Myers LLP", "Newport Beach", "Orange County partner cohort", "T3",
     "Partners in the OC office of a global firm"),
    ("Call & Jensen APC", "Newport Beach", "Shareholder cohort", "T2",
     "Owners of a boutique litigation firm with contingency upside"),
    ("Buchalter APC", "Irvine", "Orange County shareholder cohort", "T2",
     "Shareholders at a large California business firm"),
    ("Haskell & White LLP", "Irvine", "Audit and tax partner cohort", "T2",
     "Partners at an OC accounting firm serving private companies"),
    ("Baker Tilly (Orange County)", "Irvine", "Partner cohort", "T2",
     "Partners at a national accounting firm's OC practice"),
    ("Eide Bailly (Orange County)", "Irvine", "Partner cohort", "T2",
     "Partners at a national accounting firm's OC practice"),
    ("Hoag-affiliated specialist practices", "Newport Beach", "Practice-owning physicians", "T2",
     "Owners of high-margin specialty practices affiliated with Hoag"),
    ("Newport Orthopedic Institute", "Newport Beach", "Partner physicians", "T2",
     "Partner-owners of a large orthopedic group with ancillary revenue"),
    ("Southern California Permanente Medical Group (OC)", "Irvine / Anaheim", "Senior partner physicians", "T1",
     "Partner physicians with large defined-contribution and deferred balances"),
    ("Providence St. Joseph Heritage Medical Group", "Fullerton / Mission Viejo", "Senior affiliated physicians", "T1",
     "High-income affiliated specialists with practice-sale proceeds"),
    ("MemorialCare-affiliated specialty groups", "Fountain Valley", "Practice-owning physicians", "T1",
     "Owners of affiliated specialty practices"),
    ("UCI Health faculty practice", "Orange", "Senior faculty physicians", "T1",
     "Department chairs and senior clinicians with 403(b)/457 balances"),
    ("Newport Beach aesthetic and plastic surgery practices", "Newport Beach", "Owner-surgeons", "T2",
     "Cash-pay practices with exceptional margins and low payer risk"),
    ("Orange County ophthalmology / refractive surgery centers", "Orange County", "Owner-physicians", "T2",
     "Owner-physicians with surgery-center equity alongside practice income"),
    ("Orange County oncology and infusion practices", "Orange County", "Owner-physicians", "T2",
     "Practice owners with high-value ancillary infusion revenue"),
    ("Orange County cardiology groups", "Orange County", "Partner physicians", "T2",
     "Partner-owners consolidating into larger platforms"),
    ("Orange County ambulatory surgery center investors", "Orange County", "Physician-investor households", "T3",
     "Physicians holding equity units in surgery centers alongside practice income"),
    ("Orange County orthodontic / dental practice owners", "Orange County", "Owner-dentists", "T2",
     "Practice owners who are active DSO acquisition targets"),
]

for (anchor, city, target, tier, signal) in D:
    add("D", anchor, city, target, "ROLE-RESOLVE", tier, signal,
        "Practice buy-in, partner retirement buy-out, or DSO/platform acquisition offer",
        trig=4, acc=4, white=5, es=0)


# =============================================================================
# SEGMENT E — Inherited / multi-generational wealth + private foundations
# (25 households)
# The 990-PF filing is the single best public proxy for a $5M+ household:
# a private foundation is nearly always funded by one. Newport Beach alone
# hosts roughly 265 private foundations holding ~$7.6B in assets.
# =============================================================================

E = [
    ("Samueli Foundation / Henry & Susan Samueli", "Newport Coast", "T4",
     "Broadcom co-founder family; one of the largest foundations in the county", 2, 1),
    ("Henry T. Nicholas III family holdings", "Newport Beach", "T4",
     "Broadcom co-founder; large concentrated and philanthropic holdings", 2, 2),
    ("Merage family / Merage Foundations", "Newport Beach", "T4",
     "Proceeds from the Chef America (Hot Pockets) sale; active multi-branch family", 3, 3),
    ("Beall Family Foundation", "Newport Beach", "T4",
     "Founded by a former Rockwell International chairman; long-standing OC donor", 3, 3),
    ("Jack & Shanaz Langson Family Foundation", "Newport Beach", "T4",
     "990-PF shows roughly $37M in assets against $33M income", 4, 4),
    ("Isidore C. & Penny W. Myers Foundation", "Newport Beach", "T4",
     "990-PF shows roughly $44M in assets", 3, 4),
    ("Alfredo & Maria Bubion Charitable Foundation", "Newport Beach", "T4",
     "990-PF shows roughly $38M in assets", 3, 4),
    ("Argyros Family Foundation", "Newport Beach", "T4",
     "Family foundation tied to Arnel & Affiliates and Chapman University", 3, 3),
    ("Segerstrom family foundations", "Costa Mesa", "T4",
     "Family philanthropy anchored to South Coast Plaza and the arts center", 3, 3),
    ("Anne Catherine Getty Earhart", "Corona del Mar", "T4",
     "Getty family heir resident in Orange County", 2, 2),
    ("Caroline Getty", "Corona del Mar", "T4",
     "Getty family heir resident in Orange County", 2, 2),
    ("Lynsi Snyder family trust / Slave 2 Nothing Foundation", "Irvine", "T4",
     "In-N-Out ownership held in family trust structures", 2, 2),
    ("William Wang family (Vizio founder)", "Irvine", "T4",
     "Founder proceeds from the 2024 Walmart acquisition of Vizio", 5, 3),
    ("James Jannard family (Oakley, RED)", "Foothill Ranch", "T4",
     "Two separate company sales; very large realised liquidity", 4, 3),
    ("Dean Stoecker family (Alteryx co-founder)", "Irvine", "T4",
     "Post-take-private founder liquidity", 5, 3),
    ("Vinny Smith family (Quest Software)", "Aliso Viejo", "T4",
     "Realised software proceeds redeployed through a family investment firm", 4, 3),
    ("David Sun family foundation (Kingston)", "Orange County", "T4",
     "Kingston co-founder family philanthropy", 3, 2),
    ("John Tu family foundation (Kingston)", "Orange County", "T4",
     "Kingston co-founder family philanthropy", 3, 2),
    ("Olenicoff family foundation", "Newport Beach", "T4",
     "Real estate family philanthropy", 3, 3),
    ("Donald Bren Foundation and related entities", "Newport Beach", "T4",
     "Largest single philanthropic vehicle in the county", 2, 1),
    ("Kennedy family (First American, third generation)", "Santa Ana", "T3",
     "Multi-generational holding in an S&P 500 company founded in 1889", 3, 3),
    ("Hoag Hospital Foundation principal donors ($1M+ cumulative)", "Newport Beach", "T3",
     "Named-gift donors are reliably $10M+ households", 4, 4),
    ("Orange County Community Foundation DAF holders", "Irvine", "T3",
     "A $688M community foundation whose donor-advised funds are held by HNW households", 4, 5),
    ("Segerstrom Center for the Arts major donors", "Costa Mesa", "T3",
     "Named-seat and gala-table donors at OC's flagship arts institution", 4, 4),
    ("Chapman University trustees and named-gift donors", "Orange", "T3",
     "Trustee boards concentrate OC business owners and inherited wealth", 4, 5),
]

for (anchor, city, tier, signal, trig, acc) in E:
    add("E", anchor, city, "Principal / trustee household", "NAMED-VERIFY", tier, signal,
        "Foundation grant cycle, trustee succession, or appreciated-asset gifting window",
        trig=trig, acc=acc, white=2, es=0)


# =============================================================================
# SEGMENT F — Recent or imminent liquidity events  (10 households/cohorts)
# The highest-conversion segment in private banking. A household that has just
# converted illiquid equity into cash has an unavoidable, dated decision to make.
# =============================================================================

F = [
    ("Inari Medical / Stryker acquisition (2025)", "Irvine",
     "Founder, executive, and employee equity cohort", "T3",
     "All-cash acquisition of an Irvine medical device company", 5, 4, 4),
    ("Axonics / Boston Scientific acquisition (2024)", "Irvine",
     "Executive and employee equity cohort", "T3",
     "All-cash acquisition converting options and RSUs to cash", 5, 4, 4),
    ("Vizio / Walmart acquisition (2024)", "Irvine",
     "Founder and early equity holders", "T4",
     "~$2.3B all-cash acquisition of an Irvine consumer-electronics company", 5, 3, 3),
    ("RED Digital Cinema / Nikon acquisition (2024)", "Foothill Ranch",
     "Founder and senior equity holders", "T3",
     "Sale of a founder-owned camera manufacturer to a strategic buyer", 5, 3, 4),
    ("Alteryx take-private (Clearlake / Insight, 2024)", "Irvine",
     "Founder and executive equity cohort", "T3",
     "$4.4B take-private converting all public shares to cash", 5, 3, 3),
    ("NextGen Healthcare take-private (Thoma Bravo, 2023)", "Irvine",
     "Executive equity cohort", "T2",
     "$1.8B take-private of an Irvine health-IT company", 4, 3, 4),
    ("Pathway Capital Management / Clearlake (2025)", "Irvine",
     "Partner and principal cohort", "T4",
     "~$1B acquisition of a $90B-AUM fund-of-funds manager", 5, 3, 3),
    ("Ingram Micro re-IPO (2024)", "Irvine",
     "Management rollover equity holders", "T3",
     "Return to public markets creating first liquidity since the 2021 take-private", 5, 3, 4),
    ("Anduril employee secondary tenders", "Costa Mesa",
     "Participating employee shareholders", "T3",
     "Recurring company-sponsored tenders at escalating valuations", 5, 3, 5),
    ("H.I.G. Capital acquisition of IAC (Irvine)", "Irvine",
     "Selling owner and management cohort", "T3",
     "Sponsor acquisition of an Irvine-based operating company", 5, 4, 5),
]

for (anchor, city, target, tier, signal, trig, acc, white) in F:
    add("F", anchor, city, target, "ROLE-RESOLVE", tier, signal,
        "Transaction close and cash settlement — engage 60-90 days pre-close",
        trig=trig, acc=acc, white=white, es=0)


# =============================================================================
# SCORE, RANK, WRITE
# =============================================================================

def score(r):
    return (TIER_PTS[r["tier"]]
            + r["trig"] * 5          # 0-25  liquidity/event proximity
            + r["acc"] * 4           # 0-20  quality of the path in
            + r["white"] * 2         # 0-10  competitive whitespace
            + r["es"] * 10)          # 0-10  Spanish-language / affinity fit


def band(s):
    if s >= 80:
        return "P1 - Work now"
    if s >= 65:
        return "P2 - Work this quarter"
    if s >= 50:
        return "P3 - Nurture"
    return "P4 - Monitor"


for r in rows:
    r["score"] = score(r)
    r["band"] = band(r["score"])

rows.sort(key=lambda r: (-r["score"], r["segment"], r["anchor"]))

FIELDS = ["lead_id", "priority_score", "priority_band", "segment", "anchor_entity",
          "city", "target_household", "name_status", "est_wealth_tier_INFERRED",
          "wealth_signal_public_basis", "trigger_event", "verification_source",
          "best_path_in", "spanish_language_affinity"]

with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    w.writeheader()
    for i, r in enumerate(rows, 1):
        w.writerow({
            "lead_id": f"OC-{i:03d}",
            "priority_score": r["score"],
            "priority_band": r["band"],
            "segment": SEGMENT_NAME[r["segment"]],
            "anchor_entity": r["anchor"],
            "city": r["city"],
            "target_household": r["target"],
            "name_status": r["status"],
            "est_wealth_tier_INFERRED": TIER_LABEL[r["tier"]],
            "wealth_signal_public_basis": r["signal"],
            "trigger_event": r["trigger"],
            "verification_source": r["verify"],
            "best_path_in": r["path"],
            "spanish_language_affinity": "YES" if r["es"] else "",
        })

# ---- console summary -------------------------------------------------------
seg = Counter(r["segment"] for r in rows)
bnd = Counter(r["band"] for r in rows)
tier = Counter(r["tier"] for r in rows)

print(f"Wrote {OUT}: {len(rows)} households\n")
print("By segment:")
for k in sorted(seg):
    print(f"  {SEGMENT_NAME[k]:<48} {seg[k]:>3}")
print("\nBy priority band:")
for k in sorted(bnd):
    print(f"  {k:<48} {bnd[k]:>3}")
print("\nBy inferred wealth tier:")
for k in sorted(tier):
    print(f"  {TIER_LABEL[k]:<48} {tier[k]:>3}")
print(f"\nSpanish-language affinity flagged: "
      f"{sum(1 for r in rows if r['es'])}")
print(f"Named-to-verify: {sum(1 for r in rows if r['status'] == 'NAMED-VERIFY')}  |  "
      f"Role-to-resolve: {sum(1 for r in rows if r['status'] == 'ROLE-RESOLVE')}")
