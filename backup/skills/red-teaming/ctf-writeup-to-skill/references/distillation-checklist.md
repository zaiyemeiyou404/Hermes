# Distillation Checklist

Use this checklist while converting a CTF challenge or writeup into reusable skills.

## 1. Artifact Intake
- What did I receive? (challenge text / binary / pcap / repo / blog / exploit script / screenshots)
- What is missing?
- What parts are source-of-truth vs commentary?

## 2. Challenge Classification
- Primary family: web / pwn / rev / crypto / forensics / osint / misc
- Secondary family if mixed:
- Evidence for this classification:

## 3. Reproduction Ledger
For each key step, mark one:
- observed directly
- reproduced locally
- reproduced remotely
- inferred only

Questions:
- What is the first decisive insight?
- What is the decisive primitive?
- What is the shortest solve chain that still works?
- Which steps are decorative rather than necessary?

## 4. Hidden Assumptions
List any assumptions that were not initially obvious:
- environment/version/libc assumptions
- challenge-specific paths
- timing/race assumptions
- local-only conditions
- disabled mitigations / debug conditions

## 5. Reusable Signals
What clues should trigger this technique in future tasks?
- code-level signals
- protocol-level signals
- binary mitigations / memory behavior
- ciphertext / data-shape signals
- filesystem / metadata / traffic signals

## 6. Preconditions
When does the method apply?
When does it definitely NOT apply?

## 7. Verification Points
For each major step:
- what hypothesis is being tested?
- what exact signal would confirm it?
- what result would falsify it?

## 8. Skill Shape Decision
Choose one:
- create a new technique skill
- patch an existing skill
- keep only a reproduction note

Reason:
- repeated enough?
- challenge-specific or general?
- strong enough verification to be reusable?

## 9. Final Extraction
The reusable skill should contain:
- When to Use
- Signals
- Preconditions
- Workflow
- Verification
- Pitfalls
- Boundaries

The reproduction note should contain:
- exact challenge context
- artifacts used
- challenge-specific offsets/paths/hosts/constants
- what was reproduced vs inferred
