"""Long-term memory for the financial coach.

Four human-readable JSON files in data/ that persist between sessions:
    profile.json        who the user is: income, goals, personality, coaching notes
    budget.json         agreed category limits + method + rationale
    review_log.json     history of weekly reviews (list)
    subscriptions.json  recurring charges and keep/cancel decisions (list)

The agent reads and writes these through tools; the user can also open them
in any text editor to see or correct what the agent knows.
"""

import json
import pathlib

_DATA_DIR = pathlib.Path(__file__).parent / "data"

PROFILE_FILE = _DATA_DIR / "profile.json"
BUDGET_FILE = _DATA_DIR / "budget.json"
REVIEW_LOG_FILE = _DATA_DIR / "review_log.json"
SUBSCRIPTIONS_FILE = _DATA_DIR / "subscriptions.json"


def _load(path: pathlib.Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default


def _save(path: pathlib.Path, data) -> None:
    _DATA_DIR.mkdir(exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_profile() -> dict:
    return _load(PROFILE_FILE, {})


def save_profile(profile: dict) -> None:
    _save(PROFILE_FILE, profile)


def load_budget() -> dict:
    return _load(BUDGET_FILE, {})


def save_budget(budget: dict) -> None:
    _save(BUDGET_FILE, budget)


def load_review_log() -> list:
    return _load(REVIEW_LOG_FILE, [])


def append_review(entry: dict) -> None:
    log = load_review_log()
    log.append(entry)
    _save(REVIEW_LOG_FILE, log)


def load_subscriptions() -> list:
    return _load(SUBSCRIPTIONS_FILE, [])


def save_subscriptions(subscriptions: list) -> None:
    _save(SUBSCRIPTIONS_FILE, subscriptions)
