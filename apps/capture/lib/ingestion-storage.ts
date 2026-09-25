import "server-only";
import { createHash } from "node:crypto";
import { S3Client, PutObjectCommand, HeadObjectCommand, GetObjectCommand } from "@aws-sdk/client-s3";
import { getSignedUrl } from "@aws-sdk/s3-request-presigner";
import { localIngestionTestEnabled } from "./db";
import { MAX_ACTION_BYTES, previewLimitError, type Source } from "./ingestion-validation";
export function storageConfig() {
  const { R2_ENDPOINT, R2_BUCKET, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY } = process.env;
  if (!R2_ENDPOINT || !R2_BUCKET || !R2_ACCESS_KEY_ID || !R2_SECRET_ACCESS_KEY) throw new Error("Storage configuration unavailable");
  const endpoint = new URL(R2_ENDPOINT);
  const local = localIngestionTestEnabled();
  if ((local ? !["http:", "https:"].includes(endpoint.protocol) : endpoint.protocol !== "https:") || endpoint.username || endpoint.password || endpoint.search || endpoint.hash || endpoint.pathname !== "/" || !/^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$/.test(R2_BUCKET)) throw new Error("Invalid storage configuration");
  return { bucket: R2_BUCKET, client: new S3Client({ endpoint: endpoint.origin, region: "auto", forcePathStyle: true, requestChecksumCalculation: "WHEN_REQUIRED", responseChecksumValidation: "WHEN_REQUIRED", credentials: { accessKeyId: R2_ACCESS_KEY_ID, secretAccessKey: R2_SECRET_ACCESS_KEY } }) };
}
export async function signUpload(source: Source) {
  const { client, bucket } = storageConfig();
  const headers = { "content-type": source.media_type, "if-none-match": "*", "x-amz-meta-sha256": source.content_sha256, "x-amz-meta-source-id": source.source_id, "x-amz-meta-revision-id": source.revision_id };
  const command = new PutObjectCommand({ Bucket: bucket, Key: source.object_key, ContentType: source.media_type, ContentLength: source.size_bytes, IfNoneMatch: "*", Metadata: { sha256: source.content_sha256, "source-id": source.source_id, "revision-id": source.revision_id } });
  const url = await getSignedUrl(client, command, { expiresIn: 300, signableHeaders: new Set(["content-type", "content-length", "if-none-match"]), unhoistableHeaders: new Set(["x-amz-meta-sha256", "x-amz-meta-source-id", "x-amz-meta-revision-id"]) });
  return { url, headers };
}
export async function verifyUpload(source: Source) {
  const { client, bucket } = storageConfig();
  const head = await client.send(new HeadObjectCommand({ Bucket: bucket, Key: source.object_key }));
  if (head.ContentLength !== source.size_bytes || head.ContentType !== source.media_type || head.Metadata?.sha256 !== source.content_sha256 || head.Metadata?.["source-id"] !== source.source_id || head.Metadata?.["revision-id"] !== source.revision_id) throw new Error("Uploaded object does not match the registered source");
  // HEAD verifies the receipt only. The CPU worker verifies the actual SHA-256 before parsing.
}
export async function readVerifiedDocument(receipt: { key: string; sha256: string; size_bytes: number }, jobId: string) {
  if (!new RegExp(`^artifacts/broadbridge-oil-gas/${jobId}/[a-f0-9]{32}/normalized\\.json$`).test(receipt.key) || !/^[a-f0-9]{64}$/.test(receipt.sha256) || !Number.isSafeInteger(receipt.size_bytes) || receipt.size_bytes < 0) throw new Error("Invalid preview receipt");
  if (receipt.size_bytes > MAX_ACTION_BYTES / 2 - 16384) throw previewLimitError();
  const { client, bucket } = storageConfig();
  const result = await client.send(new GetObjectCommand({ Bucket: bucket, Key: receipt.key }));
  if (result.ContentLength !== receipt.size_bytes || !result.Body) throw new Error("Artifact size mismatch");
  const chunks: Uint8Array[] = []; let size = 0;
  for await (const chunk of result.Body as AsyncIterable<Uint8Array>) { size += chunk.length; if (size > receipt.size_bytes) throw new Error("Artifact size mismatch"); chunks.push(chunk); }
  const bytes = Buffer.concat(chunks);
  if (bytes.length !== receipt.size_bytes || createHash("sha256").update(bytes).digest("hex") !== receipt.sha256) throw new Error("Artifact verification failed");
  return JSON.parse(bytes.toString("utf8")) as unknown;
}
