import { useSceneEngine } from "../context";
import { SCENE_STEPS } from "../steps";

export default function PlaceholderStep() {
  const { currentStep } = useSceneEngine();
  const label = SCENE_STEPS.find((s) => s.id === currentStep)?.label ?? "";

  return (
    <div className="flex h-full items-center justify-center">
      <span className="text-xs text-muted-foreground">{label}</span>
    </div>
  );
}
