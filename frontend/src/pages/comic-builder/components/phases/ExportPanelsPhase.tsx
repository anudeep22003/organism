import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { useAppSelector } from "@/store/hooks";
import {
  CheckCircle2,
  Download,
  ImageIcon,
  Layers,
} from "lucide-react";
import { selectPanels } from "../../slices/comicSlice";
import { downloadPanelsZip } from "../../utils";

const ExportPanelsPhase = () => {
  const panels = useAppSelector(selectPanels);
  const projectName = useAppSelector(
    (state) => state.comic.projectName
  );
  const renderedPanels = panels.filter(
    (panel) => panel.render && panel.render.url
  );

  const totalPanelsLength = panels.length;
  const renderedPanelsLength = renderedPanels.length;

  const progress =
    totalPanelsLength > 0
      ? (renderedPanelsLength / totalPanelsLength) * 100
      : 0;
  const isReadyToExport = renderedPanelsLength > 0;

  const handleDownloadClick = async () => {
    const downloadablePanels = renderedPanels.map((panel, index) => ({
      index,
      imageUrl: panel.render!.url!,
    }));
    await downloadPanelsZip(downloadablePanels, projectName!);
  };

  return (
    <div className="w-full max-w-2xl px-4">
      <Card className="overflow-hidden border-neutral-300">
        <CardHeader className="pb-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-black text-white">
              <Layers className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-lg text-black">
                Export Your Comic
              </CardTitle>
              <CardDescription>
                Download all rendered panels as a ZIP archive
              </CardDescription>
            </div>
          </div>
        </CardHeader>

        <CardContent className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl bg-neutral-50 p-4 border border-neutral-200">
              <div className="flex items-center gap-2 text-neutral-500 mb-1">
                <ImageIcon className="h-4 w-4" />
                <span className="text-xs font-medium uppercase tracking-wide">
                  Total Panels
                </span>
              </div>
              <p className="text-3xl font-bold text-black tabular-nums">
                {totalPanelsLength}
              </p>
            </div>

            <div className="rounded-xl bg-neutral-100 p-4 border border-neutral-200">
              <div className="flex items-center gap-2 text-neutral-600 mb-1">
                <CheckCircle2 className="h-4 w-4" />
                <span className="text-xs font-medium uppercase tracking-wide">
                  Rendered
                </span>
              </div>
              <p className="text-3xl font-bold text-black tabular-nums">
                {renderedPanelsLength}
              </p>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-neutral-500">Render Progress</span>
              <span className="font-medium text-black">
                {Math.round(progress)}%
              </span>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-neutral-200">
              <div
                className="h-full rounded-full bg-black transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        </CardContent>

        <CardFooter className="bg-neutral-50 border-t border-neutral-200 pt-4">
          <Button
            onClick={handleDownloadClick}
            disabled={!isReadyToExport}
            variant="outline"
            size="lg"
            className="w-full border-black text-black hover:bg-black hover:text-white transition-colors"
          >
            <Download className="h-4 w-4" />
            {isReadyToExport
              ? `Export ${renderedPanelsLength} Panel${
                  renderedPanelsLength === 1 ? "" : "s"
                }`
              : "No Panels to Export"}
          </Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default ExportPanelsPhase;
