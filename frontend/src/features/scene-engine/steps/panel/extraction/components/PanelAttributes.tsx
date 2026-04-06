import type { PanelRecord } from "../../panel.types";

type PanelAttributesProps = {
  panel: PanelRecord;
};

function formatKey(key: string): string {
  return key.replace(/_/g, " ");
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

export function PanelAttributes({ panel }: PanelAttributesProps) {
  const entries = Object.entries(panel.attributes).filter(
    ([, v]) => v !== null && v !== undefined && v !== "",
  );

  return (
    <div className="flex flex-col gap-3">
      {entries.map(([key, value]) => (
        <div key={key} className="flex flex-col gap-0.5">
          <span className="text-[10px] font-semibold uppercase tracking-wide text-foreground/60">
            {formatKey(key)}
          </span>
          <span className="text-xs text-foreground">
            {formatValue(value)}
          </span>
        </div>
      ))}
    </div>
  );
}
