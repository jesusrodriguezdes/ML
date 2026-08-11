#!/usr/bin/env python3
"""Render the OC Private Bank plan as a single self-contained HTML page.

Reads leads_orange_county_200.csv and embeds it as JSON so the lead table is
searchable and filterable in the browser.
"""

import csv
import json
import math

CSV_IN = "leads_orange_county_200.csv"
HTML_OUT = "oc_private_bank_plan.html"

with open(CSV_IN, encoding="utf-8") as fh:
    leads = list(csv.DictReader(fh))

# Compact keys to keep the embedded payload small.
payload = [{
    "id": r["lead_id"],
    "s": int(r["priority_score"]),
    "b": r["priority_band"].split(" - ")[0],
    "ba": r["priority_band"].split(" - ")[1],
    "sg": r["segment"].split(" - ")[0],
    "sn": r["segment"].split(" - ")[1],
    "a": r["anchor_entity"],
    "c": r["city"],
    "t": r["target_household"],
    "ns": r["name_status"],
    "w": r["est_wealth_tier_INFERRED"],
    "sig": r["wealth_signal_public_basis"],
    "tr": r["trigger_event"],
    "v": r["verification_source"],
    "p": r["best_path_in"],
    "es": bool(r["spanish_language_affinity"]),
} for r in leads]

data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

# ---- market step-down, log-scaled bar widths --------------------------------
STEPS = [
    ("Net worth &ge; $5M", 75000, "The figure J.P. Morgan gave you", False),
    ("Investable &ge; $5M", 37000, "Primary-residence equity removed", False),
    ("Investable &ge; $10M", 12000, "The real Private Bank threshold", True),
    ("Investable &ge; $25M", 3200, "The core of the book", False),
    ("Investable &ge; $100M", 450, "Consistent with 12 OC billionaires", False),
]
lo, hi = math.log(300), math.log(90000)
step_html = "\n".join(
    f'''      <div class="step{' step--key' if key else ''}">
        <div class="step__label">{label}</div>
        <div class="step__track"><div class="step__bar" style="--w:{(math.log(v)-lo)/(hi-lo)*100:.1f}%"></div></div>
        <div class="step__val">{v:,}</div>
        <div class="step__note">{note}</div>
      </div>'''
    for (label, v, note, key) in STEPS)

FUNNEL = [
    ("Qualified target households", 200, "the working list"),
    ("First meetings", 50, "25% conversion"),
    ("Live opportunities", 20, "40% progress"),
    ("New relationships", 10, "50% close"),
]
funnel_html = "\n".join(
    f'''      <div class="fn">
        <div class="fn__bar" style="--w:{v/200*100:.0f}%"><span>{v}</span></div>
        <div class="fn__txt"><strong>{label}</strong><span>{note}</span></div>
      </div>''' for (label, v, note) in FUNNEL)

SEGMENTS = [
    ("A", "Concentrated public-company equity", 60,
     "Officers and directors of 20 OC-headquartered issuers. Fastest to identify — Forms 4 and 144 are public and dated."),
    ("B", "Private business owner, pre-liquidity", 45,
     "Wealth trapped in the operating company. Longest cycle, highest value, and where the Private Bank actually wins."),
    ("C", "Real estate owner / operator", 35,
     "The most OC-native wealth form. Assessor and recorder data make ownership, debt, and transfer dates fully verifiable."),
    ("D", "Professional practice equity", 25,
     "Physicians, dentists, law and accounting partners. Chronically under-advised; entered at the buy-in or practice sale."),
    ("E", "Inherited / multi-generational + foundation", 25,
     "A 990-PF filing is the strongest free proxy for a $5M+ household. Newport Beach alone hosts ~265 private foundations."),
    ("F", "Recent or imminent liquidity event", 10,
     "Highest conversion of any segment. The household faces a dated decision it cannot avoid making."),
]
seg_html = "\n".join(
    f'''      <article class="seg">
        <div class="seg__top"><span class="seg__key">{k}</span><span class="seg__n">{n}</span></div>
        <h3>{name}</h3><p>{desc}</p>
      </article>''' for (k, name, n, desc) in SEGMENTS)

LAYERS = [
    ("Securities disclosure", "SEC EDGAR",
     "DEF 14A, Forms 3/4/5, Form 144, SC 13D/G, 8-K",
     "Highest confidence. A Form 144 is a household converting stock to cash on a known date."),
    ("Real property records", "OC Assessor &amp; Clerk-Recorder",
     "Parcel roll, grant deeds, deeds of trust, permits",
     "Repeat ownership across 5+ parcels; high value with no open deed of trust; 1031 exchanges in flight."),
    ("Business ownership", "CA SoS, CSLB, ABC, DBO, UCC",
     "Entity filings, licences, bonds, lender filings",
     "Entity age &times; headcount &times; industry margin is a reliable proxy for owner net worth."),
    ("Philanthropic disclosure", "IRS Form 990-PF",
     "Foundation assets, grants, named trustees",
     "A private foundation is almost never created by a household worth under $5M."),
    ("Event intelligence", "Deal press, 8-K, probate",
     "M&amp;A, IPO, tender offers, ESOP, settlements, estates",
     "Converts several times better than any other layer, because the decision is dated."),
]
layer_html = "\n".join(
    f'''      <div class="layer">
        <div class="layer__hd"><h3>{name}</h3><span class="layer__src">{src}</span></div>
        <p class="layer__what">{what}</p>
        <p class="layer__why">{why}</p>
      </div>''' for (name, src, what, why) in LAYERS)

ROUTES = [
    ("Centre-of-influence referral", "Highest conversion, slowest to build",
     "25 active COIs each delivering two qualified introductions a year is 50 introductions — five times what you need. Approach CPAs and attorneys with <em>analysis</em>, not a brochure. This is where a portfolio manager's background is worth the most."),
    ("Event trigger outreach", "Highest per-contact conversion",
     "Direct contact is effective only when genuinely event-driven. Name the filing, frame a non-obvious problem, offer analysis, ask for nothing. No trigger in the record means no contact."),
    ("The Spanish-language franchise", "Your structural advantage",
     "~30,000 Hispanic-owned businesses in Orange County; the largest several hundred are Private Bank households. Almost no competitor runs the conversation in Spanish across two generations. Build it as market coverage with a revenue number, never as a diversity initiative."),
    ("Convening and content", "Scales credibility",
     "Host the room rather than working it. Concentrated-stock workshops, exit-readiness roundtables, Spanish-language owner sessions — and a next-gen forum, which is quietly the most valuable, because every incumbent covers the patriarch and nobody covers the children."),
    ("Institutional and board proximity", "Slowest, most durable",
     "Nonprofit boards are the highest-yield warm-introduction surface in the county — the households have already self-identified as approachable. Serve on one finance committee genuinely; it pays off for a decade."),
]
route_html = "\n".join(
    f'''      <article class="route">
        <div class="route__hd"><h3>{name}</h3><span class="route__tag">{tag}</span></div>
        <p>{body}</p>
      </article>''' for (name, tag, body) in ROUTES)

PLAN = [
    ("Days 1&ndash;30", "Map and validate", [
        "Build the standing list of 20 OC-headquartered issuers; pull CIKs; set weekly Form 4/144 monitoring",
        "Resolve every ROLE-RESOLVE row to a named household in the firm's tools",
        "Rank 40 candidate COIs; book the first 15 meetings",
        "Confirm internal referral protocol with Chase Business Banking and Commercial Banking OC",
        "Join the Orange County Hispanic Chamber of Commerce",
        "Compliance sign-off on outreach templates and the content plan",
    ]),
    ("Days 31&ndash;60", "Route and engage", [
        "20 COI meetings completed, each with a specific named introduction requested",
        "First 30 trigger-based approaches sent &mdash; P1 band only",
        "8&ndash;12 first meetings held",
        "First co-hosted seminar scheduled with a CPA partner",
        "Second-generation contacts identified inside the top 25 family targets",
    ]),
    ("Days 61&ndash;90", "Convert and systematise", [
        "50 households at Stage 3 (Engaged) &mdash; the only number that predicts the year",
        "8&ndash;10 live opportunities at Stage 4",
        "First 2&ndash;3 relationships funded, expected from the post-liquidity cohort",
        "First Spanish-language roundtable delivered",
        "Full pipeline review; conversion by segment and source; list re-scored",
    ]),
]
plan_html = "\n".join(
    f'''      <article class="phase">
        <div class="phase__when">{when}</div>
        <h3>{what}</h3>
        <ul>{''.join(f"<li>{i}</li>" for i in items)}</ul>
      </article>''' for (when, what, items) in PLAN)

n_p1 = sum(1 for r in payload if r["b"] == "P1")
n_p2 = sum(1 for r in payload if r["b"] == "P2")
n_es = sum(1 for r in payload if r["es"])
n_named = sum(1 for r in payload if r["ns"] == "NAMED-VERIFY")

HTML = f"""<title>Orange County $5M+ Household Map &mdash; Private Bank Business Plan</title>
<style>
:root {{
  --paper:#F7F9F8; --surface:#FFFFFF; --surface-2:#EFF4F2; --border:#D8E1DE;
  --ink:#12211F; --ink-2:#3A4B48; --muted:#5F716E;
  --accent:#0E5C60; --accent-soft:#DCEBEA; --signal:#8A5D12; --signal-soft:#F5EBD6;
  --shadow:0 1px 2px rgba(18,33,31,.05), 0 8px 24px -12px rgba(18,33,31,.14);
  --font-display:'Iowan Old Style','Palatino Linotype',Palatino,'Book Antiqua',Georgia,serif;
  --font-body:system-ui,-apple-system,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;
  --font-mono:ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,monospace;
  --wrap:1180px; --prose:68ch;
}}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{
    --paper:#0B1211; --surface:#111B1A; --surface-2:#172422; --border:#25352F;
    --ink:#E6EDEB; --ink-2:#BCCAC7; --muted:#8DA09C;
    --accent:#5CB8AE; --accent-soft:#14312F; --signal:#D2A247; --signal-soft:#2E2517;
    --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -12px rgba(0,0,0,.6);
  }}
}}
:root[data-theme="dark"] {{
  --paper:#0B1211; --surface:#111B1A; --surface-2:#172422; --border:#25352F;
  --ink:#E6EDEB; --ink-2:#BCCAC7; --muted:#8DA09C;
  --accent:#5CB8AE; --accent-soft:#14312F; --signal:#D2A247; --signal-soft:#2E2517;
  --shadow:0 1px 2px rgba(0,0,0,.4), 0 8px 24px -12px rgba(0,0,0,.6);
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; background:var(--paper); color:var(--ink);
  font-family:var(--font-body); font-size:16px; line-height:1.65;
  -webkit-font-smoothing:antialiased;
}}
.wrap {{ max-width:var(--wrap); margin:0 auto; padding:0 24px; }}
.prose {{ max-width:var(--prose); }}
h1,h2,h3 {{ font-family:var(--font-display); font-weight:600; text-wrap:balance; line-height:1.2; margin:0; }}
p {{ margin:0; }}
a {{ color:var(--accent); }}
em {{ font-style:italic; }}

/* ---- top bar ---- */
.bar {{
  position:sticky; top:0; z-index:50; background:color-mix(in srgb, var(--paper) 88%, transparent);
  backdrop-filter:blur(10px); border-bottom:1px solid var(--border);
}}
.bar__in {{ max-width:var(--wrap); margin:0 auto; padding:10px 24px; display:flex; align-items:center; gap:20px; }}
.bar__mark {{ font-family:var(--font-mono); font-size:11px; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); white-space:nowrap; }}
.bar__nav {{ display:flex; gap:18px; overflow-x:auto; margin-left:auto; }}
.bar__nav a {{ font-size:13px; color:var(--muted); text-decoration:none; white-space:nowrap; padding:4px 0; border-bottom:1.5px solid transparent; }}
.bar__nav a:hover {{ color:var(--ink); border-bottom-color:var(--accent); }}

/* ---- hero ---- */
.hero {{ padding:72px 0 48px; border-bottom:1px solid var(--border); }}
.eyebrow {{ font-family:var(--font-mono); font-size:11.5px; letter-spacing:.16em; text-transform:uppercase; color:var(--muted); }}
.hero h1 {{ font-size:clamp(2.4rem,5.2vw,3.9rem); margin:16px 0 20px; letter-spacing:-.015em; }}
.hero__sub {{ font-size:1.18rem; color:var(--ink-2); max-width:60ch; }}
.thesis {{
  margin-top:40px; padding:26px 28px; background:var(--surface); border:1px solid var(--border);
  border-left:3px solid var(--accent); border-radius:3px; box-shadow:var(--shadow); max-width:74ch;
}}
.thesis p {{ font-family:var(--font-display); font-size:1.2rem; line-height:1.5; }}
.thesis strong {{ color:var(--accent); font-weight:600; }}

/* ---- sections ---- */
section {{ padding:64px 0; border-bottom:1px solid var(--border); }}
.sec__hd {{ display:flex; align-items:baseline; gap:14px; margin-bottom:10px; }}
.sec__hd h2 {{ font-size:clamp(1.6rem,3vw,2.15rem); letter-spacing:-.01em; }}
.sec__num {{ font-family:var(--font-mono); font-size:12px; color:var(--accent); letter-spacing:.1em; }}
.sec__lede {{ color:var(--ink-2); margin-bottom:36px; max-width:var(--prose); font-size:1.05rem; }}

/* ---- market step-down ---- */
.steps {{ display:flex; flex-direction:column; gap:2px; }}
.step {{
  display:grid; grid-template-columns:210px minmax(0,1fr) 92px 250px; gap:20px; align-items:center;
  padding:13px 14px; border-radius:3px;
}}
.step--key {{ background:var(--accent-soft); }}
.step__label {{ font-size:.95rem; font-weight:550; }}
.step__track {{ height:12px; background:var(--surface-2); border-radius:2px; overflow:hidden; }}
.step__bar {{ height:100%; width:var(--w); background:var(--accent); border-radius:2px; animation:grow .9s cubic-bezier(.22,.8,.3,1) both; }}
.step--key .step__bar {{ background:var(--accent); }}
.step__val {{ font-family:var(--font-mono); font-variant-numeric:tabular-nums; font-size:1.05rem; text-align:right; font-weight:600; }}
.step__note {{ font-size:.85rem; color:var(--muted); }}
@keyframes grow {{ from {{ width:0; }} }}
@media (max-width:820px) {{
  .step {{ grid-template-columns:1fr 78px; grid-template-areas:"l v" "t t" "n n"; gap:6px 12px; }}
  .step__label {{ grid-area:l; }} .step__val {{ grid-area:v; }}
  .step__track {{ grid-area:t; }} .step__note {{ grid-area:n; }}
}}

/* ---- funnel ---- */
.funnel {{ display:flex; flex-direction:column; gap:10px; margin-top:8px; max-width:760px; }}
.fn {{ display:flex; align-items:center; gap:18px; }}
.fn__bar {{
  width:var(--w); min-width:74px; background:var(--accent); color:var(--surface);
  padding:9px 12px; border-radius:2px; font-family:var(--font-mono);
  font-variant-numeric:tabular-nums; font-size:.95rem; font-weight:600; text-align:right;
}}
:root[data-theme="dark"] .fn__bar, :root:not([data-theme="light"]) .fn__bar {{ color:#08110F; }}
.fn__txt {{ display:flex; flex-direction:column; }}
.fn__txt strong {{ font-size:.95rem; font-weight:550; }}
.fn__txt span {{ font-size:.82rem; color:var(--muted); }}

/* ---- grids ---- */
.grid {{ display:grid; gap:16px; }}
.grid--3 {{ grid-template-columns:repeat(auto-fit,minmax(290px,1fr)); }}
.grid--2 {{ grid-template-columns:repeat(auto-fit,minmax(380px,1fr)); }}
.seg, .route, .phase, .layer {{
  background:var(--surface); border:1px solid var(--border); border-radius:4px;
  padding:22px 24px; box-shadow:var(--shadow);
}}
.seg__top {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }}
.seg__key {{
  font-family:var(--font-mono); font-size:11px; letter-spacing:.1em; color:var(--accent);
  background:var(--accent-soft); padding:3px 9px; border-radius:2px;
}}
.seg__n {{ font-family:var(--font-mono); font-size:1.6rem; font-weight:600; font-variant-numeric:tabular-nums; }}
.seg h3 {{ font-size:1.05rem; margin-bottom:8px; }}
.seg p, .route p, .layer__why {{ font-size:.9rem; color:var(--ink-2); }}

.layer__hd {{ display:flex; justify-content:space-between; align-items:baseline; gap:12px; margin-bottom:6px; }}
.layer h3 {{ font-size:1.05rem; }}
.layer__src {{ font-family:var(--font-mono); font-size:10.5px; color:var(--accent); text-align:right; }}
.layer__what {{ font-size:.83rem; color:var(--muted); margin-bottom:10px; font-family:var(--font-mono); }}

.route__hd {{ display:flex; justify-content:space-between; align-items:baseline; gap:12px; margin-bottom:10px; flex-wrap:wrap; }}
.route h3 {{ font-size:1.1rem; }}
.route__tag {{ font-size:11px; font-family:var(--font-mono); color:var(--signal); background:var(--signal-soft); padding:3px 9px; border-radius:2px; letter-spacing:.04em; }}

.phase__when {{ font-family:var(--font-mono); font-size:11px; letter-spacing:.12em; text-transform:uppercase; color:var(--accent); margin-bottom:8px; }}
.phase h3 {{ font-size:1.15rem; margin-bottom:12px; }}
.phase ul {{ margin:0; padding-left:18px; display:flex; flex-direction:column; gap:7px; }}
.phase li {{ font-size:.89rem; color:var(--ink-2); }}

/* ---- lead table ---- */
.tools {{ display:flex; gap:10px; flex-wrap:wrap; align-items:center; margin-bottom:16px; }}
.tools input, .tools select {{
  font-family:var(--font-body); font-size:.88rem; padding:8px 11px; border-radius:3px;
  border:1px solid var(--border); background:var(--surface); color:var(--ink);
}}
.tools input {{ min-width:230px; flex:1 1 230px; }}
.tools input:focus-visible, .tools select:focus-visible, .chk:focus-within {{ outline:2px solid var(--accent); outline-offset:1px; }}
.chk {{ display:flex; align-items:center; gap:7px; font-size:.85rem; color:var(--ink-2); cursor:pointer; }}
.count {{ font-family:var(--font-mono); font-size:.8rem; color:var(--muted); margin-left:auto; }}
.tbl-wrap {{ overflow-x:auto; border:1px solid var(--border); border-radius:4px; background:var(--surface); }}
table {{ border-collapse:collapse; width:100%; min-width:840px; }}
th {{
  text-align:left; font-size:10.5px; font-family:var(--font-mono); letter-spacing:.1em; text-transform:uppercase;
  color:var(--muted); font-weight:500; padding:11px 14px; border-bottom:1px solid var(--border);
  position:sticky; top:0; background:var(--surface-2);
}}
td {{ padding:11px 14px; border-bottom:1px solid var(--border); font-size:.87rem; vertical-align:top; }}
tr.lead {{ cursor:pointer; }}
tr.lead:hover td {{ background:var(--surface-2); }}
.id {{ font-family:var(--font-mono); font-size:.78rem; color:var(--muted); white-space:nowrap; }}
.score {{ font-family:var(--font-mono); font-variant-numeric:tabular-nums; font-weight:600; }}
.pill {{ display:inline-block; font-family:var(--font-mono); font-size:10px; letter-spacing:.06em; padding:2px 7px; border-radius:2px; white-space:nowrap; }}
.pill--p1 {{ background:var(--signal-soft); color:var(--signal); }}
.pill--p2 {{ background:var(--accent-soft); color:var(--accent); }}
.pill--p3 {{ background:var(--surface-2); color:var(--muted); }}
.es {{ color:var(--signal); font-weight:600; font-size:.75rem; font-family:var(--font-mono); }}
.tgt {{ font-weight:550; }}
.anchor {{ color:var(--ink-2); }}
.tier {{ font-family:var(--font-mono); font-size:.76rem; color:var(--muted); white-space:nowrap; }}
tr.detail td {{ background:var(--surface-2); padding:16px 18px; }}
.det {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:16px; }}
.det div span {{ display:block; font-family:var(--font-mono); font-size:10px; letter-spacing:.1em; text-transform:uppercase; color:var(--muted); margin-bottom:4px; }}
.det div p {{ font-size:.85rem; color:var(--ink-2); }}

/* ---- callout ---- */
.warn {{
  background:var(--signal-soft); border:1px solid color-mix(in srgb, var(--signal) 30%, transparent);
  border-radius:4px; padding:24px 26px; margin-top:32px;
}}
.warn h3 {{ font-size:1.05rem; color:var(--signal); margin-bottom:12px; }}
.warn ul {{ margin:0; padding-left:18px; display:flex; flex-direction:column; gap:8px; }}
.warn li {{ font-size:.89rem; color:var(--ink-2); }}
.warn code {{ font-family:var(--font-mono); font-size:.8rem; background:var(--surface); padding:1px 5px; border-radius:2px; }}

/* ---- stats strip ---- */
.stats {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:1px; background:var(--border); border:1px solid var(--border); border-radius:4px; overflow:hidden; margin-top:36px; }}
.stat {{ background:var(--surface); padding:18px 20px; }}
.stat__v {{ font-family:var(--font-mono); font-size:1.7rem; font-weight:600; font-variant-numeric:tabular-nums; letter-spacing:-.02em; }}
.stat__l {{ font-size:.78rem; color:var(--muted); margin-top:3px; }}

/* ---- close ---- */
.close {{ background:var(--surface); border:1px solid var(--border); border-left:3px solid var(--signal); border-radius:3px; padding:28px 30px; max-width:74ch; box-shadow:var(--shadow); }}
.close p {{ font-family:var(--font-display); font-size:1.15rem; line-height:1.55; color:var(--ink); }}
footer {{ padding:44px 0 64px; color:var(--muted); font-size:.83rem; }}
footer p + p {{ margin-top:10px; }}
@media (prefers-reduced-motion:reduce) {{ * {{ animation:none !important; transition:none !important; }} }}
</style>

<div class="bar"><div class="bar__in">
  <span class="bar__mark">OC &middot; Private Bank</span>
  <nav class="bar__nav">
    <a href="#market">Market</a><a href="#method">Method</a><a href="#segments">Segments</a>
    <a href="#leads">200 Leads</a><a href="#access">Access</a><a href="#plan">30/60/90</a>
  </nav>
</div></div>

<div class="wrap">

<header class="hero">
  <div class="eyebrow">Business plan &middot; J.P. Morgan Private Bank &middot; Orange County</div>
  <h1>Mapping Orange County's $5M+ households</h1>
  <p class="hero__sub">A process for identifying them from public record, a scored list of the first two hundred, and the referral architecture that gets you in the room.</p>
  <div class="thesis">
    <p>Seventy-five thousand is right for <em>net worth</em>. But the Private Bank's addressable market in Orange County is closer to <strong>twelve thousand households</strong>, and about <strong>three thousand</strong> are the real core. That isn't a discouraging number &mdash; it's a targeting number. It means the strategy is precision, not volume, and the whole game is competitive displacement.</p>
  </div>
  <div class="stats">
    <div class="stat"><div class="stat__v">200</div><div class="stat__l">Scored households</div></div>
    <div class="stat"><div class="stat__v">{n_p1}</div><div class="stat__l">P1 &mdash; work now</div></div>
    <div class="stat"><div class="stat__v">{n_p2}</div><div class="stat__l">P2 &mdash; this quarter</div></div>
    <div class="stat"><div class="stat__v">{n_es}</div><div class="stat__l">Spanish-language affinity</div></div>
    <div class="stat"><div class="stat__v">6</div><div class="stat__l">Wealth segments</div></div>
  </div>
</header>

<section id="market">
  <div class="sec__hd"><span class="sec__num">01</span><h2>The number they gave you, stress-tested</h2></div>
  <p class="sec__lede">Orange County has roughly 1.06 million households. 75,000 at $5M+ implies 7.1% of them &mdash; about 4.7&times; the national rate. That is plausible at the aggressive end of a defensible band. The problem isn't accuracy. It's that net worth includes the primary residence and illiquid business equity, and a Private Bank can manage neither.</p>
  <div class="steps">
{step_html}
  </div>
  <p class="sec__lede" style="margin-top:32px">A household in Villa Park with a paid-off $1.6M home, $2.2M in retirement accounts and $1.4M besides is a genuine $5.2M net worth household. It is not a Private Bank client &mdash; it's Chase Private Client. Twelve thousand households, by contrast, is small enough that one banker can actually map it.</p>
  <h3 style="margin:36px 0 6px; font-size:1.15rem">Why the list is exactly two hundred</h3>
  <p class="sec__lede" style="margin-bottom:24px">At realistic private banking conversion rates, a 200-name qualified list is precisely what one banker needs to underwrite a credible year-one plan. It isn't an arbitrary round number &mdash; it's the funnel inverted.</p>
  <div class="funnel">
{funnel_html}
  </div>
</section>

<section id="method">
  <div class="sec__hd"><span class="sec__num">02</span><h2>How you actually identify them</h2></div>
  <p class="sec__lede">No lawful source publishes households by net worth. Anyone selling you one is selling modelled estimates or scraped data. Wealth is not found &mdash; it is inferred from public signals, then confirmed through a relationship. Five layers carry the signal, and every one of them is free and compliance-safe.</p>
  <div class="grid grid--2">
{layer_html}
  </div>
  <div class="warn">
    <h3>Data integrity rules &mdash; read before using the list</h3>
    <ul>
      <li><strong>No net worth is asserted anywhere.</strong> Every tier is a modelled inference from a public signal, carried in a field named <code>est_wealth_tier_INFERRED</code>.</li>
      <li><strong><code>NAMED-VERIFY</code></strong> ({n_named} rows) means a name drawn from public business reporting that must be re-confirmed in the firm's system of record before contact. Executive rosters change constantly, and a stale title in a first email destroys credibility permanently.</li>
      <li><strong><code>ROLE-RESOLVE</code></strong> ({200 - n_named} rows) identifies a role at a real entity; the verification source tells you exactly how to resolve it to a person.</li>
      <li><strong>Business information only.</strong> Entity, role, public filing. No home addresses, personal contact details, or family information.</li>
      <li><strong>Public record and firm-provided sources only.</strong> Nothing scraped, nothing bought from an unapproved vendor &mdash; because as a JPM employee your prospect records and outreach materials are subject to supervisory review.</li>
    </ul>
  </div>
</section>

<section id="segments">
  <div class="sec__hd"><span class="sec__num">03</span><h2>Six segments, six different plays</h2></div>
  <p class="sec__lede">Each segment has a different source, a different natural trigger, and a very different sales cycle &mdash; one to three months for a household whose cash has already landed, nine to eighteen for an owner whose wealth is still inside the company.</p>
  <div class="grid grid--3">
{seg_html}
  </div>
</section>

<section id="leads">
  <div class="sec__hd"><span class="sec__num">04</span><h2>The two hundred</h2></div>
  <p class="sec__lede">Scored 0&ndash;100 across wealth signal (35), trigger proximity (25), access quality (20), competitive whitespace (10) and affinity fit (10). Trigger proximity is weighted second-heaviest deliberately: a $50M household with no event is a three-year cultivation, while a $12M household sixty days from close is a this-quarter opportunity. Bankers who sort by wealth alone starve. <strong>Select any row to see its verification path.</strong></p>
  <div class="tools">
    <input id="q" type="search" placeholder="Search household, entity, or city&hellip;" aria-label="Search leads">
    <select id="fseg" aria-label="Filter by segment"><option value="">All segments</option></select>
    <select id="fband" aria-label="Filter by priority"><option value="">All priorities</option><option value="P1">P1 &mdash; Work now</option><option value="P2">P2 &mdash; This quarter</option><option value="P3">P3 &mdash; Nurture</option></select>
    <label class="chk"><input id="fes" type="checkbox"> Spanish affinity only</label>
    <span class="count" id="count"></span>
  </div>
  <div class="tbl-wrap">
    <table>
      <thead><tr>
        <th>ID</th><th>Score</th><th>Priority</th><th>Target household</th>
        <th>Anchor entity</th><th>City</th><th>Est. tier</th><th>Trigger</th>
      </tr></thead>
      <tbody id="tbody"></tbody>
    </table>
  </div>
</section>

<section id="access">
  <div class="sec__hd"><span class="sec__num">05</span><h2>Getting in front of them</h2></div>
  <p class="sec__lede">Identification is the easy half. Nobody with $20M takes a cold call from a banker. The governing principle: never approach as a banker looking for assets &mdash; approach as a specialist responding to a specific event they are already thinking about. No trigger in the record means no contact.</p>
  <div class="grid grid--2">
{route_html}
  </div>
</section>

<section id="plan">
  <div class="sec__hd"><span class="sec__num">06</span><h2>First ninety days</h2></div>
  <p class="sec__lede">Two-thirds of a year-one book comes from the post-liquidity cohort, because it is the only segment with a short cycle. The pre-liquidity work planted in year one pays out in years two and three &mdash; which is exactly the argument for hiring someone who intends to still be there.</p>
  <div class="grid grid--3">
{plan_html}
  </div>
  <h3 style="margin:44px 0 16px; font-size:1.3rem">The line to close on</h3>
  <div class="close">
    <p>&ldquo;Seventy-five thousand households at $5M is the market. About twelve thousand are actually Private Bank households, and roughly three thousand are the core. I've built the process that finds them, a scored list of the first two hundred, and the referral network plan that gets me in the room. What I'd want to know from you is how much of that list the firm already banks &mdash; because that changes whether year one is competitive displacement or net new.&rdquo;</p>
  </div>
  <p class="sec__lede" style="margin-top:20px">Ending on a question about <em>their</em> book is what separates a candidate from a colleague.</p>
</section>

<footer>
  <p>Public figures drawn from Orange County Business Journal reporting on the county's largest private companies and wealthiest residents, Forbes billionaires coverage identifying 12 Orange County residents, IRS Form 990-PF data via ProPublica Nonprofit Explorer, SEC EDGAR, and California public business and property records.</p>
  <p>Household counts and wealth tiers are modelled estimates, not survey counts. No verified net worth data exists or is asserted here. Every named individual must be re-verified in the firm's system of record before any outreach.</p>
</footer>

</div>

<script>
const LEADS = {data_json};
const tbody = document.getElementById('tbody');
const q = document.getElementById('q'), fseg = document.getElementById('fseg');
const fband = document.getElementById('fband'), fes = document.getElementById('fes');
const countEl = document.getElementById('count');

[...new Set(LEADS.map(l => l.sg + ' \\u2014 ' + l.sn))].sort().forEach(s => {{
  const o = document.createElement('option');
  o.value = s.split(' \\u2014 ')[0]; o.textContent = s; fseg.appendChild(o);
}});

const esc = s => String(s).replace(/[&<>"]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}})[c]);
let open = null;

function render() {{
  const term = q.value.trim().toLowerCase();
  const rows = LEADS.filter(l =>
    (!term || (l.t + ' ' + l.a + ' ' + l.c + ' ' + l.tr).toLowerCase().includes(term)) &&
    (!fseg.value || l.sg === fseg.value) &&
    (!fband.value || l.b === fband.value) &&
    (!fes.checked || l.es));

  countEl.textContent = rows.length + ' of ' + LEADS.length + ' households';
  tbody.innerHTML = rows.map(l => `
    <tr class="lead" data-id="${{l.id}}" tabindex="0">
      <td class="id">${{l.id}}</td>
      <td class="score">${{l.s}}</td>
      <td><span class="pill pill--${{l.b.toLowerCase()}}">${{esc(l.ba)}}</span></td>
      <td class="tgt">${{esc(l.t)}} ${{l.es ? '<span class="es">&nbsp;ES</span>' : ''}}</td>
      <td class="anchor">${{esc(l.a)}}</td>
      <td>${{esc(l.c)}}</td>
      <td class="tier">${{esc(l.w)}}</td>
      <td>${{esc(l.tr)}}</td>
    </tr>`).join('');
  if (!rows.length) tbody.innerHTML = '<tr><td colspan="8" style="padding:28px;text-align:center;color:var(--muted)">No households match those filters.</td></tr>';
  open = null;
}}

function toggle(tr) {{
  const l = LEADS.find(x => x.id === tr.dataset.id);
  if (open && open.prev === tr) {{ open.el.remove(); open = null; return; }}
  if (open) {{ open.el.remove(); open = null; }}
  const d = document.createElement('tr');
  d.className = 'detail';
  d.innerHTML = `<td colspan="8"><div class="det">
    <div><span>Segment</span><p>${{esc(l.sg)}} &mdash; ${{esc(l.sn)}}</p></div>
    <div><span>Public wealth signal</span><p>${{esc(l.sig)}}</p></div>
    <div><span>Name status</span><p>${{esc(l.ns)}}</p></div>
    <div><span>Verification source</span><p>${{esc(l.v)}}</p></div>
    <div><span>Best path in</span><p>${{esc(l.p)}}</p></div>
  </div></td>`;
  tr.after(d);
  open = {{ el: d, prev: tr }};
}}

tbody.addEventListener('click', e => {{
  const tr = e.target.closest('tr.lead'); if (tr) toggle(tr);
}});
tbody.addEventListener('keydown', e => {{
  if (e.key !== 'Enter' && e.key !== ' ') return;
  const tr = e.target.closest('tr.lead'); if (tr) {{ e.preventDefault(); toggle(tr); }}
}});
[q, fseg, fband, fes].forEach(el => el.addEventListener('input', render));
render();
</script>
"""

with open(HTML_OUT, "w", encoding="utf-8") as fh:
    fh.write(HTML)

print(f"Wrote {HTML_OUT} ({len(HTML):,} bytes) with {len(payload)} leads embedded.")
