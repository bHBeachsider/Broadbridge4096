"use server";
import { requireActor } from "../../auth";
import { scoreInputSchema } from "../../lib/public-review";
import { persistPublicScore } from "../../lib/public-review-repository";

export async function savePublicScore(value:unknown){
  try{
    const actor=await requireActor();
    const input=scoreInputSchema.parse(value);
    const saved=await persistPublicScore(input,actor);
    return {ok:true as const,saved};
  }catch(error){
    const stale=typeof error==="object"&&error!==null&&"code" in error&&error.code==="40001";
    return {ok:false as const,message:stale?"This score changed in another tab. Reload and review the saved version before trying again.":"Score not saved. Check the fields and your sign-in, then try again. Your notes remain in this tab."};
  }
}
