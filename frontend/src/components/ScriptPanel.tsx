import { useState } from "react";
import { api } from "../api";
import type { ScriptVariation } from "../types";

interface Props {
  scripts: ScriptVariation[];
  onChange: () => void;
}

interface DraftFields {
  hook_ms: string;
  body_ms: string;
  cta_ms: string;
  caption_ms: string;
  visual_notes: string;
}

function toDraft(script: ScriptVariation): DraftFields {
  return {
    hook_ms: script.hook_ms,
    body_ms: script.body_ms,
    cta_ms: script.cta_ms,
    caption_ms: script.caption_ms,
    visual_notes: script.visual_notes,
  };
}

export function ScriptPanel({ scripts, onChange }: Props) {
  const [busyId, setBusyId] = useState<number | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [draft, setDraft] = useState<DraftFields | null>(null);
  const alreadySelected = scripts.some((s) => s.is_selected);

  function startEdit(script: ScriptVariation) {
    setEditingId(script.id);
    setDraft(toDraft(script));
  }

  async function handleSelect(scriptId: number) {
    setBusyId(scriptId);
    try {
      await api.selectScript(scriptId);
      onChange();
    } finally {
      setBusyId(null);
    }
  }

  async function handleSaveEdit(scriptId: number) {
    if (!draft) return;
    setBusyId(scriptId);
    try {
      await api.updateScript(scriptId, draft);
      setEditingId(null);
      setDraft(null);
      onChange();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4">
      <h2 className="mb-3 text-sm font-semibold text-gray-900">Scripts</h2>
      <div className="grid gap-3 sm:grid-cols-3">
        {scripts.map((script) => {
          const isEditing = editingId === script.id;
          return (
            <div
              key={script.id}
              className={`rounded-lg border p-3 text-sm ${
                script.is_selected ? "border-emerald-400 bg-emerald-50" : "border-gray-200"
              }`}
            >
              <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
                {script.angle_type.replace(/_/g, " ")}
              </p>

              {isEditing && draft ? (
                <div className="space-y-2">
                  <EditField label="Hook" value={draft.hook_ms} onChange={(v) => setDraft({ ...draft, hook_ms: v })} />
                  <EditField label="Body" value={draft.body_ms} onChange={(v) => setDraft({ ...draft, body_ms: v })} />
                  <EditField label="CTA" value={draft.cta_ms} onChange={(v) => setDraft({ ...draft, cta_ms: v })} />
                  <EditField
                    label="Caption"
                    value={draft.caption_ms}
                    onChange={(v) => setDraft({ ...draft, caption_ms: v })}
                  />
                  <EditField
                    label="Shot notes"
                    value={draft.visual_notes}
                    onChange={(v) => setDraft({ ...draft, visual_notes: v })}
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleSaveEdit(script.id)}
                      disabled={busyId === script.id}
                      className="flex-1 rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-700 disabled:opacity-50"
                    >
                      {busyId === script.id ? "Saving..." : "Save"}
                    </button>
                    <button
                      onClick={() => {
                        setEditingId(null);
                        setDraft(null);
                      }}
                      className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Cancel
                    </button>
                  </div>
                </div>
              ) : (
                <>
                  <p className="font-medium text-gray-900">{script.hook_ms}</p>
                  <p className="mt-1 line-clamp-3 text-gray-600">{script.body_ms}</p>
                  <div className="mt-3 flex gap-2">
                    {!alreadySelected && (
                      <button
                        onClick={() => handleSelect(script.id)}
                        disabled={busyId === script.id}
                        className="flex-1 rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-700 disabled:opacity-50"
                      >
                        {busyId === script.id ? "Selecting..." : "Use this script"}
                      </button>
                    )}
                    <button
                      onClick={() => startEdit(script)}
                      className="rounded-lg border border-gray-300 px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-gray-50"
                    >
                      Edit
                    </button>
                  </div>
                  {script.is_selected && (
                    <p className="mt-2 text-center text-xs font-medium text-emerald-700">Selected</p>
                  )}
                </>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}

function EditField({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <label className="block text-xs text-gray-600">
      {label}
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        rows={2}
        className="mt-1 w-full rounded-lg border border-gray-300 px-2 py-1 text-sm"
      />
    </label>
  );
}