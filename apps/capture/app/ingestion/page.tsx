import { redirect } from "next/navigation";
import { requireActor } from "../../auth";
import { listSources } from "../../lib/ingestion-repository";
import { assertActionBudget } from "../../lib/ingestion-validation";
import IngestionApp from "../../components/IngestionApp";
export const dynamic = "force-dynamic";
export default async function IngestionPage() {
  let email: string;
  try { email = await requireActor(); } catch { redirect("/signin"); }
  try { return <IngestionApp initial={assertActionBudget(await listSources())} email={email} />; }
  catch { return <main><h1>Source intake is temporarily unavailable</h1><p>Saved source records remain pending. Reload to retry.</p><a href="/">Case capture</a></main>; }
}
