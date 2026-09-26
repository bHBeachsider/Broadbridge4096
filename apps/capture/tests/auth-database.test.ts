import { randomUUID } from "node:crypto";
import { afterEach, describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { getSql } from "../lib/db";
import { createAuthAdapter } from "../lib/auth-adapter";

const enabled = Boolean(process.env.BROADBRIDGE_DATABASE_URL && process.env.CAPTURE_DB_TEST_HOST);
const identifiers = new Set<string>();

function verifyTarget() {
  const target = new URL(process.env.BROADBRIDGE_DATABASE_URL!);
  if (target.hostname !== process.env.CAPTURE_DB_TEST_HOST) {
    throw new Error("Verify a dedicated development branch before running database tests.");
  }
}

function mailbox() {
  verifyTarget();
  const email = `auth-test-${randomUUID()}@example.invalid`;
  identifiers.add(email);
  vi.stubEnv("CAPTURE_ALLOWED_EMAILS", email);
  return email;
}

afterEach(async () => {
  vi.restoreAllMocks();
  vi.unstubAllEnvs();
  if (!enabled) return;
  verifyTarget();
  const sql = getSql();
  // Never reset auth tables or remove tokens belonging to another test/reviewer.
  for (const identifier of identifiers) {
    await sql`DELETE FROM broadbridge.auth_verification_tokens WHERE identifier=${identifier}`;
    await sql`DELETE FROM broadbridge.auth_email_cooldowns WHERE identifier=${identifier}`;
    await sql`DELETE FROM broadbridge.auth_users WHERE email=${identifier}`;
  }
  identifiers.clear();
});

describe.skipIf(!enabled)("auth tokens on a verified development database", () => {
  it("caps an ahead-of-database app expiry using the database issuance clock", async () => {
    const identifier = mailbox();
    const clock = await getSql()`SELECT (extract(epoch FROM clock_timestamp()) * 1000)::bigint::text AS milliseconds`;
    const appTime = Number(clock[0].milliseconds) + 60_000;
    vi.spyOn(Date, "now").mockReturnValue(appTime);
    const requested = new Date(appTime + 15 * 60_000);
    const token = "a".repeat(64);
    const stored = await createAuthAdapter().createVerificationToken!({ identifier, token, expires: requested });
    expect(stored!.expires.getTime()).toBeLessThanOrEqual(requested.getTime());
    const rows = await getSql()`SELECT expires <= created_at + interval '15 minutes' AS bounded,
      expires > created_at AS valid, expires = created_at + interval '15 minutes' AS clipped
      FROM broadbridge.auth_verification_tokens WHERE identifier=${identifier} AND token=${token}`;
    expect(rows).toEqual([{ bounded: true, valid: true, clipped: true }]);
  });

  it("preserves a shorter expiry and permits exactly one concurrent token consumer", async () => {
    const identifier = mailbox();
    const token = "b".repeat(64);
    const requested = new Date(Date.now() + 5 * 60_000);
    const adapter = createAuthAdapter();
    const stored = await adapter.createVerificationToken!({ identifier, token, expires: requested });
    expect(stored!.expires.toISOString()).toBe(requested.toISOString());
    const consumed = await Promise.all([
      adapter.useVerificationToken!({ identifier, token }),
      adapter.useVerificationToken!({ identifier, token }),
    ]);
    expect(consumed.filter(Boolean)).toHaveLength(1);
    expect(await adapter.useVerificationToken!({ identifier, token })).toBeNull();
    expect(await getSql()`SELECT token FROM broadbridge.auth_verification_tokens WHERE identifier=${identifier}`).toHaveLength(0);
  });
});
