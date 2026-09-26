import "server-only";
import { appendFile } from "node:fs/promises";
import NextAuth from "next-auth";
import Resend from "next-auth/providers/resend";
import { claimEmailIssuance, createAuthAdapter } from "./lib/auth-adapter";
import { allowedEmail, assertAllowedEmail, authAvailability, configuredAuthOrigin, localTestOutbox } from "./lib/auth-policy";

// Emit fixed diagnostic vocabulary only: never messages, stacks, URLs or SQL.
const authErrorTypes = new Set(["AuthError", "AdapterError", "AccessDenied", "CallbackRouteError", "EmailSignInError", "JWTSessionError", "SessionTokenError", "MissingAdapter", "MissingAdapterMethods", "MissingSecret", "UntrustedHost", "Verification", "Configuration"]);
const causeErrorTypes = new Set(["Error", "TypeError", "URIError", "AggregateError", "NeonDbError"]);
const diagnosticCodes = new Set(["08001", "08006", "22001", "22007", "22P02", "23502", "23503", "23505", "23514", "28000", "28P01", "3D000", "3F000", "40001", "42501", "42601", "42703", "42804", "42883", "42P01", "53300", "57014", "ENOTFOUND", "ECONNREFUSED", "ECONNRESET", "ETIMEDOUT", "ENOENT", "EACCES", "EPERM"]);
function authDiagnostic(error: unknown) {
  const value = error as { type?: unknown; cause?: { err?: { name?: unknown; code?: unknown } } } | null;
  const recognized = (item: unknown, vocabulary: Set<string>) => typeof item === "string" && vocabulary.has(item) ? item : "Unknown";
  return { type: recognized(value?.type, authErrorTypes), causeType: recognized(value?.cause?.err?.name, causeErrorTypes), code: recognized(value?.cause?.err?.code, diagnosticCodes) };
}

export const { handlers, auth, signIn, signOut } = NextAuth(() => ({
  secret: process.env.AUTH_SECRET,
  trustHost: Boolean(configuredAuthOrigin()),
  adapter: createAuthAdapter(),
  session: { strategy: "jwt", maxAge: 8 * 60 * 60 },
  pages: { signIn: "/signin", verifyRequest: "/check-email", error: "/signin" },
  providers: [
    Resend({
      apiKey: process.env.RESEND_API_KEY,
      from: process.env.CAPTURE_EMAIL_FROM,
      maxAge: 15 * 60,
      normalizeIdentifier: (identifier) => assertAllowedEmail(identifier),
      async sendVerificationRequest(params) {
        const email = assertAllowedEmail(params.identifier);
        if (!authAvailability().available) throw new Error("Authentication is unavailable");
        const origin = configuredAuthOrigin();
        if (!origin || new URL(params.url).origin !== origin) throw new Error("Authentication is unavailable");
        const outbox = localTestOutbox(); // Throws if a test outbox is configured outside local development.
        await claimEmailIssuance(email);
        if (outbox) {
          // Only an explicitly configured local test process may receive the real verification URL.
          await appendFile(outbox, JSON.stringify({ email, url: params.url, expires: params.expires.toISOString() }) + "\n", { encoding: "utf8", mode: 0o600 });
          return;
        }
        await Resend({}).sendVerificationRequest({ ...params, identifier: email });
      },
    }),
  ],
  callbacks: {
    async signIn({ user, account }) {
      return account?.provider === "resend" && account.type === "email"
        && authAvailability().available && allowedEmail(user.email) !== null;
    },
    async jwt({ token, user }) {
      const email = allowedEmail(user?.email ?? token.email);
      if (!email || !authAvailability().available) return null;
      return { ...token, email };
    },
    async session({ session, token }) {
      const email = allowedEmail(token.email);
      return { ...session, user: { ...session.user, email } };
    },
    async redirect({ url }) {
      const origin = configuredAuthOrigin();
      if (!origin) throw new Error("Authentication is unavailable");
      const destination = new URL(url, origin);
      return destination.origin === origin ? destination.href : `${origin}/`;
    },
  },
  logger: {
    error(error) {
      // Provider/adapter causes can contain credentials, tokens or captured request details.
      console.error("Capture authentication operation failed.", authDiagnostic(error));
    },
    warn() {},
    debug() {},
  },
  debug: false,
}));

export async function requireActor(): Promise<string> {
  if (!authAvailability().available) throw new Error("Authentication is unavailable");
  const session = await auth();
  return assertAllowedEmail(session?.user?.email);
}
