import { z } from "zod";
export const PROJECT = "broadbridge-oil-gas";
export const MAX_UPLOAD_BYTES = 50 * 1024 * 1024;
export const identifier = z.string().regex(/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/);
export const hash = z.string().regex(/^[a-f0-9]{64}$/);
export const filename = z.string().trim().min(1).max(240).refine(v => !/[\\/\u0000-\u001f\u007f]/.test(v) && v !== "." && v !== "..", "Use a filename without paths or control characters.");
export const uploadSchema = z.strictObject({ original_filename: filename, media_type: z.string().regex(/^[a-zA-Z0-9!#$&^_.+-]+\/[a-zA-Z0-9!#$&^_.+-]+$/).max(150), size_bytes: z.number().int().min(1).max(MAX_UPLOAD_BYTES), content_sha256: hash, confidentiality: z.enum(["public", "internal", "confidential", "restricted"]) });
export const identitySchema = z.strictObject({ source_id: identifier, revision_id: identifier, content_sha256: hash });
const reviewId = z.union([z.string().regex(/^[1-9][0-9]*$/), z.number().int().positive().safe().transform(String)]).nullable();
export const rightsSchema = identitySchema.extend({ decision: z.enum(["approved", "revoked"]), permitted_use: z.enum(["training", "testing_only", "reference_only"]), rights_basis: z.string().trim().min(1).max(4000), expected_review_id: reviewId });
export const candidateReviewSchema = z.strictObject({ example_id: identifier, candidate_hash: hash, decision: z.enum(["approved", "rejected"]), reason: z.string().trim().min(1).max(4000), expected_review_id: reviewId });
export const sourceSchema = uploadSchema.extend({ schema: z.literal("foundry.source_revision/1"), project_id: z.literal(PROJECT), source_id: identifier, revision_id: identifier, family_id: identifier, object_key: z.string().regex(/^incoming\/broadbridge-oil-gas\/[A-Za-z0-9._/-]+$/).refine(v => !v.split("/").includes("..")), permission: z.strictObject({ permitted_use: z.enum(["training", "testing_only", "reference_only"]), status: z.enum(["pending", "approved", "revoked"]), rights_basis: z.string(), reviewed_by: z.string().nullable(), reviewed_at: z.string().nullable() }), relationships: z.array(z.strictObject({ kind: z.enum(["attachment", "thread", "version", "case_family"]), target_id: identifier })) });
export type Source = z.infer<typeof sourceSchema>;
export type Identity = z.infer<typeof identitySchema>;
export type RightsInput = z.infer<typeof rightsSchema>;
export type CandidateReviewInput = z.infer<typeof candidateReviewSchema>;
export type SourceRow = Identity & { source_ref: string; original_filename: string; media_type: string; size_bytes: number; confidentiality: string; current_permission_status: string; current_permitted_use: string; current_rights_review_id: string | null; created_by: string; job_id: string | null; state: string | null; error_code: string | null; document_status: string | null };
export const sourceCursorSchema = identitySchema.nullable();
export const candidateCursorSchema = z.strictObject({ example_id: identifier, candidate_hash: hash }).nullable();
export type SourceCursor = z.infer<typeof sourceCursorSchema>;
export type CandidateCursor = z.infer<typeof candidateCursorSchema>;
export const MAX_ACTION_BYTES = 1024 * 1024;
export function previewLimitError() { return Object.assign(new Error("Preview exceeds the safe response budget"), { code: "PREVIEW_TOO_LARGE" }); }
// Reserve framing space and count nested JSON/string escaping conservatively.
export function actionResponseBytes(value: unknown) {
  const encoded = JSON.stringify({ ok: true, value }).replace(/[<>&\u2028\u2029]/g, char => `\\u${char.charCodeAt(0).toString(16).padStart(4, "0")}`);
  return new TextEncoder().encode(encoded).byteLength * 2 + 16384;
}
export function assertActionBudget<T>(value: T): T { if (actionResponseBytes(value) > MAX_ACTION_BYTES) throw previewLimitError(); return value; }
export type Candidate = { example_id: string; candidate_hash: string; status: string; review_id: string | null; reason: string | null; candidate_record: Record<string, unknown> | null; preview_oversized?: boolean };
export type Preview = { document: Record<string, unknown> | null };
export type CandidatePage = { candidates: Candidate[]; next_cursor: CandidateCursor };
export type Snapshot = { sources: SourceRow[]; next_cursor: SourceCursor };
export type ActionResult<T> = { ok: true; value: T } | { ok: false; error: string; conflict?: boolean };
