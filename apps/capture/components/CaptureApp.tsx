"use client";

import React, { useEffect, useReducer, useRef, useState } from "react";
import { deleteCaseAction, saveCaseAction, saveWorkflowAction } from "../app/actions";
import type { CaseRecord, WorkflowRecord } from "../lib/validation";
import { ABOUT_HTML, DECISION, EVI_COLS, HINDSIGHT, HYP_COLS, IDENTITY, OBS_COLS, PART_A, Q_TYPES } from "../lib/capture-copy";

type CaptureRecord = CaseRecord | WorkflowRecord;
type Entry = {
  record: CaptureRecord;
  revision: string | null;
  version: number;
  savedVersion: number;
  error?: string;
  conflict?: boolean;
  timer?: ReturnType<typeof setTimeout>;
  inFlight?: Promise<boolean>;
};
type Props = {
  initialCases: Array<{ record: CaseRecord; revision: string }>;
  initialWorkflow: { record: WorkflowRecord; revision: string } | null;
  email: string;
  onSignOut?: () => Promise<void>;
};
type Tab = "identity" | "decision" | "hindsight" | "evidence" | "questions" | "signoff";
type Rows = "observations" | "hypotheses" | "evidence";
type Row = Record<string, string | boolean>;
const TABS: readonly [Tab, string][] = [["identity", "Identity"], ["decision", "B · At the time"], ["hindsight", "B · In hindsight"], ["evidence", "Evidence"], ["questions", "C · Test questions"], ["signoff", "Sign-off"]];
const permissions = ["training", "testing_only", "reference_only"] as const;
const caseKey = (id: string) => `case:${id}`;
const dirty = (entry: Entry) => entry.version !== entry.savedVersion;
const clone = <T,>(value: T): T => structuredClone(value);
const signoffComplete = (record: CaseRecord) => [record.reviewer_signoff.name, record.reviewer_signoff.date].every((value) => !["", "unknown", "undecided"].includes(value.trim().toLowerCase()));

function newCase(): CaseRecord {
  const id = `BB-${crypto.randomUUID()}`;
  const timestamp = new Date().toISOString();
  return {
    schema: "broadbridge.case_record/1", case_id: id, family_id: id, status: "draft",
    identity: { title: "", unit_service: "", period: "", record_type: "real_event", confidentiality: "", permitted_use: "training" },
    decision_time: { b1_trigger: "", b2_operating_context: "", b3_initial_info_and_requests: "", observations: [], b5_initial_hypotheses: "", b6_distrusted_or_missing: "" },
    hindsight: { hypotheses: [], b8_turning_point: "", b9_calculations: "", b10_actions_taken: "", b11_confidence: "", b12_dangerous_wrong_answer: "", b13_lesson_and_limits: "" },
    evidence: [], questions: [], reviewer_signoff: { signed: false, name: "", date: "" }, created_at: timestamp, updated_at: timestamp,
  };
}

function QuestionField({ id, number, label, hint, value, onChange }: { id: string; number?: string; label: string; hint?: string; value: string; onChange: (value: string) => void }) {
  return <div className="q"><label htmlFor={id}>{number && <span className="n">{number}</span>}{label}</label>{hint && <p className="hint">{hint}</p>}<textarea id={id} value={value} onChange={(event) => onChange(event.target.value)} /></div>;
}

export default function CaptureApp({ initialCases, initialWorkflow, email, onSignOut }: Props) {
  const [entries] = useState(() => {
    const values = new Map<string, Entry>();
    for (const item of initialCases) values.set(caseKey(item.record.case_id), { ...clone(item), version: 0, savedVersion: 0 });
    values.set("workflow", { record: clone(initialWorkflow?.record ?? { schema: "broadbridge.workflow/1", answers: {}, updated_at: "" }), revision: initialWorkflow?.revision ?? null, version: 0, savedVersion: 0 });
    return values;
  });
  const [, redraw] = useReducer((value: number) => value + 1, 0);
  const mounted = useRef(true);
  const [view, setView] = useState<"about" | "workflow" | "case" | "export">("about");
  const [openId, setOpenId] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("identity");
  const [notice, setNotice] = useState("");
  const [saveStatus, setSaveStatus] = useState("Connected. Changes save automatically.");
  const [exportText, setExportText] = useState("");
  const [copyMessage, setCopyMessage] = useState("");
  const [deleting, setDeleting] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [signingOut, setSigningOut] = useState(false);
  const signOutPending = useRef(false);
  const deleteTimer = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const navigation = useRef(0);
  const jsonElement = useRef<HTMLPreElement>(null);
  const [theme, setTheme] = useState<"system" | "light" | "dark">("system");

  const refresh = () => { if (mounted.current) redraw(); };
  const allCases = Array.from(entries.entries()).filter(([key]) => key !== "workflow").map(([, entry]) => entry.record as CaseRecord).sort((a, b) => a.case_id.localeCompare(b.case_id));
  const workflow = entries.get("workflow")!.record as WorkflowRecord;
  const entry = openId ? entries.get(caseKey(openId)) : undefined;
  const record = entry?.record as CaseRecord | undefined;
  const unsaved = Array.from(entries.values()).some(dirty);
  const errors = Array.from(entries.entries()).filter(([, value]) => value.error);
  const saving = Array.from(entries.values()).some((value) => value.inFlight);

  useEffect(() => {
    mounted.current = true;
    const beforeUnload = (event: BeforeUnloadEvent) => {
      if (Array.from(entries.values()).some(dirty)) { event.preventDefault(); event.returnValue = ""; }
    };
    window.addEventListener("beforeunload", beforeUnload);
    return () => {
      mounted.current = false;
      window.removeEventListener("beforeunload", beforeUnload);
      for (const value of entries.values()) clearTimeout(value.timer);
      clearTimeout(deleteTimer.current);
    };
  }, [entries]);

  useEffect(() => {
    if (theme === "system") delete document.documentElement.dataset.theme;
    else document.documentElement.dataset.theme = theme;
  }, [theme]);

  async function flushKey(key: string, retry = false): Promise<boolean> {
    const item = entries.get(key);
    if (!item) return true;
    clearTimeout(item.timer);
    if (item.inFlight) {
      if (!await item.inFlight) return false;
      return flushKey(key, retry);
    }
    if (item.conflict || (item.error && !retry)) return false;
    if (retry) item.error = undefined;
    if (!dirty(item)) return true;
    const task = async () => {
      while (dirty(item) && mounted.current) {
        const version = item.version;
        const snapshot = clone(item.record);
        try {
          const result = key === "workflow" ? await saveWorkflowAction(snapshot, item.revision) : await saveCaseAction(snapshot, item.revision);
          if (!result.ok) {
            item.error = result.error;
            item.conflict = result.conflict ?? false;
            refresh();
            return false;
          }
          item.revision = result.value.revision;
          item.savedVersion = version;
          // A response can acknowledge older text, but cannot replace a later edit.
          if (item.version === version) item.record = clone(result.value.record);
          item.error = undefined;
          if (mounted.current) setSaveStatus(`Saved ${new Date().toLocaleTimeString()}`);
          refresh();
        } catch {
          item.error = "Save failed. Your text is still in this tab; try again shortly.";
          refresh();
          return false;
        }
      }
      return !dirty(item);
    };
    item.inFlight = task();
    refresh();
    try { return await item.inFlight; }
    finally { item.inFlight = undefined; refresh(); }
  }

  function changed(key: string, next: CaptureRecord) {
    if (signOutPending.current) return;
    const item = entries.get(key)!;
    item.record = next;
    item.version++;
    clearTimeout(item.timer);
    item.timer = setTimeout(() => { void flushKey(key); }, 1200);
    setCopyMessage("");
    refresh();
  }

  function editCase(update: (draft: CaseRecord) => void, renewReview = true) {
    if (!openId || deleting === openId || signOutPending.current) return;
    const current = entries.get(caseKey(openId))!;
    const draft = clone(current.record as CaseRecord);
    if (renewReview && (draft.status === "signed" || draft.reviewer_signoff.signed)) {
      draft.status = "draft";
      draft.reviewer_signoff.signed = false;
      setNotice("This case changed after sign-off. Review the updated record and sign it again.");
    }
    update(draft);
    draft.updated_at = new Date().toISOString();
    changed(caseKey(openId), draft);
  }

  async function flushAll() {
    const results = await Promise.all(Array.from(entries.keys(), (key) => flushKey(key)));
    return results.every(Boolean) && !Array.from(entries.values()).some(dirty);
  }

  async function handleSignOut() {
    if (!onSignOut || signOutPending.current || deleting) return;
    // Lock synchronously as well as disabling the controls, so an event already
    // queued before React renders cannot add a new edit between flush and logout.
    signOutPending.current = true;
    setSigningOut(true);
    setNotice("");
    let signedOut = false;
    try {
      const saved = await flushAll();
      if (!mounted.current) return;
      if (!saved || Array.from(entries.values()).some((item) => dirty(item) || item.error || item.conflict)) {
        setNotice("Sign out is paused until all changes are saved. Resolve the save errors below.");
        return;
      }
      await onSignOut();
      signedOut = true;
    } catch {
      if (mounted.current) setNotice("Sign out failed. Your text remains in this tab; try again.");
    } finally {
      // Keep editing locked after success until the server action navigates away.
      if (!signedOut) {
        signOutPending.current = false;
        if (mounted.current) setSigningOut(false);
      }
    }
  }

  function exportRecord(id?: string) {
    if (id) return entries.get(caseKey(id))!.record;
    return { exported_at: new Date().toISOString(), workflow: entries.get("workflow")!.record, cases: Array.from(entries.entries()).filter(([key]) => key !== "workflow").map(([, item]) => item.record) };
  }

  async function showExport() {
    const request = ++navigation.current;
    setExporting(true);
    try {
      if (!await flushAll()) { setNotice("Export is paused until all changes are saved. Resolve the save errors below."); return; }
      if (!mounted.current || request !== navigation.current) return;
      setExportText(JSON.stringify(exportRecord(), null, 2));
      setView("export");
      setOpenId(null);
      setCopyMessage("");
    } finally { if (mounted.current) setExporting(false); }
  }

  async function copyJson(id?: string) {
    const flushed = await flushAll();
    if (!mounted.current) return;
    if (!flushed) { setNotice("Export is paused until all changes are saved. Resolve the save errors below."); return; }
    const text = JSON.stringify(exportRecord(id), null, 2);
    if (!id) setExportText(text);
    try { await navigator.clipboard.writeText(text); if (mounted.current) setCopyMessage("Copied."); }
    catch {
      if (!mounted.current) return;
      if (jsonElement.current) {
        const range = document.createRange();
        range.selectNodeContents(jsonElement.current);
        const selection = window.getSelection();
        selection?.removeAllRanges();
        selection?.addRange(range);
      }
      setCopyMessage("Select-all applied; press Ctrl/Cmd+C.");
    }
  }

  function navigate(next: "about" | "workflow" | "case", id: string | null = null) {
    navigation.current++;
    setView(next); setOpenId(id); setTab("identity"); setNotice(""); setCopyMessage(""); setConfirmDelete(null);
    clearTimeout(deleteTimer.current);
  }

  function addCase() {
    if (signOutPending.current) return;
    const next = newCase();
    entries.set(caseKey(next.case_id), { record: next, revision: null, version: 0, savedVersion: 0 });
    navigate("case", next.case_id);
    changed(caseKey(next.case_id), next);
  }

  async function removeCase(id: string) {
    if (signOutPending.current) return;
    if (confirmDelete !== id) {
      setConfirmDelete(id);
      clearTimeout(deleteTimer.current);
      deleteTimer.current = setTimeout(() => setConfirmDelete(null), 4000);
      return;
    }
    clearTimeout(deleteTimer.current);
    const key = caseKey(id);
    const item = entries.get(key)!;
    clearTimeout(item.timer);
    setDeleting(id);
    try {
      if (item.inFlight) await item.inFlight;
      if (item.revision) {
        if (!await flushKey(key)) return;
        const result = await deleteCaseAction(id, item.revision);
        if (!result.ok) {
          item.error = result.error; item.conflict = result.conflict ?? false;
          setNotice("Delete failed. The case remains in this tab.");
          refresh(); return;
        }
      }
      entries.delete(key);
      navigate("about");
      refresh();
    } catch { setNotice("Delete failed. The case remains in this tab; try again shortly."); }
    finally { if (mounted.current) { setDeleting(null); setConfirmDelete(null); } }
  }

  function setStatus(value: CaseRecord["status"]) {
    if (!record) return;
    if (value === "signed" && (!record.reviewer_signoff.signed || !signoffComplete(record))) {
      setNotice("Enter the reviewer name and date, then tick the sign-off before marking this case signed.");
      setTab("signoff"); return;
    }
    editCase((draft) => { draft.status = value; if (value !== "signed") draft.reviewer_signoff.signed = false; }, false);
  }

  function setSigned(checked: boolean) {
    if (!record) return;
    if (checked && !signoffComplete(record)) { setNotice("Enter the reviewer name and date before ticking the sign-off."); return; }
    setNotice("");
    editCase((draft) => { draft.reviewer_signoff.signed = checked; draft.status = checked ? "signed" : "draft"; }, false);
  }

  function rowsOf(value: CaseRecord, key: Rows): Row[] {
    return (key === "observations" ? value.decision_time.observations : key === "hypotheses" ? value.hindsight.hypotheses : value.evidence) as unknown as Row[];
  }

  function rowTable(key: Rows, columns: readonly (readonly [string, string])[]) {
    if (!record) return null;
    return <><div className="tbl-wrap"><table><thead><tr>{columns.map(([field, label]) => <th key={field}>{label}</th>)}<th /></tr></thead><tbody>{rowsOf(record, key).map((row, index) => <tr key={index}>{columns.map(([field, label]) => <td key={field}><textarea aria-label={label} value={String(row[field] ?? "")} onChange={(event) => editCase((draft) => { rowsOf(draft, key)[index][field] = event.target.value; })} /></td>)}<td><button className="x" aria-label="Remove row" onClick={() => editCase((draft) => { rowsOf(draft, key).splice(index, 1); })}>×</button></td></tr>)}</tbody></table></div><div className="row-actions"><button className="btn small" onClick={() => editCase((draft) => { rowsOf(draft, key).push(Object.fromEntries(columns.map(([field]) => [field, ""]))); })}>+ Row</button></div></>;
  }

  function permissionField(signoff = false) {
    if (!record) return null;
    return <div className="q" style={signoff ? { maxWidth: 360 } : undefined}><label htmlFor={signoff ? "pu2" : "id_permitted_use"}>{signoff ? "Permitted use for this case" : "Permitted use"}</label>{signoff && <p className="hint">Training: may teach the model. Testing only: hidden from training, used to score it. Reference only: never used as data.</p>}<select id={signoff ? "pu2" : "id_permitted_use"} value={record.identity.permitted_use} onChange={(event) => editCase((draft) => { draft.identity.permitted_use = event.target.value as CaseRecord["identity"]["permitted_use"]; })}>{permissions.map((value) => <option key={value} value={value}>{value.replace(/_/g, " ")}</option>)}</select></div>;
  }

  return <fieldset className="capture-fields" aria-label="Case capture" aria-busy={signingOut} disabled={signingOut}><div className="app"><aside className="side">
    <div><div className="brand">Broadbridge Oil &amp; Gas</div><h1>Case capture</h1></div>
    <div className="account"><span>{email}</span><label htmlFor="theme">Theme</label><select id="theme" value={theme} onChange={(event) => setTheme(event.target.value as typeof theme)}><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></div>
    {onSignOut && <button type="button" className="btn small" disabled={signingOut || Boolean(deleting)} onClick={() => { void handleSignOut(); }}>{signingOut ? "Signing out…" : "Sign out"}</button>}
    <div className="nav" id="navTop"><a className="btn" href="/ingestion">Source intake &amp; review</a><a className="btn" href="/review/public-v1">Public-document scoring</a><button className={view === "about" ? "on" : ""} onClick={() => navigate("about")}><span className="t">Read this first</span></button><button className={view === "workflow" ? "on" : ""} onClick={() => navigate("workflow")}><span className="t">A · Your workflow</span><span className="pill">{Object.values(workflow.answers).filter((value) => value?.trim()).length}/10</span></button></div>
    <div className="sec-label">Cases</div><div className="nav" id="caseNav">{allCases.length ? allCases.map((item) => <button key={item.case_id} className={view === "case" && openId === item.case_id ? "on" : ""} onClick={() => navigate("case", item.case_id)}><span className="t">{item.case_id} {item.identity.title || "(untitled)"}</span><span className={`pill ${item.status}`}>{item.status}</span></button>) : <div className="muted" style={{ padding: "6px 10px" }}>No cases yet.</div>}</div>
    <button className="btn small" onClick={addCase}>+ New case</button><div className="sec-label">Export</div><div className="nav"><button className={view === "export" ? "on" : ""} onClick={() => { void showExport(); }} disabled={exporting}><span className="t">All records as JSON</span></button></div>
    <div className={`status ${errors.length ? "warn" : ""}`} role="status" aria-live="polite">{errors.length ? "Save failed. Your text is still in this tab." : saving ? "Saving…" : unsaved ? "Unsaved changes…" : saveStatus}</div>
  </aside><main id="main">
    {notice && <div className="banner" role="status">{notice}</div>}
    {errors.map(([key, item]) => <div className="banner" role="alert" key={key}><strong>{key === "workflow" ? "A · Your workflow" : (item.record as CaseRecord).case_id}: </strong>{item.error}{item.conflict ? <><p>This record changed elsewhere. Keep this tab open while you compare your text with the saved record in another tab. Reload to resolve the conflict before saving again.</p><button className="btn small" onClick={() => window.location.reload()}>Reload saved records</button></> : <div className="foot"><button className="btn small" onClick={() => { void flushKey(key, true); }}>Retry save</button></div>}</div>)}
    {view === "about" && <div dangerouslySetInnerHTML={{ __html: ABOUT_HTML }} />}
    {view === "workflow" && <><div className="head"><div><h2>A · Your workflow today</h2><p className="sub">Once. Where an engineer&apos;s time goes, and what a signable brief must contain.</p></div></div><div className="section">{PART_A.map(([number, label, hint]) => <QuestionField key={number} id={`wf_${number}`} number={number} label={label} hint={hint} value={workflow.answers[number] ?? ""} onChange={(value) => { const next = clone(entries.get("workflow")!.record as WorkflowRecord); next.answers[number] = value; next.updated_at = new Date().toISOString(); changed("workflow", next); }} />)}</div></>}
    {view === "export" && <><div className="head"><div><h2>All records</h2><p className="sub">{allCases.length} case(s). This is exactly what the training harness reads.</p></div></div><div className="foot" style={{ marginBottom: 12 }}><button className="btn small" onClick={() => { void copyJson(); }}>Copy JSON</button><span className="muted" role="status">{copyMessage}</span></div><pre ref={jsonElement}>{exportText}</pre></>}
    {view === "case" && record && <fieldset className="capture-fields" disabled={deleting === record.case_id}><div className="head"><div><h2>{record.case_id} {record.identity.title}</h2><p className="sub">Family <span style={{ fontFamily: "var(--mono)" }}>{record.family_id || record.case_id}</span> · updated {new Date(record.updated_at).toLocaleString()}</p></div><div className="case-actions"><select id="statusSel" className="btn small" aria-label="Status" value={record.status} onChange={(event) => setStatus(event.target.value as CaseRecord["status"])}>{["draft", "complete", "signed"].map((value) => <option key={value}>{value}</option>)}</select><button className="btn small" onClick={() => { void removeCase(record.case_id); }}>{deleting ? "Deleting…" : confirmDelete === record.case_id ? "Confirm delete" : "Delete"}</button></div></div>
      <div className="tabs" role="tablist">{TABS.map(([key, label]) => <button key={key} id={`tab-${key}`} role="tab" aria-selected={tab === key} aria-controls={`pane-${key}`} className={tab === key ? "on" : ""} onClick={() => { setTab(key); setCopyMessage(""); if (key === "signoff") void flushAll(); }}>{label}</button>)}</div>
      <div className="section" role="tabpanel" id={`pane-${tab}`} aria-labelledby={`tab-${tab}`}>
        {tab === "identity" && <><h3>Identity and permissions</h3><div className="grid2">{IDENTITY.map(([key, label, type, options]) => key === "permitted_use" ? <React.Fragment key={key}>{permissionField()}</React.Fragment> : <div className="q" key={key}><label htmlFor={`id_${key}`}>{label}</label>{type === "select" ? <select id={`id_${key}`} value={record.identity[key]} onChange={(event) => editCase((draft) => { draft.identity.record_type = event.target.value as CaseRecord["identity"]["record_type"]; })}>{options?.map((value) => <option key={value} value={value}>{value.replace(/_/g, " ")}</option>)}</select> : <input type="text" id={`id_${key}`} value={record.identity[key]} onChange={(event) => editCase((draft) => { (draft.identity as Record<string, string>)[key] = event.target.value; })} />}</div>)}</div><div className="q"><label htmlFor="fam">Family ID</label><p className="hint">Cases that are retellings or variants of the same incident share a family, so they never straddle train and test.</p><input type="text" id="fam" value={record.family_id} placeholder={record.case_id} onChange={(event) => editCase((draft) => { draft.family_id = event.target.value; })} /></div></>}
        {tab === "decision" && <><h3>What was known at decision time</h3>{DECISION.slice(0, 3).map(([key, number, label, hint]) => <QuestionField key={key} id={key} number={number} label={label} hint={hint} value={record.decision_time[key]} onChange={(value) => editCase((draft) => { draft.decision_time[key] = value; })} />)}<h3>B4 · Observations at decision time</h3><p className="hint muted">One row per measurement. Say whether pressures are gauge or absolute; give the basis of each value (tag, lab, operator report, estimate).</p>{rowTable("observations", OBS_COLS)}{DECISION.slice(3).map(([key, number, label, hint]) => <QuestionField key={key} id={key} number={number} label={label} hint={hint} value={record.decision_time[key]} onChange={(value) => editCase((draft) => { draft.decision_time[key] = value; })} />)}</>}
        {tab === "hindsight" && <><h3>B7 · Competing explanations</h3>{rowTable("hypotheses", HYP_COLS)}{HINDSIGHT.map(([key, number, label, hint]) => <QuestionField key={key} id={key} number={number} label={label} hint={hint} value={record.hindsight[key]} onChange={(value) => editCase((draft) => { draft.hindsight[key] = value; })} />)}</>}
        {tab === "evidence" && <><h3>B14 · Evidence you can share for this case</h3><p className="hint muted">Files are collected separately; list them here so we know what exists and its restrictions.</p>{rowTable("evidence", EVI_COLS)}</>}
        {tab === "questions" && <><h3>C · Test questions from this case (3–6)</h3><div className="types">{Q_TYPES.map(([key, title, description]) => <div key={key}><b>{title}</b>{description}</div>)}</div>{record.questions.length ? record.questions.map((question, index) => <div className="qcard" key={question.question_id}><div className="qh"><b>{question.question_id}</b><button className="btn small" onClick={() => editCase((draft) => { draft.questions.splice(index, 1); })}>Remove</button></div><div className="grid2"><div className="q"><label htmlFor={`q-${index}-type`}>Type</label><select id={`q-${index}-type`} value={question.type} onChange={(event) => editCase((draft) => { draft.questions[index].type = event.target.value as typeof question.type; })}>{Q_TYPES.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></div><div className="q"><label htmlFor={`q-${index}-split`}>Split</label><select id={`q-${index}-split`} value={question.split} onChange={(event) => editCase((draft) => { draft.questions[index].split = event.target.value as typeof question.split; })}>{["train", "dev", "locked_test"].map((value) => <option key={value} value={value}>{value.replace("_", " ")}</option>)}</select></div></div><QuestionField id={`q-${index}-question`} label="Question, as the engineer would ask it" value={question.question} onChange={(value) => editCase((draft) => { draft.questions[index].question = value; })} /><div className="q"><label htmlFor={`q-${index}-evidence`}>Evidence supplied with the question (IDs or descriptions)</label><input type="text" id={`q-${index}-evidence`} value={question.evidence_ids} onChange={(event) => editCase((draft) => { draft.questions[index].evidence_ids = event.target.value; })} /></div><QuestionField id={`q-${index}-reference`} label="Reference answer (Bill)" value={question.reference_answer} onChange={(value) => editCase((draft) => { draft.questions[index].reference_answer = value; })} /><div className="grid2"><div className="q"><label htmlFor={`q-${index}-tolerance`}>Numeric tolerance / units, if any</label><input type="text" id={`q-${index}-tolerance`} value={question.tolerance} onChange={(event) => editCase((draft) => { draft.questions[index].tolerance = event.target.value; })} /></div><div className="q"><label htmlFor={`q-${index}-hard-fail`}>Hard fail: an answer is wrong if it…</label><input type="text" id={`q-${index}-hard-fail`} value={question.hard_fail_criteria} onChange={(event) => editCase((draft) => { draft.questions[index].hard_fail_criteria = event.target.value; })} /></div></div></div>) : <p className="muted">No questions yet. Brad usually drafts these from section B; you correct the reference answer and set the tolerance.</p>}<div className="row-actions"><button className="btn small" onClick={() => editCase((draft) => { draft.questions.push({ question_id: `${draft.case_id}-Q-${crypto.randomUUID()}`, type: "brief", question: "", evidence_ids: "", reference_answer: "", tolerance: "", hard_fail_criteria: "", split: "dev" }); })}>+ Question</button></div></>}
        {tab === "signoff" && <><h3>Reviewer sign-off</h3>{permissionField(true)}<p className="muted">Ticking this marks the written record as reviewed and usable as marked above. You can untick it at any time.</p><label className="chk"><input type="checkbox" id="signed" checked={record.reviewer_signoff.signed} onChange={(event) => setSigned(event.target.checked)} /><span>I have reviewed this case record. It is accurate to the best of my knowledge, contains nothing I am not permitted to share, and may be used as marked.</span></label><div className="grid2"><div className="q"><label htmlFor="sname">Name</label><input type="text" id="sname" value={record.reviewer_signoff.name} onChange={(event) => editCase((draft) => { draft.reviewer_signoff.name = event.target.value; })} /></div><div className="q"><label htmlFor="sdate">Date</label><input type="text" id="sdate" value={record.reviewer_signoff.date} placeholder="YYYY-MM-DD" onChange={(event) => editCase((draft) => { draft.reviewer_signoff.date = event.target.value; })} /></div></div><h3>This record as JSON</h3>{unsaved || errors.length ? <p className="muted">Save pending. JSON is available once all changes are saved.</p> : <pre id="caseJson" ref={jsonElement}>{JSON.stringify(record, null, 2)}</pre>}<div className="foot"><button className="btn small" onClick={() => { void copyJson(record.case_id); }}>Copy JSON</button><span className="muted" role="status">{copyMessage}</span></div></>}
      </div></fieldset>}
  </main></div></fieldset>;
}
