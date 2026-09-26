import { notFound,redirect } from "next/navigation";
import { requireActor } from "../../../auth";
import { loadPublicReview } from "../../../lib/public-review-repository";
import { packetIdSchema,safeReviewReturn } from "../../../lib/public-review";
import PublicReview from "../../../components/PublicReview";
export const dynamic="force-dynamic";
export default async function ReviewPage({params,searchParams}:{params:Promise<{packetId:string}>;searchParams:Promise<{question?:string;response?:string}>}){
  const {packetId}=await params;
  if(!packetIdSchema.safeParse(packetId).success)notFound();
  const query=await searchParams;
  const destination=safeReviewReturn(`/review/${packetId}`+(query.question&&query.response?`?question=${query.question}&response=${query.response}`:""));
  let actor:string;
  try{actor=await requireActor();}catch{redirect("/signin?next="+encodeURIComponent(destination));}
  let loaded;
  try{loaded=await loadPublicReview(packetId,actor);}catch{
    return <main className="review-shell"><h1>Review is temporarily unavailable</h1><p>Scores have not been changed. Reload to retry.</p><a href="/">Case capture</a></main>;
  }
  if(!loaded)notFound();
  const index=query.question?loaded.packet.items.findIndex(i=>i.question_id===query.question&&i.response_label===(query.response||"A")):0;
  if(index<0)notFound();
  return <PublicReview {...loaded} actor={actor} initialIndex={index}/>;
}
