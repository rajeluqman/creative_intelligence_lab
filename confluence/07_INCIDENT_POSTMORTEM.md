# Incident Postmortem

> ## 🚧 STATUS: STUB — no real incident yet
> **This page is intentionally empty.** This project hasn't shipped to live serving yet (Snowflake
> Cortex is unbuilt; DuckDB VSS is the only live search path, internal-use only) — there has been
> **no production incident** to write up. Per this project's own no-fabrication convention
> (`tests/doc_reference_contract.py`'s philosophy, the troubleshooting cheatsheet's authoring rule:
> "no fabricated incidents, no invented citations"), this page will not be pre-filled with a
> hypothetical postmortem.
>
> The closest real precedent — bugs found and fixed *during build*, not in production — are
> documented honestly in `PROJECT_STATUS.md`'s dated sections (e.g. the CRLF/CSV-sniffer bug, the
> Bronze-grain veto-and-fix, the `.env` not loaded in a fresh shell). Those are build-time fixes,
> not incidents, and are correctly kept there, not promoted here.
>
> **Gate to write a real entry here:** an actual production-serving incident occurs.
> **Format to use when it does:** mirror `cheatsheets/troubleshooting/`'s card format (Symptom →
> Backward trace → Root cause → Fix/guard with a real `file:line` → Junior mistake) — that
> library already reserves a `09_postmortem.md` phase for exactly this, currently gated at 0 cards.
> **Owner:** whoever owns the incident (routes through @senior-data-engineer for the pipeline,
> @data-architect if it's a model/lineage defect).
