import { useSceneEngine } from "../context";
import { SCENE_STEPS } from "../steps";

const firstStepId = SCENE_STEPS[0].id;
const lastStepId = SCENE_STEPS[SCENE_STEPS.length - 1].id;

export default function StepperControls() {
  const { currentStep, goBack, goNext } = useSceneEngine();

  return (
    <div className="flex items-center justify-between border-t border-border px-4 py-2">
      {currentStep > firstStepId ? (
        <button
          onClick={goBack}
          className="text-[10px] text-muted-foreground hover:text-foreground"
        >
          ← Back
        </button>
      ) : (
        <span />
      )}
      {currentStep < lastStepId ? (
        <button
          onClick={goNext}
          className="text-[10px] text-muted-foreground hover:text-foreground"
        >
          Next →
        </button>
      ) : (
        <span />
      )}
    </div>
  );
}
