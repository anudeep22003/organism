import type { PanelBundle } from "../../panel.types";
import { PanelCard } from "./PanelCard";

type PanelListProps = {
  panels: PanelBundle[];
  onActivate: (panelId: string) => void;
};

export function PanelList({ panels, onActivate }: PanelListProps) {
  return (
    <div className="h-full w-full overflow-y-auto p-4">
      <div className="mx-auto flex w-full max-w-4xl flex-col gap-2">
        {panels.map((bundle, index) => (
          <PanelCard
            key={bundle.panel.id}
            bundle={bundle}
            displayIndex={index + 1}
            onActivate={() => onActivate(bundle.panel.id)}
          />
        ))}
      </div>
    </div>
  );
}
