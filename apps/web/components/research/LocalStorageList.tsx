"use client";
// LocalStorageList — shared CRUD grid for Ideas / Signal Lab / Graveyard.
//
// Each entry is stored under a namespaced key in ``window.localStorage``.  We
// do NOT sync to the server; these are personal, client-only scratchpads.
import { useCallback, useEffect, useMemo, useState } from "react";

export interface LSField {
  name: string;
  label: string;
  placeholder?: string;
  type?: "text" | "textarea" | "select";
  options?: string[];
  width?: string; // tailwind-ish hint, e.g. "w-40"
}

export interface LSEntry {
  id: string;
  created_at: string;
  updated_at: string;
  [k: string]: unknown;
}

interface Props {
  storageKey: string;
  title: string;
  fields: LSField[];
  emptyCopy?: string;
}

function uid(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

function readAll(key: string): LSEntry[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? (parsed as LSEntry[]) : [];
  } catch {
    return [];
  }
}

function writeAll(key: string, items: LSEntry[]): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(key, JSON.stringify(items));
  } catch {
    /* ignore quota errors — client-only */
  }
}

export function LocalStorageList({ storageKey, title, fields, emptyCopy }: Props) {
  const [items, setItems] = useState<LSEntry[]>([]);
  const [draft, setDraft] = useState<Record<string, string>>({});
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setItems(readAll(storageKey));
    setReady(true);
  }, [storageKey]);

  const blankDraft = useMemo(() => {
    const d: Record<string, string> = {};
    for (const f of fields) {
      d[f.name] = f.type === "select" && f.options?.length ? f.options[0] : "";
    }
    return d;
  }, [fields]);

  useEffect(() => {
    if (Object.keys(draft).length === 0) setDraft(blankDraft);
  }, [blankDraft, draft]);

  const add = useCallback(() => {
    const hasContent = Object.values(draft).some(
      (v) => typeof v === "string" && v.trim() !== "",
    );
    if (!hasContent) return;
    const now = new Date().toISOString();
    const entry: LSEntry = {
      id: uid(),
      created_at: now,
      updated_at: now,
      ...draft,
    };
    const next = [entry, ...items];
    setItems(next);
    writeAll(storageKey, next);
    setDraft(blankDraft);
  }, [blankDraft, draft, items, storageKey]);

  const remove = useCallback(
    (id: string) => {
      const next = items.filter((x) => x.id !== id);
      setItems(next);
      writeAll(storageKey, next);
    },
    [items, storageKey],
  );

  const patch = useCallback(
    (id: string, changes: Partial<LSEntry>) => {
      const next = items.map((x) =>
        x.id === id ? { ...x, ...changes, updated_at: new Date().toISOString() } : x,
      );
      setItems(next);
      writeAll(storageKey, next);
    },
    [items, storageKey],
  );

  return (
    <div className="space-y-4">
      <div
        className="rounded-md border p-3"
        style={{ background: "var(--surface)", borderColor: "var(--border)" }}
      >
        <div className="text-[10px] uppercase tracking-widest text-[color:var(--muted)] mb-2">
          add {title}
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
          {fields.map((f) => (
            <div key={f.name} className="flex flex-col gap-1">
              <label className="text-[10px] mono text-[color:var(--fg-muted)]">
                {f.label}
              </label>
              {f.type === "textarea" ? (
                <textarea
                  rows={2}
                  value={draft[f.name] ?? ""}
                  placeholder={f.placeholder}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, [f.name]: e.target.value }))
                  }
                  className="py-1.5 px-2 rounded bg-transparent border text-sm outline-none"
                  style={{ borderColor: "var(--border)" }}
                />
              ) : f.type === "select" && f.options ? (
                <select
                  value={draft[f.name] ?? f.options[0]}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, [f.name]: e.target.value }))
                  }
                  className="py-1.5 px-2 rounded bg-transparent border text-sm outline-none"
                  style={{ borderColor: "var(--border)" }}
                >
                  {f.options.map((o) => (
                    <option key={o} value={o}>
                      {o}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  value={draft[f.name] ?? ""}
                  placeholder={f.placeholder}
                  onChange={(e) =>
                    setDraft((d) => ({ ...d, [f.name]: e.target.value }))
                  }
                  className="py-1.5 px-2 rounded bg-transparent border text-sm outline-none"
                  style={{ borderColor: "var(--border)" }}
                />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-end mt-2">
          <button
            type="button"
            onClick={add}
            className="px-3 py-1 text-[12px] rounded border mono"
            style={{
              borderColor: "var(--border)",
              background: "var(--surface-raised)",
            }}
          >
            + add
          </button>
        </div>
      </div>

      {ready && items.length === 0 ? (
        <div
          className="rounded-md border p-4 text-sm text-[color:var(--fg-muted)]"
          style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
        >
          {emptyCopy ?? "아직 저장된 항목이 없습니다. 위 폼에서 추가하세요."}
        </div>
      ) : null}

      <ul className="space-y-2">
        {items.map((it) => (
          <li
            key={it.id}
            className="rounded-md border p-3"
            style={{ background: "var(--surface)", borderColor: "var(--border-soft)" }}
          >
            <div className="flex items-baseline justify-between gap-2 text-[11px] mono text-[color:var(--fg-muted)]">
              <span>
                {new Date(it.created_at).toLocaleString()} · id {it.id.slice(0, 8)}
              </span>
              <button
                type="button"
                onClick={() => remove(it.id)}
                className="px-2 py-0.5 rounded border"
                style={{ borderColor: "var(--border)" }}
              >
                delete
              </button>
            </div>
            <div className="mt-2 grid grid-cols-1 md:grid-cols-2 gap-x-3 gap-y-1 text-[13px]">
              {fields.map((f) => {
                const val = (it[f.name] as string) ?? "";
                if (f.type === "select" && f.options) {
                  return (
                    <div key={f.name} className="flex items-center gap-2">
                      <span className="text-[10px] mono text-[color:var(--fg-muted)] w-16">
                        {f.label}
                      </span>
                      <select
                        value={val || f.options[0]}
                        onChange={(e) => patch(it.id, { [f.name]: e.target.value })}
                        className="py-0.5 px-2 rounded bg-transparent border text-[12px] outline-none"
                        style={{ borderColor: "var(--border)" }}
                      >
                        {f.options.map((o) => (
                          <option key={o} value={o}>
                            {o}
                          </option>
                        ))}
                      </select>
                    </div>
                  );
                }
                return (
                  <div key={f.name}>
                    <div className="text-[10px] mono text-[color:var(--fg-muted)]">
                      {f.label}
                    </div>
                    <div className="leading-snug whitespace-pre-wrap">
                      {val || <span className="text-[color:var(--fg-muted)]">—</span>}
                    </div>
                  </div>
                );
              })}
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
