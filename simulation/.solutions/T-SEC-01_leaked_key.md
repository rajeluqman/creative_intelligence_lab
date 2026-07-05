# 🔒 GATED SOLUTION — T-SEC-01 Leaked Credential (8-phase incident)

> **STOP.** Only open this after you've worked through all 9 sub-answers in the drill's §3.
> This is the L3 drill — grading is on comms + prevention (Phases 2, 7, 8) as much as the fix.

---

## Mental model (analogi dulu)
A leaked key is not "a file with bad content" — it's **a live, usable credential now sitting
somewhere you don't control the copies of.** Deleting the file is like burning your own copy of
a key you handed to a stranger: it does nothing about the copy they already have. That's why
rotate-first is non-negotiable — it invalidates every copy, everywhere, including ones you don't
know exist.

## Phase-by-phase model answers

**Phase 0 — Detect:** the regex scan in §2 IS the detection signal (standing in for a real
secret-scanner or a stranger's disclosure email, per the bank entry). Detected by: you, running
the check — in a real incident, note whether a human beat an automated scanner to it (that gap
is itself a Phase-8 finding).

**Phase 1 — Triage:** what leaked = an AWS-shaped access key (fake here, but the SHAPE is real:
`AKIA[0-9A-Z]{16}`). Blast radius (if real): anything that key's IAM policy allows — S3
read/write on whatever buckets, possibly more if over-privileged (see bank's T-SEC-04 sibling
entry). Severity: **P1 if the key were real and live** — a leaked credential is "wrong access is
possible," which the runbook ranks worse than downtime; for this drill, since it's a planted fake
that was never functional, the honest severity call is **P3/simulated**, and you should say so
explicitly rather than dramatizing a fake incident as a real P1.

**Phase 2 — Comms (initial), BEFORE fixing:**
> **[SIMULATED][P3][creative-intel-sim] Drill: leaked-credential-shaped fixture detected in
> `simulation/faults/.fixtures/`.** Not a real incident — planted for T-SEC-01 training. No real
> credential was ever valid. Proceeding through the full runbook for practice; no rotation of any
> real system needed.
(If this were real: state impact in consumer terms, what's safe to keep using, commit to a
next-update time — exactly per the runbook's own worked example.)

**Phase 3 — Contain:** for a REAL key: rotate first (kills every existing copy at the source,
including ones already exfiltrated), THEN purge git history (`git filter-repo` / BFG), THEN audit
usage logs for the exposure window (CloudTrail/access logs) to see if it was actually used by
anyone else before rotation. Purging history alone leaves the OLD key valid — anyone who already
cloned/forked/cached the repo still has a working credential.

**Phase 4 — Diagnose:** root cause is a **process gap**, not a typo — nothing stopped a
secret-shaped literal from being committed. The prevention control is exactly what U2 of this
session built: `framework_template/gates/secrets_scan.py` (pre-commit/CI pattern-scan for
`password/api_key/secret/token = "literal"`, AWS `AKIA[0-9A-Z]{16}`, private-key headers).

**Phase 5 — Fix (this drill):** delete the fixture (`simulation/faults/reset.py`); in a real repo,
also add the pre-commit hook wired to `secrets_scan.py` so this class can't land again.

**Phase 6 — Recover & validate:** re-run §2's scan — zero hits is the named gate, not "looks
deleted."

**Phase 7 — Comms (resolution):**
> **[RESOLVED][SIMULATED][creative-intel-sim] T-SEC-01 drill complete.** Fixture removed, scan
> confirms zero secret-shaped matches remain. No real credential was ever live or usable at any
> point in this drill — nothing to rotate outside the simulation.
(State the guarantee precisely — this is the line graders check hardest: don't overstate OR
understate what actually happened.)

**Phase 8 — Postmortem, prevention artifact:** `framework_template/gates/secrets_scan.py` (built
this same session, U2 of the 2026-07-04 handover) — a real, runnable, config-driven gate that
would have caught this pre-commit rather than requiring a human/scanner to find it after the fact.

## Card fields (model answer)
- **⚠️ Junior mistake:** deleting the file and calling it fixed — leaves any real leaked
  credential still valid everywhere else it was copied to; also skipping Phase 2 comms because
  "I'll just fix it quietly" — silence on a security-shaped incident is its own trust problem
  even when (especially when) it turns out to be a false alarm.
- **🎤 Soundbite:** *"Leaked credential first: rotate, not just remove — a deleted file doesn't
  invalidate copies that already exist. Then I traced why no pre-commit gate caught it and shipped
  one, so the fix is the incident's LAST output, not its only output."*

## Cloud vocab (for interview transfer)
Same lifecycle regardless of cloud: AWS key rotation + `git filter-repo`/BFG history purge +
CloudTrail usage-window audit; the "rotate before purge" ordering is universal, not AWS-specific.
