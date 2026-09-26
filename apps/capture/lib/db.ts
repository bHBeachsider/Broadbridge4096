import "server-only";
import { neon } from "@neondatabase/serverless";

export function getSql() {
  const url = process.env.BROADBRIDGE_DATABASE_URL;
  if (!url) throw new Error("The dedicated Broadbridge database is not configured.");
  // Deliberately no DATABASE_URL or provider-default fallback.
  return neon(url);
}
