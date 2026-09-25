import { readFile, writeFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";
import { resolve, join } from "node:path";
import { test, expect } from "@playwright/test";
import { neon, neonConfig } from "@neondatabase/serverless";

test("real magic-link intake → CPU evidence → separate reviews → immutable dataset", async ({ page, browser }) => {
  const connection = process.env.BROADBRIDGE_DATABASE_URL;
  const endpoint = process.env.CAPTURE_TEST_SQL_ENDPOINT;
  const outbox = process.env.CAPTURE_TEST_OUTBOX;
  const email = process.env.CAPTURE_TEST_EMAIL;
  if (process.env.CAPTURE_LOCAL_INGESTION_TEST !== "1" || !connection || !endpoint || !outbox || !email) throw new Error("Configure disposable local ingestion services and real Auth.js test outbox first.");
  const db = new URL(connection);
  if (!["localhost", "127.0.0.1"].includes(db.hostname) || !db.pathname.startsWith("/broadbridge_test") || new URL(endpoint).hostname !== "127.0.0.1" || new URL(endpoint).protocol !== "http:") throw new Error("Only a disposable loopback PostgreSQL target is allowed.");
  for (const value of [process.env.AUTH_URL, process.env.R2_ENDPOINT, process.env.INGESTION_API_URL]) if (!value || new URL(value).hostname !== "127.0.0.1") throw new Error("Every ingestion test service must use loopback.");
  neonConfig.fetchEndpoint = () => endpoint;
  const sql = neon(connection);
  await page.goto("/ingestion");
  await page.getByLabel("Email address", { exact: true }).fill(email);
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  await expect(page.getByRole("heading", { name: "Check your email." })).toBeVisible();
  let magicLink = "";
  await expect.poll(async () => {
    try { magicLink = (await readFile(outbox, "utf8")).trim().split("\n").map(line => JSON.parse(line)).findLast(item => item.email === email)?.url ?? ""; return Boolean(magicLink); } catch { return false; }
  }).toBe(true);
  await page.goto(magicLink);
  await page.goto("/ingestion");
  await expect(page.getByRole("heading", { name: "Source intake & review" })).toBeVisible();
  const marker = `synthetic-${Date.now()}`;
  await page.getByLabel("Source files", { exact: true }).setInputFiles([
    { name: `${marker}.txt`, mimeType: "text/plain", buffer: Buffer.from("Synthetic pump inspection. Measured inlet pressure: 3 bar absolute. No operational advice.") },
    { name: `${marker}.csv`, mimeType: "text/csv", buffer: Buffer.from("equipment,pressure,basis\npump,3,bar absolute\n") },
  ]);
  await page.getByRole("combobox", { name: "Confidentiality", exact: true }).selectOption("internal");
  await page.getByRole("button", { name: "Upload selected files" }).click();
  await expect(page.getByText("Queued for CPU verification", { exact: false })).toHaveCount(2);
  await expect.poll(async () => {
    const rows = await sql`SELECT count(*)::int AS n FROM broadbridge.source_revisions WHERE source_record->>'original_filename' LIKE ${marker + "%"}`;
    return rows[0].n;
  }).toBe(2);
  const records = await sql`SELECT source_id, revision_id, content_sha256, source_record, created_by FROM broadbridge.source_revisions WHERE source_record->>'original_filename' LIKE ${marker + "%"} ORDER BY source_record->>'original_filename'`;
  for (const record of records) {
    expect(record.created_by).toBe(email);
    expect(record.source_record.permission).toMatchObject({ status: "pending", permitted_use: "reference_only" });
    expect(record.source_record.object_key).toMatch(/^incoming\/broadbridge-oil-gas\//);
  }
  expect(records[0].source_record.object_key).not.toBe(records[1].source_record.object_key);
  // The local harness runs the real CPU worker; refresh until its committed result is visible.
  await expect.poll(async () => {
    await page.getByRole("button", { name: "Refresh status", exact: true }).click();
    return page.getByText(/^Extraction (complete|partial|unsupported)/).count();
  }, { timeout: 60000 }).toBeGreaterThanOrEqual(2);
  const card = page.getByRole("article").filter({ has: page.getByRole("heading", { name: `${marker}.txt`, exact: true }) });
  await card.getByRole("button", { name: "Review source" }).click();
  const review = page.getByRole("complementary", { name: "Source review" });
  await expect(review.getByText("Synthetic pump inspection.", { exact: false })).toBeVisible();
  await expect(review.getByText("No candidate messages are available for this revision.")).toBeVisible();
  const stale = await page.context().newPage();
  await stale.goto("/ingestion");
  await stale.getByRole("article").filter({ has: stale.getByRole("heading", { name: `${marker}.txt`, exact: true }) }).getByRole("button", { name: "Review source" }).click();
  await review.getByLabel("Permitted use", { exact: true }).selectOption("training");
  await review.getByLabel("Rights basis / revocation reason").fill("Synthetic document created for isolated acceptance testing.");
  await review.getByRole("button", { name: "Approve source rights" }).click();
  await expect(page.getByText("Rights decision recorded for this revision.")).toBeVisible();
  await stale.getByLabel("Rights basis / revocation reason").fill("Stale tab must not replace a newer review.");
  await stale.getByRole("button", { name: "Approve source rights" }).click();
  await expect(stale.getByText("This source or review changed. Refresh and review the current version before saving.")).toBeVisible();
  await stale.close();
  const textRecord = records.find(record => record.source_record.original_filename.endsWith(".txt"))!;
  const status = await sql`SELECT current_permission_status,current_permitted_use,rights_reviewed_by FROM broadbridge.ingestion_source_status WHERE source_id=${textRecord.source_id}`;
  expect(status[0]).toMatchObject({ current_permission_status: "approved", current_permitted_use: "training", rights_reviewed_by: email });
  // Authored synthetic target only: the bridge, reviews and release builder are
  // real; no LLM or GPU process runs in this acceptance path.
  const foundry = process.env.CAPTURE_TEST_FOUNDRY;
  const python = process.env.CAPTURE_TEST_PYTHON;
  const objects = process.env.CAPTURE_TEST_OBJECT_ROOT;
  const runRoot = process.env.CAPTURE_TEST_RUN_ROOT;
  if (!foundry || !python || !objects || !runRoot) throw new Error("Owned harness paths are required for release verification.");
  const jobs = await sql`SELECT result_json::jsonb AS result FROM broadbridge.ingestion_jobs WHERE source_json::jsonb->>'source_id'=${textRecord.source_id} AND state='succeeded'`;
  expect(jobs).toHaveLength(1);
  const document = JSON.parse(await readFile(join(objects, jobs[0].result.normalized.key), "utf8"));
  const exampleId = `example-${textRecord.source_id}`;
  const inputPath = join(runRoot, "candidate.json");
  await writeFile(inputPath, JSON.stringify({
    schema: "foundry.training_example/1", example_id: exampleId,
    family_id: textRecord.source_record.family_id, split: "train", task_type: "grounded_explanation",
    source_refs: [{ source_id: textRecord.source_id, revision_id: textRecord.revision_id,
      content_sha256: textRecord.content_sha256, block_ids: document.blocks.map((block: { block_id: string }) => block.block_id) }],
    messages: [{ role: "user", content: "What inlet pressure was recorded in the synthetic inspection?" },
      { role: "assistant", content: "The recorded inlet pressure was 3 bar absolute." }],
    review: { status: "pending", reviewer: null, reviewed_at: null, reason: "Authored synthetic acceptance fixture; no model output." }, quality_flags: [],
  }));
  const pack = resolve("../../packs/oil-gas");
  const bridge = (args: string[]) => execFileSync(python, [join(pack, "scripts/ingestion_release.py"), "--foundry", foundry,
    "--pack", pack, "--local-object-root", objects, ...args], { env: process.env, timeout: 60000, stdio: "pipe" });
  const registeredPath = join(runRoot, "registered.json");
  bridge(["register-candidates", "--input", inputPath, "--actor", email, "--output", registeredPath]);
  const registered = JSON.parse(await readFile(registeredPath, "utf8"));
  expect(registered.registered).toHaveLength(1);
  const candidateHash = registered.registered[0].candidate_hash;
  const preparedPath = join(runRoot, "prepared.json");
  expect(() => bridge(["prepare-release", "--output", preparedPath])).toThrow();
  await page.reload();
  await page.getByRole("article").filter({ has: page.getByRole("heading", { name: `${marker}.txt`, exact: true }) }).getByRole("button", { name: "Review source" }).click();
  await expect(review.getByRole("heading", { name: exampleId, exact: true })).toBeVisible();
  await review.getByLabel("Technical review reason", { exact: true }).fill("Synthetic target checked against the displayed 3 bar absolute evidence.");
  await review.getByRole("button", { name: "Accept candidate", exact: true }).click();
  await expect(page.getByText("Technical review recorded.", { exact: true })).toBeVisible();
  const reviews = await sql`SELECT status,reviewed_by FROM broadbridge.current_candidate_reviews WHERE example_id=${exampleId} AND candidate_hash=${candidateHash}`;
  expect(reviews[0]).toMatchObject({ status: "approved", reviewed_by: email });
  bridge(["prepare-release", "--output", preparedPath]);
  const prepared = JSON.parse(await readFile(preparedPath, "utf8"));
  const approvalPath = join(runRoot, "approval.json");
  await writeFile(approvalPath, JSON.stringify({ status: "approved", reviewer: email, reviewed_at: new Date().toISOString(), candidate_content_hash: prepared.candidate_content_hash }));
  const manifestPath = join(runRoot, "release.json");
  const buildArgs = ["build-release", "--approval", approvalPath, "--release-root", join(runRoot, "releases"), "--actor", email, "--output", manifestPath];
  bridge(buildArgs);
  bridge(buildArgs); // Idempotent immutable publication and natural-key DB reference.
  const manifest = JSON.parse(await readFile(manifestPath, "utf8"));
  expect(manifest.release_id).toBe(prepared.candidate_content_hash);
  expect(manifest.artifacts.train.row_count).toBe(1);
  const releases = await sql`SELECT release_id,approved_by FROM broadbridge.dataset_releases`;
  expect(releases).toEqual([{ release_id: manifest.release_id, approved_by: email }]);
  await page.getByLabel("Theme", { exact: true }).selectOption("light");
  await page.screenshot({ path: "test-results/ingestion-light.png", fullPage: true });
  await page.getByLabel("Theme", { exact: true }).selectOption("dark");
  await page.screenshot({ path: "test-results/ingestion-dark.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: "test-results/ingestion-mobile.png", fullPage: true });
  const anonymous = await browser.newContext();
  try { const other = await anonymous.newPage(); await other.goto(`${process.env.AUTH_URL}/ingestion`); await expect(other.getByRole("heading", { name: "Sign in to capture." })).toBeVisible(); } finally { await anonymous.close(); }
  await writeFile("test-results/ingestion-smoke-summary.json", JSON.stringify({ synthetic_sources: 2, real_auth: true, pending_default: true, cpu_preview: true, stale_review_rejected: true, actor_verified: true, pending_candidate_blocked: true, exact_hash_technical_review: true, immutable_dataset_recorded: true, idempotent_release: true, local_only: true, live_model: "not_run" }, null, 2));
});
