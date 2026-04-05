import { EmptyState } from "./components/EmptyState";
import { CharacterRenderList } from "./components/CharacterRenderList";

const hasRenderedCharacters = false;

export default function CharacterRenderingStep() {
  return (
    <div className="flex h-full w-full flex-col">
      {hasRenderedCharacters ? (
        <CharacterRenderList />
      ) : (
        <EmptyState />
      )}
    </div>
  );
}
