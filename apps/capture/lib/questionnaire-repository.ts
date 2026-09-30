import "server-only";
import { createHash } from "node:crypto";
import { getSql } from "./db";
import { questionnaire, responseSchema, type QuestionnaireResponse, type SavedQuestionnaire } from "./questionnaire";

export const questionnaireHash = createHash("sha256").update(JSON.stringify(questionnaire)).digest("hex");
export async function loadQuestionnaire(actor: string): Promise<SavedQuestionnaire | null> {
  const sql = getSql();
  const packets = await sql`SELECT packet_sha256 FROM broadbridge.questionnaire_packets WHERE questionnaire_id=${questionnaire.id} AND version=${questionnaire.version}`;
  if (packets[0]?.packet_sha256 !== questionnaireHash) throw new Error("Questionnaire unavailable");
  const rows = await sql`SELECT record, reviewer, revision, saved_at::text FROM broadbridge.current_questionnaire_responses
    WHERE questionnaire_id=${questionnaire.id} AND version=${questionnaire.version} AND reviewer=${actor}`;
  if (!rows.length) return null;
  return {...rows[0], record: responseSchema.parse(rows[0].record)} as SavedQuestionnaire;
}
export async function persistQuestionnaire(record: QuestionnaireResponse, actor: string, expected: number | null): Promise<SavedQuestionnaire> {
  const parsed = responseSchema.parse(record);
  if (parsed.questionnaire_sha256 !== questionnaireHash) throw new Error("Questionnaire changed");
  const rows = await getSql()`SELECT broadbridge.save_questionnaire_response(${JSON.stringify(parsed)}::jsonb, ${actor}, ${expected}::integer) AS saved`;
  return rows[0].saved as SavedQuestionnaire;
}
