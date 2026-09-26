import Link from "next/link";

export default function CheckEmailPage() {
  return (
    <main className="auth-shell" style={{ maxWidth: 520, margin: "8vh auto", padding: 24, background: "var(--panel)", border: "1px solid var(--rule)", borderRadius: 8 }}>
      <p className="brand">BROADBRIDGE / CASE CAPTURE</p>
      <h1>Check your email.</h1>
      <p>If your address has capture access, a sign-in link is on its way. Open it in this browser to continue.</p>
      <p>The link expires after 15 minutes and works once. Please wait a minute before requesting another.</p>
      <Link href="/signin" className="btn" style={{ display: "inline-block", textDecoration: "none" }}>Back to sign in</Link>
    </main>
  );
}
