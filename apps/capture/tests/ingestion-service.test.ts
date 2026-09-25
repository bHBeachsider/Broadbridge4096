import { beforeEach, describe, expect, it, vi } from "vitest";
import { createHash } from "node:crypto";
vi.mock("server-only", () => ({}));
const mock = vi.hoisted(() => ({ registerSource: vi.fn(), findSource: vi.fn(), findJob: vi.fn(), listCandidates: vi.fn(), signUpload: vi.fn(), verifyUpload: vi.fn(), readVerifiedDocument: vi.fn(), local: vi.fn() }));
vi.mock("../lib/ingestion-repository", () => mock);
vi.mock("../lib/ingestion-storage", () => mock);
vi.mock("../lib/db", () => ({ localIngestionTestEnabled: mock.local }));
import { prepareUpload, completeUpload, retryJob, engineRequest } from "../lib/ingestion-service";
const metadata = { original_filename: "synthetic.txt", size_bytes: 8, media_type: "text/plain", content_sha256: "a".repeat(64), confidentiality: "internal" };
const identity = { source_id: "source1", revision_id: "r1", content_sha256: metadata.content_sha256 };
beforeEach(() => { vi.resetAllMocks(); vi.stubEnv("INGESTION_API_URL","https://engine.example.invalid"); vi.stubEnv("INGESTION_API_TOKEN","private-token"); mock.signUpload.mockResolvedValue({ url: "private-signed-url", headers: {} }); mock.local.mockReturnValue(false); });
describe("durable intake orchestration", () => {
  it("records pending rights and a unique server-generated scope before signing", async () => {
    await prepareUpload(metadata, "session@example.invalid");
    const [source, ref, actor] = mock.registerSource.mock.calls[0];
    expect(source).toMatchObject({ project_id:"broadbridge-oil-gas", revision_id:"r1", permission:{status:"pending",permitted_use:"reference_only",reviewed_by:null} });
    expect(ref).toBe(`registry/broadbridge-oil-gas/${createHash("sha256").update(JSON.stringify(source.object_key)).digest("hex")}.json`);
    expect(actor).toBe("session@example.invalid");
    expect(mock.registerSource.mock.invocationCallOrder[0]).toBeLessThan(mock.signUpload.mock.invocationCallOrder[0]);
  });
  it("never issues an upload URL after SQL failure", async () => { mock.registerSource.mockRejectedValue(new Error("SQL failed")); await expect(prepareUpload(metadata,"actor")).rejects.toThrow(); expect(mock.signUpload).not.toHaveBeenCalled(); });
  it("rejects oversize before any registration", async () => { await expect(prepareUpload({...metadata,size_bytes:50*1024*1024+1},"actor")).rejects.toThrow(); expect(mock.registerSource).not.toHaveBeenCalled(); });
  it("does not register or enqueue when HEAD verification fails", async () => { mock.findSource.mockResolvedValue({ source:{},sourceRef:"registry" }); mock.verifyUpload.mockRejectedValue(new Error("mismatch")); const fetcher = vi.fn(); vi.stubGlobal("fetch",fetcher); await expect(completeUpload(identity)).rejects.toThrow(); expect(fetcher).not.toHaveBeenCalled(); });
  it("replays registration and enqueue using only stored identity after interrupted queueing", async () => {
    const source = { ...identity, object_key:"incoming/broadbridge-oil-gas/s/original" }; const sourceRef = "registry/broadbridge-oil-gas/" + "c".repeat(64) + ".json";
    mock.findSource.mockResolvedValue({ source,sourceRef });
    const fetcher = vi.fn().mockResolvedValueOnce(new Response(JSON.stringify({source_ref:sourceRef,object_key:source.object_key}))).mockResolvedValueOnce(new Response("{}",{status:503})).mockResolvedValueOnce(new Response(JSON.stringify({source_ref:sourceRef,object_key:source.object_key}))).mockResolvedValueOnce(new Response(JSON.stringify({job_id:"d".repeat(64),state:"queued"})));
    vi.stubGlobal("fetch",fetcher); await expect(completeUpload(identity)).rejects.toThrow(); expect((await completeUpload(identity)).state).toBe("queued"); expect(JSON.parse(fetcher.mock.calls[3][1].body)).toEqual({source_ref:sourceRef});
  });
  it("binds retry to the stored source before contacting the engine", async () => { mock.findJob.mockRejectedValue(new Error("wrong project")); const fetcher = vi.fn(); vi.stubGlobal("fetch",fetcher); await expect(retryJob(identity,"b".repeat(64))).rejects.toThrow(); expect(fetcher).not.toHaveBeenCalled(); });
  it.each(["http://engine.example", "https://u:p@engine.example", "https://engine.example?token=secret", "https://engine.example/path"])("rejects unsafe API endpoint %s", async endpoint => { vi.stubEnv("INGESTION_API_URL",endpoint); await expect(engineRequest("/v1/jobs",{})).rejects.toThrow(); });
});
