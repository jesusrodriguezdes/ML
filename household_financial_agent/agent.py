"""Household financial planning agent.

Interactive CLI that uses Claude to answer natural-language budget questions.
Financial data is read from local CSV files you can edit in Excel or Google Sheets.

Required env vars (in .env):
    ANTHROPIC_API_KEY

Data files to fill in with your numbers:
    household_financial_agent/data/accounts.csv
    household_financial_agent/data/transactions.csv

Run:
    python household_financial_agent/agent.py
"""

import pathlib

import anthropic
from dotenv import load_dotenv

load_dotenv()

from tools import TOOL_DEFINITIONS, dispatch

MODEL = "claude-opus-4-8"
SYSTEM = (
    "You are a household financial assistant. "
    "Always use the provided tools to retrieve real financial data before answering — "
    "never guess or invent numbers. "
    "Be concise and precise. Format all currency as USD with two decimal places."
)

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


def ask(question: str) -> str:
    """Send a question through the agentic loop and return the final text response."""
    messages = [{"role": "user", "content": question}]

    for _ in range(10):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        # Append the full assistant turn before dispatching tools or returning.
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "end_turn":
            break

        if resp.stop_reason == "tool_use":
            # Collect ALL tool_use blocks from this turn and return them together
            # in a single user message — required by the Anthropic API.
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

        # pause_turn or unexpected stop reason — let Claude continue
        break

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

    print("Household Financial Agent. Type 'quit' to exit.\n")
    while True:
        try:
            question = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if question.lower() in {"quit", "exit", "q"}:
            break
        if not question:
            continue
        print(f"\nAgent: {ask(question)}\n")


if __name__ == "__main__":
    main()
