"use server";

import { z } from "zod";
import { requireActor } from "../auth";
import { persistCase, persistWorkflow, removeCase } from "../lib/repository";
import { parseCase, parseWorkflow, type StoredCase, type StoredWorkflow } from "../lib/validation";

type Failure = { ok: false; error: string; conflict?: boolean };
type Result<T> = { ok: true; value: T } | Failure;
const revisionSchema = z.string().min(1).max(80).nullable();

function failure(error: unknown): Failure {
  if (error instanceof z.ZodError) return { ok: false, error: "Some fields do not match the capture form. Check the selected values and required fields." };
  const code = typeof error === "object" && error !== null && "code" in error ? String(error.code) : "";
  if (code === "40001") return { ok: false, error: "This record changed in another tab. Copy your unsaved text, reload, and resolve the changes.", conflict: true };
  if (code === "23503") return { ok: false, error: "This case is linked to saved evidence or runs and cannot be deleted." };
  if (code === "23505") return { ok: false, error: "A case or question ID already exists. Reload and check the IDs." };
  if (code === "23514") return { ok: false, error: "The record could not be accepted. Check sign-off and required fields; changed signed content needs review again." };
  // Do not return raw database/provider diagnostics or SQL containing case text.
  return { ok: false, error: "Save unavailable. Check your sign-in and required fields, then retry. Your text remains in this tab." };
}

export async function saveCaseAction(input: unknown, revision: string | null): Promise<Result<StoredCase>> {
  try {
    const actor = await requireActor();
    const record = parseCase(input);
    record.updated_at = new Date().toISOString();
    parseCase(record); // The server timestamp must also fit within the record cap.
    return { ok: true, value: await persistCase(record, actor, revisionSchema.parse(revision)) };
  } catch (error) { return failure(error); }
}

export async function saveWorkflowAction(input: unknown, revision: string | null): Promise<Result<StoredWorkflow>> {
  try {
    const actor = await requireActor();
    const record = parseWorkflow(input);
    record.updated_at = new Date().toISOString();
    parseWorkflow(record);
    return { ok: true, value: await persistWorkflow(record, actor, revisionSchema.parse(revision)) };
  } catch (error) { return failure(error); }
}

export async function deleteCaseAction(caseId: string, revision: string): Promise<{ ok: true } | Failure> {
  try {
    const actor = await requireActor();
    const id = z.string().regex(/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/).parse(caseId);
    await removeCase(id, actor, z.string().min(1).max(80).parse(revision));
    return { ok: true };
  } catch (error) { return failure(error); }
}
