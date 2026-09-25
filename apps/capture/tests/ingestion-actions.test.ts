import { beforeEach, describe, expect, it, vi } from "vitest";
const mocks = vi.hoisted(() => ({ actor: vi.fn(), prepareUpload: vi.fn(), resumeUpload: vi.fn(), completeUpload: vi.fn(), previewSource: vi.fn(), retryJob: vi.fn(), listSources: vi.fn(), saveRights: vi.fn(), saveCandidateReview: vi.fn() }));
vi.mock("../auth", () => ({ requireActor: mocks.actor }));
vi.mock("../lib/ingestion-service", () => mocks);
vi.mock("../lib/ingestion-repository", () => mocks);
import * as actions from "../app/ingestion/actions";
const identity = { source_id: "s1", revision_id: "r1", content_sha256: "a".repeat(64) };
const rights = { ...identity, decision: "approved", permitted_use: "training", rights_basis: "Owner consent", expected_review_id: null };
beforeEach(() => { vi.resetAllMocks(); mocks.actor.mockResolvedValue("session@example.invalid"); });
describe("ingestion authenticated actions", () => {
  it("checks every exported action before touching a dependency", async () => {
    mocks.actor.mockRejectedValue(new Error("revoked"));
    for (const action of Object.values(actions)) expect((await (action as (...a: unknown[]) => Promise<{ok:boolean}>)(identity, "b".repeat(64))).ok).toBe(false);
    for (const [key, fn] of Object.entries(mocks)) if (key !== "actor") expect(fn).not.toHaveBeenCalled();
  });
  it("records session actor and rejects forged authority", async () => {
    expect((await actions.reviewRightsAction(rights)).ok).toBe(true);
    expect(mocks.saveRights).toHaveBeenCalledWith(rights, "session@example.invalid");
    expect((await actions.reviewRightsAction({ ...rights, actor: "fake" })).ok).toBe(false);
  });
  it("rejects arbitrary keys on completion", async () => {
    expect((await actions.completeUploadAction({ ...identity, object_key: "incoming/other" })).ok).toBe(false);
    expect(mocks.completeUpload).not.toHaveBeenCalled();
  });
  it("shows stale review conflicts and sanitizes provider details", async () => {
    mocks.saveRights.mockRejectedValue(Object.assign(new Error("secret SQL"), { code: "40001" }));
    expect(await actions.reviewRightsAction(rights)).toMatchObject({ ok: false, conflict: true });
    mocks.completeUpload.mockRejectedValue(new Error("signed URL secret"));
    const response = await actions.completeUploadAction(identity);
    expect(response.ok).toBe(false); expect(JSON.stringify(response)).not.toContain("secret");
  });
});
