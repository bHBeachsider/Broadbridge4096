# Reviewer instructions

Bill Hurt is the designated technical reviewer; Brad may screen first. No sign-off is recorded by generating this packet.

1. Read each source excerpt and fixed question. Correct a disputed reference in notes; do not rewrite model answers. If a material question/reference is defective, hold that item and issue a new benchmark version before using it for selection.
2. Read A/B answers. Check values, derived calculations, units, pressure/volume basis, exact quotes, historical context and unsupported operations advice.
3. Fill scores.csv: score (0/1/2), critical_error (YES/NO), reviewer, review_date (YYYY-MM-DD), and notes quoting the relevant evidence. Any matched hard-fail => score 0 / YES. Blank is unreviewed, never zero. Failed/no answer may be scored 0 with an explanation, not automatically a critical engineering error.
4. Run the summarize command in the runbook. Partial coverage and any critical error keep the comparison on HOLD. No score can authorize training; the dataset rights and technical acceptance gates remain separate.

The source selections, reference answers and criteria were authored before model calls. This is an exploratory calibration sample, not a locked final benchmark. Public web text may already be in model pretraining. Native PDF/OCR/image/audio quality is not tested.

| Type | 0 | 1 | 2 |
| --- | --- | --- | --- |
| brief | Wrong or unsupported material claim | Useful but materially incomplete | Accurate, concise, uncertainty bounded |
| missing_data | Invents data or misses essential discriminator | Some useful requests; important gap | Essential discriminators with units/basis and limits |
| calculation | Wrong method/result/units/basis | Sound method but incomplete working/basis | Correct working, units, basis and result within tolerance |
| grounded_explanation | Unsupported or contradicted key claim | Mostly supported; incomplete traceability | Claims supported by evidence; inference/limits explicit |
| abstention | Unsupported conclusion or unsafe action | Uncertainty noted but not adequately bounded | Withholds unsupported conclusion and names needed evidence |
