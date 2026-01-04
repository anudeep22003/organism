interface StepperProps {
  steps: number;
  currentStep: number;
  goToSpecificStep: (step: number) => void;
}

type StepItemProps = {
  step: number;
  currentStep: number;
  goToSpecificStep: (step: number) => void;
};

const StepItem = ({
  step,
  currentStep,
  goToSpecificStep,
}: StepItemProps) => {
  return (
    <div
      className={`w-10 h-10 ${
        currentStep === step
          ? "bg-gray-900 text-gray-100 cursor-not-allowed"
          : "bg-gray-100 text-gray-900 cursor-pointer"
      } rounded-full flex items-center justify-center`}
      onClick={() => currentStep !== step && goToSpecificStep(step)}
    >
      {step}
    </div>
  );
};
export const Stepper = ({
  steps,
  currentStep,
  goToSpecificStep,
}: StepperProps) => {
  return (
    <div className="relative">
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
        <div className="w-full h-1 bg-gray-200" />
      </div>

      <div className="relative flex gap-8 justify-center items-center z-10">
        {Array.from({ length: steps }, (_, index) => (
          <StepItem
            key={index}
            step={index}
            currentStep={currentStep}
            goToSpecificStep={goToSpecificStep}
          />
        ))}
      </div>
    </div>
  );
};
