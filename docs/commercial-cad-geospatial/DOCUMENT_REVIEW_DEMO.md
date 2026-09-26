# Local engineering-document review demonstration

The first commercial CAD/document prototype is now at
[prototypes/document-review](../../prototypes/document-review/README.md).

It contains a fictional twelve-asset package, two document revisions, a
deterministic checker, an evidence-linked interactive report and local review
notes. Open the [example report](../../prototypes/document-review/example/report.html)
in a browser or follow the local serving instructions in its README.

Expected fixture result: ten discrepancies/clarifications and one explicitly
withheld operating-versus-design comparison. Technical proof comes from an
independent defect key and executable tests; the fixture is not a measured
customer benefit or engineering approval.

This work implements the approved document-demo scope A1-A4. IFC queries and
geometry (A5), real client samples and commercial validation remain subsequent
steps. No case-capture or public-review production route changes are included.

Branch: codex/cad-document-review, based on the current released main to avoid
carrying old application snapshots into this separate feature. The commercial
research and private partner correspondence remain on their existing branches.
