"""Cheap-model bulk classifier for the transaction review queue.

Model routing in action: a fast, inexpensive model (Haiku) tags the obvious
leftover merchants so the expensive coach only has to discuss the genuinely
ambiguous ones (Venmo/Zelle to people, self-transfers, mystery ACH).

Run it between ingest and the agent:
    python household_financial_agent/ingest_monarch.py   # free rules pass
    python household_financial_agent/classify.py          # cheap model pass
    python household_financial_agent/agent.py             # expensive coach

Re-runnable and safe: it only touches rows still marked NEEDS_REVIEW.
"""

import json
import os
import re

import anthropic
from dotenv import load_dotenv

load_dotenv()

import taxonomy
from tools import get_review_queue, resolve_transactions

CLASSIFIER_MODEL = os.environ.get("CLASSIFIER_MODEL", "claude-haiku-4-5-20251001")

_PROMPT = """You classify bank transactions into budgeting categories.

Valid categories (use these names EXACTLY):
{categories}

For each merchant below, choose the best category. Rules:
- Only classify when you are confident from the merchant name.
- Return "ASK_USER" (do NOT guess) for any of these:
  - person-to-person payments: Venmo, PayPal to a person, "Zelle payment to/from <a person>"
  - money the user moved between their own accounts (mark is_transfer true only if certain)
  - anything ambiguous or that you don't recognize
- A clear store/service (groceries, restaurants, software, gas, etc.) should get its category.

Return ONLY a JSON array, one object per merchant, no prose:
[{{"match": "<match string, copied exactly>", "category": "<a category above or ASK_USER>", "is_transfer": false}}]

Merchants (match | example | count | total_dollars):
{merchants}
"""


def _extract_json(text: str):
    """Pull a JSON array out of the model reply, tolerating code fences/prose."""
    fenced = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", text, re.S)
    raw = fenced.group(1) if fenced else None
    if raw is None:
        start, end = text.find("["), text.rfind("]")
        raw = text[start : end + 1] if start != -1 and end != -1 else "[]"
    return json.loads(raw)


def classify() -> dict:
    queue = get_review_queue(limit=1000)
    groups = queue["batch"]
    if not groups:
        return {"classified": 0, "escalated": 0, "remaining": 0, "note": "nothing to classify"}

    client = anthropic.Anthropic()
    categories = "\n".join(f"- {c}" for c in taxonomy.EXPENSE_CATEGORIES + [taxonomy.INCOME_CATEGORY])
    merchants = "\n".join(
        f'{g["match"]} | {g["example"][:40]} | {g["occurrences"]} | {g["total"]}' for g in groups
    )

    resp = client.messages.create(
        model=CLASSIFIER_MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": _PROMPT.format(categories=categories, merchants=merchants)}],
    )
    text = "".join(b.text for b in resp.content if hasattr(b, "text"))
    items = _extract_json(text)

    valid = set(taxonomy.EXPENSE_CATEGORIES) | {taxonomy.INCOME_CATEGORY, taxonomy.TRANSFER_CATEGORY}
    classified = 0
    escalated = 0
    for item in items:
        match = str(item.get("match", "")).strip()
        category = str(item.get("category", "")).strip()
        if not match or category == "ASK_USER" or category not in valid:
            escalated += 1
            continue
        resolve_transactions(match, category, bool(item.get("is_transfer", False)))
        classified += 1

    remaining = get_review_queue(limit=1000)["remaining_groups"]
    return {"classified": classified, "escalated": escalated, "remaining": remaining}


def main() -> None:
    print(f"Classifying with {CLASSIFIER_MODEL} ...")
    r = classify()
    if r.get("note"):
        print(r["note"])
        return
    print(f"  Auto-classified: {r['classified']} merchant groups")
    print(f"  Left for you:    {r['remaining']} groups still need your judgment "
          f"(mostly person-to-person payments and transfers)")
    print("\nRun 'python household_financial_agent/agent.py' to finish the rest with the coach.")


if __name__ == "__main__":
    main()
