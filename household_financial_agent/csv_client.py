"""CSV-based financial data client — reads from local data files.

Drop-in replacement for plaid_client.py while Plaid production access is pending.
To switch back to Plaid: change the import in tools.py from csv_client to plaid_client.

Edit these files with Excel, Google Sheets, or any text editor:
    household_financial_agent/data/accounts.csv
    household_financial_agent/data/transactions.csv

Amount sign convention (same as Plaid, so swapping back later requires no logic changes):
    positive amount = money going OUT (expense/purchase)
    negative amount = money coming IN (income/deposit)
"""

import calendar
import csv
import datetime
import pathlib

_DATA_DIR = pathlib.Path(__file__).parent / "data"
_TRANSACTIONS_FILE = _DATA_DIR / "transactions.csv"
_ACCOUNTS_FILE = _DATA_DIR / "accounts.csv"


def fetch_account_balances() -> list[dict]:
    """Return current balances for all accounts in accounts.csv."""
    accounts = []
    with open(_ACCOUNTS_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            accounts.append(
                {
                    "name": row["name"],
                    "type": row["type"],
                    "subtype": row["subtype"],
                    "current_balance": float(row["current_balance"]),
                    "available_balance": float(row["available_balance"]) if row.get("available_balance") else None,
                    "currency": row.get("currency", "USD"),
                }
            )
    return accounts


def fetch_transactions(days: int) -> list[dict]:
    """Return transactions from the past `days` days."""
    cutoff = datetime.date.today() - datetime.timedelta(days=days)
    transactions = []
    with open(_TRANSACTIONS_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            txn_date = datetime.date.fromisoformat(row["date"])
            if txn_date >= cutoff:
                transactions.append(
                    {
                        "date": row["date"],
                        "name": row["name"],
                        "amount": float(row["amount"]),
                        "category": row.get("category", "Uncategorized"),
                        "account_id": row.get("account", ""),
                    }
                )
    return transactions


def fetch_spending_by_category(year: int, month: int) -> dict[str, float]:
    """Return total spending per category for the given month (expenses only)."""
    _, last_day = calendar.monthrange(year, month)
    start = datetime.date(year, month, 1)
    end = datetime.date(year, month, last_day)
    days_back = (datetime.date.today() - start).days + 1
    transactions = fetch_transactions(max(days_back, 1))

    totals: dict[str, float] = {}
    for txn in transactions:
        txn_date = datetime.date.fromisoformat(txn["date"])
        if not (start <= txn_date <= end):
            continue
        if txn["amount"] <= 0:
            continue
        cat = txn["category"]
        totals[cat] = round(totals.get(cat, 0.0) + txn["amount"], 2)
    return dict(sorted(totals.items(), key=lambda x: x[1], reverse=True))


def detect_recurring_charges() -> list[dict]:
    """Find likely subscriptions: same merchant charged in 2+ distinct months
    at a similar amount (within 15% of the average).

    Returns candidates with estimated monthly cost, sorted most expensive first.
    """
    by_name: dict[str, list[dict]] = {}
    with open(_TRANSACTIONS_FILE, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            amount = float(row["amount"])
            if amount <= 0:
                continue  # only money going out can be a subscription
            key = row["name"].strip().lower()
            by_name.setdefault(key, []).append(
                {"date": row["date"], "name": row["name"], "amount": amount}
            )

    candidates = []
    for txns in by_name.values():
        months = {txn["date"][:7] for txn in txns}  # YYYY-MM
        if len(months) < 2:
            continue
        amounts = [txn["amount"] for txn in txns]
        avg = sum(amounts) / len(amounts)
        if any(abs(a - avg) > 0.15 * avg for a in amounts):
            continue  # amounts vary too much to look like a subscription
        candidates.append(
            {
                "name": txns[0]["name"],
                "estimated_monthly_cost": round(avg, 2),
                "months_seen": sorted(months),
                "occurrences": len(txns),
                "last_charged": max(txn["date"] for txn in txns),
            }
        )
    return sorted(candidates, key=lambda c: c["estimated_monthly_cost"], reverse=True)


def fetch_monthly_summary(year: int, month: int) -> dict:
    """Return income, expenses, and net for the given month."""
    _, last_day = calendar.monthrange(year, month)
    start = datetime.date(year, month, 1)
    end = datetime.date(year, month, last_day)
    days_back = (datetime.date.today() - start).days + 1
    transactions = fetch_transactions(max(days_back, 1))

    income = 0.0
    expenses = 0.0
    for txn in transactions:
        txn_date = datetime.date.fromisoformat(txn["date"])
        if not (start <= txn_date <= end):
            continue
        if txn["amount"] < 0:
            income += abs(txn["amount"])
        else:
            expenses += txn["amount"]

    return {
        "year": year,
        "month": month,
        "income": round(income, 2),
        "expenses": round(expenses, 2),
        "net": round(income - expenses, 2),
    }
