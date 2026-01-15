import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { selectStoryText } from "../slices/comicSlice";
import { streamComicStory } from "../slices/thunks/storyThunks";
import InputArea from "./InputArea";

const WriteStoryPhase = () => {
  const dispatch = useAppDispatch();
  const storyText = useAppSelector(selectStoryText);

  const handleSubmit = (draft: string) => {
    dispatch(streamComicStory(draft));
  };

  return (
    <div className="flex flex-col gap-4 w-full max-w-4xl px-4">
      <InputArea onSubmit={handleSubmit} />
      {storyText && (
        <div className="text-sm text-muted-foreground p-2 border border-border rounded-md">
          <MarkdownRenderer content={storyText} />
        </div>
      )}
    </div>
  );
};

export default WriteStoryPhase;
