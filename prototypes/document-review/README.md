# Engineering document review demo

A local, fictional demonstration for Broadbridge Oil & Gas. It compares an
equipment register, datasheet table and explicitly tagged drawing, then presents
an evidence-linked discrepancy register. It uses Python's standard library at
runtime. It does not use an LLM, credentials, database, network or GPU.

Open [the example report](example/report.html) in a browser. Keep the neighboring
review.css and review.js files with it. The report also works from a local
static server. All package and report records are invented; no client documents,
expert approvals or training examples are included.

## Try it

1. Search for **E-202**: the register states 200 degC and the current datasheet
   states 220 degC for the same operating condition.
2. Select either evidence button to inspect its original record, revision and
   SHA-256. Superseded revision A remains inspectable but is excluded from
   comparisons of current values.
3. Select **V-302** to see a gauge/absolute pressure mismatch. No atmospheric
   pressure or engineering answer is invented.
4. Enter a disposition and note. Reload to check browser-local persistence.
   Add your name and **Export review notes** to save a portable JSON record.
5. Clear filters. **E-203** is separately marked as not comparable because its
   records describe operating and design conditions.

Local notes are not authenticated sign-off. They remain in that browser's
storage under the report hash. If storage is blocked, the page warns that notes
will be lost and export remains available. Export before changing computers,
browsers or source packages. There is no cloud sync or note-import feature.

## Reproduce

From this repository checkout, using Python 3.13:

~~~powershell
python prototypes/document-review/review.py --out prototypes/document-review/output/run-001
~~~

The output directory must be new and outside the input directory. To inspect a
modified copy of the fictional package:

~~~powershell
python prototypes/document-review/review.py --package C:\path\to\fictional-package --out C:\path\to\new-report
~~~

Do not point this prototype at live client archives. It only accepts the
documented synthetic package contract. Inputs remain unchanged. A temporary
directory is renamed into place only after every output is ready; an existing
output is never replaced.

Outputs:

- report.html, review.css, review.js: offline interactive view.
- report.json: findings, withheld comparisons, provenance and deterministic ID.
- normalized.json: source records with document/revision/locator/hash.
- Exported review notes: user-generated JSON bound to the report ID; saved by
  the browser only on request. Keep actual reviewer notes in private storage.

Optional local browser serving, scoped to the example directory:

~~~powershell
python -m http.server 8766 --bind 127.0.0.1 --directory prototypes/document-review/example
# Visit http://127.0.0.1:8766/report.html ; Ctrl+C stops the local server.
~~~

## Input contract

fixtures/package.json uses schema broadbridge.document_demo/1, a package_id,
title, synthetic=true and revision_index=revision_index.csv.

The revision index columns, in order, are document_id, revision, status, kind,
file. Exactly one document identity and one approved revision are required for
each kind: equipment, datasheets and drawing. Historical revisions are marked
superseded; dates or alphabetic revision ordering never select the current one.

| File kind | Required columns / representation |
| --- | --- |
| equipment | tag, service, condition, pressure, pressure_unit, pressure_basis, temperature, temperature_unit, datasheet_id, datasheet_revision |
| datasheets | row_id, asset_tags, condition, pressure, pressure_unit, pressure_basis, temperature, temperature_unit |
| drawing | SVG elements with unique id and explicit data-tag attributes; label extraction only |

A vertical bar in asset_tags represents a deliberately unresolved multi-asset
association, not permission to duplicate a value across those assets.

Supported pressure units: Pa, kPa, MPa, bar, psi. Pressure basis must be explicitly
absolute or gauge. Supported temperature units: degC, degF, K. Conditions are
operating, design or test. Unknown or different conditions are withheld from
numerical comparison. Equivalent values are normalized with Decimal arithmetic;
1e-9 in base units is a conversion-rounding allowance, not engineering tolerance.
A value difference is a review finding, not a declaration of equipment failure.

Filenames must be plain names within the package. Sources are capped at 1 MiB;
the index at 50 entries and CSV tables at 5,000 records. Malformed contracts,
conflicting approved revisions and active SVG content fail the package visibly.
Unknown quantities/units produce unresolved findings, not fabricated values.

## Fixture coverage and limits

The twelve register assets are P-101 through P-104, E-201 through E-203, V-301,
V-302, T-401, C-501 and F-601. There are six document versions and a control index.
The current drawing substitutes T-499 for F-601 deliberately.

The separate, hand-specified tests/expected_findings.json is never loaded by the
checker. The exact expected result is ten findings: duplicate register tag,
missing service, ambiguous datasheet association, temperature conflict, wrong
unit dimension, pressure-basis mismatch, superseded reference, unsupported unit,
unmatched drawing tag and missing drawing tag. Three need clarification.
One operating/design comparison remains explicitly unassessed. The clean P-101
control uses equivalent 10 bar and 1,000 kPa values.

Tests also cover unmatched datasheets, duplicate/unknown references, numeric
edge cases, changed sources, malformed input, source isolation, output refusal,
inert source text, browser storage failure, local export and responsive layout.
These demonstrate software behavior on this fixture, not engineering accuracy
on unseen documents, ROI or a trained petrochemical model.

Actual PDF/OCR, spreadsheet parsing, P&ID connectivity, native CAD/IFC properties,
geometry and general archive ingestion are not implemented here. The drawing is
an equipment-label reference, not a flowsheet or spatial model. Future adapters
must establish source/field mapping before reusing these comparisons.

## Tests and validation

Development dependencies only (not needed to open the report or run the checker):

~~~powershell
python -m pip install -r prototypes/document-review/requirements-dev.txt
python -m playwright install chromium
python -m pytest prototypes/document-review/tests -q
~~~

On Linux CI, use python -m playwright install --with-deps chromium.
No real credentials or network model services are used by tests. Installing test
dependencies/browser binaries is a separate download step.

Validation on 26 September 2026: **35 passed**, including five real Chromium
browser tests. The example was also opened directly from disk, with no page
errors, and visually inspected at desktop and mobile widths. All ten seeded
findings matched the independent key, with zero additional findings in that
fixture. Current-condition separation, equivalent-unit controls and deterministic
report hashes passed.

## Relationship to the SLM project

This is a separate CAD/commercial workstream on codex/cad-document-review. The
capture app, Foundry code, expert-case contract, source rights, data splits and
training gates are unchanged. Source-document discrepancies may eventually be
explained by Qwen, but a report disposition here grants neither training rights
nor technical acceptance. The next integration choice is an IFC property-query
spike or a permitted customer document sample after Bill identifies the useful
workflow.
