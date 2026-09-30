"use server";
import { requireActor } from "../../../auth";
import { saveInputSchema, type SavedQuestionnaire } from "../../../lib/questionnaire";
import { persistQuestionnaire } from "../../../lib/questionnaire-repository";
export async function saveQuestionnaire(input: unknown): Promise<{ok: true; value: SavedQuestionnaire} | {ok: false; message: string; conflict: boolean}> {
  try {
    const actor = await requireActor();
    const parsed = saveInputSchema.parse(input);
    return {ok: true, value: await persistQuestionnaire(parsed.record, actor, parsed.expected_revision)};
  } catch (error) {
    const conflict = typeof error === "object" && error !== null && "code" in error && error.code === "40001";
    return {ok: false, conflict, message: conflict
      ? "This response changed in another tab. Download your unsaved text before reloading."
      : "Save unavailable. Check your sign-in and answers, then retry. Your text remains in this tab."};
  }
}
