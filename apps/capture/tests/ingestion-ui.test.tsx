// @vitest-environment jsdom
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";
const mocks = vi.hoisted(() => ({ loadIngestionAction:vi.fn(),loadCandidatesAction:vi.fn(),previewSourceAction:vi.fn(),reviewRightsAction:vi.fn(),reviewCandidateAction:vi.fn(),completeUploadAction:vi.fn(),prepareUploadAction:vi.fn(),resumeUploadAction:vi.fn(),retryIngestionAction:vi.fn() }));
vi.mock("../app/ingestion/actions",() => mocks);
import IngestionApp from "../components/IngestionApp";
import type { SourceRow } from "../lib/ingestion-validation";
let root:Root; let host:HTMLDivElement;
const source:SourceRow = {source_id:"synthetic-source",revision_id:"r1",content_sha256:"a".repeat(64),source_ref:"registry/synthetic",original_filename:"Synthetic report.txt",media_type:"text/plain",size_bytes:8,confidentiality:"internal",current_permission_status:"pending",current_permitted_use:"reference_only",current_rights_review_id:null,created_by:"actor@example.invalid",job_id:null,state:null,error_code:null,document_status:null};
beforeEach(() => {vi.resetAllMocks(); (globalThis as {IS_REACT_ACT_ENVIRONMENT?:boolean}).IS_REACT_ACT_ENVIRONMENT=true; host=document.createElement("div");document.body.append(host);root=createRoot(host);mocks.loadIngestionAction.mockResolvedValue({ok:true,value:{sources:[source],next_cursor:null}});mocks.previewSourceAction.mockResolvedValue({ok:true,value:{document:null}});mocks.loadCandidatesAction.mockResolvedValue({ok:true,value:{candidates:[],next_cursor:null}});});
afterEach(async () => {await act(async()=>root.unmount());host.remove();});
async function mount() {await act(async()=>root.render(<IngestionApp initial={{sources:[source],next_cursor:null}} email="actor@example.invalid"/>));}
async function click(label:string) {const button=Array.from(host.querySelectorAll("button")).find(b=>b.textContent===label);expect(button).toBeTruthy();await act(async()=>button!.click());}
async function fill(selector:string,value:string) {const field=host.querySelector<HTMLTextAreaElement>(selector)!;await act(async()=>{Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,"value")!.set!.call(field,value);field.dispatchEvent(new Event("input",{bubbles:true}));});}
describe("source intake and separate review controls",()=>{
  it("shows pending receipt honestly and preserves reference-only rights",async()=>{await mount();expect(host.textContent).toContain("Pending upload verification / queueing");expect(host.textContent).toContain("pending · reference_only");expect(host.querySelector('input[type="file"]')?.hasAttribute("multiple")).toBe(true);expect(host.querySelector('a[href="/"]')).toBeTruthy();});
  it("sends exact source identity and previous review with rights decision",async()=>{mocks.reviewRightsAction.mockResolvedValue({ok:true});await mount();await click("Review source");await fill("#rights-basis","Synthetic owner consent");await click("Approve source rights");expect(mocks.reviewRightsAction).toHaveBeenCalledWith({source_id:source.source_id,revision_id:"r1",content_sha256:source.content_sha256,expected_review_id:null,decision:"approved",permitted_use:"reference_only",rights_basis:"Synthetic owner consent"});expect(mocks.reviewCandidateAction).not.toHaveBeenCalled();});
  it("keeps review text and shows stale rejection without claiming approval",async()=>{mocks.reviewRightsAction.mockResolvedValue({ok:false,conflict:true,error:"Review changed. Refresh."});await mount();await click("Review source");await fill("#rights-basis","Keep my reason");await click("Approve source rights");expect(host.textContent).toContain("Review changed. Refresh.");expect((host.querySelector("#rights-basis") as HTMLTextAreaElement).value).toBe("Keep my reason");expect(host.textContent).toContain("Current decision: pending");});
  it("renders source text as inert evidence and keeps technical review separate",async()=>{mocks.previewSourceAction.mockResolvedValue({ok:true,value:{document:{status:"partial",blocks:[{block_id:"b1",kind:"text",text:"<script>fakeApproval()</script>",location:{page:2}}],quality_flags:["ocr_review"]},candidates:[]}});await mount();await click("Review source");expect(host.textContent).toContain("Extraction disposition: partial");expect(host.textContent).toContain("<script>fakeApproval()</script>");expect(host.querySelector("script")).toBeNull();expect(host.textContent).toContain("No candidate messages");});
  it("does not claim stored when completion fails",async()=>{mocks.completeUploadAction.mockResolvedValue({ok:false,error:"Pending verification. Retry."});await mount();await click("Verify and queue");expect(host.textContent).toContain("Pending verification. Retry.");expect(host.textContent).toContain("Pending upload verification / queueing");});
});
describe("visible pagination and full-content review state",()=>{
  it("navigates source pages with the exact prior cursor and shows window counts",async()=>{
    const cursor={source_id:source.source_id,revision_id:"r1",content_sha256:source.content_sha256};
    await act(async()=>root.render(<IngestionApp initial={{sources:[source],next_cursor:cursor}} email="actor@example.invalid"/>));
    mocks.loadIngestionAction.mockResolvedValueOnce({ok:true,value:{sources:[{...source,source_id:"beyond-old-window",original_filename:"Source 201.txt"}],next_cursor:null}});
    await click("Next sources");expect(mocks.loadIngestionAction).toHaveBeenCalledWith(cursor);expect(host.textContent).toContain("Source page 2 · 1 shown");expect(host.textContent).toContain("Source 201.txt");
    await click("Previous sources");expect(mocks.loadIngestionAction).toHaveBeenLastCalledWith(null);expect(host.textContent).toContain("Source page 1 · 1 shown");
  });
  it("keeps candidate pages available when evidence is oversized and blocks acceptance of unavailable full content",async()=>{
    const cursor={example_id:"candidate-020",candidate_hash:"c".repeat(64)};
    mocks.previewSourceAction.mockResolvedValue({ok:false,error:"This complete preview exceeds the 1 MiB response budget."});
    mocks.loadCandidatesAction.mockResolvedValueOnce({ok:true,value:{candidates:[],next_cursor:cursor}}).mockResolvedValueOnce({ok:true,value:{candidates:[{example_id:"candidate-101",candidate_hash:"d".repeat(64),status:"pending",review_id:null,reason:null,candidate_record:null,preview_oversized:true}],next_cursor:null}});
    await mount();await click("Review source");await click("Next candidates");
    expect(mocks.loadCandidatesAction).toHaveBeenLastCalledWith({source_id:source.source_id,revision_id:"r1",content_sha256:source.content_sha256},cursor);
    expect(host.textContent).toContain("Candidate page 2 · 1 shown");expect(host.textContent).toContain("no candidate text has been truncated");
    await fill(`#reason-candidate-101-${"d".repeat(64)}`,"Cannot approve without full content");
    const accept=Array.from(host.querySelectorAll("button")).find(button=>button.textContent==="Accept candidate")!;
    expect(accept.disabled).toBe(true);expect(mocks.reviewCandidateAction).not.toHaveBeenCalled();
  });
});
