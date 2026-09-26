import { describe, expect, it } from "vitest";
import { scoreInputSchema, validateScoreForItem, safeReviewReturn, scoresCsv } from "../lib/public-review";

const input = {packet_id:"public-v1", packet_sha256:"a".repeat(64),question_id:"PUB-001",response_label:"B",score:2,critical_error:false,hard_fail:false,notes:"The stated basis matches the excerpt.",expected_revision:null};
describe("public review boundaries",()=>{
  it("requires deliberate complete scores and prohibits injected reviewer identity",()=>{
    expect(scoreInputSchema.parse(input).score).toBe(2);
    for(const change of [{score:3},{score:"2"},{score:null},{critical_error:null},{notes:" "},{reviewer:"Bill"},{expected_revision:0}])
      expect(scoreInputSchema.safeParse({...input,...change}).success).toBe(false);
  });
  it("requires hard failures to be critical and zero",()=>{
    expect(scoreInputSchema.safeParse({...input,hard_fail:true}).success).toBe(false);
    expect(scoreInputSchema.safeParse({...input,critical_error:true}).success).toBe(false);
    expect(scoreInputSchema.parse({...input,hard_fail:true,critical_error:true,score:0}).score).toBe(0);
  });
  it("cannot award or attribute an engineering error to an absent answer",()=>{
    expect(()=>validateScoreForItem(scoreInputSchema.parse(input), {answer:null})).toThrow();
    expect(()=>validateScoreForItem(scoreInputSchema.parse({...input,score:0}), {answer:null})).not.toThrow();
    expect(()=>validateScoreForItem(scoreInputSchema.parse({...input,score:0,critical_error:true}), {answer:null})).toThrow();
  });
  it.each(["https://evil.invalid/", "//evil.invalid/", "/\\evil.invalid", "/review/x?next=https://evil.invalid", "/review/../signin", "/review/x%0d%0a", "javascript:foo"])("rejects unsafe sign-in destination %s",path=>expect(safeReviewReturn(path)).toBe("/"));
  it("preserves an exact question URL after sign-in",()=>{
    expect(safeReviewReturn("/review/public-v1?question=PUB-022&response=A")).toBe("/review/public-v1?question=PUB-022&response=A");
  });
  it("exports CSV with blank unreviewed rows and escaped notes",()=>{
    const packet:any = {items:[{source_id:"s1",question_id:"q1",type:"brief",response_label:"A"},{source_id:"s1",question_id:"q1",type:"brief",response_label:"B"}]};
    const scores:any=[{question_id:"q1",response_label:"A",score:1,critical_error:false,reviewer:"test@example.invalid",review_date:"2026-09-26",notes:'=formula, "unsafe"\nline'}];
    const csv=scoresCsv(packet,scores);
    expect(csv).toContain('"\'=formula, ""unsafe""\nline"');
    expect(csv).toContain('"s1","q1","brief","B","","","","",""');
  });
});
