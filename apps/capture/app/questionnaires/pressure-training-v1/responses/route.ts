import { requireActor } from "../../../../auth";
import { loadQuestionnaire } from "../../../../lib/questionnaire-repository";
export const dynamic = "force-dynamic";
export async function GET() {
  let actor: string;
  try { actor = await requireActor(); } catch { return new Response("Sign-in required", {status: 401}); }
  try {
    const saved = await loadQuestionnaire(actor);
    return new Response(JSON.stringify({schema: "broadbridge.training_questionnaire_export/1", exported_at: new Date().toISOString(), authenticated_reviewer: actor, response: saved}, null, 2), {
      headers: {"Content-Type": "application/json", "Cache-Control": "private, no-store", "Content-Disposition": 'attachment; filename="broadbridge-training-review.json"'},
    });
  } catch { return new Response("Export unavailable", {status: 503}); }
}
