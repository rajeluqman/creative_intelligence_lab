# The 10 Business Questions — what 80% of bank stakeholders actually ask

> Feeds `journey/02_BUSINESS_QUESTIONS.md` in the new repo. These 10 ARE the scope of Gold —
> any mart not answering one of them is scope creep (@scope-guardian enforces). Each BQ names
> its join path deliberately: 8 of 10 are impossible without `dim_customer_xwalk`, which is
> the proof the pipeline (and the MDM layer) needs to exist.

| # | Business question | Stakeholder | Sources joined | Gold artifact |
|---|-------------------|-------------|----------------|---------------|
| BQ-01 | **Customer 360** — how many products does each customer hold (deposits, cards, loans), and what is their total relationship value? | Management, relationship managers | ALL 4 + xwalk | `mart_customer_360` |
| BQ-02 | **Fraud trend** — fraud transaction count & value this month vs last, broken down by transaction type/channel? | Fraud ops | MSSQL cards | `mart_fraud_daily` |
| BQ-03 | **Fraud follow-up SLA** — of customers hit by fraud, what % got a CRM follow-up ticket within 48h? | Fraud ops + customer service | cards + CRM + xwalk | `mart_fraud_followup` |
| BQ-04 | **Loan funnel** — applications in per month, approval rate, average time from application to decision? | Loan/sales dept | Postgres loans | `mart_loan_funnel` |
| BQ-05 | **Default risk by segment** — default rate by customer segment (income band, employment type), and which ACTIVE customers are currently high-risk? | Risk | loans + core + xwalk | `mart_risk_segment` |
| BQ-06 | **Cross-sell targets** — customers with healthy deposits (high balance, active txns) but NO card/loan yet? | Marketing | core + loans + cards + xwalk | `mart_cross_sell` |
| BQ-07 | **Dormancy** — how many customers went dormant (no txn in X days) this month, and what do they look like? | Retention | cards + core + CRM + xwalk | `mart_dormancy` |
| BQ-08 | **Liquidity view** — total deposits and daily net flow (in vs out), daily trend? | Treasury / management | core + cards | `mart_daily_flows` |
| BQ-09 | **Spending behaviour** — distribution of transaction types & values per customer segment per month? | Marketing / product | cards + CRM demographics + xwalk | `fact_card_txn` × `dim_customer` |
| BQ-10 | **Can we trust the numbers?** — when did each source last refresh, how many records failed DQ yesterday, do source→Gold counts reconcile? | ALL stakeholders (the question behind every other question) | pipeline run metadata | `mart_pipeline_health` |

## Notes
- **BQ-10 is deliberate and non-optional.** Freshness/DQ/reconciliation is the question every
  stakeholder asks before believing BQ-01…09; it also forces the pipeline to emit run metadata
  as a first-class output (R-30).
- **Definition of done per BQ** = one runnable query against Gold + its output captured in
  `journey/08_SERVING_AND_EVIDENCE.md`. Demo-able or it doesn't count (@product-owner).
- Segment definitions (income band, dormancy X days, "healthy" balance) are set once in
  `journey/03_DATA_REQUIREMENTS.md` — not invented per-mart.
