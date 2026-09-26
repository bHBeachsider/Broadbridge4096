import { readFile, writeFile } from "node:fs/promises";
import { test, expect } from "@playwright/test";
import { neon } from "@neondatabase/serverless";

test("real one-use magic link → autosave → signed canonical case in Neon", async ({ page, browser }) => {
  const connection = process.env.BROADBRIDGE_DATABASE_URL;
  const outbox = process.env.CAPTURE_TEST_OUTBOX;
  const email = process.env.CAPTURE_TEST_EMAIL;
  if (!connection || !outbox || !email || new URL(connection).hostname !== process.env.CAPTURE_DB_TEST_HOST) {
    throw new Error("Configure the verified Neon dev endpoint, local test outbox, and allowlisted test email first.");
  }
  const sql = neon(connection);
  const started = Date.now();
  await page.goto("/");
  await page.getByLabel("Email address", { exact: true }).fill(email);
  await page.getByRole("button", { name: "Email me a sign-in link" }).click();
  await expect(page.getByRole("heading", { name: "Check your email." })).toBeVisible();
  let magicLink = "";
  await expect.poll(async () => {
    try {
      const lines = (await readFile(outbox, "utf8")).trim().split("\n").map(line => JSON.parse(line));
      magicLink = lines.findLast(item => item.email === email)?.url ?? "";
      return Boolean(magicLink);
    } catch { return false; }
  }).toBe(true);
  // Do not attach the outbox, raw link, trace, or credentials to the test report.
  await page.goto(magicLink);
  await expect(page.getByRole("heading", { name: "Read this first" })).toBeVisible();
  await page.getByRole("button", { name: "+ New case", exact: true }).click();
  const caseId = (await page.locator(".head h2").innerText()).match(/BB-[0-9a-f-]+/)?.[0];
  if (!caseId) throw new Error("New case did not expose its identifier");
  await page.getByLabel("Short title", { exact: true }).fill("Synthetic browser smoke draft");
  await page.getByLabel("Short title", { exact: true }).fill("Synthetic browser smoke reviewed");
  await page.getByRole("tab", { name: "B · At the time", exact: true }).click();
  await page.locator("#b1_trigger").fill("Synthetic pressure rise; no real operating data.");
  await page.getByRole("tab", { name: "C · Test questions", exact: true }).click();
  await page.getByRole("button", { name: "+ Question", exact: true }).click();
  await page.getByLabel("Question, as the engineer would ask it", { exact: true }).fill("What should be checked first?");
  await page.getByLabel("Reference answer (Bill)", { exact: true }).fill("Verify the pressure measurement before diagnosis.");
  await page.getByLabel("Hard fail: an answer is wrong if it…", { exact: true }).fill("Inventing a pressure value.");
  await page.getByRole("tab", { name: "Sign-off", exact: true }).click();
  await page.getByLabel("Permitted use for this case", { exact: true }).selectOption("testing_only");
  await page.getByLabel("Name", { exact: true }).fill("Synthetic Test Reviewer");
  await page.getByLabel("Date", { exact: true }).fill("2026-09-24");
  await page.locator("#signed").check();
  await expect.poll(async () => {
    const rows = await sql`SELECT status, signed, updated_by, record->'identity'->>'title' AS title
      FROM broadbridge.cases WHERE case_id=${caseId}`;
    return rows.length === 1 && rows[0].signed && rows[0].status === "signed"
      && rows[0].updated_by === email && rows[0].title === "Synthetic browser smoke reviewed";
  }).toBe(true);
  const questions = await sql`SELECT effective_split, record FROM broadbridge.questions WHERE case_id=${caseId}`;
  expect(questions).toHaveLength(1);
  expect(questions[0].effective_split).toBe("dev");
  expect(questions[0].record.hard_fail_criteria).toBe("Inventing a pressure value.");
  expect(await sql`SELECT * FROM broadbridge.train_candidates WHERE case_id=${caseId}`).toHaveLength(0);
  const audit = await sql`SELECT actor FROM broadbridge.review_log WHERE case_id=${caseId} ORDER BY review_id DESC LIMIT 1`;
  expect(audit[0].actor).toBe(email);
  await page.getByLabel("Theme", { exact: true }).selectOption("light");
  await page.screenshot({ path: "test-results/capture-light.png", fullPage: true });
  await page.getByLabel("Theme", { exact: true }).selectOption("dark");
  await page.screenshot({ path: "test-results/capture-dark.png", fullPage: true });
  await page.getByRole("button", { name: "All records as JSON", exact: true }).click();
  const exported = JSON.parse(await page.locator("pre").innerText());
  expect(exported.cases.find((item: { case_id: string }) => item.case_id === caseId)?.status).toBe("signed");

  const replay = await browser.newContext();
  try {
    const anonymous = await replay.newPage();
    await anonymous.goto(magicLink);
    await anonymous.goto(process.env.AUTH_URL!);
    await expect(anonymous.getByRole("heading", { name: "Sign in to capture." })).toBeVisible();
  } finally { await replay.close(); }

  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Sign in to capture." })).toBeVisible();
  await writeFile("test-results/capture-smoke-summary.json", JSON.stringify({
    case_id: caseId, status: "signed", permitted_use: "testing_only", questions: 1,
    actor_verified: true, single_use_link_verified: true, export_verified: true,
    elapsed_seconds: (Date.now() - started) / 1000,
  }, null, 2));
});
