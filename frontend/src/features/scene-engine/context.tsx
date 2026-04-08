import type { ReactNode } from "react";
import {
  createContext,
  useCallback,
  useContext,
  useState,
} from "react";
import { SCENE_STEPS } from "./steps";

type SceneEngineContextValue = {
  currentStep: number;
  goTo: (id: number) => void;
  goNext: () => void;
  goBack: () => void;
  projectId: string;
  storyId: string;
};

const SceneEngineContext =
  createContext<SceneEngineContextValue | null>(null);

export function SceneEngineProvider({
  projectId,
  storyId,
  children,
}: {
  projectId: string;
  storyId: string;
  children: ReactNode;
}) {
  const [currentStep, setCurrentStep] = useState(1);

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
