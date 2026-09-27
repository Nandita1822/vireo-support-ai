**To:** Priya Raman, Head of Customer Experience, Vireo Audio
**From:** [Account team]
**Date:** [submission date]
**Subject:** Support ticket categorisation and headcount recommendation

## What we analysed
18–24 months of support tickets (11,780 records, Jun 2024–Jun 2026), the agent roster, and
your support-policy document. We re-checked how each ticket gets tagged with a category and
team, because your team had already flagged the tags as "probably rubbish."

## Key finding
Your intake system tags a ticket the moment it's created, from the customer's first message
only — before any agent has looked at it. It's tagging tickets **Billing** whenever a
customer mentions having paid, even when the real problem is a late delivery ("I paid,
nothing has arrived"). That single pattern is inflating Billing's numbers.

## Which team actually has the highest volume
**Logistics — not Billing.**

We checked two ways, independently:
1. **Who actually resolved each ticket** (a direct fact from your own systems, not a model):
   Logistics resolved **2,673 tickets (22.7%)**; Billing resolved **1,838 (15.6%)**.
2. **What the ticket is actually about**, read from the customer's message: confirms the
   same direction, by a wider margin.

This holds in **every single month** since your current helpdesk went live (Sep 2025) —
it isn't a one-off spike.

## Why this differs from what you'd heard
Your and Sameer's numbers (Billing 22%, Logistics 16%) are correct as a read of the raw
tag export — the tag itself is just misleading. Neha's instinct in the email thread
("it's Logistics who are actually drowning") is the one the data supports: Billing-tagged
tickets get handed off to another team **3.8× more often** than average, which is exactly
what you'd expect if many of them are actually Logistics issues wearing a Billing label.

## Monthly trend
Logistics has run consistently above Billing on actual-resolver volume for the full
18 months of the current helpdesk. Chart attached in the tool / GitHub repo
(`outputs/monthly_team_actual_resolving.csv`).

## Two-hire implication
Applying your own rule ("whichever team has the most volume gets the next two hires")
to the corrected numbers points the two hires at **Logistics**, not Billing.

## Financial impact
Separately from headcount: the Billing mis-tag is also costing you real money in avoidable
internal hand-offs — about **₹1.79 lakh/year** at your ₹305-per-transfer cost, just from
Billing-tagged tickets being transferred out at 3.8× the normal rate once we correct the
routing at intake. That's on top of — not a substitute for — the hiring decision.

## Confidence / validation
The headcount conclusion is checked two independent ways and agrees both times; the second
check (who actually resolved the ticket) doesn't rely on any model at all, just a join
against your agent roster. Full method and a 60-ticket manual accuracy check are in
`docs/validation.md`.

## Key limitation
The category-classification tool built alongside this analysis is a solid first pass
(rule-based, transparent, free to run) but isn't perfect on the harder, ambiguous tickets —
it shouldn't be trusted yet to auto-route tickets live without a human spot-check. It's
built to help you monitor the category/team split monthly going forward, not to replace
agent judgement.

## Recommended next step
Direct the two approved hires to **Logistics**, and separately ask your helpdesk vendor
to fix the intake bot's Billing-vs-Delivery confusion — that alone should meaningfully
cut the excess hand-offs quantified above.
