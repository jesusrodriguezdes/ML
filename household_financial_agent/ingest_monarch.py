"""Convert a raw Monarch/bank CSV export into the clean canonical dataset.

Reads   data/raw/monarch_export.csv
Writes  data/transactions.csv     (canonical, the app's source of truth)
        data/review_queue.csv      (merchant groups still needing a decision)

Re-runnable: it re-applies every saved rule in rules.json, so as the user
answers questions the review queue shrinks and nothing is ever re-asked.

Run:
    python household_financial_agent/ingest_monarch.py
"""

import collections
import csv
import pathlib

import categorize
import taxonomy

_DATA_DIR = pathlib.Path(__file__).parent / "data"
RAW_FILE = _DATA_DIR / "raw" / "monarch_export.csv"
OUT_FILE = _DATA_DIR / "transactions.csv"
QUEUE_FILE = _DATA_DIR / "review_queue.csv"

CANONICAL_FIELDS = ["date", "name", "amount", "category", "account", "is_transfer", "source_note"]


def _merchant(row: dict) -> str:
    """Best available human-readable merchant name."""
    return (row.get("Custom Name") or row.get("Name") or row.get("Description") or "").strip()


def _account(row: dict) -> str:
    inst = (row.get("Institution Name") or "").strip()
    num = (row.get("Account Number") or "").strip()
    return f"{inst} {num}".strip()


def ingest() -> dict:
    if not RAW_FILE.exists():
        raise SystemExit(f"Missing {RAW_FILE}. Put your Monarch export there and re-run.")

    rules = categorize.load_rules()
    raw_rows = list(csv.DictReader(open(RAW_FILE, encoding="utf-8")))

    out_rows = []
    conf_counts = collections.Counter()
    review_groups = collections.defaultdict(lambda: {"count": 0, "total": 0.0, "monarch": "", "match": ""})

    for row in raw_rows:
        name = _merchant(row)
        monarch_cat = (row.get("Category") or "").strip()
        try:
            amount = float(row.get("Amount") or 0)
        except ValueError:
            amount = 0.0

        result = categorize.categorize(name, monarch_cat, rules)
        conf_counts[result["confidence"]] += 1

        out_rows.append(
            {
                "date": (row.get("Date") or "").strip(),
                "name": name,
                "amount": amount,
                "category": result["category"],
                "account": _account(row),
                "is_transfer": str(result["is_transfer"]).lower(),
                "source_note": f"monarch:{monarch_cat}",
            }
        )

        if result["category"] == taxonomy.REVIEW:
            key = taxonomy.normalize_merchant(name)
            g = review_groups[key]
            g["count"] += 1
            g["total"] += amount
            g["monarch"] = monarch_cat
            g["match"] = key
            g.setdefault("example", name)

    OUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUT_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CANONICAL_FIELDS)
        writer.writeheader()
        writer.writerows(out_rows)

    # Aggregated review queue, biggest total first (most worth resolving).
    groups = sorted(review_groups.values(), key=lambda g: abs(g["total"]), reverse=True)
    with open(QUEUE_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["match", "example", "occurrences", "total_amount", "monarch_category"])
        for g in groups:
            writer.writerow([g["match"], g["example"], g["count"], round(g["total"], 2), g["monarch"]])

    transfers = sum(1 for r in out_rows if r["is_transfer"] == "true")
    needs_review = sum(1 for r in out_rows if r["category"] == taxonomy.REVIEW)
    return {
        "total": len(out_rows),
        "auto_categorized": len(out_rows) - needs_review,
        "transfers": transfers,
        "needs_review": needs_review,
        "review_groups": len(groups),
        "confidence": dict(conf_counts),
    }


def main() -> None:
    summary = ingest()
    print("Ingest complete.")
    print(f"  Total transactions:   {summary['total']}")
    print(f"  Auto-categorized:     {summary['auto_categorized']}")
    print(f"  Transfers excluded:   {summary['transfers']}")
    print(f"  Needs review:         {summary['needs_review']} "
          f"(in {summary['review_groups']} merchant groups)")
    print(f"  Confidence breakdown: {summary['confidence']}")
    print(f"\nWrote {OUT_FILE}")
    print(f"Wrote {QUEUE_FILE}")


if __name__ == "__main__":
    main()
