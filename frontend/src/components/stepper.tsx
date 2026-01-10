interface StepperProps {
  names: string[];
  currentStep: number;
  goToSpecificStep: (step: number) => void;
}

type StepItemProps = {
  step: number;
  name: string;
  currentStep: number;
  goToSpecificStep: (step: number) => void;
};

const StepItem = ({
  step,
  name,
  currentStep,
  goToSpecificStep,
}: StepItemProps) => {
  return (
    <div
      className={`w-fit ${
        currentStep === step
          ? "bg-gray-900 text-gray-100 cursor-not-allowed"
          : "bg-gray-100 text-gray-900 cursor-pointer"
      } flex items-center justify-center gap-2 p-2 rounded-md`}
      onClick={() => currentStep !== step && goToSpecificStep(step)}
    >
      <span className="text-sm font-medium ">{name.toLowerCase()}</span>
    </div>
  );
};
export const Stepper = ({
  names,
  currentStep,
  goToSpecificStep,
}: StepperProps) => {
  return (
    <div className="relative">
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none z-0">
        <div className="w-full h-1 bg-gray-200" />
      </div>

      <div className="relative flex gap-8 justify-center items-center z-10">
        {names.map((name, index) => (
          <StepItem
            key={index}
            step={index}
            name={name}
            currentStep={currentStep}
            goToSpecificStep={goToSpecificStep}
          />
        ))}
      </div>
    </div>
  );
};
