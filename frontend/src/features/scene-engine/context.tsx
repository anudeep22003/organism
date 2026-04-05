import type { ReactNode } from "react";
import {
  createContext,
  useCallback,
  useContext,
  useState,
} from "react";
import { SCENE_STEPS } from "./steps";

const TEST_PROJECT_ID = "9c10291d-4b0a-4c2f-8deb-417d36a12d7b";
// const TEST_STORY_ID = "e446a444-2480-4e38-9560-3aa90d806494";
const TEST_STORY_ID = "f4ca0d39-4801-4e6c-b932-889f27048b09";
// const TEST_STORY_ID = "b9f99a77-4582-4798-8ade-d1340a6f2e4e";

type SceneEngineContextValue = {
  currentStep: number;
  goTo: (id: number) => void;
  goNext: () => void;
  goBack: () => void;
  projectId: string;
  storyId: string;
  setProjectId: (id: string) => void;
  setStoryId: (id: string) => void;
};

const SceneEngineContext =
  createContext<SceneEngineContextValue | null>(null);

export function SceneEngineProvider({
  children,
}: {
  children: ReactNode;
}) {
  const [currentStep, setCurrentStep] = useState(1);
  const [projectId, setProjectId] = useState(TEST_PROJECT_ID);
  const [storyId, setStoryId] = useState(TEST_STORY_ID);

  const goTo = useCallback((id: number) => {
    const valid = SCENE_STEPS.find((s) => s.id === id);
    if (valid) setCurrentStep(id);
  }, []);

  const goNext = useCallback(() => {
    setCurrentStep((prev) =>
      prev < SCENE_STEPS[SCENE_STEPS.length - 1].id ? prev + 1 : prev,
    );
  }, []);

  const goBack = useCallback(() => {
    setCurrentStep((prev) =>
      prev > SCENE_STEPS[0].id ? prev - 1 : prev,
    );
  }, []);

  return (
    <SceneEngineContext.Provider
      value={{
        currentStep,
        goTo,
        goNext,
        goBack,
        projectId,
        storyId,
        setProjectId,
        setStoryId,
      }}
    >
      {children}
    </SceneEngineContext.Provider>
  );
}

export function useSceneEngine() {
  const ctx = useContext(SceneEngineContext);
  if (!ctx)
    throw new Error(
      "useSceneEngine must be used within SceneEngineProvider",
    );
  return ctx;
}
