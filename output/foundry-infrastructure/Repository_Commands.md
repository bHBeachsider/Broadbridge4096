# Repository handoff and proposed publication commands

24 September 2026. Local work is authorized; repository creation and pushes
require Brad's confirmation and are not executed by this task.

## slm-foundry local mainline and line endings

Run from C:\Users\bradu\Documents\slm-foundry after committing the reviewed
changes using explicit file paths. These operations are local and preserve
untracked Broderick/stripe work. Verify tracked changes are committed first.

```powershell
git status --short
git merge-base --is-ancestor master feat/nast-pack-phase0-1
git switch master
git merge --ff-only feat/nast-pack-phase0-1
git switch codex/broadbridge-gate1-data-training
git rebase master
git diff --check
git ls-files --eol
```

Both repositories add `* text=auto eol=lf` with binary document/image overrides.
Normalize tracked text with `git add --renormalize -- .` only after reviewing
uncommitted changes; never use `git add -A` here. In Broadbridge4096, exclude
the pre-existing README edit with `git add --renormalize -- . ':!README.md'`.
The task stages exact new/changed paths and separately records normalization.

The Foundry ignore rules cover data/, outputs/, packs/**/data/, .env, .venv/,
venv/, Python caches and model binaries. Ignore rules do not erase Git history.
Brad explicitly chose to leave these already tracked files in place for now:

- packs/broderick/brain/data/broderick_brain_pairs.jsonl
- packs/broderick/brain/data/broderick_operators.jsonl

Review those files and their history before publishing. No untracking, history
rewrite or deletion is authorized by the present choice.

## slm-foundry publication only after confirmation

There is currently no remote. Confirm the tracked-data review and repository
visibility before these commands. `gh repo create` below intentionally omits
--push so creation and publication remain separate reviewable operations.

```powershell
Set-Location C:\Users\bradu\Documents\slm-foundry
gh repo view bHBeachsider/slm-foundry
# If confirmed absent, and Brad approves creation:
gh repo create bHBeachsider/slm-foundry --private --source . --remote origin
git remote -v
git push -u origin master
git push -u origin feat/nast-pack-phase0-1
git push -u origin codex/broadbridge-gate1-data-training
```

If the repository already exists, inspect its owner, visibility and history
before adding a remote. Do not overwrite it or force-push.

## Broadbridge4096 local commit

Its existing origin is https://github.com/bHBeachsider/Broadbridge4096.git;
the local branch is main. The requested commit scope is eight planning files,
scripts, the two requested output directories, ignore/attribute rules and the
new domain pack. The pre-existing README edit and other output directories are
preserved outside this commit.

```powershell
Set-Location C:\Users\bradu\Documents\Broadbridge4096
Get-ChildItem output -Recurse -File | Where-Object Length -gt 5242880 |
    Select-Object FullName,Length
git add -- .gitignore .gitattributes `
  Broadbridge-Foundry-Implementation-Update.md `
  Broadbridge-Multimodal-SLM-CTO-Plan.md `
  Broadbridge-Oil-and-Gas-Expert-Knowledge-Capture.md `
  Broadbridge-Oil-and-Gas-SLM-Development-Plan.md `
  Broadbridge-Oil-and-Gas-Training-Source-Synthesis.md `
  Broadbridge-Training-Information-and-Internal-Use.md `
  Norm-Lieberman-Online-Source-Review.md `
  Oil-and-Gas-Expert-Knowledge-Business-Assessment.md `
  scripts output/docx output/foundry-infrastructure packs/oil-gas
git add --renormalize -- . ':!README.md'
git diff --cached --check
git diff --cached --stat
git commit -m "docs: establish domain pack and core SLM v0 handoff"
# Only after Brad confirms publishing this reviewed commit:
git push origin main
```

The pre-commit size inventory found two files above 5 MiB, both outside the
requested output directories and excluded from this commit:

| File under output/multimodal-implementation | Bytes |
| --- | ---: |
| Broadbridge_AWS_Implementation_Gantt.xlsx.inspect.ndjson | 5874311 |
| Broadbridge_Multimodal_Implementation_Gantt.xlsx.inspect.ndjson | 5819403 |

Energy Trading/ and tmp/ remain ignored. venv/, __pycache__/, Office lock files
and output/**/*.zip are also ignored. The Energy Trading junction and source
documents are preserved. No cloud instance is started by any command here.
