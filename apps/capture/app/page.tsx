import { redirect } from "next/navigation";
import { requireActor, signOut } from "../auth";
import { loadCapture } from "../lib/repository";
import CaptureApp from "../components/CaptureApp";

export const dynamic = "force-dynamic";

export default async function Home() {
  let email: string;
  try { email = await requireActor(); } catch { redirect("/signin"); }
  let initial;
  try { initial = await loadCapture(email); } catch {
    return <main><h1>Case capture is temporarily unavailable</h1><p>Your saved records remain in the database. Please reload or contact Brad.</p></main>;
  }
  return <CaptureApp initialCases={initial.cases} initialWorkflow={initial.workflow} email={email}
    onSignOut={async () => { "use server"; await signOut({ redirectTo: "/signin" }); }} />;
}
