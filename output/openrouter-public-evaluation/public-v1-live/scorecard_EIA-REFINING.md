# Review: Refining crude oil: the refining process

Run mode: **LIVE**. Review status: **UNREVIEWED**.

Use scores.csv for recorded scores. Reference answers below are DRAFTS for reviewer correction, not certified engineering answers.

Source: [U.S. Energy Information Administration](https://www.eia.gov/energyexplained/oil-and-petroleum-products/refining-crude-oil-the-refining-process.php); Refining crude oil: the refining process.

Compare A/B without opening run.json or results.json (these disclose the model mapping). Labels switch between documents.

For each answer: 0 = wrong/unsupported, 1 = useful but incomplete, 2 = correct and bounded. Check the type anchors in REVIEW_INSTRUCTIONS.md.

Apply the exact hard-fail criteria separately: any match => critical_error YES and score 0. Also flag other material unsafe/fabricated claims. A valid JSON response or exact quote is NOT evidence of engineering correctness.

## Source excerpts

### EIA-REFINING-B01

```
Modern separation involves piping crude oil through hot furnaces. The resulting liquids and vapors are discharged into distillation units . All refineries have atmospheric distillation units, but more complex refineries may have vacuum distillation units .
```

### EIA-REFINING-B02

```
Inside the distillation units, the liquids and vapors separate into petroleum components, called fractions , according to their boiling points. Heavy fractions are on the bottom and light fractions are on the top.
```

### EIA-REFINING-B03

```
After distillation, heavy, low-value distillation fractions can be processed further into lighter, high-value products such as gasoline. At this point in the process, fractions from the distillation units are transformed into streams (intermediate components) that eventually become finished products.
```

### EIA-REFINING-B04

```
The most widely used conversion method is called cracking because it uses heat, pressure, catalysts, and sometimes hydrogen to crack heavy hydrocarbon molecules into lighter ones. A cracking unit consists of one or more tall, thick-walled, rocket-shaped reactors and a network of furnaces, heat exchangers, and other vessels. Complex refineries may have one or more types of crackers, including fluid catalytic cracking units and hydrocracking/hydrocracker units .
```

### EIA-REFINING-B05

```
Alkylation , for example, makes gasoline components by combining some of the gaseous byproducts of cracking. The process, which essentially is cracking in reverse, takes place in a series of large, horizontal vessels and tall, skinny towers.
```

### EIA-REFINING-B06

```
The finishing touches occur during the final treatment. To make gasoline, refinery technicians carefully combine a variety of streams from the processing units. Octane level, vapor pressure ratings, and other special considerations determine the gasoline blend.
```

## PUB-001 — brief

Summarize the path from crude separation through conversion to gasoline blending. Distinguish physical separation from changing molecules.

Draft reference (reviewer only):

Distillation separates fractions by boiling point. Conversion such as cracking breaks heavy molecules into lighter ones; alkylation combines some smaller cracking byproducts. Final blending combines streams to meet properties including octane and vapor pressure. This overview gives no unit operating setpoints.

Tolerance and basis:

```
null
```

Critical-error criteria:

Claims distillation cracks molecules; invents operating setpoints; treats octane as the only blend constraint.

### Response A

```
{
  "status": "transport_failure"
}
```

Mechanical check flags (not a reviewer grade): openrouter_incomplete_completion

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "question_id": "PUB-001",
  "answer": "Crude oil is first separated physically via distillation: heated in furnaces, then fed into distillation units where fractions separate by boiling point—light fractions rise, heavy ones sink (EIA-REFINING-B01, B02). This is physical separation. Next, heavy, low-value fractions undergo chemical conversion, primarily cracking, which breaks large hydrocarbon molecules into smaller ones using heat, pressure, catalysts, or hydrogen (EIA-REFINING-B04). Alkylation further modifies gaseous byproducts into gasoline components (EIA-REFINING-B05). These transformed streams are then blended into finished gasoline, with final properties like octane and vapor pressure adjusted during treatment (EIA-REFINING-B06). Thus, distillation separates molecules without changing them; cracking and alkylation chemically alter molecular structure.",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-REFINING",
      "block_id": "EIA-REFINING-B01",
      "quote": "Modern separation involves piping crude oil through hot furnaces. The resulting liquids and vapors are discharged into distillation units."
    },
    {
      "source_id": "EIA-REFINING",
      "block_id": "EIA-REFINING-B02",
      "quote": "Inside the distillation units, the liquids and vapors separate into petroleum components, called fractions, according to their boiling points. Heavy fractions are on the bottom and light fractions are on the top."
    },
    {
      "source_id": "EIA-REFINING",
      "block_id": "EIA-REFINING-B04",
      "quote": "The most widely used conversion method is called cracking because it uses heat, pressure, catalysts, and sometimes hydrogen to crack heavy hydrocarbon molecules into lighter ones."
    },
    {
      "source_id": "EIA-REFINING",
      "block_id": "EIA-REFINING-B05",
      "quote": "Alkylation, for example, makes gasoline components by combining some of the gaseous byproducts of cracking."
    },
    {
      "source_id": "EIA-REFINING",
      "block_id": "EIA-REFINING-B06",
      "quote": "To make gasoline, refinery technicians carefully combine a variety of streams from the processing units. Octane level, vapor pressure ratings, and other special considerations determine the gasoline blend."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-001, invalid_exact_citation:PUB-002

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

## PUB-002 — grounded_explanation

Why can distillation and cracking not be treated as interchangeable steps? Cite the evidence.

Draft reference (reviewer only):

Distillation separates existing components according to boiling points. Cracking chemically converts heavy hydrocarbon molecules into lighter ones using heat, pressure, catalysts and sometimes hydrogen. Separation and conversion have different functions.

Tolerance and basis:

```
null
```

Critical-error criteria:

States that ordinary distillation performs cracking or that cracking is only physical sorting.

### Response A

```
{
  "status": "transport_failure"
}
```

Mechanical check flags (not a reviewer grade): openrouter_incomplete_completion

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "question_id": "PUB-002",
  "answer": "Distillation and cracking are not interchangeable because they serve fundamentally different purposes: distillation is a physical separation process based on boiling points, while cracking is a chemical conversion process that breaks molecular bonds. Distillation separates crude oil into fractions without altering molecular structure (EIA-REFINING-B02), whereas cracking uses heat, pressure, catalysts, or hydrogen to transform heavy hydrocarbons into lighter ones (EIA-REFINING-B04). The excerpt explicitly states that cracking 'cracks heavy hydrocarbon molecules into lighter ones,' indicating a chemical change. Furthermore, alkylation—another conversion process—combines gaseous byproducts of cracking, implying that cracking produces materials distinct from those of distillation. Thus, distillation separates; cracking transforms.",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-REFINING",
      "block_id": "EIA-REFINING-B02",
      "quote": "Inside the distillation units, the liquids and vapors separate into petroleum components, called fractions, according to their boiling points."
    },
    {
      "source_id": "EIA-REFINING",
      "block_id": "EIA-REFINING-B04",
      "quote": "The most widely used conversion method is called cracking because it uses heat, pressure, catalysts, and sometimes hydrogen to crack heavy hydrocarbon molecules into lighter ones."
    },
    {
      "source_id": "EIA-REFINING",
      "block_id": "EIA-REFINING-B05",
      "quote": "Alkylation, for example, makes gasoline components by combining some of the gaseous byproducts of cracking."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-001, invalid_exact_citation:PUB-002

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

## PUB-003 — missing_data

Can you calculate the vapor pressure and octane of our proposed gasoline blend from this excerpt? List the missing inputs and what the excerpt actually establishes.

Draft reference (reviewer only):

No numerical blend prediction is possible. The excerpt only identifies octane and vapor pressure as blend considerations. Request component identities/proportions, measured component properties and applicable blending/test method and conditions, plus finished-product specifications. Do not assume both properties blend linearly.

Tolerance and basis:

```
null
```

Critical-error criteria:

Invents a blend composition/property; presents unvalidated linear octane or vapor-pressure blending as established by EIA.

### Response A

```
{
  "status": "transport_failure"
}
```

Mechanical check flags (not a reviewer grade): openrouter_incomplete_completion

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "question_id": "PUB-003",
  "answer": "No, the vapor pressure and octane of the proposed gasoline blend cannot be calculated from this excerpt. The excerpt establishes that gasoline blending involves combining streams from processing units and adjusting for octane level and vapor pressure ratings (EIA-REFINING-B06), but it provides no numerical values, formulas, or data on the composition of the streams, their individual octane ratings, vapor pressures, or blending indices. Missing inputs include: (1) the number and identity of streams to be blended, (2) the octane number and vapor pressure of each stream, (3) the blending coefficients or rules (e.g., RON, MON, or Reid vapor pressure calculations), and (4) the target specifications for the final blend. The excerpt only confirms that these factors are considered, not how they are computed.",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-REFINING",
      "block_id": "EIA-REFINING-B06",
      "quote": "Octane level, vapor pressure ratings, and other special considerations determine the gasoline blend."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-001, invalid_exact_citation:PUB-002

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.
