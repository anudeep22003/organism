import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import {
  selectCurrentPhaseContent,
  selectCurrentPhaseInputText,
  setInputText,
  streamComicStory,
} from "../comicBuilderSlice";
import InputArea from "./InputArea";

const WriteStoryPhase = () => {
  const dispatch = useAppDispatch();
  const inputText = useAppSelector(selectCurrentPhaseInputText);
  const story = useAppSelector(selectCurrentPhaseContent);

  const handleSendClick = () => {
    dispatch(streamComicStory(inputText));
  };

  return (
    <div className="flex flex-col gap-4 w-full max-w-4xl px-4">
      <InputArea
        onSendClick={handleSendClick}
        setInputText={(value) => dispatch(setInputText(value))}
        inputText={inputText}
      />
      {story && (
        <div className="text-sm text-muted-foreground p-2 border border-border rounded-md">
          <MarkdownRenderer content={story.text} />
        </div>
      )}
    </div>
  );
};

export default WriteStoryPhase;
