import type { PanelBundle } from "../../panel.types";
import { PanelAttributes } from "./PanelAttributes";
import { RefImageTray } from "./RefImageTray";

type PanelCardProps = {
  bundle: PanelBundle;
  displayIndex: number;
  onActivate: () => void;
};

export function PanelCard({ bundle, displayIndex, onActivate }: PanelCardProps) {
  return (
    <div className="flex" onClick={onActivate}>
      <div className="min-w-0 flex-1 cursor-pointer border border-border bg-muted/20 p-3 hover:bg-muted/40">
        <span className="mb-2 block text-[10px] font-semibold uppercase tracking-wide text-foreground/60">
          Panel {displayIndex}
        </span>
        <PanelAttributes panel={bundle.panel} />
      </div>
      <RefImageTray images={bundle.referenceImages} variant="card" />
    </div>
  );
}
