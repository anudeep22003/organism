import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setInputText, streamComicStory } from "./comicBuilderSlice";
import InputArea from "./components/InputArea";

const ComicBuilder = () => {
  const inputText = useAppSelector(
    (state) => state.comicBuilder.inputText
  );
  const dispatch = useAppDispatch();
  const story = useAppSelector((state) => state.comicBuilder.story);

  const handleSendClick = () => {
    console.log("send input text:", inputText);
    dispatch(streamComicStory());
  };

  return (
    <div className="flex flex-col h-screen bg-background border-r border-border items-center justify-center">
      <InputArea
        onSendClick={handleSendClick}
        setInputText={(value) => dispatch(setInputText(value))}
        inputText={inputText}
      />
      {story && (
        <div className="text-sm text-muted-foreground">
          {story.text}
        </div>
      )}
    </div>
  );
};

export default ComicBuilder;
