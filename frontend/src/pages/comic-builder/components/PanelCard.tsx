import type { ComicPanel } from "../types/consolidatedState";

type PanelCardProps = {
  panel: ComicPanel;
  index: number;
};

export const PanelCard = ({ panel, index }: PanelCardProps) => {
  return (
    <div className="flex-shrink-0 w-80 snap-center border border-neutral-300 bg-white">
      {/* Panel number header */}
      <div className="bg-neutral-900 text-white px-3 py-1 text-sm font-medium">
        Panel {index + 1}
      </div>

      {/* Render placeholder or image */}
      <div className="aspect-square bg-neutral-100 flex items-center justify-center border-b border-neutral-200">
        {panel.render?.url ? (
          <img
            src={panel.render.url}
            alt={`Panel ${index + 1}`}
            className="w-full h-full object-cover"
          />
        ) : (
          <span className="text-neutral-400 text-sm">
            Render not yet generated
          </span>
        )}
      </div>

      {/* Panel details */}
      <div className="p-3 space-y-2 text-sm">
        <div>
          <span className="font-medium text-neutral-900">
            Background:{" "}
          </span>
          <span className="text-neutral-600">{panel.background}</span>
        </div>

        <div>
          <span className="font-medium text-neutral-900">
            Characters:{" "}
          </span>
          <span className="text-neutral-600">
            {panel.characters.join(", ") || "None"}
          </span>
        </div>

        <div>
          <span className="font-medium text-neutral-900">
            Dialogue:{" "}
          </span>
          <span className="text-neutral-600 italic">
            {panel.dialogue || "—"}
          </span>
        </div>
      </div>
    </div>
  );
};
