import { AuthError } from "next-auth";
import { redirect } from "next/navigation";
import { signIn } from "../../auth";
import { allowedEmail, authAvailability } from "../../lib/auth-policy";

export const dynamic = "force-dynamic";

async function requestLink(formData: FormData) {
  "use server";
  if (!authAvailability().available) redirect("/signin?error=unavailable");
  const email = allowedEmail(formData.get("email"));
  if (!email) redirect("/check-email");
  try {
    await signIn("resend", { email, redirectTo: "/" });
  } catch (error) {
    if (error instanceof AuthError) redirect("/signin?error=request");
    throw error; // Preserve Next.js's successful redirect control flow.
  }
}

export default async function SignInPage({ searchParams }: { searchParams: Promise<{ error?: string }> }) {
  const { error } = await searchParams;
  const available = authAvailability().available;
  return (
    <main className="auth-shell" style={{ maxWidth: 520, margin: "8vh auto", padding: 24, background: "var(--panel)", border: "1px solid var(--rule)", borderRadius: 8 }}>
      <p className="brand">BROADBRIDGE / CASE CAPTURE</p>
      <h1>Sign in to capture.</h1>
      <p>Use your approved email address. We’ll send a sign-in link so you can save and review your work.</p>
      {!available || error === "unavailable" ? (
        <p role="status">Email sign-in is currently unavailable. Please contact the capture administrator.</p>
      ) : (
        <>
          {error ? <p role="alert">We couldn’t complete sign-in. Request a new link or try again shortly.</p> : null}
          <form action={requestLink} className="q">
            <label htmlFor="email">Email address</label>
            <input id="email" name="email" type="email" autoComplete="email" required maxLength={254} placeholder="you@example.com" style={{ width: "100%", border: "1px solid var(--rule)", borderRadius: 6, background: "var(--panel)", padding: "9px 11px" }} />
            <button type="submit" className="btn primary" style={{ marginTop: 8 }}>Email me a sign-in link</button>
          </form>
          <p className="muted">Links expire after 15 minutes and can be used once.</p>
        </>
      )}
    </main>
  );
}
