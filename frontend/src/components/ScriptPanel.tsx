import { useState } from "react";
import { api } from "../api";
import type { ResearchDossier, ScriptVariation } from "../types";
import { Spinner } from "./Spinner";

interface Props {
  dossier: ResearchDossier;
  scripts: ScriptVariation[];
  onChange: () => void;
}

export function ScriptPanel({ dossier, scripts, onChange }: Props) {
  const [busyId, setBusyId] = useState<number | "generate" | null>(null);
  const hasScripts = scripts.length > 0;
  const alreadySelected = scripts.some((s) => s.is_selected);

  async function handleGenerate() {
    setBusyId("generate");
    try {
      await api.generateScripts(dossier.id);
      onChange();
    } finally {
      setBusyId(null);
    }
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

  if (!hasScripts) {
    return (
      <section className="rounded-xl border border-gray-200 bg-white p-4">
        <h2 className="text-sm font-semibold text-gray-900">Scripts</h2>
        <button
          onClick={handleGenerate}
          disabled={busyId === "generate"}
          className="mt-3 rounded-lg bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700 disabled:opacity-50"
        >
          {busyId === "generate" ? <Spinner label="Writing scripts..." /> : "Generate 3 scripts"}
        </button>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-gray-200 bg-white p-4">
      <h2 className="mb-3 text-sm font-semibold text-gray-900">Scripts</h2>
      <div className="grid gap-3 sm:grid-cols-3">
        {scripts.map((script) => (
          <div
            key={script.id}
            className={`rounded-lg border p-3 text-sm ${
              script.is_selected ? "border-emerald-400 bg-emerald-50" : "border-gray-200"
            }`}
          >
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-gray-500">
              {script.angle_type.replace(/_/g, " ")}
            </p>
            <p className="font-medium text-gray-900">{script.hook_ms}</p>
            <p className="mt-1 line-clamp-3 text-gray-600">{script.body_ms}</p>
            {!alreadySelected && (
              <button
                onClick={() => handleSelect(script.id)}
                disabled={busyId === script.id}
                className="mt-3 w-full rounded-lg bg-gray-900 px-3 py-1.5 text-xs font-medium text-white hover:bg-gray-700 disabled:opacity-50"
              >
                {busyId === script.id ? "Selecting..." : "Use this script"}
              </button>
            )}
            {script.is_selected && <p className="mt-3 text-center text-xs font-medium text-emerald-700">Selected</p>}
          </div>
        ))}
      </div>
    </section>
  );
}