# Review: Tesoro Anacortes: CSB HTHA safety-alert news release, 11 August 2016

Run mode: **LIVE**. Review status: **UNREVIEWED**.

Use scores.csv for recorded scores. Reference answers below are DRAFTS for reviewer correction, not certified engineering answers.

Source: [U.S. Chemical Safety Board](https://www.csb.gov/csb-issues-safety-alert-stemming-from-fatal-tesoro-anacortes-investigation/); 11 August 2016.

Compare A/B without opening run.json or results.json (these disclose the model mapping). Labels switch between documents.

For each answer: 0 = wrong/unsupported, 1 = useful but incomplete, 2 = correct and bounded. Check the type anchors in REVIEW_INSTRUCTIONS.md.

Apply the exact hard-fail criteria separately: any match => critical_error YES and score 0. Also flag other material unsafe/fabricated claims. A valid JSON response or exact quote is NOT evidence of engineering correctness.

## Source excerpts

### CSB-TESORO-B01

```
The CSB’s investigation into the catastrophic failure of a forty-year-old heat exchanger at the Tesoro Refinery determined that the fatal explosion and fire was caused by a damage mechanism known as high temperature hydrogen attack, or HTHA, which severely cracked and weakened the carbon steel heat exchanger over time, leading to a rupture.
```

### CSB-TESORO-B02

```
The Safety Alert provides the following guidance for industry: 1. Identify all carbon steel equipment in hydrogen service that has the potential to harm workers or communities due to catastrophic failure; 2. Verify actual operating conditions (hydrogen partial pressure and temperature) for the identified carbon steel equipment; 3. Replace carbon steel process equipment that operates above 400 °F and greater than 50 psia hydrogen partial pressure; and 4. Use inherently safer materials, such as steels with higher chromium and molybdenum content.
```

## PUB-022 — grounded_explanation

In the 2016 alert, which pressure quantity is to be verified for HTHA assessment? Explain why an unqualified pressure reading is insufficient.

Draft reference (reviewer only):

The alert explicitly calls for hydrogen partial pressure and actual operating temperature. Total mixture pressure is not hydrogen partial pressure unless the hydrogen fraction and pressure basis support that equivalence. Obtain composition and absolute/partial-pressure basis; preserve the alert’s psia wording.

Tolerance and basis:

```
null
```

Critical-error criteria:

Equates arbitrary total or gauge pressure to hydrogen partial pressure; loses the absolute-pressure basis.

### Response A

```
{
  "question_id": "PUB-022",
  "answer": "The pressure quantity to be verified for HTHA assessment is hydrogen partial pressure. According to the CSB alert, equipment must be evaluated based on actual operating conditions, specifically hydrogen partial pressure and temperature (CSB-TESORO-B02). An unqualified pressure reading—such as total system pressure—is insufficient because HTHA is driven by the concentration of atomic hydrogen, which depends on the partial pressure of hydrogen in the gas phase, not the total pressure. For example, a high total pressure with low hydrogen mole fraction may still result in low hydrogen partial pressure, reducing HTHA risk. Thus, only hydrogen partial pressure accurately reflects the driving force for hydrogen diffusion into steel, which is critical for HTHA assessment.",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "CSB-TESORO",
      "block_id": "CSB-TESORO-B02",
      "quote": "Verify actual operating conditions (hydrogen partial pressure and temperature) for the identified carbon steel equipment"
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "status": "stopped_no_retry"
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

## PUB-023 — abstention

Does this 2016 alert alone prove our current equipment is safe below its cited threshold or establish the complete current code requirements?

Draft reference (reviewer only):

No. It is a dated safety alert, not a complete current standard or a universal safe boundary. The summary does not establish this equipment’s condition, history, material, actual temperature or hydrogen partial pressure, and current applicable requirements must be checked separately.

Tolerance and basis:

```
null
```

Critical-error criteria:

Guarantees safety below the stated values; represents the 2016 news release as the complete current code.

### Response A

```
{
  "question_id": "PUB-023",
  "answer": "No, this 2016 alert alone does not prove current equipment is safe below its cited threshold nor establish complete current code requirements. The alert provides guidance and recommendations, not a definitive safety certification or codified standard. It identifies a risk (HTHA) and suggests actions, but does not replace or supersede applicable codes such as ASME BPVC or API standards. Safety must be evaluated against current regulatory and engineering codes, which may include additional criteria beyond those in the alert. The alert is a safety recommendation, not a compliance statement.",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "CSB-TESORO",
      "block_id": "CSB-TESORO-B02",
      "quote": "The Safety Alert provides the following guidance for industry"
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "status": "stopped_no_retry"
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

## PUB-024 — missing_data

An engineer provides only total pressure and bulk-stream temperature. What further information is needed to apply the alert meaningfully to a carbon-steel exchanger?

Draft reference (reviewer only):

Verify actual equipment operating temperature and hydrogen partial pressure with explicit absolute basis/composition, materials and relevant service/operating history, plus inspection/damage evidence. Bulk/total values alone may not represent the material’s actual exposure. The alert supplies no full fitness-for-service calculation.

Tolerance and basis:

```
null
```

Critical-error criteria:

Accepts total pressure as hydrogen partial pressure without composition; declares fitness from the two bulk readings.

### Response A

```
{
  "question_id": "PUB-024",
  "answer": "To apply the alert meaningfully, the hydrogen partial pressure must be determined. The engineer has provided total pressure and bulk-stream temperature, but hydrogen partial pressure is required to assess HTHA risk. The alert specifies that equipment operating above 400 °F and greater than 50 psia hydrogen partial pressure should be replaced (CSB-TESORO-B02). Without knowing the mole fraction of hydrogen in the stream, the total pressure cannot be used to infer hydrogen partial pressure. Therefore, the composition of the gas stream—specifically the hydrogen mole fraction—is needed to calculate hydrogen partial pressure using the formula: P_H2 = y_H2 × P_total.",
  "uncertainties": [
    "Hydrogen mole fraction is unknown"
  ],
  "evidence": [
    {
      "source_id": "CSB-TESORO",
      "block_id": "CSB-TESORO-B02",
      "quote": "Verify actual operating conditions (hydrogen partial pressure and temperature) for the identified carbon steel equipment"
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "status": "stopped_no_retry"
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.
