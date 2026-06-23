"""Daily topic-briefing agent.

Reads topics from topics.txt, has Claude research each one with its built-in web
search tool, and sends a single Markdown digest to a Telegram chat.

Required environment variables:
    ANTHROPIC_API_KEY    Anthropic API key
    TELEGRAM_BOT_TOKEN   Token from @BotFather
    TELEGRAM_CHAT_ID     Your chat id (numeric)

Run locally:
    pip install -r daily_brief/requirements.txt
    python daily_brief/brief.py
"""

import datetime
import os
import pathlib

import anthropic
import requests

MODEL = "claude-opus-4-8"
TOPICS_FILE = pathlib.Path(__file__).with_name("topics.txt")
TELEGRAM_LIMIT = 4096  # Telegram's per-message character cap

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment


def read_topics() -> list[str]:
    """Return non-empty, non-comment lines from topics.txt."""
    lines = TOPICS_FILE.read_text(encoding="utf-8").splitlines()
    return [s.strip() for s in lines if s.strip() and not s.startswith("#")]


def research(topic: str) -> str:
    """Research one topic via Claude + web search; return a short briefing."""
    messages = [
        {
            "role": "user",
            "content": (
                f"Research the latest news on: {topic}. "
                "Give 3-5 short bullets covering only developments from roughly "
                "the last 1-2 days. End each bullet with its source URL. "
                "If there is nothing notable, say so in a single line."
            ),
        }
    ]
    tools = [{"type": "web_search_20260209", "name": "web_search"}]

    resp = None
    # The web search tool runs a server-side loop; if it hits its iteration cap
    # it returns stop_reason "pause_turn" and we re-send to let it continue.
    for _ in range(5):
        resp = client.messages.create(
            model=MODEL,
            max_tokens=1500,
            system="You are a concise news briefer. Be factual and brief.",
            tools=tools,
            messages=messages,
        )
        if resp.stop_reason != "pause_turn":
            break
        messages.append({"role": "assistant", "content": resp.content})

    text = "".join(b.text for b in resp.content if b.type == "text").strip()
    return text or "(no summary produced)"


def send_telegram(text: str) -> None:
    """Send text to Telegram, splitting into chunks under the size limit."""
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    chunk = TELEGRAM_LIMIT - 96  # leave headroom

    for start in range(0, len(text), chunk):
        part = text[start : start + chunk]
        r = requests.post(
            url,
            json={"chat_id": chat_id, "text": part, "parse_mode": "Markdown"},
            timeout=30,
        )
        # If Markdown parsing fails on a stray character, retry as plain text.
        if r.status_code == 400:
            r = requests.post(
                url, json={"chat_id": chat_id, "text": part}, timeout=30
            )
        r.raise_for_status()


def main() -> None:
    topics = read_topics()
    if not topics:
        print("No topics in topics.txt — nothing to do.")
        return

    today = datetime.date.today().isoformat()
    parts = [f"*Daily brief — {today}*", ""]
    for topic in topics:
        print(f"Researching: {topic}")
        parts.append(f"*{topic}*")
        parts.append(research(topic))
        parts.append("")

    send_telegram("\n".join(parts))
    print(f"Sent brief covering {len(topics)} topic(s).")


if __name__ == "__main__":
    main()
