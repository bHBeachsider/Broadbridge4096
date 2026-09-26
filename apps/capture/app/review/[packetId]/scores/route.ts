import { requireActor } from "../../../../auth";
import { loadPublicReview } from "../../../../lib/public-review-repository";
import { packetIdSchema,scoresCsv } from "../../../../lib/public-review";
export const dynamic="force-dynamic";
export async function GET(_request:Request,{params}:{params:Promise<{packetId:string}>}){
  let actor:string;
  try{actor=await requireActor();}catch{return new Response("Sign in to export your scores.",{status:401});}
  const {packetId}=await params;
  if(!packetIdSchema.safeParse(packetId).success)return new Response("Not found",{status:404});
  try{
    const loaded=await loadPublicReview(packetId,actor);
    if(!loaded)return new Response("Not found",{status:404});
    return new Response(scoresCsv(loaded.packet,loaded.scores),{headers:{"Content-Type":"text/csv; charset=utf-8","Content-Disposition":`attachment; filename="scores_${packetId}.csv"`,"Cache-Control":"private, no-store","X-Content-Type-Options":"nosniff"}});
  }catch{return new Response("Score export temporarily unavailable",{status:503});}
}
