import { useTheme } from "@/context/ThemeContext";
import { useAuth } from "@/features/auth";
import { myProjectOptions } from "@/features/story/projects/projects.queries";
import { useQuery } from "@tanstack/react-query";
import { Outlet, useNavigate, useParams } from "react-router";
import { SceneEngineProvider, useSceneEngine } from "./context";
import { SCENE_STEPS } from "./steps";
import Stepper from "./components/Stepper";
import StepperControls from "./components/StepperControls";

function SceneEngineShell() {
  const { logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { currentStep, goTo } = useSceneEngine();
  const navigate = useNavigate();
  const isDark = theme === "dark";

  return (
    <div className="flex h-screen flex-col">
      <div className="flex shrink-0 items-center justify-between border-b border-border px-4 py-1.5">
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted-foreground">Organism</span>
          <div className="h-2.5 w-px bg-border" />
          <button
            onClick={() => void navigate("/stories")}
            className="text-[10px] text-muted-foreground hover:text-foreground"
          >
            Stories
          </button>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={toggleTheme}
            className="text-[10px] text-muted-foreground hover:text-foreground"
          >
            {isDark ? "Light" : "Dark"}
          </button>
          <div className="h-2.5 w-px bg-border" />
          <button
            onClick={() => { void logout(); }}
            className="text-[10px] text-muted-foreground hover:text-foreground"
          >
            Sign out
          </button>
          <div className="h-2.5 w-px bg-border" />
          <button className="flex h-5 w-5 items-center justify-center border border-border text-[10px] text-muted-foreground hover:bg-muted/40">
            A
          </button>
        </div>
      </div>

      <div className="shrink-0 px-4 py-2">
        <Stepper steps={SCENE_STEPS} current={currentStep} onStepClick={goTo} />
      </div>

      <div className="flex flex-1 flex-col overflow-hidden">
        <Outlet />
      </div>

      <StepperControls />
    </div>
  );
}

function SceneEngineLayoutInner() {
  const { storyId } = useParams<{ storyId: string }>();
  const { data: myProject } = useQuery(myProjectOptions);

  if (!myProject || !storyId) {
    return (
      <div className="flex h-screen items-center justify-center">
        <span className="text-xs text-muted-foreground">Loading...</span>
      </div>
    );
  }

  return (
    <SceneEngineProvider projectId={myProject.id} storyId={storyId}>
      <SceneEngineShell />
    </SceneEngineProvider>
  );
}

export default function SceneEngineLayout() {
  return <SceneEngineLayoutInner />;
}
