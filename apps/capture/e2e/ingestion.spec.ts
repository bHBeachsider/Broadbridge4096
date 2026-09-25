import { readFile, writeFile } from "node:fs/promises";
import { test, expect } from "@playwright/test";
import { neon, neonConfig } from "@neondatabase/serverless";

test("real magic-link intake → immutable upload → CPU evidence → separate rights review", async ({ page, browser }) => {
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
  await page.getByLabel("Theme", { exact: true }).selectOption("light");
  await page.screenshot({ path: "test-results/ingestion-light.png", fullPage: true });
  await page.getByLabel("Theme", { exact: true }).selectOption("dark");
  await page.screenshot({ path: "test-results/ingestion-dark.png", fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({ path: "test-results/ingestion-mobile.png", fullPage: true });
  const anonymous = await browser.newContext();
  try { const other = await anonymous.newPage(); await other.goto(`${process.env.AUTH_URL}/ingestion`); await expect(other.getByRole("heading", { name: "Sign in to capture." })).toBeVisible(); } finally { await anonymous.close(); }
  await writeFile("test-results/ingestion-smoke-summary.json", JSON.stringify({ synthetic_sources: 2, real_auth: true, pending_default: true, cpu_preview: true, stale_review_rejected: true, actor_verified: true, local_only: true }, null, 2));
});
