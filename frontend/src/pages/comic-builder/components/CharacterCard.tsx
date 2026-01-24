import type { Character } from "../types/consolidatedState";

const formatKey = (key: string): string => {
  // Convert camelCase to Title Case with spaces
  return key
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (str) => str.toUpperCase())
    .trim();
};

type CharacterCardProps = {
  character: Character;
};

export const CharacterCard = ({ character }: CharacterCardProps) => {
  // Display fields in a readable order, excluding internal fields
  const displayFields: (keyof Character)[] = [
    "name",
    "brief",
    "characterType",
    "role",
    "era",
    "visualForm",
    "colorPalette",
    "distinctiveMarkers",
    "demeanor",
  ];

  return (
    <div className="border border-neutral-200 bg-white p-4 space-y-2">
      {displayFields.map((key) => {
        const value = character[key];
        if (value === null || value === undefined) return null;
        return (
          <div key={key} className="text-sm">
            <span className="font-medium text-neutral-900">
              {formatKey(key)}:{" "}
            </span>
            <span className="text-neutral-600">{String(value)}</span>
          </div>
        );
      })}
    </div>
  );
};

