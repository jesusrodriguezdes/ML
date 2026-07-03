"""Claude tool definitions and dispatcher for the financial agent."""

import calendar
import csv
import datetime
import json
import pathlib

import memory
import taxonomy
from categorize import add_rule
from csv_client import (
    detect_recurring_charges,
    fetch_account_balances,
    fetch_monthly_summary,
    fetch_spending_by_category,
    fetch_transactions,
)

_TX_FILE = pathlib.Path(__file__).parent / "data" / "transactions.csv"


def _read_tx() -> tuple[list[dict], list[str]]:
    with open(_TX_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        return rows, list(reader.fieldnames or [])


def _write_tx(rows: list[dict], fields: list[str]) -> None:
    with open(_TX_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def get_review_queue(limit: int = 15) -> dict:
    """Merchant groups still needing categorization, biggest dollar total first."""
    rows, _ = _read_tx()
    groups: dict[str, dict] = {}
    for r in rows:
        if r.get("category") != taxonomy.REVIEW:
            continue
        key = taxonomy.normalize_merchant(r["name"])
        g = groups.setdefault(
            key, {"match": key, "example": r["name"], "occurrences": 0, "total": 0.0}
        )
        g["occurrences"] += 1
        g["total"] = round(g["total"] + float(r["amount"]), 2)
    ordered = sorted(groups.values(), key=lambda g: abs(g["total"]), reverse=True)
    return {
        "remaining_groups": len(ordered),
        "remaining_transactions": sum(g["occurrences"] for g in ordered),
        "batch": ordered[:limit],
    }


def resolve_transactions(match: str, category: str, is_transfer: bool = False) -> dict:
    """Save a rule and apply it to every unresolved transaction whose name
    contains `match` (case-insensitive). Returns how many rows were updated."""
    match_l = match.strip().lower()
    add_rule(match_l, category, is_transfer)
    rows, fields = _read_tx()
    updated = 0
    for r in rows:
        if match_l in r["name"].lower() and r.get("category") == taxonomy.REVIEW:
            r["category"] = category
            r["is_transfer"] = "true" if is_transfer else "false"
            updated += 1
    _write_tx(rows, fields)
    return {"updated": updated, "match": match_l, "category": category, "is_transfer": is_transfer}


def get_categorization_summary() -> dict:
    """Overall state of the categorized dataset across all history."""
    rows, _ = _read_tx()
    total = len(rows)
    needs = sum(1 for r in rows if r.get("category") == taxonomy.REVIEW)
    transfers = sum(1 for r in rows if str(r.get("is_transfer")).lower() == "true")
    spend: dict[str, float] = {}
    for r in rows:
        if str(r.get("is_transfer")).lower() == "true":
            continue
        cat = r.get("category", "")
        if cat in (taxonomy.REVIEW, taxonomy.INCOME_CATEGORY, taxonomy.TRANSFER_CATEGORY):
            continue
        amt = float(r["amount"])
        if amt > 0:
            spend[cat] = round(spend.get(cat, 0.0) + amt, 2)
    return {
        "total_transactions": total,
        "needs_review": needs,
        "reviewed_percent": round(100 * (total - needs) / total, 1) if total else 0,
        "transfers_excluded": transfers,
        "lifetime_spend_by_category": dict(sorted(spend.items(), key=lambda x: x[1], reverse=True)),
    }


def get_budget_status(year: int | None = None, month: int | None = None) -> dict:
    """Compare actual spend per category against budget limits for a month.

    Deterministic math done here in Python so the model never has to compute
    remaining amounts or percentages itself.
    """
    today = datetime.date.today()
    year = year or today.year
    month = month or today.month

    budget = memory.load_budget()
    limits: dict = budget.get("categories", {})
    spent = fetch_spending_by_category(year, month)

    _, last_day = calendar.monthrange(year, month)
    if (year, month) == (today.year, today.month):
        days_left = last_day - today.day
    else:
        days_left = 0

    categories = []
    for cat in sorted(set(limits) | set(spent)):
        limit = limits.get(cat)
        actual = spent.get(cat, 0.0)
        entry = {"category": cat, "spent": round(actual, 2), "limit": limit}
        if limit:
            entry["remaining"] = round(limit - actual, 2)
            entry["percent_used"] = round(100 * actual / limit, 1)
        else:
            entry["note"] = "no budget set for this category"
        categories.append(entry)

    return {
        "year": year,
        "month": month,
        "days_left_in_month": days_left,
        "budget_exists": bool(limits),
        "categories": categories,
        "total_spent": round(sum(spent.values()), 2),
        "total_budget": round(sum(v for v in limits.values() if v), 2) if limits else None,
    }


TOOL_DEFINITIONS = [
    {
        "name": "get_account_balances",
        "description": "Retrieve current balances for all linked bank and credit accounts.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_recent_transactions",
        "description": "Fetch a list of transactions from the past N days.",
        "input_schema": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "Number of days back to retrieve (e.g. 30).",
                }
            },
            "required": ["days"],
        },
    },
    {
        "name": "get_spending_by_category",
        "description": "Return total spending per category for a given calendar month.",
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer"},
                "month": {"type": "integer", "description": "Month number 1-12."},
            },
            "required": ["year", "month"],
        },
    },
    {
        "name": "get_monthly_summary",
        "description": "Return total income, total expenses, and net savings for a given calendar month.",
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer"},
                "month": {"type": "integer", "description": "Month number 1-12."},
            },
            "required": ["year", "month"],
        },
    },
    {
        "name": "get_profile",
        "description": "Load the user's saved profile: income, savings goals, money personality, budgeting method, motivation preferences, and coaching notes. Returns {} if no profile exists yet (meaning onboarding has not happened).",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "save_profile",
        "description": "Save the user's full profile. Pass the COMPLETE profile object (this overwrites the file). Recommended keys: income {monthly_amount, type: fixed|variable, notes}, savings_goals [{name, target_amount, deadline, monthly_contribution}], money_personality, motivation_style, budgeting_method, coaching_notes [list of dated behavioral observations].",
        "input_schema": {
            "type": "object",
            "properties": {
                "profile": {
                    "type": "object",
                    "description": "The complete profile object to persist.",
                }
            },
            "required": ["profile"],
        },
    },
    {
        "name": "get_budget",
        "description": "Load the saved budget: per-category monthly limits, method, rationale. Returns {} if no budget has been created yet.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "save_budget",
        "description": "Save the agreed budget. Pass the COMPLETE budget object. Recommended shape: {method, rationale, categories: {category_name: monthly_limit_number}, monthly_savings_target, created, updated}.",
        "input_schema": {
            "type": "object",
            "properties": {
                "budget": {
                    "type": "object",
                    "description": "The complete budget object to persist.",
                }
            },
            "required": ["budget"],
        },
    },
    {
        "name": "get_budget_status",
        "description": "Compare actual spending against budget limits for a month (defaults to the current month). Returns per-category spent/limit/remaining/percent_used plus days left in the month. Use this for 'how am I doing?' questions and weekly reviews.",
        "input_schema": {
            "type": "object",
            "properties": {
                "year": {"type": "integer", "description": "Defaults to current year."},
                "month": {"type": "integer", "description": "Month 1-12. Defaults to current month."},
            },
            "required": [],
        },
    },
    {
        "name": "detect_recurring_charges",
        "description": "Scan all transactions for likely subscriptions: the same merchant charged in 2+ different months at a similar amount. Returns candidates with estimated monthly cost. Use this to start a subscription audit or hunt for forgotten charges.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_subscriptions",
        "description": "Load previously reviewed subscriptions with their usage, cost-per-use, goal alignment, and keep/cancel/downgrade decisions. Returns [] if no audit has been done.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "save_subscriptions",
        "description": "Save the full subscription list after an audit. Each entry should include: name, monthly_cost, usage_frequency (user-reported), cost_per_use, goal_alignment (goal name or null), overlap_group (e.g. 'streaming' or null), decision (keep|cancel|downgrade), decided_on (date).",
        "input_schema": {
            "type": "object",
            "properties": {
                "subscriptions": {
                    "type": "array",
                    "items": {"type": "object"},
                    "description": "The complete subscription list to persist.",
                }
            },
            "required": ["subscriptions"],
        },
    },
    {
        "name": "get_review_queue",
        "description": "Get the next batch of transaction merchant-groups that still need a category, biggest dollar total first. Each group has a 'match' string (use it verbatim when calling resolve_transactions), an example name, occurrence count, and total amount. Use this to drive the data-cleanup flow.",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "How many merchant groups to return (default 15)."}
            },
            "required": [],
        },
    },
    {
        "name": "resolve_transactions",
        "description": "Categorize every unresolved transaction whose name contains `match`, and save it as a permanent rule so it's never asked again. Set is_transfer=true for money moved between the user's own accounts (checking<->savings, cross-bank Zelle to self) so it is excluded from spending. Category must be one of the canonical categories.",
        "input_schema": {
            "type": "object",
            "properties": {
                "match": {"type": "string", "description": "Lowercase substring identifying the merchant (usually the 'match' from get_review_queue)."},
                "category": {"type": "string", "description": "Canonical category, or 'Transfer' if is_transfer is true."},
                "is_transfer": {"type": "boolean", "description": "True if this is money between the user's own accounts (not real spending or income)."},
            },
            "required": ["match", "category"],
        },
    },
    {
        "name": "get_categorization_summary",
        "description": "Overall state of the categorized dataset: total transactions, how many still need review, percent reviewed, transfers excluded, and lifetime spending by category. Use it to report cleanup progress and give a big-picture spending breakdown.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_canonical_categories",
        "description": "List the valid canonical spending categories to choose from when categorizing.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "get_review_history",
        "description": "Load the log of past weekly reviews (date, category performance, wins, concerns, commitments). Use it to spot trends across weeks and to check whether past commitments were kept.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "log_weekly_review",
        "description": "Append one weekly review entry to the history. Include: date, summary, category_performance (per-category spent vs limit), wins [list], concerns [list], commitments [list of concrete actions the user agreed to].",
        "input_schema": {
            "type": "object",
            "properties": {
                "entry": {
                    "type": "object",
                    "description": "The review entry to append.",
                }
            },
            "required": ["entry"],
        },
    },
]


def dispatch(tool_name: str, tool_input: dict) -> str:
    """Call the matching function and return a JSON string for the tool result."""
    if tool_name == "get_account_balances":
        result = fetch_account_balances()
    elif tool_name == "get_recent_transactions":
        result = fetch_transactions(days=tool_input["days"])
    elif tool_name == "get_spending_by_category":
        result = fetch_spending_by_category(tool_input["year"], tool_input["month"])
    elif tool_name == "get_monthly_summary":
        result = fetch_monthly_summary(tool_input["year"], tool_input["month"])
    elif tool_name == "get_profile":
        result = memory.load_profile()
    elif tool_name == "save_profile":
        memory.save_profile(tool_input["profile"])
        result = {"status": "saved"}
    elif tool_name == "get_budget":
        result = memory.load_budget()
    elif tool_name == "save_budget":
        memory.save_budget(tool_input["budget"])
        result = {"status": "saved"}
    elif tool_name == "get_budget_status":
        result = get_budget_status(tool_input.get("year"), tool_input.get("month"))
    elif tool_name == "detect_recurring_charges":
        result = detect_recurring_charges()
    elif tool_name == "get_subscriptions":
        result = memory.load_subscriptions()
    elif tool_name == "save_subscriptions":
        memory.save_subscriptions(tool_input["subscriptions"])
        result = {"status": "saved"}
    elif tool_name == "get_review_queue":
        result = get_review_queue(tool_input.get("limit", 15))
    elif tool_name == "resolve_transactions":
        result = resolve_transactions(
            tool_input["match"], tool_input["category"], tool_input.get("is_transfer", False)
        )
    elif tool_name == "get_categorization_summary":
        result = get_categorization_summary()
    elif tool_name == "get_canonical_categories":
        result = {"expense": taxonomy.EXPENSE_CATEGORIES, "income": taxonomy.INCOME_CATEGORY, "transfer": taxonomy.TRANSFER_CATEGORY}
    elif tool_name == "get_review_history":
        result = memory.load_review_log()
    elif tool_name == "log_weekly_review":
        memory.append_review(tool_input["entry"])
        result = {"status": "logged"}
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result, default=str)
