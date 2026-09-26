import "server-only";
import { neon, neonConfig } from "@neondatabase/serverless";
const loopback = (value: string) => ["127.0.0.1", "localhost", "[::1]"].includes(new URL(value).hostname);
export function localIngestionTestEnabled() {
  if (!process.env.CAPTURE_LOCAL_INGESTION_TEST && !process.env.CAPTURE_TEST_SQL_ENDPOINT) return false;
  if (process.env.CAPTURE_LOCAL_INGESTION_TEST !== "1" || process.env.NODE_ENV !== "development" || !process.env.AUTH_URL || !loopback(process.env.AUTH_URL) || !process.env.BROADBRIDGE_DATABASE_URL || !loopback(process.env.BROADBRIDGE_DATABASE_URL) || !new URL(process.env.BROADBRIDGE_DATABASE_URL).pathname.startsWith("/broadbridge_test")) throw new Error("Local ingestion test configuration is invalid.");
  for (const value of [process.env.R2_ENDPOINT, process.env.INGESTION_API_URL, process.env.CAPTURE_TEST_SQL_ENDPOINT]) if (value && !loopback(value)) throw new Error("Local ingestion tests require loopback services.");
  return true;
}
export function getSql() {
  const url = process.env.BROADBRIDGE_DATABASE_URL;
  if (!url) throw new Error("The dedicated Broadbridge database is not configured.");
  const local = localIngestionTestEnabled();
  if (local && process.env.CAPTURE_TEST_SQL_ENDPOINT) {
    const endpoint = new URL(process.env.CAPTURE_TEST_SQL_ENDPOINT);
    if (endpoint.protocol !== "http:" || endpoint.username || endpoint.password || endpoint.search || endpoint.hash) throw new Error("Invalid local SQL endpoint.");
    neonConfig.fetchEndpoint = () => endpoint.toString();
  }
  // Deliberately no DATABASE_URL or provider-default fallback.
  return neon(url);
}
