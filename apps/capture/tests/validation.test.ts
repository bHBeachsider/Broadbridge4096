import { describe, expect, it } from "vitest";
import seed from "../../../packs/oil-gas/tests/fixtures/SYN-001.json";
import signed from "../../../packs/oil-gas/tests/fixtures/SYN-TRAIN-001.json";
import { parseCase, parseWorkflow, RECORD_LIMIT } from "../lib/validation";

describe("canonical capture contract", () => {
  it("round trips the real page fixture and signed fixture exactly", () => {
    expect(parseCase(seed)).toEqual(seed);
    expect(parseCase(signed)).toEqual(signed);
  });
  it.each(["status", "record_type", "permitted_use", "type", "split", "hard_fail_criteria", "evidence_ids"])("rejects invalid %s", field => {
    const value = structuredClone(seed);
    if (field === "status") value.status = "approved";
    else if (field === "record_type" || field === "permitted_use") value.identity[field] = "undecided";
    else Object.assign(value.questions[0], { [field]: field.endsWith("criteria") || field === "evidence_ids" ? [] : "other" });
    expect(() => parseCase(value)).toThrow();
  });
  it("rejects extra fields and missing sections", () => {
    expect(() => parseCase({ ...seed, updated_by: "spoofed@example.invalid" })).toThrow();
    const { hindsight: _removed, ...value } = seed;
    expect(() => parseCase(value)).toThrow();
  });
  it("permits unknown narrative content and boolean evidence", () => {
    const value = { ...structuredClone(seed), evidence: [{ item: "Test observation", format: "text", restriction: "synthetic", available_at_decision_time: true }] };
    value.decision_time.b1_trigger = "unknown";
    expect(parseCase(value)).toEqual(value);
  });
  it("requires complete named and dated signoff for signed status", () => {
    for (const invalid of ["", "\t", "unknown", " undecided "]) {
      const value = structuredClone(signed);
      value.reviewer_signoff.name = invalid;
      expect(() => parseCase(value)).toThrow();
    }
  });
  it("enforces the 256 KB cap on UTF-8 bytes, not character count", () => {
    const value = structuredClone(seed);
    value.identity.title = "é".repeat(RECORD_LIMIT / 2);
    expect(() => parseCase(value)).toThrow(/256/);
  });
  it("rejects duplicate question IDs without changing case schema", () => {
    const value = structuredClone(seed);
    value.questions.push(structuredClone(value.questions[0]));
    expect(() => parseCase(value)).toThrow(/question/i);
  });
  it("preserves per-author Part A contract without actor fields", () => {
    const value = { schema: "broadbridge.workflow/1", answers: { A1: "unknown" }, updated_at: "" };
    expect(parseWorkflow(value)).toEqual(value);
    expect(() => parseWorkflow({ ...value, answers: { A11: "extra" } })).toThrow();
    expect(() => parseWorkflow({ ...value, author: "spoofed" })).toThrow();
  });
});
