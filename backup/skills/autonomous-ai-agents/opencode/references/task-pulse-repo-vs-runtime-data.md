# Task Pulse: repo code vs runtime snapshot data

Use this when a requested Task Pulse fix appears to require editing historical task JSON.

## Rule

If the source of truth lives under `.task-pulse-data/`, treat it as **runtime state**, not durable repo content.

- `.task-pulse-data/` is gitignored
- edits there can fix the current machine/view
- edits there do **not** survive a clean deploy or help reviewers understand the real fix

## What to do instead

1. check whether the user explicitly wants the fix "in the repo"
2. if yes, implement the durable behavior in repository code:
   - read-path migration
   - normalization on load/write
   - compatibility mapping from old category/group fields to new ones
3. if needed, also let the code rewrite the old snapshot on read so runtime state self-heals over time
4. keep groupName/groupId normalization after the migration step so historical tasks do not split into new groups accidentally

## Example pattern

For an old task stored as category `chat` that really belongs to `novel`:

- detect strong signals from stable fields:
  - `metadata.groupName` contains `小说创作`
  - prompt/title contains novel-writing keywords
  - `metadata.cwd` points at the novel workspace
- convert `chat -> novel` during snapshot load
- then run existing grouping normalization
- if anything changed, write the corrected snapshot back to disk

## Why this matters

Without a repo-level migration, you can end a session with:

- the live dashboard looking correct on one machine
- no reviewable git diff proving the durable fix
- the behavior regressing after redeploy because the edited snapshot file was never part of the repo
