"use client";
import React, { useEffect, useState } from "react";
import * as actions from "../app/ingestion/actions";
import { uploadSchema, type Identity, type Snapshot, type SourceRow, type Preview, type Candidate, type ActionResult } from "../lib/ingestion-validation";
import styles from "../app/ingestion/ingestion.module.css";
const identityOf = (source: Identity): Identity => ({ source_id: source.source_id, revision_id: source.revision_id, content_sha256: source.content_sha256 });
const stateLabel = (source: SourceRow) => !source.state ? "Pending upload verification / queueing" : source.state === "succeeded" ? `Extraction ${source.document_status ?? "complete"}` : source.state === "queued" ? "Queued · checksum verification pending" : source.state === "running" ? "Processing on CPU" : source.state === "retry" ? "Retry scheduled" : "Processing failed";
type QueueItem = { file: File; identity?: Identity; status: string };
function CandidateReview({ candidate, disabled, save }: { candidate: Candidate; disabled: boolean; save: (input: unknown) => Promise<void> }) {
  const [reason, setReason] = useState("");
  return <section className={styles.block}><h4>{candidate.example_id}</h4><p>Technical review: {candidate.status}</p><p className={styles.hash}>Candidate hash: {candidate.candidate_hash}</p><h5>Candidate messages and provenance</h5><pre>{JSON.stringify(candidate.candidate_record, null, 2)}</pre>{candidate.reason && <p>Recorded reason: {candidate.reason}</p>}<label htmlFor={`reason-${candidate.example_id}`}>Technical review reason</label><textarea id={`reason-${candidate.example_id}`} value={reason} onChange={e => setReason(e.target.value)} /><div className={styles.toolbar}>{(["approved", "rejected"] as const).map(decision => <button className="btn" disabled={disabled || !reason.trim()} key={decision} onClick={() => void save({ example_id: candidate.example_id, candidate_hash: candidate.candidate_hash, expected_review_id: candidate.review_id, decision, reason })}>{decision === "approved" ? "Accept candidate" : "Reject candidate"}</button>)}</div></section>;
}
export default function IngestionApp({ initial, email }: { initial: Snapshot; email: string }) {
  const [snapshot, setSnapshot] = useState(initial); const [queue, setQueue] = useState<QueueItem[]>([]);
  const [confidentiality, setConfidentiality] = useState("internal"); const [notice, setNotice] = useState(""); const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState<SourceRow | null>(null); const [preview, setPreview] = useState<Preview | null>(null);
  const [basis, setBasis] = useState(""); const [permittedUse, setPermittedUse] = useState("reference_only"); const [theme, setTheme] = useState("system");
  useEffect(() => { if (theme === "system") delete document.documentElement.dataset.theme; else document.documentElement.dataset.theme = theme; }, [theme]);
  async function refresh() {
    const result = await actions.loadIngestionAction();
    if (!result.ok) { setNotice(result.error); return; }
    setSnapshot(result.value);
    if (selected) setSelected(result.value.sources.find(s => s.source_id === selected.source_id && s.revision_id === selected.revision_id) ?? null);
  }
  async function perform(work: () => Promise<ActionResult<unknown>>, success: string) {
    setBusy(true); setNotice("");
    try { const result = await work(); setNotice(result.ok ? success : result.error); if (result.ok) { setPreview(null); await refresh(); } }
    catch { setNotice("Connection interrupted. Refresh status before retrying."); } finally { setBusy(false); }
  }
  async function inspect(source: SourceRow) {
    setSelected(source); setPreview(null); setBasis(""); setPermittedUse(source.current_permitted_use); setBusy(true);
    try { const result = await actions.previewSourceAction(identityOf(source), source.job_id); if (result.ok) setPreview(result.value); else setNotice(result.error); }
    catch { setNotice("Preview unavailable. Refresh and retry."); } finally { setBusy(false); }
  }
  const updateItem = (item: QueueItem, status: string) => { item.status = status; setQueue(current => [...current]); };
  async function uploadItems() {
    setBusy(true); setNotice("");
    try { for (const item of queue) {
      if (item.status === "Queued for CPU verification") continue;
      try {
        if (item.file.size > 50 * 1024 * 1024 || !item.file.size) throw new Error("File must contain 1 byte to 50 MiB.");
        updateItem(item, "Calculating SHA-256");
        const digest = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", await item.file.arrayBuffer())), byte => byte.toString(16).padStart(2, "0")).join("");
        if (item.identity && item.identity.content_sha256 !== digest) { updateItem(item, "This file differs from the pending revision. Select the exact original or create a new source."); continue; }
        const metadata = uploadSchema.parse({ original_filename: item.file.name, media_type: item.file.type || "application/octet-stream", size_bytes: item.file.size, content_sha256: digest, confidentiality });
        const prepared = item.identity ? await actions.resumeUploadAction(item.identity) : await actions.prepareUploadAction(metadata);
        if (!prepared.ok) { updateItem(item, prepared.error); continue; }
        item.identity = prepared.value.identity;
        updateItem(item, "Uploading original");
        const response = await fetch(prepared.value.url, { method: "PUT", headers: prepared.value.headers, body: item.file });
        // An immutable original may already exist after an interrupted response. HEAD decides identity.
        if (!response.ok && response.status !== 412) { updateItem(item, "Upload not confirmed. Retry this file or verify the pending source."); continue; }
        updateItem(item, "Verifying receipt and queueing");
        const completed = await actions.completeUploadAction(item.identity);
        updateItem(item, completed.ok ? "Queued for CPU verification" : completed.error);
      } catch { updateItem(item, "Upload not confirmed. Check the filename and 50 MiB limit, then retry. Pending records can be verified below."); }
    } await refresh(); } finally { setBusy(false); }
  }
  const blocks = Array.isArray(preview?.document?.blocks) ? preview.document.blocks as Record<string, unknown>[] : [];
  return <main className={styles.page}><header className={styles.header}><div><h1>Source intake & review</h1><p>Broadbridge oil & gas · {email}</p></div><div className={styles.toolbar}><a href="/">Case capture</a><label>Theme <select aria-label="Theme" value={theme} onChange={e => setTheme(e.target.value)}><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></label></div></header>
    <p className={styles.muted}>Bring reports, correspondence, tables, images, and recordings into a traceable source record. Originals keep their own rights review. Technical acceptance is recorded separately.</p>
    <section className={styles.intake}><h2>Add source files</h2><p>Up to 50 MiB per file. New sources start with rights pending and reference-only use. Uploading queues CPU extraction; it does not start training.</p><label>Source files<input type="file" multiple disabled={busy} onChange={e => setQueue(Array.from(e.target.files ?? []).map(file => ({ file, status: "Ready" })))} /></label><label>Confidentiality<select value={confidentiality} disabled={busy} onChange={e => setConfidentiality(e.target.value)}>{["public", "internal", "confidential", "restricted"].map(value => <option key={value}>{value}</option>)}</select></label><button className="btn primary" disabled={busy || !queue.length} onClick={() => void uploadItems()}>Upload selected files</button><ul className={styles.queue} aria-live="polite">{queue.map((item, index) => <li key={index}>{item.file.name} — {item.status}</li>)}</ul></section>
    {notice && <p role="status" className={styles.notice}>{notice}</p>}
    <div className={styles.toolbar}><h2>Source register</h2><button className="btn" disabled={busy} onClick={() => void perform(actions.loadIngestionAction, "Status refreshed.")}>Refresh status</button></div>
    <div className={styles.layout}><section className={styles.sources} aria-label="Source register">{!snapshot.sources.length && <p>No sources yet. Select files above to create pending source records.</p>}{snapshot.sources.map(source => <article key={`${source.source_id}/${source.revision_id}`} className={`${styles.source} ${selected?.source_id === source.source_id ? styles.selected : ""}`}><h3>{source.original_filename}</h3><p className={styles.status}>{stateLabel(source)}</p><dl><dt>Source</dt><dd>{source.source_id}</dd><dt>Revision</dt><dd>{source.revision_id}</dd><dt>Format / size</dt><dd>{source.media_type} / {source.size_bytes.toLocaleString()} bytes</dd><dt>Rights</dt><dd>{source.current_permission_status} · {source.current_permitted_use}</dd><dt>Confidentiality</dt><dd>{source.confidentiality}</dd></dl>{source.error_code && <p role="status">Processing error: {source.error_code}</p>}<div className={styles.toolbar}><button className="btn" disabled={busy} onClick={() => void inspect(source)}>Review source</button>{!source.job_id && <button className="btn" disabled={busy} onClick={() => void perform(() => actions.completeUploadAction(identityOf(source)), "Receipt verified; CPU verification queued.")}>Verify and queue</button>}{source.job_id && ["retry", "failed"].includes(source.state ?? "") && <button className="btn" disabled={busy} onClick={() => void perform(() => actions.retryIngestionAction(identityOf(source), source.job_id), "Retry status checked. Exhausted jobs require operator attention.")}>Check retry</button>}</div></article>)}</section>
    <aside className={styles.review} aria-label="Source review">{!selected ? <><h2>Review the evidence</h2><p>Select a source to inspect extracted blocks, provenance, and candidate messages. Rights approval and technical review remain separate.</p></> : <><h2>{selected.original_filename}</h2><p className={styles.hash}>SHA-256: {selected.content_sha256}</p>{!selected.job_id && <label>Retry original upload<input type="file" disabled={busy} onChange={e => { const file = e.target.files?.[0]; if (file) setQueue([{ file, identity: identityOf(selected), status: "Ready to retry the pending revision" }]); }} /></label>}<h3>Source rights</h3><p>Current decision: {selected.current_permission_status}. This decision applies only to this source revision and hash.</p><fieldset disabled={busy}><label htmlFor="permitted-use">Permitted use</label><select id="permitted-use" value={permittedUse} onChange={e => setPermittedUse(e.target.value)}><option value="reference_only">Reference only</option><option value="testing_only">Testing only</option><option value="training">Training</option></select><label htmlFor="rights-basis">Rights basis / revocation reason</label><textarea id="rights-basis" value={basis} onChange={e => setBasis(e.target.value)} /><div className={styles.toolbar}>{(["approved", "revoked"] as const).map(decision => <button className="btn" key={decision} disabled={!basis.trim()} onClick={() => void perform(() => actions.reviewRightsAction({ ...identityOf(selected), decision, permitted_use: permittedUse, rights_basis: basis, expected_review_id: selected.current_rights_review_id }), "Rights decision recorded for this revision.")}>{decision === "approved" ? "Approve source rights" : "Revoke source rights"}</button>)}</div></fieldset>
      <h3>Extracted evidence & provenance</h3>{!preview ? <p>Open this source again to load its latest evidence.</p> : !preview.document ? <p>Extraction is pending or unavailable. No extracted evidence is available for review yet.</p> : <><p>Extraction disposition: {String(preview.document.status)}</p><details><summary>Parser, classification, quality flags, and attachments</summary><pre>{JSON.stringify({ parser: preview.document.parser, classification: preview.document.classification, labels: preview.document.labels, quality_flags: preview.document.quality_flags, attachments: preview.document.attachments }, null, 2)}</pre></details>{blocks.map((block, i) => <article key={i} className={styles.block}><strong>{String(block.block_id ?? `Block ${i + 1}`)} · {String(block.kind ?? "evidence")}</strong><pre>{JSON.stringify(block, null, 2)}</pre></article>)}</>}
      <h3>Technical candidate review</h3><p>Review candidate answers against their source evidence. Accepting a candidate does not grant source rights or release a dataset.</p>{!preview?.candidates.length && <p>No candidate messages are available for this revision.</p>}{preview?.candidates.map(candidate => <CandidateReview key={`${candidate.example_id}/${candidate.candidate_hash}`} candidate={candidate} disabled={busy} save={async input => { await perform(() => actions.reviewCandidateAction(input), "Technical review recorded."); }} />)}</>}</aside></div>
  </main>;
}
