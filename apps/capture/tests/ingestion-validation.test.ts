import { describe, expect, it } from "vitest";
import { uploadSchema, identitySchema, rightsSchema, MAX_UPLOAD_BYTES } from "../lib/ingestion-validation";
const upload = { original_filename: "report.pdf", media_type: "application/pdf", size_bytes: 12, content_sha256: "a".repeat(64), confidentiality: "internal" };
describe("intake boundary", () => {
  it("accepts mixed media metadata with a strict 50 MiB ceiling", () => {
    expect(uploadSchema.parse({ ...upload, size_bytes: MAX_UPLOAD_BYTES })).toBeTruthy();
    expect(uploadSchema.safeParse({ ...upload, size_bytes: MAX_UPLOAD_BYTES + 1 }).success).toBe(false);
  });
  it.each(["../report.pdf", "folder/report.pdf", "a\\b.pdf", "a\n.pdf", "..", ""]) ("rejects unsafe filename %s", original_filename => {
    expect(uploadSchema.safeParse({ ...upload, original_filename }).success).toBe(false);
  });
  it("rejects client authority and malformed metadata", () => {
    for (const extra of [{ actor: "forged" }, { object_key: "other/project" }, { permission: "approved" }]) expect(uploadSchema.safeParse({ ...upload, ...extra }).success).toBe(false);
    expect(uploadSchema.safeParse({ ...upload, content_sha256: "wrong" }).success).toBe(false);
    expect(uploadSchema.safeParse({ ...upload, media_type: "text/plain\r\nX: injected" }).success).toBe(false);
  });
  it("binds rights to exact identity and previous review", () => {
    const identity = { source_id: "s1", revision_id: "r1", content_sha256: "a".repeat(64) };
    expect(identitySchema.safeParse({ ...identity, object_key: "incoming/other" }).success).toBe(false);
    expect(rightsSchema.safeParse({ ...identity, decision: "approved", permitted_use: "training", rights_basis: "", expected_review_id: null }).success).toBe(false);
  });
});
