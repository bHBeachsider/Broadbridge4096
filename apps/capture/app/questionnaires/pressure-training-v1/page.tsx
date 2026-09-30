import { redirect } from "next/navigation";
import { requireActor } from "../../../auth";
import { questionnairePath } from "../../../lib/questionnaire";
import { loadQuestionnaire, questionnaireHash } from "../../../lib/questionnaire-repository";
import TrainingQuestionnaire from "../../../components/TrainingQuestionnaire";
export const dynamic = "force-dynamic";
export default async function QuestionnairePage() {
  let actor: string;
  try { actor = await requireActor(); } catch { redirect("/signin?next=" + encodeURIComponent(questionnairePath)); }
  let saved;
  try { saved = await loadQuestionnaire(actor); } catch {
    return <main><h1>Questionnaire is temporarily unavailable</h1><p>Reload to retry. Existing responses have not changed.</p><a href="/">Case capture</a></main>;
  }
  return <TrainingQuestionnaire actor={actor} initial={saved} hash={questionnaireHash}/>;
}
