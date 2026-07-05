# Drill T-SEC-01 — Credential leaked to git (full 8-phase incident)

> **Bank entry:** `PROBLEM_BANK_TROUBLESHOOT.md` T-SEC-01 (Lvl **L3** — own the incident
> end-to-end) · **Fault:** `sec_leaked_key` · **Runbook:** every phase below is graded against
> [`../../architecture/control_plane_lab/saboteur/INCIDENT_RUNBOOK.md`](../../architecture/control_plane_lab/saboteur/INCIDENT_RUNBOOK.md)
> — this is the ONE drill where the comms/postmortem phases (2, 7, 8) matter as much as the fix.
> **Run with** [@cikgu](../CIKGU_DRILL_PROTOCOL.md). **Answer is gated** in
> `../.solutions/T-SEC-01_leaked_key.md` — do NOT open it until you've worked through §4.

Self-contained, isolation-safe: the "leaked key" is a clearly-fake fixture planted only inside
`simulation/`, never a real credential, never touching real `.env`/GitHub secrets.

---

## 0. Pre-flight
```bash
python simulation/check_isolation.py    # PASS — safe to break the lab
python simulation/faults/inject.py sec_leaked_key
```
This plants `simulation/faults/.fixtures/leaked_key_demo.py` containing an obviously-fake AWS-shaped
key (never a working credential) and prints the expected symptom + which gate should catch it.

## 1. The scenario (production framing)
> Kau on-call. Subuh tadi seorang teammate debugging locally pasted a config dump into a scratch
> file and `git add -A`'d before thinking. It's now sitting in the working tree (in a real
> incident: in git history). A secret-scanner style gate — the one U2 of this session just built,
> `framework_template/gates/secrets_scan.py` — is the kind of thing that would have caught this
> automatically; **today you're the human who has to run the equivalent check and own the
> response**, because the drill assumes it landed a moment before the gate existed.

## 2. Reproduce it (isolation-safe — read-only regex check, no real credentials anywhere)
```python
# save as /tmp/claude-1000/.../scratchpad/t_sec_01_scan.py  or paste into: python3
import re
from pathlib import Path

FIXTURE = Path("simulation/faults/.fixtures/leaked_key_demo.py")
AWS_KEY_RE = re.compile(r"AKIA[0-9A-Z]{16}")
LITERAL_SECRET_RE = re.compile(r"(?i)(password|api_key|secret|token)\s*=\s*['\"][^'\"]{8,}['\"]")

text = FIXTURE.read_text()
hits = AWS_KEY_RE.findall(text) + LITERAL_SECRET_RE.findall(text)
print("Hits:", hits if hits else "NONE")
```
Run it (after `inject.py sec_leaked_key`, §0). It finds the planted key — this is your Phase 0
**DETECT** signal, standing in for "the scanner/stranger's email" from the bank entry.

## 3. Work the runbook (answer each phase BEFORE reading ahead — cikgu asks one at a time)
Use [`INCIDENT_RUNBOOK.md`](../../architecture/control_plane_lab/saboteur/INCIDENT_RUNBOOK.md)
phases 0–8 as your checklist. This drill is graded on **all** of them, not just the fix:

1. **Phase 0 DETECT** — what's the signal, and who/what detected it (you, via the gate above)?
2. **Phase 1 TRIAGE** — what exactly leaked (a real secret shape, even if this one is fake)? Blast
   radius: what could this credential have reached if real? Severity call — justify it against
   the runbook's P1–P4 scale.
3. **Phase 2 COMMS (initial) — BEFORE fixing.** Write the actual message you'd send. (Doc pointer,
   not a template to fill blindly: re-read the runbook's Phase 2 worked example first — what tone,
   what's stated, what's promised.)
4. **Phase 3 CONTAIN** — for a REAL leaked key the bank's fix direction is "rotate FIRST, then
   purge history." Why rotate before purging, not the other way round? What does purging alone
   leave exposed?
5. **Phase 4 DIAGNOSE** — root cause here isn't "a key existed," it's a process gap. What allowed
   it to land? (This is where you connect to U2's `secrets_scan.py` — what would have stopped it
   pre-commit?)
6. **Phase 5 FIX** — the smallest reversible change. For THIS drill: remove the fixture + (name,
   don't necessarily hand-implement) the pre-commit control that prevents recurrence.
7. **Phase 6 RECOVER & VALIDATE** — what's the named gate that proves the leak is gone? (Not an
   eyeball — re-run §2's scan and show zero hits.)
8. **Phase 7 COMMS (resolution)** — write this message too. State the guarantee precisely (was any
   real credential ever live/usable in this drill? say so honestly).
9. **Phase 8 POSTMORTEM** — name ONE concrete prevention artifact this incident should produce.
   (Hint: it already exists in this repo as of this session — which file?)

## 4. Definition of Done
1. All 9 sub-answers in §3 given BEFORE opening the gated solution.
2. The named gate (§2's scan) shows zero hits after remediation (fixture removed).
3. Both comms messages (Phase 2 + Phase 7) are written out, not just described.
4. Phase 8's prevention artifact is named as a real `file:line` in this repo, not invented.
5. You wrote `runbook/T-SEC-01_leaked_key.md` in [CARD_FORMAT.md](../CARD_FORMAT.md) — this one
   should read as a mini-incident report, not just a bug card (all 8 phases summarized into the
   card's Diagnosis/Fix/Evidence fields).
6. Logged the pass in [../../learning/LEARNING_LOG.md](../../learning/LEARNING_LOG.md).

## 5. Reset
```bash
python simulation/faults/reset.py    # removes the fixture, clears the active-fault log
```

> When you've answered all of §3 — THEN open the gated solution: `../.solutions/T-SEC-01_leaked_key.md`.
