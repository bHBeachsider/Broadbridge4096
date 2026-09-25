import { randomUUID, createHash } from "node:crypto";
import { describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { getSql, localIngestionTestEnabled } from "../lib/db";
import { registerSource, findSource, listSources, saveRights, listCandidates, findJob, saveCandidateReview } from "../lib/ingestion-repository";
import { sourceSchema, type SourceCursor, type CandidateCursor } from "../lib/ingestion-validation";
const enabled = process.env.CAPTURE_LOCAL_INGESTION_TEST === "1" && Boolean(process.env.CAPTURE_TEST_SQL_ENDPOINT);
describe.skipIf(!enabled)("ingestion repository on disposable local PostgreSQL",()=>{
  it("persists pending source identity, rights overlay and rejects stale reviews",async()=>{
    if(!localIngestionTestEnabled()) throw new Error("Local disposable database required");
    const id=`t7-${randomUUID()}`;
    const source=sourceSchema.parse({schema:"foundry.source_revision/1",project_id:"broadbridge-oil-gas",source_id:id,revision_id:"r1",family_id:id,object_key:`incoming/broadbridge-oil-gas/${id}/original`,original_filename:"Synthetic test report.txt",content_sha256:"a".repeat(64),size_bytes:8,media_type:"text/plain",confidentiality:"internal",permission:{status:"pending",permitted_use:"reference_only",rights_basis:"",reviewed_by:null,reviewed_at:null},relationships:[]});
    const identity={source_id:id,revision_id:"r1",content_sha256:source.content_sha256};
    const ref=`registry/broadbridge-oil-gas/${createHash("sha256").update(JSON.stringify(source.object_key)).digest("hex")}.json`;
    await registerSource(source,ref,"test@example.invalid"); await registerSource(source,ref,"test@example.invalid");
    expect(await findSource(identity)).toEqual({source,sourceRef:ref});
    expect((await listSources({source_id:id,revision_id:"r0",content_sha256:"0".repeat(64)})).sources.find(s=>s.source_id===id)).toMatchObject({current_permission_status:"pending",current_permitted_use:"reference_only",job_id:null});
    expect(await listCandidates(identity)).toEqual({candidates:[],next_cursor:null});
    await expect(findJob(identity,"b".repeat(64))).rejects.toThrow();
    const rights={...identity,decision:"approved" as const,permitted_use:"training" as const,rights_basis:"Synthetic owner consent",expected_review_id:null};
    await saveRights(rights,"test@example.invalid");
    const reviewed=(await listSources({source_id:id,revision_id:"r0",content_sha256:"0".repeat(64)})).sources.find(s=>s.source_id===id)!;
    expect(reviewed.current_permission_status).toBe("approved"); expect(reviewed.current_rights_review_id).toBeTruthy();
    await expect(saveRights({...rights,decision:"revoked"},"test@example.invalid")).rejects.toMatchObject({code:"40001"});
    expect((await findSource(identity)).source.permission.status).toBe("pending");
    await expect(findSource({...identity,content_sha256:"c".repeat(64)})).rejects.toMatchObject({code:"40001"});
    const audit=await getSql()`SELECT created_by FROM broadbridge.source_revisions WHERE source_id=${id}`;
    expect(audit[0].created_by).toBe("test@example.invalid");
    // Immutable audit data stays in this disposable database; never delete review history.
  });
});
describe.skipIf(!enabled)("deterministic SQL continuation beyond old result windows",()=>{
  it("visits all 201 revisions and 101 candidate hashes without dropping natural-key ties",async()=>{
    if(!localIngestionTestEnabled()) throw new Error("Local disposable database required");
    const id=`pages-${randomUUID()}`; const actor="test@example.invalid";
    const sources=Array.from({length:201},(_,index)=>sourceSchema.parse({schema:"foundry.source_revision/1",project_id:"broadbridge-oil-gas",source_id:id,revision_id:`r${String(index).padStart(3,"0")}`,family_id:id,object_key:`incoming/broadbridge-oil-gas/${id}/r${index}/original`,original_filename:`Synthetic pagination ${index}.txt`,content_sha256:"a".repeat(64),size_bytes:8,media_type:"text/plain",confidentiality:"internal",permission:{status:"pending",permitted_use:"reference_only",rights_basis:"",reviewed_by:null,reviewed_at:null},relationships:[]}));
    const sql=getSql();
    const manifests=sources.map(source=>({source,ref:`registry/broadbridge-oil-gas/${createHash("sha256").update(JSON.stringify(source.object_key)).digest("hex")}.json`}));
    await sql`SELECT broadbridge.register_source_revision(item->'source',item->>'ref',${actor}) FROM jsonb_array_elements(${JSON.stringify(manifests)}::jsonb) AS item`;
    let cursor:SourceCursor={source_id:id,revision_id:"r",content_sha256:"0".repeat(64)};const seen:string[]=[];
    do {const page=await listSources(cursor);seen.push(...page.sources.filter(row=>row.source_id===id).map(row=>row.revision_id));cursor=page.next_cursor;if(!page.sources.some(row=>row.source_id===id))break;}while(cursor);
    expect(seen).toEqual(sources.map(source=>source.revision_id));
    const identity={source_id:id,revision_id:sources[0].revision_id,content_sha256:sources[0].content_sha256};
    const candidates=Array.from({length:101},(_,index)=>({hash:index.toString(16).padStart(64,"0"),record:{schema:"foundry.training_example/1",example_id:`candidate-${id}`,family_id:id,split:"train",source_refs:[{...identity,block_ids:["b1"]}],messages:[{role:"user",content:"Synthetic question"},{role:"assistant",content:`Synthetic answer ${index}`}],task_type:"grounded_explanation",quality_flags:[],review:{status:"pending",reviewer:null,reviewed_at:null,reason:""}}}));
    await sql`SELECT broadbridge.register_candidate(item->'record',item->>'hash',${actor}) FROM jsonb_array_elements(${JSON.stringify(candidates)}::jsonb) AS item`;
    let candidateCursor:CandidateCursor=null;const hashes:string[]=[];
    do{const page=await listCandidates(identity,candidateCursor);hashes.push(...page.candidates.map(row=>row.candidate_hash));candidateCursor=page.next_cursor;}while(candidateCursor);
    expect(hashes).toEqual(candidates.map(item=>item.hash));
    const last=candidates.at(-1)!;
    const review={example_id:last.record.example_id,candidate_hash:last.hash,decision:"approved" as const,reason:"Synthetic complete review beyond the old window",expected_review_id:null};
    await saveCandidateReview(review,actor);
    await expect(saveCandidateReview({...review,decision:"rejected"},actor)).rejects.toMatchObject({code:"40001"});
  },30000);
});
