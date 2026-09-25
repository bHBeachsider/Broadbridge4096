"use server";
import { z } from "zod";
import { requireActor } from "../../auth";
import { identitySchema, rightsSchema, candidateReviewSchema, hash, type ActionResult } from "../../lib/ingestion-validation";
import * as repository from "../../lib/ingestion-repository";
import * as service from "../../lib/ingestion-service";
async function protect<T>(work: (actor: string) => Promise<T>): Promise<ActionResult<T>> {
  try { return { ok: true, value: await work(await requireActor()) }; }
  catch (error) {
    if (error instanceof z.ZodError) return { ok: false, error: "Check the file metadata, 50 MiB limit, and required review fields." };
    if (typeof error === "object" && error !== null && "code" in error && error.code === "40001") return { ok: false, conflict: true, error: "This source or review changed. Refresh and review the current version before saving." };
    return { ok: false, error: "Operation unavailable. Any registered source remains pending. Refresh status, check your sign-in, and retry; no approval or completed upload is implied." };
  }
}
export async function prepareUploadAction(input: unknown) { return protect(actor => service.prepareUpload(input, actor)); }
export async function resumeUploadAction(input: unknown) { return protect(() => service.resumeUpload(identitySchema.parse(input))); }
export async function completeUploadAction(input: unknown) { return protect(() => service.completeUpload(identitySchema.parse(input))); }
export async function loadIngestionAction() { return protect(async () => ({ sources: await repository.listSources() })); }
export async function previewSourceAction(input: unknown, jobId: unknown) { return protect(() => service.previewSource(identitySchema.parse(input), hash.nullable().parse(jobId))); }
export async function retryIngestionAction(input: unknown, jobId: unknown) { return protect(() => service.retryJob(identitySchema.parse(input), hash.parse(jobId))); }
export async function reviewRightsAction(input: unknown) { return protect(actor => repository.saveRights(rightsSchema.parse(input), actor)); }
export async function reviewCandidateAction(input: unknown) { return protect(actor => repository.saveCandidateReview(candidateReviewSchema.parse(input), actor)); }
