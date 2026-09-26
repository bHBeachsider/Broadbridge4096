import { defineConfig } from "@playwright/test";

const origin = process.env.AUTH_URL ?? "http://127.0.0.1:3100";
const url = new URL(origin);
if (url.hostname !== "127.0.0.1" || url.protocol !== "http:") {
  throw new Error("The test magic-link smoke runs only on the local development server.");
}

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  expect: { timeout: 20_000 },
  workers: 1,
  retries: 0,
  reporter: "list",
  use: { baseURL: origin, browserName: "chromium", viewport: { width: 1440, height: 1000 }, trace: "off" },
  webServer: {
    command: `npm run dev -- --port ${url.port || "3100"}`,
    url: `${origin}/signin`,
    reuseExistingServer: false,
    timeout: 120_000,
  },
});
