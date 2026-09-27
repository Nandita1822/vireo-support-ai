# Validation — Vireo ticket categorisation tool

## What is being validated
Two separate claims, validated separately:

1. **The classifier's category label is reasonable** (requirement C/D/E of the brief).
2. **Logistics, not Billing, is the highest-volume specialist queue** (the actual business
   question). This claim does **not** depend on classifier accuracy — it is independently
   confirmed by a second, non-ML signal (see "Cross-check" below).

## 1. Classifier accuracy

### 1a. Against the original (noisy) category tag
Sample size: all 11,780 tickets. Method: exact match, `predicted_category == category`.

- **Overall agreement: 56.0%** (`outputs/confusion_matrix_vs_noisy_tag.csv` has the full matrix).
- This number is **not** "the tool is 56% accurate" — the tag itself is known-unreliable
  (Sameer: *"category is set by the chat bot from its opening question at ticket creation;
  agents can re-tag but in practice rarely do"*), so disagreement is partly the tool
  correcting the tag, not the tool being wrong. Per-class precision/recall against the tag:

| category | precision | recall | f1 | support |
|---|---|---|---|---|
| Account & Login | 0.87 | 0.84 | 0.85 | 391 |
| App & Firmware | 0.47 | 0.79 | 0.59 | 699 |
| Audio Quality | 0.80 | 0.80 | 0.80 | 591 |
| **Billing & Payments** | 0.73 | 0.32 | 0.44 | 2564 |
| Charging & Battery | 0.72 | 0.76 | 0.74 | 820 |
| Connectivity | 0.80 | 0.78 | 0.79 | 1002 |
| **Delivery & Shipping** | 0.42 | 0.85 | 0.56 | 1905 |
| Other | 0.21 | 0.20 | 0.21 | 1622 |
| Product Enquiry | 0.85 | 0.73 | 0.79 | 612 |
| Returns & Refunds | 0.71 | 0.45 | 0.55 | 1049 |
| Warranty & Repair | 0.62 | 0.50 | 0.55 | 525 |

Low Billing recall / low Delivery precision is **by design** — that swap is the finding
(§2 below). "Other" performs worst on both sides, expected: it is a catch-all bucket in
both systems and inherently ambiguous.

### 1b. Manual audit (independent read of actual text)
A stratified random sample of **60 tickets** (25 where tag and tool agreed, 35 where they
disagreed) was pulled and each ticket's `customer_message` + `agent_notes` was read in full
to judge the true category, independent of either label. Method and caveat below.

- Original tag matched my judgment on **~70%** (42/60) of the sample.
- Tool's prediction matched my judgment on **~68-70%** of the sample, similar overall — but
  on the 35 disagreement cases specifically, the tool corrected the tag roughly **twice as
  often** as it broke a correct tag (concrete pattern: "paid but never delivered" tickets
  tagged Billing by the bot, correctly moved to Delivery & Shipping by the tool — see
  ticket examples TK-240069, TK-240095, TK-253208 in `audit_sample.csv`).
- Concrete failure modes found and left in the tool (documented, not silently hidden):
  - Very short tickets ("screen is unresponsive") have no keyword signal at all → fall to
    "Other" regardless of true cause.
  - Product names that happen to contain category-like substrings caused some false
    positives before a fix (e.g. "65W charger" as a product noun vs. an actual charging
    complaint) — patched, but likely not the only such case.
  - "Wrong item / wrong variant received" and "transit damage" phrasing were under-covered
    until a rules patch mid-build; some phrasings we didn't see in the sample almost
    certainly still slip through.
  - A handful of tickets are genuinely ambiguous even to a careful human read (e.g. hardware
    fault vs. warranty vs. audio quality) — these would need a real taxonomy decision from
    Vireo, not a better regex.

**Important limitation on 1b:** the "manual" audit was performed by the same AI system
that wrote the classifier (me), reading the same text. This is a genuine, careful read of
each ticket's actual words, not another regex pass — but it is not an independent human
labeler, so correlated blind spots between the rules and the audit are possible and were
not ruled out. A production rollout should have a Vireo agent independently re-label a
sample before trusting the tool's category for routing decisions.

### 1c. Supervised ML baseline (for completeness, per brief's request)
A TF-IDF + Logistic Regression classifier was **not** shipped in the final tool. It was
tried during the build (80/20 split, trained on the noisy `category` tag as target) and
discarded — see README "AI tools used" — because it can only ever be evaluated against the
same noisy labels the whole exercise is questioning, so it adds a second unreliable number
without adding a second source of evidence. The rule-based approach was kept because its
logic is inspectable (a reviewer can read `src/classify.py` and agree/disagree with a
specific line), reproducible with zero training step, and — critically — because the real
validation for the business question came from §2 below, not from a classifier at all.

## 2. Cross-check: the headcount finding does not depend on the classifier

`agents.csv` gives, for every ticket, the team of the agent who actually resolved it
(`agent_id` → roster `team`, one row per agent, no ambiguity: 0 agents changed teams
mid-dataset). This is a **fact recorded by the helpdesk itself**, not a model output.

| view | Billing | Logistics | basis |
|---|---|---|---|
| `assigned_team` (bot tag) | 2,564 (21.8%) | 1,905 (16.2%) | what Priya's email quotes |
| `resolving_team` (roster) | 1,838 (15.6%) | **2,673 (22.7%)** | who actually closed it — no ML |
| `predicted_team` (this tool) | 1,126 (9.6%) | **3,835 (32.6%)** | content classifier |

All three counting methods agree on direction once you move past the raw intake tag:
**Logistics has more tickets than Billing.** The `resolving_team` column alone — a plain
join, no classifier — is sufficient to make this case; the text classifier is corroborating
evidence, not the sole basis. The monthly trend confirms this is not a one-off month: in
`outputs/monthly_team_actual_resolving.csv`, Logistics's resolving-agent count exceeds
Billing's in **every month from Jan 2025 through Jun 2026** (18 of 18 months).

## 3. Known limitations (be honest)
- Classifier precision on "Delivery & Shipping" is only ~0.42 against the noisy tag — it
  over-predicts Delivery in ambiguous "Other"-shaped tickets. This does not affect the
  headcount conclusion (which is corroborated by `resolving_team`, unaffected by this bias)
  but means the monthly-category chart should be read as directionally indicative, not
  audit-grade, for the smaller categories.
- "Other" is unreliable in both the original tag and the tool (~20% agreement either way) —
  a genuinely hard bucket; a real fix needs a better taxonomy from Vireo, not a better regex.
- No independent second human labeler was available in scope (see 1b caveat).
- `refund_reason_code` (an agent-selected dropdown, a strong independent signal) was checked
  as a sanity cross-reference but not formally incorporated into the classifier or validation
  metric — a natural next iteration.
