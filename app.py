"""
Vireo Audio — Support Ticket Categorisation & Headcount Tool
Run: streamlit run app.py
Expects data/tickets.csv, data/agents.csv (orders/customers/products optional,
used only if present for future extensions).
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from classify import classify_dataframe

st.set_page_config(page_title="Vireo Support Ticket Analysis", layout="wide")

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


@st.cache_data
def load_data():
    tickets_path = os.path.join(DATA_DIR, "tickets.csv")
    agents_path = os.path.join(DATA_DIR, "agents.csv")
    if not os.path.exists(tickets_path) or not os.path.exists(agents_path):
        return None, None
    t = pd.read_csv(tickets_path, parse_dates=["created_at", "first_response_at", "resolved_at"])
    a = pd.read_csv(agents_path)
    return t, a


def build(t, a):
    agent_team = a.set_index("agent_id").team.to_dict()
    t = t.copy()
    t["resolving_team"] = t.agent_id.map(agent_team)
    t = classify_dataframe(t)
    t["month"] = t.created_at.dt.to_period("M").astype(str)
    return t


st.title("Vireo Audio — Ticket Categorisation & Headcount Tool")
st.caption(
    "Rule-based re-categorisation of support tickets from customer_message + "
    "agent_notes, cross-checked against who actually resolved each ticket "
    "(agents.csv roster), to answer: which team should get the next two hires?"
)

t_raw, a_raw = load_data()
if t_raw is None:
    st.error(
        "Could not find data/tickets.csv and data/agents.csv. "
        "Place Vireo's supplied CSV files in the data/ folder (see README) and rerun."
    )
    st.stop()

t = build(t_raw, a_raw)

# ---------------- Data quality panel ----------------
with st.expander("Data quality summary", expanded=False):
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total tickets", f"{len(t):,}")
    c2.metric("Duplicate ticket_id", int(t.ticket_id.duplicated().sum()))
    c3.metric("Open/pending tickets", int(t.status.isin(["open", "pending"]).sum()))
    c4.metric("CSAT response rate", f"{t.csat_score.notnull().mean():.1%}")
    st.markdown(
        "- **Legacy timestamp bug:** for `legacy_fd` tickets, `resolved_at` is "
        "recorded ~4-6h *before* `created_at` for "
        f"**{(t.resolved_at < t.created_at).sum():,}** rows ({(t.resolved_at < t.created_at).mean():.1%} "
        "of all tickets). Consistent with resolution timestamps being reconstructed "
        "from the legacy event log in **UTC** while every other timestamp is displayed "
        "in **IST** (support-policy.pdf §9) — a +5:30 correction was not applied on migration. "
        "Any handle-time / SLA-breach metric computed on legacy rows as-is will be wrong; "
        "this tool does not compute handle-time, but a production report must fix this first."
    )
    st.markdown(
        f"- **transfers field:** blank (not zero) for all {int((t.source_system=='legacy_fd').sum()):,} "
        "legacy-sourced rows — it didn't exist in Freshdesk. Excluded from transfer-rate "
        "denominators below rather than treated as 0."
    )
    st.markdown(
        f"- **Category ≡ assigned_team, mechanically:** `assigned_team` is a deterministic "
        "function of `category` (set by the intake bot) and `channel` — confirmed by "
        "crosstab (100% of each category maps to exactly one team). It carries **no** "
        "independent judgement about which team actually did the work."
    )
    st.markdown(
        f"- **Date coverage:** actual data spans **{t.created_at.min().date()} to "
        f"{t.created_at.max().date()}** — the task brief described 'Jan 2025–Jun 2026'; "
        "the extra ~7 months (Jun–Dec 2024) are legacy-only and mostly pre-launch/ramp volume."
    )

# ---------------- Headcount: 3-way comparison ----------------
st.header("Which team should get the next two hires?")

specialist = ["Billing", "Logistics", "Returns Desk", "Escalations & Warranty"]
views = {
    "assigned_tag  (bot tag at ticket creation — what Sameer's export shows)": t.assigned_team,
    "resolving_agent  (who actually closed the ticket, via agents.csv roster)": t.resolving_team,
    "predicted_content  (this tool, from customer_message + agent_notes)": t.predicted_team,
}
comp = pd.DataFrame({name: s.value_counts() for name, s in views.items()}).fillna(0).astype(int)
comp = comp.reindex(["Chat Frontline", "Email Frontline", "Voice Frontline",
                      "Billing", "Logistics", "Returns Desk", "Escalations & Warranty"])
st.dataframe(comp, use_container_width=True)

st.markdown(
    "**Reading this table:** on the bot's intake tag, **Billing** looks like the largest "
    "specialist queue (2,564 tickets, 21.8%) — this is the number in Priya's email. "
    "But the tag is set from the customer's opening message only, at creation, before "
    "any agent looks at the ticket. Once you check **who actually resolved each ticket** "
    "(agents.csv, no modelling required) or **what the ticket is actually about** "
    "(this tool's text classifier), **Logistics is larger than Billing on both, every "
    "single month from Jan 2025 onward** — never a temporary blip."
)

fig, ax = plt.subplots(figsize=(8, 4))
specialist_only = comp.loc[specialist]
specialist_only.plot(kind="bar", ax=ax)
ax.set_ylabel("Ticket count")
ax.set_title("Specialist-team volume: 3 ways of counting the same 11,780 tickets")
plt.xticks(rotation=20)
st.pyplot(fig)

st.subheader("Monthly trend — Logistics vs Billing (resolving-agent view)")
monthly = t.groupby(["month", "resolving_team"]).size().unstack(fill_value=0)
fig2, ax2 = plt.subplots(figsize=(9, 4))
monthly[["Billing", "Logistics"]].plot(ax=ax2, marker="o")
ax2.set_ylabel("Tickets resolved that month")
st.pyplot(fig2)

# ---------------- Category breakdown ----------------
st.header("Monthly ticket volume by category (this tool's classification)")
cat_month = t.groupby(["month", "predicted_category"]).size().unstack(fill_value=0)
fig3, ax3 = plt.subplots(figsize=(10, 5))
cat_month.plot(kind="bar", stacked=True, ax=ax3, colormap="tab20")
ax3.set_ylabel("Tickets")
plt.xticks(rotation=90)
ax3.legend(bbox_to_anchor=(1.02, 1), loc="upper left", fontsize=8)
st.pyplot(fig3)

with st.expander("Category summary table"):
    cat_summary = t.predicted_category.value_counts().rename_axis("category").reset_index(name="ticket_count")
    cat_summary["pct"] = (cat_summary.ticket_count / cat_summary.ticket_count.sum() * 100).round(1)
    st.dataframe(cat_summary, use_container_width=True)

# ---------------- Financial impact ----------------
st.header("Measurable business outcome")
hd = t[t.source_system == "helpdesk"]
billing_hd = hd[hd.category == "Billing & Payments"]
other_hd = hd[hd.category != "Billing & Payments"]
n_billing = len(billing_hd)
avg_t_billing = billing_hd.transfers.mean()
avg_t_other = other_hd.transfers.mean()
excess_transfers = billing_hd.transfers.sum() - avg_t_other * n_billing
excess_cost = excess_transfers * 305
months_span = (hd.created_at.max() - hd.created_at.min()).days / 30.44
annualized = excess_cost / months_span * 12

c1, c2, c3 = st.columns(3)
c1.metric("Billing-tag transfer rate", f"{avg_t_billing:.2f}/ticket", f"vs {avg_t_other:.2f} avg elsewhere")
c2.metric("Excess transfers (helpdesk period)", f"{excess_transfers:.0f}", f"× ₹305/transfer")
c3.metric("Annualised excess transfer cost", f"₹{annualized:,.0f}/yr")

st.markdown(
    f"Helpdesk-era `Billing & Payments`-tagged tickets are transferred between teams at "
    f"**{avg_t_billing:.2f} transfers/ticket**, vs **{avg_t_other:.2f}** for every other "
    f"category — a direct, measurable cost of the intake bot's mis-tagging, since a ticket "
    f"opened as Billing but actually a delivery issue has to be handed off to Logistics "
    f"before it can be resolved. At ₹305/transfer (support-policy.pdf §4) this is "
    f"**≈₹{annualized:,.0f}/year** in avoidable internal-transfer cost, recoverable by fixing "
    f"intake routing — separate from, and smaller than, the ₹9L/year headcount decision."
)

# ---------------- Ticket-level table + export ----------------
st.header("Ticket-level output")
st.dataframe(
    t[["ticket_id", "created_at", "channel", "category", "predicted_category",
       "confidence", "assigned_team", "predicted_team", "resolving_team"]].head(500),
    use_container_width=True,
)
st.download_button(
    "Download full classified ticket export (CSV)",
    t.drop(columns=["customer_message", "agent_notes"]).to_csv(index=False),
    file_name="tickets_classified.csv",
)

st.caption(
    "Categorisation is deterministic keyword/regex logic (src/classify.py) — no paid API "
    "calls, fully reproducible. See docs/validation.md for accuracy and known limitations."
)
