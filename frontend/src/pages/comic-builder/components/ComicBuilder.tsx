import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useEffect } from "react";
import { useParams } from "react-router";
import { clearComicState, fetchComicState } from "../slices/comicSlice";

const ComicBuilder = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const dispatch = useAppDispatch();
  const comicState = useAppSelector((state) => state.comic);

  // Fetch project on mount
  useEffect(() => {
    if (projectId) {
      dispatch(fetchComicState(projectId));
    }
    return () => {
      dispatch(clearComicState());
    };
  }, [dispatch, projectId]);

  // Load project state into comicBuilder slice when project is fetched
  useEffect(() => {
    // TODO removing this now, but need to add the new endpoint to fetch the state here
  }, []);

  if (comicState?.status === "loading") {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-neutral-500">Loading project...</p>
      </div>
    );
  }

  if (comicState?.status === "failed") {
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
        {/* <Stepper
          names={phases.map((phase) => phase.name)}
          currentStep={currentPhaseIndex}
          goToSpecificStep={handleGoToSpecificPhaseClick}
        /> */}
        we will render the phase stepper here
      </div>
      {/* Scrollable content area */}
      <div className="flex-1 overflow-y-auto flex justify-center pb-4">
        we will render the actual phase here
      </div>
    </div>
  );
};

export default ComicBuilder;
