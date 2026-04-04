import { useSceneEngine } from "./context";
import { SCENE_STEPS } from "./steps";

export default function SceneEngine() {
  const { currentStep } = useSceneEngine();
  const step = SCENE_STEPS.find((s) => s.id === currentStep);

  if (!step) return null;

  return <step.component />;
}
