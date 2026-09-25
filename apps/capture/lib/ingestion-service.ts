import "server-only";
import { createHash, randomUUID } from "node:crypto";
import { z } from "zod";
import { localIngestionTestEnabled } from "./db";
import * as repository from "./ingestion-repository";
import * as storage from "./ingestion-storage";
import { PROJECT, uploadSchema, sourceSchema, type Identity, type Preview } from "./ingestion-validation";
export async function engineRequest(path: string, body: unknown) {
  const base = process.env.INGESTION_API_URL; const token = process.env.INGESTION_API_TOKEN;
  if (!base || !token || !/^[\x21-\x7e]{1,4096}$/.test(token)) throw new Error("Ingestion service unavailable");
  const url = new URL(base); const local = localIngestionTestEnabled();
  if ((local ? !["http:", "https:"].includes(url.protocol) : url.protocol !== "https:") || url.username || url.password || url.search || url.hash || url.pathname !== "/") throw new Error("Invalid ingestion endpoint");
  const response = await fetch(new URL(path, url), { method: "POST", headers: { "content-type": "application/json", authorization: `Bearer ${token}` }, body: JSON.stringify(body), cache: "no-store", redirect: "error", signal: AbortSignal.timeout(20000) });
  if (!response.ok) throw new Error("Ingestion service unavailable");
  const text = await response.text();
  if (text.length > 1024 * 1024) throw new Error("Invalid ingestion response");
  return JSON.parse(text) as unknown;
}
export async function prepareUpload(input: unknown, actor: string) {
  const metadata = uploadSchema.parse(input);
  const id = randomUUID();
  const source = sourceSchema.parse({ ...metadata, schema: "foundry.source_revision/1", project_id: PROJECT, source_id: id, revision_id: "r1", family_id: id, object_key: `incoming/${PROJECT}/${id}/original`, permission: { status: "pending", permitted_use: "reference_only", rights_basis: "", reviewed_by: null, reviewed_at: null }, relationships: [] });
  // Foundry hashes canonical JSON, including quotes around this ASCII object key.
  const sourceRef = `registry/${PROJECT}/${createHash("sha256").update(JSON.stringify(source.object_key)).digest("hex")}.json`;
  await repository.registerSource(source, sourceRef, actor);
  return { identity: { source_id: source.source_id, revision_id: source.revision_id, content_sha256: source.content_sha256 }, ...await storage.signUpload(source) };
}
export async function resumeUpload(identity: Identity) {
  const { source } = await repository.findSource(identity);
  return { identity, ...await storage.signUpload(source) };
}
export async function completeUpload(identity: Identity) {
  const { source, sourceRef } = await repository.findSource(identity);
  await storage.verifyUpload(source);
  const receipt = z.object({ source_ref: z.string(), object_key: z.string() }).parse(await engineRequest("/v1/sources", { source }));
  if (receipt.source_ref !== sourceRef || receipt.object_key !== source.object_key) throw new Error("Registration identity mismatch");
  const job = z.object({ job_id: z.string().regex(/^[a-f0-9]{64}$/), state: z.enum(["queued", "running", "succeeded", "retry", "failed"]) }).parse(await engineRequest("/v1/jobs", { source_ref: sourceRef }));
  return job;
}
export async function retryJob(identity: Identity, jobId: string) {
  await repository.findJob(identity, jobId);
  await engineRequest(`/v1/jobs/${jobId}/retry`, {});
}
export async function previewSource(identity: Identity, jobId: string | null): Promise<Preview> {
  await repository.findSource(identity);
  const candidates = await repository.listCandidates(identity);
  if (!jobId) return { document: null, candidates };
  const row = await repository.findJob(identity, jobId);
  const result = z.object({ normalized: z.object({ key: z.string(), sha256: z.string(), size_bytes: z.number() }) }).safeParse(row.result);
  if (!result.success) return { document: null, candidates };
  const document = z.object({ source: sourceSchema, blocks: z.array(z.record(z.string(), z.unknown())), status: z.string() }).passthrough().parse(await storage.readVerifiedDocument(result.data.normalized, jobId));
  if (document.source.source_id !== identity.source_id || document.source.revision_id !== identity.revision_id || document.source.content_sha256 !== identity.content_sha256) throw new Error("Preview identity mismatch");
  return { document, candidates };
}
