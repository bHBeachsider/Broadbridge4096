import { beforeEach, describe, expect, it, vi } from "vitest";
import seed from "../../../packs/oil-gas/tests/fixtures/SYN-001.json";
const mocks = vi.hoisted(() => ({ actor: vi.fn(), save: vi.fn(), workflow: vi.fn(), remove: vi.fn() }));
vi.mock("../auth", () => ({ requireActor: mocks.actor }));
vi.mock("../lib/repository", () => ({ persistCase: mocks.save, persistWorkflow: mocks.workflow, removeCase: mocks.remove }));
import { saveCaseAction, saveWorkflowAction, deleteCaseAction } from "../app/actions";

beforeEach(() => {
  vi.resetAllMocks();
  mocks.actor.mockResolvedValue("signed-in@example.invalid");
  mocks.save.mockImplementation(record => Promise.resolve({ record, revision: "saved" }));
  mocks.workflow.mockImplementation(record => Promise.resolve({ record, revision: "saved" }));
});

describe("protected server action boundaries", () => {
  it("uses the signed-in actor and the supplied revision", async () => {
    const result = await saveCaseAction(seed, "prior");
    expect(result.ok).toBe(true);
    expect(mocks.save).toHaveBeenCalledWith(expect.objectContaining({ case_id: seed.case_id }), "signed-in@example.invalid", "prior");
  });
  it("refuses an actor field in browser-submitted JSON", async () => {
    expect((await saveCaseAction({ ...seed, updated_by: "forged@example.invalid" }, null)).ok).toBe(false);
    expect(mocks.save).not.toHaveBeenCalled();
  });
  it("refuses unauthenticated or revoked sessions before any write", async () => {
    mocks.actor.mockRejectedValue(new Error("Access denied"));
    expect((await saveCaseAction(seed, null)).ok).toBe(false);
    expect((await saveWorkflowAction({}, null)).ok).toBe(false);
    expect((await deleteCaseAction(seed.case_id, "revision")).ok).toBe(false);
    expect(mocks.save).not.toHaveBeenCalled();
    expect(mocks.workflow).not.toHaveBeenCalled();
    expect(mocks.remove).not.toHaveBeenCalled();
  });
  it("rejects oversized records before SQL", async () => {
    expect((await saveCaseAction({ ...seed, identity: { ...seed.identity, title: "x".repeat(256 * 1024) } }, null)).ok).toBe(false);
    expect(mocks.save).not.toHaveBeenCalled();
  });
  it("reports conflicts without leaking SQL or credentials", async () => {
    mocks.save.mockRejectedValue(Object.assign(new Error("private SQL and credentials"), { code: "40001" }));
    const result = await saveCaseAction(seed, "stale");
    expect(result).toMatchObject({ ok: false, conflict: true });
    expect(JSON.stringify(result)).not.toContain("credentials");
  });
  it("sanitizes unexpected database errors", async () => {
    mocks.save.mockRejectedValue(new Error("secret connection details"));
    const result = await saveCaseAction(seed, null);
    expect(result.ok).toBe(false);
    expect(JSON.stringify(result)).not.toContain("secret");
  });
});
