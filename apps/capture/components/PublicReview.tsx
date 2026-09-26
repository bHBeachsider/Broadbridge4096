"use client";
import { useEffect,useState } from "react";
import { savePublicScore } from "../app/review/actions";
import { rubrics,scoreInputSchema,validateScoreForItem,type PublicReviewPacket,type SavedScore } from "../lib/public-review";

export default function PublicReview({packet,hash,actor,initialIndex,scores}:{packet:PublicReviewPacket;hash:string;actor:string;initialIndex:number;scores:SavedScore[]}) {
  // Delegate so changing the selected item remounts its form without stale fields.
  return <ReviewWorkspace packet={packet} hash={hash} actor={actor} initialIndex={initialIndex} scores={scores}/>;
}
function ReviewWorkspace({packet,hash,actor,initialIndex,scores:initialScores}:{packet:PublicReviewPacket;hash:string;actor:string;initialIndex:number;scores:SavedScore[]}){
  const [index,setIndex]=useState(initialIndex);
  const [scores,setScores]=useState(initialScores);
  const [dirty,setDirty]=useState(false);
  const item=packet.items[index];
  const saved=scores.find(s=>s.question_id===item.question_id&&s.response_label===item.response_label);
  const source=packet.sources.find(s=>s.source_id===item.source_id)!;
  const path=(n:number)=>`/review/${packet.packet_id}?question=${packet.items[n].question_id}&response=${packet.items[n].response_label}`;
  function choose(next:number){if(dirty)return;setIndex(next);window.history.replaceState(null,"",path(next));}
  useEffect(()=>{const protect=(event:BeforeUnloadEvent)=>{if(dirty){event.preventDefault();event.returnValue="";}};window.addEventListener("beforeunload",protect);return()=>window.removeEventListener("beforeunload",protect);},[dirty]);
  const answered=packet.items.filter(i=>i.answer!==null).length;
  return <main className="review-shell">
    <header><p className="brand">BROADBRIDGE / TECHNICAL REVIEW</p><h1>{packet.title}</h1>
      <p>Read the source, question and frozen answer. Record your judgment; no model is called here.</p>
      <nav className="review-links"><a href="/">Case capture</a><a href="/ingestion">Source intake</a><a href={`/review/${packet.packet_id}/scores`}>Download my scores (CSV)</a></nav>
    </header>
    <section className="review-panel" aria-label="Your review progress">
      <strong>{scores.length} / {packet.items.length} scored by {actor}</strong>
      <p>{answered} returned answers · {packet.items.length-answered} unavailable · {scores.filter(s=>s.critical_error).length} critical errors recorded</p>
      <p className="muted">Scores belong to your signed-in account. Brad’s screening and Bill’s technical review remain separate. These testing-only source families and scores cannot approve training.</p>
      <details><summary>Mean scores by question type (partial until every item is reviewed)</summary><table><thead><tr><th>Type</th><th>Scored / total</th><th>Mean / 2</th><th>Critical</th></tr></thead><tbody>{Object.keys(rubrics).map(type=>{const items=packet.items.filter(i=>i.type===type);const reviewed=scores.filter(s=>items.some(i=>i.question_id===s.question_id&&i.response_label===s.response_label));return <tr key={type}><td>{type.replaceAll("_"," ")}</td><td>{reviewed.length} / {items.length}</td><td>{reviewed.length?(reviewed.reduce((n,s)=>n+s.score,0)/reviewed.length).toFixed(2):"Unreviewed"}</td><td>{reviewed.filter(s=>s.critical_error).length}</td></tr>;})}</tbody></table></details>
    </section>
    <section className="review-controls" aria-label="Select response">
      <button className="btn" disabled={dirty||index===0} onClick={()=>choose(index-1)}>Previous</button>
      <label>Question / response<select aria-label="Question / response" value={index} disabled={dirty} onChange={e=>choose(Number(e.target.value))}>{packet.items.map((i,n)=><option key={i.question_id+i.response_label} value={n}>{i.question_id} · {i.response_label} · {i.type.replaceAll("_"," ")} · {scores.some(s=>s.question_id===i.question_id&&s.response_label===i.response_label)?"scored":"unreviewed"}</option>)}</select></label>
      <button className="btn" disabled={dirty||index===packet.items.length-1} onClick={()=>choose(index+1)}>Next</button>
      <a href={path(index)} onClick={e=>{if(dirty)e.preventDefault();}}>Link to this response</a>
      {dirty&&<p role="status">Save or discard your changes before switching responses.</p>}
    </section>
    <div className="review-grid">
      <section className="review-panel" aria-label="Source evidence"><h2>{source.title}</h2><p><a href={source.url} target="_blank" rel="noreferrer">Original document · {source.publisher}</a></p><p className="muted">{source.context}</p>{source.blocks.map(block=><section key={block.block_id}><h3 className="review-block-id">{block.block_id}</h3><p className="review-text">{block.text}</p></section>)}</section>
      <section className="review-panel" aria-label="Question and score"><p className="brand">{item.question_id} / {item.type.replaceAll("_"," ")}</p><h2>{item.question}</h2>
        <h3>Response {item.response_label}</h3>{item.answer?<><p className="review-text">{item.answer.answer}</p>{item.answer.uncertainties.length>0&&<><h4>Stated uncertainties</h4><ul>{item.answer.uncertainties.map((v,n)=><li key={n}>{v}</li>)}</ul></>}<details><summary>Answer’s citations</summary>{item.answer.evidence.map((e,n)=><blockquote key={n}><strong>{e.source_id} / {e.block_id}</strong><p>{e.quote}</p></blockquote>)}</details></>:<p className="review-unavailable">No answer was returned for this slot. Leave it unreviewed, or record 0 / no critical error with an explanation. Do not infer an answer.</p>}
        <details><summary>Draft reference answer and tolerance</summary><p>Reviewer aid, not an approved engineering answer. Record corrections or a defective question in your notes; the frozen reference stays unchanged.</p><p className="review-text">{item.reference_answer}</p><pre className="review-text">{item.tolerance}</pre></details>
        <h3>Critical-error criteria</h3><p className="review-text">{item.hard_fail_criteria}</p><p>Any matched criterion requires 0 / critical error Yes. Flag other material unsafe or fabricated claims too.</p>
        <details><summary>Mechanical flags (not engineering grades)</summary><ul>{(item.checks.length?item.checks:["No flags recorded / not assessed"]).map((flag,n)=><li key={n}>{flag}</li>)}</ul></details>
        <ScoreForm key={index} packetId={packet.packet_id} hash={hash} item={item} saved={saved} dirty={dirty} setDirty={setDirty} onSaved={next=>{setScores(old=>[...old.filter(s=>s.question_id!==next.question_id||s.response_label!==next.response_label),next]);setDirty(false);}}/>
      </section>
    </div>
    <p className="muted review-digest">Frozen packet SHA-256: {hash}. Model names remain masked as A/B; labels switch between source documents.</p>
  </main>;
}
function ScoreForm({packetId,hash,item,saved,dirty,setDirty,onSaved}:{packetId:string;hash:string;item:PublicReviewPacket["items"][number];saved?:SavedScore;dirty:boolean;setDirty:(dirty:boolean)=>void;onSaved:(score:SavedScore)=>void}){
  const [score,setScore]=useState(saved?String(saved.score):"");
  const [critical,setCritical]=useState(saved?String(saved.critical_error):"");
  const [hardFail,setHardFail]=useState(saved?String(saved.hard_fail):"");
  const [notes,setNotes]=useState(saved?.notes??"");
  const [busy,setBusy]=useState(false);const [message,setMessage]=useState("");
  function reset(){setScore(saved?String(saved.score):"");setCritical(saved?String(saved.critical_error):"");setHardFail(saved?String(saved.hard_fail):"");setNotes(saved?.notes??"");setDirty(false);setMessage("");}
  return <form className="review-form" onSubmit={async event=>{
    event.preventDefault();setMessage("");
    if(score===""||critical===""||hardFail===""){setMessage("Choose a score, a critical-error decision and a hard-fail decision.");return;}
    const parsed=scoreInputSchema.safeParse({packet_id:packetId,packet_sha256:hash,question_id:item.question_id,response_label:item.response_label,score:Number(score),critical_error:critical==="true",hard_fail:hardFail==="true",notes,expected_revision:saved?.revision??null});
    if(!parsed.success){setMessage("Add evidence in notes. A critical error or matched hard-fail requires score 0 and critical error Yes.");return;}
    try{validateScoreForItem(parsed.data,item);}catch(error){setMessage((error as Error).message);return;}
    setBusy(true);
    try{const result=await savePublicScore(parsed.data);if(result.ok){onSaved(result.saved);setMessage("Score saved.");}else setMessage(result.message);}catch{setMessage("Score not saved. Your notes remain in this tab; retry when connected.");}finally{setBusy(false);}
  }}>
    <h3>Your assessment</h3><ol start={0}>{rubrics[item.type].map((r,n)=><li key={r}>{r}</li>)}</ol>
    <fieldset disabled={busy}><legend className="sr-only">Score this response</legend>
      <label>Score<select aria-label="Score" value={score} required onChange={e=>{setScore(e.target.value);setDirty(true);}}><option value="">Choose…</option>{[0,1,2].map(n=><option key={n} value={n}>{n} / 2</option>)}</select></label>
      <label>Critical error<select aria-label="Critical error" value={critical} required onChange={e=>{setCritical(e.target.value);setDirty(true);}}><option value="">Choose…</option><option value="false">No</option><option value="true">Yes</option></select></label>
      <label>Any hard-fail criterion matched?<select aria-label="Any hard-fail criterion matched?" value={hardFail} required onChange={e=>{setHardFail(e.target.value);setDirty(true);}}><option value="">Choose…</option><option value="false">No</option><option value="true">Yes</option></select></label>
      <label>Evidence, corrections and notes<textarea rows={5} required maxLength={8000} value={notes} onChange={e=>{setNotes(e.target.value);setDirty(true);}}/></label>
      <button className="btn primary" type="submit" disabled={!dirty}>{busy?"Saving…":"Save score"}</button>{dirty&&<button className="btn" type="button" onClick={reset}>Discard changes</button>}
    </fieldset><p role="status" aria-live="polite">{message}</p>{saved&&<p className="muted">Saved by {saved.reviewer} · {saved.review_date} · revision {saved.revision}</p>}
  </form>;
}
