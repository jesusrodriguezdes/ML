"""Plaid API wrapper — thin layer over the Plaid Python SDK.

Required env vars (loaded from .env by callers):
    PLAID_CLIENT_ID
    PLAID_SECRET
    PLAID_ENV        sandbox | development | production
    PLAID_ACCESS_TOKEN
"""

import datetime
import os

import plaid
from plaid.api import plaid_api
from plaid.model.accounts_balance_get_request import AccountsBalanceGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions


_ENV_MAP = {
    "sandbox": plaid.Environment.Sandbox,
    "development": plaid.Environment.Development,
    "production": plaid.Environment.Production,
}


def _client() -> plaid_api.PlaidApi:
    configuration = plaid.Configuration(
        host=_ENV_MAP[os.environ["PLAID_ENV"]],
        api_key={
            "clientId": os.environ["PLAID_CLIENT_ID"],
            "secret": os.environ["PLAID_SECRET"],
        },
    )
    return plaid_api.PlaidApi(plaid.ApiClient(configuration))


def fetch_account_balances() -> list[dict]:
    """Return current balances for all linked accounts."""
    client = _client()
    access_token = os.environ["PLAID_ACCESS_TOKEN"]
    response = client.accounts_balance_get(
        AccountsBalanceGetRequest(access_token=access_token)
    )
    accounts = []
    for acct in response["accounts"]:
        balances = acct["balances"]
        accounts.append(
            {
                "name": acct["name"],
                "type": acct["type"].value if hasattr(acct["type"], "value") else str(acct["type"]),
                "subtype": acct["subtype"].value if acct.get("subtype") and hasattr(acct["subtype"], "value") else str(acct.get("subtype", "")),
                "current_balance": balances.get("current"),
                "available_balance": balances.get("available"),
                "currency": balances.get("iso_currency_code", "USD"),
            }
        )
    return accounts


def fetch_transactions(days: int) -> list[dict]:
    """Return transactions from the past `days` days, handling Plaid pagination."""
    client = _client()
    access_token = os.environ["PLAID_ACCESS_TOKEN"]
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days)

    transactions = []
    offset = 0

    while True:
        response = client.transactions_get(
            TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                options=TransactionsGetRequestOptions(offset=offset, count=500),
            )
        )
        batch = response["transactions"]
        transactions.extend(batch)
        if len(transactions) >= response["total_transactions"] or not batch:
            break
        offset += len(batch)

    result = []
    for txn in transactions:
        raw_cat = txn.get("category") or []
        result.append(
            {
                "date": str(txn["date"]),
                "name": txn["name"],
                "amount": txn["amount"],  # positive = debit, negative = credit
                "category": raw_cat[0] if raw_cat else "Uncategorized",
                "account_id": txn["account_id"],
            }
        )
    return result


def fetch_spending_by_category(year: int, month: int) -> dict[str, float]:
    """Return total spending per top-level category for the given month.

    Only positive amounts (debits/purchases) are included.
    """
    import calendar

    _, last_day = calendar.monthrange(year, month)
    start = datetime.date(year, month, 1)
    end = datetime.date(year, month, last_day)
    days = (end - datetime.date.today()).days
    # Fetch enough days to cover the full requested month
    days_back = (datetime.date.today() - start).days + 1
    transactions = fetch_transactions(max(days_back, 1))

    totals: dict[str, float] = {}
    for txn in transactions:
        txn_date = datetime.date.fromisoformat(txn["date"])
        if not (start <= txn_date <= end):
            continue
        if txn["amount"] <= 0:
            continue  # skip credits/income
        cat = txn["category"]
        totals[cat] = round(totals.get(cat, 0.0) + txn["amount"], 2)
    return dict(sorted(totals.items(), key=lambda x: x[1], reverse=True))


def fetch_monthly_summary(year: int, month: int) -> dict:
    """Return income, expenses, and net for the given month.

    Plaid sign convention: positive amount = money leaving (expense),
    negative amount = money entering (income).
    """
    import calendar

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
