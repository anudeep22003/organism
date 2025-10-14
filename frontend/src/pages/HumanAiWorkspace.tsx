import { HumanArea } from "@/components/HumanArea";
import { GenerativeArea } from "@/components/GenerativeArea";
import { useAppContext } from "@/context/AppContext";

export default function HumanAiWorkspace() {
  const { showGenerative } = useAppContext();

  return (
    <div className="h-screen flex flex-col bg-background">
      {/* Mobile View */}
      <div className="md:hidden h-full">
        <div
          className={`h-full transition-transform duration-300 ${
            showGenerative ? "-translate-x-full" : "translate-x-0"
          }`}
        >
          <HumanArea />
        </div>
        <div
          className={`absolute inset-0 transition-transform duration-300 ${
            showGenerative ? "translate-x-0" : "translate-x-full"
          }`}
        >
          <GenerativeArea />
        </div>
      </div>

      {/* Desktop View */}
      <div className="hidden md:flex h-full">
        <div className="w-1/2">
          <HumanArea />
        </div>
        <div className="w-1/2">
          <GenerativeArea />
        </div>
      </div>
    </div>
  );
}
