# Screen recording script (≤3 minutes, no slides)

**0:00–0:20 — What was built**
"This is a ticket categorisation and headcount tool for Vireo Audio. Their support ticket
tags are set by a chatbot at intake and are known to be unreliable — the brief asked me to
figure out which team should get the next two approved hires, using the actual data instead
of the bot's tags."

**0:20–0:45 — How it runs**
Show terminal: `pip install -r requirements.txt` → `streamlit run app.py`. App opens.
"No paid API calls, runs offline, reproducible on a clean machine — just pandas, sklearn's
metrics for validation, and Streamlit for the UI."

**0:45–1:15 — The finding**
Scroll to the three-way team comparison table in the app.
"Priya's email says Billing is the biggest queue — 22%, from the bot's tag. But if you
check who *actually* resolved each ticket — a plain join against the agent roster, no
model involved — Logistics is bigger: 22.7% versus Billing's 15.6%. My own text classifier
agrees, more strongly. And this holds every single month since the current helpdesk went
live, not just one bad month." Point at the monthly trend chart.

**1:15–1:45 — Prompts/AI tools used, what changed between versions**
"I used Claude throughout for EDA, writing the classifier, and the app. First version of
the classifier over-triggered 'Delivery & Shipping' on ambiguous tickets — checking message
text before agent notes, and fixing a couple of keyword bugs (like 'charger' as a product
name falsely matching 'charging' complaints) brought agreement with a hand-read validation
sample up. I also tried a TF-IDF logistic regression classifier and dropped it — it can only
be graded against the same unreliable tags I'm trying to correct, so it doesn't actually add
evidence."

**1:45–2:15 — Validation**
Show `docs/validation.md`. "56% raw agreement with the original tag — expected, since
disagreement is partly the point. I hand-read a 60-ticket stratified sample as an
independent check: the tool fixes roughly twice as many tag errors as it introduces. But
the headline finding — Logistics over Billing — doesn't rest on the classifier at all; it's
confirmed by the agent-roster join by itself."

**2:15–2:40 — Known limitation**
"The weakest part is the 'Other' bucket — about 20% reliable either way, original tag or
tool. And my manual validation was me reading the tickets, not an independent Vireo agent —
that's a real gap before anyone routes live tickets off this."

**2:40–3:00 — Close**
"End result: redirect the two hires to Logistics, not Billing, and there's a separate
₹1.79 lakh/year fixable cost from Billing tickets getting bounced to the right team after
the fact. Everything's in the repo README and validation doc."
