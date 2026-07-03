"""The categorization engine: decide (category, is_transfer) for a transaction.

Priority order:
  1. User-saved rules (rules.json) — the human is always right.
  2. Hard transfer signals (name rules, self-transfers).
  3. The export's own category via MONARCH_MAP.
  4. Merchant substring rules for uncategorized rows.
  5. Otherwise NEEDS_REVIEW — the coach will ask.
"""

import json
import pathlib

import taxonomy

_DATA_DIR = pathlib.Path(__file__).parent / "data"
RULES_FILE = _DATA_DIR / "rules.json"


def load_rules() -> list[dict]:
    """Learned rules: [{match, category, is_transfer}], match is a lowercase substring."""
    if not RULES_FILE.exists():
        return []
    try:
        return json.loads(RULES_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def add_rule(match: str, category: str, is_transfer: bool) -> dict:
    """Append (or update) a merchant rule and return it."""
    rules = load_rules()
    match = match.strip().lower()
    for rule in rules:
        if rule["match"] == match:
            rule.update(category=category, is_transfer=is_transfer)
            break
    else:
        rules.append({"match": match, "category": category, "is_transfer": is_transfer})
    _DATA_DIR.mkdir(exist_ok=True)
    RULES_FILE.write_text(json.dumps(rules, indent=2) + "\n", encoding="utf-8")
    return {"match": match, "category": category, "is_transfer": is_transfer}


def categorize(name: str, monarch_category: str, rules: list[dict] | None = None) -> dict:
    """Return {category, is_transfer, confidence} for one transaction.

    `rules` can be passed in to avoid re-reading rules.json per row.
    """
    if rules is None:
        rules = load_rules()
    n = name.lower()

    # 1. User-saved rules win.
    for rule in rules:
        if rule["match"] in n:
            return {"category": rule["category"], "is_transfer": rule["is_transfer"], "confidence": "high"}

    # 2. Hard transfer signals.
    for frag in taxonomy.TRANSFER_NAME_RULES:
        if frag in n:
            return {"category": taxonomy.TRANSFER_CATEGORY, "is_transfer": True, "confidence": "high"}
    if taxonomy.is_self_transfer(name):
        return {"category": taxonomy.TRANSFER_CATEGORY, "is_transfer": True, "confidence": "high"}

    # 3. Person-to-person payments: only the user knows what they were for.
    for frag in taxonomy.ASK_ALWAYS:
        if frag in n:
            return {"category": taxonomy.REVIEW, "is_transfer": False, "confidence": "low"}

    # 4. The export's own category.
    mapped = taxonomy.MONARCH_MAP.get(monarch_category, taxonomy.REVIEW)
    if mapped == taxonomy.TRANSFER_CATEGORY:
        return {"category": taxonomy.TRANSFER_CATEGORY, "is_transfer": True, "confidence": "high"}
    if mapped == taxonomy._SELF_CHECK:
        # Monarch called it an internal transfer, but it might be money from
        # another person. Only trust it if the name looks like a self-transfer.
        if taxonomy.is_self_transfer(name):
            return {"category": taxonomy.TRANSFER_CATEGORY, "is_transfer": True, "confidence": "high"}
        return {"category": taxonomy.REVIEW, "is_transfer": False, "confidence": "low"}
    if mapped not in (taxonomy.REVIEW,):
        return {"category": mapped, "is_transfer": False, "confidence": "high"}

    # 5. Merchant rules for the uncategorized.
    for frag, cat in taxonomy.MERCHANT_RULES.items():
        if frag in n:
            return {"category": cat, "is_transfer": False, "confidence": "medium"}

    return {"category": taxonomy.REVIEW, "is_transfer": False, "confidence": "low"}
