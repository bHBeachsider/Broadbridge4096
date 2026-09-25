import "server-only";
import { getSql } from "./db";
import { sourceSchema, type Source, type Identity, type RightsInput, type CandidateReviewInput, type SourceRow, type Candidate, type SourceCursor, type CandidateCursor, type Snapshot, type CandidatePage, MAX_ACTION_BYTES } from "./ingestion-validation";
export async function registerSource(source: Source, sourceRef: string, actor: string) {
  const sql = getSql();
  await sql`SELECT broadbridge.register_source_revision(${JSON.stringify(source)}::jsonb, ${sourceRef}, ${actor})`;
}
export async function findSource(identity: Identity): Promise<{ source: Source; sourceRef: string }> {
  const sql = getSql();
  const rows = await sql`SELECT source_record, registry_ref FROM broadbridge.source_revisions WHERE source_id=${identity.source_id} AND revision_id=${identity.revision_id} AND content_sha256=${identity.content_sha256}`;
  if (rows.length !== 1) throw Object.assign(new Error("Source changed"), { code: "40001" });
  return { source: sourceSchema.parse(rows[0].source_record), sourceRef: String(rows[0].registry_ref) };
}
export async function listSources(cursor: SourceCursor = null): Promise<Snapshot> {
  const sql = getSql();
  const rows = await sql`SELECT s.*, s.current_rights_review_id::text AS current_rights_review_id, j.job_id,j.state,j.error_code,j.result_json::jsonb->>'document_status' AS document_status FROM broadbridge.ingestion_source_status s LEFT JOIN LATERAL (SELECT job_id,state,error_code,result_json FROM broadbridge.ingestion_jobs WHERE source_json::jsonb->>'project_id'='broadbridge-oil-gas' AND source_json::jsonb->>'source_id'=s.source_id AND source_json::jsonb->>'revision_id'=s.revision_id AND source_json::jsonb->>'content_sha256'=s.content_sha256 ORDER BY created_at DESC,job_id DESC LIMIT 1) j ON true WHERE (${cursor?.source_id ?? null}::text IS NULL OR (s.source_id,s.revision_id,s.content_sha256) > (${cursor?.source_id ?? null},${cursor?.revision_id ?? null},${cursor?.content_sha256 ?? null})) ORDER BY s.source_id,s.revision_id,s.content_sha256 LIMIT 51`;
  const sources = rows.slice(0, 50).map(row => ({ source_ref: String(row.source_ref), source_id: String(row.source_id), revision_id: String(row.revision_id), content_sha256: String(row.content_sha256), original_filename: String(row.original_filename), media_type: String(row.media_type), size_bytes: Number(row.size_bytes), confidentiality: String(row.confidentiality), current_permission_status: String(row.current_permission_status), current_permitted_use: String(row.current_permitted_use), current_rights_review_id: row.current_rights_review_id as string | null, created_by: String(row.created_by), job_id: row.job_id as string | null, state: row.state as string | null, error_code: row.error_code as string | null, document_status: row.document_status as string | null }));
  const last = sources.at(-1);
  return { sources, next_cursor: rows.length > 50 && last ? { source_id: last.source_id, revision_id: last.revision_id, content_sha256: last.content_sha256 } : null };
}
export async function findJob(identity: Identity, jobId: string) {
  await findSource(identity);
  const sql = getSql();
  const rows = await sql`SELECT job_id,result_json::jsonb AS result FROM broadbridge.ingestion_jobs WHERE job_id=${jobId} AND source_json::jsonb->>'project_id'='broadbridge-oil-gas' AND source_json::jsonb->>'source_id'=${identity.source_id} AND source_json::jsonb->>'revision_id'=${identity.revision_id} AND source_json::jsonb->>'content_sha256'=${identity.content_sha256}`;
  if (rows.length !== 1) throw new Error("Unknown job");
  return rows[0];
}
export async function listCandidates(identity: Identity, cursor: CandidateCursor = null): Promise<CandidatePage> {
  const sql = getSql();
  const rows = await sql`SELECT c.example_id,c.candidate_hash,CASE WHEN octet_length(c.candidate_record::text) <= ${MAX_ACTION_BYTES / 2 - 16384} THEN c.candidate_record ELSE NULL END AS candidate_record,octet_length(c.candidate_record::text) > ${MAX_ACTION_BYTES / 2 - 16384} AS preview_oversized,r.status,r.review_id::text AS review_id,r.reason FROM broadbridge.candidate_records c LEFT JOIN broadbridge.current_candidate_reviews r USING(example_id,candidate_hash) WHERE c.candidate_record->'source_refs' @> ${JSON.stringify([identity])}::jsonb AND (${cursor?.example_id ?? null}::text IS NULL OR (c.example_id,c.candidate_hash) > (${cursor?.example_id ?? null},${cursor?.candidate_hash ?? null})) ORDER BY c.example_id,c.candidate_hash LIMIT 21`;
  const candidates: Candidate[] = rows.slice(0, 20).map(row => ({ example_id: String(row.example_id), candidate_hash: String(row.candidate_hash), candidate_record: row.candidate_record as Record<string, unknown> | null, preview_oversized: Boolean(row.preview_oversized), status: String(row.status ?? "pending"), review_id: row.review_id as string | null, reason: row.reason as string | null }));
  const last = candidates.at(-1);
  return { candidates, next_cursor: rows.length > 20 && last ? { example_id: last.example_id, candidate_hash: last.candidate_hash } : null };
}
export async function saveRights(input: RightsInput, actor: string) {
  const sql = getSql();
  await sql`SELECT broadbridge.review_source_rights(${input.source_id},${input.revision_id},${input.content_sha256},${input.decision},${input.permitted_use},${input.rights_basis},${input.expected_review_id}::bigint,${actor})`;
}
export async function saveCandidateReview(input: CandidateReviewInput, actor: string) {
  const sql = getSql();
  await sql`SELECT broadbridge.review_candidate(${input.example_id},${input.candidate_hash},${input.decision},${input.reason},${input.expected_review_id}::bigint,${actor})`;
}
