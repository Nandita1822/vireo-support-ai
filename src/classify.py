"""
Vireo Audio — rule-based ticket categorisation & team routing.

Deterministic, keyword/regex-based classifier applied to customer_message +
agent_notes. No paid API calls; fully reproducible on a clean machine.

Design notes (documented per task requirement to explain the taxonomy):
- Categories match the eleven themes already used by Vireo's intake bot
  (support-policy.pdf / README), because they already map cleanly onto the
  team-ownership definitions in support-policy.pdf section 6. We did not
  invent a new taxonomy — we kept the client's own category names and fixed
  HOW a ticket gets assigned to one, since the bot's assignment (from the
  customer's opening message only, at ticket creation) was shown by EDA to
  conflate "customer mentions having paid" with "this is a billing issue"
  even when the actual problem is non-delivery.
- Rules are applied in a fixed priority order (most specific/outcome-coded
  language first) so that a ticket mentioning several themes lands on the
  one that actually drove the resolution, based on how agents write closing
  notes (fairly consistent internal shorthand: "xfer", "rfnd", "chk", "fw").
- BILLING is deliberately narrowed to payment-mechanics language (duplicate
  charge, GST/invoice, coupon/price, EMI, payment gateway failure) rather
  than any mention of the word "paid" — this is the single change that
  matters most for the headcount question.
"""
import re
import pandas as pd

# Priority-ordered (category, compiled regex) pairs. First match wins.
RULES = [
    ("Warranty & Repair", re.compile(
        r"warranty|\brma\b|repair status|qc report|refurb|buyback|in-warranty|out of warranty",
        re.I)),
    ("Returns & Refunds", re.compile(
        r"\breturn\b|reverse pk?u?p|\bpkp\b|exchange the|refund (status|pending|not credited|reprocessed)|"
        r"rfnd (pending|not credited|reprocessed|status)|return accepted|return process|"
        r"waiting for (my |the )?refund|refund.{0,15}(nowhere|not (in|showing))",
        re.I)),
    ("Delivery & Shipping", re.compile(
        r"not delivered|not received|nobody.*(house|home)|never (arrived|showed up)|shipment|courier|\bawb\b|"
        r"tracking|\brto\b|dispatch|warehouse|re-?shipped|reship|delivery delay|"
        r"delivery address|address update|still (processing|says processing)|stuck (at|in) (transit|courier)|"
        r"lost in transit|wrong (variant|item|pincode|flat|address)|different (thing|variant|item)|"
        r"arrived damaged|damaged in transit|transit damage|\bdoa\b|dead on arrival|"
        r"wrong number|typo in the|moved houses|old flat|not what i (asked|ordered)",
        re.I)),
    ("Billing & Payments", re.compile(
        r"duplicate (payment|charge)|double payment|charged twice|deducted twice|payment deducted twice|"
        r"\bgst\b|\binvoice\b|\bcoupon\b|price (adjust|mismatch|wrong)|\bemi\b|payment (failed|gateway|error)|"
        r"wrong amount (charged|debited)|amount debited twice",
        re.I)),
    ("Connectivity", re.compile(
        r"pair(ing)?|bluetooth|discoverable|disconnect|connection drop|range issue",
        re.I)),
    ("Charging & Battery", re.compile(
        r"\bbatter(y|ies)|\bcharging\b|not charg(e|ing)|won.?t charge|no charge|\bbackup\b|\bdrain",
        re.I)),
    ("Audio Quality", re.compile(
        r"\baudio\b|\bsound\b|\bmic\b|distort|buzz|crackl|static|underwater|bass|noise cancel",
        re.I)),
    ("App & Firmware", re.compile(
        r"\bapp\b|firmware|\bfw\b|software|progress bar|bricked|update fail",
        re.I)),
    ("Account & Login", re.compile(
        r"login|\botp\b|password|sign.?in|account (locked|unlock)",
        re.I)),
    ("Product Enquiry", re.compile(
        r"before i buy|compatib|does (it|this) work with|spec sheet|before buy|\benquiry\b|"
        r"will (it|this) (talk|work|connect)",
        re.I)),
]

# support-policy.pdf section 6 ownership map (+ EDA-confirmed frontline/channel split)
CATEGORY_TEAM_MAP = {
    "Billing & Payments": "Billing",
    "Delivery & Shipping": "Logistics",
    "Returns & Refunds": "Returns Desk",
    "Warranty & Repair": "Escalations & Warranty",
}
FRONTLINE_BY_CHANNEL = {
    "chat": "Chat Frontline",
    "email": "Email Frontline",
    "voice": "Voice Frontline",
    "social": "Chat Frontline",  # per README/policy: social worked by Chat Frontline team
}


def classify_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return "Other"
    for cat, pattern in RULES:
        if pattern.search(text):
            return cat
    return "Other"


def classify_message_notes(message: str, notes: str) -> str:
    """The customer's opening message describes the ISSUE; agent_notes mixes
    the issue with downstream resolution steps (e.g. a warranty ticket that
    ends in "replacement dispatched" will otherwise false-match Delivery).
    So: classify the message first, and only fall back to the notes (with
    Delivery/Billing resolution-step words stripped out) if the message
    itself doesn't match any rule."""
    msg_cat = classify_text(message)
    if msg_cat != "Other":
        return msg_cat
    # fallback: strip common resolution/logistics-step boilerplate that
    # appears regardless of root cause, then classify what's left of notes
    stripped = re.sub(
        r"re-?shipped|reship(ped)?|dispatch(ed)?|warehouse|raised (with|w/) courier|"
        r"reverse pk?u?p|\bpkp\b",
        " ", str(notes) if isinstance(notes, str) else "", flags=re.I)
    return classify_text(stripped)


def predict_team(category: str, channel: str) -> str:
    if category in CATEGORY_TEAM_MAP:
        return CATEGORY_TEAM_MAP[category]
    return FRONTLINE_BY_CHANNEL.get(channel, "Chat Frontline")


def confidence(text: str, predicted_category: str) -> str:
    """Rough confidence: 'high' if exactly one rule category matched anywhere
    in the text, 'low' if 0 or 2+ distinct rule categories matched (i.e. the
    text is ambiguous/multi-topic and the priority order had to break a tie)."""
    if not isinstance(text, str) or not text.strip():
        return "low"
    hits = [cat for cat, pattern in RULES if pattern.search(text)]
    if len(hits) == 1:
        return "high"
    if len(hits) == 0:
        return "low"
    return "medium"  # multiple themes present; priority order picked the first


def classify_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Adds predicted_category, predicted_team, confidence columns."""
    df = df.copy()
    msg = df["customer_message"].fillna("")
    notes = df["agent_notes"].fillna("")
    combined = msg + " . " + notes
    df["predicted_category"] = [classify_message_notes(m, n) for m, n in zip(msg, notes)]
    df["predicted_team"] = [
        predict_team(cat, ch) for cat, ch in zip(df["predicted_category"], df["channel"])
    ]
    df["confidence"] = combined.apply(confidence, predicted_category=None)
    return df
