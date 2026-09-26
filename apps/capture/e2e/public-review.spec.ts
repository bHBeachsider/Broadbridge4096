import { test,expect } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { neon,neonConfig } from "@neondatabase/serverless";

test("direct review URL survives sign-in, saves audited scores and exports them",async({page,browser})=>{
  const connection=process.env.BROADBRIDGE_DATABASE_URL!;
  const endpoint=process.env.CAPTURE_TEST_SQL_ENDPOINT!;
  const outbox=process.env.CAPTURE_TEST_OUTBOX!;
  const email=process.env.CAPTURE_TEST_EMAIL!;
  if(process.env.CAPTURE_LOCAL_INGESTION_TEST!=="1"||!connection||!endpoint||!outbox||!email)throw new Error("Disposable local services required");
  if(new URL(connection).hostname!=="127.0.0.1"||!new URL(connection).pathname.startsWith("/broadbridge_test")||new URL(endpoint).hostname!=="127.0.0.1")throw new Error("Local target required");
  neonConfig.fetchEndpoint=()=>endpoint;const sql=neon(connection);
  await page.goto("/review/public-v1?question=PUB-001&response=B");
  await expect(page.getByLabel("Email address",{exact:true})).toBeVisible();
  await page.getByLabel("Email address",{exact:true}).fill(email);
  await page.getByRole("button",{name:"Email me a sign-in link"}).click();
  await expect(page.getByRole("heading",{name:"Check your email."})).toBeVisible();
  let link="";
  await expect.poll(async()=>{try{link=(await readFile(outbox,"utf8")).trim().split("\n").map(s=>JSON.parse(s)).findLast(v=>v.email===email)?.url??"";return Boolean(link);}catch{return false;}}).toBe(true);
  await page.goto(link);
  await expect(page).toHaveURL(/\/review\/public-v1\?question=PUB-001&response=B$/);
  await expect(page.getByRole("heading",{name:"Response B",exact:true})).toBeVisible();
  await expect(page.getByText(/0 \/ 60 scored by/)).toBeVisible();
  const stale=await page.context().newPage();await stale.goto("/review/public-v1?question=PUB-001&response=B");
  async function fill(target:typeof page,notes:string){
    await target.getByLabel("Score",{exact:true}).selectOption("2");
    await target.getByLabel("Critical error",{exact:true}).selectOption("false");
    await target.getByLabel("Any hard-fail criterion matched?",{exact:true}).selectOption("false");
    await target.getByLabel("Evidence, corrections and notes",{exact:true}).fill(notes);
  }
  await fill(page,"Synthetic browser acceptance score in disposable local DB; not a human judgment.");
  await expect(page.getByRole("button",{name:"Next",exact:true})).toBeDisabled();
  await page.getByRole("button",{name:"Save score",exact:true}).click();
  await expect(page.getByText("Score saved.",{exact:true})).toBeVisible();
  await fill(stale,"Stale tab must not overwrite a saved review.");await stale.getByRole("button",{name:"Save score",exact:true}).click();
  await expect(stale.getByText(/changed in another tab/)).toBeVisible();await stale.close();
  await page.reload();await expect(page.getByLabel("Score",{exact:true})).toHaveValue("2");
  const rows=await sql`SELECT reviewer,score,revision FROM broadbridge.current_public_review_scores WHERE packet_id='public-v1' AND question_id='PUB-001' AND response_label='B' AND reviewer=${email}`;
  expect(rows).toEqual([{reviewer:email,score:2,revision:1}]);
  const exported=await page.request.get("/review/public-v1/scores");expect(exported.status()).toBe(200);
  const csv=await exported.text();expect(csv).toContain('"PUB-001","brief","B","2","NO","'+email+'"');expect(csv).toContain('"PUB-001","brief","A","","","","",""');
  const anonymous=await browser.newContext();expect((await anonymous.request.get(new URL("/review/public-v1/scores",process.env.AUTH_URL).toString())).status()).toBe(401);await anonymous.close();
  const output=process.env.CAPTURE_TEST_RUN_ROOT!;
  await page.screenshot({path:join(output,"public-review-desktop.png"),fullPage:true});
  await page.setViewportSize({width:390,height:844});await page.screenshot({path:join(output,"public-review-mobile.png"),fullPage:true});
  expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBe(true);
});
