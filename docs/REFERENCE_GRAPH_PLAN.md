# Independent reference-graph work — execution plan

Scope: source-model topology and signed human tracing only. No vision-derived reference, training, EC2, client drawing or production change. Existing Foundry #13 and Broadbridge #17 stay drafts. New work uses successor branches and one implementation lane.

1. Verify source URLs, revisions, actual licenses and sizes; write a human registry and JSON manifest. UNKNOWN rights block training. DEXPI examples and benchmark families stay eval-only, including derivatives. Inspect SynthPID availability only.
2. Implement an optional local pyDEXPI adapter with explicit class/connection handling, original IDs/tags/line lineage and unknown directions preserved. Fail on unmapped topology. Round-trip C01 through pyDEXPI serialization and compare graph identities; record unsupported portions without guessing.
3. Generate eight or fewer original small schematics using pyDEXPI data models, render image/graph/seed pairs locally. Evaluate with the existing bounded vision profile and independent checker. Separate software round-trip metrics from actual vision metrics; retain all failures and unknown directions.
4. Read one bounded PID2Graph annotation/image sample using a published per-file endpoint if available. Preserve connectors, patch boundaries and unknown direction; document gaps and the real-world subset's licensing separately.
5. Specify human-trace sign-off (tracer, independent reviewer Bill, date, drawing revision, exact graph/source hashes and proposal diff). Unsigned traces remain UNREVIEWED. No client data is collected.
6. Run the existing 215/375 regression groups plus new tests, record receipts and licensing blocks, and publish successor draft PRs only.

Pre-flight/rulings:

- The current v1 frozen checker limits nodes/edges to a tiny visual proposal and carries no line IDs. Preserve a lossless native topology artifact with lineage and project explicit bounded views to the existing frozen schema. Do not silently drop nodes or flatten parallel lines.
- PID2Graph's full archive is 9,303,633,645 bytes. It is blocked by the user's >1 GB approval boundary. Zenodo exposes individual archive members; obtain only a small named sample, with hard byte limits, never the whole archive.
- pyDEXPI currently declares AGPL-3.0. Use it only as an optional local research dependency; proprietary deployment remains a license-review decision. A software license does not automatically license bundled third-party drawings.
- Synthetic generation must use original parameters/shapes, not mutate the eval-only C01 or OPEN100 benchmark families.

Progress:

- Source registry and pinned acquisition receipt complete; 7,511,497 bytes acquired, no archive download. UNKNOWN rights block training.
- C01 adapter and JSON/source-ID-sidecar round-trip complete: 37 nodes, 31 edges, four unresolved endpoints retained. Tests exposed upstream loss of Proteus IDs; sidecar is explicit rather than inventing IDs.
- Six original models + one renderer correction evaluated locally; raw receipts retained. Qualified edge P/R 87.5%/100%, known-direction P/R 75%/75%; no training admitted.
- PID2Graph small member mapped: 452 nodes / 496 undirected edges. Ruling: paper confirms segment-overlap conversion; classify as annotation adjacency, not human-signed/native gold. This is a stronger provenance distinction than the initial source list assumed.
- Ruling: visually ambiguous first crossing is not qualified gold. Retain original result; add one corrected rendering in the same family (seven images total, within the eight-image plan cap). Do not retry based on model score.
- Human sign-off design complete; Foundry refuses unsigned traces even when a reviewer name is supplied.
- Foundry regression + new tests: 234 passed. Broadbridge original regression + new tests: 389 passed / 113 skipped. Final combined counts, renderer portability limits and review findings are recorded in the results document.
- Final read-only review complete; all three findings fixed and regression-tested. Successor draft PR publication follows. Original #13/#17 remain drafts at their original heads.
