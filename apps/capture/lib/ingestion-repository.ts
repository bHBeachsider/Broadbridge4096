import "server-only";
import { getSql } from "./db";
import { sourceSchema, type Source, type Identity, type RightsInput, type CandidateReviewInput, type SourceRow, type Candidate } from "./ingestion-validation";
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
export async function listSources(): Promise<SourceRow[]> {
  const sql = getSql();
  const rows = await sql`SELECT s.*, s.current_rights_review_id::text AS current_rights_review_id, j.job_id,j.state,j.error_code,j.result_json::jsonb->>'document_status' AS document_status FROM broadbridge.ingestion_source_status s LEFT JOIN LATERAL (SELECT job_id,state,error_code,result_json FROM broadbridge.ingestion_jobs WHERE source_json::jsonb->>'project_id'='broadbridge-oil-gas' AND source_json::jsonb->>'source_id'=s.source_id AND source_json::jsonb->>'revision_id'=s.revision_id AND source_json::jsonb->>'content_sha256'=s.content_sha256 ORDER BY created_at DESC LIMIT 1) j ON true ORDER BY s.created_at DESC LIMIT 200`;
  return rows.map(row => ({ source_ref: String(row.source_ref), source_id: String(row.source_id), revision_id: String(row.revision_id), content_sha256: String(row.content_sha256), original_filename: String(row.original_filename), media_type: String(row.media_type), size_bytes: Number(row.size_bytes), confidentiality: String(row.confidentiality), current_permission_status: String(row.current_permission_status), current_permitted_use: String(row.current_permitted_use), current_rights_review_id: row.current_rights_review_id as string | null, created_by: String(row.created_by), job_id: row.job_id as string | null, state: row.state as string | null, error_code: row.error_code as string | null, document_status: row.document_status as string | null }));
}
export async function findJob(identity: Identity, jobId: string) {
  await findSource(identity);
  const sql = getSql();
  const rows = await sql`SELECT job_id,result_json::jsonb AS result FROM broadbridge.ingestion_jobs WHERE job_id=${jobId} AND source_json::jsonb->>'project_id'='broadbridge-oil-gas' AND source_json::jsonb->>'source_id'=${identity.source_id} AND source_json::jsonb->>'revision_id'=${identity.revision_id} AND source_json::jsonb->>'content_sha256'=${identity.content_sha256}`;
  if (rows.length !== 1) throw new Error("Unknown job");
  return rows[0];
}
export async function listCandidates(identity: Identity): Promise<Candidate[]> {
  const sql = getSql();
  const rows = await sql`SELECT c.example_id,c.candidate_hash,c.candidate_record,r.status,r.review_id::text AS review_id,r.reason FROM broadbridge.candidate_records c LEFT JOIN broadbridge.current_candidate_reviews r USING(example_id,candidate_hash) WHERE c.candidate_record->'source_refs' @> ${JSON.stringify([identity])}::jsonb ORDER BY c.created_at DESC LIMIT 100`;
  return rows.map(row => ({ example_id: String(row.example_id), candidate_hash: String(row.candidate_hash), candidate_record: row.candidate_record as Record<string, unknown>, status: String(row.status ?? "pending"), review_id: row.review_id as string | null, reason: row.reason as string | null }));
}
export async function saveRights(input: RightsInput, actor: string) {
  const sql = getSql();
  await sql`SELECT broadbridge.review_source_rights(${input.source_id},${input.revision_id},${input.content_sha256},${input.decision},${input.permitted_use},${input.rights_basis},${input.expected_review_id}::bigint,${actor})`;
}
export async function saveCandidateReview(input: CandidateReviewInput, actor: string) {
  const sql = getSql();
  await sql`SELECT broadbridge.review_candidate(${input.example_id},${input.candidate_hash},${input.decision},${input.reason},${input.expected_review_id}::bigint,${actor})`;
}
