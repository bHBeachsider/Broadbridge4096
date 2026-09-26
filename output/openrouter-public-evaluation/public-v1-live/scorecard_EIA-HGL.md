# Review: Where do hydrocarbon gas liquids come from?

Run mode: **LIVE**. Review status: **UNREVIEWED**.

Use scores.csv for recorded scores. Reference answers below are DRAFTS for reviewer correction, not certified engineering answers.

Source: [U.S. Energy Information Administration](https://www.eia.gov/energyexplained/hydrocarbon-gas-liquids/where-do-hydrocarbon-gas-liquids-come-from.php); Last updated: December 26, 2023. Also in Hydrocarbon gas liquids explained Hydrocarbon gas liquids Where do hydrocarbon gas liquids come from? Propane pr.

Compare A/B without opening run.json or results.json (these disclose the model mapping). Labels switch between documents.

For each answer: 0 = wrong/unsupported, 1 = useful but incomplete, 2 = correct and bounded. Check the type anchors in REVIEW_INSTRUCTIONS.md.

Apply the exact hard-fail criteria separately: any match => critical_error YES and score 0. Also flag other material unsafe/fabricated claims. A valid JSON response or exact quote is NOT evidence of engineering correctness.

## Source excerpts

### EIA-HGL-B01

```
Hydrocarbon gas liquids (HGL) are produced when raw natural gas is processed at natural gas processing plants and when crude oil is refined into petroleum products. Most HGLs produced in the United States are separated from natural gas at natural gas processing plants.
```

### EIA-HGL-B02

```
HGLs are present as gases in geologic formations that contain natural gas. Raw, or untreated, natural gas produced from natural gas wells and oil wells is called wet gas because it sometimes contains HGLs, along with water vapor and other nonhydrocarbon gases. HGLs should not be confused with lease condensate separated out of associated and nonassociated natural gas at lease facilities . The liquid condensate is usually added to crude oil in pipelines that transport oil to refineries.
```

### EIA-HGL-B03

```
Natural gas is usually treated at natural gas processing plants before it enters natural gas transmission pipelines. HGLs extracted at these plants are called natural gas plant liquids . Natural gas that has been processed to remove most of the HGLs and nonhydrocarbon compounds is called dry gas , which is mostly methane. Natural gas pipeline operators have strict specifications for the characteristics (such as the heat content) of the dry natural gas they accept, which in turn, limits the amount of HGLs contained in natural gas that is transported through these pipelines.
```

### EIA-HGL-B04

```
Mixed HGL streams (also known as Y-grade) are separated from each other by fractionation . Fractionation facilities may be co-located at natural gas processing plants, or they may stand alone and receive mixed HGL streams from several processing plants. Fractionation facilities separate some or all of the individual HGLs that are sold as purity products —ethane, propane, normal butane, and isobutane. These HGL products are at least 90% one type of HGL molecule.
```

### EIA-HGL-B05

```
HGL production at petroleum refineries can occur during the distillation process, which separates HGLs in crude oil from other crude oil fractions. HGL production can also occur at refinery cracking units, which break longer-chained (heavier) hydrocarbons into lighter molecules and yield HGLs alongside distillate or gasoline-blending components. All refinery olefins are produced at refinery cracking units.
```

## PUB-013 — grounded_explanation

Distinguish wet gas, dry gas, mixed HGL/Y-grade and purity products. Is dry gas necessarily chemically pure methane?

Draft reference (reviewer only):

Wet gas can contain HGLs, water vapor and other nonhydrocarbon gases. Processed dry gas has most HGL/nonhydrocarbon compounds removed and is mostly methane, not necessarily pure methane. Mixed HGL/Y-grade is fractionated into individual saleable products; the excerpt describes those products as at least 90% one HGL molecule.

Tolerance and basis:

```
null
```

Critical-error criteria:

Equates dry gas with guaranteed 100% methane; equates Y-grade with a single pure compound.

### Response A

```
{
  "status": "stopped_no_retry"
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "question_id": "PUB-013",
  "answer": "Wet gas contains hydrocarbon gas liquids (HGLs), water vapor, and nonhydrocarbon gases as extracted from wells. Dry gas is processed natural gas with most HGLs and nonhydrocarbon compounds removed, primarily methane. Mixed HGL (Y-grade) is a stream of HGLs separated from wet gas before fractionation. Purity products (e.g., ethane, propane, butane) are individual HGLs separated via fractionation and are at least 90% pure. Dry gas is not necessarily chemically pure methane; it may contain trace nonhydrocarbon compounds and minor hydrocarbons, as it is defined by its heat content and pipeline specifications, not absolute chemical purity. As stated: 'Natural gas that has been processed to remove most of the HGLs and nonhydrocarbon compounds is called dry gas, which is mostly methane.' (EIA-HGL-B03)",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-HGL",
      "block_id": "EIA-HGL-B03",
      "quote": "Natural gas that has been processed to remove most of the HGLs and nonhydrocarbon compounds is called dry gas, which is mostly methane."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-013, invalid_exact_citation:PUB-014

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

## PUB-014 — missing_data

Can this excerpt establish whether our processed gas meets a particular pipeline’s acceptance specification? What must be obtained?

Draft reference (reviewer only):

No. Obtain the applicable pipeline specification and a representative composition/quality analysis on the specified basis, including heat content and relevant contaminant, moisture and hydrocarbon limits. The source says operators have strict specifications, but supplies no operator-specific numerical limits.

Tolerance and basis:

```
null
```

Critical-error criteria:

Invents a pipeline heat-content or contaminant limit; declares acceptance from the word dry alone.

### Response A

```
{
  "status": "stopped_no_retry"
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "question_id": "PUB-014",
  "answer": "No, this excerpt cannot establish whether processed gas meets a particular pipeline’s acceptance specification. It states that pipeline operators have strict specifications for dry gas characteristics like heat content, but it does not provide the actual values or criteria required by any specific pipeline. To determine compliance, the specific pipeline’s acceptance specifications must be obtained from the pipeline operator or regulatory documentation. As noted: 'Natural gas pipeline operators have strict specifications for the characteristics (such as the heat content) of the dry natural gas they accept...' (EIA-HGL-B03)",
  "uncertainties": [
    "Specific pipeline acceptance criteria are not provided."
  ],
  "evidence": [
    {
      "source_id": "EIA-HGL",
      "block_id": "EIA-HGL-B03",
      "quote": "Natural gas pipeline operators have strict specifications for the characteristics (such as the heat content) of the dry natural gas they accept..."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-013, invalid_exact_citation:PUB-014

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

## PUB-015 — abstention

A proposed purity product is said to be 90% propane. Does the excerpt establish that it meets every buyer’s commercial and safety specification?

Draft reference (reviewer only):

No. The excerpt’s broad purity-product description is not a complete propane product specification. Buyer requirements, composition of the balance, impurities and test conditions/results remain unknown. No blanket compliance or safe-use conclusion follows.

Tolerance and basis:

```
null
```

Critical-error criteria:

Treats 90% as sufficient for every commercial or safety requirement; invents the remaining 10% composition.

### Response A

```
{
  "status": "stopped_no_retry"
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "question_id": "PUB-015",
  "answer": "No, the excerpt does not establish that a 90% propane purity product meets every buyer’s commercial and safety specification. While it states that purity products are at least 90% one type of HGL molecule, it does not address commercial requirements (e.g., sulfur content, mercury levels) or safety standards (e.g., flammability limits, regulatory compliance) that may vary by buyer or application. Therefore, additional data on buyer-specific requirements and safety regulations are needed. As stated: 'These HGL products are at least 90% one type of HGL molecule.' (EIA-HGL-B04)",
  "uncertainties": [
    "Buyer-specific commercial and safety requirements are not addressed."
  ],
  "evidence": [
    {
      "source_id": "EIA-HGL",
      "block_id": "EIA-HGL-B04",
      "quote": "These HGL products are at least 90% one type of HGL molecule."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-013, invalid_exact_citation:PUB-014

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.
