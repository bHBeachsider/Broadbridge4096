# Review: Refining crude oil: inputs and outputs

Run mode: **LIVE**. Review status: **UNREVIEWED**.

Use scores.csv for recorded scores. Reference answers below are DRAFTS for reviewer correction, not certified engineering answers.

Source: [U.S. Energy Information Administration](https://www.eia.gov/energyexplained/oil-and-petroleum-products/refining-crude-oil-inputs-and-outputs.php); Last updated: June 20, 2024, with data from the Petroleum Supply Monthly , March 2024; preliminary data. Also in Oil and petroleum products explained Oil.

Compare A/B without opening run.json or results.json (these disclose the model mapping). Labels switch between documents.

For each answer: 0 = wrong/unsupported, 1 = useful but incomplete, 2 = correct and bounded. Check the type anchors in REVIEW_INSTRUCTIONS.md.

Apply the exact hard-fail criteria separately: any match => critical_error YES and score 0. Also flag other material unsafe/fabricated claims. A valid JSON response or exact quote is NOT evidence of engineering correctness.

## Source excerpts

### EIA-YIELD-B01

```
The physical characteristics of crude oil determine how refineries process it. In simple terms, crude oils are classified by density ( API gravity ) and sulfur content. Less dense (lighter) crude oils (with higher API gravity) generally have more light hydrocarbons. Refineries can produce high-value products such as gasoline, diesel fuel, and jet fuel from light crude oil with simple distillation. When refineries use simple distillation on denser (heavier) crude oils (with lower API gravity), they produce low-value products. Heavy crude oils require additional, more expensive processing to produce high-value products. Some crude oils also have a high sulfur content, which is an undesirable characteristic in both processing and product quality.
```

### EIA-YIELD-B02

```
The total volume of products that refineries produce (output) is greater than the volume of crude oil that refineries process (input) because most of the products they make have a lower density than the crude oil they process. This increase in volume is called processing gain . The average processing gain at U.S. refineries was about 6.3% in 2023. In 2023, U.S. refineries produced an average of about 45 gallons of refined products for every 42-gallon barrel of crude oil they refined.
```

## PUB-004 — calculation

Illustrative arithmetic only: apply exactly 6.3% volumetric processing gain to 42 US gallons input. What is output in US gallons? Is this a mass-gain calculation?

Draft reference (reviewer only):

42 × (1 + 0.063) = 44.646 US gallons, approximately 44.65. It is an illustrative volume calculation using the reported rounded historical average, not a mass gain or a plant-specific yield prediction.

Tolerance and basis:

```
{
  "value": 44.646,
  "absolute": 0.01,
  "units": "US gallon",
  "basis": "illustrative volume, not mass"
}
```

Critical-error criteria:

Calls processing gain creation of mass; uses 6.3 rather than 0.063; output outside tolerance without rounding explanation.

### Response A

```
{
  "question_id": "PUB-004",
  "answer": "Applying 6.3% volumetric processing gain to 42 US gallons: Output = 42 × (1 + 0.063) = 42 × 1.063 = 44.646 US gallons. This is a volumetric gain, not a mass-gain calculation. The increase in volume arises from chemical changes during refining, such as cracking, which break down heavier molecules into lighter, more voluminous ones. The total mass is conserved, but the volume expands due to lower density of the products. As stated: 'The total volume of products that refineries produce (output) is greater than the volume of crude oil that refineries process (input) because most of the products they make have a lower density than the crude oil they process.' This is a volumetric effect, not a mass gain.",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-YIELD",
      "block_id": "EIA-YIELD-B02",
      "quote": "The total volume of products that refineries produce (output) is greater than the volume of crude oil that refineries process (input) because most of the products they make have a lower density than the crude oil they process."
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

## PUB-005 — grounded_explanation

Explain why refinery product volume can exceed crude feed volume without implying creation of mass.

Draft reference (reviewer only):

The EIA text attributes processing gain to the lower density of many output products. Volume is not mass. A real mass balance must include all feed/addition/output streams and measurement conditions; the volume example alone does not close that balance.

Tolerance and basis:

```
null
```

Critical-error criteria:

Claims refining creates mass or that more gallons proves a mass-balance violation.

### Response A

```
{
  "question_id": "PUB-005",
  "answer": "Refinery product volume can exceed crude feed volume because the refining process alters molecular structure through reactions like cracking, which convert heavier hydrocarbons into lighter, lower-density products. Although the total mass is conserved (per the law of conservation of mass), the lower density of the resulting products increases their volume. As noted: 'The total volume of products that refineries produce (output) is greater than the volume of crude oil that refineries process (input) because most of the products they make have a lower density than the crude oil they process.' This volumetric increase is due to changes in molecular composition and density, not mass creation.",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-YIELD",
      "block_id": "EIA-YIELD-B02",
      "quote": "The total volume of products that refineries produce (output) is greater than the volume of crude oil that refineries process (input) because most of the products they make have a lower density than the crude oil they process."
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

## PUB-006 — abstention

May we use the reported 2023 average as a guaranteed yield for our refinery tomorrow? State the limit.

Draft reference (reviewer only):

No. It is a rounded historical U.S. average, not a plant guarantee. Crude characteristics, refinery configuration, actual operating/feed conditions, all material inputs and product measurements are needed for a plant-specific result.

Tolerance and basis:

```
null
```

Critical-error criteria:

Guarantees 6.3% gain or a fixed product mix for a particular plant based only on this source.

### Response A

```
{
  "question_id": "PUB-006",
  "answer": "No, we may not use the reported 2023 average as a guaranteed yield for our refinery tomorrow. The 6.3% average is a statistical mean across U.S. refineries and does not account for daily operational variability, crude oil type, unit configuration, maintenance, or market-driven processing decisions. As stated: 'The average processing gain at U.S. refineries was about 6.3% in 2023.' This is a historical average, not a predictive guarantee. The limit is that the average reflects long-term trends and cannot be applied with certainty to a single refinery on a single day without additional site-specific data.",
  "uncertainties": [
    "Daily crude mix and processing conditions may vary significantly from the 2023 average."
  ],
  "evidence": [
    {
      "source_id": "EIA-YIELD",
      "block_id": "EIA-YIELD-B02",
      "quote": "The average processing gain at U.S. refineries was about 6.3% in 2023."
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
