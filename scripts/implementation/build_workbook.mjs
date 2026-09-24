import fs from 'node:fs/promises';
import path from 'node:path';
import {Workbook,SpreadsheetFile} from '@oai/artifact-tool';

const root=path.resolve(import.meta.dirname,'../..');
const out=path.join(root,'output/multimodal-implementation');
const qa=path.join(root,'tmp/implementation-qa');
const data=JSON.parse(await fs.readFile(path.join(out,'implementation_data.json'),'utf8'));
const tasks=data.tasks,n=tasks.length,last=n+5,weeks=36;
const wb=Workbook.create();
const names=['AWS start','Start here','Gantt','Tasks','Task detail','Source routing','Processing recipes','Capacity','Weekly effort','References'];
const sheets=Object.fromEntries(names.map(n=>[n,wb.worksheets.add(n)]));
const navy='#18364D',pale='#EDF2F5',amber='#FFF2CC';
function clean(s){return typeof s==='string'?s.replace(/([a-z])(?=\d)/g,'$1 ').replace(/(?<=\d)(?=[a-z])/g,' ').replace(/Qwen 3/g,'Qwen3').replace(/p 95/g,'p95').replace(/(\d) e([+-]\d)/g,'$1e$2').replaceAll('g 6 e.2 xlarge','g6e.2xlarge').replaceAll('G6 e','G6e').replaceAll('gp 3','gp3').replaceAll('s 3://','s3://').replaceAll('IMDSv 2','IMDSv2'):s;}
function col(n){let s='';for(n++;n;n=Math.floor((n-1)/26))s=String.fromCharCode(65+(n-1)%26)+s;return s;}
function init(name,title,subtitle,headers,widths,rows,height=60){
 const s=sheets[name],end=col(headers.length-1),bottom=rows.length+5;
 s.showGridLines=false;
 s.getRange(`A1:${end}${bottom}`).format.font={name:'Arial',size:10,color:'#202020'};
 s.getRange('A1').values=[[title]];s.getRange('A1').format.font={name:'Arial',size:17,bold:true,color:'#000000'};
 s.getRange('A1').format.rowHeight=27;
 s.getRange('A2').values=[[clean(subtitle)]];s.getRange('A2').format.font={italic:true,size:10,color:'#404040'};
 s.getRange('A2').format.rowHeight=28;
 s.getRange(`A5:${end}5`).values=[headers];
 s.getRange(`A5:${end}5`).format={fill:navy,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},wrapText:true,rowHeight:38,verticalAlignment:'center'};
 if(rows.length){s.getRange(`A6:${end}${bottom}`).values=rows;s.getRange(`A6:${end}${bottom}`).format.wrapText=true;s.getRange(`A6:${end}${bottom}`).format.verticalAlignment='top';s.getRange(`A6:${end}${bottom}`).format.rowHeight=height;}
 widths.forEach((v,i)=>s.getRange(`${col(i)}1:${col(i)}${bottom}`).format.columnWidth=v);
 for(let r=6;r<=bottom;r++)if(r%2===0)s.getRange(`A${r}:${end}${r}`).format.fill=pale;
 s.freezePanes.freezeRows(5);s.freezePanes.freezeColumns(name==='Gantt'?3:1);
 return s;
}

const aws=init('AWS start','Start by running the foundation in AWS','Begin at step 1. These steps map to Tasks; effort is already included there. Commands are in runbook AWS 2 through AWS 5.',
 ['Step','Task IDs','Action','Lead','How to do it','Completion evidence','Runbook section'],[8,26,43,30,94,72,17],data.aws_rows,105);
aws.tables.add(`A5:G${data.aws_rows.length+5}`,true,'AWSExecutionSteps');
const start=sheets['Start here'];start.showGridLines=false;
start.getRange('A1:D34').format.font={name:'Arial',size:11,color:'#202020'};
start.getRange('A1').values=[['Broadbridge multimodal implementation']];start.getRange('A1').format.font={size:18,bold:true};
start.getRange('A2').values=[['Read AWS start first then use this sheet to set the schedule']];
start.getRange('A4:C4').values=[['Input or result','Value','Meaning']];start.getRange('A4:C4').format={fill:navy,font:{color:'#FFFFFF',bold:true},rowHeight:28};
start.getRange('A5:C12').values=[['Approved kickoff',null,'Enter an Excel date. Blank means relative working-day schedule only.'],['Task count',n,'Includes six delivery gates. Every status starts at Not started.'],['Finish working day',null,'Calculated from all task dependencies and resource-level baseline holds.'],['Planned weeks',null,'Five working days per week; holidays excluded from this model.'],['Earlier target weeks',24,'Earlier CTO target. Detailed dependencies and resource reservations revise timing.'],['Difference in weeks',null,'The earlier 24-week budget and eight-week first tranche must be rebaselined.'],['Schedule buffer display',weeks,'Gantt shows36 weeks. If tasks extend past week36, extend the displayed columns.'],['Dates recalculated',null,'Finish date stays blank until an approved kickoff is entered.']];
start.getRange('B5').format.fill=amber;start.getRange('B5').setNumberFormat('yyyy-mm-dd');
start.getRange('B5:B12').format.horizontalAlignment='center';
start.getRange('B7').formulas=[[`=MAX('Tasks'!L6:L${last})`]];
start.getRange('B8').formulas=[['=ROUNDUP(B7/5,0)']];start.getRange('B10').formulas=[['=B8-B9']];
start.getRange('B12').formulas=[['=IF(B5="","",WORKDAY(B5-1,B7))']];start.getRange('B12').setNumberFormat('yyyy-mm-dd');
const instructions=[
 ['How to use','Start on AWS start: provision EC2, download Qwen3.5-4B and run text/image inference. The AWS starter ZIP supplies reference scripts. Detailed format recipes follow in the runbook.'],
 ['Tasks','Edit amber task inputs for estimated duration, baseline hold day, predecessor IDs, effort, status and progress. Calculated dates and Gantt update. One day is a working day.'],
 ['Baseline logic','All predecessors are finish-to-start plus one working day. Baseline hold days include initial daily resource leveling. They are not promised dates.'],
 ['Resource availability','The initial schedule assumes a maximum8h/day per role and24h/day for a pooled expert/reviewer team. Confirm those peak reservations at mobilization.'],
 ['After edits','Dependencies recalculate, but resource leveling does not rerun automatically. Check Capacity and Weekly effort and move hold days to resolve conflicts. Holidays and absence calendars require a schedule update.'],
 ['Task detail','Inputs, steps, deliverable and acceptance check define completion. Paste evidence or blocker references in Tasks. A date passing never marks work complete.'],
 ['Source routing','All51 prior source leads are mapped. Model weights, tool software, documents, datasets and catalog leads follow different routes. No source has been newly ingested by this plan.'],
 ['Formats','Raw PDF/DOCX/EML/audio/images become reviewed evidence JSONL. Retrieval gets chunks and vectors. SFT gets prompt/completion JSONL plus local images decoded by the loader.'],
 ['Model setup','Download a pinned Hugging Face model snapshot separately from data. Prove processor, mixed batches, loss masks, adapter updates and save/reload before substantive training.'],
 ['Budget','Task hours are bottom-up execution/review estimates, not full payroll cost. Capacity planning-hour inputs preserve the earlier envelope. Unassigned hours cover overhead and uncertainty, not automatically savings.'],
 ['Release boundary','Internal refining pilot only. Rights, technical acceptance and security acceptance are prerequisites. Expert candidates and licensing are unconfirmed.'],
 ['Legend','Amber = editable planning input. Blue Gantt bar = scheduled task. Darker bar = decision gate. Initial progress is zero. Original documents remain unchanged.']
];
start.getRange('A15:B26').values=instructions;start.getRange('A15:A26').format.font={bold:true};
start.getRange('A1:A34').format.columnWidth=31;start.getRange('B1:B34').format.columnWidth=28;start.getRange('C1:C34').format.columnWidth=86;
// Put long instructions in the wide narrative column, leaving B as a gutter.
instructions.forEach((r,i)=>{start.getRange(`B${15+i}`).values=[['']];start.getRange(`C${15+i}`).values=[[clean(r[1])]];});
start.getRange('C11').values=[['Gantt shows 36 weeks. If tasks extend past week 36, extend the displayed columns.']];
start.getRange('A5:C26').format.wrapText=true;start.getRange('A5:C26').format.verticalAlignment='top';start.getRange('A5:C12').format.rowHeight=48;start.getRange('A15:C26').format.rowHeight=64;

const th=['ID','Workstream','Task','Owner code','Baseline hold day','Duration days','Predecessor1','Predecessor2','Predecessor3','Predecessor4','Start day','Finish day','Start date','Finish date','Owner hours','Reviewer code','Review hours','Status','Complete','Runbook section','Blocker or evidence'];
const tr=tasks.map(t=>[t.id,t.phase,t.title,t.owner,t.not_before,t.duration,...Array.from({length:4},(_,i)=>t.predecessors[i]||''),null,null,null,null,t.hours,t.reviewer,t.review_hours,t.status,t.percent,t.section,'']);
const ts=init('Tasks','Implementation tasks','Amber fields are editable. Start and finish are formulas. Owner and reviewer codes are defined in Capacity.',th,[9,17,48,14,15,13,14,14,14,14,12,12,15,15,13,15,13,18,12,13,46],tr,54);
ts.tables.add(`A5:U${last}`,true,'ImplementationTasks');
for(const range of [`D6:J${last}`,`O6:S${last}`,`U6:U${last}`])ts.getRange(range).format.fill=amber;
ts.getRange(`S6:S${last}`).setNumberFormat('0%');ts.getRange(`M6:N${last}`).setNumberFormat('yyyy-mm-dd');
ts.getRange(`R6:R${last}`).dataValidation={rule:{type:'list',values:['Not started','In progress','Blocked','Complete']}};
for(let r=6;r<=last;r++){
 const prev=['G','H','I','J'].map(c=>`IF(${c}${r}="",1,INDEX($L$6:$L$${last},MATCH(${c}${r},$A$6:$A$${last},0))+1)`);
 ts.getRange(`K${r}:N${r}`).formulas=[[`=MAX(E${r},${prev.join(',')})`,`=K${r}+F${r}-1`,`=IF('Start here'!$B$5="","",WORKDAY('Start here'!$B$5-1,K${r}))`,`=IF('Start here'!$B$5="","",WORKDAY('Start here'!$B$5-1,L${r}))`]];
}
const gh=['ID','Task','Owner','Start week','Finish week','Status','Complete',...Array.from({length:weeks},(_,i)=>i+1)];
const gs=init('Gantt','Implementation Gantt','Relative weeks. Set kickoff on Start here for calendar dates. Planned bars are not completion claims.',gh,[9,49,12,11,11,17,10,...Array(weeks).fill(4)],tasks.map(t=>[t.id,t.title,t.owner,null,null,null,null,...Array(weeks).fill(null)]),38);
for(let r=6;r<=last;r++){
 gs.getRange(`D${r}:G${r}`).formulas=[[`=ROUNDUP('Tasks'!K${r}/5,0)`,`=ROUNDUP('Tasks'!L${r}/5,0)`,`='Tasks'!R${r}`,`='Tasks'!S${r}`]];
 gs.getRange(`G${r}`).setNumberFormat('0%');
 gs.getRange(`H${r}:${col(6+weeks)}${r}`).formulas=[Array.from({length:weeks},(_,i)=>`=IF(AND(${col(7+i)}$5>=$D${r},${col(7+i)}$5<=$E${r}),1,0)`)];
 const gr=gs.getRange(`H${r}:${col(6+weeks)}${r}`);gr.setNumberFormat(';;;');
 gr.conditionalFormats.add('cellIs',{operator:'equal',formula:1,format:{fill:tasks[r-6].phase==='Gate'?'#694822':'#547D99'}});
}
const detail=init('Task detail','Task procedures and acceptance','Follow the row identified in Tasks. Deliverables are required implementation outputs, not files already produced.',
 ['ID','Task','Inputs','Implementation steps','Required output','Acceptance check','Reviewer','Runbook section'],[9,40,50,88,44,74,30,12],tasks.map(t=>[t.id,t.title,clean(t.inputs),clean(t.steps),t.output,clean(t.acceptance),data.roles[t.reviewer],t.section]),100);
detail.tables.add(`A5:H${last}`,true,'ImplementationDetail');
const sr=init('Source routing','Existing source processing routes','Prior review status retained. Acquisition and permission decisions are implementation tasks.',
 ['Source ID','Source or model','Recipe','Disposition','Task IDs','Original URL','Processing status'],[12,64,19,76,27,70,48],data.sources,78);
sr.tables.add(`A5:G${data.sources.length+5}`,true,'SourceRoutes');
const pr=init('Processing recipes','Processing recipes by input format','Raw formats are preserved; reviewed derivatives are routed separately to retrieval, training and evaluation.',
 ['Recipe','Input type','Accepted source formats','Processing steps','Output formats','Permitted destination after clearance','Quality check','Task IDs'],[10,31,43,95,68,62,63,27],data.recipes.map(row=>row.map(clean)),115);
pr.tables.add(`A5:H${data.recipes.length+5}`,true,'ProcessingRecipes');
const wr=[];tasks.forEach((t,i)=>{wr.push([t.id,t.owner,'Owner',null,null,null,null,...Array(weeks).fill(null)]);wr.push([t.id,t.reviewer,'Review',null,null,null,null,...Array(weeks).fill(null)]);});
const ws=init('Weekly effort','Weekly owner and review effort','Uniform effort within each task duration. These estimates exclude unassigned overhead and buffers.',
 ['Task','Role','Work type','Total hours','Days','Start day','Finish day',...Array.from({length:weeks},(_,i)=>i+1)],
 [10,12,15,14,12,14,14,...Array(weeks).fill(9)],wr,27);
for(let i=0;i<wr.length;i++){
 const r=i+6,trow=Math.floor(i/2)+6,isReview=i%2===1;
 ws.getRange(`B${r}`).formulas=[[`='Tasks'!${isReview?'P':'D'}${trow}`]];
 ws.getRange(`D${r}:G${r}`).formulas=[[`='Tasks'!${isReview?'Q':'O'}${trow}`,`='Tasks'!F${trow}`,`='Tasks'!K${trow}`,`='Tasks'!L${trow}`]];
 ws.getRange(`H${r}:${col(6+weeks)}${r}`).formulas=[Array.from({length:weeks},(_,i)=>`=MAX(0,MIN($G${r},${(i+1)*5})-MAX($F${r},${i*5+1})+1)*$D${r}/$E${r}`)];
}
ws.getRange(`D6:${col(6+weeks)}${wr.length+5}`).setNumberFormat('0.0');
const cr=Object.entries(data.roles).map(([id,name])=>[id,name,data.capacity[id],null,null,data.daily_capacity[id]*5,null,null,...Array(weeks).fill(null)]);
const cs=init('Capacity','Resource capacity and workload','Inputs are planning hours and peak weekly availability. MD/CD/technical peaks require explicit reservation; experts form a pool.',
 ['Code','Role','Planning hours','Assigned hours','Unassigned hours','Weekly peak capacity','Peak scheduled hours','Capacity review',...Array.from({length:weeks},(_,i)=>i+1)],
 [10,43,16,17,17,18,18,24,...Array(weeks).fill(10)],cr,52);
for(let i=0;i<cr.length;i++){
 const r=i+6;
 cs.getRange(`D${r}:E${r}`).formulas=[[`=SUMIF('Weekly effort'!$B$6:$B$${wr.length+5},$A${r},'Weekly effort'!$D$6:$D$${wr.length+5})`,`=C${r}-D${r}`]];
 cs.getRange(`I${r}:${col(7+weeks)}${r}`).formulas=[Array.from({length:weeks},(_,i)=>`=SUMIF('Weekly effort'!$B$6:$B$${wr.length+5},$A${r},'Weekly effort'!${col(7+i)}$6:${col(7+i)}$${wr.length+5})`)];
 cs.getRange(`G${r}:H${r}`).formulas=[[`=MAX(I${r}:${col(7+weeks)}${r})`,`=IF(G${r}>F${r}+0.01,"Review capacity","Within peak limit")`]];
}
cs.getRange('C6:C15').format.fill=amber;cs.getRange('F6:F15').format.fill=amber;cs.getRange(`C6:${col(7+weeks)}15`).setNumberFormat('0.0');
cs.getRange('H6:H15').conditionalFormats.add('containsText',{text:'Review capacity',format:{fill:'#F9D8C8'}});
cs.getRange('A18').values=[['Hour envelopes']];
cs.getRange('B18:B21').values=[['Earlier employee allocation: 4,080 hours.'],['Expert pool: 1,000 hours proposed.'],['Implementation specialist: 300 hours.'],['Parent security: 160 hours proposed.']];
cs.getRange('B18:B21').format.wrapText=true;cs.getRange('B18:B21').format.rowHeight=42;
const rs=init('References','Technical references','AWS and foundation references checked 24 September 2026. Exact versions are pinned and proven during implementation.',
 ['ID','Reference','URL or record','Use'],[13,43,99,74],data.refs,56);

// Independent schedule reconciliation before export.
// The authoring engine retains stale dependent values after input mutations.
// Verify exported-file input changes with a separate office recalculation in QA.
const check=await wb.inspect({kind:'table',range:'Tasks!A6:N12',include:'values,formulas',tableMaxRows:7,tableMaxCols:14,maxChars:4500});
console.log(check.ndjson);
console.log((await wb.inspect({kind:'table',range:"'Start here'!A5:C12",include:'values',tableMaxRows:8,tableMaxCols:3,maxChars:2400})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},summary:'Formula error scan',maxChars:2000})).ndjson);
const actual=ts.getRange(`K6:L${last}`).values;
tasks.forEach((t,i)=>{if(actual[i][0]!==t.start_day||actual[i][1]!==t.finish_day)throw new Error(`Schedule mismatch ${t.id}: ${actual[i]} != ${t.start_day},${t.finish_day}`);});
const capValues=cs.getRange('C6:H15').values;
if(capValues.some(r=>r[1]>r[0]||r[4]>r[3]+.01))throw new Error('Resource capacity exceeded');
const weeklyValues=ws.getRange(`H6:${col(6+weeks)}${wr.length+5}`).values;
const ownerReviewValues=ws.getRange(`D6:D${wr.length+5}`).values;
weeklyValues.forEach((row,i)=>{if(Math.abs(row.reduce((a,b)=>a+b,0)-ownerReviewValues[i][0])>0.0001)throw new Error('Weekly effort reconciliation failed');});
const previewRanges={
 'AWS start':'A1:G9','Start here':'A1:C12','Gantt':`A1:${col(6+weeks)}18`,'Tasks':'A1:F12','Task detail':'A1:H9',
 'Source routing':'A1:G9','Processing recipes':'A1:H9','Capacity':`A1:${col(7+weeks)}15`,'Weekly effort':'A1:O13','References':'A1:D11'
};
for(const [name,range] of Object.entries(previewRanges)){
 const preview=await wb.render({sheetName:name,range,scale:1,format:'png'});
 await fs.writeFile(path.join(qa,`sheet-${name.replaceAll(' ','-')}.png`),new Uint8Array(await preview.arrayBuffer()));
}
const xlsx=await SpreadsheetFile.exportXlsx(wb);await xlsx.save(path.join(out,'Broadbridge_AWS_Implementation_Gantt.xlsx'));
await fs.writeFile(path.join(qa,'workbook_checks.json'),JSON.stringify({tasks:n,finishDay:Math.max(...tasks.map(t=>t.finish_day)),weeks:Math.ceil(Math.max(...tasks.map(t=>t.finish_day))/5),scheduleMatch:true,capacityWithinLimits:true,capacity:capValues},null,2));
console.log('Exported workbook and nine sheet previews');
