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
    <>
      <InputArea
        onSendClick={handleSendClick}
        setInputText={(value) => dispatch(setInputText(value))}
        inputText={inputText}
      />
      {story && (
        <div className="text-sm text-muted-foreground max-w-2/3 overflow-y-auto h-full p-2 border border-border rounded-md">
          <MarkdownRenderer content={story.text} />
        </div>
      )}
    </>
  );
};

export default WriteStoryPhase;
