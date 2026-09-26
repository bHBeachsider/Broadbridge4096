import { afterEach, describe, expect, it, vi } from "vitest";
vi.mock("server-only", () => ({}));
import { localIngestionTestEnabled } from "../lib/db";
afterEach(() => vi.unstubAllEnvs());
function local() { for (const [key,value] of Object.entries({ NODE_ENV: "development", CAPTURE_LOCAL_INGESTION_TEST: "1", AUTH_URL: "http://127.0.0.1:3100", BROADBRIDGE_DATABASE_URL: "postgres://test:test@127.0.0.1/broadbridge_test_t7", R2_ENDPOINT: "http://127.0.0.1:9000", INGESTION_API_URL: "http://127.0.0.1:8080", CAPTURE_TEST_SQL_ENDPOINT: "http://127.0.0.1:9001/sql" })) vi.stubEnv(key,value); }
describe("local test transport isolation", () => {
  it("permits only explicitly opted-in loopback development targets", () => { local(); expect(localIngestionTestEnabled()).toBe(true); });
  it.each([["NODE_ENV","production"],["AUTH_URL","https://capture.example"],["BROADBRIDGE_DATABASE_URL","postgres://u:p@remote.example/broadbridge_test"],["BROADBRIDGE_DATABASE_URL","postgres://u:p@127.0.0.1/production"],["R2_ENDPOINT","https://cloud.example"],["INGESTION_API_URL","https://cloud.example"],["CAPTURE_TEST_SQL_ENDPOINT","http://remote.example/sql"],["CAPTURE_LOCAL_INGESTION_TEST","0"]])("rejects unsafe %s", (key,value) => { local(); vi.stubEnv(key,value); expect(() => localIngestionTestEnabled()).toThrow(); });
});
