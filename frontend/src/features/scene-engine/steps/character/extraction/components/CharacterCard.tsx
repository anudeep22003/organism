import type { CharacterBundle } from "../../character.types";
import { CharacterAttributes } from "./CharacterAttributes";
import { RefImageTray } from "./RefImageTray";

type CharacterCardProps = {
  bundle: CharacterBundle;
  onActivate: () => void;
};

export function CharacterCard({ bundle, onActivate }: CharacterCardProps) {
  return (
    <div className="flex" onClick={onActivate}>
      <div className="min-w-0 flex-1 cursor-pointer border border-border bg-muted/20 p-3 hover:bg-muted/40">
        <CharacterAttributes character={bundle.character} />
      </div>
      <RefImageTray images={bundle.referenceImages} variant="card" />
    </div>
  );
}
