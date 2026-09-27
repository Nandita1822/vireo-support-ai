# Vireo Audio — Support Ticket Categorisation & Headcount Tool

## 1. What this project does
Takes Vireo's raw support ticket export, re-categorises each ticket from its actual text
(not the intake bot's tag), cross-checks that against who really resolved it, and answers
the question Priya Raman (Head of CX) asked: **which support team should get the next two
hires?**

**Headline finding:** Priya's email cites Billing as the biggest queue (22% of tickets, per
the bot's intake tag). Once you look at who actually resolved each ticket — a plain join
against `agents.csv`, no classifier required — **Logistics is larger than Billing**
(22.7% vs 15.6%), and has been every single month since the current helpdesk went live.
The classifier built here (reading `customer_message` + `agent_notes`) independently
confirms the same direction. Full evidence in `docs/validation.md`.

## 2. Business problem
Vireo's support tags (`category`, `assigned_team`) are set by a chatbot from the customer's
opening message at ticket creation, before an agent has looked at the ticket. The bot
conflates "customer mentions having paid" with "this is a billing issue" — so a ticket
that's really about a late delivery, where the customer opens with *"I paid, nothing has
arrived,"* gets tagged Billing and never re-tagged (agents "rarely" correct it). This
inflates Billing's apparent volume and was about to drive a headcount decision.

## 3. Dataset requirements
`tickets.csv` and `agents.csv` from Vireo (18–24 months of support tickets + agent roster).
Not included in this repo — see `data/README.md`.

## 4. Installation
```bash
git clone <this-repo>
cd vireo-support-ai
python3 -m venv venv && source venv/bin/activate   # optional but recommended
pip install -r requirements.txt
```
Tested on Python 3.11, clean virtualenv, no other system dependencies.

## 5. How to run
1. Copy Vireo's `tickets.csv` and `agents.csv` into `data/` (see `data/README.md`).
2. `streamlit run app.py`
3. Open the local URL Streamlit prints (defaults to http://localhost:8501).

The app loads the CSVs, runs the classifier, and renders: data-quality summary,
three-way team-volume comparison (bot tag / resolving agent / content classifier),
monthly Billing-vs-Logistics trend, monthly category breakdown, the measurable financial
outcome, and a ticket-level export you can download.

To regenerate the static CSVs in `outputs/` without the UI:
```bash
python3 -c "
import sys; sys.path.insert(0,'src')
import pandas as pd
from classify import classify_dataframe
t = pd.read_csv('data/tickets.csv', parse_dates=['created_at','first_response_at','resolved_at'])
a = pd.read_csv('data/agents.csv')
t['resolving_team'] = t.agent_id.map(a.set_index('agent_id').team.to_dict())
t = classify_dataframe(t)
t['month'] = t.created_at.dt.to_period('M').astype(str)
t.groupby(['month','predicted_category']).size().unstack(fill_value=0).to_csv('outputs/monthly_category.csv')
t.groupby(['month','predicted_team']).size().unstack(fill_value=0).to_csv('outputs/monthly_team.csv')
"
```

## 6. How categorisation works
Deterministic keyword/regex rules (`src/classify.py`), applied to `customer_message` first
and `agent_notes` as fallback, in a fixed priority order (Warranty → Returns → Delivery →
Billing → product-issue themes → Product Enquiry → Other). No paid API calls. The taxonomy
is Vireo's own eleven category names (kept, not reinvented) — what changed is *how* a
ticket is assigned to one. See the module docstring in `src/classify.py` for the full
reasoning, in particular why Billing is deliberately narrowed to payment-mechanics language
rather than any mention of "paid".

## 7. How team routing works
`predicted_team = f(predicted_category, channel)`, using support-policy.pdf §6 ownership
(Billing→Billing, Delivery & Shipping→Logistics, Returns & Refunds→Returns Desk,
Warranty & Repair→Escalations & Warranty; everything else routes to the Tier-1 frontline
team matching the ticket's channel, per README.txt/policy — social routes to Chat Frontline).

## 8. Outputs generated
All in `outputs/`:
- `category_summary.csv`, `team_summary.csv` — totals and % share, three counting methods
- `monthly_category.csv`, `monthly_team.csv` — monthly pivot (classifier)
- `monthly_team_actual_resolving.csv`, `monthly_team_original_tag.csv` — the other two views,
  for comparison
- `confusion_matrix_vs_noisy_tag.csv` — classifier vs. original tag, full matrix
- `tickets_classified_deidentified.csv` — ticket-level export with PII columns dropped
  (`customer_message`, `agent_notes`, `customer_id`, `order_id` excluded)

## 9. Validation methodology
See `docs/validation.md`. Short version: 56% raw agreement with the (known-unreliable)
original tag; a 60-ticket manual audit; and — most importantly — the headcount conclusion
is corroborated by a non-ML signal (`agents.csv` roster join), so it doesn't rest on
classifier accuracy alone.

## 10. Known limitations
- Rule-based classifier, not ML — will miss phrasings not covered by the keyword list
  (documented failure modes in `docs/validation.md` §1b).
- "Other" bucket is unreliable in both the original tag and this tool (~20% agreement with
  manual read either way) — needs a real taxonomy decision from Vireo, not a better regex.
- Legacy (`legacy_fd`) ticket `resolved_at` timestamps appear to be off by Vireo's UTC/IST
  migration bug (see data-quality panel in the app) — this tool doesn't compute handle-time
  or SLA breach, so it isn't affected, but any future report that does must fix this first.
- `transfers` is blank (not analysable as 0) for all legacy rows — the transfer-cost
  calculation below uses helpdesk-era data only (Sep 2025–Jun 2026, ~1,558 Billing tickets).
- No independent second human labeler for validation (see `docs/validation.md`).

## 11. AI tools used
- **Claude (Anthropic)**, used interactively as a coding/analysis assistant for: initial
  EDA and hypothesis generation, drafting and iterating `src/classify.py`, writing the
  Streamlit app, and drafting this documentation set.
- A TF-IDF + Logistic Regression classifier (scikit-learn, local, no API cost) was tried
  and **discarded** — see `docs/validation.md` §1c for why.
- No paid external LLM API calls were used anywhere in the pipeline; `src/classify.py` is
  pure regex/pandas and costs nothing to run, repeatedly, on a clean machine.

## 12. AI/API cost
**₹0.** The shipped classifier is deterministic Python (no API calls at inference time).
See the submission form answer to "what does one run cost" for the arithmetic at Vireo's
stated ~650 tickets/week volume.

## 13. Scope decisions
This was scoped to fit ~5 hours against a brief that is explicitly broader than that.
Prioritised (P0): correct data analysis, categorisation, team/category/monthly summaries,
a headcount conclusion grounded in actual data, a measurable business number, validation,
a working tool, this README. Also done (P1): memo, charts, exports, this file, a recording
script. **Deliberately left out** (P2, per brief's own priority list): a trained ML model
in the shipped path (tried, discarded, documented — not silently skipped), advanced UI,
extra automation, a full handle-time/SLA-breach report (blocked on the legacy-timestamp bug
noted above — flagging it was in scope, fixing it and rebuilding SLA metrics was not).

## 14. Data privacy considerations
- No `customer_message`, `agent_notes`, `customer_id`, or `order_id` in the GitHub-facing
  export (`outputs/tickets_classified_deidentified.csv`).
- Raw `tickets.csv` / `agents.csv` are git-ignored — never intended for the public repo;
  see `data/README.md`.
- The Streamlit app is meant to run locally against Vireo-supplied data; it is not deployed
  anywhere public in this delivery.
