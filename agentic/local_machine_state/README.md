# `local_machine_state/` — the last things that existed only on one laptop

Preserved 2026-08-21 during a deliberate "the building is on fire" sweep:
everything here was local-only and would have gone with the machine. Neither
item is load-bearing; they are saved because that judgement is cheap to get
wrong.

## `stash-superseded-a6-closeout-draft.patch`

The single `git stash` entry, labelled by its own author
*"On agent/a6-pilot-selection-closeout: codex superseded A6 closeout draft"* --
so it was already superseded when stashed. 113 lines touching
`doc/DECISION_LOG.md` (+29) and `doc/RESEARCH_STATUS.md` (+52/-37).

Do **not** `git apply` it blindly. Both files have moved on, and the decision
log must only ever record ratified gate closures. If you want the content, read
it and re-derive.

## `dot-claude-settings.local.json`

The untracked `.claude/settings.local.json`: Claude Code tool-permission
settings for this project, and the reason agents behaved consistently on that
machine. Copy it to `.claude/` in a fresh clone to get the same permissions. No
secrets, no scientific content.

## Checked and found NOT at risk

- Branches `agent/a6-pilot-selection-closeout` (`c663fcf`) and
  `agent/a6-holdout-implementation` (`71c93d1`) looked orphaned -- one had no
  upstream, the other's remote was deleted. `git cherry origin/main <branch>`
  showed every commit already equivalent in `main`. Nothing lost. (`c663fcf`
  also survives as `origin/cursor/a6-local-preflight-5fa0`.)
- Every other local branch tracks a live remote and is pushed.
- Raw experiment evidence under `src/runs/` is gitignored **by design** and is
  deliberately NOT here. It lives on Unicorn and still needs an independent
  backup -- see `../01_STATE.md` for which tree to prioritise and why.
