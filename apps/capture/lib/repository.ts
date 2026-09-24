import "server-only";
import { getSql } from "./db";
import { parseCase, parseWorkflow, type StoredCase, type StoredWorkflow, type CaseRecord, type WorkflowRecord } from "./validation";

export async function loadCapture(actor: string): Promise<{ cases: StoredCase[]; workflow: StoredWorkflow | null }> {
  const sql = getSql();
  const [cases, workflow] = await Promise.all([
    sql`SELECT record, updated_at::text AS revision FROM broadbridge.cases ORDER BY case_id`,
    sql`SELECT record, updated_at::text AS revision FROM broadbridge.workflow WHERE author_email = lower(${actor})`,
  ]);
  return {
    cases: cases.map(row => ({ record: parseCase(row.record), revision: row.revision as string })),
    workflow: workflow.length ? { record: parseWorkflow(workflow[0].record), revision: workflow[0].revision as string } : null,
  };
}

export async function persistCase(record: CaseRecord, actor: string, revision: string | null): Promise<StoredCase> {
  const sql = getSql();
  const rows = await sql`SELECT broadbridge.capture_save_case(${JSON.stringify(record)}::jsonb, ${actor}, ${revision}::timestamptz) AS saved`;
  return rows[0].saved as StoredCase;
}

export async function persistWorkflow(record: WorkflowRecord, actor: string, revision: string | null): Promise<StoredWorkflow> {
  const sql = getSql();
  const rows = await sql`SELECT broadbridge.capture_save_workflow(${JSON.stringify(record)}::jsonb, ${actor}, ${revision}::timestamptz) AS saved`;
  return rows[0].saved as StoredWorkflow;
}

export async function removeCase(caseId: string, actor: string, revision: string): Promise<void> {
  const sql = getSql();
  await sql`SELECT broadbridge.capture_delete_case(${caseId}, ${actor}, ${revision}::timestamptz)`;
}
