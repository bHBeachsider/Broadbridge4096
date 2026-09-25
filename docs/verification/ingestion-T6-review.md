# T6 domain acceptance — 25 September 2026

Specification review: **PASS**. Generic engine code remains in slm-foundry and
is loaded through an absolute external path. The existing case_record/1
contract is unchanged. Case user messages contain unit/service, decision-time
information and question/evidence identifiers; hindsight and scoring criteria
do not enter the input. Signed/training case eligibility and conservative
confidentiality are covered by regressions.

The additive 0005 migration owns Broadbridge source rights, durable jobs,
candidate identity/review/artifact bindings, datasets and model-run references.
Source rights and technical review remain distinct. Original revisions and
review history are immutable. Release approval names the exact current content
hash, and the bridge re-verifies artifact bytes and current database decisions.
Object publication and SQL are explicitly not a distributed transaction.

Independent quality re-review: **APPROVE**, source commit
`a44952f42a690e91d9631dca9d2896f571e9b1ca`. **56 tests passed** on an owned
loopback PostgreSQL 17 container. The reviewer independently replayed the three
original findings: historical test holdouts survive replacement; a revoked
source can be explicitly excluded while valid sources release; incomplete
source JSON is rejected with SQLSTATE 23514 and leaves no row.

Producer verification also passed **277 offline pack tests** and **1 migration
idempotence/checksum test**. Committed SQL column/foreign-key/count evidence:
`packs/oil-gas/db/verification/ingestion-T6-fixes.json`.

The combined local browser rehearsal subsequently exercised registration,
source rights, exact-hash candidate acceptance and idempotent dataset recording
through these functions. Its separate evidence belongs to T8.

No remote database was migrated. Migration 0005 has only run on owned disposable
databases; production application requires Brad's separate go. No real source
data, model endpoint or EC2 instance was used.
