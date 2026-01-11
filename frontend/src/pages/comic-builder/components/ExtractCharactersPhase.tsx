import { Button } from "@/components/ui/button";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useParams } from "react-router";
import {
  extractCharacters,
  selectCurrentPhaseContent,
} from "../comicBuilderSlice";
import type { PayloadItem } from "../types";

const formatKey = (key: string): string => {
  // Convert camelCase to Title Case with spaces
  return key
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (str) => str.toUpperCase())
    .trim();
};

const renderValue = (value: string | string[]): React.ReactNode => {
  if (Array.isArray(value)) {
    return value.join(", ");
  }
  return value;
};

type PayloadCardProps = {
  item: PayloadItem;
};

const PayloadCard = ({ item }: PayloadCardProps) => {
  const entries = Object.entries(item);

  return (
    <div className="border border-neutral-200 bg-white p-4 space-y-2">
      {entries.map(([key, value]) => (
        <div key={key} className="text-sm">
          <span className="font-medium text-neutral-900">
            {formatKey(key)}:{" "}
          </span>
          <span className="text-neutral-600">{renderValue(value)}</span>
        </div>
      ))}
    </div>
  );
};

const ExtractCharactersPhase = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const dispatch = useAppDispatch();
  const content = useAppSelector(selectCurrentPhaseContent);

  if (!projectId) {
    return <div>Project ID not found</div>;
  }

  const payloadItems = content?.payload ?? [];

  const handleExtractCharactersClick = () => {
    dispatch(extractCharacters(projectId));
  };

  return (
    <div className="w-full max-w-4xl px-4 space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-semibold text-black">Characters</h2>
        <Button
          onClick={handleExtractCharactersClick}
          variant="outline"
          className="border-black text-black hover:bg-neutral-100"
        >
          Extract Characters
        </Button>
      </div>

      {payloadItems.length === 0 ? (
        <p className="text-neutral-500 text-sm">
          No characters extracted yet. Click the button above to extract
          characters from your story.
        </p>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {payloadItems.map((item, index) => (
            <PayloadCard key={index} item={item} />
          ))}
        </div>
      )}
    </div>
  );
};

export default ExtractCharactersPhase;
