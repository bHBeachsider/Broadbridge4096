"use client";
import { startTransition, useEffect, useRef, useState } from "react";
import { saveQuestionnaire } from "../app/questionnaires/pressure-training-v1/actions";
import { answered, criticalOptions, emptyResponse, importance, inclusions, questionnaire, questionnairePath, verdicts, type Answer, type QuestionnaireResponse, type SavedQuestionnaire } from "../lib/questionnaire";
import styles from "./TrainingQuestionnaire.module.css";

type Question = typeof questionnaire.questions[number];
function PressureGraphic({kind}: {kind: string | null | undefined}) {
  if (!kind) return null;
  if (kind === "references") return <figure className={styles.graphic}><div className={styles.pair}><div><strong>30 psia</strong><span>Reference: absolute vacuum</span></div><div><strong>30 psig</strong><span>Reference: atmosphere</span></div></div><figcaption>Same numerical reading; different reference points.</figcaption></figure>;
  const vacuum = kind === "vacuum", below = vacuum || kind === "negative_gauge";
  const label = vacuum ? "Positive vacuum depression" : below ? "Negative gauge difference" : "Positive gauge difference";
  return <figure className={styles.graphic}><svg viewBox="0 0 640 225" role="img" aria-label={`${label}. Measured pressure is ${below ? "below" : "above"} atmosphere.`}>
    <line x1="35" y1="105" x2="605" y2="105"/>{[35,300,520].map(x => <line key={x} x1={x} y1="90" x2={x} y2="125"/>)}
    <text x="35" y="163">0 psia</text><text x="35" y="196" style={{fontSize:20}}>Absolute vacuum</text>
    <text x="300" y="163" textAnchor="middle">{below ? "Measured" : "Atmosphere"}</text><text x="520" y="163" textAnchor="middle">{below ? "Atmosphere" : "Measured"}</text>
    <path d="M300 70 V55 H520 V70" fill="none"/><text x="410" y="30" textAnchor="middle" style={{fontSize:23}}>{label}</text>
  </svg><figcaption>Schematic, not to scale. Pressure increases to the right.</figcaption></figure>;
}

export default function TrainingQuestionnaire({actor, initial, hash}: {actor: string; initial: SavedQuestionnaire | null; hash: string}) {
  const [record, setRecord] = useState<QuestionnaireResponse>(() => initial?.record ?? emptyResponse(hash));
  const current = useRef(record), acknowledged = useRef(record), revision = useRef(initial?.revision ?? null);
  const blocked = useRef(false), inFlight = useRef<Promise<void> | null>(null), mounted = useRef(true);
  const [section, setSection] = useState(0), [busy, setBusy] = useState(false), [dirty, setDirty] = useState(false);
  const [conflict, setConflict] = useState(false), [message, setMessage] = useState(initial ? `Saved ${initial.record.state} · revision ${initial.revision}` : "Enter responses to start a draft.");
  const count = Object.values(record.answers).filter(answered).length;
  useEffect(() => { mounted.current = true; return () => { mounted.current = false; }; }, []);
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => { if (current.current !== acknowledged.current) { event.preventDefault(); event.returnValue = ""; } };
    window.addEventListener("beforeunload", warn); return () => window.removeEventListener("beforeunload", warn);
  }, []);
  function update(next: QuestionnaireResponse) { current.current = next; setRecord(next); setDirty(true); if (!blocked.current) setMessage("Unsaved changes…"); }
  function change(id: string, field: keyof Answer, value: string) {
    update({...current.current, state: "draft", answers: {...current.current.answers, [id]: {...current.current.answers[id], [field]: value}}});
  }
  async function flush() {
    if (inFlight.current) return inFlight.current;
    if (blocked.current) return;
    setBusy(true);
    const task = (async () => {
      while (mounted.current && current.current !== acknowledged.current && !blocked.current) {
        const snapshot = current.current;
        try {
          const result = await saveQuestionnaire({record: snapshot, expected_revision: revision.current});
          if (!mounted.current) return;
          if (!result.ok) { blocked.current = true; setConflict(result.conflict); setMessage(result.message); return; }
          revision.current = result.value.revision; acknowledged.current = snapshot;
          setDirty(current.current !== snapshot);
          setMessage(`${result.value.record.state === "submitted" ? "Feedback submitted" : "Draft saved"} · revision ${result.value.revision}`);
        } catch {
          if (mounted.current) { blocked.current = true; setMessage("Save unavailable. Your text remains in this tab. Retry or download this draft."); }
          return;
        }
      }
    })();
    inFlight.current = task;
    try { await task; } finally { inFlight.current = null; if (mounted.current) setBusy(false); }
  }
  useEffect(() => {
    if (record === acknowledged.current || blocked.current) return;
    const timer = setTimeout(() => startTransition(() => { void flush(); }), 1200);
    return () => clearTimeout(timer);
  }, [record]); // Each edit schedules a save; flush serializes snapshots and revisions.
  function saveNow(submit = false) {
    if (conflict) return;
    blocked.current = false;
    if (submit) update({...current.current, state: "submitted"});
    startTransition(() => { void flush(); });
  }
  function downloadDraft() {
    const blob = new Blob([JSON.stringify({schema: "broadbridge.training_questionnaire_local_copy/1", exported_at: new Date().toISOString(), last_saved_revision: revision.current, unsaved_changes: current.current !== acknowledged.current, record: current.current}, null, 2)], {type: "application/json"});
    const url = URL.createObjectURL(blob), a = document.createElement("a"); a.href = url; a.download = "broadbridge-training-review-draft.json"; a.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function topic(index: number) { setSection(index); window.scrollTo({top: 0}); requestAnimationFrame(() => document.getElementById("topic-heading")?.focus()); }
  function field(q: Question, name: keyof Answer, label: string, hint = "") {
    return <div className={styles.field}><label htmlFor={`${q.id}-${name}`}>{label}</label>{hint && <p className={styles.muted}>{hint}</p>}<textarea id={`${q.id}-${name}`} value={record.answers[q.id]?.[name] ?? ""} maxLength={8000} onChange={e => change(q.id, name, e.target.value)}/></div>;
  }
  function choice(q: Question, name: keyof Answer, label: string, options: readonly (readonly [string,string])[]) {
    return <div className={styles.field}><label htmlFor={`${q.id}-${name}`}>{label}</label><select id={`${q.id}-${name}`} value={record.answers[q.id]?.[name] ?? ""} onChange={e => change(q.id, name, e.target.value)}><option value="">Choose…</option>{options.map(([value, text]) => <option key={value} value={value}>{text}</option>)}</select></div>;
  }
  const category = questionnaire.categories[section];
  return <div className={styles.root}>
    <header className={styles.header}><div><p className="brand">BROADBRIDGE / ENGINEERING TRAINING REVIEW</p><p className={styles.muted}>Signed in as {actor}</p></div><a className="btn" href="/">Case capture</a><a className="btn" href="/review/public-v1">Public-document scoring</a></header>
    <div className={styles.shell}><aside className={styles.sidebar}><nav aria-label="Questionnaire topics">{questionnaire.categories.map((c,i) => <button key={c.id} type="button" aria-current={i===section ? "page" : undefined} onClick={() => topic(i)}>{i+1}. {c.title}</button>)}</nav><label className={styles.mobile} htmlFor="questionnaire-topic">Choose a topic<select id="questionnaire-topic" aria-label="Choose a topic" value={section} onChange={e => topic(Number(e.target.value))}>{questionnaire.categories.map((c,i) => <option key={c.id} value={i}>{i+1}. {c.title}</option>)}</select></label><p>{count} of {questionnaire.questions.length} questions have a response</p><progress value={count} max={questionnaire.questions.length} aria-label="Questions with a response"/><p className={styles.muted}>Responses autosave to Broadbridge. Submit feedback when the review is ready.</p></aside>
    <main className={styles.main}>{section === 0 && <div className={styles.intro}><h1>{questionnaire.title}</h1><p>{questionnaire.introduction}</p><p className={styles.muted}>{questionnaire.estimated_time}</p></div>}
      <h2 id="topic-heading" tabIndex={-1}>{category.title}</h2><p className={styles.muted}>{category.intro}</p>
      {questionnaire.questions.filter(q => q.category === category.id).map(q => <article key={q.id} className={styles.card} aria-labelledby={`title-${q.id}`}><p className={styles.id}>{q.id}</p><h3 id={`title-${q.id}`}>{q.title}</h3><p className={styles.scenario}>{q.question}</p><PressureGraphic kind={q.graphic}/>
        {q.kind === "open" ? field(q,"answer","Response",q.help) : <>
          <details><summary>Read the source notes</summary><p>{q.evidence_note}</p><a href={q.source_url} target="_blank" rel="noopener noreferrer">{q.source_label}</a></details>
          {field(q,"expectation","What should a good answer say or ask?",q.help)}
          <details onToggle={e => { if (e.currentTarget.open && !current.current.answers[q.id]?.reference_seen_at) change(q.id, "reference_seen_at", new Date().toISOString()); }}><summary>Compare with our draft answer</summary><div className={styles.reference}><p className={styles.muted}>Authored reference — not a generated Qwen answer</p><p>{q.reference_answer}</p><p><strong>Proposed serious error:</strong> {q.hard_fail_criteria}</p><p>{q.tolerance}</p></div>{choice(q,"verdict","How would you assess this draft?",verdicts)}{field(q,"correction","Correction or qualification")}</details>
          <div className={styles.pair}>{choice(q,"include","Does this task belong in the first set?",inclusions)}{choice(q,"critical","Could a wrong answer cause a serious error?",criticalOptions)}</div>
          <details><summary>Refine the checks we should use</summary><p className={styles.muted}>Mark the requirements to use when evaluating model answers.</p>{q.requirements?.map((r,i) => <div key={r}>{choice(q,`requirement${i}` as keyof Answer,r,importance)}</div>)}</details>
        </>}
        <p className={styles.muted}>Purpose: {q.why}</p>
      </article>)}
      <div className={styles.buttons}><button className="btn" disabled={section===0} onClick={() => topic(section-1)}>Previous topic</button>{section < questionnaire.categories.length-1 && <button className="btn primary" onClick={() => topic(section+1)}>Next topic</button>}</div>
      <section className={styles.save} aria-label="Save review"><p role="status" aria-live="polite">{busy ? "Saving…" : message}</p><div className={styles.buttons}><button className="btn" disabled={busy || conflict || !dirty} onClick={() => saveNow()}>Save now / retry</button><button className="btn primary" disabled={busy || conflict || count===0 || (!dirty && record.state==="submitted")} onClick={() => saveNow(true)}>Submit feedback</button><button className="btn" onClick={downloadDraft}>Download this draft</button>{!dirty && revision.current && <a className="btn" href={`${questionnairePath}/responses`}>Download saved responses</a>}</div><p className={styles.muted}>Feedback defines tasks and evaluation criteria. Submitting does not sign a case or grant training rights. Further edits create a new draft revision.</p></section>
    </main></div>
  </div>;
}
