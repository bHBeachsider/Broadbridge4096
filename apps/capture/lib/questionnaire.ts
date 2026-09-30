import { z } from "zod";
import content from "./pressure-questionnaire.json";

export const questionnaire = content;
export const questionnairePath = "/questionnaires/pressure-training-v1";
export const verdicts = [["supported", "Supported as written"], ["revise", "Needs correction or qualification"], ["contradicted", "Contradicted / wrong"], ["insufficient_evidence", "Insufficient evidence to judge"], ["outside_expertise", "Outside my expertise"]] as const;
export const inclusions = [["include", "Include this task"], ["revise", "Include after changes"], ["exclude", "Leave this task out"], ["unsure", "Unsure"]] as const;
export const criticalOptions = [["yes", "Yes — potentially serious"], ["no", "No — ordinary correction"], ["context_needed", "Depends on the context"], ["unsure", "Unsure"]] as const;
export const importance = [["essential", "Essential"], ["useful", "Useful, not mandatory"], ["revise", "Revise this check"], ["unsure", "Unsure"]] as const;
const text = z.string().max(8000);
const answerSchema = z.object({
  answer: text.optional(), expectation: text.optional(), correction: text.optional(),
  verdict: z.enum(["", ...verdicts.map(v => v[0])]).optional(),
  include: z.enum(["", ...inclusions.map(v => v[0])]).optional(),
  critical: z.enum(["", ...criticalOptions.map(v => v[0])]).optional(),
  requirement0: z.enum(["", ...importance.map(v => v[0])]).optional(),
  requirement1: z.enum(["", ...importance.map(v => v[0])]).optional(),
  requirement2: z.enum(["", ...importance.map(v => v[0])]).optional(),
  reference_seen_at: z.iso.datetime().optional(),
}).strict();
export type Answer = z.infer<typeof answerSchema>;
export const responseSchema = z.object({
  schema: z.literal("broadbridge.training_questionnaire_response/1"),
  questionnaire_id: z.literal("pressure-training-v1"), questionnaire_version: z.literal(1),
  questionnaire_sha256: z.string().regex(/^[0-9a-f]{64}$/),
  state: z.enum(["draft", "submitted"]), training_approved: z.literal(false),
  answers: z.record(z.string(), answerSchema),
}).strict().superRefine((record, ctx) => {
  if (new TextEncoder().encode(JSON.stringify(record)).length > 256 * 1024) ctx.addIssue({code: "custom", message: "Response exceeds 256 KB"});
  for (const [id, answer] of Object.entries(record.answers)) {
    const question = questionnaire.questions.find(q => q.id === id);
    const invalid = !question || (question.kind === "open" ? Object.keys(answer).some(k => k !== "answer") : "answer" in answer);
    if (invalid) ctx.addIssue({code: "custom", message: "Unknown question or incompatible answer fields"});
  }
  if (record.state === "submitted" && !Object.values(record.answers).some(answered)) ctx.addIssue({code: "custom", message: "Add a response before submitting"});
});
export function answered(answer: Answer) { return Object.entries(answer).some(([k, v]) => k !== "reference_seen_at" && typeof v === "string" && v.trim().length > 0); }
export type QuestionnaireResponse = z.infer<typeof responseSchema>;
export type SavedQuestionnaire = { record: QuestionnaireResponse; reviewer: string; revision: number; saved_at: string };
export const saveInputSchema = z.object({record: responseSchema, expected_revision: z.number().int().positive().nullable()}).strict();
export function emptyResponse(hash: string): QuestionnaireResponse {
  return {schema: "broadbridge.training_questionnaire_response/1", questionnaire_id: "pressure-training-v1", questionnaire_version: 1, questionnaire_sha256: hash, state: "draft", training_approved: false, answers: {}};
}
