# Review: Natural gas pipelines

Run mode: **LIVE**. Review status: **UNREVIEWED**.

Use scores.csv for recorded scores. Reference answers below are DRAFTS for reviewer correction, not certified engineering answers.

Source: [U.S. Energy Information Administration](https://www.eia.gov/energyexplained/natural-gas/natural-gas-pipelines.php); Last updated: March 19, 2024. Also in Natural gas explained Natural gas Data and statistics Delivery and storage Natural gas pipelines Liquefied natural.

Compare A/B without opening run.json or results.json (these disclose the model mapping). Labels switch between documents.

For each answer: 0 = wrong/unsupported, 1 = useful but incomplete, 2 = correct and bounded. Check the type anchors in REVIEW_INSTRUCTIONS.md.

Apply the exact hard-fail criteria separately: any match => critical_error YES and score 0. Also flag other material unsafe/fabricated claims. A valid JSON response or exact quote is NOT evidence of engineering correctness.

## Source excerpts

### EIA-PIPELINE-B01

```
Gathering systems, primarily made up of small-diameter, low-pressure pipelines, move raw natural gas from the wellhead to a natural gas processing plant or to an interconnection with a larger mainline pipeline.
```

### EIA-PIPELINE-B02

```
Natural gas processing plants separate hydrocarbon gas liquids , nonhydrocarbon gases, and water from the natural gas before the natural gas is delivered into a mainline transmission system.
```

### EIA-PIPELINE-B03

```
Wide-diameter, high-pressure interstate transmission pipelines that cross state boundaries and intrastate transmission pipelines that operate within state boundaries transport natural gas from the producing and processing areas to storage facilities and distribution centers. Compressor stations (or pumping stations) on the pipeline network keep the natural gas flowing forward through the pipeline system.
```

### EIA-PIPELINE-B04

```
Local distribution companies deliver natural gas to consumers through small-diameter, lower pressure service lines.
```

## PUB-010 — calculation

Synthetic compressor screening only: suction is 30 bar absolute and discharge is 60 bar absolute. Define pressure ratio as discharge absolute pressure divided by suction absolute pressure. Calculate it. Can this alone determine compressor power?

Draft reference (reviewer only):

60 bara / 30 bara = 2, dimensionless. Power cannot be determined from the ratio alone; flow, gas composition/properties, suction temperature and compressor/driver efficiency or model are also needed. The numbers and formula are question givens, not EIA plant measurements.

Tolerance and basis:

```
{
  "value": 2,
  "absolute": 0.001,
  "units": "dimensionless",
  "basis": "absolute discharge / absolute suction"
}
```

Critical-error criteria:

Subtracts pressures and labels the result a ratio; changes absolute to gauge basis; invents compressor power.

### Response A

```
{
  "question_id": "PUB-010",
  "answer": "Pressure ratio = discharge absolute pressure / suction absolute pressure = 60 bar / 30 bar = 2.0. This ratio is dimensionless. However, this alone cannot determine compressor power, as power depends on additional factors such as gas flow rate, gas composition, efficiency, and temperature changes during compression. The provided text does not include data on flow rate, efficiency, or temperature, which are essential for power calculation. Therefore, while the pressure ratio is calculated as 2.0, it is insufficient to determine compressor power. Cited: 'Compressor stations (or pumping stations) on the pipeline network keep the natural gas flowing forward through the pipeline system.' (EIA-PIPELINE-B03)",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-PIPELINE",
      "block_id": "EIA-PIPELINE-B03",
      "quote": "Compressor stations (or pumping stations) on the pipeline network keep the natural gas flowing forward through the pipeline system."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-012

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "status": "stopped_no_retry"
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

## PUB-011 — missing_data

The text says compressor stations keep gas moving. What data are still needed before selecting a compressor for our line?

Draft reference (reviewer only):

The overview supplies no design duty. Request flow range and volume basis, suction/discharge pressures with gauge/absolute basis, temperatures, composition and gas properties, operating envelope/turndown, allowable pipeline pressure/losses and equipment/driver performance constraints. A selection cannot be made from this text alone.

Tolerance and basis:

```
null
```

Critical-error criteria:

Selects a size/power/operating pressure without the necessary duty or pressure basis.

### Response A

```
{
  "question_id": "PUB-011",
  "answer": "To select a compressor for the line, additional data are needed beyond the function of keeping gas moving. Specifically, required gas flow rate, inlet and outlet temperatures, gas composition (to determine compressibility and heating value), desired discharge temperature, and compressor efficiency are necessary. The text only states that compressor stations maintain flow but does not provide flow rate, temperature, or efficiency data. Without these, the size, type, and power of the compressor cannot be determined. Cited: 'Compressor stations (or pumping stations) on the pipeline network keep the natural gas flowing forward through the pipeline system.' (EIA-PIPELINE-B03)",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-PIPELINE",
      "block_id": "EIA-PIPELINE-B03",
      "quote": "Compressor stations (or pumping stations) on the pipeline network keep the natural gas flowing forward through the pipeline system."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-012

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "status": "stopped_no_retry"
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

## PUB-012 — brief

Summarize the sequence from gathering through processing, transmission and local distribution, including the purpose of compression.

Draft reference (reviewer only):

Gathering moves raw well gas toward processing or a mainline interconnection. Processing removes HGLs, nonhydrocarbon gases and water. High-pressure transmission moves gas toward storage/distribution; compressor stations maintain flow. Local delivery uses smaller, lower-pressure lines. This is a general sequence, not universal site routing.

Tolerance and basis:

```
null
```

Critical-error criteria:

Confuses high-pressure transmission with low-pressure local delivery; says processing adds water or impurities.

### Response A

```
{
  "question_id": "PUB-012",
  "answer": "Natural gas is first gathered via small-diameter, low-pressure pipelines from the wellhead to a processing plant (EIA-PIPELINE-B01). At the processing plant, hydrocarbon gas liquids, nonhydrocarbon gases, and water are removed (EIA-PIPELINE-B02). The cleaned gas is then transported via wide-diameter, high-pressure interstate or intrastate transmission pipelines to storage and distribution centers (EIA-PIPELINE-B03). Compressor stations maintain flow in transmission lines. Finally, local distribution companies deliver gas to consumers through small-diameter, lower-pressure service lines (EIA-PIPELINE-B04). Compression is essential to maintain pressure and flow over long distances in transmission systems. Cited: 'Compressor stations (or pumping stations) on the pipeline network keep the natural gas flowing forward through the pipeline system.' (EIA-PIPELINE-B03)",
  "uncertainties": [],
  "evidence": [
    {
      "source_id": "EIA-PIPELINE",
      "block_id": "EIA-PIPELINE-B01",
      "quote": "Gathering systems, primarily made up of small-diameter, low-pressure pipelines, move raw natural gas from the wellhead to a natural gas processing plant or to an interconnection with a larger mainline pipeline."
    },
    {
      "source_id": "EIA-PIPELINE",
      "block_id": "EIA-PIPELINE-B02",
      "quote": "Natural gas processing plants separate hydrocarbon gas liquids, nonhydrocarbon gases, and water from the natural gas before the natural gas is delivered into a mainline transmission system."
    },
    {
      "source_id": "EIA-PIPELINE",
      "block_id": "EIA-PIPELINE-B03",
      "quote": "Wide-diameter, high-pressure interstate transmission pipelines that cross state boundaries and intrastate transmission pipelines that operate within state boundaries transport natural gas from the producing and processing areas to storage facilities and distribution centers. Compressor stations (or pumping stations) on the pipeline network keep the natural gas flowing forward through the pipeline system."
    },
    {
      "source_id": "EIA-PIPELINE",
      "block_id": "EIA-PIPELINE-B04",
      "quote": "Local distribution companies deliver natural gas to consumers through small-diameter, lower pressure service lines."
    }
  ]
}
```

Mechanical check flags (not a reviewer grade): invalid_exact_citation:PUB-012

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.

### Response B

```
{
  "status": "stopped_no_retry"
}
```

Mechanical check flags (not a reviewer grade): none / not assessed

Score: ____ / 2. Critical error: UNASSESSED. Reviewer/date: ____. Evidence and corrections: ____.
