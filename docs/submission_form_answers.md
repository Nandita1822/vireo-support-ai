# Submission form — answers

**1. What did you build, and what business outcome does it move? State the number and money.**
A reproducible ticket categorisation tool + headcount analysis for Vireo Audio's support
desk. It found that the two approved hires (Finance-quoted at ≈₹9,00,000/year) were about
to be misdirected to Billing based on a mis-tagged intake bot, when actual resolver data
shows **Logistics has the higher volume** (22.7% vs Billing's 15.6% of all tickets,
consistent every month since Sep 2025). Redirecting the hiring decision avoids spending
₹9L/year of approved headcount against the wrong queue. Separately, the tool quantifies
≈**₹1,78,700/year** in avoidable internal-transfer cost (₹305/transfer, support-policy.pdf
§4) caused specifically by Billing-tagged tickets being handed off elsewhere 3.8× more
often than average — a fixable intake-routing bug, not a headcount problem.

**2. What does one run cost, and what would a month cost at Vireo's volume (≈650 tickets/week)?**
₹0 per run. The classifier (`src/classify.py`) is deterministic regex/pandas — no paid API
calls at inference time. Running it over 650 tickets/week (≈2,817/month) costs the same
₹0, plus whatever compute Vireo already pays for to host a small Python job (negligible;
runs in under 2 seconds on a laptop for the full 11,780-row historical file). No paid
calls were used anywhere in the shipped pipeline.

**3. How do you know it works?**
Two separate checks (`docs/validation.md`):
- **Classifier vs. the original noisy tag:** 56.0% exact-match agreement across all 11,780
  tickets; per-category precision/recall/F1 in `docs/validation.md` §1a; full confusion
  matrix in `outputs/confusion_matrix_vs_noisy_tag.csv`.
- **60-ticket manual audit** (stratified: 25 agreement cases, 35 disagreement cases), each
  ticket's actual text read and judged independently: original tag matched my judgment
  ~70% of the time, the tool ~68-70% — similar overall, but on the 35 disagreement cases the
  tool corrected the tag roughly twice as often as it broke one.
- **Most importantly, the headcount conclusion itself doesn't depend on classifier
  accuracy at all** — it's corroborated by a plain, non-ML join (`agent_id` → team, from
  `agents.csv`), which independently shows the same Logistics > Billing result.
- Error types found: short/terse tickets with no keyword signal (fall to "Other" always);
  a couple of product-name false positives (patched, likely not exhaustive); ambiguous
  ownership calls (hardware fault vs. warranty vs. audio) that a human would also disagree
  on.

**4. Did you change, narrow, or push back on the client's ask? Explain what, when, why.**
Yes, three things:
- **Scope narrowing (up front):** the brief explicitly said it's bigger than 5 hours.
  Skipped a trained ML classifier (tried a TF-IDF+LogReg baseline, discarded — see
  `docs/validation.md` §1c), a full handle-time/SLA report, and any deployment — kept to
  categorisation + headcount + one financial number, all validated.
- **Pushback on "team" for the headcount rule:** taken literally across all 7 teams
  (including Tier-1 Chat/Email/Voice Frontline), Chat Frontline is the largest by every
  counting method (it absorbs the highest-volume channel plus all general/"Other"
  categories) — a strictly literal reading of "whichever team has the most volume" would
  point the hires there, not at a specialist team at all. I read Priya's own email
  (comparing only Billing vs. Logistics) as implicitly scoping the rule to specialist
  queues, since frontline headcount is a different lever tied to channel mix — but this is
  my assumption, not confirmed by the client, and is flagged explicitly for someone to
  check with Priya.
- **Redefined what "Billing" means, not the taxonomy:** kept Vireo's own 11 category names
  rather than inventing a new one (per brief: "do not force these categories if the data
  suggests a better taxonomy" — the data didn't; the *assignment logic* was the problem).

**5. What is wrong with what you are handing us? Be specific.**
- The rule-based classifier's "Other" bucket is unreliable both in the original data and
  in this tool (~20% manual-audit agreement either way) — treat categorised volumes for
  small/ambiguous categories as directional, not audit-grade.
- "Delivery & Shipping" precision is only ~0.42 against the noisy tag — the classifier
  over-predicts it on ambiguous tickets. Doesn't affect the headcount conclusion (which is
  corroborated independently, see Q3) but affects the monthly-category chart's fine detail.
- The manual validation audit was done by the same AI system that built the classifier —
  not an independent human labeler. A real second opinion from a Vireo agent hasn't happened.
- Legacy-ticket (`legacy_fd`) `resolved_at` timestamps appear to carry an unfixed UTC/IST
  offset bug (flagged, not corrected — see README §10). The tool doesn't compute anything
  timestamp-dependent, so it isn't affected, but don't reuse `resolved_at` from legacy rows
  for SLA/handle-time work without fixing this first.
- No automated tests beyond the manual runs performed during this build (documented in
  this conversation) — there's no CI, no pytest suite.

**6. What did you deliberately leave out, and why?**
A trained ML classifier in the shipped path (see Q3/Q5), a full SLA-breach/handle-time
report (blocked by the legacy timestamp bug — fixing that is a separate task), any live
deployment or scheduling, and orders.csv/customers.csv/products.csv integration (loaded and
inspected during analysis but not wired into app.py — no P0 finding needed them; a natural
next step is joining product family to complaint category, e.g. to see if returns cluster
by SKU).

**7. Anything you built or found that nobody asked for?**
Found, not asked for: the deterministic `category → assigned_team` mapping (100% mechanical,
confirmed by crosstab) — meaning `assigned_team` in the export carries zero independent
signal beyond the category tag itself; and the legacy-ticket UTC/IST timestamp bug
(§9 of support-policy.pdf explains why it exists, but nobody had flagged that it's actually
live in the export). Built, not asked for: the three-way team-volume comparison table
(tag vs. resolver vs. classifier) in the app — useful for anyone auditing this analysis
later, since it makes the "which number do you trust" question explicit instead of picking
one silently.

**8. What did you use AI for?**
See README §11. Claude (Anthropic), interactively, for EDA/hypothesis generation, writing
and iterating the classifier and Streamlit app, and drafting this documentation. A
scikit-learn TF-IDF+LogReg baseline was tried and discarded (§1c of validation.md) — the
main thing "wasted" here was the time spent tuning it before deciding a noisy-label-trained
model wasn't the right validation story for this specific business question. No paid LLM
API calls in the shipped pipeline; cost = ₹0.

**9. Someone picks this up on Monday and you are unreachable. What are the three things they need to know?**
1. The headline number (Logistics > Billing) does **not** depend on the classifier being
   right — it's confirmed by a simple `agents.csv` join. If anyone questions the
   classifier's accuracy, point them to that independent check first (`docs/validation.md` §2).
2. `data/*.csv` is git-ignored on purpose — the repo has no raw ticket data or PII. Anyone
   re-running this needs Vireo's original files dropped into `data/` (see `data/README.md`).
3. This assumes Priya's "team with most volume" rule is scoped to specialist teams,
   excluding Tier-1 frontline (see Q4) — that assumption was never confirmed with Priya
   directly and should be checked before the recommendation is finalised.

**10. Honest hours spent.**
~5 hours.

**11. GitHub Repo Link.**
[Not created in this session — see "Exact steps to submit" below for how to push the
`/home/claude/vireo` working directory to a new repository.]
