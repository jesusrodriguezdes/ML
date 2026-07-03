"""Canonical spending taxonomy and the rules that map raw bank data onto it.

The bank export already carries a category on ~97% of rows, so the primary
signal is MONARCH_MAP (existing category -> clean canonical category). Transfer
detection and a small set of merchant rules handle the rest. Anything left
unresolved becomes NEEDS_REVIEW and is driven to zero by the coach in chat.
"""

# ---- The clean category set -------------------------------------------------

# Real spending — counted in the budget.
EXPENSE_CATEGORIES = [
    "Groceries",
    "Dining & Drinks",
    "Shopping",
    "Entertainment & Recreation",
    "Bills & Utilities",
    "Auto & Transport",
    "Housing",
    "Health & Medical",
    "Personal Care",
    "Home & Garden",
    "Pets",
    "Travel & Vacation",
    "Software & Subscriptions",
    "Education",
    "Fees & Charges",
    "Taxes",
    "Charitable Donations",
    "Loan Payment",
]

# Money coming in — tracked, but not spending.
INCOME_CATEGORY = "Income"

# Money moving between the user's own accounts — excluded from all analysis.
TRANSFER_CATEGORY = "Transfer"

# Placeholder until a human (or a saved rule) decides.
REVIEW = "NEEDS_REVIEW"

CANONICAL_CATEGORIES = EXPENSE_CATEGORIES + [INCOME_CATEGORY, TRANSFER_CATEGORY]

# ---- Mapping the export's existing categories onto the canonical set --------

# Sentinels for categories that can't be trusted at face value.
_SELF_CHECK = "__SELF_CHECK__"  # transfer if it's the user moving own money, else review

MONARCH_MAP = {
    "Dining & Drinks": "Dining & Drinks",
    "Shopping": "Shopping",
    "Groceries": "Groceries",
    "Income": INCOME_CATEGORY,
    "Entertainment & Rec.": "Entertainment & Recreation",
    "Auto & Transport": "Auto & Transport",
    "Bills & Utilities": "Bills & Utilities",
    "Health & Wellness": "Health & Medical",
    "Medical": "Health & Medical",
    "Loan Payment": "Loan Payment",
    "Home & Garden": "Home & Garden",
    "Home & kitchen": "Home & Garden",
    "Fees": "Fees & Charges",
    "Legal": "Fees & Charges",
    "Pets": "Pets",
    "Travel & Vacation": "Travel & Vacation",
    "Software & Tech": "Software & Subscriptions",
    "Personal Care": "Personal Care",
    "Fishing": "Entertainment & Recreation",
    "Education": "Education",
    "Charitable Donations": "Charitable Donations",
    "Taxes": "Taxes",
    # Always a transfer between own accounts:
    "Credit Card Payment": TRANSFER_CATEGORY,
    "Investment": TRANSFER_CATEGORY,
    # Can't be trusted at face value — decide per-transaction:
    "Internal Transfers": _SELF_CHECK,  # mix of self-transfers and money from other people
    "Cash & Checks": REVIEW,            # ATM / checks — could be spending or transfer
    "Uncategorized": REVIEW,
    "": REVIEW,
}

# ---- Self-transfer detection ------------------------------------------------

# The account holder's own name. A Zelle/transfer naming the user is money
# moving between his own banks (Chase <-> Wells Fargo), not a real expense.
def is_self_transfer(name: str) -> bool:
    n = name.lower()
    if "zelle to jesus" in n or "zelle payment to jesus" in n:
        return True
    if "jesus" in n and "rodriguez" in n:
        return True
    return False

# Raw-name substrings that always indicate a transfer, whatever the category.
TRANSFER_NAME_RULES = [
    "automatic payment - thank",   # payment received on a credit card
    "credit crd autopay",
    "online/mobile recurring from chk",
    "online scheduled payment to acct",
]

# ---- Merchant rules for the genuinely uncategorized -------------------------

# Substring (lowercased) -> canonical category. Kept small on purpose; most
# rows are handled by MONARCH_MAP, and unknown merchants go to review so the
# user is asked (and the answer is saved as a rule).
MERCHANT_RULES: dict[str, str] = {
    # left intentionally small; grows via user answers saved to rules.json
}

# Merchant substrings that should always be asked about (person-to-person),
# never auto-categorized, because only the user knows what they were for.
# NOTE: PayPal/Venmo to a real store (e.g. "PAYPAL INST XFER CHEWY INC") is a
# purchase, so we only force review for Zelle and bare Venmo; PayPal falls
# through to normal category mapping unless it names a person.
ASK_ALWAYS = ["venmo", "zelle payment to", "zelle payment from", "zelle to jesus"]


# ---- Merchant-name normalization -------------------------------------------

import re

# Everything from these markers onward is a confirmation/reference tail.
_CUT_MARKERS = [" conf#", " conf #", " ref #", " ref#", " id:", " date:", " time:",
                " indn:", " co id:", " ppd id:", " web id:", " des:"]
_LONG_TOKEN = re.compile(r"\b(?=\w*\d)\w{6,}\b")  # 6+ char tokens containing a digit


def normalize_merchant(name: str) -> str:
    """Collapse a raw transaction name to a stable merchant key.

    Strips confirmation numbers, reference IDs, and trailing account codes so
    that "Zelle payment to Wife Conf# abc" and "...Conf# xyz" group together.
    """
    n = name.lower().strip()
    for marker in _CUT_MARKERS:
        idx = n.find(marker)
        if idx != -1:
            n = n[:idx]
    n = re.sub(r"\b\d{1,2}/\d{1,2}(?:/\d{2,4})?\b", "", n)  # dates like 03/28
    n = _LONG_TOKEN.sub("", n)          # drop stray ref codes like 29673236809
    n = re.sub(r"\s+", " ", n).strip(" -#*")
    return n
