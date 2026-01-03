import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import {
  selectCurrentPhaseInputText,
  setInputText,
  streamComicStory,
  selectCurrentPhaseContent,
} from "./comicBuilderSlice";
import InputArea from "./components/InputArea";

const ComicBuilder = () => {
  const inputText = useAppSelector(selectCurrentPhaseInputText);
  const dispatch = useAppDispatch();
  const story = useAppSelector(selectCurrentPhaseContent);

  const handleSendClick = () => {
    console.log("send input text:", inputText);
    dispatch(streamComicStory(inputText));
  };

  return (
    <div className="flex flex-col h-screen bg-background border-r border-border items-center justify-center gap-4 mt-4 mb-4">
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
    </div>
  );
};

export default ComicBuilder;
