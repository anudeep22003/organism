import type { CharacterRecord } from "../../character.types";

type CharacterAttributesProps = {
  character: CharacterRecord;
};

function formatKey(key: string): string {
  return key.replace(/_/g, " ");
}

function formatValue(value: unknown): string {
  if (Array.isArray(value)) return value.join(", ");
  if (typeof value === "string") return value;
  return JSON.stringify(value);
}

export function CharacterAttributes({ character }: CharacterAttributesProps) {
  const entries = Object.entries(character.attributes).filter(
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
