import { useSceneEngine } from "../context";
import { SCENE_STEPS } from "../steps";

const firstStepId = SCENE_STEPS[0].id;
const lastStepId = SCENE_STEPS[SCENE_STEPS.length - 1].id;

export default function StepperControls() {
  const { currentStep, goBack, goNext } = useSceneEngine();

  const canGoBack = currentStep > firstStepId;
  const canGoNext = currentStep < lastStepId;

  return (
    <div className="flex items-center justify-between border-t border-border px-4 py-2">
      <button
        onClick={goBack}
        disabled={!canGoBack}
        className="border border-border px-3 py-1.5 text-[10px] text-muted-foreground hover:bg-muted/40 disabled:pointer-events-none disabled:opacity-30"
      >
        Back
      </button>
      {canGoNext ? (
        <button
          onClick={goNext}
          className="bg-foreground px-3 py-1.5 text-[10px] text-background hover:bg-foreground/80"
        >
          Next
        </button>
      ) : (
        <button className="bg-foreground px-3 py-1.5 text-[10px] text-background hover:bg-foreground/80">
          Done
        </button>
      )}
    </div>
  );
}
