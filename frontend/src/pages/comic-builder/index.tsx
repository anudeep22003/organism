import InputArea from "./components/InputArea";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { setInputText } from "./comicBuilderSlice";

const ComicBuilder = () => {
  const inputText = useAppSelector(
    (state) => state.comicBuilder.inputText
  );
  const dispatch = useAppDispatch();

  const handleSendClick = () => {
    console.log("send input text:", inputText);
  };

  return (
    <div className="flex flex-col h-screen bg-background border-r border-border items-center justify-center">
      <InputArea
        onSendClick={handleSendClick}
        setInputText={(value) => dispatch(setInputText(value))}
        inputText={inputText}
      />
    </div>
  );
};

export default ComicBuilder;
