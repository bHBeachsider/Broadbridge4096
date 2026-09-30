import { beforeEach, expect, it, vi } from "vitest";
const deps = vi.hoisted(() => ({actor:vi.fn(),save:vi.fn(),load:vi.fn()}));
vi.mock("../auth",()=>({requireActor:deps.actor}));
vi.mock("../lib/questionnaire-repository",()=>({persistQuestionnaire:deps.save,loadQuestionnaire:deps.load}));
import { saveQuestionnaire } from "../app/questionnaires/pressure-training-v1/actions";
import { GET } from "../app/questionnaires/pressure-training-v1/responses/route";
import { emptyResponse } from "../lib/questionnaire";
const input = {record:emptyResponse("a".repeat(64)),expected_revision:null};
beforeEach(()=>{vi.resetAllMocks();deps.actor.mockResolvedValue("reviewer@example.invalid");deps.save.mockResolvedValue({revision:1});deps.load.mockResolvedValue(null);});
it("uses the signed-in actor and validates the save envelope",async()=>{
  expect((await saveQuestionnaire(input)).ok).toBe(true);
  expect(deps.save).toHaveBeenCalledWith(input.record,"reviewer@example.invalid",null);
  expect((await saveQuestionnaire({...input,reviewer:"other@example.invalid"})).ok).toBe(false);
  expect(deps.save).toHaveBeenCalledTimes(1);
});
it("refuses signed-out writes and exports",async()=>{
  deps.actor.mockRejectedValue(new Error("denied"));
  expect((await saveQuestionnaire(input)).ok).toBe(false);
  expect((await GET()).status).toBe(401);expect(deps.save).not.toHaveBeenCalled();expect(deps.load).not.toHaveBeenCalled();
});
it("reports conflicts and hides raw diagnostics",async()=>{
  deps.save.mockRejectedValue({code:"40001",message:"private-data"});
  const result=await saveQuestionnaire(input);expect(result).toMatchObject({ok:false,conflict:true});expect(JSON.stringify(result)).not.toContain("private-data");
});
it("exports only the current actor with no-store headers",async()=>{
  const response=await GET();expect(response.status).toBe(200);expect(response.headers.get("Cache-Control")).toBe("private, no-store");
  expect(deps.load).toHaveBeenCalledWith("reviewer@example.invalid");expect((await response.json()).authenticated_reviewer).toBe("reviewer@example.invalid");
});
