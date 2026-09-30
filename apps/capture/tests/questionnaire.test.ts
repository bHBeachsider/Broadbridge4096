import { describe, expect, it } from "vitest";
import { answered, emptyResponse, questionnaire, responseSchema } from "../lib/questionnaire";
import { safeReviewReturn } from "../lib/public-review";
const base = () => emptyResponse("a".repeat(64));
describe("training questionnaire contract", () => {
  it("retains the 16 questions, eight examples and three pressure diagrams", () => {
    expect(questionnaire.questions).toHaveLength(16);
    expect(questionnaire.questions.filter(q => q.kind === "example")).toHaveLength(8);
    expect(questionnaire.questions.find(q => q.id === "DOE-DEMO-PROBE-02")?.graphic).toBe("negative_gauge");
    expect(responseSchema.parse(base()).training_approved).toBe(false);
  });
  it.each([{reviewer:"Bill"}, {training_approved:true}, {state:"signed"}, {questionnaire_version:2}, {questionnaire_sha256:"wrong"}])("rejects forged contract metadata %j", patch => {
    expect(responseSchema.safeParse({...base(), ...patch}).success).toBe(false);
  });
  it.each([
    {unknown:{answer:"text"}}, {"PRIORITY-01":{verdict:"supported"}}, {"PRIORITY-01":{answer:"x".repeat(8001)}},
    {"DOE-DEMO-PROBE-01":{answer:"40.6"}}, {"DOE-DEMO-PROBE-01":{verdict:"guaranteed"}},
    {"DOE-DEMO-PROBE-01":{reviewer:"Bill"}}, {"DOE-DEMO-PROBE-01":{reference_seen_at:"yesterday"}},
  ])("rejects unknown, oversized or incompatible answers %j", answers => expect(responseSchema.safeParse({...base(),answers}).success).toBe(false));
  it("keeps reveal-only records separate from actual responses", () => {
    expect(answered({reference_seen_at:"2026-09-30T12:00:00.000Z"})).toBe(false);
    expect(answered({answer:" "})).toBe(false);
    expect(answered({verdict:"insufficient_evidence"})).toBe(true);
    expect(responseSchema.safeParse({...base(),state:"submitted"}).success).toBe(false);
    expect(responseSchema.safeParse({...base(),state:"submitted",answers:{"PRIORITY-01":{answer:"Check pressure references"}}}).success).toBe(true);
  });
  it("preserves the exact questionnaire return path only", () => {
    expect(safeReviewReturn("/questionnaires/pressure-training-v1")).toBe("/questionnaires/pressure-training-v1");
    for (const path of ["//evil.invalid/questionnaires/pressure-training-v1", "/questionnaires/pressure-training-v1?next=//evil.invalid", "/questionnaires/../signin"]) expect(safeReviewReturn(path)).toBe("/");
  });
  it("enforces the aggregate UTF-8 response cap", () => {
    const answers = Object.fromEntries(questionnaire.questions.filter(q => q.kind === "example").map(q => [q.id,{expectation:"界".repeat(8000),correction:"界".repeat(8000)}]));
    expect(responseSchema.safeParse({...base(),answers}).success).toBe(false);
  });
});
