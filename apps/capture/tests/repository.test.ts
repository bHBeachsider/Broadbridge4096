import { randomUUID } from "node:crypto";
import { afterEach, describe, expect, it, vi } from "vitest";
import fixture from "../../../packs/oil-gas/tests/fixtures/SYN-TRAIN-001.json";
import { parseCase } from "../lib/validation";
vi.mock("server-only", () => ({}));
import { getSql } from "../lib/db";
import { persistCase, persistWorkflow, removeCase } from "../lib/repository";

const enabled = Boolean(process.env.BROADBRIDGE_DATABASE_URL && process.env.CAPTURE_DB_TEST_HOST);
const cases = new Set<string>();
const workflows = new Set<string>();
function verifyTarget() {
  const target = new URL(process.env.BROADBRIDGE_DATABASE_URL!);
  if (target.hostname !== process.env.CAPTURE_DB_TEST_HOST) throw new Error("Verify a dedicated development branch before running database tests.");
}
function sample(family?: string) {
  const record = parseCase(structuredClone(fixture));
  record.case_id = `TEST-${randomUUID()}`;
  record.family_id = family ?? record.case_id;
  record.questions = record.questions.map((question, i) => ({ ...question, question_id: `${record.case_id}-Q${i + 1}` }));
  cases.add(record.case_id);
  return record;
}
afterEach(async () => {
  if (!enabled) return;
  verifyTarget();
  const sql = getSql();
  for (const id of cases) {
    const rows = await sql`SELECT updated_at::text AS revision FROM broadbridge.cases WHERE case_id=${id}`;
    if (rows.length) await removeCase(id, "test-cleanup@example.invalid", rows[0].revision as string);
  }
  for (const author of workflows) await sql`DELETE FROM broadbridge.workflow WHERE author_email=${author}`;
  cases.clear(); workflows.clear();
});

describe.skipIf(!enabled)("shared SQL upserts on a verified Neon development branch", () => {
  it("round trips canonical fields, stamps the actor, rejects stale and blind overwrites", async () => {
    verifyTarget();
    const record = sample();
    const first = await persistCase(record, "reviewer@example.invalid", null);
    expect(first.record).toEqual(record);
    expect(await persistCase(record, "reviewer@example.invalid", first.revision)).toEqual(first);
    await expect(persistCase(record, "other@example.invalid", null)).rejects.toMatchObject({ code: "40001" });
    const revised = { ...record, status: "draft" as const, reviewer_signoff: { ...record.reviewer_signoff, signed: false } };
    const next = await persistCase(revised, "editor@example.invalid", first.revision);
    expect(next.revision).not.toEqual(first.revision);
    await expect(persistCase(revised, "stale@example.invalid", first.revision)).rejects.toMatchObject({ code: "40001" });
    const sql = getSql();
    const rows = await sql`SELECT updated_by FROM broadbridge.cases WHERE case_id=${record.case_id}`;
    expect(rows[0].updated_by).toBe("editor@example.invalid");
    const log = await sql`SELECT actor FROM broadbridge.review_log WHERE case_id=${record.case_id} ORDER BY review_id DESC LIMIT 1`;
    expect(log[0].actor).toBe("editor@example.invalid");
  });
  it("projects every question and enforces the family-wide holdout", async () => {
    verifyTarget();
    const first = sample(); const held = sample(first.family_id);
    held.questions[0].split = "locked_test";
    await persistCase(first, "reviewer@example.invalid", null);
    await persistCase(held, "reviewer@example.invalid", null);
    const sql = getSql();
    const questions = await sql`SELECT q.effective_split FROM broadbridge.questions q JOIN broadbridge.cases c USING(case_id) WHERE c.family_id=${first.family_id}`;
    expect(questions).toHaveLength(2);
    expect(questions.every(row => row.effective_split === "locked_test")).toBe(true);
    expect(await sql`SELECT * FROM broadbridge.train_candidates WHERE family_id=${first.family_id}`).toHaveLength(0);
  });
  it("keeps one workflow per author and protects its revision", async () => {
    verifyTarget();
    const author = `test-${randomUUID()}@example.invalid`; workflows.add(author);
    const record = { schema: "broadbridge.workflow/1" as const, answers: { A1: "test workflow" }, updated_at: "" };
    const first = await persistWorkflow(record, author, null);
    expect(first.record).toEqual(record);
    await expect(persistWorkflow(record, author, null)).rejects.toMatchObject({ code: "40001" });
    const updated = await persistWorkflow({ ...record, answers: { A1: "updated workflow" } }, author, first.revision);
    expect(updated.record.answers.A1).toBe("updated workflow");
  });
  it("refuses malformed hard-fail criteria through the shared SQL boundary", async () => {
    verifyTarget();
    const record = sample();
    Object.assign(record.questions[0], { hard_fail_criteria: [] });
    await expect(persistCase(record, "reviewer@example.invalid", null)).rejects.toMatchObject({ code: "23514" });
  });
});
