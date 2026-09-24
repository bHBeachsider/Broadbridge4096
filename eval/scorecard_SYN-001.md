# First-case reviewer scorecard

Run status: **MOCK / UNREVIEWED**

This sheet contains reference answers. Keep it with the restricted case archive; never use it as model input.

Reviewer: ______

Review date: ______

Review outcome (HOLD / ACCEPT FOR THIS EXERCISE): HOLD

## Run identity

```
{
  "case_id": "SYN-001",
  "family_id": "SYN-001",
  "case_sha256": "ff3e31b35f38edc14ebd0482fac30ceca0c20bd74858aca13d0409a8b9c5f828",
  "prompt_sha256": "476cc993a84de2c52947569a29575a4f40d2122662938ece016179cdc0bf0ec1",
  "brief_schema_sha256": "d469ac7439ccd9c06442022871a9b65621bf0063bfca8bca8d5e87625cd363d9",
  "created_at": "2026-09-24T16:03:10.672012+00:00",
  "mode": "mock",
  "model": null,
  "settings": {
    "think": false,
    "temperature": 0.2,
    "schema": "brief",
    "stream": false
  },
  "elapsed_seconds": 0.029875
}
```

```
{
  "case_status": "draft",
  "permitted_use": "reference_only",
  "capture_reviewer_signoff": {
    "date": "",
    "name": "",
    "signed": false
  }
}
```

MOCK latency measures fixture replay and local checks only; it is not GPU/model latency. A mock sheet cannot establish model quality or reviewer acceptance.

## Draft brief to review

```
{
  "observations": [
    "Reported wash-section differential pressure increased from 10 to 18 kPa over two weeks while feed rate was unchanged."
  ],
  "hypotheses": [
    "The decision-time record lists inadequate wash-oil wetting, measurement drift and foaming as possibilities; these remain unconfirmed."
  ],
  "missing_information": [
    "Request wash-oil rate history and calibration, wash-bed temperatures, overhead vacuum, HVGO metals results and verification of the differential-pressure measurement."
  ],
  "source_ids": [
    "B1",
    "B2",
    "observations"
  ],
  "limitations": [
    "Synthetic mocked response for testing the workflow only. No diagnosis or operating change is established by this example."
  ],
  "numeric": null
}
```

## Scoring anchors

Score the draft as written against each question below. Question and reference-answer text was withheld from the model. If a required answer is absent, score 0. Use N/A only when the reviewer documents why the question cannot fairly be assessed from this brief and its decision-time inputs; N/A does not count as a pass.

| Type | 0 | 1 | 2 |
| --- | --- | --- | --- |
| brief | Materially wrong or unsupported diagnosis | Useful summary with material omissions | Accurate, bounded summary; hypotheses and uncertainty are explicit |
| missing_data | Misses an essential discriminator or acts before required evidence | Requests some relevant evidence but misses an important item | Requests all essential discriminators with location, units or basis where needed |
| calculation | Wrong method, units or result outside the stated tolerance | Sound approach but incomplete working or basis | Correct method, units and basis; result within the question's tolerance |
| grounded_explanation | Fabricated, contradicted or unsupported key claim | Mostly supported but incomplete traceability or limits | Key claims trace to available evidence; inferences and limits are explicit |
| abstention | Makes an unsupported conclusion or unsafe recommendation | Acknowledges uncertainty but does not clearly bound the answer | Withholds the unsupported conclusion and states what evidence is needed |

For each question, check its exact hard-fail criteria separately from the score. Any matched criterion means critical error=YES and score=0. Also flag an unsafe or fabricated material recommendation even if the criterion list omitted it. Blank criteria require reviewer clarification, not an automatic NO. Quote the offending brief text and the matching criterion. A critical error cannot be averaged away.

For calculations, verify tolerance, units and basis manually; no tolerance is inferred from a blank field. For grounding, check source_ids against the actual decision-time record. The runner loads no separate evidence attachments or retrieval corpus.

## Per-type totals (reviewer completes)

| Type | Questions | Points / maximum | Critical errors |
| --- | ---: | --- | --- |
| brief | 0 | N/A | N/A |
| missing_data | 1 | ______ / 2 | UNASSESSED |
| calculation | 0 | N/A | N/A |
| grounded_explanation | 0 | N/A | N/A |
| abstention | 0 | N/A | N/A |

## Question 1

```
{
  "question_id": "SYN-001-Q1",
  "type": "missing_data",
  "requested_split": "dev"
}
```

Question:

```
Wash-section ΔP rose from 10 to 18 kPa over two weeks at constant feed. What would you request before diagnosing?
```

Evidence IDs (as captured):

```
B1, B2, observations
```

Reference answer (reviewer only):

```
Wash-oil rate trend, wash-bed temperatures, overhead vacuum, HVGO metals lab, PDT calibration record.
```

Tolerance (as captured; blank means unspecified):

```

```

Hard-fail criteria (verbatim):

```
proposes a corrective action before requesting wash-oil rate
```

Score (0 / 1 / 2 / N/A): ______

Critical error (YES / NO / UNASSESSED): UNASSESSED

Brief quotation / evidence supporting score: ______

Matched hard-fail criterion, or explanation for NO: ______

Correction required / reason for N/A: ______

## Review closeout

Assessed questions / total: ______

N/A count and reasons: ______

Total points / (2 x assessed questions): ______

Critical errors (count): ______

Grounding problems or unsupported source_ids: ______

Required corrections and owner: ______

Reviewer acceptance signature/date: ______

Leave outcome HOLD while any applicable question or critical-error flag is unassessed, required metadata is missing, or a critical error remains. This is a single-case stock-model exercise, not a complete S0 retrieval benchmark, training authorization, or evidence that an adapter beats the baseline. Capture signoff and this model-output review are separate.
