import { z } from "zod";

const identifier = z.string().regex(/^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$/);
export const packetIdSchema = z.string().regex(/^[a-z0-9][a-z0-9-]{0,63}$/);
const hash = z.string().regex(/^[0-9a-f]{64}$/);
const text = z.string().min(1).max(32000);
export const questionType = z.enum(["brief", "missing_data", "calculation", "grounded_explanation", "abstention"]);
const answerSchema = z.object({question_id:identifier, answer:text, uncertainties:z.array(z.string()),
  evidence:z.array(z.object({source_id:identifier,block_id:identifier,quote:text}).strict())}).strict();
export const publicReviewPacketSchema = z.object({
  schema:z.literal("broadbridge.public_review/1"),packet_id:packetIdSchema,title:text,training_approved:z.literal(false),
  frozen_files:z.record(z.string(),hash),
  sources:z.array(z.object({source_id:identifier,title:text,url:z.url().startsWith("https://"),publisher:text,context:text,
    blocks:z.array(z.object({block_id:identifier,text}).strict()).min(1)}).strict()).min(1).max(100),
  items:z.array(z.object({source_id:identifier,question_id:identifier,type:questionType,question:text,reference_answer:text,
    hard_fail_criteria:text,tolerance:z.string(),split:z.literal("dev"),permitted_use:z.literal("testing_only"),
    response_label:z.enum(["A","B"]),answer:answerSchema.nullable(),availability:z.enum(["answered","unavailable"]),checks:z.array(z.string())}).strict()).min(1).max(1000),
}).strict().superRefine((packet,ctx)=>{
  const keys=new Set<string>();
  for(const item of packet.items){
    const key=item.question_id+":"+item.response_label;
    if(keys.has(key)||!packet.sources.some(s=>s.source_id===item.source_id)||
      (item.answer!==null)!==(item.availability==="answered")||(item.answer&&item.answer.question_id!==item.question_id))
      ctx.addIssue({code:"custom",message:"Invalid packet item identity"});
    keys.add(key);
  }
});
export type PublicReviewPacket=z.infer<typeof publicReviewPacketSchema>;
export type ReviewItem=PublicReviewPacket["items"][number];
export const scoreInputSchema=z.object({packet_id:packetIdSchema,packet_sha256:hash,question_id:identifier,
  response_label:z.enum(["A","B"]),score:z.number().int().min(0).max(2),critical_error:z.boolean(),hard_fail:z.boolean(),
  notes:z.string().trim().min(1).max(8000),expected_revision:z.number().int().positive().nullable(),
}).strict().superRefine((value,ctx)=>{
  if((value.critical_error&&value.score!==0)||(value.hard_fail&&(!value.critical_error||value.score!==0)))
    ctx.addIssue({code:"custom",message:"Critical errors and matched hard-fail criteria require score 0 / critical error Yes."});
});
export type ScoreInput=z.infer<typeof scoreInputSchema>;
export type SavedScore=Omit<ScoreInput,"packet_sha256"|"expected_revision"> & {reviewer:string;review_date:string;revision:number};
export function validateScoreForItem(score:ScoreInput,item:Pick<ReviewItem,"answer">){
  if(!item.answer&&(score.score!==0||score.critical_error||score.hard_fail)) throw new Error("An unavailable answer may be recorded as zero, with an explanation; it is not an engineering claim.");
}
export const rubrics:Record<ReviewItem["type"],string[]>={
  brief:["Wrong or unsupported material claim","Useful but materially incomplete","Accurate, concise, uncertainty bounded"],
  missing_data:["Invents data or misses essential discriminator","Some useful requests; important gap","Essential discriminators with units/basis and limits"],
  calculation:["Wrong method/result/units/basis","Sound method but incomplete working/basis","Correct working, units, basis and result within tolerance"],
  grounded_explanation:["Unsupported or contradicted key claim","Mostly supported; incomplete traceability","Claims supported by evidence; inference/limits explicit"],
  abstention:["Unsupported conclusion or unsafe action","Uncertainty noted but not adequately bounded","Withholds unsupported conclusion and names needed evidence"],
};
export function safeReviewReturn(value:unknown):string{
  // Only this workflow's exact relative destinations survive magic-link sign-in.
  return typeof value==="string"&&/^\/review\/[a-z0-9][a-z0-9-]{0,63}(?:\?question=[A-Za-z0-9][A-Za-z0-9_.-]{0,127}&response=[AB])?$/.test(value)?value:"/";
}
function csvCell(value:unknown){
  let text=String(value??"");
  if(/^[\s]*[=+@-]/.test(text))text="'"+text;
  return '"'+text.replaceAll('"','""')+'"';
}
export function scoresCsv(packet:Pick<PublicReviewPacket,"items">,scores:SavedScore[]):string{
  const fields=["source_id","question_id","type","response_label","score","critical_error","reviewer","review_date","notes"];
  const lines=packet.items.map(item=>{
    const score=scores.find(s=>s.question_id===item.question_id&&s.response_label===item.response_label);
    return [item.source_id,item.question_id,item.type,item.response_label,score?.score,score?score.critical_error?"YES":"NO":"",score?.reviewer,score?.review_date,score?.notes].map(csvCell).join(",");
  });
  return fields.join(",")+"\r\n"+lines.join("\r\n")+"\r\n";
}
