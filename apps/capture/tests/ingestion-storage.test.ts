import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
import { createHash } from "node:crypto";
vi.mock("server-only", () => ({}));
const mock = vi.hoisted(() => ({ send:vi.fn(), sign:vi.fn(), local:vi.fn() }));
vi.mock("@aws-sdk/client-s3", () => ({ S3Client: class { send = mock.send; }, PutObjectCommand: class { constructor(public input: unknown) {} }, HeadObjectCommand: class { constructor(public input: unknown) {} }, GetObjectCommand: class { constructor(public input: unknown) {} } }));
vi.mock("@aws-sdk/s3-request-presigner", () => ({ getSignedUrl:mock.sign }));
vi.mock("../lib/db", () => ({ localIngestionTestEnabled:mock.local }));
import { storageConfig, signUpload, verifyUpload, readVerifiedDocument } from "../lib/ingestion-storage";
import type { Source } from "../lib/ingestion-validation";
const source = { source_id:"s1", revision_id:"r1", content_sha256:"a".repeat(64), object_key:"incoming/broadbridge-oil-gas/s1/original", media_type:"text/plain",size_bytes:12 } as Source;
beforeEach(() => { vi.resetAllMocks(); for(const [k,v] of Object.entries({R2_ENDPOINT:"https://r2.example.invalid",R2_BUCKET:"test-bucket",R2_ACCESS_KEY_ID:"synthetic",R2_SECRET_ACCESS_KEY:"synthetic"})) vi.stubEnv(k,v); });
afterEach(() => vi.unstubAllEnvs());
describe("private immutable storage", () => {
  it("requires explicit R2 credentials with no AWS fallback", () => { vi.stubEnv("R2_SECRET_ACCESS_KEY",""); vi.stubEnv("AWS_SECRET_ACCESS_KEY","ambient"); expect(() => storageConfig()).toThrow(); });
  it("signs the exact key, size, MIME, metadata and conditional write", async () => { await signUpload(source); const command = mock.sign.mock.calls[0][1]; expect(command.input).toMatchObject({Key:source.object_key,ContentLength:12,IfNoneMatch:"*",ContentType:"text/plain",Metadata:{sha256:source.content_sha256}}); expect(mock.sign.mock.calls[0][2].signableHeaders.has("if-none-match")).toBe(true); });
  it.each([{ContentLength:13},{ContentType:"application/pdf"},{Metadata:{sha256:"b".repeat(64)}}])("refuses mismatched HEAD %j",async mismatch => { mock.send.mockResolvedValue({ContentLength:12,ContentType:"text/plain",Metadata:{sha256:source.content_sha256,"source-id":"s1","revision-id":"r1"},...mismatch}); await expect(verifyUpload(source)).rejects.toThrow(); });
  it("only previews a stored job attempt artifact after validating its bytes",async () => { const job = "b".repeat(64); const data = Buffer.from('{"synthetic":true}'); const receipt = {key:`artifacts/broadbridge-oil-gas/${job}/${"c".repeat(32)}/normalized.json`,sha256:createHash("sha256").update(data).digest("hex"),size_bytes:data.length}; mock.send.mockResolvedValue({ContentLength:data.length,Body:(async function*(){yield data;})()}); expect(await readVerifiedDocument(receipt,job)).toEqual({synthetic:true}); await expect(readVerifiedDocument({...receipt,key:"incoming/other"},job)).rejects.toThrow(); });
});
it("rejects a large verified artifact receipt before downloading the body", async () => {
  await expect(readVerifiedDocument({key:`artifacts/broadbridge-oil-gas/${"b".repeat(64)}/${"c".repeat(32)}/normalized.json`,sha256:"a".repeat(64),size_bytes:5*1024*1024},"b".repeat(64))).rejects.toMatchObject({code:"PREVIEW_TOO_LARGE"});
  expect(mock.send).not.toHaveBeenCalled();
});
