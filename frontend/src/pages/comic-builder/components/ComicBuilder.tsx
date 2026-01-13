import { Stepper } from "@/components/stepper";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useEffect } from "react";
import { useParams } from "react-router";
import {
  clearProjectState,
  goToSpecificPhase,
  selectComicBuilderState,
  selectCurrentPhaseIndex,
  selectCurrentPhaseName,
  selectPhases,
} from "../comicBuilderSlice";
import {
  clearCurrentProject,
  fetchProject,
  selectCurrentProjectStatus,
} from "../projectsSlice";
import ExtractCharactersPhase from "./ExtractCharactersPhase";
import WriteStoryPhase from "./WriteStoryPhase";

const ComicBuilder = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const dispatch = useAppDispatch();

  const projectStatus = useAppSelector(selectCurrentProjectStatus);
  const comicState = useAppSelector(selectComicBuilderState);
  const currentPhaseIndex = useAppSelector(selectCurrentPhaseIndex);
  const phases = useAppSelector(selectPhases);
  const currentPhaseName = useAppSelector(selectCurrentPhaseName);

  const renderPhaseComponent = () => {
    switch (currentPhaseName) {
      case "write-story":
        return <WriteStoryPhase />;
      case "extract-characters":
        return <ExtractCharactersPhase />;
      default:
        return null;
    }
  };

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
    // TODO removing this now, but need to add the new endpoint to fetch the state here
  }, []);

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
    <div className="flex flex-col h-screen bg-background border-r border-border">
      {/* Stepper stays fixed at top */}
      <div className="shrink-0 flex justify-center py-4">
        <Stepper
          names={phases.map((phase) => phase.name)}
          currentStep={currentPhaseIndex}
          goToSpecificStep={handleGoToSpecificPhaseClick}
        />
      </div>
      {/* Scrollable content area */}
      <div className="flex-1 overflow-y-auto flex justify-center pb-4">
        {renderPhaseComponent()}
      </div>
    </div>
  );
};

export default ComicBuilder;
