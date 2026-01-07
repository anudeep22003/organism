import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { Stepper } from "@/components/stepper";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useParams } from "react-router";
import {
  goToSpecificPhase,
  selectCurrentPhaseContent,
  selectCurrentPhaseInputText,
  setInputText,
  streamComicStory,
} from "../comicBuilderSlice";
import InputArea from "../components/InputArea";

const ComicBuilder = () => {
  const { projectId } = useParams<{ projectId: string }>();

  // TODO: remove this
  console.log("projectId:", projectId);

  const inputText = useAppSelector(selectCurrentPhaseInputText);
  const dispatch = useAppDispatch();
  const story = useAppSelector(selectCurrentPhaseContent);
  const currentPhaseIndex = useAppSelector(
    (state) => state.comicBuilder.currentPhaseIndex
  );
  const phases = useAppSelector((state) => state.comicBuilder.phases);

  const handleSendClick = () => {
    console.log("send input text:", inputText);
    dispatch(streamComicStory(inputText));
  };

  const handleGoToSpecificPhaseClick = (phaseIndex: number) => {
    dispatch(goToSpecificPhase(phaseIndex));
  };

  return (
    <div className="flex flex-col h-screen bg-background border-r border-border items-center justify-center gap-4 mt-4 mb-4">
      <Stepper
        steps={phases.length}
        currentStep={currentPhaseIndex}
        goToSpecificStep={handleGoToSpecificPhaseClick}
      />
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
