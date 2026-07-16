/** FR-4.3: large, clean script text for use while filming. */
import type { ScriptVariation } from "../types";

export function TeleprompterView({ script }: { script: ScriptVariation }) {
  return (
    <div className="mx-auto max-w-2xl space-y-6 p-8 text-2xl leading-relaxed">
      <p>{script.hook_ms}</p>
      <p>{script.body_ms}</p>
      <p className="font-medium">{script.cta_ms}</p>
    </div>
  );
}
