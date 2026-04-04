import type { StepDef } from "../types";

type StepperProps = {
  steps: StepDef[];
  current: number;
  onStepClick?: (id: number) => void;
};

export default function Stepper({ steps, current, onStepClick }: StepperProps) {
  const before = steps.filter((s) => s.id < current);
  const active = steps.find((s) => s.id === current)!;
  const after = steps.filter((s) => s.id > current);

  return (
    <div className="flex w-full items-center">
      {before.length > 0 && (
        <div className="flex shrink-0 items-center gap-1">
          {before.map((step) => (
            <div
              key={step.id}
              onClick={() => onStepClick?.(step.id)}
              className="flex h-5 w-5 shrink-0 cursor-pointer items-center justify-center border border-foreground bg-foreground text-[10px] text-background opacity-40 hover:opacity-70"
            >
              {step.id}
            </div>
          ))}
        </div>
      )}

      {before.length > 0 && <div className="mx-2 h-px flex-1 bg-border" />}

      <div className="flex shrink-0 items-center gap-1.5">
        <div
          onClick={() => onStepClick?.(active.id)}
          className="flex h-5 w-5 shrink-0 cursor-pointer items-center justify-center border border-foreground bg-foreground text-[10px] text-background"
        >
          {active.id}
        </div>
        <span className="text-xs text-foreground">{active.label}</span>
      </div>

      {after.length > 0 && <div className="mx-2 h-px flex-1 bg-border" />}

      {after.length > 0 && (
        <div className="flex shrink-0 items-center gap-1">
          {after.map((step) => (
            <div
              key={step.id}
              onClick={() => onStepClick?.(step.id)}
              className="flex h-5 w-5 shrink-0 cursor-pointer items-center justify-center border border-border bg-background text-[10px] text-muted-foreground hover:opacity-70"
            >
              {step.id}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
