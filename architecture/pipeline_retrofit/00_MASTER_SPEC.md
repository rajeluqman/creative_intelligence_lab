# Pipeline Retrofit — Master Spec (feed for Opus thinktank)

> Status: PLANNING ONLY. No code/agents/ADRs generated yet for the 4 target repos.
> Branch: `framework/pipeline-retrofit-plan` (created off `drill/t-l01-dup-pk`, which is untouched).
> Author of this pass: Sonnet (listing + mapping per owner instruction). Opus takes over for
> framework design + decision-making from here.

## 0. Scope of this document
Map the governance/framework layer of **two reference projects** onto **four target repos**,
picking "best of both worlds" between the references, while **each target repo keeps its own
existing stack** (Databricks vs Glue vs ADLS vs S3, etc.). This doc is the brief Opus reads
before designing the actual `CLAUDE.md` / `.claude/agents/` / ADRs / hooks / contracts for each
target repo.

## 1. Reference ranking (owner's explicit priority)
1. **`creative_intelligence_lab` (this repo) — PRIMARY reference.** Owner's reasoning: this repo
   has had the most enhancement passes (token-efficiency protocol, anti-shortcut protocol,
   lineage/boundary contracts, repo-map gate, isolation-contracted gym). Default to this repo's
   pattern whenever both references offer a working solution.
2. **`pharma_novartis_sttm` — SECONDARY reference, gap-filler only.** Use only for elements this
   repo (CIL) does not have at all, or where pharma's version is genuinely more complete for a
   reason that survives the recheck (see §2).

This ranking was tested by direct recheck (see conversation history) — CIL's `simulation/` gym
(untracked, isolated) is functionally equivalent to or stricter than pharma's Track B/Track I gym,
just named differently. Pharma is NOT ahead on learning/gym. Pharma is ahead on: agent roster
breadth, and the Confluence-publish mechanism being implemented end-to-end (CIL has the ADR for it
but the script is referenced only, not confirmed built — verify before citing as built).

## 2. Best-of-both-worlds element table (with justification)

| Element | CIL version | Pharma version | Pick | Why |
|---|---|---|---|---|
| Root context file | `CLAUDE.md`, stop-gate + anti-shortcut protocol baked in | `CLAUDE.md`, Token Discipline section, simpler gate | **CIL structure** | CIL's stop-gate (cite ADR before touching governed files) + anti-shortcut protocol (read-before-touch, enumerate-don't-sample, reconcile-before-done, tag-assumptions) is the more mechanically enforced version — backed by a hook, not just prose |
| Pre/post-edit enforcement | `.claude/hooks/governance_guard.py` (blocks edits to governed files without ADR citation) | none observed | **CIL** | Pharma has no equivalent hook — this is a real gap-fill, CIL wins outright |
| ADR system | 13 ADRs + addenda pattern (`ADR-00X` + "Addendum YYYY-MM-DD") | ADR-001 through ADR-006(-A1) with sub-addenda too | **Tie → CIL's numbering/addendum convention**, but adopt pharma's habit of writing ADR addenda for INFRA/process discoveries found mid-build (e.g. `O-AIR-07`-style "supersedes" notes), since CIL hasn't needed that yet but the 4 target repos (real cloud, real Glue/Databricks limits) will hit infra surprises mid-build | Both work; CIL's is cleaner, pharma demonstrated the addendum pattern under real infra friction which the 4 repos will also face |
| Repo-map / navigation index | `scripts/gen_repo_map.py` → `architecture/REPO_MAP.md`, CI `--check` gated, 100% generated | not observed in pharma | **CIL** | Pure gap-fill from CIL; pharma repo is large (20 agents, many docs) and would benefit from this but doesn't have it — recommend retrofitting pharma too, separately, not in scope here |
| Doc-reference contract | `tests/doc_reference_contract.py` — proves every model/path a doc cites exists | not observed | **CIL** | Gap-fill |
| Lineage/boundary contracts | `tests/lineage_contract.py`, `tests/boundary_contract.py` | GE suites only (no lineage-specific contract) | **CIL pattern, pharma's *content*** | CIL's contract *mechanism* (Python script, hard gate) is reusable as-is; pharma's actual lineage rules (crosswalk coverage as a DQD KPI, e.g. `dim_drug` ATC↔pharm_class↔free-text) are domain content worth mapping into the 4 repos' own lineage rules (each repo has its own identity problem: dedup keys, content hash, applicant SCD2, etc.) |
| Token-efficiency / model-routing protocol | ADR-012 — explicit lever list, Context-Bar red>75%→checkpoint rule | Token Discipline section (similar, less formalized) | **CIL** | CIL's version is the matured one; pharma's reads like an earlier draft of the same idea |
| Conversational language protocol | ADR-011 — Manglish opt-in, English default | pharma CLAUDE.md uses Malay/English mix natively (WAJIB section in Malay) | **CIL's opt-in model** | Owner explicitly repealed Manglish-first in CIL (Addendum 2026-06-27) because it drifted Indonesian-sounding; carry that lesson forward — default English narration in all 4 repos, Manglish opt-in only if requested per-repo |
| Agent roster | 8 agents (lean, 2 veto holders) | 20 agents (3-tier: veto/strategic/executor + training adversary) | **Pharma's breadth, CIL's restraint as the filter** | CIL deliberately rejected `bottleneck-saboteur` as a roster agent (kept as a tool only) and kept roster small per `AGENT_ROSTER_RECOMMENDATION.md`. For the 4 repos: take pharma's full 13 non-gym agents as the *candidate* list, then apply CIL's own filtering logic (does this role's function already exist as a script/doc? if yes, no agent needed) — see §4 |
| Executor tier (Haiku agents) | not present — CIL has no Haiku executor agents, only Sonnet build agents + Opus veto | `data-engineer`, `analytics-engineer`, `devops-orchestrator` (Haiku) | **Pharma** | Genuine gap-fill — CIL is single-dev/single-session scale and didn't need a cheap-executor tier; the 4 repos have more repetitive mechanical work (per-table Glue jobs, per-DAG wiring) that suits a cheap tier. Recommend adopting for cost reasons (ADR-012 lever 1: model routing) |
| Learning/teaching system | `learning/` (build-phase, CURRICULUM.md M0-M11, scored) + `simulation/` (gym, isolated, untracked, isolation-contracted) | `learning/` (Track A) + Track B (SLA) + Track I (incident) folded into main tree, not isolated | **CIL** | Confirmed by recheck: CIL's split (build-teaching in tracked `learning/`, gym in untracked isolated `simulation/`) is the safer pattern — pharma's gym artifacts live in the main tree with no isolation contract, so a sim drill could in principle touch real models. CIL's `ISOLATION_CONTRACT.md` (R1/R2/R3 mechanical rules) is strictly better and should be the template if/when the 4 repos get a gym layer |
| Alerting | ADR-009 references Slack + Confluence; Slack described as built in this CLAUDE.md's stack table reference, **not yet verified built in CIL itself** (mark unverified) | pharma: `publish_to_confluence.py` referenced, Slack via webhook in other repos' own pattern | **Pharma's Confluence script as the concrete artifact to copy**; **2 of the 4 target repos (home-credit, paysim) already have working Slack webhooks — copy THAT, not CIL's or pharma's, since it's proven in the same stack family** | Don't invent a new Slack integration — home-credit/paysim's existing webhook code is the working reference; olist and Volve need it backfilled from that pattern. Confluence sync is net-new for all 4 — pharma's script is the only existing implementation to adapt |
| Cost/checkpoint logs | `PROJECT_STATUS.md` "▶ RESUME HERE", `COST_LOG.md` | `PROJECT_STATUS.md`, `COST_LOG.md`, `JOURNEY_LOG.md`, `DEBUG_CHECKPOINT.md`, `SIGN_OFF_LOG.md`, `BLOCKER_LOG.md`, `HINT_LOG.md`, `DECISION_LOG.md`, `DOCS_CONSULTED.md`, `INFRA_LIMITS_LOG.md`, `PERFORMANCE_LOG.md`, `TROUBLESHOOTING.md` | **Pharma's log breadth, CIL's discipline about WHEN to write them** | Pharma has more log *types* (useful for a 4-repo retrofit where infra surprises are expected — `INFRA_LIMITS_LOG.md` and `BLOCKER_LOG.md` map directly onto known constraints like home-credit's documented Glue OOM risk and Volve's "3 of 29 wells" free-tier cap) but CIL's rule of *only write a log when load-bearing, not performatively* should govern which of pharma's 11 logs actually get instantiated per repo — likely subset: `PROJECT_STATUS.md`, `COST_LOG.md`, `DECISION_LOG.md`, `INFRA_LIMITS_LOG.md` (only repos with documented free-tier constraints: home-credit, Volve) |

## 3. Stack-preservation rule (hard constraint for Opus)

The framework/governance layer is **stack-agnostic and gets tailored per repo**; the underlying
data stack in each repo is **untouched**. Concretely:

| Repo | Stack to preserve as-is | What the new CLAUDE.md's "Stack" table must say |
|---|---|---|
| olist-ecommerce-pipeline | Azure ADLS Gen2 + Databricks Unity Catalog (Bronze/Silver) + Snowflake/dbt (Gold) + Airflow + Power BI | Document exactly this; add a "rejected tech" boundary row only if the project's own ADR-001 already implies one (check `docs/ADR/ADR-001-data-modelling-paradigm.md` content before asserting) |
| Volve-Sensor-Production-Analytics-Pipeline | Databricks Volume/Delta Share, all layers in Databricks SQL Warehouse, MLflow, Snowflake serving (5 views), Airflow Docker | Same — plus flag the missing ADR layer as the first thing to backfill (§4) |
| home-credit-pipeline | AWS S3 + Delta Lake (Bronze) + AWS Glue PySpark (Silver, PII masking) + Snowflake/dbt (Gold, SCD2 snapshot) + Airflow + Slack + Power BI/Databricks Serverless SQL | Already has `.mcp.json` (Snowflake/Databricks/aws-docs/dbt MCP servers) — preserve, extend only |
| paysim-fraud-pipeline | AWS S3 + Delta Lake (Databricks Unity Catalog) + Databricks SQL Warehouse (Silver) + Arrow/Snowflake (Gold, dbt) + Airflow + Slack + Power BI | Preserve; this repo's "Hybrid Kimball + Cumulative Table" modelling choice is itself ADR-worthy and currently undocumented as an ADR (only implied in README) |

**Rule for Opus:** never propose swapping a tool (e.g. don't suggest Glue→Databricks for
home-credit, or S3→ADLS for Volve). The retrofit adds governance scaffolding around the existing
stack — it does not re-architect data infrastructure. Any tool-boundary opinion belongs in a new
ADR for that repo, written in the repo's own voice, not copy-pasted from CIL's stack table.

## 4. Per-repo file/doc gap list (what to create, source justification)

### olist-ecommerce-pipeline
| Missing | Source pattern to adapt | Why needed |
|---|---|---|
| `CLAUDE.md` | CIL structure, stripped of CIL-specific content (LLM/Gemini stuff irrelevant here) | onboarding + stop-gate for future sessions |
| `.claude/agents/` (subset, see §5) | pharma's agent files, tailored to ADLS/Databricks/Snowflake stack | governance + role clarity |
| `.claude/hooks/governance_guard.py` equivalent | CIL hook, retargeted to olist's own "governed files" (DATA_MODEL.md, dbt marts, ADR folder) | enforce ADR-before-edit |
| 3rd+ ADR (currently has 2: template + data-modelling-paradigm) | pharma's addenda habit | KPI/star-schema choices beyond modelling paradigm (e.g. why SCD2 for customers/sellers but SCD1 for products) are currently undocumented decisions |
| `architecture/REPO_MAP.md` equivalent | CIL `gen_repo_map.py` | repo has 9+ top-level dirs already, navigation aid justified |
| Slack alerting | home-credit/paysim's existing webhook code (README says "Slack integration pending") | closes a documented gap in olist's own README |
| Confluence publish script | pharma's `publish_to_confluence.py` | net-new capability |

### Volve-Sensor-Production-Analytics-Pipeline
| Missing | Source pattern to adapt | Why needed |
|---|---|---|
| `CLAUDE.md` | CIL structure | same as above |
| `docs/ADR/` folder — **currently has ZERO ADRs** despite README claiming decisions | pharma's ADR-001 style (real estate: storage/compute trade-off, free-tier well-count cap) | biggest doc gap of the 4 repos; the "3 of 29 wells" constraint and ML-model choices (XGBoost vs RF vs IsolationForest) are real architecture decisions with no record |
| `docs/DATA_MODEL.md`, `docs/DATA_DICTIONARY.md` | olist/home-credit/paysim's existing versions as template | only repo of the 4 missing these entirely |
| `.claude/agents/` (subset) | pharma, tailored — **`infra-reality-agent` is most justified here** (free-tier well-count limit, WITSML XML parsing fragility) | |
| `INFRA_LIMITS_LOG.md` | pharma | document the 3/29-well constraint formally instead of only in README prose |
| Slack + Confluence | same as olist | |

### home-credit-pipeline
| Missing | Source pattern to adapt | Why needed |
|---|---|---|
| `CLAUDE.md` | CIL structure | |
| `.claude/agents/` (subset) | pharma | already has `.mcp.json` suggesting prior Claude Code use — agents are the natural next step |
| More ADRs (has 1: kimball-star-schema) | pharma's addenda habit | PII-masking order (365243→NULL before SHA-256) is a real decision currently only in README prose, not an ADR; same for the "Kimball over OBT, deferred to Snowflake" sizing decision |
| `INFRA_LIMITS_LOG.md` | pharma | Glue OOM risk on free tier is explicitly named in README — promote to a tracked log/ADR |
| Confluence publish | pharma | Slack already exists — don't touch |

### paysim-fraud-pipeline
| Missing | Source pattern to adapt | Why needed |
|---|---|---|
| `CLAUDE.md` | CIL structure | |
| `.claude/agents/` (subset) | pharma | likely has `.mcp.json` too (same author/era as home-credit — verify before asserting built) |
| More ADRs (has 1: hybrid-paradigm) | pharma's addenda habit | the "1 WARN documented" GE result (Silver 14/15) is a quality decision with no ADR trail — should be either fixed or formally accepted with a written rationale |
| Confluence publish | pharma | Slack already exists — don't touch |

## 5. Agent roster — per-repo tailoring (candidate pool = pharma's 13 non-gym agents, filtered by CIL's "does this duplicate an existing script/doc?" rule)

| Agent | olist | Volve | home-credit | paysim | Tailoring note |
|---|---|---|---|---|---|
| `data-architect` (Opus, veto) | ✅ | ✅ | ✅ | ✅ | universal — star-schema doctrine owner in all 4 |
| `scope-guardian` (Sonnet, veto) | ✅ | ✅ | ✅ | ✅ | universal |
| `product-owner` | ✅ | ✅ | ✅ | ✅ | universal — BRD already exists in all, formalize ownership |
| `business-analyst` | ✅ | ✅ | ✅ | ✅ | universal — DRD/data-dictionary owner, currently nobody's job |
| `senior-data-engineer` | ✅ | ✅ | ✅ | ✅ | universal |
| `data-quality-steward` | ✅ | ✅ | ✅ | ✅ | universal — GE suites exist everywhere, no owner |
| `qa-engineer` | ✅ | ✅ | ✅ | ✅ | unit tests exist everywhere |
| `finops-agent` | 🟡 light | ✅ | ✅ | ✅ | olist on ADLS free tier — lower cost risk than the 3 AWS/Databricks-heavy repos |
| `data-platform-engineer` | ✅ | ✅ | ✅ | ✅ | multi-cloud infra wiring in all 4 (none are single-tool like CIL) |
| `infra-reality-agent` | 🟡 | ✅ **priority** | ✅ **priority** | 🟡 | Volve (free-tier well cap, WITSML fragility) and home-credit (Glue OOM, documented in README) have the sharpest real-infra constraints |
| `documentation-sherpa` | ✅ | ✅ **priority** | ✅ | ✅ | Volve most needs this — it's the repo with zero ADRs/data-model docs to catch up on |
| `devops-orchestrator` (Haiku) | ✅ | ✅ | ✅ | ✅ | Airflow DAG wiring is mechanical across all 4 — cheap tier appropriate |
| `analytics-engineer` (Haiku) | ✅ | n/a (no dbt layer in Volve — Gold built in Databricks, not dbt) | ✅ | ✅ | Volve doesn't use dbt at all — this role only applies where dbt exists |
| `data-engineer` (Haiku, executor) | ✅ | ✅ | ✅ | ✅ | per-table/per-job mechanical build work in all 4 |
| `project-manager` | 🟡 optional | 🟡 optional | 🟡 optional | 🟡 optional | README "Phase Completion" tables already serve this; only add if owner wants a dedicated tracker |
| `cikgu` + gym agents | ❌ not in scope | ❌ | ❌ | ❌ | explicitly out of scope unless owner separately decides to retrofit a learning gym onto these portfolio repos too — not requested here |

## 6. Open questions for Opus (do not silently resolve — surface to owner)

1. **Volve's missing ADR backlog** — does Opus reconstruct ADRs retroactively from README prose
   (risk: inventing rationale that wasn't actually deliberated), or does the owner need to re-derive
   the real reasoning first? Recommend: draft as "ADR (reconstructed from README, owner to confirm
   rationale)" — tag honestly, don't fabricate confidence.
2. **Confluence publish script** — pharma's `publish_to_confluence.py` is referenced in this
   project's ADR-009 but not yet confirmed as a working file in either CIL or pharma in this audit
   pass. Opus should verify the actual script exists and works before treating it as a proven
   pattern to copy 4×.
3. **Per-repo CLAUDE.md language** — default English per the ADR-011 lesson (Manglish drifted
   Indonesian-sounding); confirm this applies to all 4 portfolio repos too (likely yes, since
   they're public portfolio pieces, not a private practice lab).
4. **Haiku executor tier cost tradeoff** — confirm with `finops-agent`-equivalent reasoning whether
   adding a 3-tier model-routing system across 4 repos is worth the setup cost vs just using Sonnet
   uniformly, given these are already-built portfolio pipelines (lower marginal benefit than an
   active build).
5. **Gym/simulation layer** — owner did not request this for the 4 repos in this pass. Confirm
   explicitly before Opus extends `simulation/`-style isolated practice labs to any of them.

## 7. Session/token scoping (carried from prior estimate, restated for Opus)

Full retrofit of all 4 repos to this spec is **not a single 5-hour session**. Recommend Opus
scopes its first pass to **one repo** (home-credit-pipeline — closest stack overlap with CIL's own
Snowflake/dbt pattern, already has `.mcp.json`, smallest doc-gap list) as the template, then
replicates the *pattern* (not a literal copy — stacks differ) to the other 3 in follow-up sessions.
