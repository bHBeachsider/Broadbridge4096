# Approved L4 relocation and runtime checks

29 September 2026. Brad approved creating one replacement L4 from a private image of the stopped source, trying alternate availability zones sequentially, and running the bounded runtime checks on the first successful launch. This supersedes the earlier existing-instance-only restriction for this relocation. It does not authorize model inference, a new model-weight download, training, a fleet, or production changes.

## Prepared scope

- Source: `i-0e5e1cbc7b1367566`, stopped, `us-east-1d`, retained with its original disk.
- Private image: `ami-0a425c55dcc606687`; snapshot `snap-0eff751f166d56c0f`, 200 GiB source gp3 volume. Public image access is false and the snapshot has no sharing permissions.
- Replacement type: `g6.2xlarge`, same L4 hardware. Try `us-east-1a`, then `1b`, `1c`, `1f` only after an explicit capacity rejection with no resulting instance. Stop after the first successful launch. No claim that offered zones have free capacity.
- Network: existing VPC, existing zone subnets and `sg-00c7894c78785b6c3`; only SSH ingress. IMDSv2 required, no instance profile. No public Ollama port.
- Replacement disk: 200 GiB gp3, 3,000 IOPS, 125 MiB/s, encrypted at launch; source disk and snapshot retained. These retained resources have storage charges independently of stopped compute.
- Session: at most 90 minutes from the first launch request, including failed zone attempts. Guest deadline at minute 80 and an independent local stop watchdog at minute 85. Immediate cleanup on completion/failure; force-stop/guest-bypass fallback after three minutes of unsuccessful normal cleanup or by minute 87, whichever comes first. Stop only the owned instance boot.
- Source image contents are copied; no application-level Qwen inference is requested. Reverify the cached 113-wheel runtime and both archives, install only the pinned candidate in an isolated venv, and run small synthetic GPU checks plus selected CPU tests if preflight passes.

## Offline validation

All **113 wheels / 3,792,751,006 bytes** and both transfer archives were reverified. Python parsing and LF shell syntax checks passed. The private launcher passed **9 mocked tests**: first-success stop, sequential capacity fallback, all-four failure, ambiguous-outcome halt, reconciliation of a timed-out successful launch, existing-token refusal, graceful cleanup, force-stop timing and changed-boot refusal. No network or GPU was used in those tests.

Private operational files are under Foundry `outputs/runtime-relocation-20260929-1326/`. Previous session evidence is preserved. Source and replacement use separate recorded identities. An uncertain launch outcome never permits moving to the next zone; the idempotency token is reconciled first.

## Capacity and prerequisite results

The private image and snapshot completed with no public sharing permissions. AWS rejected the sequential `us-east-1a` and `us-east-1b` attempts with `InsufficientInstanceCapacity`, then accepted the single replacement **`i-0439f5841d631d9f8` in `us-east-1c`**. No `us-east-1f` attempt was made. The replacement has encrypted root volume `vol-02363edb189de9088`; the original host and disk remain stopped and retained.

The session's first launch request was **13:36:03 UTC**. All subsequent activity retains the same **15:06:03 UTC / 11:06 a.m. Eastern** absolute deadline. The first preflight verified the L4, driver and disk but found no Python 3.11. Cleanup confirmed stopped at **13:43:58 UTC** after the bounded force-stop fallback. No runtime archive was transferred in that first attempt.

An intervening start request at 13:44:42 UTC received `InsufficientInstanceCapacity` and was confirmed stopped at 13:44:53 UTC. Further execution was held for Brad's explicit approval of Python 3.11, pip and headers, plus GCC only if missing. Brad approved that prerequisite installation and one further start, keeping the original deadline. That approved restart succeeded at **13:47:51 UTC** (AWS launch time 13:47:53 UTC). SSH host-key continuity and guest IMDSv2 identity were verified; the 80-minute guest guard and independent 85-minute API fallback were retained. The old-instance retry automation stays paused.

The reviewed transaction used only the `amazonlinux` repository at explicit release **2023.12.20260918**, with GPG checking and weak dependencies disabled. It installed **seven packages, 16 MB download / 69 MB installed**, without upgrades or removals:

- `python3.11`, `python3.11-devel`, `python3.11-libs`: `3.11.16-1.amzn2023.0.1.x86_64`.
- `python3.11-pip`, `python3.11-pip-wheel`: `22.3.1-2.amzn2023.0.14.noarch`.
- `python3.11-setuptools`, `python3.11-setuptools-wheel`: `65.5.1-2.amzn2023.0.7.noarch`.

GCC `11.5.0-5.amzn2023.0.5.x86_64` was already installed. The system Python 3.9 and NVIDIA driver were not changed. The explicit release flag, rather than an assumed `/etc/dnf/vars/releasever` file, pins this transaction. Do not substitute the image's advertised build date for the actual OS release observed on the guest.

At **13:51:04 UTC**, host preflight passed: Python **3.11.16**, glibc **2.34**, Python headers and GCC present; NVIDIA **L4**, driver **595.91.07**, **23,034 MiB** VRAM; **149,799,608,320 bytes** free before runtime transfer. These are host prerequisites, not a training qualification.

## Runtime transfer result

The runtime transfer started at **13:51:04 UTC**, but the private harness imposed `min(1800, remaining_transfer)` on SCP. It therefore timed out at **14:21:06 UTC**, before the nominal 50-minute transfer-phase boundary at 14:26:03 UTC. This was a controller limit, not an AWS capacity rejection or a tested CUDA incompatibility. Progress commentary incorrectly used the later phase boundary when estimating the remaining transfer window; the actual 30-minute command cap was shorter.

The last measured partial archive was **3,523,805,184 of 3,792,842,240 bytes (92.9%)** at 14:20:44 UTC. The exact durable prefix at shutdown is unverified and must be checked before resumption. The controller never reached hash verification, extraction, candidate venv creation, installation or GPU/pytest execution. **On-host GPU probes: 0; selected on-host CPU tests: 0.** Python OS prerequisites remain installed.

Normal stop was requested at 14:21:09 UTC; the bounded force-stop fallback was requested at **14:24:12 UTC**. The controller confirmed **stopped at 14:26:58 UTC**, **50 minutes 55 seconds** after the relocation's first launch request, before the original 15:06:03 UTC deadline. A separate AWS check confirmed both the replacement and original host stopped. The local controller and watchdog exited.

Private receipts and logs are retained in Foundry `outputs/runtime-relocation-20260929-1326-resume/`; earlier attempts are preserved. No new Qwen checkpoint download, model inference, training, datasets, database/R2 operations or production changes occurred. The private image carries the original disk contents; this is distinct from acquiring the trainable Hugging Face checkpoint.

## Prepared recovery; not executed

A resumable transfer helper passed **nine offline tests**, including a real local OpenSSH SFTP client/server transfer with invented bytes. It compares the retained remote prefix's SHA-256 with the exact local prefix before `reput -f`; completed files are skipped only after a full hash match. Oversized, changed or unexpected files are rejected without overwrite. The unchanged installer still checks every complete archive/script hash and every wheel before candidate admission. SFTP resume alone is not integrity verification; see the [OpenSSH manual](https://man.openbsd.org/sftp.1).

The prepared driver uses an explicit absolute transfer cutoff, without a hidden 30-minute command ceiling, and retains strict SSH identity, guest identity, the original 80/85/90-minute controls and no automatic repeat start. Runtime installation, GPU checks and model/smoke qualification remain open. A further paid start requires a new explicit decision; preparing or testing this helper does not authorize one. The existing heartbeat remains paused.

A further-start question was presented with a **14:33 UTC / 10:33 a.m. Eastern** latest-start cutoff and the unchanged 15:06 UTC shutdown deadline. No approval arrived before that cutoff, so no additional start was made. The prepared driver's time guard now refuses that expired start window. A later attempt needs a newly approved session window and a fresh private receipt; do not edit old receipts to manufacture additional time.

## Later bounded attempt: both hosts capacity-blocked

**29 September 16:47 UTC retry:** Brad authorized a new bounded attempt using whichever existing host was available. The replacement in `us-east-1c` and then the original in `us-east-1d` each returned `InsufficientInstanceCapacity`; neither started. Both were independently confirmed stopped with unchanged launch times. The verified wheelhouse, replacement Python prerequisites and partial upload are preserved. All 18 offline selection/resume tests passed. No guest command, new transfer, installation or GPU test ran. Retry automation remains paused. [Receipt](evidence/aws-runtime-bundle-2026-09-28/retry-pair-2026-09-29-1647.json).

The new session was prepared privately at Foundry `outputs/runtime-session-20260929-1645/`, with a fresh maximum 90-minute budget starting at 16:47:21 UTC. It made one start request per candidate, sequentially: replacement at 16:47:21 UTC, original at 16:47:32 UTC. The selection guard required an unchanged stopped boot after each explicit capacity rejection before falling back. An ambiguous error or any running host would have stopped selection. No replacement instance, image, disk, network rule or IAM resource was created in this attempt. Earlier receipts and deadlines were not changed.
