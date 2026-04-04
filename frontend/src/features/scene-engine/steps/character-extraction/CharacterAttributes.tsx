import type { CharacterRecord } from "./character-extraction.types";

type CharacterAttributesProps = {
  character: CharacterRecord;
};

export function CharacterAttributes({ character }: CharacterAttributesProps) {
  return (
    <pre className="whitespace-pre-wrap text-[10px] text-muted-foreground">
      {JSON.stringify(character.attributes, null, 2)}
    </pre>
  );
}
