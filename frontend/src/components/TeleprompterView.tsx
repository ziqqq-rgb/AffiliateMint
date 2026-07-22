import { useState } from "react";
import type { ScriptVariation } from "../types";

export function TeleprompterView({ script, onClose }: { script: ScriptVariation; onClose: () => void }) {
  const [copied, setCopied] = useState(false);
  const hashtags: string[] = JSON.parse(script.hashtags);

  async function copyCaption() {
    const text = `${script.caption_ms}\n\n${hashtags.map((h) => `#${h}`).join(" ")}`;
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="min-h-screen bg-black text-white">
      <div className="flex items-center justify-between px-6 py-4">
        <span className="text-xs uppercase tracking-widest text-gray-400">
          {script.angle_type.replace(/_/g, " ")}
        </span>
        <div className="flex gap-4">
          <button onClick={copyCaption} className="text-sm text-gray-400 hover:text-white">
            {copied ? "Copied!" : "Copy caption + hashtags"}
          </button>
          <button onClick={onClose} className="text-sm text-gray-400 hover:text-white">
            Close
          </button>
        </div>
      </div>

      <div className="mx-auto max-w-2xl space-y-8 px-8 py-12 font-serif text-3xl leading-relaxed">
        <p>{script.hook_ms}</p>
        <p>{script.body_ms}</p>
        <p className="font-semibold text-emerald-300">{script.cta_ms}</p>
      </div>

      {script.visual_notes && (
        <div className="mx-auto max-w-2xl border-t border-gray-800 px-8 py-6 font-sans text-sm text-gray-400">
          <p className="mb-1 font-medium text-gray-300">Shot notes</p>
          <p>{script.visual_notes}</p>
        </div>
      )}
    </div>
  );
}