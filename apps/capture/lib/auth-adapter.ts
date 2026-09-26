import type { Adapter, AdapterUser, VerificationToken } from "next-auth/adapters";
import { getSql } from "./db";
import { allowedEmail, assertAllowedEmail } from "./auth-policy";

type Row = Record<string, unknown>;

function asDate(value: unknown): Date {
  return value instanceof Date ? new Date(value.getTime()) : new Date(String(value));
}

function asUser(row: Row | undefined): AdapterUser | null {
  const email = allowedEmail(row?.email);
  if (!row || !email || typeof row.id !== "string") return null;
  return {
    id: row.id,
    email,
    emailVerified: row.email_verified ? asDate(row.email_verified) : null,
    name: typeof row.name === "string" ? row.name : null,
    image: typeof row.image === "string" ? row.image : null,
  };
}

function asToken(row: Row | undefined): VerificationToken | null {
  if (!row || typeof row.identifier !== "string" || typeof row.token !== "string") return null;
  return { identifier: row.identifier, token: row.token, expires: asDate(row.expires) };
}

function validHash(token: unknown): token is string {
  return typeof token === "string" && /^[0-9a-f]{64}$/.test(token);
}

export function createAuthAdapter(): Adapter {
  const adapter: Adapter = {
    async createUser(user) {
      const email = assertAllowedEmail(user.email);
      const rows = await getSql()`
        INSERT INTO broadbridge.auth_users(email, email_verified, name, image)
        VALUES (${email}, ${user.emailVerified?.toISOString() ?? null}, ${user.name ?? null}, ${user.image ?? null})
        ON CONFLICT (email) DO UPDATE
          SET email_verified = COALESCE(broadbridge.auth_users.email_verified, EXCLUDED.email_verified)
        RETURNING id, email, email_verified, name, image`;
      const saved = asUser(rows[0]);
      if (!saved) throw new Error("Authentication is unavailable");
      return saved;
    },
    async getUser(id) {
      const rows = await getSql()`SELECT id, email, email_verified, name, image FROM broadbridge.auth_users WHERE id = ${id}`;
      return asUser(rows[0]);
    },
    async getUserByEmail(value) {
      const email = allowedEmail(value);
      if (!email) return null;
      const rows = await getSql()`SELECT id, email, email_verified, name, image FROM broadbridge.auth_users WHERE email = ${email}`;
      return asUser(rows[0]);
    },
    async getUserByAccount() {
      return null; // Email is the only configured provider; no OAuth account linking.
    },
    async updateUser(user) {
      const email = user.email === undefined ? undefined : assertAllowedEmail(user.email);
      const current = await adapter.getUser!(user.id);
      if (!current) throw new Error("Access denied");
      const rows = await getSql()`
        UPDATE broadbridge.auth_users
        SET email = CASE WHEN ${email !== undefined} THEN ${email ?? null} ELSE email END,
          email_verified = CASE WHEN ${user.emailVerified !== undefined} THEN ${user.emailVerified?.toISOString() ?? null}::timestamptz ELSE email_verified END,
          name = CASE WHEN ${user.name !== undefined} THEN ${user.name ?? null} ELSE name END,
          image = CASE WHEN ${user.image !== undefined} THEN ${user.image ?? null} ELSE image END
        WHERE id = ${user.id} AND email = ${current.email}
        RETURNING id, email, email_verified, name, image`;
      const saved = asUser(rows[0]);
      if (!saved) throw new Error("Access denied");
      return saved;
    },
    async createVerificationToken(verification) {
      const identifier = assertAllowedEmail(verification.identifier);
      const expires = verification.expires.getTime();
      if (!validHash(verification.token) || !Number.isFinite(expires)
          || expires <= Date.now() || expires > Date.now() + 15 * 60_000) {
        throw new Error("Invalid verification token");
      }
      const rows = await getSql()`
        WITH issued AS MATERIALIZED (
          SELECT clock_timestamp() AS created_at
        ), expired AS (
          DELETE FROM broadbridge.auth_verification_tokens WHERE expires <= (SELECT created_at FROM issued)
        )
        INSERT INTO broadbridge.auth_verification_tokens(identifier, token, expires, created_at)
        SELECT ${identifier}, ${verification.token},
          LEAST(${verification.expires.toISOString()}::timestamptz, created_at + interval '15 minutes'), created_at
        FROM issued
        RETURNING identifier, token, expires`;
      const saved = asToken(rows[0]);
      if (!saved) throw new Error("Authentication is unavailable");
      return saved;
    },
    async useVerificationToken({ identifier: value, token }) {
      const identifier = allowedEmail(value);
      if (!identifier || !validHash(token)) return null;
      const rows = await getSql()`
        DELETE FROM broadbridge.auth_verification_tokens
        WHERE identifier = ${identifier} AND token = ${token} AND expires > clock_timestamp()
        RETURNING identifier, token, expires`;
      const consumed = asToken(rows[0]);
      return consumed && consumed.expires.getTime() > Date.now() ? consumed : null;
    },
  };
  return adapter;
}

export async function claimEmailIssuance(value: string): Promise<void> {
  const identifier = assertAllowedEmail(value);
  const rows = await getSql()`
    INSERT INTO broadbridge.auth_email_cooldowns(identifier, last_issued_at)
    VALUES (${identifier}, clock_timestamp())
    ON CONFLICT (identifier) DO UPDATE SET last_issued_at = clock_timestamp()
    WHERE broadbridge.auth_email_cooldowns.last_issued_at <= clock_timestamp() - interval '60 seconds'
    RETURNING identifier`;
  if (rows.length === 0) throw new Error("Please wait before requesting another sign-in link");
}
