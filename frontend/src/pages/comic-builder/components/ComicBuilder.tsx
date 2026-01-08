import { MarkdownRenderer } from "@/components/MarkdownRenderer";
import { Stepper } from "@/components/stepper";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useEffect } from "react";
import { useParams } from "react-router";
import {
  clearProjectState,
  goToSpecificPhase,
  loadProjectState,
  selectComicBuilderState,
  selectCurrentPhaseContent,
  selectCurrentPhaseIndex,
  selectCurrentPhaseInputText,
  selectPhases,
  setInputText,
  streamComicStory,
} from "../comicBuilderSlice";
import {
  clearCurrentProject,
  fetchProject,
  selectCurrentProject,
  selectCurrentProjectStatus,
} from "../projectsSlice";
import InputArea from "./InputArea";

const ComicBuilder = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const dispatch = useAppDispatch();

  const currentProject = useAppSelector(selectCurrentProject);
  const projectStatus = useAppSelector(selectCurrentProjectStatus);
  const comicState = useAppSelector(selectComicBuilderState);
  const inputText = useAppSelector(selectCurrentPhaseInputText);
  const story = useAppSelector(selectCurrentPhaseContent);
  const currentPhaseIndex = useAppSelector(selectCurrentPhaseIndex);
  const phases = useAppSelector(selectPhases);

  // Fetch project on mount
  useEffect(() => {
    if (projectId) {
      dispatch(fetchProject(projectId));
    }
    return () => {
      dispatch(clearCurrentProject());
      dispatch(clearProjectState());
    };
  }, [dispatch, projectId]);

  // Load project state into comicBuilder slice when project is fetched
  useEffect(() => {
    if (currentProject && !comicState) {
      dispatch(loadProjectState(currentProject.state));
    }
  }, [currentProject, comicState, dispatch]);

  const handleSendClick = () => {
    dispatch(streamComicStory(inputText));
  };

  const handleGoToSpecificPhaseClick = (phaseIndex: number) => {
    dispatch(goToSpecificPhase(phaseIndex));
  };

  if (projectStatus === "loading") {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-neutral-500">Loading project...</p>
      </div>
    );
  }

  if (projectStatus === "failed") {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-red-500">Failed to load project</p>
      </div>
    );
  }

  if (!comicState) {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-neutral-500">Initializing...</p>
      </div>
    );
  }

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
