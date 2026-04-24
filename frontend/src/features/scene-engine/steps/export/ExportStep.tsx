import { useState } from "react";
import { BACKEND_URL } from "@/constants";
import { useSceneEngine } from "@scene-engine/context";
import { STORY_API_BASE } from "@scene-engine/core/scene-engine.constants";

type ExportFormat = "zip" | "instagram" | "pdf";

type ExportOption = {
  id: ExportFormat;
  title: string;
  description: string;
  cta: string;
};

const EXPORT_OPTIONS: ExportOption[] = [
  {
    id: "pdf",
    title: "Export as PDF",
    description: "Download your comic as a print-ready PDF file.",
    cta: "Download PDF",
  },
  {
    id: "zip",
    title: "Export as ZIP",
    description: "Download all panel images as a ZIP archive.",
    cta: "Download ZIP",
  },
  {
    id: "instagram",
    title: "Instagram Export",
    description: "Download your panels formatted for Instagram.",
    cta: "Download for Instagram",
  },
];

function triggerBrowserDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

type ExportRowProps = {
  option: ExportOption;
  projectId: string;
  storyId: string;
};

function ExportRow({ option, projectId, storyId }: ExportRowProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleDownload = async () => {
    setIsDownloading(true);
    setError(null);
    try {
      const url = `${BACKEND_URL}${STORY_API_BASE}/project/${projectId}/story/${storyId}/export/${option.id}`;
      const response = await fetch(url, {
        credentials: "include",
      });

      if (!response.ok) {
        if (response.status === 422) {
          setError("No rendered panels yet. Complete Step 5 before exporting.");
        } else if (response.status === 404) {
          setError("Story not found. Try refreshing.");
        } else {
          setError("Export failed. Try again.");
        }
        return;
      }

      const blob = await response.blob();
      const disposition = response.headers.get("Content-Disposition") ?? "";
      const match = disposition.match(/filename="([^"]+)"/);
      const filename = match?.[1] ?? `comic-${storyId}.${option.id === "pdf" ? "pdf" : "zip"}`;
      triggerBrowserDownload(blob, filename);
    } catch {
      setError("Export failed. Try again.");
    } finally {
      setIsDownloading(false);
    }
  };

  return (
    <div className="flex flex-col border border-border p-4">
      <div className="flex items-center justify-between">
        <div className="flex flex-col gap-1">
          <span className="text-xs font-medium">{option.title}</span>
          <span className="text-[10px] text-muted-foreground">
            {option.description}
          </span>
        </div>
        <button
          onClick={() => void handleDownload()}
          disabled={isDownloading}
          className="ml-6 shrink-0 bg-foreground px-3 py-1.5 text-[10px] text-background hover:bg-foreground/80 disabled:opacity-50"
        >
          {isDownloading ? "Downloading…" : option.cta}
        </button>
      </div>
      {error && (
        <span className="mt-2 text-[10px] text-destructive">{error}</span>
      )}
    </div>
  );
}

export default function ExportStep() {
  const { projectId, storyId } = useSceneEngine();

  return (
    <div className="flex h-full w-full items-center justify-center">
      <div className="flex w-full max-w-4xl flex-col gap-2">
        {EXPORT_OPTIONS.map((option) => (
          <ExportRow
            key={option.id}
            option={option}
            projectId={projectId}
            storyId={storyId}
          />
        ))}
      </div>
    </div>
  );
}
