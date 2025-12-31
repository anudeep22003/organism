import { useState } from "react";
import InputArea from "./components/InputArea";

const ComicBuilder = () => {
  const [inputText, setInputText] = useState("");

  const handleSendClick = () => {
    console.log("send input text:", inputText);
  };

  return (
    <div className="flex flex-col h-screen bg-background border-r border-border items-center justify-center">
      <InputArea
        onSendClick={handleSendClick}
        setInputText={setInputText}
        inputText={inputText}
      />
    </div>
  );
};

export default ComicBuilder;
