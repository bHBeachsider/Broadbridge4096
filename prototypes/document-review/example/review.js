"use strict";
(() => {
  const report = JSON.parse(document.getElementById("report-data").textContent);
  const $ = id => document.getElementById(id);
  const statuses = {pending: "Pending", confirmed: "Confirmed discrepancy", dismissed: "Dismissed", needs_information: "Needs information"};
  const key = "broadbridge-document-review:" + report.report_id;
  const state = {reviewer: "", findings: {}};
  let persistence = true;
  const el = (tag, text, cls) => {
    const node = document.createElement(tag);
    if (text !== undefined) node.textContent = text;
    if (cls) node.className = cls;
    return node;
  };
  const identity = evidence => JSON.stringify([evidence.document_key, evidence.locator]);
  const sourceNodes = new Map();
  try {
    const saved = JSON.parse(localStorage.getItem(key) || "null");
    if (saved && saved.report_id === report.report_id && saved.findings && typeof saved.findings === "object") {
      state.reviewer = typeof saved.reviewer === "string" ? saved.reviewer.slice(0,160) : "";
      for (const finding of report.findings) {
        const row = saved.findings[finding.id];
        if (row && Object.hasOwn(statuses, row.disposition) && typeof row.notes === "string") {
          state.findings[finding.id] = {disposition: row.disposition, notes: row.notes.slice(0,4000)};
        }
      }
    }
  } catch { persistence = false; }
  const noteFor = f => state.findings[f.id] || {disposition: "pending", notes: ""};
  const storageMessage = () => {
    $("storage-status").textContent = persistence
      ? "Notes stay in this browser. Export a copy to keep or share them."
      : "Browser storage is unavailable: notes are not saved after closing this page. Export before leaving.";
  };
  function save() {
    try {
      localStorage.setItem(key, JSON.stringify({report_id: report.report_id, ...state}));
      persistence = true;
    } catch { persistence = false; }
    storageMessage();
    updateCount();
  }
  function showSource(evidence) {
    for (const n of document.querySelectorAll(".highlight")) n.classList.remove("highlight");
    const node = sourceNodes.get(identity(evidence));
    if (!node) return;
    node.closest("details").open = true;
    node.classList.add("highlight");
    node.tabIndex = -1;
    node.focus({preventScroll: true});
    node.scrollIntoView({block: "center", behavior: "instant"});
  }
  function evidenceButton(evidence) {
    const button = el("button", evidence.document_id + " rev " + evidence.revision + " · " + evidence.locator, "evidence-link");
    button.type = "button";
    button.addEventListener("click", () => showSource(evidence));
    return button;
  }
  for (const doc of report.documents) {
    const details = el("details", undefined, "source");
    const summary = el("summary");
    summary.append(el("strong", doc.document_id + " / " + doc.revision), el("span", doc.file + " — " + doc.status));
    details.append(summary, el("p", "SHA-256 " + doc.sha256, "hash"));
    const records = el("div", undefined, "source-records");
    for (const row of doc.records) {
      const node = el("article", undefined, "source-record");
      node.append(el("h3", row.locator));
      const dl = el("dl");
      for (const [field, value] of Object.entries(row.values)) {
        dl.append(el("dt", field.replaceAll("_", " ")), el("dd", value || "(empty)"));
      }
      node.append(dl);
      sourceNodes.set(identity({document_key: doc.document_key, locator: row.locator}), node);
      records.append(node);
    }
    details.append(records);
    $("sources").append(details);
  }
  $("run-meta").append(el("strong", report.package.package_id), el("span", report.rules_version),
    el("span", "Run " + report.report_id.slice(0,12)));
  const metrics = [
    ["Registered assets", report.summary.assets],
    ["Approved documents", report.summary.current_documents],
    ["Findings to review", report.summary.findings],
    ["Need clarification", report.summary.needs_review]
  ];
  for (const [label,value] of metrics) $("metrics").append(el("dt",label), el("dd",String(value)));
  const drawing = report.documents.find(d => d.kind === "drawing" && d.status === "approved");
  for (const row of drawing.records) {
    const tag = row.values.tag;
    const count = report.findings.filter(f => f.tag.split("|").includes(tag)).length;
    const button = el("button", undefined, "asset" + (count ? " flagged" : ""));
    button.type = "button";
    button.append(el("strong",tag), el("span",count ? count + " finding" + (count === 1 ? "" : "s") : "No finding"));
    button.addEventListener("click", () => {
      $("search").value = tag; $("category").value = "all"; $("disposition").value = "all";
      renderFindings();
      $("findings-title").scrollIntoView({block:"start",behavior:"instant"});
    });
    $("diagram").append(button);
  }
  for (const item of report.not_compared) {
    const box = el("div", undefined, "comparison-note");
    box.append(el("strong", item.tag + " · comparison held"),
      el("p", "Operating and design/test conditions differ or are unspecified. No numerical conflict is inferred."));
    for (const evidence of item.evidence) box.append(evidenceButton(evidence));
    $("conditions").append(box);
  }
  function updateCount() {
    const completed = report.findings.filter(f => noteFor(f).disposition !== "pending").length;
    $("result-count").textContent = $("findings").querySelectorAll(".finding").length +
      " of " + report.findings.length + " shown · " + completed + " with a review disposition";
  }
  function renderFindings() {
    const query = $("search").value.trim().toLowerCase();
    const category = $("category").value, status = $("disposition").value;
    $("findings").replaceChildren();
    for (const finding of report.findings) {
      const note = noteFor(finding);
      if (query && ![finding.tag,finding.field,finding.rule,finding.message].join(" ").toLowerCase().includes(query)) continue;
      if (category !== "all" && finding.category !== category) continue;
      if (status !== "all" && note.disposition !== status) continue;
      const card = el("article", undefined, "finding");
      const top = el("div", undefined, "finding-top");
      top.append(el("h3",finding.tag), el("span", finding.category === "needs_review" ? "Needs clarification" : "Document discrepancy", "category"));
      card.append(top, el("p", finding.message, "finding-message"));
      const comparison = el("div", undefined, "evidence-list");
      for (const evidence of finding.evidence) {
        const block = el("div", undefined, "evidence");
        block.append(evidenceButton(evidence));
        const values = evidence.values;
        let shown;
        if (finding.field === "pressure" || finding.field === "temperature") {
          shown = [values[finding.field],values[finding.field+"_unit"],values[finding.field+"_basis"],values.condition].filter(v=>v).join(" · ");
        } else {
          shown = values[finding.field] ?? values.tag ?? values.asset_tags ?? values.status ?? "";
        }
        block.append(el("p", shown || "(empty)", "observed"));
        comparison.append(block);
      }
      card.append(comparison);
      const controls = el("div", undefined, "finding-review");
      const choiceWrap = el("div");
      const label = el("label","Disposition for " + finding.tag);
      label.htmlFor = "status-" + finding.id;
      const select = el("select"); select.id = label.htmlFor;
      for (const [value,text] of Object.entries(statuses)) {
        const option = el("option",text); option.value = value; select.append(option);
      }
      select.value = note.disposition;
      choiceWrap.append(label,select);
      const notesWrap = el("div");
      const notesLabel = el("label","Notes for " + finding.tag); notesLabel.htmlFor = "notes-" + finding.id;
      const notes = el("textarea"); notes.id = notesLabel.htmlFor; notes.rows = 2; notes.maxLength = 4000;
      notes.placeholder = "Evidence, correction or follow-up needed"; notes.value = note.notes;
      notesWrap.append(notesLabel,notes);
      const changed = () => {
        state.findings[finding.id] = {disposition:select.value,notes:notes.value};
        save();
      };
      select.addEventListener("change",()=>{ changed(); if ($("disposition").value !== "all") renderFindings(); });
      notes.addEventListener("input",changed);
      controls.append(choiceWrap,notesWrap);
      card.append(controls, el("small",finding.rule + " · " + finding.rule_version + " · " + finding.id,"rule"));
      $("findings").append(card);
    }
    if (!$("findings").children.length) $("findings").append(el("p","No findings match these filters. Clear filters to see the full register.","empty"));
    updateCount();
  }
  $("reviewer").value = state.reviewer;
  $("reviewer").addEventListener("input",()=>{state.reviewer=$("reviewer").value;save();});
  $("search").addEventListener("input",renderFindings);
  for (const name of ["category","disposition"]) $(name).addEventListener("change",renderFindings);
  $("clear").addEventListener("click",()=>{
    $("search").value="";$("category").value="all";$("disposition").value="all";renderFindings();
  });
  $("export").addEventListener("click",()=>{
    const exported = {schema:"broadbridge.document_review_notes/1",report_id:report.report_id,
      package_id:report.package.package_id,synthetic:true,engineering_signoff:false,
      exported_at:new Date().toISOString(),reviewer:state.reviewer,
      findings:report.findings.map(f=>({finding_id:f.id,rule:f.rule,tag:f.tag,field:f.field,
        ...noteFor(f),evidence:f.evidence.map(e=>({document_key:e.document_key,locator:e.locator,sha256:e.sha256}))}))};
    const url=URL.createObjectURL(new Blob([JSON.stringify(exported,null,2)+"\n"],{type:"application/json"}));
    const link=el("a");link.href=url;link.download="review_notes_"+report.package.package_id+"_"+report.report_id.slice(0,12)+".json";
    document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
  });
  renderFindings();storageMessage();
})();
