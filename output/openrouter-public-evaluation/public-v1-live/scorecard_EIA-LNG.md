# Review: Liquefied natural gas

Run mode: **LIVE**. Review status: **UNREVIEWED**.

Use scores.csv for recorded scores. Reference answers below are DRAFTS for reviewer correction, not certified engineering answers.

Source: [U.S. Energy Information Administration](https://www.eia.gov/energyexplained/natural-gas/liquefied-natural-gas.php); Last updated: June 21, 2024, with data from the Natural Gas Monthly , March 2024; preliminary data for 2023. Also in Natural gas explained Natural gas Da.

Compare A/B without opening run.json or results.json (these disclose the model mapping). Labels switch between documents.

For each answer: 0 = wrong/unsupported, 1 = useful but incomplete, 2 = correct and bounded. Check the type anchors in REVIEW_INSTRUCTIONS.md.

Apply the exact hard-fail criteria separately: any match => critical_error YES and score 0. Also flag other material unsafe/fabricated claims. A valid JSON response or exact quote is NOT evidence of engineering correctness.

## Source excerpts

### EIA-LNG-B01

```
Liquefied natural gas (LNG) is natural gas that has been cooled to a liquid state ( liquefied ), to about -260° Fahrenheit, for shipping and storage. The volume of natural gas in a liquid state is about 600 times smaller than its volume in a gaseous state (in natural gas pipelines). The liquefaction process, developed in the 19 th century, makes it possible to transport natural gas to places natural gas pipelines do not reach and to use natural gas as a transportation fuel.
```

### EIA-LNG-B02

```
LNG export facilities receive natural gas by pipeline and liquefy the gas for transport on special ocean-going LNG ships, or tankers . Most LNG is transported by tankers called LNG carriers in large, onboard, super-cooled (cryogenic) tanks. LNG is also transported in smaller International Organization for Standardization (ISO)-compliant containers that can be placed on ships and on trucks.
```

### EIA-LNG-B03

```
At import terminals, LNG is offloaded from ships and is stored in cryogenic storage tanks before it is returned to its gaseous state, or regasified . After regasification, the natural gas is transported by natural gas pipelines to natural gas-fired power plants, industrial facilities, and residential and commercial customers.
```

### EIA-LNG-B04

```
Not all natural gas delivered to LNG export facilities (feed gas) is exported as LNG because LNG export terminals consume some of the feed gas to operate on-site liquefaction equipment. EIA estimates (based on survey Form EIA-176 ; see LNG respondent data ) that approximately 7% to 15% of LNG feed gas is used for liquefaction processes, mostly to operate on-site liquefaction equipment. 3 U.S. LNG export facilities, except Freeport LNG, use natural gas turbine-driven refrigerant compressors to convert natural gas to LNG. Freeport LNG is the only liquefaction facility in the United States that uses electric motors instead of natural gas turbines to drive refrigerant compressors. As a result, most of Freeport LNG's feed gas is converted into LNG.
```

## PUB-007 — calculation

Illustrative conversion: for 120,000 m3 of gas on the SAME gaseous-volume basis underlying the excerpt’s approximate 600:1 comparison, estimate liquid volume. Do not change the stated basis.

Draft reference (reviewer only):

120,000 / 600 = approximately 200 m3 LNG. This uses the approximate source comparison and the stated same gas basis; it is not an exact equation of state or a universal standard-volume conversion.

Tolerance and basis:

```
{
  "value": 200,
  "absolute": 1,
  "units": "m3 LNG",
  "basis": "approximate same-basis 600:1 volume comparison"
}
```

Critical-error criteria:

Multiplies by 600; calls the approximate factor exact or universally independent of pressure, temperature or composition.

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
  "question_id": "PUB-007",
  "answer": "Given the 600:1 volume reduction from gaseous to liquid state, the liquid volume is calculated as: 120,000 m³ ÷ 600 = 200 m³. This maintains the same gaseous-volume basis as stated in the excerpt. The calculation is based on the volume reduction ratio provided in EIA-LNG-B01: 'The volume of natural gas in a liquid state is about 600 times smaller than its volume in a gaseous state.'",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-LNG",
      "block_id": "EIA-LNG-B01",
      "quote": "The volume of natural gas in a liquid state is about 600 times smaller than its volume in a gaseous state."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-007

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

## PUB-008 — calculation

Synthetic simplified balance: feed gas is 100 million standard cubic feet/day; exactly 10% is consumed onsite for liquefaction, with no other losses. On the same gas-equivalent basis, how much remains for LNG export? Do not report physical liquid cubic feet.

Draft reference (reviewer only):

100 × (1 − 0.10) = 90 million standard cubic feet/day gas-equivalent available for export. The 10% is a stated synthetic assumption, not a measurement for any named terminal. Physical LNG volume cannot be obtained without a separate conversion and basis.

Tolerance and basis:

```
{
  "value": 90,
  "absolute": 0.1,
  "units": "million standard cubic feet/day gas-equivalent",
  "basis": "synthetic 10% onsite use; no other losses"
}
```

Critical-error criteria:

Reports 90 million liquid cubic feet/day; confuses feed gas with exported LNG; attributes the synthetic 10% to a real plant.

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
  "question_id": "PUB-008",
  "answer": "Feed gas = 100 million standard cubic feet/day. 10% consumed onsite: 100 × 0.10 = 10 million standard cubic feet/day. Remaining for export: 100 - 10 = 90 million standard cubic feet/day. This is on the same gas-equivalent basis as feed gas, with no physical liquid volume reported. The calculation assumes no other losses and uses the given 10% onsite consumption. The basis is consistent with the feed gas volume as stated in EIA-LNG-B04: 'approximately 7% to 15% of LNG feed gas is used for liquefaction processes.'",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-LNG",
      "block_id": "EIA-LNG-B04",
      "quote": "approximately 7% to 15% of LNG feed gas is used for liquefaction processes"
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-007

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

## PUB-009 — brief

Summarize the LNG export/import chain and explain why feed-gas volume and exported gas-equivalent volume can differ.

Draft reference (reviewer only):

Pipeline gas is liquefied, shipped in cryogenic carriers, stored at import terminals and regasified for pipeline delivery. Export terminals may consume feed gas to power liquefaction; the cited historical estimate is about 7–15%. Facility design matters; do not turn this range into a universal efficiency or guarantee.

Tolerance and basis:

```
null
```

Critical-error criteria:

Equates LNG and pipeline gas volumes; says every terminal exports all feed gas or has identical fuel consumption.

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
  "question_id": "PUB-009",
  "answer": "The LNG export/import chain involves: (1) natural gas delivered via pipeline to export facilities; (2) liquefaction into cryogenic liquid for transport via LNG carriers or ISO containers; (3) offloading at import terminals; (4) storage in cryogenic tanks; and (5) regasification and delivery via pipelines to end users. Feed-gas volume and exported gas-equivalent volume differ because a portion of the feed gas (7–15%) is consumed on-site to power liquefaction equipment, as noted in EIA-LNG-B04: 'approximately 7% to 15% of LNG feed gas is used for liquefaction processes, mostly to operate on-site liquefaction equipment.' Thus, not all feed gas becomes exported LNG.",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-LNG",
      "block_id": "EIA-LNG-B04",
      "quote": "approximately 7% to 15% of LNG feed gas is used for liquefaction processes, mostly to operate on-site liquefaction equipment."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-007

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.
