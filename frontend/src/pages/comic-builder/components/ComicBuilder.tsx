import { Stepper } from "@/components/stepper";
import { useAppDispatch, useAppSelector } from "@/store/hooks";
import { useEffect } from "react";
import { useParams } from "react-router";
import phaseMap, { phases, type PhaseMapKey } from "../phaseMap";
import { clearComicState, setCurrentPhase } from "../slices/comicSlice";
import { fetchComicState } from "../slices/thunks/comicThunks";

const ComicBuilder = () => {
  const { projectId } = useParams<{ projectId: string }>();
  const dispatch = useAppDispatch();
  const comicStatus = useAppSelector((state) => state.comic.status);
  const currentPhase = useAppSelector(
    (state) => state.comic.currentPhase
  );

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

  const renderPhaseComponent = () => {
    const PhaseComponent = phaseMap[currentPhase];
    return <PhaseComponent />;
  };

  const handlePhaseChange = (phase: PhaseMapKey) => {
    dispatch(setCurrentPhase(phase));
  };

  if (comicStatus === "loading") {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-neutral-500">Loading project...</p>
      </div>
    );
  }

  if (comicStatus === "failed") {
    return (
      <div className="flex h-screen items-center justify-center">
        <p className="text-red-500">Failed to load project</p>
      </div>
    );
  }

  // if (!comicState) {
  //   return (
  //     <div className="flex h-screen items-center justify-center">
  //       <p className="text-neutral-500">Initializing...</p>
  //     </div>
  //   );
  // }

  return (
    <div className="flex flex-col h-screen bg-background border-r border-border">
      {/* Stepper stays fixed at top */}
      <div className="shrink-0 flex justify-center py-4">
        <Stepper
          phases={phases}
          currentPhase={currentPhase}
          onPhaseChange={handlePhaseChange}
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
