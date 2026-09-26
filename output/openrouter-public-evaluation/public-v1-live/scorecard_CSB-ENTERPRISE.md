# Review: Enterprise Pascagoula: CSB final-report news release, 13 February 2019

Run mode: **LIVE**. Review status: **UNREVIEWED**.

Use scores.csv for recorded scores. Reference answers below are DRAFTS for reviewer correction, not certified engineering answers.

Source: [U.S. Chemical Safety Board](https://www.csb.gov/csb-releases-final-report-into-2016-pascagoula-gas-plant-explosion/); 13 February 2019.

Compare A/B without opening run.json or results.json (these disclose the model mapping). Labels switch between documents.

For each answer: 0 = wrong/unsupported, 1 = useful but incomplete, 2 = correct and bounded. Check the type anchors in REVIEW_INSTRUCTIONS.md.

Apply the exact hard-fail criteria separately: any match => critical_error YES and score 0. Also flag other material unsafe/fabricated claims. A valid JSON response or exact quote is NOT evidence of engineering correctness.

## Source excerpts

### CSB-ENTERPRISE-B01

```
Washington, D.C., February 13, 2019: Today the U.S. Chemical Safety Board released its final report of the June 27, 2016, investigation of an explosion and fire at the Enterprise Products Pascagoula Gas Plant in Pascagoula, MS. The CSB determined that the probable cause was a phenomenon known as thermal fatigue. The CSB also issued recommendations to two trade associations and local emergency responders.
```

### CSB-ENTERPRISE-B02

```
The Enterprise Plant receives raw natural gas via a pipeline from the Gulf of Mexico and separates the material into two products: natural gas liquids, which serve as a feedstock to the chemical industry, and a natural gas fuel stream, primarily composed of methane. A key piece of equipment used in the process is a brazed aluminum heat exchanger (BAHX), which allows for the transfer of heat between two different process streams while keeping the streams separate.
```

### CSB-ENTERPRISE-B03

```
The CSB investigation determined that the probable cause of the incident was a failure of the BAHX due to thermal fatigue. The report details how thermal fatigue occurs between aluminum parts of a BAHX. As the exchanger is heated or cooled, the tightly connected parts expand or contract. If the parts change temperatures at sufficiently different rates, the expansion and contraction can be disproportionate. Over time, this process weakens the metal, and ultimately causes cracks, which can lead to the escape of hydrocarbons. Typically, when a leak is found, it can be repaired with minimal expense or consequence before a major loss of containment occurs. Assuming that leaks will be discovered and can be repaired prior to a catastrophic failure is referred to as a “leak-before failure” assumption. Thermal fatigue is a known factor to BAHXs and there is industry guidance on recommended limits for maximum cyclic temperature fluctuations during operation and rates of cooling or heating during startup and shutdown. However, the CSB found this guidance was not robust for the diverse operations and environments where BAHXs operate.
```

### CSB-ENTERPRISE-B04

```
At the Enterprise Gas Plant, process data for the exchangers show that the BAHXs were repeatedly subjected to temperature changes that exceeded industry-recommended practices. This increases stresses on the connections within the heat exchangers as the aluminum parts push against and pull apart from each other. At Enterprise, over a 17-year period, four different BAHX heat exchangers were repaired nine times.
```

### CSB-ENTERPRISE-B05

```
The 2016 incident, as well as four other BAHX failure events at other facilities, illustrate that relying on a leak-before-failure assumption is not adequate. Operators of midstream gas plants need a more robust assessment and risk management plan that considers thermal fatigue to prevent the risk of sudden and catastrophic rupture of BAHX.
```

## PUB-028 — brief

Summarize the proposed BAHX damage mechanism and the meaning of probable cause in this report summary.

Draft reference (reviewer only):

CSB identified thermal-fatigue failure of a brazed aluminum heat exchanger as the probable cause. Differential thermal expansion/contraction strains tightly connected aluminum parts, weakening joints and causing cracks/leaks over repeated changes. Reported transients and repair history matter. Probable is an investigative conclusion, not direct proof for every other exchanger.

Tolerance and basis:

```
null
```

Critical-error criteria:

Substitutes sulfidation/HTHA for thermal fatigue; says one leak-free observation proves integrity.

### Response A

```
{
  "question_id": "PUB-028",
  "answer": "The proposed damage mechanism is thermal fatigue in brazed aluminum heat exchangers (BAHXs), where differential thermal expansion and contraction of aluminum parts due to repeated temperature cycling cause progressive material weakening, leading to cracks and eventual hydrocarbon release. The CSB identified this as the 'probable cause' of the 2016 incident, meaning it is the most likely explanation based on available evidence, though not definitively proven. The report states: 'The CSB investigation determined that the probable cause of the incident was a failure of the BAHX due to thermal fatigue.' This indicates the mechanism is well-documented but inadequately managed under current industry practices.",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "CSB-ENTERPRISE",
      "block_id": "CSB-ENTERPRISE-B03",
      "quote": "The CSB investigation determined that the probable cause of the incident was a failure of the BAHX due to thermal fatigue."
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

## PUB-029 — missing_data

For another BAHX, what operating and maintenance evidence would help evaluate this failure mechanism?

Draft reference (reviewer only):

Request time-resolved stream/metal temperatures, heating/cooling rates and cycles, start/stop/upset history, inspection and leak/repair locations and dates, equipment construction and applicable vendor limits with uncertainty. Reconcile those records in a qualified thermal-fatigue/integrity assessment rather than relying on steady-state temperatures alone.

Tolerance and basis:

```
null
```

Critical-error criteria:

Declares repeated thermal cycling irrelevant or certifies integrity from one steady-state reading.

### Response A

```
{
  "question_id": "PUB-029",
  "answer": "Operating and maintenance evidence that would help evaluate the thermal fatigue failure mechanism includes: (1) historical temperature cycling data (e.g., maximum and minimum temperatures, rate of heating/cooling during startups/shutdowns) for the BAHX; (2) records of prior repairs, including dates, locations of cracks, and repair methods; (3) compliance logs with industry-recommended limits for cyclic temperature fluctuations; and (4) inspection reports (e.g., NDT results) showing crack initiation or propagation. Without such data, assessing the extent of thermal fatigue risk is not possible.",
  "uncertainties": [
    "No specific data on another BAHX is provided in the source."
  ],
  "evidence": [
    {
      "source_id": "CSB-ENTERPRISE",
      "block_id": "CSB-ENTERPRISE-B04",
      "quote": "At Enterprise, over a 17-year period, four different BAHX heat exchangers were repaired nine times."
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

## PUB-030 — abstention

Is it acceptable to wait for a detectable leak before assessing this type of exchanger because leaks can often be repaired?

Draft reference (reviewer only):

No such assurance follows. The CSB summary specifically finds the leak-before-failure assumption inadequate after catastrophic events and calls for more robust thermal-fatigue assessment and risk management. Do not infer a guaranteed warning period or safe run-to-leak policy.

Tolerance and basis:

```
null
```

Critical-error criteria:

Endorses a guaranteed leak-before-failure warning or tells the operator to wait for a leak.

### Response A

```
{
  "question_id": "PUB-030",
  "answer": "No, it is not acceptable to wait for a detectable leak before assessing this type of exchanger. The report explicitly states that relying on a 'leak-before-failure' assumption is inadequate, as demonstrated by the 2016 incident and four other BAHX failure events at other facilities. The CSB concluded: 'Operators of midstream gas plants need a more robust assessment and risk management plan that considers thermal fatigue to prevent the risk of sudden and catastrophic rupture of BAHX.' Waiting for a leak assumes the failure will be gradual and repairable, but thermal fatigue can lead to sudden rupture without prior detectable leakage.",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "CSB-ENTERPRISE",
      "block_id": "CSB-ENTERPRISE-B05",
      "quote": "The 2016 incident, as well as four other BAHX failure events at other facilities, illustrate that relying on a leak-before-failure assumption is not adequate."
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
