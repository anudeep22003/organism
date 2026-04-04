import { useState } from "react";
import type { ReactNode } from "react";

type Tab = {
  id: string;
  label: string;
  panel: "left" | "right";
};

type BlockProps = {
  tabs?: [Tab, Tab];
  leftContent?: ReactNode;
  rightContent?: ReactNode;
  className?: string;
};

export default function Block({
  tabs,
  leftContent,
  rightContent,
  className = "",
}: BlockProps) {
  const [activePanel, setActivePanel] = useState<"left" | "right">("left");

  const hasTwoPanels = leftContent !== undefined && rightContent !== undefined;
  const showTabs = tabs !== undefined && hasTwoPanels;

  return (
    <div className={`flex h-full w-full flex-col gap-2 ${className}`}>
      {showTabs && (
        <div className="flex shrink-0 border border-border md:hidden">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={(e) => {
                e.stopPropagation();
                setActivePanel(tab.panel);
              }}
              className={`flex-1 py-1.5 text-xs transition-colors ${
                activePanel === tab.panel
                  ? "bg-foreground text-background"
                  : "text-muted-foreground"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      <div className="flex min-h-0 flex-1 gap-4">
        {leftContent !== undefined && (
          <div
            className={`min-h-0 flex-1 ${
              showTabs ? (activePanel === "left" ? "flex" : "hidden") : "flex"
            } md:flex`}
          >
            {leftContent}
          </div>
        )}

        {rightContent !== undefined && (
          <div
            className={`min-h-0 flex-1 ${
              showTabs ? (activePanel === "right" ? "flex" : "hidden") : "flex"
            } md:flex`}
          >
            {rightContent}
          </div>
        )}
      </div>
    </div>
  );
}
