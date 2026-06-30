"""Claude tool definitions and dispatcher for the financial agent."""

import json

from csv_client import (
    fetch_account_balances,
    fetch_monthly_summary,
    fetch_spending_by_category,
    fetch_transactions,
)

TOOL_DEFINITIONS = [
    {
        "name": "get_account_balances",
        "description": "Retrieve current balances for all linked bank and credit accounts.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
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
]


def dispatch(tool_name: str, tool_input: dict) -> str:
    """Call the appropriate plaid_client function and return a JSON string."""
    if tool_name == "get_account_balances":
        result = fetch_account_balances()
    elif tool_name == "get_recent_transactions":
        result = fetch_transactions(days=tool_input["days"])
    elif tool_name == "get_spending_by_category":
        result = fetch_spending_by_category(tool_input["year"], tool_input["month"])
    elif tool_name == "get_monthly_summary":
        result = fetch_monthly_summary(tool_input["year"], tool_input["month"])
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
    return json.dumps(result, default=str)
