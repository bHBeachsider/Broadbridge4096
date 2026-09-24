import { describe, expect, it } from "vitest";
import {
  allowedEmail,
  assertAllowedEmail,
  authAvailability,
  configuredAuthOrigin,
  localTestOutbox,
  normalizeEmail,
} from "../lib/auth-policy";

const env = {
  NODE_ENV: "production",
  AUTH_SECRET: "a-secret-only-for-tests",
  AUTH_URL: "https://capture.example.com",
  BROADBRIDGE_DATABASE_URL: "postgresql://not-used",
  RESEND_API_KEY: "test-key-not-used",
  CAPTURE_EMAIL_FROM: "Capture <capture@example.com>",
  CAPTURE_ALLOWED_EMAILS: "Brad@Example.com,second@example.com",
};

describe("allowlist policy", () => {
  it("normalizes a single mailbox and admits only explicit members", () => {
    expect(normalizeEmail("  Brad@Example.com  ")).toBe("brad@example.com");
    expect(allowedEmail("BRAD@example.com", env)).toBe("brad@example.com");
    expect(allowedEmail("other@example.com", env)).toBeNull();
  });

  it.each([undefined, "", "*", "@example.com", "brad@example.com,invalid", "brad@example.com,,second@example.com"])(
    "denies all for missing or malformed configuration %s", (configuration) => {
      expect(allowedEmail("brad@example.com", { ...env, CAPTURE_ALLOWED_EMAILS: configuration })).toBeNull();
    },
  );

  it.each(["Brad <brad@example.com>", "brad@example.com,other@example.com", "brad@example.com\nother@example.com", "a..b@example.com", ".brad@example.com", "brad@-example.com", "brad@example..com", "brad@@localhost"])(
    "rejects ambiguous or invalid mailbox input %s", (email) => {
      expect(normalizeEmail(email)).toBeNull();
    },
  );

  it("rechecks a revoked allowlist when protecting a write", () => {
    expect(assertAllowedEmail("brad@example.com", env)).toBe("brad@example.com");
    expect(() => assertAllowedEmail("brad@example.com", { ...env, CAPTURE_ALLOWED_EMAILS: "second@example.com" })).toThrow("Access denied");
    expect(() => assertAllowedEmail(undefined, env)).toThrow("Access denied");
  });

  it("accepts the explicitly allowed local smoke mailbox without inferring DNS", () => {
    expect(allowedEmail("permitcase@invalid", { CAPTURE_ALLOWED_EMAILS: "permitcase@invalid" })).toBe("permitcase@invalid");
  });
});

describe("test outbox boundary", () => {
  const local = { ...env, NODE_ENV: "development", AUTH_URL: "http://127.0.0.1:3210", CAPTURE_TEST_OUTBOX: "C:/local/outbox.jsonl" };

  it("allows a real link outbox only on explicit loopback development", () => {
    expect(localTestOutbox(local)).toBe("C:/local/outbox.jsonl");
    expect(localTestOutbox({ ...local, AUTH_URL: "http://localhost:3210" })).toBe("C:/local/outbox.jsonl");
    expect(localTestOutbox(env)).toBeNull();
  });

  it.each([
    { NODE_ENV: "production" }, { NODE_ENV: "test" }, { VERCEL: "1" },
    { VERCEL: "0" }, { AUTH_URL: "https://capture.example.com" },
    { AUTH_URL: "http://127.0.0.1.attacker.test" }, { AUTH_URL: undefined },
    { AUTH_URL: "http://user:password@localhost:3210" },
  ])("fails closed outside local development: %s", (overrides) => {
    expect(() => localTestOutbox({ ...local, ...overrides })).toThrow("unavailable");
  });
});

describe("safe configuration availability", () => {
  it("requires authentication, database and verified sender configuration", () => {
    expect(authAvailability(env)).toEqual({ available: true });
    for (const key of ["AUTH_SECRET", "AUTH_URL", "BROADBRIDGE_DATABASE_URL", "RESEND_API_KEY", "CAPTURE_EMAIL_FROM", "CAPTURE_ALLOWED_EMAILS"]) {
      expect(authAvailability({ ...env, [key]: undefined })).toEqual({ available: false });
    }
  });

  it("requires only the real local test outbox instead of Resend credentials", () => {
    expect(authAvailability({ ...env, NODE_ENV: "development", AUTH_URL: "http://127.0.0.1:3210", CAPTURE_TEST_OUTBOX: "C:/local/outbox.jsonl", RESEND_API_KEY: undefined, CAPTURE_EMAIL_FROM: undefined })).toEqual({ available: true });
    expect(authAvailability({ ...env, CAPTURE_TEST_OUTBOX: "C:/must-not-write.jsonl" })).toEqual({ available: false });
  });

  it("accepts trusted Vercel deployment metadata while still refusing a test outbox", () => {
    const preview = { ...env, AUTH_URL: undefined, VERCEL: "1", VERCEL_URL: "capture-unique-team.vercel.app" };
    expect(authAvailability(preview)).toEqual({ available: true });
    expect(configuredAuthOrigin(preview)).toBe("https://capture-unique-team.vercel.app");
    expect(configuredAuthOrigin({ ...preview, AUTH_URL: "https://capture.example.com" })).toBe("https://capture.example.com");
    expect(authAvailability({ ...preview, CAPTURE_TEST_OUTBOX: "C:/must-not-write.jsonl" })).toEqual({ available: false });
    expect(authAvailability({ ...preview, VERCEL: "0" })).toEqual({ available: false });
    expect(authAvailability({ ...preview, VERCEL_URL: "user@untrusted.example" })).toEqual({ available: false });
  });
});
