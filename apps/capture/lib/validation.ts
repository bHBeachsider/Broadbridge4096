import { z } from "zod";
import canonical from "../../../packs/oil-gas/schemas/case_record.schema.json";
import exportContract from "../../../packs/oil-gas/schemas/export.schema.json";

export const RECORD_LIMIT = 256 * 1024;
export type QuestionType = "brief" | "missing_data" | "calculation" | "grounded_explanation" | "abstention";
export type Split = "train" | "dev" | "locked_test";
export type Permission = "training" | "testing_only" | "reference_only";
export type Question = {
  question_id: string; type: QuestionType; question: string; evidence_ids: string;
  reference_answer: string; tolerance: string; hard_fail_criteria: string; split: Split;
};
export type CaseRecord = {
  schema: "broadbridge.case_record/1"; case_id: string; family_id: string;
  status: "draft" | "complete" | "signed";
  identity: { title: string; unit_service: string; period: string; record_type: "real_event" | "reconstructed" | "hypothetical"; confidentiality: string; permitted_use: Permission };
  decision_time: { b1_trigger: string; b2_operating_context: string; b3_initial_info_and_requests: string;
    observations: Array<{ time: string; variable_location: string; value_units_basis: string; source: string; quality: string }>;
    b5_initial_hypotheses: string; b6_distrusted_or_missing: string };
  hindsight: { hypotheses: Array<{ hypothesis: string; evidence_for: string; evidence_against: string; discriminator: string }>;
    b8_turning_point: string; b9_calculations: string; b10_actions_taken: string; b11_confidence: string; b12_dangerous_wrong_answer: string; b13_lesson_and_limits: string };
  evidence: Array<{ item: string; format: string; available_at_decision_time: string | boolean; restriction: string }>;
  questions: Question[]; reviewer_signoff: { signed: boolean; name: string; date: string };
  created_at: string; updated_at: string;
};
export type WorkflowRecord = { schema: "broadbridge.workflow/1"; answers: Partial<Record<`A${1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10}`, string>>; updated_at: string };
export type StoredCase = { record: CaseRecord; revision: string };
export type StoredWorkflow = { record: WorkflowRecord; revision: string };

// Zod consumes the same authoritative JSON Schema used by Python and SQL.
// These TypeScript types are compile-time conveniences, never a second validator.
const caseSchema = z.fromJSONSchema(canonical as Parameters<typeof z.fromJSONSchema>[0]);
const workflowSchema = z.fromJSONSchema(exportContract.properties.workflow as Parameters<typeof z.fromJSONSchema>[0]);

function checkSize(value: unknown) {
  const encoded = JSON.stringify(value);
  if (encoded === undefined || new TextEncoder().encode(encoded).byteLength > RECORD_LIMIT) {
    throw new Error("Record must be valid JSON and no larger than 256 KB.");
  }
}

export function parseCase(value: unknown): CaseRecord {
  checkSize(value);
  const record = caseSchema.parse(value) as CaseRecord;
  if (!/^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$/.test(record.case_id) || !record.family_id.trim()) {
    throw new Error("Case ID and family ID are required.");
  }
  if (record.status === "signed" && (!record.reviewer_signoff.signed || [record.reviewer_signoff.name, record.reviewer_signoff.date]
    .some(item => ["", "unknown", "undecided"].includes(item.trim().toLowerCase())))) {
    throw new Error("Signed cases need a checked sign-off, reviewer name and date.");
  }
  const questionIds = new Set<string>();
  for (const question of record.questions) {
    const id = question.question_id.trim().toLowerCase();
    if (!id || questionIds.has(id)) throw new Error("Every question needs a unique question ID.");
    questionIds.add(id);
  }
  return record;
}

export function parseWorkflow(value: unknown): WorkflowRecord {
  checkSize(value);
  return workflowSchema.parse(value) as WorkflowRecord;
}
