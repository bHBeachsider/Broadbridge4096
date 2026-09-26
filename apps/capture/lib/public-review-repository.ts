import "server-only";
import { getSql } from "./db";
import { packetIdSchema, publicReviewPacketSchema, scoreInputSchema, validateScoreForItem, type ScoreInput, type SavedScore } from "./public-review";

export async function loadPublicReview(packetId:string,actor:string){
  packetIdSchema.parse(packetId);
  const sql=getSql();
  const packets=await sql`SELECT packet_sha256,record FROM broadbridge.public_review_packets WHERE packet_id=${packetId}`;
  if(!packets.length)return null;
  const packet=publicReviewPacketSchema.parse(packets[0].record);
  const scores=await sql`SELECT packet_id,question_id,response_label,reviewer,revision,score,critical_error,hard_fail,notes,review_date
    FROM broadbridge.current_public_review_scores WHERE packet_id=${packetId} AND reviewer=${actor}`;
  return {packet,hash:packets[0].packet_sha256 as string,scores:scores as SavedScore[]};
}

export async function persistPublicScore(input:ScoreInput,actor:string):Promise<SavedScore>{
  const score=scoreInputSchema.parse(input);
  const loaded=await loadPublicReview(score.packet_id,actor);
  if(!loaded||loaded.hash!==score.packet_sha256)throw new Error("Review packet changed");
  const item=loaded.packet.items.find(i=>i.question_id===score.question_id&&i.response_label===score.response_label);
  if(!item)throw new Error("Unknown review item");
  validateScoreForItem(score,item);
  const sql=getSql();
  const rows=await sql`SELECT broadbridge.save_public_review_score(${score.packet_id},${score.packet_sha256},${score.question_id},${score.response_label},${actor},
    ${score.score},${score.critical_error},${score.hard_fail},${score.notes},${score.expected_revision}::integer) AS saved`;
  return rows[0].saved as SavedScore;
}
