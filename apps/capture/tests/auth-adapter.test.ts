import { beforeEach, describe, expect, it, vi } from "vitest";

const { query } = vi.hoisted(() => ({ query: vi.fn() }));
vi.mock("../lib/db", () => ({ getSql: () => query }));

import { claimEmailIssuance, createAuthAdapter } from "../lib/auth-adapter";

const token = "a".repeat(64);
const userRow = { id: "u-1", email: "brad@example.com", email_verified: "2026-09-24T12:00:00Z", name: null, image: null };

beforeEach(() => {
  vi.stubEnv("CAPTURE_ALLOWED_EMAILS", "brad@example.com,second@example.com");
  query.mockReset();
});

describe("email adapter", () => {
  it("stores an allowed user with a parameterized email and returns Auth.js dates", async () => {
    query.mockResolvedValue([userRow]);
    const user = await createAuthAdapter().createUser!({ id: "u-1", email: "Brad@Example.com", emailVerified: null });
    expect(user).toEqual({ id: "u-1", email: "brad@example.com", emailVerified: new Date("2026-09-24T12:00:00Z"), name: null, image: null });
    const [strings, ...values] = query.mock.calls[0];
    expect(strings.join("?")).not.toContain("brad@example.com");
    expect(values).toContain("brad@example.com");
  });

  it("rejects user creation or email replacement outside the current allowlist", async () => {
    const adapter = createAuthAdapter();
    await expect(adapter.createUser!({ id: "u-1", email: "outsider@example.com", emailVerified: null })).rejects.toThrow("Access denied");
    await expect(adapter.updateUser!({ id: "u-1", email: "outsider@example.com" })).rejects.toThrow("Access denied");
    expect(query).not.toHaveBeenCalled();
  });

  it("returns null for unknown or revoked users and never links OAuth accounts", async () => {
    const adapter = createAuthAdapter();
    query.mockResolvedValueOnce([]);
    expect(await adapter.getUser!("absent")).toBeNull();
    query.mockResolvedValueOnce([{ ...userRow, email: "revoked@example.com" }]);
    expect(await adapter.getUser!("u-1")).toBeNull();
    expect(await adapter.getUserByAccount!({ provider: "github", providerAccountId: "123" })).toBeNull();
  });

  it("updates verification timestamps while preserving unspecified user fields", async () => {
    query.mockResolvedValue([{ ...userRow, email_verified: "2026-09-24T13:00:00Z" }]);
    const updated = await createAuthAdapter().updateUser!({ id: "u-1", emailVerified: new Date("2026-09-24T13:00:00Z") });
    expect(updated.email).toBe("brad@example.com");
    expect(updated.emailVerified?.toISOString()).toBe("2026-09-24T13:00:00.000Z");
  });
});

describe("verification token boundary", () => {
  it("caps expiry against the same database clock used for created_at", async () => {
    const requestedExpiry = new Date(Date.now() + 15 * 60_000);
    const storedExpiry = new Date(requestedExpiry.getTime() - 1_087);
    query.mockResolvedValue([{ identifier: "brad@example.com", token, expires: storedExpiry }]);
    const saved = await createAuthAdapter().createVerificationToken!({ identifier: "brad@example.com", token, expires: requestedExpiry });
    expect(saved?.expires).toEqual(storedExpiry);
    const [strings, ...values] = query.mock.calls[0];
    const statement = strings.join("?").replace(/\s+/g, " ");
    expect(statement).toContain("issued AS MATERIALIZED ( SELECT clock_timestamp() AS created_at )");
    expect(statement).toContain("auth_verification_tokens(identifier, token, expires, created_at)");
    expect(statement).toContain("LEAST(?::timestamptz, created_at + interval '15 minutes'), created_at FROM issued");
    expect(values).toEqual(["brad@example.com", token, requestedExpiry.toISOString()]);
    expect(statement).not.toContain(token);
  });

  it("accepts only hashed tokens and a bounded future expiration", async () => {
    const adapter = createAuthAdapter();
    const expires = new Date(Date.now() + 14 * 60_000);
    query.mockResolvedValue([{ identifier: "brad@example.com", token, expires }]);
    expect(await adapter.createVerificationToken!({ identifier: "BRAD@example.com", token, expires })).toEqual({ identifier: "brad@example.com", token, expires });
    await expect(adapter.createVerificationToken!({ identifier: "brad@example.com", token: "raw-secret", expires })).rejects.toThrow("Invalid verification token");
    await expect(adapter.createVerificationToken!({ identifier: "brad@example.com", token, expires: new Date(Date.now() + 60 * 60_000) })).rejects.toThrow("Invalid verification token");
  });

  it("atomically consumes a token once and handles absent or expired rows", async () => {
    const adapter = createAuthAdapter();
    const expires = new Date(Date.now() + 60_000);
    query.mockResolvedValueOnce([{ identifier: "brad@example.com", token, expires }]).mockResolvedValueOnce([]);
    expect(await adapter.useVerificationToken!({ identifier: "brad@example.com", token })).toEqual({ identifier: "brad@example.com", token, expires });
    expect(await adapter.useVerificationToken!({ identifier: "brad@example.com", token })).toBeNull();
    const emitted = query.mock.calls[0][0].join("?");
    expect(emitted).toMatch(/DELETE FROM broadbridge\.auth_verification_tokens/i);
    expect(emitted).toMatch(/RETURNING/i);
    expect(emitted).toMatch(/expires > clock_timestamp\(\)/i);
    expect(query.mock.calls[0].slice(1)).toEqual(["brad@example.com", token]);
  });

  it("denies a revoked mailbox before consuming a token", async () => {
    expect(await createAuthAdapter().useVerificationToken!({ identifier: "revoked@example.com", token })).toBeNull();
    expect(query).not.toHaveBeenCalled();
  });
});

describe("issuance cooldown", () => {
  it("admits the first request and refuses another during the SQL cooldown", async () => {
    query.mockResolvedValueOnce([{ identifier: "brad@example.com" }]).mockResolvedValueOnce([]);
    await expect(claimEmailIssuance("brad@example.com")).resolves.toBeUndefined();
    await expect(claimEmailIssuance("brad@example.com")).rejects.toThrow("Please wait");
  });
});
