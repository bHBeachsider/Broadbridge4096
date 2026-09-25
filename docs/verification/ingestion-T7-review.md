# T7 source intake and review acceptance — 25 September 2026

Specification review: **PASS**. The capture app reuses existing allowlisted
Auth.js sessions and server actions. It issues unique scoped immutable upload
keys, records pending/reference-only source rights and queues CPU extraction
only after object verification. Source permissions and technical candidate
acceptance are distinct, hash-bound audited decisions. Uploaded content cannot
supply the signed-in actor or approve itself.

Status comes from durable jobs. Evidence previews retain block/source metadata.
Keyset pagination reaches every source revision and candidate hash. Responses
are bounded to 1 MiB; oversized records require explicit offline review and
cannot be approved from a truncated preview.

Independent quality re-review: **APPROVE** at integration source `aac3774`:
**56 targeted tests passed**. Producer verification: **125 unit tests passed**,
8 database-gated tests skipped in that unit-only command; TypeScript and Next.js
build passed. Actual owned PostgreSQL acceptance separately passed **2 repository
tests**, including 201 source revisions and 101 candidate versions beyond the
old fixed windows. The final fixture correction restores the existing candidate
field names and required fields; no assertion was removed.

The combined browser rehearsal passed actual local Auth.js magic-link sign-in,
two immutable uploads, two CPU extraction jobs, stale rights rejection,
authenticated exact-hash candidate approval, and dataset release. T8 records
the full browser-to-release evidence and light/dark/mobile screenshots.

No live R2 signature/CORS, deployed preview database mapping, production write,
email delivery, EC2 or model inference was tested. Automatic Vercel preview
builds do not authorize uploads there. Apply migration 0005 only after the
target database is explicitly approved; production needs Brad's separate go.
