import { describe,expect,it,vi } from "vitest";
vi.mock("server-only",()=>({}));
import { getSql,localIngestionTestEnabled } from "../lib/db";
import { emptyResponse } from "../lib/questionnaire";
import { loadQuestionnaire,persistQuestionnaire,questionnaireHash } from "../lib/questionnaire-repository";
const enabled=process.env.CAPTURE_LOCAL_INGESTION_TEST==="1"&&Boolean(process.env.CAPTURE_TEST_SQL_ENDPOINT);
describe.skipIf(!enabled)("questionnaire on disposable PostgreSQL",()=>{
  it("isolates reviewers, preserves revisions, retries idempotently and refuses stale saves",async()=>{
    if(!localIngestionTestEnabled())throw new Error("Local target required");
    const actor="sql-reviewer@example.invalid",other="sql-other@example.invalid",sql=getSql();
    const one={...emptyResponse(questionnaireHash),answers:{"PRIORITY-01":{answer:"Synthetic review only"}}};
    const first=await persistQuestionnaire(one,actor,null);expect(first.revision).toBe(1);expect(first.reviewer).toBe(actor);
    expect((await persistQuestionnaire(one,actor,null)).revision).toBe(1);
    const two={...one,answers:{"PRIORITY-01":{answer:"Revised synthetic review"}}};
    await expect(persistQuestionnaire(two,actor,null)).rejects.toMatchObject({code:"40001"});
    expect((await persistQuestionnaire(two,actor,1)).revision).toBe(2);
    expect(await loadQuestionnaire(other)).toBeNull();expect((await persistQuestionnaire(one,other,null)).revision).toBe(1);
    expect((await loadQuestionnaire(actor))?.record.answers["PRIORITY-01"].answer).toBe("Revised synthetic review");
    await expect(persistQuestionnaire({...one,questionnaire_sha256:"b".repeat(64)},actor,2)).rejects.toThrow();
    await expect(sql`SELECT broadbridge.save_questionnaire_response(${JSON.stringify({...one,answers:{unknown:{answer:"bad"}}})}::jsonb,${actor},2)`).rejects.toMatchObject({code:"23514"});
    await expect(sql`UPDATE broadbridge.questionnaire_responses SET record=record WHERE reviewer=${actor}`).rejects.toMatchObject({code:"23514"});
    await expect(sql`DELETE FROM broadbridge.questionnaire_packets WHERE questionnaire_id='pressure-training-v1'`).rejects.toMatchObject({code:"23514"});
    const history=await sql`SELECT revision FROM broadbridge.questionnaire_responses WHERE reviewer=${actor} ORDER BY revision`;
    expect(history).toEqual([{revision:1},{revision:2}]);
  });
});
