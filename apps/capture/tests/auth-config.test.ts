import { beforeEach, describe, expect, it, vi } from "vitest";
import type { NextAuthConfig } from "next-auth";

const state = vi.hoisted(() => ({ factory: undefined as undefined | (() => NextAuthConfig) }));
vi.mock("server-only", () => ({}));
vi.mock("next-auth", () => ({ default: (factory: () => NextAuthConfig) => {
  state.factory = factory;
  return { handlers: {}, auth: vi.fn(), signIn: vi.fn(), signOut: vi.fn() };
} }));
vi.mock("../lib/auth-adapter", () => ({ createAuthAdapter: () => ({}), claimEmailIssuance: vi.fn() }));
import "../auth";

beforeEach(() => { vi.restoreAllMocks(); });

describe("authentication diagnostic redaction", () => {
  it("reports a recognized Auth.js type and database SQLSTATE without raw details", () => {
    const log = vi.spyOn(console, "error").mockImplementation(() => {});
    const error = Object.assign(new Error("secret URL and token"), {
      type: "AdapterError", cause: { err: Object.assign(new Error("private SQL"), { name: "NeonDbError", code: "23514" }) },
    });
    state.factory!().logger!.error!(error);
    expect(log).toHaveBeenCalledWith("Capture authentication operation failed.", {
      type: "AdapterError", causeType: "NeonDbError", code: "23514",
    });
    expect(JSON.stringify(log.mock.calls)).not.toMatch(/secret|private/);
  });

  it("never logs arbitrary names, codes, messages, stacks, or cause fields", () => {
    const log = vi.spyOn(console, "error").mockImplementation(() => {});
    const error = Object.assign(new Error("private message"), {
      type: "private type", cause: { err: { name: "private name", code: "private code", query: "private SQL" } },
    });
    state.factory!().logger!.error!(error);
    expect(log).toHaveBeenCalledWith("Capture authentication operation failed.", {
      type: "Unknown", causeType: "Unknown", code: "Unknown",
    });
    expect(JSON.stringify(log.mock.calls)).not.toContain("private");
  });
});
