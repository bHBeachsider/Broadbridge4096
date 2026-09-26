import { beforeEach,expect,it,vi } from "vitest";
const deps=vi.hoisted(()=>({actor:vi.fn(),save:vi.fn()}));
vi.mock("../auth",()=>({requireActor:deps.actor}));
vi.mock("../lib/public-review-repository",()=>({persistPublicScore:deps.save}));
import { savePublicScore } from "../app/review/actions";
const input={packet_id:"public-v1",packet_sha256:"a".repeat(64),question_id:"PUB-001",response_label:"B",score:2,critical_error:false,hard_fail:false,notes:"Checked evidence",expected_revision:null};
beforeEach(()=>{vi.resetAllMocks();deps.actor.mockResolvedValue("reviewer@example.invalid");deps.save.mockResolvedValue({revision:1});});
it("takes actor only from the authenticated session",async()=>{
  expect((await savePublicScore(input)).ok).toBe(true);
  expect(deps.save).toHaveBeenCalledWith(input,"reviewer@example.invalid");
});
it("does not write if signed out",async()=>{
  deps.actor.mockRejectedValue(new Error("denied"));
  expect((await savePublicScore(input)).ok).toBe(false);
  expect(deps.save).not.toHaveBeenCalled();
});
it("refuses forged identity and malformed values",async()=>{
  expect((await savePublicScore({...input,reviewer:"Bill"})).ok).toBe(false);
  expect(deps.save).not.toHaveBeenCalled();
});
it("reports conflicts without leaking SQL or configuration",async()=>{
  deps.save.mockRejectedValue({code:"40001",message:"secret-db-data"});
  const result=await savePublicScore(input);
  expect(result).toMatchObject({ok:false,message:expect.stringContaining("another tab")});
  expect(JSON.stringify(result)).not.toContain("secret-db-data");
});
