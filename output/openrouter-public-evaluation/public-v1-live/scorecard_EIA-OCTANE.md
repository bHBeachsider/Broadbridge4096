# Review: Octane in depth

Run mode: **LIVE**. Review status: **UNREVIEWED**.

Use scores.csv for recorded scores. Reference answers below are DRAFTS for reviewer correction, not certified engineering answers.

Source: [U.S. Energy Information Administration](https://www.eia.gov/energyexplained/gasoline/octane-in-depth.php); Octane in depth.

Compare A/B without opening run.json or results.json (these disclose the model mapping). Labels switch between documents.

For each answer: 0 = wrong/unsupported, 1 = useful but incomplete, 2 = correct and bounded. Check the type anchors in REVIEW_INSTRUCTIONS.md.

Apply the exact hard-fail criteria separately: any match => critical_error YES and score 0. Also flag other material unsafe/fabricated claims. A valid JSON response or exact quote is NOT evidence of engineering correctness.

## Source excerpts

### EIA-OCTANE-B01

```
The large number on the yellow gasoline pump octane label is the minimum octane rating. (R+M)/2 Method on the label refers to the octane testing method used, where R is Research Octane Number and M is Motor Octane Number.
```

### EIA-OCTANE-B02

```
Engines are designed to burn fuel in a controlled combustion . A flame starts at the spark plug and burns throughout the cylinder until all fuel in the cylinder is burned. In comparison, spontaneous combustion , also called auto-ignition , detonation , or knock , happens when rising temperature and pressure from the primary combustion causes unburned fuel to ignite. This uncontrolled secondary combustion causes pressure in the cylinder to spike and causes the knock to occur.
```

### EIA-OCTANE-B03

```
The competition between the intended (controlled) and unintended (spontaneous) combustion causes the energy from the burning fuel to disperse unevenly, which can damage and place high pressure on the engine's piston before it enters the power stroke (the part of the cycle when the piston's motion is generating power).
```

### EIA-OCTANE-B04

```
The (R+M)/2 you see on the label refers to the average of the research octane number ( R ON) and the motor octane number ( M ON) ratings. To determine the RON, the fuel is tested under engine idle conditions with a low air temperature and slow engine speed. To determine the MON, the fuel is tested under the more stressful conditions of higher air temperature and engine speed.
```

## PUB-016 — calculation

Synthetic lab values: RON is 96 and MON is 86. Using the displayed (R+M)/2 method, calculate the pump rating.

Draft reference (reviewer only):

(96 + 86) / 2 = 91, an octane rating with no physical unit. These are illustrative test values, not a measured blend from EIA.

Tolerance and basis:

```
{
  "value": 91,
  "absolute": 0.01,
  "units": "octane rating",
  "basis": "synthetic (RON + MON)/2"
}
```

Critical-error criteria:

Uses RON alone as the U.S. pump rating; result outside tolerance.

### Response A

```
{
  "question_id": "PUB-016",
  "answer": "Using the (R+M)/2 method: (RON + MON) / 2 = (96 + 86) / 2 = 182 / 2 = 91. The pump rating is 91. Cited: 'The (R+M)/2 you see on the label refers to the average of the research octane number (R ON) and the motor octane number (M ON) ratings.' (EIA-OCTANE-B04)",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-OCTANE",
      "block_id": "EIA-OCTANE-B04",
      "quote": "The (R+M)/2 you see on the label refers to the average of the research octane number (R ON) and the motor octane number (M ON) ratings."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-016, invalid_exact_citation:PUB-017

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "status": "stopped_no_retry"
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

## PUB-017 — calculation

Synthetic lab check: the (R+M)/2 rating is 91 and RON is 96. Solve for MON and show your equation.

Draft reference (reviewer only):

91 = (96 + MON)/2, so MON = 2 × 91 − 96 = 86. The rating is not an energy-content unit.

Tolerance and basis:

```
{
  "value": 86,
  "absolute": 0.01,
  "units": "MON octane rating",
  "basis": "synthetic (RON + MON)/2"
}
```

Critical-error criteria:

Divides 91 by two instead of rearranging correctly; wrong result or physical energy unit.

### Response A

```
{
  "question_id": "PUB-017",
  "answer": "Given (R+M)/2 = 91 and RON = 96, solve: (96 + MON) / 2 = 91 → 96 + MON = 182 → MON = 182 - 96 = 86. MON is 86. Equation: (RON + MON) / 2 = (R+M)/2. Cited: 'The (R+M)/2 you see on the label refers to the average of the research octane number (R ON) and the motor octane number (M ON) ratings.' (EIA-OCTANE-B04)",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-OCTANE",
      "block_id": "EIA-OCTANE-B04",
      "quote": "The (R+M)/2 you see on the label refers to the average of the research octane number (R ON) and the motor octane number (M ON) ratings."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-016, invalid_exact_citation:PUB-017

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "status": "stopped_no_retry"
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

## PUB-018 — grounded_explanation

What does the displayed (R+M)/2 label combine, and why are RON and MON distinct measurements?

Draft reference (reviewer only):

The label is the arithmetic average of Research Octane Number and Motor Octane Number. The source describes different test conditions, with MON using higher air temperature and engine speed than RON. They are distinct test ratings, not liquid-volume percentages.

Tolerance and basis:

```
null
```

Critical-error criteria:

Calls MON and RON the same test condition; treats the average as a molecular composition or energy content.

### Response A

```
{
  "question_id": "PUB-018",
  "answer": "The (R+M)/2 label combines the Research Octane Number (RON) and Motor Octane Number (MON) to provide a balanced average rating. RON measures fuel resistance to knock under mild conditions (low speed, low temperature), while MON tests under severe conditions (high speed, high temperature). Their distinction reflects real-world engine performance across varying operating conditions. Cited: 'To determine the RON, the fuel is tested under engine idle conditions with a low air temperature and slow engine speed. To determine the MON, the fuel is tested under the more stressful conditions of higher air temperature and engine speed.' (EIA-OCTANE-B04)",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-OCTANE",
      "block_id": "EIA-OCTANE-B04",
      "quote": "To determine the RON, the fuel is tested under engine idle conditions with a low air temperature and slow engine speed. To determine the MON, the fuel is tested under the more stressful conditions of higher air temperature and engine speed."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-016, invalid_exact_citation:PUB-017

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "status": "stopped_no_retry"
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.
