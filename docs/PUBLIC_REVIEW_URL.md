# Public-document review in production

Release target: https://broadbridge-capture.vercel.app/review/public-v1

Case Capture remains at https://broadbridge-capture.vercel.app/. Both routes use
one Auth.js session and the same exact-email allowlist. A signed-out review link
returns to its question after email sign-in. Review scores remain private to each
reviewer; public source documents do not make reviewer records public.

## Reviewer steps

1. Sign in with the approved email address. Open the newest emailed link within
   15 minutes. No Vercel account or Preview sharing token is needed on production.
2. Open Public-document scoring from Case Capture, or use the direct review URL.
3. Read the original question, source excerpts and frozen A/B answer. The original
   agency URL and draft reference answer are available alongside the response.
4. Choose 0/1/2, critical error Yes/No and whether a hard-fail criterion matched;
   add evidence/corrections and Save score. A matched hard fail requires 0/Yes.
5. Use Next to continue or Download my scores (CSV). Blank scores remain unreviewed.

The packet has 30 returned answers and 30 unavailable slots. Unavailable slots
cannot receive positive credit or an invented engineering-error flag. References
are reviewer aids; report defective questions/references in notes. Scores do not
grant training rights or release a training batch.

## Production release

Project: ProjectNext / broadbridge-capture, root apps/capture.
Database: the dedicated Broadbridge Neon production branch, verified by the operator.
The release uses migrations 0001 through 0006 without changing existing migration
bytes. 0005 is required by the helper functions used in 0006; its additional
intake tables remain empty. This release does not publish the source-intake UI,
start ingestion workers, call models, train, or start EC2.

Use the existing db.py migration path with separately supplied matching pooled
BROADBRIDGE_DATABASE_URL and direct DATABASE_URL_UNPOOLED; never reset production:

```powershell
python packs/oil-gas/scripts/db.py status
python packs/oil-gas/scripts/db.py migrate
python scripts/research/public_review_packet.py --db
```

The packet adapter verifies the four frozen input SHA-256 values before inserting
one immutable public-v1 packet. An identical registration is idempotent; changed
content is refused. No dev cases or reviewer scores are copied. Verify existing
capture records before and after migration, as well as packet digest and score counts.

Build the approved release with Production environment settings. Never promote a
Preview built against the dev database merely by repointing the production alias.
After deployment verify anonymous sign-in redirects, preserved review destinations,
protected score exports, runtime errors, and the release deployment commit.

Replace old Preview links in outgoing correspondence with the production review
URL. A Preview URL in an already-sent email retains its separate protection;
releasing production does not rewrite that URL or the recipient's email.

## Rollback

Return the production domain to the previously recorded production deployment.
Leave additive migrations, the immutable packet and any genuine scores in place.
Do not reset or drop tables. Record the actual deployment and database receipts
in ignored local operator storage after release.
