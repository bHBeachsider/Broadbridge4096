/** Server-side capture admission policy. Configuration is re-read on each decision. */
export type AuthEnvironment = Readonly<Record<string, string | undefined>>;

export function normalizeEmail(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const email = value.trim().toLowerCase();
  if (!email || email.length > 254 || /[\s\x00-\x1f\x7f]/.test(email)) return null;
  const pieces = email.split("@");
  if (pieces.length !== 2) return null;
  const [local, domain] = pieces;
  if (!local || !domain || local.length > 64 || !/^[a-z0-9!#$%&'*+/=?^_`{|}~.-]+$/.test(local)
      || local.startsWith(".") || local.endsWith(".") || local.includes("..")) return null;
  if (!domain.split(".").every((label) => /^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$/.test(label))) return null;
  return email;
}

function allowedEmails(env: AuthEnvironment): Set<string> {
  const configured = env.CAPTURE_ALLOWED_EMAILS;
  if (!configured?.trim()) return new Set();
  const values = configured.split(/[,\n]/).map(normalizeEmail);
  if (values.some((email) => email === null)) return new Set();
  return new Set(values as string[]);
}

export function allowedEmail(value: unknown, env: AuthEnvironment = process.env): string | null {
  const email = normalizeEmail(value);
  return email && allowedEmails(env).has(email) ? email : null;
}

export function assertAllowedEmail(value: unknown, env: AuthEnvironment = process.env): string {
  const email = allowedEmail(value, env);
  if (!email) throw new Error("Access denied");
  return email;
}

export function configuredAuthOrigin(env: AuthEnvironment = process.env): string | null {
  try {
    const configured = env.AUTH_URL || (env.VERCEL === "1" && env.VERCEL_URL ? `https://${env.VERCEL_URL}` : undefined);
    if (!configured) return null;
    const url = new URL(configured);
    if (url.username || url.password || url.search || url.hash || (url.pathname !== "/" && url.pathname !== "")) return null;
    const local = ["127.0.0.1", "localhost", "[::1]"].includes(url.hostname);
    if (url.protocol !== "https:" && !(env.NODE_ENV === "development" && local && url.protocol === "http:")) return null;
    return url.origin;
  } catch {
    return null;
  }
}

export function localTestOutbox(env: AuthEnvironment = process.env): string | null {
  if (env.CAPTURE_TEST_OUTBOX === undefined) return null;
  const origin = configuredAuthOrigin(env);
  if (!env.CAPTURE_TEST_OUTBOX.trim() || env.NODE_ENV !== "development" || env.VERCEL !== undefined
      || !origin || !["127.0.0.1", "localhost", "[::1]"].includes(new URL(origin).hostname)) {
    throw new Error("Authentication is unavailable");
  }
  return env.CAPTURE_TEST_OUTBOX;
}

export function authAvailability(env: AuthEnvironment = process.env): { available: boolean } {
  try {
    if (!env.AUTH_SECRET?.trim() || !env.BROADBRIDGE_DATABASE_URL?.trim() || !configuredAuthOrigin(env)
        || allowedEmails(env).size === 0) return { available: false };
    if (localTestOutbox(env)) return { available: true };
    const sender = env.CAPTURE_EMAIL_FROM?.trim();
    const mailbox = sender?.match(/^[^<>\r\n]+<([^<>]+)>$/)?.[1] ?? sender;
    return { available: !!env.RESEND_API_KEY?.trim() && normalizeEmail(mailbox) !== null };
  } catch {
    return { available: false };
  }
}
