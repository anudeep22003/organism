import type { PhaseMapKey } from "@/pages/comic-builder/phaseMap";

interface StepperProps {
  phases: PhaseMapKey[];
  currentPhase: PhaseMapKey;
  onPhaseChange: (phase: PhaseMapKey) => void;
}

type StepItemProps = {
  phase: PhaseMapKey;
  currentPhase: PhaseMapKey;
  onPhaseChange: (phase: PhaseMapKey) => void;
};

const StepItem = ({
  phase,
  currentPhase,
  onPhaseChange,
}: StepItemProps) => {
  const handleClick = () => {
    if (currentPhase !== phase) {
      onPhaseChange(phase);
    }
  };
  return (
    <div
      className={`w-fit ${
        currentPhase === phase
          ? "bg-gray-900 text-gray-100 cursor-not-allowed"
          : "bg-gray-100 text-gray-900 cursor-pointer"
      } flex items-center justify-center gap-2 p-2 rounded-md`}
      onClick={handleClick}
    >
      <span className="text-sm font-medium ">{phase}</span>
    </div>
  );
};
export const Stepper = ({
  phases,
  currentPhase,
  onPhaseChange,
}: StepperProps) => {
  return (
    <div className="relative">
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
        <div className="w-full h-1 bg-gray-200" />
      </div>

      <div className="relative flex gap-8 justify-center items-center z-10">
        {phases.map((phase) => (
          <StepItem
            key={phase}
            phase={phase}
            currentPhase={currentPhase}
            onPhaseChange={onPhaseChange}
          />
        ))}
      </div>
    </div>
  );
};
