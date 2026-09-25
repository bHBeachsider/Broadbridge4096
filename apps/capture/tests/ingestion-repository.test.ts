import { randomUUID, createHash } from "node:crypto";
import { describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { getSql, localIngestionTestEnabled } from "../lib/db";
import { registerSource, findSource, listSources, saveRights, listCandidates, findJob } from "../lib/ingestion-repository";
import { sourceSchema } from "../lib/ingestion-validation";
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
    expect((await listSources()).find(s=>s.source_id===id)).toMatchObject({current_permission_status:"pending",current_permitted_use:"reference_only",job_id:null});
    expect(await listCandidates(identity)).toEqual([]);
    await expect(findJob(identity,"b".repeat(64))).rejects.toThrow();
    const rights={...identity,decision:"approved" as const,permitted_use:"training" as const,rights_basis:"Synthetic owner consent",expected_review_id:null};
    await saveRights(rights,"test@example.invalid");
    const reviewed=(await listSources()).find(s=>s.source_id===id)!;
    expect(reviewed.current_permission_status).toBe("approved"); expect(reviewed.current_rights_review_id).toBeTruthy();
    await expect(saveRights({...rights,decision:"revoked"},"test@example.invalid")).rejects.toMatchObject({code:"40001"});
    expect((await findSource(identity)).source.permission.status).toBe("pending");
    await expect(findSource({...identity,content_sha256:"c".repeat(64)})).rejects.toMatchObject({code:"40001"});
    const audit=await getSql()`SELECT created_by FROM broadbridge.source_revisions WHERE source_id=${id}`;
    expect(audit[0].created_by).toBe("test@example.invalid");
    // Immutable audit data stays in this disposable database; never delete review history.
  });
});
