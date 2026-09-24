# Repository publication and audit

24 September 2026. Brad explicitly authorized publication after the v3 corrections. The canonical brief and domain tooling belong in Broadbridge4096; the generic engine belongs in slm-foundry. These commands use ordinary pushes, not force pushes. Final remote commit IDs are reported in the task after push verification.

## Audit before publication

| Repository or artifact | Result |
| --- | --- |
| Broadbridge4096 main tracked tree and history | No blob over 5,000,000 bytes. Existing origin is bHBeachsider/Broadbridge4096 (public). |
| slm-foundry master, feat/nast-pack-phase0-1, codex/broadbridge-gate1-data-training and reachable history | No tracked file or historical blob over 5,000,000 bytes; no size-triggered model/dataset blocker. |
| Existing tracked Broderick brain pairs | 198,676 bytes; retained as instructed. |
| Existing tracked Broderick operators | 71,242 bytes; retained as instructed. |
| Untracked AWS workbook inspection log | 5,874,311 bytes; generated QA, ignored via output/**/*.inspect.ndjson. |
| Untracked multimodal workbook inspection log | 5,819,403 bytes; generated QA, ignored via output/**/*.inspect.ndjson. |

Foundry git check-ignore --no-index verified all nine probes: data/, outputs/, packs/oil-gas/data/, packs/broderick/brain/data/, .env, venv/, .venv/, *.gguf and *.safetensors. Ignore rules do not untrack existing files or erase history. No tracked-data removal or history rewrite is part of this publication.

Both repositories already carry * text=auto eol=lf with binary overrides. Stage explicit files, verify git diff --cached --check, and inspect the staged inventory. Do not use git add -A. Preserve Foundry's unrelated untracked Broderick/stripe work.

## Broadbridge4096

Commit the corrected plan and canonical fallback changes, README and remaining planning documents/reference artifacts. Keep Energy Trading/, tmp/, venv/, __pycache__/, Office lock files, output ZIP archives, inspection logs and real pack data/outputs ignored. The Energy Trading junction and original source files remain intact. README links to unpacked reference examples rather than ignored ZIPs.

```powershell
Set-Location C:\Users\bradu\Documents\Broadbridge4096
git diff --cached --check
git diff --cached --stat
git commit -m "docs: publish canonical case intake and staged baselines"
git push origin main
git fetch origin main
git log origin/main -1 --oneline
```

## slm-foundry

The preflight found no local remote and no existing bHBeachsider/slm-foundry repository. Ignore-only commit 56aa5bc brings master and feat/nast-pack-phase0-1 into line with the reviewed Gate 1 ignore rules. Merge 850df0b incorporates that ancestry into codex/broadbridge-gate1-data-training; its final tree is unchanged from reviewed commit cd9fc19. All three branches now have identical ignore rules. The earlier mainline work is retained; no history was rewritten.

```powershell
Set-Location C:\Users\bradu\Documents\slm-foundry
gh repo create bHBeachsider/slm-foundry --private --source . --remote origin
gh repo view bHBeachsider/slm-foundry --json nameWithOwner,url,visibility
git push -u origin master
git push -u origin feat/nast-pack-phase0-1
git push -u origin codex/broadbridge-gate1-data-training
git fetch origin
git log origin/master -1 --oneline
git log origin/feat/nast-pack-phase0-1 -1 --oneline
git log origin/codex/broadbridge-gate1-data-training -1 --oneline
```

If creation reports an existing repository, inspect its owner, private visibility and remote history before continuing. Never overwrite another remote or force-push. No EC2 start, model call, training or deployment is part of publication.
