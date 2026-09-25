// @vitest-environment jsdom
import React, { act } from "react";
import { createRoot, type Root } from "react-dom/client";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import CaptureApp from "../components/CaptureApp";
import type { CaseRecord } from "../lib/validation";
import syntheticCase from "../../../packs/oil-gas/tests/fixtures/SYN-TRAIN-001.json";

const actions = vi.hoisted(() => ({ saveCase: vi.fn(), saveWorkflow: vi.fn(), deleteCase: vi.fn() }));
vi.mock("../app/actions", () => ({
  saveCaseAction: actions.saveCase,
  saveWorkflowAction: actions.saveWorkflow,
  deleteCaseAction: actions.deleteCase,
}));

let host: HTMLDivElement;
let root: Root;
let caseRecord: CaseRecord;

beforeEach(() => {
  vi.useFakeTimers();
  vi.resetAllMocks();
  (globalThis as { IS_REACT_ACT_ENVIRONMENT?: boolean }).IS_REACT_ACT_ENVIRONMENT = true;
  caseRecord = structuredClone(syntheticCase) as CaseRecord;
  actions.saveCase.mockImplementation(async (record: CaseRecord) => ({ ok: true, value: { record, revision: "next" } }));
  actions.saveWorkflow.mockImplementation(async (record: unknown) => ({ ok: true, value: { record, revision: "next" } }));
  host = document.createElement("div");
  document.body.append(host);
  root = createRoot(host);
});

afterEach(async () => {
  await act(async () => root?.unmount());
  host?.remove();
  vi.useRealTimers();
});

async function mount(record = caseRecord, onSignOut?: () => Promise<void>) {
  await act(async () => root.render(<CaptureApp initialCases={[{ record, revision: "first" }]} initialWorkflow={null} email="reviewer@example.test" onSignOut={onSignOut} />));
  await click(record.case_id, true);
}

async function click(label: string, partial = false) {
  const button = Array.from(host.querySelectorAll("button")).find((item) => partial ? item.textContent?.includes(label) : item.textContent === label);
  expect(button, `Button ${label}`).toBeTruthy();
  await act(async () => button!.click());
}

async function input(selector: string, value: string) {
  const element = host.querySelector<HTMLInputElement | HTMLTextAreaElement>(selector)!;
  expect(element, selector).toBeTruthy();
  const proto = element.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  await act(async () => {
    Object.getOwnPropertyDescriptor(proto, "value")!.set!.call(element, value);
    element.dispatchEvent(new Event("input", { bubbles: true }));
  });
}

describe("capture UI save behavior", () => {
  it("keeps later edits while a first save is in flight and serializes the next revision", async () => {
    let resolveFirst!: (value: unknown) => void;
    actions.saveCase.mockImplementationOnce(() => new Promise((resolve) => { resolveFirst = resolve; }));
    await mount();
    await input("#id_title", "First edit");
    await act(async () => { await vi.advanceTimersByTimeAsync(1199); });
    expect(actions.saveCase).not.toHaveBeenCalled();
    await act(async () => { await vi.advanceTimersByTimeAsync(1); });
    expect(actions.saveCase).toHaveBeenCalledTimes(1);
    const first = structuredClone(actions.saveCase.mock.calls[0][0]);
    await input("#id_title", "Latest edit");
    expect(actions.saveCase).toHaveBeenCalledTimes(1);
    await act(async () => { resolveFirst({ ok: true, value: { record: first, revision: "second" } }); });
    expect((host.querySelector("#id_title") as HTMLInputElement).value).toBe("Latest edit");
    expect(actions.saveCase).toHaveBeenCalledTimes(2);
    expect(actions.saveCase.mock.calls[1][0].identity.title).toBe("Latest edit");
    expect(actions.saveCase.mock.calls[1][1]).toBe("second");
  });

  it("retains a conflicting draft, blocks export, and does not silently retry", async () => {
    actions.saveCase.mockResolvedValue({ ok: false, conflict: true, error: "Changed in another tab" });
    await mount();
    await input("#id_title", "Keep this local draft");
    await act(async () => { await vi.advanceTimersByTimeAsync(1200); });
    await click("All records as JSON");
    expect(host.textContent).toContain("Changed in another tab");
    expect((host.querySelector("#id_title") as HTMLInputElement).value).toBe("Keep this local draft");
    expect(host.querySelector("pre")).toBeNull();
    await input("#id_title", "Keep another local change");
    await act(async () => { await vi.advanceTimersByTimeAsync(2400); });
    expect(actions.saveCase).toHaveBeenCalledTimes(1);
    const event = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  });

  it("clears signoff when signed content is edited and retains boolean evidence", async () => {
    caseRecord.evidence = [{ item: "Synthetic", format: "txt", restriction: "", available_at_decision_time: true }];
    await mount();
    await input("#id_title", "A reviewed case changed");
    await act(async () => { await vi.advanceTimersByTimeAsync(1200); });
    const saved = actions.saveCase.mock.calls[0][0];
    expect(saved.status).toBe("draft");
    expect(saved.reviewer_signoff.signed).toBe(false);
    expect(saved.evidence[0].available_at_decision_time).toBe(true);
  });

  it("requires named dated signoff before signing and never reuses deleted question IDs", async () => {
    caseRecord.status = "draft";
    caseRecord.reviewer_signoff = { signed: false, name: "", date: "" };
    await mount();
    await click("Sign-off");
    await act(async () => (host.querySelector("#signed") as HTMLInputElement).click());
    expect((host.querySelector("#signed") as HTMLInputElement).checked).toBe(false);
    expect((host.querySelector("#statusSel") as HTMLSelectElement).value).toBe("draft");
    await click("C · Test questions");
    await click("+ Question");
    await click("+ Question");
    const before = Array.from(host.querySelectorAll(".qh b"), (item) => item.textContent);
    await act(async () => (host.querySelectorAll<HTMLButtonElement>(".qh button")[1]).click());
    await click("+ Question");
    const after = Array.from(host.querySelectorAll(".qh b"), (item) => item.textContent);
    expect(new Set(after).size).toBe(after.length);
    expect(after[2]).not.toBe(before[1]);
    expect(after[2]).not.toBe(before[2]);
  });

  it("flushes pending changes before showing an export and renders captured text safely", async () => {
    await mount();
    await input("#id_title", '<img src=x onerror="alert(1)">');
    await click("All records as JSON");
    expect(actions.saveCase).toHaveBeenCalledTimes(1);
    const exported = JSON.parse(host.querySelector("pre")!.textContent!);
    expect(exported.cases[0].identity.title).toBe('<img src=x onerror="alert(1)">');
    expect(host.querySelector("img")).toBeNull();
  });

  it("keeps failed changes for an explicit retry and clears pending timers on unmount", async () => {
    actions.saveCase.mockResolvedValueOnce({ ok: false, error: "Temporarily unavailable" });
    await mount();
    await input("#id_title", "Keep through a failure");
    await act(async () => { await vi.advanceTimersByTimeAsync(1200); });
    expect(host.textContent).toContain("Temporarily unavailable");
    await click("Retry save");
    expect(actions.saveCase).toHaveBeenCalledTimes(2);
    expect(actions.saveCase.mock.calls[1][0].identity.title).toBe("Keep through a failure");
    await input("#id_title", "Unsaved before leaving");
    await act(async () => root.unmount());
    await act(async () => { await vi.advanceTimersByTimeAsync(2400); });
    expect(actions.saveCase).toHaveBeenCalledTimes(2);
  });

  it("flushes pending edits before sign-out and locks editing until navigation", async () => {
    let finishSave!: (value: unknown) => void;
    actions.saveCase.mockImplementationOnce(() => new Promise((resolve) => { finishSave = resolve; }));
    const onSignOut = vi.fn(async () => undefined);
    await mount(caseRecord, onSignOut);
    await input("#id_title", "Save before signing out");
    await click("Sign out");
    expect(actions.saveCase).toHaveBeenCalledTimes(1);
    expect(onSignOut).not.toHaveBeenCalled();
    expect(host.querySelector("#id_title")!.matches(":disabled")).toBe(true);
    const saved = structuredClone(actions.saveCase.mock.calls[0][0]);
    await act(async () => { finishSave({ ok: true, value: { record: saved, revision: "saved" } }); });
    expect(onSignOut).toHaveBeenCalledTimes(1);
    expect(saved.identity.title).toBe("Save before signing out");
    expect(host.querySelector("#id_title")!.matches(":disabled")).toBe(true);
  });

  it.each([false, true])("blocks sign-out on save failure (conflict=%s) and keeps the draft editable", async (conflict) => {
    actions.saveCase.mockResolvedValue({ ok: false, error: "Could not save this draft", conflict });
    const onSignOut = vi.fn(async () => undefined);
    await mount(caseRecord, onSignOut);
    await input("#id_title", "Keep this unsaved draft");
    await click("Sign out");
    expect(onSignOut).not.toHaveBeenCalled();
    expect(host.textContent).toContain("Sign out is paused");
    expect((host.querySelector("#id_title") as HTMLInputElement).value).toBe("Keep this unsaved draft");
    expect(host.querySelector("#id_title")!.matches(":disabled")).toBe(false);
    const event = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(event);
    expect(event.defaultPrevented).toBe(true);
  });
});
