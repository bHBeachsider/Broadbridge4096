# Engineering Discovery — questionnaire and brainstorm experience

Revision: draft-2, 27 September 2026. Based on Brad's approval of the first written design and request for a categorized questionnaire with a separate free-form verbal brainstorm.
This is a design handoff. It is not a deployed form.
[Question copy](ENGINEERING_DISCOVERY_V1_DRAFT.md) · [System design](../superpowers/specs/2026-09-27-expert-discovery-design.md).

## Two entry paths, one response workspace

Entry page title: **Help shape the engineering assistant**
Subtitle: **Tell us what would help, what we have missed, and where the usual answers fail.**

Primary choices:
- **Answer by topic** — Pick a section and write as much or as little as you wish.
- **Record a brainstorm** — Talk freely. We will help organize it for you to check.
- Supporting action: **Upload a recording or transcript**.

A participant can switch paths without starting another response. A free-form recording belongs to the session/response, not a required question ID. One session can contain multiple recordings, transcripts and typed contributions.

Show "Your contributions" with last saved time and processing states. "Review and submit" is always reachable. Submission confirms the contribution, not engineering sign-off, and processing an accepted recording can continue separately.

## Topic navigation

| Navigation label | Questions | What the page does |
| --- | --- | --- |
| About your work | A01-A03 | Experience, intended users and participation choices |
| Problems and priorities | B01-B03, C01-C02, C06 | Open discovery, task cards, practical impact and buyer/user context |
| Evidence and good answers | C03-C05, C07 | Inputs, evidence, useful outputs, dangerous answers and source nominations |
| Rare or difficult cases | D01-D06 | Exceptions, missing clues, initial beliefs, turning points and limits |
| Tools and opportunities | E01-E03 | Suggested product directions, software/formats and a bounded first demonstration |
| Experts and next steps | F01-F03 | Specialist input, disagreement and follow-up |
| Record a brainstorm | Session workspace | Record, upload/paste, play back and organize spoken contributions |
| Review your contribution | Review workspace | Typed responses, proposed matches, new issues and unresolved passages |

Repeat-feedback R01-R06 appear only for a follow-up study tied to an identifiable result/version. Internal question IDs are not the primary navigation labels. Preserve their existing meanings and links.

The open-discovery prompts appear before the suggested product list. Participants may skip or leave uncertainty; do not manufacture a completion percentage for optional questions. Show "3 topics contributed" and "2 suggestions to check", not an implication that every field is required.

Keep task cards associated with a stable task ID across the priorities/evidence pages. Show the selected task title when asking detailed questions. Add/remove task actions cannot orphan its evidence; an archived task stays in history.

## Record a brainstorm screen

Intro:
**You do not need to answer one question at a time. Talk about recurring problems, an unusual case, or an idea we have not considered. You can pause, change direction and come back to a point.**

Optional prompts, collapsed by default:
- What took more effort than it should?
- When did the usual explanation turn out to be wrong?
- What would you want a good assistant to prepare?
- What have we failed to ask?

Recording controls: **Start recording**, **Pause / Resume**, **Stop**, elapsed recorded time and microphone/activity indicator. No automatic start or browser speech service. User gesture and microphone permission are both required. Pause does not create a new contribution.

After Stop, show playback, optional title, **Save recording**, **Record another**, **Download a copy**, and **Discard unsaved recording**. Explain that a clip is only on this device until the server confirms storage. A failed upload retains the local clip in the open tab; retry or download remains available. Do not promise survival after a tab/browser crash.

Pilot limits: 15 minutes per audio clip (recorded or uploaded) and 50 MiB maximum, both enforced. Stop browser capture safely when either limit is reached. Longer interviews use multiple linked clips. These are configurable product limits, not browser guarantees. The upload path accepts a tested subset of WebM/Opus, MP4 audio, WAV and MP3; the worker validates actual format/duration before transcription. File extension alone is insufficient.

The browser chooses supported recording MIME types using runtime checks, not a hardcoded assumption. Recorded chunks are assembled in order into one bounded clip; a timeslice chunk is not assumed to be a standalone playable file. Stop/release every media track on finish, error or page exit. Never log raw audio, transcript text or media URLs.

Unavailable states:
- Permission denied: "Microphone access is off. You can enable it in your browser or upload a recording."
- No input device: "No microphone was found. Upload a recording or type your contribution."
- Unsupported browser: "Recording is unavailable in this browser. Upload a recording or transcript."
- Insecure origin: recording unavailable; use deployed HTTPS or local development.
- Limit reached: stop safely, preserve the clip and offer Save / record another.
- Session expired: preserve the unsaved clip while re-authenticating; do not claim it uploaded.
- Worker/model unavailable: "Recording saved. Transcription is waiting." Supply a transcript remains an option.

## Parse and normalize without losing meaning

Pipeline:
1. Store original audio with its checksum, session ownership and allowed processing.
2. Transcribe into stable segments with actual timing and anonymous speaker labels where supported.
3. Preserve the verbatim transcript. Corrections produce a new revision; a readable transcript is a separate view.
4. Segment by ideas/topics. One passage may relate to several questions; several passages may support one proposed answer.
5. Produce proposed answer cards and independent new-issue cards. Distinguish an observed event, opinion, hypothesis, suggestion and unknown.
6. Link every proposed claim to exact transcript segment/span references. Preserve the surrounding context for pronouns and cross-topic references.
7. Flag numbers, units, equipment tags, negation, conflicting statements and uncertain speaker attribution.
8. Ask the participant/facilitator to confirm, edit, reject, remap or leave the proposal unresolved.
9. Save accepted interpretations as versioned discovery answers/issues, keeping raw evidence and the named confirming actor.

Do not infer missing operating conditions, convert gauge/absolute pressure without explicit information, or turn "might" into "did". Deterministic unit parsing may annotate an explicitly stated value but must retain the original expression. Canonical engineering conversions/answers remain separately verified.

Generic transcript parsing and provenance live in Foundry; question mappings, engineering taxonomy and allowed semantics live in the Broadbridge pack. Transcript instructions cannot change schemas, reveal other records or grant rights.

Normalization is suggestion, not automatic field replacement. Existing typed answers are shown alongside proposed additions; contradictions become a decision to resolve. The participant's words may reveal a new task outside the questionnaire. Preserve it under "New ideas and issues" with optional category, not a forced nearest match.

## Review workspace

Desktop layout: transcript/audio evidence on the left; proposed cards on the right. Mobile: one card with a "Hear/read the source" disclosure directly above its actions. No hidden drag-and-drop requirement.

Queues:
- **Suggested answers** — matched question, proposed text and source passages.
- **New ideas and issues** — participant-originated tasks outside the current list.
- **Rare cases and exceptions** — unusual/high-consequence observations.
- **Needs clarification** — unresolved meaning, speaker, quantities or contradictions.
- **Remaining passages** — not mapped, reviewed as contextual/no-action only by an explicit decision.

Every card has **Accept**, **Edit**, **Move to another topic**, **Keep as new issue**, **Reject suggestion** and **Leave for later**, with relevant actions shown by type. Accept applies only to that version. No bulk "approve all" for a first pilot.

Display who confirmed the interpretation. Facilitator confirmation is not labeled participant confirmation or independent technical review. Never expose the whole group recording to a participant authorized only for one excerpt.

Illustrative fabricated example:
At 02:10 the speaker describes repeated data-cleaning work; at 04:35 they describe an unusual start-up problem. Produce a priority-task proposal and a separate rare-case card. If they later retract a pressure value, retain the contradiction/correction and request confirmation instead of choosing a number.

## Visual and accessibility handoff

Reuse IBM Plex Sans/Mono and existing capture light/dark tokens: --paper, --panel, --ink, --ink-2, --rule, --accent, --accent-soft, --warn and --bad. No new branding dependency.

| Element | Specification |
| --- | --- |
| Desktop shell | Max width 1440px; 240px topic rail; remaining content minmax(0,1fr); 24px gutters |
| Topic reading area | Max width 800px; one question/task card per row; 16-24px card padding |
| Two-column evidence review | Equal flexible columns with 24px gap at widths above 1000px |
| Mobile/tablet | At 820px or below replace rail with a labeled topic chooser; stack evidence/cards |
| Controls | Minimum 44px touch target; text plus icon for recorder states |
| Save state | Visible "Saving", "Saved at [time]" or "Not saved—retry"; only server receipt permits Saved |
| Text | Wrap long words/URLs; expandable text, no clipping of evidence or critical qualifiers |
| Focus | Visible focus, logical keyboard order; focus first validation error; return focus after dialogs |
| Status | Polite live region for upload/transcription/normalization changes; timer is not announced every second |
| Motion | Respect prefers-reduced-motion; no flashing recording indicator |
| Contrast | Verify light/dark text, borders and all state labels; do not communicate state by color alone |

Pause/stop and ordinary save controls remain distinct. Navigating with an active/unsaved recording warns about the specific unsaved item. An error never clears typed answers or source passages.

## Recording and model boundary

Browser recording uses MediaRecorder and microphone capture, not SpeechRecognition: some speech-recognition implementations may use a remote service, which would conflict with the intended explicit processing policy. Browser recording does not itself transcribe or understand an engineering story.

Transcription and structured interpretation are separate jobs. Reuse the private local-only Foundry path after actual speech/normalization acceptance; no EC2 is started automatically. With the local model route unavailable, keep proposals pending and allow manual passage mapping. Any cloud path would require separate exact-input permission and the user's provider-selection policy.

Sources checked 27 September 2026: [MediaRecorder](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder), [runtime MIME support](https://developer.mozilla.org/en-US/docs/Web/API/MediaRecorder/isTypeSupported_static), [microphone access](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia). Browser/device behavior still needs acceptance tests.
