"""Fast batch review: answer everything first, then ONE cheap model call.

Instead of cleaning up transactions by chatting with the expensive coach one
merchant at a time (dozens of large API calls), this:
  1. Finds every remaining unknown (no API).
  2. Asks you about each one in the terminal — you just type what it was for.
     Collecting your answers costs nothing (it's all local, no tokens, no wait).
  3. Makes a SINGLE cheap-model call to turn all your answers into categories.
  4. Applies them and saves the rules.

Run it after classify.py:
    python household_financial_agent/review.py
"""

import os

import anthropic
from dotenv import load_dotenv

load_dotenv()

import taxonomy
from classify import _extract_json
from tools import get_review_queue, resolve_transactions

CLASSIFIER_MODEL = os.environ.get("CLASSIFIER_MODEL", "claude-haiku-4-5-20251001")

_INTERPRET_PROMPT = """The user explained what each transaction was for. Map each line to one category.

Valid categories (use these EXACT names):
{categories}
Also allowed: "Transfer" — money the user moved between their OWN accounts; set is_transfer true for these.

Guidance:
- "moved my own money", their own name, own savings/checking -> Transfer (is_transfer true).
- Money they RECEIVED that is real income/rent/pay -> Income. A reimbursement they got back -> Transfer.
- Otherwise choose the expense category that matches their explanation.

Return ONLY a JSON array, one object per line, no prose:
[{{"match": "<match copied exactly>", "category": "<a category above>", "is_transfer": false}}]

Lines (match ||| direction ||| user_explanation):
{lines}
"""


def interpret_and_apply(answers: list[dict]) -> dict:
    """One model call: turn free-text answers into applied categories."""
    client = anthropic.Anthropic()
    categories = "\n".join(f"- {c}" for c in taxonomy.EXPENSE_CATEGORIES + [taxonomy.INCOME_CATEGORY])
    lines = "\n".join(
        f'{a["match"]} ||| {"received" if a["total"] < 0 else "spent"} ||| {a["answer"]}'
        for a in answers
    )
    resp = client.messages.create(
        model=CLASSIFIER_MODEL,
        max_tokens=4000,
        messages=[{"role": "user", "content": _INTERPRET_PROMPT.format(categories=categories, lines=lines)}],
    )
    text = "".join(b.text for b in resp.content if hasattr(b, "text"))
    items = _extract_json(text)

    valid = set(taxonomy.EXPENSE_CATEGORIES) | {taxonomy.INCOME_CATEGORY, taxonomy.TRANSFER_CATEGORY}
    applied = 0
    unmapped = []
    for item in items:
        match = str(item.get("match", "")).strip()
        category = str(item.get("category", "")).strip()
        if match and category in valid:
            resolve_transactions(match, category, bool(item.get("is_transfer", False)))
            applied += 1
        else:
            unmapped.append(match or category)
    return {"applied": applied, "unmapped": unmapped}


def main() -> None:
    groups = get_review_queue(limit=1000)["batch"]
    if not groups:
        print("Nothing left to review — you're all caught up!")
        return

    print(f"{len(groups)} things need your input. I'll ask about each one, then")
    print("categorize them all in a single quick step.\n")
    print("Just say what it was for — e.g. 'dinner with friends', 'rent to my wife',")
    print("'moving my own money between banks', 'paying a contractor', 'my paycheck'.")
    print("Press Enter to skip one (it'll stay for later). Ctrl+C to stop and apply.\n")

    answers = []
    for i, g in enumerate(groups, 1):
        direction = "received" if g["total"] < 0 else "spent"
        try:
            ans = input(
                f"[{i}/{len(groups)}] {g['example'][:50]} "
                f"({g['occurrences']}x, ${abs(g['total']):,.2f} {direction}): "
            ).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nStopping here — applying what you've answered so far.")
            break
        if ans:
            answers.append({"match": g["match"], "total": g["total"], "answer": ans})

    if not answers:
        print("\nNo answers given — nothing to apply.")
        return

    print(f"\nGot {len(answers)} answers. Making ONE call to categorize them all...")
    result = interpret_and_apply(answers)
    print(f"Done — categorized {result['applied']} of {len(answers)}.")
    if result["unmapped"]:
        print(f"(Couldn't map {len(result['unmapped'])}; they stay in the queue.)")

    remaining = get_review_queue(limit=1000)["remaining_groups"]
    print(f"\n{remaining} merchant groups still unresolved.")
    if remaining == 0:
        print("Everything is categorized. Run agent.py to start budgeting!")


if __name__ == "__main__":
    main()
