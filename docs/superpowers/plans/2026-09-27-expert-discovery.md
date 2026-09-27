# Engineering Discovery Questionnaire and Brainstorm Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Use one implementation lane. Steps use checkbox (`- [ ]`) syntax for tracking. Do not dispatch subagents from this plan.

**Goal:** Deliver an authenticated, categorized questionnaire with a separate free-form brainstorm recording/transcript workspace, source-linked normalization proposals and participant review.

**Architecture:** Extend released Broadbridge Capture. Keep discovery enrollment separate from access to engineering cases. Store versioned domain records in the dedicated Neon schema and original media in private R2. Reuse Foundry's local processing boundary for transcript/normalization jobs; app recording, speech transcription and semantic normalization are separate observable states.

**Tech Stack:** Existing Next.js App Router, React/TypeScript, Auth.js, Zod/JSON Schema, Neon parameterized SQL, private R2, Python/psycopg/pytest and the Foundry normalized-document contract. Browser MediaRecorder handles capture only. No new hosted provider or training runtime is provisioned by implementation.

**Spec:** [system design](../specs/2026-09-27-expert-discovery-design.md), [question copy](../../questionnaires/ENGINEERING_DISCOVERY_V1_DRAFT.md), [UI/UX handoff](../../questionnaires/ENGINEERING_DISCOVERY_UX.md).

Status: written plan for Brad's review after his approval of the initial design and requested revisions. No task below is implemented by adding this file. Preserve the requested single-lane/draft-PR execution method.

## Global constraints

- Proposed live entry: `/discovery`; it must not be represented as deployed until release verification succeeds.
- Existing `CAPTURE_ALLOWED_EMAILS` remains the engineering staff permission boundary. Discovery participation alone never confers case, scoring or ingestion access.
- Add `DISCOVERY_ALLOWED_EMAILS` for sign-in eligibility only; database study enrollment still gates each discovery action.
- Keep `broadbridge.case_record/1`, `broadbridge.workflow/1` and `foundry.training_example/1` unchanged.
- Dedicated Broadbridge database only: pooled `BROADBRIDGE_DATABASE_URL` at runtime; matching `DATABASE_URL_UNPOOLED` only for migrations.
- Development migrations and fixtures use a verified dev branch or owned local PostgreSQL, never production.
- No EC2, training, production migration/deployment or invitation email without the existing separately recorded authorization.
- No private audio/transcript sent to OpenRouter or another external inference service by default; unavailable local processing remains visible.
- Pilot limits: 15 minutes per audio clip (recorded or uploaded), 50 MiB per audio upload, 1 MiB per supplied transcript and 256 KiB per response revision. Segment/paginate long transcripts; never silently truncate.
- Do not persist secrets, signed URLs, real participant responses or recordings in public Git or application logs.
- Questionnaire definitions and submitted response/interpretation revisions are immutable; edits append revisions.
- Audio storage success, transcription success, interpretation confirmation, engineering acceptance and training admission are separate states.
- Stage named files only; all PRs draft. Do not merge an old ingestion snapshot over current released app changes.

## Review focus

1. A discovery participant follows a copied case/review/media URL: deny across pages, actions, exports and playback, including existing routes (tasks 1, 3, 4).
2. A recording includes several topics, a retraction and an issue outside the questionnaire: preserve every passage and return explicit suggestions/unresolved items without overwriting typed answers (tasks 5, 6).
3. Navigation, microphone denial, expired auth, upload failure or an unavailable worker: preserve recoverable input, distinguish unsaved/saved/queued states and avoid accidental recording (tasks 3, 4, 7).
4. Two tabs or normalization against an older transcript/answer revision: conflict; no silent overwrite or stale confirmation (tasks 2, 5, 6).
5. Group audio and speaker attribution: own-response access does not expose an entire shared recording; facilitator review is not participant confirmation (tasks 1, 4, 6).

## Deliverables and dependencies

A. **Questionnaire + brainstorm capture:** tasks 1-4. A usable form, persistent answers, recording/upload and transcript input with truthful pending states.
B. **Verbal interpretation + feedback:** tasks 5-7. CPU transcript parsing, bounded local processing, source-linked suggestions, review and repeat rounds.
C. **Preview acceptance:** task 8. Both paths verified before the full experience is promoted.

A can be evaluated without a running model, but must not advertise automatic transcription/normalization as complete. B depends on A's exact ownership and revision contracts. The two delivery PRs can be reviewed independently; deployment of either remains explicit.

## Task 1: Isolate discovery identity from engineering access

**Files**
- Modify `apps/capture/lib/auth-policy.ts`, `auth.ts`, `app/signin/page.tsx`, `app/page.tsx`, `.env.example`.
- Create `apps/capture/lib/discovery/access.ts`, `tests/discovery-access.test.ts`.
- Extend `tests/auth-policy.test.ts`, `tests/auth-config.test.ts`, `tests/actions.test.ts`.

**Interfaces**
- Keep `allowedEmail(value, env)` and `requireActor(): Promise<string>` restricted to existing capture staff.
- Add `signinEmail(value: unknown, env = process.env): string | null`: normalized membership in the union of the two explicit email lists; malformed configured lists fail closed.
- Add `requireSigninActor(): Promise<string>`: verifies signed-in identity only.
- Add `requireDiscoveryAccess(actor: string, studyId: string, capability: "respond" | "facilitate" | "administer"): Promise<void>`: current database enrollment/role check from task 2.
- Existing staff landing remains capture; a discovery-only identity is directed to discovery without reading shared cases.
- Task 1 tests inject an enrollment reader for the authorization boundary; task 2 supplies and exercises the real database implementation. Do not deploy discovery access between these tasks.

- [ ] Write policy and action tests, including the following concrete boundary:
```ts
const env = {
  CAPTURE_ALLOWED_EMAILS: "staff@example.invalid",
  DISCOVERY_ALLOWED_EMAILS: "guest@example.invalid",
};
expect(signinEmail("guest@example.invalid", env)).toBe("guest@example.invalid");
expect(allowedEmail("guest@example.invalid", env)).toBeNull();
expect(signinEmail("stranger@example.invalid", env)).toBeNull();
```
- [ ] Run `npm test -- tests/auth-policy.test.ts tests/discovery-access.test.ts tests/actions.test.ts` from `apps/capture`; record the intended failures.
- [ ] Use the union only at Auth.js normalization, verification-email issuance, sign-in, JWT and session identity boundaries. Update `authAvailability` to require a nonempty valid sign-in union; test staff-only, discovery-only and both-list configurations. Keep legacy `requireActor` staff-only. Recheck enrollment per discovery request; never trust a client-supplied email, role or participant ID.
- [ ] Test revocation with an existing session, malformed lists, protected return URLs and denial at `/`, `/review/*` and any integration branch's `/ingestion/*` actions. Preserve local test-outbox restrictions.
- [ ] Rerun focused auth/action tests and typecheck; commit only the named files.

## Task 2: Versioned questionnaire and discovery persistence

**Files**
- Create `packs/oil-gas/schemas/discovery_questionnaire.schema.json`, `discovery_response.schema.json`, `discovery_interpretation.schema.json`.
- Create `packs/oil-gas/discovery/questionnaire.v1.json` from the reviewed copy, retaining all 31 question IDs.
- Create the next unused SQL migration after checking main; at inspected main this is `packs/oil-gas/db/migrations/0007_discovery.sql`.
- Create `apps/capture/lib/discovery/contract.ts`, `repository.ts`, `tests/discovery-contract.test.ts`, `tests/discovery-repository.test.ts`.
- Create `packs/oil-gas/tests/test_discovery_db.py` and fabricated fixtures under `packs/oil-gas/tests/fixtures/discovery/`.

**Record contract**
```ts
type Answer = {question_id: string; task_id: string | null; text: string;
  state: "answered" | "unknown" | "not_applicable"};
type DiscoveryResponse = {
  schema: "broadbridge.discovery_response/1";
  response_id: string; study_id: string; session_id: string;
  questionnaire_version: string; answers: Answer[];
  new_issues: {id: string; text: string; kind: "task" | "rare_case" | "dissent" | "question"}[];
  status: "draft" | "submitted";
};
type StoredResponse = {record: DiscoveryResponse; revision: number};
```
Actor, owner, attribution, enrollment and consent records are server/database metadata; clients cannot forge them in the response. Store repeat task instances by stable `task_id`, and require nonrepeatable questions to use null.

**Interfaces**
- `parseDiscoveryResponse(value: unknown): DiscoveryResponse`, `questionCatalog(version: string)`.
- `loadDiscoveryResponse(actor: string, responseId: string): Promise<StoredResponse>`.
- `saveDiscoveryResponse(actor: string, record: DiscoveryResponse, expectedRevision: number | null): Promise<StoredResponse>`.
- `createDiscoverySession(actor: string, studyId: string, mode: "individual" | "facilitated"): Promise<{sessionId: string; responseId: string}>`.

- [ ] Create schema tests for invalid IDs, duplicate question/task pairs, wrong version, null versus unknown, extra actor fields, byte limits and unknown question IDs. Pin catalog grouping:
```ts
const catalog = questionCatalog("v1");
expect(new Set(catalog.questions.map(q => q.id)).size).toBe(31);
expect(catalog.questions.find(q => q.id === "D06")?.category).toBe("rare-cases");
expect(() => parseDiscoveryResponse({...validRecord, actor: "forged"})).toThrow();
```
Here `validRecord` is the committed fabricated response JSON; tests import it directly.
- [ ] Run schema tests and the new PostgreSQL tests before functions exist; verify failure is the missing contract/table, not a live target mistake.
- [ ] Implement questionnaire/study/enrollment/session/response revision tables, issue links, consent revisions and audit records. Enforce published-version immutability, session ownership, current enrollment and optimistic concurrency in SQL. Use the existing pooled runtime connection and migration tool.
- [ ] Reuse existing owned-local-PostgreSQL test support; verify A/B separation, two independent interview rounds, idempotent identical writes, stale revision rejection and no insertion into `cases` or `train_candidates`.
- [ ] Run `python -m pytest packs/oil-gas/tests/test_discovery_db.py -q` and the two Vitest files; commit named schema, SQL, domain definition, repository and test files. Document the actual migration number chosen; do not rewrite an applied migration.

## Task 3: Categorized form and review shell

**Files**
- Create `apps/capture/app/discovery/page.tsx`, `app/discovery/[studyId]/page.tsx`, `app/discovery/actions.ts`.
- Create `components/discovery/DiscoveryApp.tsx`, `TopicForm.tsx`, `ContributionReview.tsx`, `discovery.css`.
- Create `tests/discovery-ui.test.tsx`, `tests/discovery-actions.test.ts`, `e2e/discovery.spec.ts`.
- Read installed Next.js server/client and data-mutation documentation before writing components/actions; preserve the repository's existing framework version.

**Interfaces**
- `saveDiscoveryAction(input: unknown, expectedRevision: number | null)` returns `{ok:true,value:StoredResponse}` or `{ok:false,error:string,conflict?:boolean}`.
- `DiscoveryApp({initial: StoredResponse, catalog, capabilities})` owns selected category and dirty/save state; no direct DB client in browser.
- `ContributionReview` shows typed answers plus individually confirmed interpretations; pending proposals never count as confirmed answers.

- [ ] Write UI tests requiring six category labels, separate "Record a brainstorm", optional questions, repeat tasks, new issues, unknown values, visible failed saves and retained text after stale-response conflicts.
- [ ] Add a fabricated Playwright case:
```ts
await page.getByRole("button", {name: "Problems and priorities", exact: true}).click();
await page.getByLabel("A task or issue we have missed").fill("SYN: an overlooked commissioning handoff");
await page.getByRole("button", {name: "Save contribution", exact: true}).click();
await expect(page.getByRole("status")).toContainText("Saved");
await page.reload();
await expect(page.getByLabel("A task or issue we have missed")).toHaveValue("SYN: an overlooked commissioning handoff");
```
Run it under the local authenticated outbox fixture, never against production.
- [ ] Implement the UX handoff with existing fonts/tokens, responsive category rail/chooser, per-task context and server-confirmed autosave after 1.2 seconds of inactivity. Manual Save remains available. Expose save errors without discarding text.
- [ ] Keep the proposed product list in Tools and opportunities, after open discovery. Use accessible labels/focus and no forced full-form completion.
- [ ] Run focused Vitest/UI tests, typecheck and local Playwright; visually inspect desktop/mobile and light/dark; commit only this task's files and necessary shared styling.

## Task 4: Separate brainstorm recorder and private media lifecycle

**Files**
- Create `components/discovery/BrainstormRecorder.tsx`, `BrainstormWorkspace.tsx`.
- Create `lib/discovery/recording.ts`, `media-repository.ts`, `media-storage.ts`, `app/discovery/media-actions.ts`.
- Add media metadata and job lifecycle tables/functions in a new migration after task 2.
- Create `tests/discovery-recording.test.ts`, `tests/discovery-media.test.ts`, `e2e/discovery-recording.spec.ts`.

**Interfaces**
- `chooseRecordingMime(supports: (mime: string) => boolean): string | null`: first supported type among `audio/webm;codecs=opus`, `audio/mp4`, `audio/webm`.
- `prepareBrainstormUpload(actor, {responseId,filename,contentType,sizeBytes,sha256})`: checks access/consent/quota and returns a media ID plus short-lived upload authorization.
- `completeBrainstormUpload(actor, mediaId)`: checks receipt and transitions to stored-pending-byte-verification; CPU verification precedes parsing.
- `loadBrainstormMedia(actor, mediaId)`: returns only authorized metadata/playback access, never group media merely because the actor owns a linked response.

- [ ] Write failed-state recorder tests and a privacy regression:
```ts
expect(chooseRecordingMime(m => m === "audio/mp4")).toBe("audio/mp4");
expect(chooseRecordingMime(() => false)).toBeNull();
// In the browser fixture, navigation alone must never call getUserMedia.
expect(microphoneRequestCount).toBe(0);
```
The test fixture supplies the MediaRecorder/getUserMedia fakes and checks every track is stopped on stop/error/unmount.
- [ ] Implement the standalone workspace: optional title, consent, Start/Pause/Resume/Stop, assembled bounded Blob, preview, Save, Download, Discard and upload/paste alternatives. A question ID is never required to create a brainstorm.
- [ ] Reuse the existing R2 signing pattern from the reviewed ingestion branch deliberately; do not merge that branch wholesale. Verify actual SDK versions from its lockfile before adding dependencies. Use a discovery-specific private object prefix, unique key and 5-minute authorization; metadata checks are not proof of byte integrity.
- [ ] Limit new pending uploads to five per participant and 250 MiB reserved bytes until completed/expired; incomplete registrations expire after 24 hours and cleanup records the disposition. Existing source content is never purged as part of this quota.
- [ ] Stop browser recording when either its duration or byte cap is reached, preserving the clip. Worker validates actual size/hash, decodable format and the same 15-minute maximum for uploaded audio; a mismatch remains rejected. Keep every lifecycle state explicit and idempotent. Use no media bodies in ordinary Vercel action requests.
- [ ] Test actor/session mismatch, forged ownership, guessed IDs, MIME disguise, over-limit clip, failed PUT, expired auth, whole-group download denial and unavailable worker. Use local transport/fabricated audio; no microphone action in a real user browser.
- [ ] Run media tests and recorder Playwright; commit task files. This completes a functioning capture path, not automatic speech acceptance.

## Task 5: Transcript parsing and local processing bridge

**Files**
- Foundry: create `src/ingestion/transcript_segments.py`, `schemas/transcript_segments.schema.json`, `tests/test_transcript_segments.py`.
- Broadbridge: create `packs/oil-gas/scripts/discovery_worker.py`, `tests/test_discovery_worker.py`; extend media/job SQL in its next migration.
- Create `apps/capture/lib/discovery/transcript-repository.ts`, `tests/discovery-transcripts.test.ts`.

**Interfaces**
- `parse_transcript(data: bytes, *, format: str) -> dict`: TXT/VTT/SRT input; output `foundry.transcript_segments/1` with source hash and segment IDs, exact text, optional start/end seconds and optional speaker labels.
- `process_discovery_media(job, *, storage, transcriber, repository) -> dict`: injected dependencies, bounded reads, verified bytes, current permission and lease checks.
- `transcriber` uses the existing local `convert_with_docling(..., kind="audio", artifacts_path=...)`; no implicit downloads or remote fallback.

- [ ] Create independent TXT/VTT/SRT fixtures, including multi-topic speech, malformed times, repeated speakers, UTF-8 BOM, missing times and instruction-like text. Pin the plain-text behavior:
```python
result = parse_transcript(b"SYN: this is an untimed brainstorm.", format="txt")
assert result["segments"][0]["start_seconds"] is None
assert result["segments"][0]["text"] == "SYN: this is an untimed brainstorm."
```
- [ ] Run `python -m pytest tests/test_transcript_segments.py -q` in Foundry and the domain worker tests before implementation; require intended failures.
- [ ] Preserve supplied timings exactly; reject invalid ranges rather than repairing them silently. Label unsupplied speakers unknown. Split oversized text into documented, source-offset-bearing segments without dropping bytes.
- [ ] Implement the domain worker using existing job leases, private storage and database publication patterns. Record parser/ASR versions, artifact manifest hashes, source checksum, attempts and reason for unavailable/rejected states. Only configured pre-provisioned local artifacts may run.
- [ ] Add actual speech acceptance as a separately executed local test: a permitted fabricated recording, independently written transcript, declared model/artifact hashes and measured errors on numbers/units/negation/tags. Simulated ASR cannot close this check. No EC2 is authorized; if CPU artifacts are unavailable, report this as a remaining live-processing prerequisite.
- [ ] Re-run Foundry extraction/Docling regression tests and domain worker tests; open separate draft Foundry/domain PRs with explicit dependency heads. No actual participant recording is a Git fixture.

## Task 6: Source-linked normalization proposals and review

**Files**
- Foundry: create `src/ingestion/transcript_proposals.py`, `tests/test_transcript_proposals.py`.
- Broadbridge: create `packs/oil-gas/discovery/normalization_prompt.md`, `normalization_policy.json`, `tests/test_discovery_normalization.py`.
- App: create `lib/discovery/proposals.ts`, `proposal-repository.ts`, `components/discovery/BrainstormReview.tsx`, `tests/discovery-proposals.test.ts`.
- Add versioned proposal/interpretation/audit SQL in the next new migration.

**Interfaces**
- `validate_transcript_proposals(value, *, transcript, question_ids) -> dict`: exact segment/span resolution, target-question validity, proposal kinds and typed semantics.
- Proposal kinds: `answer`, `new_issue`, `rare_case`, `clarification`, `context`; each has text, source spans, proposed question IDs, uncertainty flags and a pending disposition.
- `confirmDiscoveryProposal(actor, proposalId, expectedProposalRevision, expectedResponseRevision, decision)`: updates neither original transcript nor existing typed answer; creates an explicit accepted addition/correction after access/concurrency checks.

- [ ] Write a fixture transcript containing three topics, one retracted numerical value and a genuinely new issue. Expected mappings/flags are independently authored; test fabricated span/quote, no-match passage, multiple matches, contradiction and existing typed-answer conflict.
```python
bad = {"kind": "answer", "question_ids": ["NOT-A-QUESTION"], "source_spans": [], "text": "invented"}
with pytest.raises(ValueError):
    validate_transcript_proposals({"proposals": [bad]}, transcript=fixture, question_ids={"B01"})
```
The test imports an exact fabricated transcript fixture; no private source text.
- [ ] Implement schema/span checks and preserve all unassigned segments in a remaining-passages queue. A matching quote does not prove interpretation truth; human confirmation remains required.
- [ ] Use the existing local-only model client with `think=False`, schema-constrained output and explicit configured model route. Do not call it merely because a recording arrived. Job authorization/consent and current source state are checked before each call; no cloud or second-model retry.
- [ ] If local inference is unavailable, manual passage-to-question/new-issue mapping is functional and suggestions remain unavailable. Do not generate canned responses and label them model interpretation.
- [ ] Implement per-card source playback/text, Accept/Edit/Move/New issue/Reject/Later controls. A contradictory proposal cannot silently overwrite a prior answer; show both and record resolution. Re-transcription invalidates pending/accepted derivative references until re-reviewed.
- [ ] Run validator/domain/app tests, confirm pending proposals cannot create signed cases or training examples, and record a real normalization acceptance result separately from mocked transport tests. Commit only scoped files.

## Task 7: Feedback rounds and rare-issue visibility

**Files**
- Create `lib/discovery/summary.ts`, `components/discovery/DiscoverySummary.tsx`, `app/discovery/[studyId]/review/page.tsx`.
- Create `tests/discovery-summary.test.ts`, `e2e/discovery-review.spec.ts`.
- Extend study-round and decision records through a new migration where needed.

**Interfaces**
- `summarizeDiscovery(records, interpretations)`: returns separate recurring-task, rare/high-consequence, dissent/unresolved lists; counts unique respondents and sessions explicitly.
- `createFollowupRound(actor, studyId, resultReference)`: new round linked to exact artifact/version, never reuses the old response identity.

- [ ] Test one severe issue remains present alongside twenty repeated low-impact comments:
```ts
const summary = summarizeDiscovery(fabricatedResponses, confirmedInterpretations);
expect(summary.rareIssues.some(x => x.issueId === "SYN-RARE-01")).toBe(true);
expect(summary.respondentCount).toBe(new Set(fabricatedResponses.map(x => x.owner)).size);
```
Both arrays come from versioned fabricated fixtures with intentionally repeated sessions.
- [ ] Implement filters, evidence links, named triage decisions and explicit unknown denominators. Automated clusters cannot erase original wording, dissent or unmatched topics.
- [ ] Add R01-R06 only to linked follow-up rounds. Preserve old rankings/answers, and distinguish participant feedback from qualified engineering acceptance.
- [ ] Nomination to a canonical case creates a draft only through existing validation, with source and family ancestry. Locked test details are never fed back into a generator.
- [ ] Run summary/UI/round tests and commit scoped files.

## Task 8: End-to-end acceptance and deployment handoff

**Files**
- Create `scripts/research/smoke_discovery.py`, `apps/capture/e2e/discovery-flow.spec.ts`, `docs/DISCOVERY_CAPTURE.md`.
- Add a narrowly scoped CI workflow using the existing lockfiles/test infrastructure. No production secrets in CI.

- [ ] Build an owned local PostgreSQL + loopback SQL/R2/outbox harness following the existing capture acceptance patterns. Refuse non-loopback endpoints or inherited production routing. Use three fake identities: staff, participant A and participant B.
- [ ] Exercise sign-in → categorized answers → free-form transcript/recording → saved original → proposal review → rare-issue summary → new feedback round. Verify database rows, content hashes, ownership, question IDs and audit actors directly.
- [ ] Attempt A-to-B reads/writes/downloads, discovery-to-case access and withdrawal/revocation before processing. Confirm denial and absence of side-effect writes.
- [ ] Run the existing app suite and typecheck/build plus new domain/Foundry tests. Record actual counts; do not treat skipped model/DB/browser tests as passes.
- [ ] Verify keyboard, desktop/mobile/light/dark, microphone failure, unsaved clip, stalled job and long transcript. Capture screenshots of the real preview states with fabricated data.
- [ ] Verify the Preview's database/bucket target before any synthetic upload. Apply migrations to the verified dev target with the existing `db.py migrate` command using its explicitly matched unpooled URL. Never apply production migrations as part of this task.
- [ ] Publish draft PRs only; report head hashes, checks, Preview URL, synthetic row counts, live speech/normalization results and remaining human steps. `gh pr checks N --repo ...` without `--watch`.
- [ ] Brad reviews the real Preview and decides production promotion separately. Only after migration/deployment acceptance succeeds should documentation advertise the permanent `/discovery` URL as live.

## Plan review and execution method

Document self-review: all six categories and 31 stable question IDs are covered; recording/normalization and rights/engineering acceptance remain separate; auth availability and media duration limits are consistent across the copy, UX and tasks. The existing one-lane execution method is preserved. Review this plan together with the revised question copy and UX handoff before implementation. A real recording workflow must not be represented by a nonfunctional Record button; a queued/unavailable processing state must be honest about what has and has not run.
