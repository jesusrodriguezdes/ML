"""Household financial coach agent.

Interactive CLI that helps you build a budget, stay within it, cut wasted
spending, and hit your savings goals. Data comes from local CSV files you
can edit in Excel or Google Sheets; what the agent learns about you is
stored in human-readable JSON files in data/.

Required env vars (in .env):
    ANTHROPIC_API_KEY

Data files to fill in with your numbers:
    household_financial_agent/data/accounts.csv
    household_financial_agent/data/transactions.csv

Run:
    python household_financial_agent/agent.py
"""

import datetime
import json
import pathlib

import anthropic
from dotenv import load_dotenv

load_dotenv()

import memory
from tools import TOOL_DEFINITIONS, dispatch

MODEL = "claude-opus-4-8"
MAX_TOKENS = 4000
MAX_TOOL_ITERATIONS = 15

COACH_PROMPT = """\
You are a personal household financial coach. Your job is not to display data — \
it is to help the user hit their financial goals, starting with staying within budget.

## Ground rules
- Always retrieve real data with tools before making any claim about the user's \
finances. Never guess or invent numbers. All math on budgets comes from \
get_budget_status, not your own arithmetic.
- Format currency as USD with two decimal places.
- Never shame the user about spending. Curiosity, not judgment.
- Adapt your tone to the motivation_style in the user's profile (encouragement, \
hard numbers, streaks/gamification). If no profile exists yet, be warm and plain.
- Ask ONE question at a time in interviews. Waiting for an answer beats a questionnaire.
- Persist anything worth remembering: profile changes via save_profile, budget \
changes via save_budget, completed reviews via log_weekly_review. If the user \
tells you something durable about their life (rent change, new goal, new job), \
update the profile before the conversation moves on.
- Amounts in transactions: positive = money out (expense), negative = money in (income).

## Flow 1 — Onboarding interview (when get_profile returns empty)
Introduce yourself briefly, then interview the user one question at a time:
1. Income: how much per month, and is it fixed or variable?
2. Savings goals: what are they saving for, how much, by when? (Push gently for \
concrete numbers and dates.)
3. Money personality: do they enjoy tracking details, or do they want this \
hands-off?
4. Motivation: what keeps them going — encouragement, cold hard numbers, or \
streaks and challenges?
Then analyze their recent transactions (get_recent_transactions for ~90 days, \
get_spending_by_category and get_monthly_summary for the last 2-3 months). \
Based on the interview AND the data, choose the budgeting method that fits them:
- data-driven + goals: limits based on actual spending, trimmed to hit the savings \
goal (best default for most people)
- 50/30/20: needs/wants/savings buckets (good for hands-off personalities)
- zero-based: every dollar assigned (only for detail-lovers with stable income)
Explain WHY you chose it in one short paragraph. Propose per-category monthly \
limits grounded in their real spending — realistic, not aspirational. Negotiate \
until they agree, then save_profile and save_budget.

## Flow 2 — Weekly review (user asks, or you offer when one is overdue)
1. get_budget_status for the current month, get_review_history for trends, \
get_recent_transactions for the past week.
2. Lead with wins — what went well since last review.
3. Flag risks: categories trending over budget given days left in the month, \
upcoming known charges, patterns repeating from past reviews ("third week in a \
row over on Food and Drink").
4. Check on commitments from the previous review — kept or not, no judgment.
5. End with 1-2 concrete, small commitments for the coming week that the user \
explicitly agrees to.
6. log_weekly_review with the full entry, and append any new behavioral \
observation to coaching_notes via save_profile.

## Flow 3 — Subscription audit (on request)
1. detect_recurring_charges to find candidates; get_subscriptions for past decisions.
2. For each candidate, one at a time: do they recognize it? How often do they \
actually use it? Does it serve one of their savings goals or values?
3. Compute cost-per-use from their answer (monthly cost / uses per month).
4. Group overlapping services (multiple streaming, multiple cloud storage, \
gym + fitness app) and recommend keeping the best one per group.
5. Recommend keep / cancel / downgrade for each, using: cost-per-use, goal \
alignment, overlap, and whether it was a forgotten charge. Total the monthly \
and yearly savings if they follow through.
6. save_subscriptions with every decision.

## Otherwise
Answer ad-hoc questions (balances, spending, "can I afford X?") with tool data, \
always connecting the answer back to their budget and goals when one exists.
"""


client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


def build_system_prompt() -> str:
    """Coach prompt + today's date + everything we remember about the user."""
    parts = [COACH_PROMPT, f"\nToday's date: {datetime.date.today().isoformat()}"]

    profile = memory.load_profile()
    if profile:
        parts.append(
            "\n## What you remember about this user (from profile.json)\n"
            + json.dumps(profile, indent=2, ensure_ascii=False)
        )
        reviews = memory.load_review_log()
        if reviews:
            last = reviews[-1].get("date", "unknown")
            parts.append(f"\nLast weekly review: {last} ({len(reviews)} total reviews on record).")
        else:
            parts.append("\nNo weekly reviews on record yet.")
    else:
        parts.append(
            "\nNo profile exists yet — this is a brand-new user. "
            "Start with the onboarding interview (Flow 1)."
        )
    return "\n".join(parts)


def run_turn(messages: list, system_prompt: str) -> str:
    """Run one agentic turn: call the model, dispatch tools until it stops."""
    for _ in range(MAX_TOOL_ITERATIONS):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS,
            system=system_prompt,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "tool_use":
            tool_results = []
            for block in resp.content:
                if block.type == "tool_use":
                    output = dispatch(block.name, block.input)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": output,
                        }
                    )
            messages.append({"role": "user", "content": tool_results})
            continue

        break  # end_turn or anything else — hand back to the user

    text_blocks = [b.text for b in resp.content if hasattr(b, "text")]
    return "\n".join(text_blocks).strip() or "(no response)"


def main() -> None:
    load_dotenv()

    data_dir = pathlib.Path(__file__).parent / "data"
    missing = [f for f in ("transactions.csv", "accounts.csv") if not (data_dir / f).exists()]
    if missing:
        print(
            f"Missing data file(s): {', '.join(missing)}\n"
            "Open the files in household_financial_agent/data/ and add your numbers.\n"
            "You can edit them in Excel, Google Sheets, or any text editor."
        )
        return

    system_prompt = build_system_prompt()

    # One messages list for the whole session so the agent remembers the
    # entire conversation, not just the last question.
    messages = [
        {
            "role": "user",
            "content": (
                "[The user just opened the app. Greet them appropriately: run the "
                "onboarding interview if they have no profile; otherwise give a "
                "one-paragraph status check-in — how this month is tracking against "
                "budget — and offer a weekly review if one is overdue. Use tools first.]"
            ),
        }
    ]
    print("Household Financial Coach. Type 'quit' to exit.\n")
    print(f"Coach: {run_turn(messages, system_prompt)}\n")

    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if question.lower() in {"quit", "exit", "q"}:
            print("Bye.")
            break
        if not question:
            continue
        messages.append({"role": "user", "content": question})
        print(f"\nCoach: {run_turn(messages, system_prompt)}\n")


if __name__ == "__main__":
    main()
